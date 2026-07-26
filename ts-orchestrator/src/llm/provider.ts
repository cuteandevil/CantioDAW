import type {
  LLMCompletionRequest,
  LLMCompletionResponse,
  LLMModelInfo,
  LLMProviderConfig,
} from './types.js';

export abstract class LLMProvider {
  readonly config: LLMProviderConfig;

  constructor(config: LLMProviderConfig) {
    this.config = config;
  }

  abstract get name(): string;

  abstract complete(req: LLMCompletionRequest): Promise<LLMCompletionResponse>;

  abstract completeStream(
    req: LLMCompletionRequest,
    onChunk: (text: string) => void,
  ): Promise<LLMCompletionResponse>;

  abstract listModels(): Promise<LLMModelInfo[]>;

  abstract testConnection(): Promise<boolean>;

  protected buildHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${this.config.apiKey}`,
    };
  }

  protected async fetch(url: string, body: unknown, signal?: AbortSignal): Promise<Response> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.config.timeout ?? 60_000);
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify(body),
        signal: signal ?? controller.signal,
      });
      return res;
    } finally {
      clearTimeout(timeout);
    }
  }

  isAvailable(): boolean {
    return !!this.config.apiKey && this.config.apiKey.length > 0;
  }
}
