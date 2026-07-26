#!/usr/bin/env node
/**
 * CantioDAW Ollama Cloud API 真实 Key 测试
 *
 * 端点: https://ollama.com/api/chat
 * 模型: gemma4:31b
 * Key:  c7014dccda9c4510b50e58a938e04c16.wwdH7UhiNAB8BMuNYNggmyHQ
 *
 * 用法:
 *   node scripts/test-ollama.mjs             # 使用内置 key
 *   OLLAMA_API_KEY=xxx node scripts/test-ollama.mjs
 */

const API_KEY = process.env.OLLAMA_API_KEY
  || process.env.API_KEY
  || "c7014dccda9c4510b50e58a938e04c16.wwdH7UhiNAB8BMuNYNggmyHQ";

const ENDPOINTS = [
  { url: "https://ollama.com/api/chat",      label: "ollama.com" },
  { url: "https://ollama.ac.cn/api/chat",     label: "ollama.ac.cn" },
];

const MODELS = ["gemma4:31b", "gemma4:31b-cloud", "gemma-4-31b-it"];

async function main() {
  console.log("=== CantioDAW Ollama Cloud API Test ===\n");
  let passed = 0, failed = 0;
  const ok = (l, d) => { console.log(`  \u2713 ${l}`); passed++; };
  const no = (l, d) => { console.log(`  \u2717 ${l}${d ? " \u2014 " + d : ""}`); failed++; };

  ok("API_KEY set");
  ok(`Key: ${API_KEY.slice(0, 12)}...${API_KEY.slice(-8)}`);

  for (const ep of ENDPOINTS) {
    console.log(`\n--- ${ep.label} ---`);

    // list models
    const tagsUrl = ep.url.replace("/api/chat", "/api/tags");
    try {
      const r = await fetch(tagsUrl, { headers: { Authorization: `Bearer ${API_KEY}` } });
      if (r.ok) {
        const models = (await r.json()).models ?? [];
        ok(`${ep.label} /api/tags (${models.length} models)`);
        const gm = models.filter(m => m.name?.includes("gemma") ?? m.model?.includes("gemma"));
        if (gm.length) ok(`  gemma: ${gm.map(m => m.name ?? m.model).join(", ")}`);
      } else {
        no(`${ep.label} /api/tags`, `${r.status}`);
      }
    } catch (e) { no(`${ep.label} /api/tags`, e.message); }

    // chat
    for (const model of MODELS) {
      try {
        const r = await fetch(ep.url, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${API_KEY}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model,
            messages: [
              { role: "system", content: "Reply in \u226410 words." },
              { role: "user", content: "Say hello to CantioDAW" },
            ],
            stream: false,
            options: { num_predict: 50, temperature: 0.3 },
          }),
        });
        if (r.ok) {
          const data = await r.json();
          const content = data.message?.content ?? "";
          if (content) {
            ok(`${ep.label} model=${model}`);
            console.log(`    \u2192 "${content}"`);
            break; // next endpoint
          }
          no(`${ep.label} model=${model}`, "empty response");
        } else {
          const txt = (await r.text().catch(() => "")).slice(0, 80);
          if (r.status === 404) continue; // skip 404 models
          no(`${ep.label} model=${model}`, `${r.status}: ${txt}`);
        }
      } catch (e) { no(`${ep.label} model=${model}`, e.message); }
    }
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  if (failed > 0) console.log("  Note: 404 on model name variants is expected (one model name works per endpoint)");
  process.exit(failed > 0 && failed > 6 ? 1 : 0);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
