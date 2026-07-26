export type LLMRole = 'system' | 'user' | 'assistant' | 'tool';

export interface LLMMessage {
  role: LLMRole;
  content: string;
  name?: string;
  toolCallId?: string;
}

export interface LLMToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface LLMCompletionRequest {
  model: string;
  messages: LLMMessage[];
  maxTokens?: number;
  temperature?: number;
  topP?: number;
  stop?: string[];
  stream?: boolean;
  tools?: Array<{
    type: 'function';
    function: {
      name: string;
      description: string;
      parameters: Record<string, unknown>;
    };
  }>;
}

export interface LLMCompletionResponse {
  id: string;
  model: string;
  provider: string;
  choices: Array<{
    index: number;
    message: {
      role: 'assistant';
      content: string;
      toolCalls?: LLMToolCall[];
    };
    finishReason: 'stop' | 'length' | 'tool_calls' | 'error';
  }>;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface LLMModelInfo {
  id: string;
  provider: string;
  displayName: string;
  maxTokens: number;
  supportsTools: boolean;
  supportsVision: boolean;
  costPer1kPrompt?: number;
  costPer1kCompletion?: number;
}

export interface LLMProviderConfig {
  name: string;
  apiKey: string;
  baseUrl: string;
  defaultModel: string;
  models: string[];
  priority?: number;
  timeout?: number;
  maxRetries?: number;
}

export type RouterStrategy = 'priority' | 'cost' | 'capability' | 'manual';

export interface RouterConfig {
  strategy: RouterStrategy;
  fallback: boolean;
  timeout: number;
  maxRetries: number;
  usageLogPath?: string;
}

export interface LLMUsageRecord {
  provider: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  timestamp: number;
  duration: number;
  success: boolean;
}
