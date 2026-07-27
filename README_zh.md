<div align="center">

# CantioDAW · AI 智能体音乐制作框架

**AI 驱动的歌声/音乐制作管线** — 离线批处理，生成 MIDI + 音频导入 DAW。

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

<br>

[English](README.md) ｜ 简体中文

<br>

<a href="#快速开始">快速开始</a> ｜
<a href="#工具列表">工具列表 (66)</a> ｜
<a href="#管线">管线</a> ｜
<a href="#架构">架构</a> ｜
<a href="https://github.com/cuteandevil/CantioDAW/releases">发行版</a>

</div>

---

## 快速开始

```bash
# 从 https://github.com/cuteandevil/CantioDAW/releases 下载最新版本
# 环境依赖
pip install torch torchaudio soundfile numpy mido scipy

# 解压并运行
unzip demucs.zip
cantiodaw-mcp.exe --test
```

## 架构

```
自然语言
   ↓
┌──────────────────────────────────────────┐
│  意图解析智能体                           │
│  NL → 音乐语义 IR                         │
│  (llm_parse_intent)                       │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  作曲智能体                               │
│  IR → 编曲方案 (结构/旋律/和声/配器)        │
│  (llm_compose_from_intent)                │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  参数映射智能体                           │
│  IR → 参数增量                             │
│  (parameter_mapper.py)                    │
└──────────────────┬───────────────────────┘
                   ↓
        MIDI 生成 / 轨道管理
                   ↓
┌──────────────────────────────────────────┐
│  乐评智能体 (5 模块)                      │
│  和声 / 旋律 / 节奏 / 音频 / 人声          │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  修订智能体                               │
│  诊断 → 修复方案 → 应用 → 复查 (自动循环)   │
│  (revision_execute)                       │
└──────────────────┬───────────────────────┘
                   ↓
           迭代优化循环
                   ↓
           人工偏好反馈
```

## 管线

```
音频数据集 → 声音训练 → 加载模型 → 编曲 MIDI + 歌词 → 合成 → 混音 → 导出
                           ↘                              ↗
                    SVC / RVC → 自动检测 → 模型格式适配
                                               ↗
              SoundFont (SF2/FluidSynth) — 真实乐器合成
```

## 工具列表 (66)

### 项目管理 (9)
| 工具 | 说明 |
|------|------|
| `project_create` | 创建新项目 |
| `project_list` | 列出所有项目 |
| `project_load` | 加载项目详情 |
| `project_delete` | 删除项目 |
| `project_export` | 导出项目为音频 |
| `track_add` | 添加音频/MIDI 轨道 |
| `track_remove` | 删除轨道 |
| `track_update` | 更新轨道属性 |
| `track_add_clip` | 添加片段 (MIDI 音符/和弦/音频) |

### MIDI 与合成 (6)
| 工具 | 说明 |
|------|------|
| `midi_notes_to_f0` | MIDI 音符 → F0 包络 |
| `midi_lyrics_to_phonemes` | 歌词 → 音素 |
| `synthesize` | 歌声合成 (MIDI + 模型) |
| `synthesize_midi` | SoundFont 乐器合成 / 振荡器回退 |
| `list_soundfonts` | 列出可用 SoundFont 文件 |
| `download_soundfont` | 下载 FluidR3_GM.sf2 (144 MB) |

### 音频分析与扒谱
| 工具 | 说明 |
|------|------|
| `audio_analyze_deep` | 深度分析：BPM、调性、频谱、节拍、结构 |
| `audio_transcribe` | 自动扒谱：HPS 音高 + 起止点 + 和弦识别 |
| `separate_audio` | Demucs v4 音源分离 (后台异步) |
| `analyze_audio` | 音频质量分析 |
| `analyze_vocal_quality` | 人声音高偏差、电音痕迹检测 |
| `adjust_synthesized_pitch` | 局部音高修正 |

### 参数微调 (7)
| 工具 | 说明 |
|------|------|
| `adjust_dynamics` | 力度曲线 |
| `adjust_articulation` | 连奏/断奏、起音时间 |
| `adjust_vibrato` | 颤音深度与速率 |
| `adjust_micro_timing` | 微时序偏移 |
| `adjust_harmonic_color` | 和声色彩/调式 |
| `apply_swing` | 摇摆律动 |
| `apply_rubato` | 弹性速度 |

### 版本与反馈 (9)
| 工具 | 说明 |
|------|------|
| `project_snapshot` | 创建版本快照 |
| `diff_versions` | 版本差异对比 |
| `rollback_to_version` | 回滚至指定版本 |
| `list_versions` | 列出所有版本 |
| `feedback_submit` | 提交评分 (1-5) |
| `feedback_ab_test` | AB 测试 |
| `list_feedback` | 反馈汇总 |
| `track_replay` | 记录回放事件 |
| `track_favorite` | 收藏/取消收藏 |

### 渲染 (2)
| 工具 | 说明 |
|------|------|
| `render_preview` | 快速预览渲染 |
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
| `llm_compose_music` | 从文字描述直接编曲 |
| `llm_parse_intent` | 自然语言 → MusicIR |
| `llm_query_knowledge_graph` | 知识图谱查询 |
| `llm_compose_from_intent` | IR → 编曲 + MIDI |
| `llm_analyze_music` | 多领域音乐评价 |
| `llm_request_checkpoint` | 人工检查点 |
| `llm_list_providers` | 列出 LLM 提供商 |
| `llm_list_models` | 列出可用模型 |
| `llm_usage_stats` | 用量统计 |
| **`llm_adapt_to_acoustic`** | **电音 → 原声改编管线** |

## 电音 → 原声改编

```
Step 1: audio_analyze_deep     → BPM / 调性 / 频谱 / 结构
Step 2: separate_audio          → Demucs v4 人声+伴奏 (后台异步)
Step 3: audio_transcribe        → 从纯净人声 FFT 扒谱 → MIDI 音符
                                 → Chroma 和弦识别
Step 4: 自动伴奏                  → 和弦琶音 + 贝斯
Step 5: render_final             → SoundFont/振荡器 → WAV
```

使用详情见 [发行版](https://github.com/cuteandevil/CantioDAW/releases)。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CANTIODAW_PYTHON` | `python` | Python 可执行文件路径 |
| `CANTIODAW_ROOT` | 自动检测 | CantioDAW 项目根目录 |
| `OLLAMA_API_KEY` | 内置 | Ollama Cloud API 密钥 |
| `OLLAMA_MODEL` | `gemma4:31b` | Ollama 模型名 |
| `OPENAI_API_KEY` | — | OpenAI API 密钥 (可选) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI 默认模型 |

## 系统要求

- Python 3.9+, PyTorch 2.0+, Node.js 18+
- `pip install torch torchaudio soundfile numpy mido scipy`
- 可选: `pyfluidsynth` 用于 SoundFont 真实乐器合成
- 可选: CUDA GPU 加速 Demucs 推理

---

<div align="center">

© 2025-2026 CantioDAW. All Rights Reserved.

</div>
