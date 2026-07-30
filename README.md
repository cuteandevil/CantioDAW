<div align="center">

# CantioDAW · The AI Producer

**描述一首歌。AI 写编曲，用神经合成乐器演奏，自己批评自己直到满意。没有钢琴卷帘、没有时间线、没有手动混音——只有你的创意和一条命令。**

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

<br>

<a href="README.md">English</a> | <a href="README_zh.md">简体中文</a>

<br>

<a href="#quick-start">快速开始</a> |
<a href="#download">下载</a> |
<a href="#features">功能特性</a> |
<a href="#tools">工具 (80)</a> |
<a href="https://github.com/cuteandevil/CantioDAW/releases">发布页</a>

</div>

---

## 下载

**[下载 v0.2.0](https://github.com/cuteandevil/CantioDAW/releases/tag/v0.2.0)** — 一体化打包，无需额外下载。

| 文件 | 大小 | 说明 |
|------|------|------|
| CantioDAW.exe | 128 MB | 独立 DAW 桌面应用 (PyQt GUI) |
| cantiodaw-mcp.exe | 88 MB | 混淆后的 MCP 服务器 (80 工具) |
| python_bridge.py | 95 KB | Python 桥 (56 DAW 方法 + Demucs v4 + FluidSynth) |
| demucs.zip | 79 KB | Demucs v4 HTDemucs 源分离 (35 .py) |
| soundfonts.zip | 27 MB | GeneralUser GS SoundFont (145 GM 乐器) |
| fluidsynth_dlls.zip | 1.5 MB | FluidSynth 运行时 DLL |
| CantioDAW-v0.2.0-win64.zip | 245 MB | 以上全部 + 一键解压 |

---

## 快速开始

### 1. CantioDAW.exe — 桌面 DAW 应用

全功能 PyQt6 桌面应用，支持项目管理、MIDI 编辑、声音训练和混音。运行 `CantioDAW.exe gui` 启动图形界面，或访问 Web UI `http://127.0.0.1:8080`。

### 2. cantiodaw-mcp.exe — AI 代理接口 (MCP 服务器)

MCP (Model Context Protocol) 服务器，向 Claude、Cursor 等 AI 代理暴露全部 80 个工具。通过 stdio 通信——你的 AI 代理直接操控 CantioDAW。

**Python 依赖:** `pip install torch torchaudio soundfile numpy mido scipy`

**LLM 供应商（三选一）：** Ollama Cloud（免费版可用）、OpenAI 兼容 API 或 Anthropic。设置对应的 `*_API_KEY` 环境变量或放入 `.env` 文件。

**可选:** `pip install demucs` 用于音源分离。AI 推理建议使用 CUDA GPU。

---

## 功能特性

### 神经合成引擎 (DDSP)

输入 MIDI 音符，输出富有表现力的音频。**DDSP 神经合成引擎**渲染 15 种乐器，带有人性化的吐字、力度、颤音和微 timing——由 **PerformanceHead** 将演奏意图映射为物理合成参数（tau、气息、瞬态衰减）。无需采样库，无需 MIDI CC 编程——只需描述你想要的声音。

**演奏表情管线:**

```
LLM 意图 → MusicIR → 编曲方案 → 演奏意图 → DDSP 参数 → 音频
```

内置六种表情预设（连奏、断奏、重音、次断奏、拨弦、颤音），支持连续参数调节。

### 真实乐器渲染 (SoundFont)

内置 **FluidSynth** + **GeneralUser GS** SoundFont（145 种 GM 乐器）。所有 MIDI 轨自动通过真实采样乐器渲染——大钢琴、尼龙弦吉他、小提琴、大提琴、弦乐合奏、长笛、原声贝司等。支持音色/库选择。

### AI 作曲与编配

用自然语言描述音乐——LLM 解析你的意图为结构化 **MusicIR**（情绪、能量、风格、场景、配器），然后生成完整的编曲方案，包含段落、和弦、旋律和乐器分配。

```
"电影感钢琴曲，感情丰富，C 小调"
  → MusicIR → 编曲方案 → MIDI → DDSP/SoundFont → WAV
```

### 智能批评与修订系统

四个专业批评家分析输出:
- **和声批评家** — 和弦进行、声部连接、紧张度
- **旋律批评家** — 轮廓、乐句结构、动机发展
- **节奏批评家** — 律动、切分、时值一致性
- **音频批评家** — 频谱平衡、动态、伪影、底噪

**修订代理**运行诊断-修复-验证循环，带收敛控制，自动改进输出直到达到质量标准。

### 声音训练与合成

从音频样本训练声音模型（支持 LoRA 微调），然后通过 MIDI 音符 + 歌词合成歌声，支持音素对齐。

### 音源分离

集成 **Demucs v4 (HTDemucs)**，分离人声和伴奏，用于混音、原声改编或歌词转录。

### 录音室级混音与效果

多轨混音、混响、EQ、压缩、增益控制，导出为 WAV/FLAC，44.1 kHz / 24-bit。

### 版本管理与人工反馈

快照每个项目状态、版本间差异对比、回滚、人工评分 (1-5)、A/B 测试、播放次数追踪。系统从你的偏好中学习。

### 电子 → 原声改编

将电子音乐改编为原声编曲。Demucs 分离音轨，LLM 重新编配为真实乐器，FluidSynth 渲染输出。

---

## 工具 (80)

| 分类 | 数量 | 关键工具 |
|------|------|----------|
| DAW 桌面应用 | 1 | CantioDAW.exe (PyQt GUI) |
| 项目与音轨 | 9 | 创建、添加、更新、片段 |
| MIDI 与合成 | 6 | 基频、音素、SoundFont 合成 |
| 音频分析 | 6 | 深度分析、扒谱、Demucs 分离 |
| 演奏表情 | 7 | 力度、吐字、颤音、摇摆、自由速度、微调、和声色彩 |
| 版本与反馈 | 9 | 快照、差异、回滚、评分、A/B 测试、收藏 |
| 渲染与导出 | 2 | 预览、最终、分轨导出 |
| LLM 作曲 | 17 | 作曲、歌词、分析、改编、对话、流式、钢琴编曲 |
| MCP 工具集 | 11 | 音色库、下载、模型列表、参数参考 |
| 修订与检查点 | 4 | 修订、诊断、检查点、人工介入 |

完整列表: 运行 `cantiodaw-mcp.exe toollist` 或查看[发布页](https://github.com/cuteandevil/CantioDAW/releases)。

---

## 系统要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | python_bridge.py 必需 |
| PyTorch | 2.0+ | pip install torch torchaudio |
| 内存 | 8 GB+ | 运行 Demucs 建议 16 GB |
| 硬盘 | 2 GB+ | 模型缓存 + 音频 + SoundFont |
| CUDA GPU | 可选 | 加速 Demucs 和 DDSP |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| OLLAMA_API_KEY | — | Ollama Cloud 密钥 |
| OLLAMA_MODEL | gemma4:31b | Ollama 模型名 |
| OPENAI_API_KEY | — | OpenAI 兼容 API 密钥 |
| ANTHROPIC_API_KEY | — | Anthropic API 密钥 |
| LLM_PROVIDER | ollama | 当前供应商: ollama / openai / anthropic |
| CANTIODAW_PYTHON | python | Python 可执行路径 |
| CANTIODAW_ROOT | (父目录) | CantioDAW 项目根目录 |

在 `cantiodaw-mcp.exe` 同级创建 `.env` 文件存放 API 密钥。

---

<div align="center">

(c) 2025-2026 CantioDAW. 保留所有权利。

</div>
