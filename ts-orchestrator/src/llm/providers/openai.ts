import { LLMProvider } from '../provider.js';
import type {
  LLMCompletionRequest,
  LLMCompletionResponse,
  LLMModelInfo,
  LLMProviderConfig,
} from '../types.js';

interface OpenAIChatResponse {
  id: string;
  object: string;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string | null;
      tool_calls?: Array<{
        id: string;
        type: 'function';
        function: { name: string; arguments: string };
      }>;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

interface OpenAIModelsResponse {
  data: Array<{
    id: string;
    object: string;
    created: number;
    owned_by: string;
  }>;
}

interface OpenAIStreamChunk {
  id: string;
  object: string;
  model: string;
  choices: Array<{
    index: number;
    delta: { role?: string; content?: string };
    finish_reason: string | null;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export class OpenAIProvider extends LLMProvider {
  constructor(config?: Partial<LLMProviderConfig>) {
    super({
      name: 'openai',
      apiKey: config?.apiKey ?? process.env.OPENAI_API_KEY ?? '',
      baseUrl: config?.baseUrl ?? (process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1'),
      defaultModel: config?.defaultModel ?? process.env.OPENAI_MODEL ?? 'gpt-4o',
      models: config?.models ?? [],
      priority: config?.priority ?? 20,
      timeout: config?.timeout ?? 120_000,
      maxRetries: config?.maxRetries ?? 2,
    });
  }

  get name(): string {
    return this.config.name;
  }

  async testConnection(): Promise<boolean> {
    if (!this.isAvailable()) return false;
    try {
      const res = await fetch(`${this.config.baseUrl}/models`, {
        headers: this.buildHeaders(),
        signal: AbortSignal.timeout(10_000),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async listModels(): Promise<LLMModelInfo[]> {
    try {
      const res = await fetch(`${this.config.baseUrl}/models`, {
        headers: this.buildHeaders(),
        signal: AbortSignal.timeout(10_000),
      });
      if (!res.ok) return [];
      const data = (await res.json()) as OpenAIModelsResponse;
      return (data.data ?? []).map((m) => ({
        id: m.id,
        provider: this.config.name,
        displayName: m.id,
        maxTokens: 128_000,
        supportsTools: true,
        supportsVision: m.id.includes('vision') || m.id.includes('vl'),
      }));
    } catch {
      return [];
    }
  }

  async complete(req: LLMCompletionRequest): Promise<LLMCompletionResponse> {
    const body = {
      model: req.model || this.config.defaultModel,
      messages: req.messages.map((m) => ({
        role: m.role,
        content: m.content,
        ...(m.name ? { name: m.name } : {}),
      })),
      max_tokens: req.maxTokens ?? 2048,
      temperature: req.temperature ?? 0.7,
      top_p: req.topP ?? 0.9,
      stop: req.stop,
      stream: false,
      ...(req.tools?.length ? { tools: req.tools } : {}),
    };

    const res = await this.withRetry(() =>
      this.fetch(`${this.config.baseUrl}/chat/completions`, body),
    );

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      throw new Error(`OpenAI API error ${res.status}: ${errText.slice(0, 200)}`);
    }

    const data = (await res.json()) as OpenAIChatResponse;

    return {
      id: data.id,
      model: data.model,
      provider: this.config.name,
      choices: data.choices.map((c) => ({
        index: c.index,
        message: {
          role: 'assistant',
          content: c.message?.content ?? '',
          toolCalls: c.message?.tool_calls?.map((tc) => ({
            id: tc.id,
            type: 'function' as const,
            function: {
              name: tc.function.name,
              arguments: tc.function.arguments,
            },
          })),
        },
        finishReason: c.finish_reason === 'stop' ? 'stop'
          : c.finish_reason === 'length' ? 'length'
          : c.finish_reason === 'tool_calls' ? 'tool_calls'
          : 'stop',
      })),
      usage: data.usage
        ? {
            promptTokens: data.usage.prompt_tokens,
            completionTokens: data.usage.completion_tokens,
            totalTokens: data.usage.total_tokens,
          }
        : undefined,
    };
  }

  async completeStream(
    req: LLMCompletionRequest,
    onChunk: (text: string) => void,
  ): Promise<LLMCompletionResponse> {
    const body = {
      model: req.model || this.config.defaultModel,
      messages: req.messages,
      max_tokens: req.maxTokens ?? 2048,
      temperature: req.temperature ?? 0.7,
      stream: true,
      stream_options: { include_usage: true },
    };

    const res = await this.withRetry(() =>
      this.fetch(`${this.config.baseUrl}/chat/completions`, body),
    );

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      throw new Error(`OpenAI stream error ${res.status}: ${errText.slice(0, 200)}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let fullContent = '';
    let buffer = '';
    let finalUsage: OpenAIStreamChunk['usage'];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === 'data: [DONE]') continue;
        const jsonStr = trimmed.startsWith('data: ') ? trimmed.slice(6) : trimmed;
        try {
          const chunk = JSON.parse(jsonStr) as OpenAIStreamChunk;
          if (chunk.usage) finalUsage = chunk.usage;
          const delta = chunk.choices?.[0]?.delta?.content;
          if (delta) {
            fullContent += delta;
            onChunk(delta);
          }
        } catch {
          // skip
        }
      }
    }

    return {
      id: `openai-${Date.now()}`,
      model: body.model,
      provider: this.config.name,
      choices: [
        {
          index: 0,
          message: { role: 'assistant', content: fullContent },
          finishReason: 'stop',
        },
      ],
      usage: finalUsage
        ? {
            promptTokens: finalUsage.prompt_tokens,
            completionTokens: finalUsage.completion_tokens,
            totalTokens: finalUsage.total_tokens,
          }
        : undefined,
    };
  }

  private async withRetry(
    fn: () => Promise<Response>,
    attempt = 0,
  ): Promise<Response> {
    try {
      return await fn();
    } catch (err) {
      if (attempt < (this.config.maxRetries ?? 2)) {
        await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
        return this.withRetry(fn, attempt + 1);
      }
      throw err;
    }
  }
}
