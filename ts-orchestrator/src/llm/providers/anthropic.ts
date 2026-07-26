import { LLMProvider } from '../provider.js';
import type {
  LLMCompletionRequest,
  LLMCompletionResponse,
  LLMModelInfo,
  LLMProviderConfig,
} from '../types.js';

interface AnthropicContentBlock {
  type: string;
  text?: string;
  id?: string;
  name?: string;
  input?: unknown;
}

interface AnthropicResponse {
  id: string;
  type: string;
  role: string;
  content: AnthropicContentBlock[];
  model: string;
  stop_reason: string | null;
  stop_sequence: string | null;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

interface AnthropicModelsResponse {
  data: Array<{
    type: string;
    id: string;
    display_name?: string;
    created_at?: string;
  }>;
}

interface AnthropicStreamEvent {
  type: string;
  index?: number;
  content_block?: AnthropicContentBlock;
  delta?: Record<string, unknown>;
  message?: AnthropicResponse;
  usage?: { output_tokens: number };
}

export class AnthropicProvider extends LLMProvider {
  constructor(config?: Partial<LLMProviderConfig>) {
    super({
      name: 'anthropic',
      apiKey: config?.apiKey ?? process.env.ANTHROPIC_API_KEY ?? '',
      baseUrl: config?.baseUrl ?? (process.env.ANTHROPIC_BASE_URL || 'https://api.anthropic.com'),
      defaultModel: config?.defaultModel ?? process.env.ANTHROPIC_MODEL ?? '',
      models: config?.models ?? [],
      priority: config?.priority ?? 15,
      timeout: config?.timeout ?? 120_000,
      maxRetries: config?.maxRetries ?? 2,
    });
  }

  get name(): string {
    return this.config.name;
  }

  protected buildHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'x-api-key': this.config.apiKey,
      'anthropic-version': '2023-06-01',
    };
  }

  async testConnection(): Promise<boolean> {
    if (!this.isAvailable()) return false;
    try {
      const res = await fetch(`${this.config.baseUrl}/v1/models`, {
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
      const res = await fetch(`${this.config.baseUrl}/v1/models`, {
        headers: this.buildHeaders(),
        signal: AbortSignal.timeout(10_000),
      });
      if (!res.ok) return [];
      const data = (await res.json()) as AnthropicModelsResponse;
      return (data.data ?? []).map((m) => ({
        id: m.id,
        provider: this.config.name,
        displayName: m.display_name || m.id,
        maxTokens: 200_000,
        supportsTools: true,
        supportsVision: m.id.includes('vision'),
      }));
    } catch {
      return [];
    }
  }

  async complete(req: LLMCompletionRequest): Promise<LLMCompletionResponse> {
    const model = req.model || this.config.defaultModel;
    if (!model) {
      throw new Error('Anthropic: no model specified. Set ANTHROPIC_MODEL env var or pass model in request.');
    }

    const systemMessages = req.messages.filter((m) => m.role === 'system');
    const nonSystemMessages = req.messages.filter((m) => m.role !== 'system');
    const system = systemMessages.map((m) => m.content).join('\n');

    const body: Record<string, unknown> = {
      model,
      max_tokens: req.maxTokens ?? 4096,
      messages: nonSystemMessages.map((m) => ({
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: m.content,
      })),
      ...(req.temperature !== undefined ? { temperature: req.temperature } : {}),
      ...(req.topP !== undefined ? { top_p: req.topP } : {}),
      ...(req.stop?.length ? { stop_sequences: req.stop } : {}),
      ...(req.tools?.length ? { tools: req.tools } : {}),
    };

    if (system) {
      body.system = system;
    }

    const res = await this.withRetry(() =>
      this.fetch(`${this.config.baseUrl}/v1/messages`, body),
    );

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      throw new Error(`Anthropic API error ${res.status}: ${errText.slice(0, 200)}`);
    }

    const data = (await res.json()) as AnthropicResponse;

    const textContent = data.content
      .filter((b) => b.type === 'text')
      .map((b) => b.text || '')
      .join('');

    const toolCalls = data.content
      .filter((b) => b.type === 'tool_use')
      .map((b) => ({
        id: b.id || '',
        type: 'function' as const,
        function: {
          name: b.name || '',
          arguments: JSON.stringify(b.input || {}),
        },
      }));

    return {
      id: data.id,
      model: data.model,
      provider: this.config.name,
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: textContent,
            ...(toolCalls.length ? { toolCalls } : {}),
          },
          finishReason: data.stop_reason === 'end_turn' ? 'stop'
            : data.stop_reason === 'max_tokens' ? 'length'
            : data.stop_reason === 'tool_use' ? 'tool_calls'
            : 'stop',
        },
      ],
      usage: data.usage
        ? {
            promptTokens: data.usage.input_tokens,
            completionTokens: data.usage.output_tokens,
            totalTokens: data.usage.input_tokens + data.usage.output_tokens,
          }
        : undefined,
    };
  }

  async completeStream(
    req: LLMCompletionRequest,
    onChunk: (text: string) => void,
  ): Promise<LLMCompletionResponse> {
    const model = req.model || this.config.defaultModel;
    if (!model) {
      throw new Error('Anthropic: no model specified. Set ANTHROPIC_MODEL env var or pass model in request.');
    }

    const systemMessages = req.messages.filter((m) => m.role === 'system');
    const nonSystemMessages = req.messages.filter((m) => m.role !== 'system');
    const system = systemMessages.map((m) => m.content).join('\n');

    const body: Record<string, unknown> = {
      model,
      max_tokens: req.maxTokens ?? 4096,
      stream: true,
      messages: nonSystemMessages.map((m) => ({
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: m.content,
      })),
      ...(req.temperature !== undefined ? { temperature: req.temperature } : {}),
      ...(req.tools?.length ? { tools: req.tools } : {}),
    };

    if (system) {
      body.system = system;
    }

    const res = await this.withRetry(() =>
      this.fetch(`${this.config.baseUrl}/v1/messages`, body),
    );

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      throw new Error(`Anthropic stream error ${res.status}: ${errText.slice(0, 200)}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let fullContent = '';
    let buffer = '';
    let currentEvent = '';
    let inputTokens = 0;
    let outputTokens = 0;
    let stopReason: string | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;
          try {
            const event = JSON.parse(jsonStr) as AnthropicStreamEvent;

            if (event.type === 'content_block_delta' && event.delta) {
              const delta = event.delta as { text?: string };
              if (delta.text) {
                fullContent += delta.text;
                onChunk(delta.text);
              }
            } else if (event.type === 'message_delta') {
              const d = event.delta as { stop_reason?: string } || {};
              if (d.stop_reason) stopReason = d.stop_reason;
              if (event.usage?.output_tokens) {
                outputTokens = event.usage.output_tokens;
              }
            } else if (event.type === 'message_start' && event.message) {
              inputTokens = event.message.usage?.input_tokens || 0;
            }
          } catch {
            // skip unparseable chunks
          }
        }
      }
    }

    return {
      id: `anthropic-${Date.now()}`,
      model,
      provider: this.config.name,
      choices: [
        {
          index: 0,
          message: { role: 'assistant', content: fullContent },
          finishReason: stopReason === 'end_turn' ? 'stop'
            : stopReason === 'max_tokens' ? 'length'
            : stopReason === 'tool_use' ? 'tool_calls'
            : 'stop',
        },
      ],
      usage: {
        promptTokens: inputTokens,
        completionTokens: outputTokens,
        totalTokens: inputTokens + outputTokens,
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