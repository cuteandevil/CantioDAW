import type {
  LLMCompletionRequest,
  LLMCompletionResponse,
  LLMProviderConfig,
  LLMModelInfo,
  RouterConfig,
  LLMUsageRecord,
} from './types.js';
import { LLMProvider } from './provider.js';
import { OllamaProvider } from './providers/ollama.js';
import { OpenAIProvider } from './providers/openai.js';
import { AnthropicProvider } from './providers/anthropic.js';

export class LLMRouter {
  private providers: Map<string, LLMProvider> = new Map();
  private config: RouterConfig;
  private usageHistory: LLMUsageRecord[] = [];
  private modelCache: LLMModelInfo[] | null = null;

  constructor(routerConfig?: Partial<RouterConfig>) {
    this.config = {
      strategy: routerConfig?.strategy ?? 'priority',
      fallback: routerConfig?.fallback ?? true,
      timeout: routerConfig?.timeout ?? 120_000,
      maxRetries: routerConfig?.maxRetries ?? 2,
    };
  }

  register(provider: LLMProvider): void {
    this.providers.set(provider.config.name, provider);
  }

  registerDefault(): void {
    const ollama = new OllamaProvider();
    if (ollama.isAvailable()) this.register(ollama);

    const openai = new OpenAIProvider();
    if (openai.isAvailable()) this.register(openai);

    const anthropic = new AnthropicProvider();
    if (anthropic.isAvailable()) this.register(anthropic);
  }

  getProvider(name: string): LLMProvider | undefined {
    return this.providers.get(name);
  }

  getProviders(): LLMProvider[] {
    return Array.from(this.providers.values());
  }

  setStrategy(strategy: RouterConfig['strategy']): void {
    this.config.strategy = strategy;
  }

  async testAll(): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};
    for (const [name, provider] of this.providers) {
      results[name] = await provider.testConnection();
    }
    return results;
  }

  async listAllModels(): Promise<LLMModelInfo[]> {
    if (this.modelCache) return this.modelCache;
    const all: LLMModelInfo[] = [];
    for (const provider of this.providers.values()) {
      const models = await provider.listModels();
      all.push(...models);
    }
    this.modelCache = all;
    return all;
  }

  clearModelCache(): void {
    this.modelCache = null;
  }

  async complete(req: LLMCompletionRequest): Promise<LLMCompletionResponse> {
    const provider = this.selectProvider(req);
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        const start = Date.now();
        const result = await provider.complete(req);
        const duration = Date.now() - start;

        this.recordUsage({
          provider: provider.config.name,
          model: result.model,
          promptTokens: result.usage?.promptTokens ?? 0,
          completionTokens: result.usage?.completionTokens ?? 0,
          totalTokens: result.usage?.totalTokens ?? 0,
          timestamp: Date.now(),
          duration,
          success: true,
        });

        return result;
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        this.recordUsage({
          provider: provider.config.name,
          model: req.model || provider.config.defaultModel,
          promptTokens: 0,
          completionTokens: 0,
          totalTokens: 0,
          timestamp: Date.now(),
          duration: 0,
          success: false,
        });

        if (!this.config.fallback) throw lastError;
        if (attempt < this.config.maxRetries) {
          const altProvider = this.getFallbackProvider(provider.config.name);
          if (altProvider) {
            console.error(`[router] ${provider.config.name} failed, falling back to ${altProvider.config.name}: ${lastError.message}`);
            return await altProvider.complete(req);
          }
        }
      }
    }

    throw lastError ?? new Error('All providers failed');
  }

  getUsageHistory(): LLMUsageRecord[] {
    return [...this.usageHistory];
  }

  getUsageSummary(): {
    totalCalls: number;
    successes: number;
    failures: number;
    totalTokens: number;
    byProvider: Record<string, { calls: number; tokens: number }>;
  } {
    const summary = {
      totalCalls: this.usageHistory.length,
      successes: 0,
      failures: 0,
      totalTokens: 0,
      byProvider: {} as Record<string, { calls: number; tokens: number }>,
    };

    for (const record of this.usageHistory) {
      if (record.success) summary.successes++;
      else summary.failures++;
      summary.totalTokens += record.totalTokens;
      if (!summary.byProvider[record.provider]) {
        summary.byProvider[record.provider] = { calls: 0, tokens: 0 };
      }
      summary.byProvider[record.provider].calls++;
      summary.byProvider[record.provider].tokens += record.totalTokens;
    }

    return summary;
  }

  private selectProvider(req: LLMCompletionRequest): LLMProvider {
    if (this.config.strategy === 'manual' && req.model) {
      for (const provider of this.providers.values()) {
        if (provider.config.models.includes(req.model) || provider.config.defaultModel === req.model) {
          return provider;
        }
      }
    }

    if (this.config.strategy === 'cost') {
      const sorted = Array.from(this.providers.values()).sort(
        (a, b) => (a.config.priority ?? 50) - (b.config.priority ?? 50),
      );
      return sorted[0];
    }

    // Priority strategy (default): sort by priority (lower = higher)
    const sorted = Array.from(this.providers.values()).sort(
      (a, b) => (a.config.priority ?? 50) - (b.config.priority ?? 50),
    );
    return sorted[0];
  }

  private getFallbackProvider(excludeName: string): LLMProvider | undefined {
    return Array.from(this.providers.values())
      .filter((p) => p.config.name !== excludeName)
      .sort((a, b) => (a.config.priority ?? 50) - (b.config.priority ?? 50))[0];
  }

  private recordUsage(record: LLMUsageRecord): void {
    this.usageHistory.push(record);
    if (this.usageHistory.length > 1000) {
      this.usageHistory = this.usageHistory.slice(-500);
    }
  }
}
