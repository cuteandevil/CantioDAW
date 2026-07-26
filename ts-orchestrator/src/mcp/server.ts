import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { PythonBridge } from '../bridge/python.js';
import { ALL_TOOLS, type ToolDefinition } from './tools.js';
import { LLM_TOOLS } from '../llm/tools.js';
import type { LLMRouter } from '../llm/router.js';

type AnyHandler = (router: LLMRouter | null, bridge: PythonBridge, params: Record<string, unknown>) => Promise<{ success: boolean; data?: unknown; error?: string }>;

interface ToolEntry {
  definition: { name: string; description: string; inputSchema: Record<string, unknown> };
  handler: AnyHandler;
  isLLM: boolean;
}

export class CantioDAWMCPServer {
  private server: Server;
  private bridge: PythonBridge;
  private router: LLMRouter | null = null;
  private allTools: ToolEntry[] = [];

  constructor(bridge: PythonBridge, router?: LLMRouter) {
    this.bridge = bridge;
    this.router = router ?? null;

    for (const t of ALL_TOOLS) {
      this.allTools.push({
        definition: { name: t.name, description: t.description, inputSchema: t.inputSchema },
        handler: (_router, bridge, params) => t.handler(bridge, params),
        isLLM: false,
      });
    }

    for (const t of LLM_TOOLS) {
      this.allTools.push({
        definition: { name: t.name, description: t.description, inputSchema: t.inputSchema },
        handler: (router, bridge, params) => (t as unknown as { handler: AnyHandler }).handler(router!, bridge, params),
        isLLM: true,
      });
    }

    this.server = new Server(
      { name: 'cantiodaw-mcp', version: '0.1.0' },
      { capabilities: { tools: {} } },
    );

    this.setupHandlers();
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: this.allTools.map((t) => t.definition),
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      const entry = this.allTools.find((t) => t.definition.name === name);

      if (!entry) {
        return { content: [{ type: 'text', text: `Unknown tool: ${name}` }], isError: true };
      }

      if (entry.isLLM && !this.router) {
        return { content: [{ type: 'text', text: 'LLM router not available. No LLM provider configured.' }], isError: true };
      }

      const result = await entry.handler(this.router, this.bridge, (args ?? {}) as Record<string, unknown>);

      if (!result.success) {
        return { content: [{ type: 'text', text: result.error ?? 'Unknown error' }], isError: true };
      }

      return {
        content: [{ type: 'text', text: typeof result.data === 'string' ? result.data : JSON.stringify(result.data, null, 2) }],
      };
    });

    this.server.onerror = (error) => console.error('[MCP Error]', error);
  }

  async start(): Promise<void> {
    await this.bridge.ensureRunning();
    if (this.router) {
      const statuses = await this.router.testAll();
      const available = Object.entries(statuses).filter(([, v]) => v).map(([k]) => k);
      console.error(`[cantiodaw-mcp] LLM providers: ${available.join(', ') || 'none'}`);
    }
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error(`[cantiodaw-mcp] MCP server running on stdio (${this.allTools.length} tools)`);
  }

  async stop(): Promise<void> {
    await this.server.close();
    await this.bridge.close();
  }
}
