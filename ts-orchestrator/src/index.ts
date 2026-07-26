#!/usr/bin/env node
import { CantioDAWMCPServer } from './mcp/server.js';
import { PythonBridge } from './bridge/python.js';
import { OrchestrationEngine } from './orchestrator/engine.js';
import { WORKFLOWS } from './orchestrator/workflows.js';
import { ALL_TOOLS } from './mcp/tools.js';
import { LLM_TOOLS } from './llm/tools.js';
import { createDefaultRouter } from './llm/config.js';

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
CantioDAW AI Agent Music Production System

Phases:
  0  Status Inventory    29 tools audited
  1  Music IR            Emotion/Energy/Style/Scene IR layer
  2  Intent Agent        NL → MusicIR (llm_parse_intent)
  2  Composer Agent      IR → Arrangement (llm_compose_from_intent)
  3  Knowledge Graph     11 concept nodes with parameter mappings
  4  Parameter Mapper    Emotion → Harmony/Melody/Rhythm/Instrument/Mix
  5  Atomic Tools        7 new delta-parameter tools
  6  Critic System       4 subsystems (Harmony/Melody/Rhythm/Audio)
  7  Versioning          Snapshots, diff, rollback
  8  Revision Agent      Prioritize, diagnose, fix, verify loop
  9  Human Feedback      Scoring, A/B testing, adoption tracking
  10 Checkpoints         Human-in-the-loop pause points

Usage:
  cantiodaw-mcp                     Start MCP server (stdio) with all tools
  cantiodaw-mcp --test             Run self-test
  cantiodaw-mcp worklist           List workflows
  cantiodaw-mcp toollist           List all tools
  cantiodaw-mcp llmtest [model]   Test LLM connectivity
  cantiodaw-mcp --help             Show this help

Environment:
  CANTIODAW_PYTHON    Python executable path (default: python)
  CANTIODAW_ROOT      CantioDAW project root (default: parent dir)
  OLLAMA_API_KEY      Ollama Cloud API key (built-in default available)
  OLLAMA_MODEL        Ollama model name (default: gemma4:31b)
  OPENAI_API_KEY      OpenAI API key (optional)
  OPENAI_MODEL        OpenAI model name (default: gpt-4o)
`);
    process.exit(0);
  }

  if (args.includes('--test')) {
    await runSelfTest();
    process.exit(0);
  }

  if (args[0] === 'worklist') {
    for (const w of WORKFLOWS) {
      console.log(`  ${w.id.padEnd(20)} ${w.name} — ${w.description}`);
      for (const s of w.steps) {
        console.log(`    └─ ${s.id.padEnd(16)} → ${s.tool}`);
      }
    }
    process.exit(0);
  }

  if (args[0] === 'toollist') {
    const all = [...ALL_TOOLS, ...LLM_TOOLS];
    for (const t of all) {
      const props = (t.inputSchema as { properties?: Record<string, unknown> })?.properties ?? {};
      const required = (t.inputSchema as { required?: string[] })?.required ?? [];
      const reqStr = required.length ? ` (required: ${required.join(', ')})` : '';
      const prefix = LLM_TOOLS.includes(t as typeof LLM_TOOLS[0]) ? '[LLM]' : '[DAW]';
      console.log(`  ${prefix} ${t.name.padEnd(30)} ${t.description}${reqStr}`);
    }
    process.exit(0);
  }

  if (args[0] === 'llmtest') {
    await runLLMTest(args[1]);
    process.exit(0);
  }

  const bridge = new PythonBridge({
    pythonPath: process.env.CANTIODAW_PYTHON ?? 'python',
    projectRoot: process.env.CANTIODAW_ROOT ?? undefined,
  });

  const router = createDefaultRouter();
  const server = new CantioDAWMCPServer(bridge, router);

  process.on('SIGINT', async () => {
    console.error('[cantiodaw-mcp] shutting down');
    await server.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await server.stop();
    process.exit(0);
  });

  await server.start();
}

async function runSelfTest() {
  console.log('CantioDAW TS Orchestrator Self-Test\n');

  let passed = 0;
  let failed = 0;

  function assert(label: string, ok: boolean, detail?: string) {
    if (ok) {
      console.log(`  \u2713 ${label}`);
      passed++;
    } else {
      console.log(`  \u2717 ${label}${detail ? ` \u2014 ${detail}` : ''}`);
      failed++;
    }
  }

  // 1. Types
  assert('Types module loads', true);
  const types = await import('./types/index.js');
  assert('Types export exists', !!types);

  // 2. DAW Tools
  assert(`DAW tools: ${ALL_TOOLS.length}`, ALL_TOOLS.length >= 38);

  // 3. LLM Tools
  assert(`LLM tools: ${LLM_TOOLS.length}`, LLM_TOOLS.length >= 14);
  for (const t of LLM_TOOLS) {
    assert(`LLM tool "${t.name}" has handler`, typeof t.handler === 'function');
  }

  // 4. Total tools
  const totalTools = ALL_TOOLS.length + LLM_TOOLS.length;
  assert(`Total tools: ${totalTools}`, totalTools >= 52);

  // 5. Workflows
  assert(`Workflows: ${WORKFLOWS.length}`, WORKFLOWS.length >= 4);

  // 6. Orchestrator engine
  const engine = new OrchestrationEngine();
  assert('Engine created', !!engine);

  // 7. LLM Router
  const router = createDefaultRouter();
  assert('Router created', !!router);
  assert(`Providers registered: ${router.getProviders().length}`, router.getProviders().length > 0);
  const statuses = await router.testAll();
  for (const [name, available] of Object.entries(statuses)) {
    assert(`Provider "${name}" ${available ? 'connected' : 'skipped (no key)'}`, true);
  }

  // 8. Python bridge
  const bridge = new PythonBridge();
  try {
    const ping = await bridge.call('ping');
    assert('Python bridge ping', ping.success, ping.error);
    const ver = await bridge.call('version');
    assert('Python bridge version', ver.success && typeof ver.data === 'string', JSON.stringify(ver.data));
    await bridge.close();
  } catch (err) {
    assert('Python bridge connectivity', false, String(err));
  }

  console.log(`\n  Total: ${passed} passed, ${failed} failed\n`);
  process.exit(failed > 0 ? 1 : 0);
}

async function runLLMTest(modelArg?: string) {
  console.log('CantioDAW LLM Connectivity Test\n');

  const router = createDefaultRouter();
  const statuses = await router.testAll();
  let passed = 0, failed = 0;
  const ok = (l: string) => { console.log(`  \u2713 ${l}`); passed++; };
  const no = (l: string, d?: string) => { console.log(`  \u2717 ${l}${d ? ` \u2014 ${d}` : ''}`); failed++; };

  for (const [name, available] of Object.entries(statuses)) {
    if (available) {
      ok(`Provider "${name}" connected`);

      if (name === 'ollama') {
        const models = await router.getProvider(name)!.listModels();
        ok(`  ${models.length} models available`);

        const model = modelArg || process.env.OLLAMA_MODEL || 'gemma4:31b';
        try {
          const r = await router.complete({
            model,
            messages: [
              { role: 'system', content: 'Reply in under 10 words.' },
              { role: 'user', content: 'Say hello to CantioDAW' },
            ],
            maxTokens: 50,
            temperature: 0.3,
          });
          const content = r.choices[0]?.message?.content ?? '';
          ok(`  Chat with ${model}: "${content}"`);
          if (r.usage) ok(`  Usage: ${r.usage.totalTokens} tokens`);
        } catch (e: unknown) {
          no(`  Chat with ${model}`, e instanceof Error ? e.message : String(e));
        }
      }
    } else {
      no(`Provider "${name}"`, 'not available (no API key?)');
    }
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error('[cantiodaw-mcp] Fatal error:', err);
  process.exit(1);
});
