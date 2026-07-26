# CantioDAW

**AI 驱动的歌声制作 DAW**

从音色训练到音乐制作的完整管线，基于 CantioAI 构建。

## 管线

```
音频数据集 → 声音训练 → 加载模型 → 创作 MIDI + 歌词 → 合成 → 混音 → 导出
                    ↑                          ↑
               SVC / RVC  ← 自动检测 — 模型格式适配器
```

## 快速开始

```bash
# 安装
pip install -e .

# 使用任意模型格式（自动检测）
cantiodaw synthesize --model so-vits-svc/G_10000.pth \
  --config so-vits-svc/config.json --pitch 60 -o output.wav

# 启动 Web UI
cantiodaw serve
# 或: python -m cantiodaw serve

# 打开 http://127.0.0.1:8080
```

## CLI 使用

```bash
# 创建项目
cantiodaw project create --name MySong

# 列出项目
cantiodaw project list

# 训练声音模型
cantiodaw train --voice MyVoice --data-dir data/voices/my_voice --epochs 50

# 合成（自动检测格式）
cantiodaw synthesize --model checkpoints/MyVoice/best_model.safetensors \
  --config config.yaml --pitch 60 --duration 2.0 -o output.wav

# 检测模型格式
cantiodaw detect --model so-vits-svc/G_10000.pth

# 导出项目音频
cantiodaw project export --name MySong -o mix.wav
```

## Web UI 功能

- 项目管理（创建、保存、加载）
- 音轨管理（添加、删除、选中）
- 模型加载（.pt / .safetensors / .pth）
- 声音训练及实时进度
- WAV 导出

## 架构

- **Project Manager** — `.cantio` JSON 文件持久化项目
- **Audio Engine** — 通过 sounddevice/soundfile 实现播放、录音、加载
- **MIDI Engine** — 音符/音高/F0 转换工具
- **Mixer** — 多轨混音及效果链
- **Voice Trainer** — 封装 CantioAI 训练管线，支持 LoRA
- **SVS Engine** — MIDI 音符 + 歌词 → 歌声音频（通过自动检测的模型适配器）
- **Model Format Detector** — 检查模型文件（.pth / .pt / .safetensors / .onnx）和配置，识别 so-vits-svc、RVC v1/v2 或 CantioDAW HybridSVC
- **Model Adapter** — 统一 `synthesize(phoneme_features, f0, spk_id)` 接口，将 SVC/RVC 配置映射到内部配置
- **Audio Effects** — 混响、均衡器、压缩器、增益、归一化
- **Web UI** — 基于 Flask 的 REST API + SSE 训练进度

## 支持的模型格式

| 格式 | 检测特征 | 配置来源 | 推理方式 |
|------|----------|----------|----------|
| **CantioDAW HybridSVC** (`.safetensors`/`.pt`) | `phoneme_feature_dim` / `spectral_envelope_dim` 键 | `config.yaml` | 原生 WORLD + 神经声码器 |
| **so-vits-svc** (`.pth`) | `inter_channels` / `filter_channels` / `n_heads` 键 | `config.json` | 自动适配 → HybridSVC |
| **RVC v1** (`.pth`, 256 维) | `generator.` / `emb_g` 键，256 维特征 | `config.json` | 自动适配 → HybridSVC |
| **RVC v2** (`.pth`, 768 维) | `generator.` / `dec.4` / `794` 键，768 维特征 | `config.json` | 自动适配 → HybridSVC |

## Python API

```python
from cantiodaw import detect_model_format, adapt_config, create_adapter

# 检测格式
fmt = detect_model_format("model.pth", "config.json")
# → "cantiodaw_hybrid_svc" | "so_vits_svc" | "rvc_v1" | "rvc_v2"

# 获取适配后的配置
config = adapt_config("model.pth", "config.json")

# 创建并使用适配器
adapter = create_adapter("model.pth", "config.json")
waveform = adapter.synthesize(phoneme_features, f0, spk_id)
```

## 依赖

- Python 3.9+
- PyTorch 2.0+
- NumPy
- soundfile
- Flask
- PyYAML

可选:
- sounddevice（播放/录音）
- librosa（音频加载）
- mido（MIDI 导出）
- pyworld（WORLD 分析）
- scipy（音频效果）
- onnxruntime（ONNX 推理）
- safetensors（安全检查点格式）

## TS Orchestrator

TypeScript 编排层位于 `ts-orchestrator/`，为 CantioDAW 提供 MCP (Model Context Protocol) 支持，通过 29 个工具（19 DAW + 10 LLM）供 AI 助手调用。

详见 [ts-orchestrator/README.md](ts-orchestrator/README.md)。

## 许可证

Apache 2.0
