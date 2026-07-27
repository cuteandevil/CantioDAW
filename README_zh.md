<div align="center">

# CantioDAW · AI 智能体音乐制作框架

**AI 驱动的歌声/音乐制作管线** — 离线批处理，生成 MIDI + 音频导入 DAW。

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

<br>

<a href="README.md">English</a> ｜ <a href="README_zh.md">简体中文</a>

<br>

<a href="#快速开始">快速开始</a> ｜
<a href="#配置指南">配置指南</a> ｜
<a href="#工具列表">工具 (66)</a> ｜
<a href="#核心功能">核心功能</a> ｜
<a href="#架构">架构</a> ｜
<a href="https://github.com/cuteandevil/CantioDAW/releases">发行版</a>

</div>

---

## 快速开始

### 1. 下载
从 [Releases](https://github.com/cuteandevil/CantioDAW/releases/latest) 获取最新版本。

### 2. 安装 Python 依赖
```bash
pip install torch torchaudio soundfile numpy mido scipy
```

### 3. 解压并配置
```bash
unzip demucs.zip
# 创建 .env 配置文件（见下方）
notepad .env
```

### 4. 运行
```bash
cantiodaw-mcp.exe --test    # 自检
cantiodaw-mcp.exe            # 启动 MCP 服务
cantiodaw-mcp.exe toollist   # 列出全部 66 个工具
```

---

## 配置指南

在 `cantiodaw-mcp.exe` 同级目录创建 `.env` 文件：

```env
# LLM 功能必填
OLLAMA_API_KEY=your_ollama_cloud_api_key
OLLAMA_MODEL=gemma4:31b

# 可选
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-3-opus-20240229

# Python 路径（如果不在 PATH 中）
CANTIODAW_PYTHON=python
```

### API Key 获取

| 提供商 | 注册地址 | 说明 |
|--------|----------|------|
| **Ollama Cloud** | [ollama.com](https://ollama.com) | LLM 功能必填，有免费额度 |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | 可选，推荐 `gpt-4o` |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com) | 可选 |

> 未配置 LLM API Key 时，16 个 LLM 工具将提示 "LLM router not available"，但 50 个 DAW 工具仍可正常使用。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_API_KEY` | — | Ollama Cloud API 密钥 (**LLM 功能必填**) |
| `OLLAMA_MODEL` | `gemma4:31b` | Ollama 模型名 |
| `OPENAI_API_KEY` | — | OpenAI API 密钥 (可选) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI 模型 |
| `ANTHROPIC_API_KEY` | — | Anthropic API 密钥 (可选) |
| `ANTHROPIC_MODEL` | — | Anthropic 模型 |
| `CANTIODAW_PYTHON` | `python` | Python 可执行文件路径 |
| `CANTIODAW_ROOT` | 自动检测 | CantioDAW 项目根目录 |

### 系统要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | 必装 |
| PyTorch | 2.0+ | `pip install torch` |
| torchaudio | 0.9+ | `pip install torchaudio` |
| Node.js | 18+ | 已打包在 .exe 中 |
| CUDA GPU | 可选 | 加速 Demucs 推理 |
| 内存 | 8 GB+ | 大文件建议 16 GB |
| 磁盘 | 2 GB+ | 模型缓存 + 音频文件 |

---

## 核心功能

### 电音 → 原声改编
```bash
# 第 1 步：分离人声（后台运行, CPU 约 5-8 分钟）
separate_audio { "audio_path": "song.flac" }

# 第 2 步：基于纯净人声轨改编
llm_adapt_to_acoustic {
  "audio_path": "song.flac",
  "vocal_path": "separated/song_vocals.wav"
}
```
完整管线：分析 → Demucs v4 分离 → FFT 扒谱 → 自动编曲 → 渲染

### AI 作曲
```bash
llm_compose_music {
  "description": "一首电影感钢琴曲，情感丰富，120 BPM，C 小调"
}
```

### 歌声合成
```bash
# 训练声音模型
train_voice_from_audio { "voice_name": "my_voice", "data_dir": "data/voice_samples" }

# 合成歌声
synthesize { "model_path": "models/my_voice.pth", "config_path": "config.yaml", "pitch": 60 }
```

---

## 工具列表 (66)

### 项目管理 (9)
| 工具 | 说明 |
|------|------|
| `project_create` | 创建项目 |
| `project_list` | 列出项目 |
| `project_load` | 加载项目详情 |
| `project_delete` | 删除项目 |
| `project_export` | 导出为音频 |
| `track_add` | 添加音频/MIDI 轨 |
| `track_remove` | 删除轨道 |
| `track_update` | 更新轨道 (音量/静音/名称) |
| `track_add_clip` | 添加片段 (MIDI/和弦/音频) |

### MIDI 与合成 (6)
| 工具 | 说明 |
|------|------|
| `midi_notes_to_f0` | MIDI 音符 → F0 包络 |
| `midi_lyrics_to_phonemes` | 歌词 → 音素 |
| `synthesize` | 歌声合成 (MIDI + 模型) |
| `synthesize_midi` | SoundFont / 振荡器合成 |
| `list_soundfonts` | 列出 SoundFont 文件 |
| `download_soundfont` | 下载 FluidR3_GM.sf2 |

### 音频分析与扒谱
| 工具 | 说明 |
|------|------|
| `audio_analyze_deep` | BPM、调性、频谱、节拍、结构分析 |
| `audio_transcribe` | HPS 音高 + 起止点 + 和弦识别 |
| `separate_audio` | Demucs v4 音源分离 (后台异步) |
| `analyze_audio` | 音频质量分析 |
| `analyze_vocal_quality` | 音高偏差、电音痕迹检测 |
| `adjust_synthesized_pitch` | 局部音高修正 |

### 参数微调 (7)
| 工具 | 说明 |
|------|------|
| `adjust_dynamics` | 力度曲线 |
| `adjust_articulation` | 连奏/断奏、起音时间 |
| `adjust_vibrato` | 颤音深度/速率 |
| `adjust_micro_timing` | 微时序偏移 |
| `adjust_harmonic_color` | 和声色彩/调式 |
| `apply_swing` | 摇摆律动 |
| `apply_rubato` | 弹性速度 |

### 版本与反馈 (9)
| 工具 | 说明 |
|------|------|
| `project_snapshot` | 版本快照 |
| `diff_versions` | 版本对比 |
| `rollback_to_version` | 回滚 |
| `list_versions` | 版本列表 |
| `feedback_submit` | 提交评分 (1-5) |
| `feedback_ab_test` | AB 测试 |
| `list_feedback` | 反馈汇总 |
| `track_replay` | 回放记录 |
| `track_favorite` | 收藏/取消 |

### 渲染 (2)
| 工具 | 说明 |
|------|------|
| `render_preview` | 快速预览 |
| `render_final` | 最终高质量渲染 |

### LLM 工具 (16)
| 工具 | 说明 |
|------|------|
| `llm_chat` | 通用 LLM 对话 |
| `llm_stream` | 流式对话 |
| `llm_generate_lyrics` | AI 歌词生成 |
| `llm_compose_song` | 端到端作曲 |
| `llm_suggest_arrangement` | 编曲建议 |
| `llm_analyze_lyrics` | 歌词分析 |
| `llm_compose_music` | 从描述直接编曲 |
| `llm_parse_intent` | 自然语言 → MusicIR |
| `llm_query_knowledge_graph` | 知识图谱查询 |
| `llm_compose_from_intent` | IR → 编曲 + MIDI |
| `llm_analyze_music` | 多领域乐评 |
| `llm_request_checkpoint` | 人工检查点 |
| `llm_list_providers` | 列出 LLM 提供商 |
| `llm_list_models` | 列出可用模型 |
| `llm_usage_stats` | 用量统计 |
| **`llm_adapt_to_acoustic`** | **电音 → 原声改编** |

---

## 架构

```
自然语言
   ↓
┌──────────────────────────────────────────┐
│  意图解析    NL → Music Semantic IR        │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  作曲智能体   IR → 编曲方案                 │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  参数映射     IR → 参数增量                 │
└──────────────────┬───────────────────────┘
                   ↓
        MIDI 生成 / 轨道管理
                   ↓
┌──────────────────────────────────────────┐
│  乐评 (5模块) + 修订 (自动循环)             │
└──────────────────┬───────────────────────┘
                   ↓
           人工偏好反馈
```

## 限制

- **离线批处理** — 不能替代实时 DAW
- **LLM 作曲质量** — 取决于模型和提示词
- **CPU Demucs 速度较慢** — 大文件建议使用 GPU

---

<div align="center">

© 2025-2026 CantioDAW. All Rights Reserved.

</div>
