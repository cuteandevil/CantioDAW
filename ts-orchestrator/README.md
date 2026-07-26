# CantioDAW TS Orchestrator

TypeScript 编排层 — 为 CantioDAW 提供 LLM 工具链支持，通过 MCP (Model Context Protocol) 暴露 29 个工具供 AI 助手调用。

## 架构

```
┌──────────────────────────────────────────────────────┐
│                 LLM Host (Claude Desktop 等)          │
│  MCP JSON-RPC over stdio                              │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              CantioDAW MCP Server                     │
│  ┌─────────────────┐  ┌──────────────────────────┐   │
│  │  19 DAW Tools   │  │  10 LLM Tools            │   │
│  │  (project,      │  │  (chat, lyrics, compose, │   │
│  │   track, midi,  │  │  arrange, analyze,       │   │
│  │   synth, train) │  │  compose_music)          │   │
│  └────────┬────────┘  └───────────┬──────────────┘   │
│           │                       │                   │
└───────────┼───────────────────────┼───────────────────┘
            │                       │
┌───────────▼───────────────────────▼───────────────────┐
│  Python Bridge (stdin/stdout JSON)                    │
│  ┌────────────────┐  ┌────────────────────────────┐  │
│  │ CantioDAW 核心  │  │ synthesizer_midi           │  │
│  │ project, midi,  │  │ (numpy 波形合成器)          │  │
│  │ svs, training,  │  │ sine/triangle/sawtooth/   │  │
│  │ audio effects   │  │ square/piano              │  │
│  └────────────────┘  └────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  LLM Router                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │ Ollama   │ │ OpenAI   │ │ (更多 provider...)    │ │
│  │ Provider │ │ Provider │ │                      │ │
│  │ gemma4   │ │ gpt-4o   │ │                      │ │
│  └──────────┘ └──────────┘ └──────────────────────┘ │
│  路由策略: priority / cost / manual + 自动回退       │
└──────────────────────────────────────────────────────┘
```

## 29 个 MCP 工具

### DAW 工具 (19)

| 分类 | 工具 | 说明 |
|------|------|------|
| **项目** | `project_create` / `list` / `load` / `delete` / `export` | 完整 CRUD |
| **音轨** | `track_add` / `remove` / `update` | 音量/静音/名称 |
| **MIDI** | `midi_notes_to_f0` / `midi_lyrics_to_phonemes` | 音符→F0, 歌词→音素 |
| **合成** | `synthesize` | 用训练模型合成歌声 |
| **效果** | `effect_apply` | reverb / eq / compressor |
| **混音** | `mix_tracks` / `export_stems` | 混音/导出分轨 |
| **训练** | `train_prepare` / `train_start` | 数据准备/模型训练 |
| **复合** | `compose_song` / `train_voice_from_audio` / `apply_voice_to_midi` | 多步工作流 |

### LLM 工具 (10)

| 工具 | 说明 | 必填参数 |
|------|------|---------|
| `llm_chat` | 通用对话，自动路由 provider/model | messages |
| `llm_stream` | 流式对话 | messages |
| `llm_generate_lyrics` | 生成歌词（主题/风格/语言/结构） | theme |
| `llm_compose_song` | 端到端：LLM 写词 + 建项目 + 合成 | theme, project_name, model_path, config_path |
| `llm_suggest_arrangement` | AI 编曲建议 | style |
| `llm_analyze_lyrics` | 歌词情感/主题分析 | lyrics |
| `llm_compose_music` | **直接编曲**：描述 → 结构化乐谱 → 合成音频 | description |
| `llm_list_providers` | 列出已注册 provider | - |
| `llm_list_models` | 列出各 provider 可用模型 | - |
| `llm_usage_stats` | 用量统计 | - |

## 快速开始

```bash
# 安装
npm install

# 编译
npm run build

# 启动 MCP server (连接 Claude Desktop 等 LLM 宿主)
cantiodaw-mcp

# 自测 (22/22 passed)
node dist/index.js --test

# LLM 连通性测试
node dist/index.js llmtest

# 查看工具列表
node dist/index.js toollist

# 查看工作流列表
node dist/index.js worklist
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_API_KEY` | 内置 key | Ollama Cloud API 密钥 |
| `OLLAMA_MODEL` | `gemma4:31b` | Ollama 模型名 |
| `OPENAI_API_KEY` | - | OpenAI API 密钥（可选，有此 key 则自动注册 OpenAI provider） |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI 默认模型 |
| `CANTIODAW_PYTHON` | `python` | Python 路径 |
| `CANTIODAW_ROOT` | 自动检测 | CantioDAW 项目根目录 |

## LLM 路由

```
Router Strategy: priority → cost → manual
Fallback: ✅ 自动切换
Providers: Ollama (gemma4:31b) + OpenAI (可选)
```

路由策略：
- **priority**（默认）：按优先级选 provider（Ollama 优先）
- **cost**：按成本排序
- **manual**：通过 `provider` 参数指定
- 失败时自动 fallback 到下一 provider

## 直接编曲 (`llm_compose_music`)

LLM 直接生成结构化 JSON 乐谱，经 Python 合成引擎实时生成 WAV 音频。

```
用户描述 → LLM 生成 JSON 乐谱 → 提取 MIDI 音符 → 合成 WAV
```

支持的波形：`sine` | `triangle` | `sawtooth` | `square` | `piano`

示例输出生成的编排结构：
```json
{
  "title": "Sunny Day",
  "tempo": 120,
  "key": "C",
  "sections": [
    { "name": "intro",  "bars": 4, "chords": ["C","G","Am","F"], "noteCount": 8 },
    { "name": "verse",  "bars": 8, "chords": ["C","G","Am","F"], "noteCount": 16 },
    { "name": "chorus", "bars": 8, "chords": ["F","C","G","C"],  "noteCount": 24 }
  ],
  "totalNotes": 48,
  "audio": { "output_path": "composed.wav", "duration": 30 }
}
```

## 工作流 (4 个)

| 工作流 | 步骤 |
|--------|------|
| `compose_song` | 创建项目 → 加音轨 → 转歌词 → 合成 → 导出 |
| `train_voice` | 准备数据集 → 训练模型 |
| `apply_voice` | 歌词转音素 → F0 → 合成 |
| `mix_export` | 混音 → 导出分轨 |

## 项目结构

```
ts-orchestrator/
├── src/
│   ├── index.ts                  # 入口 (MCP server / test / llmtest / toollist / worklist)
│   ├── bridge/
│   │   ├── python.ts             # Node ↔ Python stdin/stdout JSON 通信
│   │   └── python_bridge.py      # Python 守护进程 (20 个 DAW 方法)
│   ├── mcp/
│   │   ├── server.ts             # MCP 协议 server (stdio 传输)
│   │   └── tools.ts              # 19 个 DAW 工具定义
│   ├── llm/
│   │   ├── types.ts              # LLM 消息/请求/响应/配置类型
│   │   ├── provider.ts           # LLMProvider 抽象基类
│   │   ├── router.ts             # LLMRouter (多 provider 路由/回退/用量)
│   │   ├── config.ts             # createDefaultRouter()
│   │   ├── tools.ts              # 10 个 LLM 工具定义
│   │   ├── index.ts              # 重导出
│   │   └── providers/
│   │       ├── ollama.ts         # Ollama Cloud Provider (ollama.com/api)
│   │       └── openai.ts         # OpenAI 兼容 Provider
│   ├── orchestrator/
│   │   ├── engine.ts             # 工作流执行引擎
│   │   ├── workflows.ts          # 4 个预定义工作流
│   │   └── index.ts
│   └── types/                    # DAW 领域类型
│       ├── project.ts / midi.ts / audio.ts / training.ts / synthesis.ts
├── scripts/
│   ├── test-ollama.mjs           # Ollama API 连通性测试
│   └── test-compose.mjs          # 编曲流水线测试
├── package.json
├── tsconfig.json
└── README.md
```

## 依赖

- Node.js >= 18
- Python >= 3.9 (需安装 CantioDAW)
- @modelcontextprotocol/sdk — MCP 协议
- zod — 类型校验
