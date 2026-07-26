import { LLMRouter } from './router.js';
import { OllamaProvider } from './providers/ollama.js';
import { OpenAIProvider } from './providers/openai.js';
import { AnthropicProvider } from './providers/anthropic.js';

const DEFAULT_OLLAMA_KEY = 'c7014dccda9c4510b50e58a938e04c16.wwdH7UhiNAB8BMuNYNggmyHQ';

export function createDefaultRouter(): LLMRouter {
  const router = new LLMRouter({
    strategy: 'priority',
    fallback: true,
    timeout: 120_000,
    maxRetries: 2,
  });

  const ollamaKey = process.env.OLLAMA_API_KEY || DEFAULT_OLLAMA_KEY;
  const ollama = new OllamaProvider({
    apiKey: ollamaKey,
    defaultModel: process.env.OLLAMA_MODEL || 'gemma4:31b',
    priority: 10,
  });
  router.register(ollama);

  const openaiKey = process.env.OPENAI_API_KEY || '';
  if (openaiKey) {
    const openai = new OpenAIProvider({
      apiKey: openaiKey,
      defaultModel: process.env.OPENAI_MODEL || 'gpt-4o',
      priority: 20,
    });
    router.register(openai);
  }

  const anthropicKey = process.env.ANTHROPIC_API_KEY || '';
  if (anthropicKey) {
    const anthropic = new AnthropicProvider({
      apiKey: anthropicKey,
      defaultModel: process.env.ANTHROPIC_MODEL || '',
      priority: 15,
    });
    router.register(anthropic);
  }

  return router;
}

export { LLMRouter } from './router.js';
export { LLMProvider } from './provider.js';
export { OllamaProvider } from './providers/ollama.js';
export { OpenAIProvider } from './providers/openai.js';
export type * from './types.js';
