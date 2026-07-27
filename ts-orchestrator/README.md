# CantioDAW TS Orchestrator

TypeScript 编排层 — 为 CantioDAW 提供 LLM + 音频分析 + 扒谱 + 原声改编工具链，通过 MCP (Model Context Protocol) 暴露 66 个工具。

## 架构

```
┌──────────────────────────────────────────────────────┐
│                 LLM Host (Claude Desktop 等)          │
│  MCP JSON-RPC over stdio                              │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              CantioDAW MCP Server (66 tools)          │
│  ┌─────────────────┐  ┌──────────────────────────┐   │
│  │  50 DAW Tools   │  │  16 LLM Tools            │   │
│  │  project, track, │  │  chat, lyrics, compose,  │   │
│  │  midi, synth,    │  │  arrange, analyze,       │   │
│  │  analyze,        │  │  transcribe, adapt       │   │
│  │  transcribe,     │  │                          │   │
│  │  separate        │  │                          │   │
│  └────────┬────────┘  └───────────┬──────────────┘   │
│           │                       │                   │
└───────────┼───────────────────────┼───────────────────┘
            │                       │
┌───────────▼───────────────────────▼───────────────────┐
│  Python Bridge (stdin/stdout JSON)                    │
│  ┌────────────────┐  ┌────────────────────────────┐  │
│  │ CantioDAW 核心  │  │ Integrated Demucs v4       │  │
│  │ project, midi,  │  │ (HTDemucs source sep)     │  │
│  │ svs, training,  │  │                            │  │
│  │ audio effects,  │  │ Audio Analysis             │  │
│  │ SoundFont synth │  │ BPM / Key / Chroma /       │  │
│  │ (osc fallback)  │  │ Spectral / Beat / RMS      │  │
│  └────────────────┘  ├────────────────────────────┤  │
│                      │ Transcription               │  │
│                      │ F0 detection (FFT peak)     │  │
│                      │ Onset detection (spectral)  │  │
│                      │ Chord detection (chroma)    │  │
│                      └────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  LLM Router                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │ Ollama   │ │ OpenAI   │ │ Anthropic             │ │
│  │ Provider │ │ Provider │ │ Provider              │ │
│  └──────────┘ └──────────┘ └──────────────────────┘ │
│  路由策略: priority / cost / manual + 自动回退       │
└──────────────────────────────────────────────────────┘
```

## 66 个 MCP 工具

### 核心 DAW 工具 (50)

| 分类 | 工具 | 说明 |
|------|------|------|
| **项目** | `project_create` / `list` / `load` / `delete` / `export` | 完整 CRUD |
| **音轨** | `track_add` / `remove` / `update` / `add_clip` | 音量/静音/名称/MIDI片段 |
| **MIDI** | `midi_notes_to_f0` / `midi_lyrics_to_phonemes` | 音符→F0, 歌词→音素 |
| **合成** | `synthesize` / `synthesize_midi` | 歌声合成 / SoundFont MIDI合成 |
| **效果** | `effect_apply` | reverb / eq / compressor |
| **混音** | `mix_tracks` / `export_stems` | 混音/导出分轨 |
| **渲染** | `render_preview` / `render_final` | 预览/最终渲染 |
| **训练** | `train_prepare` / `train_start` | 数据准备/模型训练 |
| **版本** | `project_snapshot` / `diff_versions` / `rollback_to_version` / `list_versions` | 版本管理 |
| **反馈** | `feedback_submit` / `feedback_ab_test` / `list_feedback` / `track_replay` / `track_favorite` | 用户评分/AB测试 |
| **参数** | `adjust_dynamics` / `adjust_articulation` / `adjust_vibrato` / `adjust_micro_timing` / `adjust_harmonic_color` / `apply_swing` / `apply_rubato` | 微调参数 |
| **评价** | `analyze_harmony` / `analyze_melody` / `analyze_rhythm` / `analyze_audio` | 质量分析 |
| **修订** | `revision_execute` | 自动修订循环 |
| **复合** | `compose_song` / `train_voice_from_audio` / `apply_voice_to_midi` | 多步工作流 |
| **工具** | `list_soundfonts` / `download_soundfont` / `parameter_reference` / `audio_analyze_deep` / `audio_transcribe` / `separate_audio` | 辅助工具 |

### LLM 工具 (16)

| 工具 | 说明 |
|------|------|
| `llm_chat` | 通用对话，自动路由 |
| `llm_stream` | 流式对话 |
| `llm_generate_lyrics` | 生成歌词（主题/风格/语言/结构） |
| `llm_compose_song` | 端到端：LLM 写词 + 建项目 + 合成 |
| `llm_suggest_arrangement` | AI 编曲建议 |
| `llm_analyze_lyrics` | 歌词情感/主题分析 |
| `llm_compose_music` | 从文字描述编曲 → 合成 WAV |
| `llm_parse_intent` | NL → MusicIR (情绪/能量/风格/场景) |
| `llm_query_knowledge_graph` | 查询音乐知识图谱 |
| `llm_compose_from_intent` | MusicIR → 编曲 → MIDI |
| `llm_analyze_music` | 多领域音乐分析 |
| `llm_request_checkpoint` | 人工确认检查点 |
| **`llm_adapt_to_acoustic`** | **电音→原声改编管线** |
| `llm_list_providers` | 列出 provider |
| `llm_list_models` | 列出可用模型 |
| `llm_usage_stats` | LLM 用量统计 |

## 电音→原声改编管线

完整的自动化管线，将一首电子音乐改编为原声版本。

### 工作流

```
Step 1: audio_analyze_deep     → BPM / 调性 / 频谱 / 结构
Step 2: separate_audio          → Demucs v4 分离人声+伴奏（后台异步）
Step 3: audio_transcribe        → 从纯净人声轨 FFT 扒谱 → MIDI 音符
                                 → Chroma 和弦识别
Step 4: 自动生成伴奏              → 和弦琶音 + 低音贝斯
Step 5: render_final             → SoundFont/oscillator 渲染 → WAV
```

### 使用方式

```bash
# 1. 先分离人声（后台运行, 5-8min CPU）
llm_adapt_to_acoustic  # 或单独调用 separate_audio

# 2. 改编（传入预分离人声轨）
llm_adapt_to_acoustic { 
  "audio_path": "song.flac",
  "vocal_path": "output/song_vocals.wav" 
}
```

### 关键技术

- **Demucs v4 (HTDemucs)**: Meta 的混合 Transformer 音源分离，4 声道（人声/鼓/贝斯/其他）
- **FFT 频谱峰值音高检测**: 从纯净人声提取旋律音高
- **Chroma + Krumhansl 调性识别**: 自动检测调性
- **谱通量 onset 检测**: 自动识别音符起止
- **SoundFont 渲染**: GM 原声乐器 (钢琴/吉他/弦乐/贝斯/长笛等)

## 快速开始

```bash
# 安装
npm install

# 编译
npm run build

# 生产构建
npm run build:prod

# 启动 MCP server
cantiodaw-mcp

# 自测 (28/28 passed)
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
| `OPENAI_API_KEY` | - | OpenAI API 密钥 |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI 默认模型 |
| `CANTIODAW_PYTHON` | `python` | Python 路径 |
| `CANTIODAW_ROOT` | 自动检测 | CantioDAW 项目根目录 |

## 工作流 (8 个)

| 工作流 | ID | 步骤 |
|--------|-----|------|
| 作曲 | `compose_song` | 创建项目 → 加音轨 → 转歌词 → 合成 → 导出 |
| 训练 | `train_voice` | 准备数据集 → 训练模型 |
| 声乐 | `apply_voice` | 歌词转音素 → F0 → 合成 |
| 混音 | `mix_export` | 混音 → 导出分轨 |
| NL编曲 | `compose_from_intent` | NL → MusicIR → 编曲 → MIDI |
| 修改 | `critic_revise` | 分析 → 修订循环 → 预览 |
| 全管线 | `full_pipeline` | NL → 编曲 → 分析 → 修订 → Diff → 渲染 |
| **原声改编** | **`adapt_to_acoustic`** | **分析 → 分离 → 扒谱 → 编曲 → 渲染** |

## 直接编曲 (`llm_compose_music`)

LLM 直接生成结构化 JSON 乐谱，经合成引擎实时生成 WAV。

```
用户描述 → LLM 生成 JSON 乐谱 → 提取 MIDI 音符 → 合成 WAV
```

支持的波形：`sine` | `triangle` | `sawtooth` | `square` | `piano`

## 项目结构

```
ts-orchestrator/
├── src/
│   ├── index.ts                  # 入口
│   ├── bridge/
│   │   ├── python.ts             # Node ↔ Python stdin/stdout JSON
│   │   └── python_bridge.py      # Python 守护进程 (56 个方法)
│   ├── mcp/
│   │   ├── server.ts             # MCP 协议 server
│   │   └── tools.ts              # 50 个 DAW 工具定义
│   ├── llm/
│   │   ├── tools.ts              # 16 个 LLM 工具定义
│   │   ├── router.ts             # 多 provider 路由/回退
│   │   ├── provider.ts           # Provider 抽象基类
│   │   ├── prompts/              # 系统提示词
│   │   └── providers/            # Ollama / OpenAI / Anthropic
│   ├── orchestrator/
│   │   ├── engine.ts             # 工作流执行引擎
│   │   ├── composer.ts           # 编曲生成 (和弦/旋律/贝斯)
│   │   ├── revision.ts           # 修订代理
│   │   └── workflows.ts          # 8 个预定义工作流
│   ├── music/
│   │   ├── ir.ts                 # MusicIR 中间表示
│   │   └── labels.ts             # 情绪/场景/风格标签
│   └── types/                    # 领域类型定义
├── scripts/
├── package.json
├── tsconfig.json
└── README.md
```

## 依赖

- Node.js >= 18
- Python >= 3.9 (CantioDAW + Demucs)
- torch >= 1.8, torchaudio
- @modelcontextprotocol/sdk — MCP 协议
- D:\demucs-main — 集成 Demucs v4 (HTDemucs)

## 发布构建

```bash
npm run release
# 输出: ../release/cantiodaw-mcp.exe + python_bridge.py + README
```
