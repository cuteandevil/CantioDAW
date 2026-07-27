<div align="center">

# CantioDAW · AI Agent Music Production Framework

**AI agent-driven vocal/music production pipeline** — offline batch processing, generates MIDI + audio for import into DAWs.

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

<br>

<a href="README.md">English</a> ｜ <a href="README_zh.md">简体中文</a>

<br>

<a href="#quick-start">Quick Start</a> ｜
<a href="#configuration">Configuration</a> ｜
<a href="#tools">Tools (66)</a> ｜
<a href="#features">Features</a> ｜
<a href="#architecture">Architecture</a> ｜
<a href="https://github.com/cuteandevil/CantioDAW/releases">Releases</a>

</div>

---

## Quick Start

### 1. Download
Get the latest release from [Releases](https://github.com/cuteandevil/CantioDAW/releases/latest).

### 2. Install Python Dependencies
```bash
pip install torch torchaudio soundfile numpy mido scipy
```

### 3. Extract & Configure
```bash
unzip demucs.zip
# Create .env file (see below)
notepad .env
```

### 4. Run
```bash
cantiodaw-mcp.exe --test    # Self-test
cantiodaw-mcp.exe            # Start MCP server
cantiodaw-mcp.exe toollist   # List all 66 tools
```

---

## Configuration

Create a `.env` file alongside `cantiodaw-mcp.exe`:

```env
# Required for LLM features
OLLAMA_API_KEY=your_ollama_cloud_api_key
OLLAMA_MODEL=gemma4:31b

# Optional
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-3-opus-20240229

# Python path (if not in PATH)
CANTIODAW_PYTHON=python
```

### Getting API Keys

| Provider | Sign Up | Notes |
|----------|---------|-------|
| **Ollama Cloud** | [ollama.com](https://ollama.com) | Required for LLM tools. Free tier available. |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | Optional. `gpt-4o` recommended. |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com) | Optional. |

> Without an LLM API key, LLM tools (16 tools) will show "LLM router not available". DAW tools (50 tools) still work.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_API_KEY` | — | Ollama Cloud API key (**required for LLM**) |
| `OLLAMA_MODEL` | `gemma4:31b` | Ollama model name |
| `OPENAI_API_KEY` | — | OpenAI API key (optional) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (optional) |
| `ANTHROPIC_MODEL` | — | Anthropic model |
| `CANTIODAW_PYTHON` | `python` | Python executable path |
| `CANTIODAW_ROOT` | auto-detect | CantioDAW project root |

### System Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.9+ | Required |
| PyTorch | 2.0+ | `pip install torch` |
| torchaudio | 0.9+ | `pip install torchaudio` |
| Node.js | 18+ | Bundled in .exe |
| CUDA GPU | optional | Faster Demucs inference |
| RAM | 8 GB+ | 16 GB recommended for large files |
| Disk | 2 GB+ | Model cache + audio files |

---

## Features

### Electro → Acoustic Adaptation
```bash
# Step 1: Separate vocals (background, ~5-8 min CPU)
separate_audio { "audio_path": "song.flac" }

# Step 2: Adapt with clean vocal track
llm_adapt_to_acoustic {
  "audio_path": "song.flac",
  "vocal_path": "separated/song_vocals.wav"
}
```
Full pipeline: analyze → Demucs v4 separation → FFT transcription → auto arrangement → render

### AI Composition
```bash
llm_compose_music {
  "description": "cinematic piano piece, emotional, 120 BPM, C minor"
}
```

### Voice Synthesis
```bash
# Train a voice model
train_voice_from_audio { "voice_name": "my_voice", "data_dir": "data/voice_samples" }

# Synthesize singing
synthesize { "model_path": "models/my_voice.pth", "config_path": "config.yaml", "pitch": 60 }
```

---

## Tools (66)

### Project & Track (9)
| Tool | Description |
|------|-------------|
| `project_create` | Create a new project |
| `project_list` | List all projects |
| `project_load` | Load project details |
| `project_delete` | Delete project |
| `project_export` | Export project to audio |
| `track_add` | Add audio/MIDI track |
| `track_remove` | Remove track |
| `track_update` | Update track (volume/mute/name) |
| `track_add_clip` | Add clip (MIDI notes/chords/audio) |

### MIDI & Synthesis (6)
| Tool | Description |
|------|-------------|
| `midi_notes_to_f0` | Convert MIDI to F0 contour |
| `midi_lyrics_to_phonemes` | Lyrics → phonemes |
| `synthesize` | Singing voice from MIDI + model |
| `synthesize_midi` | SoundFont / oscillator synthesis |
| `list_soundfonts` | List SoundFont files |
| `download_soundfont` | Download FluidR3_GM.sf2 |

### Audio Analysis & Transcription
| Tool | Description |
|------|-------------|
| `audio_analyze_deep` | BPM, key, spectral, beat, structure |
| `audio_transcribe` | HPS pitch + onset + chord detection |
| `separate_audio` | Demucs v4 source separation (async) |
| `analyze_audio` | Audio quality analysis |
| `analyze_vocal_quality` | Pitch deviation, artifacts |
| `adjust_synthesized_pitch` | Localized pitch correction |

### Parameter Adjustment (7)
| Tool | Description |
|------|-------------|
| `adjust_dynamics` | Dynamics curve |
| `adjust_articulation` | Legato/staccato, attack |
| `adjust_vibrato` | Vibrato depth/rate |
| `adjust_micro_timing` | Micro-timing offsets |
| `adjust_harmonic_color` | Harmonic quality/mode |
| `apply_swing` | Swing feel |
| `apply_rubato` | Tempo rubato curve |

### Version & Feedback (9)
| Tool | Description |
|------|-------------|
| `project_snapshot` | Create version snapshot |
| `diff_versions` | Compare versions |
| `rollback_to_version` | Rollback to version |
| `list_versions` | List all versions |
| `feedback_submit` | Submit rating (1-5) |
| `feedback_ab_test` | Submit A/B test |
| `list_feedback` | List all feedback |
| `track_replay` | Record replay event |
| `track_favorite` | Toggle favorite |

### Render (2)
| Tool | Description |
|------|-------------|
| `render_preview` | Quick preview render |
| `render_final` | Full quality final render |

### LLM Tools (16)
| Tool | Description |
|------|-------------|
| `llm_chat` | General LLM chat (auto-routing) |
| `llm_stream` | Streaming LLM chat |
| `llm_generate_lyrics` | AI lyrics generation |
| `llm_compose_song` | End-to-end song composition |
| `llm_suggest_arrangement` | Arrangement suggestions |
| `llm_analyze_lyrics` | Lyric analysis |
| `llm_compose_music` | Compose from description |
| `llm_parse_intent` | NL → Music Semantic IR |
| `llm_query_knowledge_graph` | Query knowledge graph |
| `llm_compose_from_intent` | IR → Arrangement + MIDI |
| `llm_analyze_music` | Multi-domain music critic |
| `llm_request_checkpoint` | Human checkpoint |
| `llm_list_providers` | List LLM providers |
| `llm_list_models` | List available models |
| `llm_usage_stats` | Usage statistics |
| **`llm_adapt_to_acoustic`** | **Electro → Acoustic pipeline** |

---

## Architecture

```
Natural Language
   ↓
┌──────────────────────────────────────────┐
│  Intent Agent    NL → Music Semantic IR   │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  Composer Agent  IR → Arrangement         │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  Parameter Agent  IR → Parameter Delta    │
└──────────────────┬───────────────────────┘
                   ↓
  MIDI Generation / Track Management
                   ↓
┌──────────────────────────────────────────┐
│  Critic (5 modules) + Revision (auto-loop)│
└──────────────────┬───────────────────────┘
                   ↓
         Human Preference Feedback
```

## Limitations

- **Offline batch processing** — does not replace real-time DAWs
- **LLM-dependent composition** — quality varies by model/prompt
- **CPU Demucs is slow** — GPU recommended for large files

---

<div align="center">

© 2025-2026 CantioDAW. All Rights Reserved.

</div>
