<div align="center">

# CantioDAW · AI 智能体音乐制作框架

**AI 驱动的歌声/音乐制作管线** — 离线批处理，生成 MIDI + 音频导入 DAW。

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

<br>

<a href="README.md">English</a> | <a href="README_zh.md">简体中文</a>

<br>

<a href="#快速开始">快速开始</a> |
<a href="#下载">下载</a> |
<a href="#核心功能">核心功能</a> |
<a href="#工具列表">工具 (66)</a> |
<a href="https://github.com/cuteandevil/CantioDAW/releases">发行版</a>

</div>

---

## 下载

**[下载 v0.2.0](https://github.com/cuteandevil/CantioDAW/releases/tag/v0.2.0)** — 开箱即用，无需额外下载。

| 文件 | 大小 | 说明 |
|------|------|------|
| `cantiodaw-mcp.exe` | 89.8 MB | 混淆编译 MCP 服务 (66 工具) |
| `python_bridge.py` | 82 KB | Python 桥接 (56 方法 + Demucs v4 + FluidSynth) |
| `demucs.zip` | 79 KB | Demucs v4 音源分离 (35 .py) |
| `soundfonts.zip` | 29.8 MB | GeneralUser GS 音色库 (145 真实乐器) |
| `fluidsynth_dlls.zip` | 11 DLL | FluidSynth 运行库 |

## 快速开始

```bash
# 1. 安装 Python 依赖
pip install torch torchaudio soundfile numpy mido scipy

# 2. 解压所有文件
unzip demucs.zip
unzip soundfonts.zip
unzip fluidsynth_dlls.zip

# 3. 运行
cantiodaw-mcp.exe --test    # 自检 (28/28)
cantiodaw-mcp.exe            # 启动 MCP 服务
cantiodaw-mcp.exe toollist   # 列出 66 工具
```

## 核心功能

### 真实乐器合成
内置 **FluidSynth** + **GeneralUser GS** 音色库 (145 种乐器)。所有 MIDI 轨自动通过真实采样乐器渲染 — 大钢琴、尼龙吉他、小提琴、大提琴、弦乐合奏、长笛、原声贝斯等。

### 电音 → 原声改编
```bash
# 第 1 步：分离人声
separate_audio { "audio_path": "song.flac" }

# 第 2 步：基于纯净人声轨改编
llm_adapt_to_acoustic {
  "audio_path": "song.flac",
  "vocal_path": "separated/song_vocals.wav"
}
```
管线：分析 → Demucs v4 分离 → FFT 扒谱 → 自动编曲 → SoundFont 渲染

### AI 作曲
```bash
llm_compose_music { "description": "一首电影感钢琴曲，情感丰富，C 小调" }
```

### 歌声合成
```bash
train_voice_from_audio { "voice_name": "my_voice", "data_dir": "samples" }
synthesize { "model_path": "model.pth", "config_path": "config.yaml" }
```

## 工具列表 (66)

| 分类 | 数量 | 主要工具 |
|------|------|----------|
| 项目管理 | 9 | create, add, update, clip |
| MIDI 合成 | 6 | f0, phonemes, SoundFont |
| 音频分析 | 6 | 深度分析, 扒谱, Demucs 分离 |
| 参数微调 | 7 | 力度, 连奏, 颤音, 摇摆 |
| 版本反馈 | 9 | 快照, 对比, 回滚, 评分 |
| 渲染 | 2 | 预览, 最终 |
| LLM | 16 | 作曲, 歌词, 分析, 改编 |
| 工具 | 11 | soundfonts, download, reference |

完整列表：见 [发行版](https://github.com/cuteandevil/CantioDAW/releases) 或运行 `cantiodaw-mcp.exe toollist`。

## 系统要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | 必装 |
| PyTorch | 2.0+ | `pip install torch torchaudio` |
| 内存 | 8 GB+ | 建议 16 GB |
| 磁盘 | 2 GB+ | 模型缓存 + 音频 |
| CUDA GPU | 可选 | 加速 Demucs |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_API_KEY` | — | Ollama Cloud 密钥 (LLM 必填) |
| `OLLAMA_MODEL` | `gemma4:31b` | Ollama 模型 |
| `OPENAI_API_KEY` | — | OpenAI 密钥 (可选) |
| `ANTHROPIC_API_KEY` | — | Anthropic 密钥 (可选) |

在 `cantiodaw-mcp.exe` 同级创建 `.env` 文件配置 API 密钥。

---

<div align="center">

(c) 2025-2026 CantioDAW. All Rights Reserved.

</div>
