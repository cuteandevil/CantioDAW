<div align="center">

# CantioDAW · AI Agent Music Production Framework

**AI agent-driven vocal/music production pipeline** — offline batch processing, generates MIDI + audio for import into DAWs.

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

<br>

<a href="README.md">English</a> | <a href="README_zh.md">简体中文</a>

<br>

<a href="#quick-start">Quick Start</a> |
<a href="#download">Download</a> |
<a href="#features">Features</a> |
<a href="#tools">Tools (80)</a> |
<a href="https://github.com/cuteandevil/CantioDAW/releases">Releases</a>

</div>

---

## Download

**[Download v0.2.0](https://github.com/cuteandevil/CantioDAW/releases/tag/v0.2.0)** — All-in-one package, no external downloads needed.

| File | Size | Description |
|------|------|-------------|
| CantioDAW.exe | 128 MB | Standalone DAW desktop application (PyQt GUI) |
| cantiodaw-mcp.exe | 88 MB | Obfuscated MCP server (80 tools) |
| python_bridge.py | 95 KB | Python bridge (56 DAW methods + Demucs v4 + FluidSynth) |
| demucs.zip | 79 KB | Demucs v4 HTDemucs source separation (35 .py) |
| soundfonts.zip | 29.8 MB | GeneralUser GS SoundFont (145 real instruments) |
| fluidsynth_dlls.zip | 11 DLLs | FluidSynth runtime libraries |

## Quick Start

`ash
# 1. Install Python dependencies
pip install torch torchaudio soundfile numpy mido scipy

# 2. Extract all zip files
unzip demucs.zip
unzip soundfonts.zip
unzip fluidsynth_dlls.zip

# 3. Run
cantiodaw-mcp.exe --test    # Self-test (28/28)
cantiodaw-mcp.exe            # Start MCP server
cantiodaw-mcp.exe toollist   # List all 80 tools
`

## Features

### Real Instrument Synthesis
Built-in **FluidSynth** + **GeneralUser GS** SoundFont (145 instruments). All MIDI tracks automatically rendered through real sampled instruments — acoustic grand piano, nylon guitar, violin, cello, string ensemble, flute, acoustic bass, and more.

### Electro → Acoustic Adaptation
`ash
# Step 1: Separate vocals
separate_audio { "audio_path": "song.flac" }

# Step 2: Adapt with clean vocal track
llm_adapt_to_acoustic {
  "audio_path": "song.flac",
  "vocal_path": "separated/song_vocals.wav"
}
`
Pipeline: analyze → Demucs v4 separation → FFT transcription → auto arrangement → SoundFont render

### AI Composition
`ash
llm_compose_music { "description": "cinematic piano piece, emotional, C minor" }
`

### Voice Synthesis
`ash
train_voice_from_audio { "voice_name": "my_voice", "data_dir": "samples" }
synthesize { "model_path": "model.pth", "config_path": "config.yaml" }
`

## Tools (80)

| Category | Count | Key Tools |
|----------|-------|-----------|
| DAW Desktop App | 1 | CantioDAW.exe (PyQt GUI) |
| Project & Track | 9 | create, add, update, clip |
| MIDI & Synthesis | 6 | f0, phonemes, SoundFont synth |
| Audio Analysis | 6 | deep analyze, transcribe, Demucs separate |
| Parameter Adjust | 7 | dynamics, articulation, vibrato, swing |
| Version & Feedback | 9 | snapshot, diff, rollback, ratings |
| Render | 2 | preview, final |
| LLM | 17 | compose, lyrics, analyze, adapt, chat, stream |
| MCP Utility | 11 | soundfonts, download, reference, list models |

Full list: see [Releases](https://github.com/cuteandevil/CantioDAW/releases) or run cantiodaw-mcp.exe toollist.

## System Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.9+ | Required |
| PyTorch | 2.0+ | pip install torch torchaudio |
| RAM | 8 GB+ | 16 GB recommended |
| Disk | 2 GB+ | Model cache + audio |
| CUDA GPU | optional | Faster Demucs |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_API_KEY | — | Ollama Cloud key (required for LLM) |
| OLLAMA_MODEL | gemma4:31b | Ollama model |
| OPENAI_API_KEY | — | OpenAI key (optional) |
| ANTHROPIC_API_KEY | — | Anthropic key (optional) |

Create a .env file alongside cantiodaw-mcp.exe for API keys.

---

<div align="center">

(c) 2025-2026 CantioDAW. All Rights Reserved.

</div>
