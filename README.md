<div align="center">

# CantioDAW · The AI Producer

**Describe a song. The AI writes the arrangement, performs with neural-expressive instruments, and criticizes its own output until it's ready. No piano roll, no timeline, no manual mixing — just your idea and one command.**

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)(LICENSE)

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

```bash
# Run the desktop DAW
CantioDAW.exe gui

# Or run the MCP server (for AI agent integration)
cantiodaw-mcp.exe --test    # Self-test (28/28)
cantiodaw-mcp.exe            # Start MCP server (stdio)
cantiodaw-mcp.exe toollist   # List all 80 tools
```

**Requires:** Python 3.9+ with `pip install torch torchaudio soundfile numpy mido scipy`

---

## Two Ways to Use CantioDAW

### 1. CantioDAW.exe — Desktop DAW Application
A full-featured PyQt6 desktop application for project management, MIDI editing, voice training, and audio mixing. Launch with `CantioDAW.exe gui` or access the Web UI at `http://127.0.0.1:8080`.

### 2. cantiodaw-mcp.exe — AI Agent Interface (MCP Server)
An MCP (Model Context Protocol) server that exposes all 80 tools to AI agents like Claude, Cursor, or any MCP-compatible client. Connect via stdio — your AI agent talks to CantioDAW directly.

---

## Features

### Neural Instrument Synthesis (DDSP)
MIDI notes in, expressive audio out. The **DDSP neural synthesis engine** renders 15 instruments with human-like articulation, dynamics, vibrato, and micro-timing — controlled by a **PerformanceHead** that maps performance intent to physical synthesis parameters (tau, breath, transient decay). No sampling, no MIDI CC programming — just describe how you want it to sound.

**Performance Expression Pipeline:**
```
LLM Intent → MusicIR → SongArrangementPlan → PerformanceIntent → DDSP Params → Audio
```

Six built-in expression presets (legato, staccato, marcato, portato, pizzicato, tremolo) plus continuous parameter control.

### Real Instrument Rendering (SoundFont)
Built-in **FluidSynth** + **GeneralUser GS** SoundFont (145 GM instruments). All MIDI tracks automatically rendered through real sampled instruments — acoustic grand piano, nylon guitar, violin, cello, string ensemble, flute, acoustic bass, and more. Program/bank selection supported.

### AI Composition & Arrangement
Describe music in natural language — the LLM parses your intent into a structured **MusicIR** (emotion, energy, style, scene, arrangement), then generates a complete arrangement with sections, chords, melody, and instrument assignment.

```
"cinematic piano piece, emotional, C minor"
  → MusicIR → SongArrangementPlan → MIDI → DDSP/SoundFont → WAV
```

### Intelligent Critic & Revision System
Four specialized critics analyze the output:
- **Harmony Critic** — chord progression, voice leading, tension
- **Melody Critic** — contour, phrase structure, motivic development
- **Rhythm Critic** — groove, syncopation, timing consistency
- **Audio Critic** — spectral balance, dynamics, artifacts, noise floor

The **Revision Agent** runs a diagnose-fix-verify loop with convergence control, automatically improving the output until quality thresholds are met.

### Voice Training & Synthesis
Train a voice model from audio samples (with or without LoRA fine-tuning), then synthesize singing from MIDI notes + lyrics with phoneme alignment.

### Audio Source Separation
Integrated **Demucs v4 (HTDemucs)** separates vocals from accompaniment for remixing, acoustic adaptation, or lyric transcription.

### Studio-Quality Mixing & Effects
Multi-track mixing, reverb, EQ, compression, gain staging, and export to WAV/FLAC at 44.1 kHz / 24-bit.

### Versioning & Human Feedback
Snapshot every project state, diff between versions, rollback, collect human ratings (1-5), A/B test two versions, track replay counts. The system learns from your preferences.

### Electro → Acoustic Adaptation
Transform electronic productions into acoustic arrangements. Demucs separates stems, the LLM re-orchestrates for real instruments, FluidSynth renders the result.

---

## Tools (80)

| Category | Count | Key Tools |
|----------|-------|-----------|
| DAW Desktop App | 1 | CantioDAW.exe (PyQt GUI) |
| Project & Track | 9 | create, add, update, clip |
| MIDI & Synthesis | 6 | f0, phonemes, SoundFont synth |
| Audio Analysis | 6 | deep analyze, transcribe, Demucs separate |
| Performance Expression | 7 | dynamics, articulation, vibrato, swing, rubato, micro-timing, harmonic color |
| Version & Feedback | 9 | snapshot, diff, rollback, ratings, A/B test, favorites |
| Render & Export | 2 | preview, final, stem export |
| LLM Composition | 17 | compose, lyrics, analyze, adapt, chat, stream, piano arrange |
| MCP Utility | 11 | soundfonts, download, model list, parameter reference |
| Revision & Checkpoints | 4 | revise, diagnose, checkpoint, human-in-the-loop |

Full list: run `cantiodaw-mcp.exe toollist` or see the [Releases page](https://github.com/cuteandevil/CantioDAW/releases).

---

## System Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.9+ | Required for python_bridge.py |
| PyTorch | 2.0+ | pip install torch torchaudio |
| RAM | 8 GB+ | 16 GB recommended for Demucs |
| Disk | 2 GB+ | Model cache + audio + SoundFont |
| CUDA GPU | Optional | Accelerates Demucs and DDSP |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_API_KEY | — | Ollama Cloud key (required for LLM tools) |
| OLLAMA_MODEL | gemma4:31b | Ollama model name |
| OPENAI_API_KEY | — | OpenAI key (optional, alternative provider) |
| ANTHROPIC_API_KEY | — | Anthropic key (optional, alternative provider) |
| CANTIODAW_PYTHON | python | Python executable path for bridge |
| CANTIODAW_ROOT | (parent dir) | CantioDAW project root |

Create a `.env` file alongside `cantiodaw-mcp.exe` for API keys.

---

<div align="center">

(c) 2025-2026 CantioDAW. All Rights Reserved.

</div>
