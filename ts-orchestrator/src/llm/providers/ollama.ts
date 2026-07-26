import { LLMProvider } from '../provider.js';
import type {
  LLMCompletionRequest,
  LLMCompletionResponse,
  LLMModelInfo,
  LLMProviderConfig,
} from '../types.js';

interface OllamaChatResponse {
  model: string;
  message: { role: string; content: string };
  done: boolean;
  total_duration?: number;
  prompt_eval_count?: number;
  eval_count?: number;
}

interface OllamaTagsResponse {
  models: Array<{
    name: string;
    modified_at?: string;
    size?: number;
    details?: { parameter_size?: string; family?: string };
  }>;
}

export class OllamaProvider extends LLMProvider {
  constructor(config?: Partial<LLMProviderConfig>) {
    super({
      name: 'ollama',
      apiKey: config?.apiKey ?? process.env.OLLAMA_API_KEY ?? '',
      baseUrl: config?.baseUrl ?? 'https://ollama.com/api',
      defaultModel: config?.defaultModel ?? process.env.OLLAMA_MODEL ?? 'gemma4:31b',
      models: config?.models ?? [process.env.OLLAMA_MODEL ?? 'gemma4:31b'],
      priority: config?.priority ?? 10,
      timeout: config?.timeout ?? 120_000,
      maxRetries: config?.maxRetries ?? 2,
    });
  }

  get name(): string {
    return 'ollama';
  }

  async testConnection(): Promise<boolean> {
    if (!this.isAvailable()) return false;
    try {
      const res = await fetch(`${this.config.baseUrl}/tags`, {
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
      const res = await fetch(`${this.config.baseUrl}/tags`, {
        headers: this.buildHeaders(),
        signal: AbortSignal.timeout(10_000),
      });
      if (!res.ok) return [];
      const data = (await res.json()) as OllamaTagsResponse;
      return (data.models ?? []).map((m) => ({
        id: m.name,
        provider: 'ollama',
        displayName: m.name,
        maxTokens: 128_000,
        supportsTools: true,
        supportsVision: m.name.includes('vl') || m.name.includes('vision'),
        costPer1kPrompt: 0,
        costPer1kCompletion: 0,
      }));
    } catch {
      return [];
    }
  }

  async complete(req: LLMCompletionRequest): Promise<LLMCompletionResponse> {
    const model = req.model || this.config.defaultModel;
    const body = {
      model,
      messages: req.messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      stream: false,
      options: {
        num_predict: req.maxTokens ?? 2048,
        temperature: req.temperature ?? 0.7,
        top_p: req.topP ?? 0.9,
        stop: req.stop,
      },
    };

    const res = await this.withRetry(() =>
      this.fetch(`${this.config.baseUrl}/chat`, body),
    );

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      throw new Error(`Ollama API error ${res.status}: ${errText.slice(0, 200)}`);
    }

    const data = (await res.json()) as OllamaChatResponse;

    return {
      id: `ollama-${Date.now()}`,
      model: data.model,
      provider: 'ollama',
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: data.message?.content ?? '',
          },
          finishReason: data.done ? 'stop' : 'length',
        },
      ],
      usage: {
        promptTokens: data.prompt_eval_count ?? 0,
        completionTokens: data.eval_count ?? 0,
        totalTokens: (data.prompt_eval_count ?? 0) + (data.eval_count ?? 0),
      },
    };
  }

  async completeStream(
    req: LLMCompletionRequest,
    onChunk: (text: string) => void,
  ): Promise<LLMCompletionResponse> {
    const model = req.model || this.config.defaultModel;
    const body = {
      model,
      messages: req.messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      stream: true,
      options: {
        num_predict: req.maxTokens ?? 2048,
        temperature: req.temperature ?? 0.7,
        top_p: req.topP ?? 0.9,
      },
    };

    const res = await this.withRetry(() =>
      this.fetch(`${this.config.baseUrl}/chat`, body),
    );

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      throw new Error(`Ollama stream error ${res.status}: ${errText.slice(0, 200)}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let fullContent = '';
    let buffer = '';
    let promptEval = 0;
    let evalCount = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const chunk = JSON.parse(line) as OllamaChatResponse;
          if (chunk.message?.content) {
            fullContent += chunk.message.content;
            onChunk(chunk.message.content);
          }
          if (chunk.prompt_eval_count) promptEval = chunk.prompt_eval_count;
          if (chunk.eval_count) evalCount = chunk.eval_count;
        } catch {
          // skip incomplete JSON lines
        }
      }
    }

    return {
      id: `ollama-${Date.now()}`,
      model,
      provider: 'ollama',
      choices: [
        {
          index: 0,
          message: { role: 'assistant', content: fullContent },
          finishReason: 'stop',
        },
      ],
      usage: {
        promptTokens: promptEval,
        completionTokens: evalCount,
        totalTokens: promptEval + evalCount,
      },
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
