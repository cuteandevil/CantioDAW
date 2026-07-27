<div align="center">

# CantioDAW · AI Agent Music Production Framework

**AI agent-driven vocal/music production pipeline** — offline batch processing, generates MIDI + audio for import into DAWs.

[![GitHub release](https://img.shields.io/github/v/release/cuteandevil/CantioDAW?color=76bad9)](https://github.com/cuteandevil/CantioDAW/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

<br>

<a href="#quick-start">Quick Start</a> ｜
<a href="#tools">Tools (66)</a> ｜
<a href="#pipeline">Pipeline</a> ｜
<a href="#architecture">Architecture</a> ｜
<a href="https://github.com/cuteandevil/CantioDAW/releases">Releases</a>

</div>

---

## Quick Start

```bash
# Download latest release from https://github.com/cuteandevil/CantioDAW/releases
# Requirements
pip install torch torchaudio soundfile numpy mido scipy

# Extract & run
unzip demucs.zip
cantiodaw-mcp.exe --test
```

## Architecture

```
Natural Language
   ↓
┌──────────────────────────────────────────┐
│  Intent Agent                             │
│  NL → Music Semantic IR                   │
│  (llm_parse_intent)                       │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  Composer Agent                           │
│  IR → Arrangement (structure/melody/      │
│  harmony/orchestration)                   │
│  (llm_compose_from_intent)                │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  Parameter Agent                          │
│  IR → Parameter Delta                     │
│  (parameter_mapper.py)                    │
└──────────────────┬───────────────────────┘
                   ↓
     MIDI Generation / Track Management
                   ↓
┌──────────────────────────────────────────┐
│  Critic Agent (5 modules)                 │
│  Harmony / Melody / Rhythm / Audio /      │
│  Vocal                                    │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│  Revision Agent                           │
│  Diagnosis → fix plan → apply →           │
│  re-check (auto-loop)                     │
│  (revision_execute)                       │
└──────────────────┬───────────────────────┘
                   ↓
        Optimization Loop
                   ↓
        Human Preference
```

## Pipeline

```
Audio Dataset → Voice Training → Load Model → Compose MIDI + Lyrics → Synthesize → Mix → Export
                           ↘                              ↗
                    SVC / RVC → auto-detect → Model Format Adapter
                                               ↗
                    SoundFont (SF2/FluidSynth) — real instrument synthesis
```

## Tools (66)

### Project & Track (9)
| Tool | Description |
|------|-------------|
| `project_create` | Create a new project |
| `project_list` | List all projects |
| `project_load` | Load project details |
| `project_delete` | Delete a project |
| `project_export` | Export project to audio |
| `track_add` | Add audio/MIDI track |
| `track_remove` | Remove a track |
| `track_update` | Update track properties |
| `track_add_clip` | Add clip to a track |

### MIDI & Synthesis (6)
| Tool | Description |
|------|-------------|
| `midi_notes_to_f0` | Convert MIDI notes to F0 contour |
| `midi_lyrics_to_phonemes` | Convert lyrics to phonemes |
| `synthesize` | Synthesize singing voice from MIDI + model |
| `synthesize_midi` | Synthesize via SoundFont or oscillator fallback |
| `list_soundfonts` | List available SoundFont files |
| `download_soundfont` | Download FluidR3_GM.sf2 (144 MB) |

### Audio Analysis & Transcription
| Tool | Description |
|------|-------------|
| `audio_analyze_deep` | BPM, key detection, spectral features, beat grid, structure |
| `audio_transcribe` | Auto transcription: HPS pitch detection + onset + chord recognition |
| `separate_audio` | Demucs v4 source separation (async background) |
| `analyze_audio` | Audio quality analysis |
| `analyze_vocal_quality` | Pitch deviation, electrical artifacts |
| `adjust_synthesized_pitch` | Localized pitch correction |

### Parameter Adjustment (7)
| Tool | Description |
|------|-------------|
| `adjust_dynamics` | Dynamics curve delta |
| `adjust_articulation` | Legato/staccato, attack time |
| `adjust_vibrato` | Vibrato depth and rate |
| `adjust_micro_timing` | Micro-timing offsets |
| `adjust_harmonic_color` | Harmonic quality/mode |
| `apply_swing` | Swing feel |
| `apply_rubato` | Tempo rubato curve |

### Version & Feedback (9)
| Tool | Description |
|------|-------------|
| `project_snapshot` | Create version snapshot |
| `diff_versions` | Compare two versions |
| `rollback_to_version` | Rollback to version |
| `list_versions` | List all versions |
| `feedback_submit` | Submit rating (1-5) |
| `feedback_ab_test` | Submit A/B test |
| `list_feedback` | List all feedback |
| `track_replay` | Record replay event |
| `track_favorite` | Toggle favorite |

### LLM Tools (16)
| Tool | Description |
|------|-------------|
| `llm_chat` | General LLM chat (auto-routing) |
| `llm_stream` | Streaming LLM chat |
| `llm_generate_lyrics` | Lyrics generation |
| `llm_compose_song` | End-to-end song composition |
| `llm_suggest_arrangement` | Arrangement suggestions |
| `llm_analyze_lyrics` | Lyric analysis |
| `llm_compose_music` | Direct composition from description |
| `llm_parse_intent` | NL → Music Semantic IR |
| `llm_query_knowledge_graph` | Query knowledge graph |
| `llm_compose_from_intent` | IR → Arrangement with MIDI |
| `llm_analyze_music` | Multi-domain music critic |
| `llm_request_checkpoint` | Human checkpoint request |
| `llm_list_providers` | List LLM providers |
| `llm_list_models` | List available models |
| `llm_usage_stats` | Usage statistics |
| **`llm_adapt_to_acoustic`** | **Electro → Acoustic pipeline** |

## Electro → Acoustic Pipeline

```
Step 1: audio_analyze_deep     → BPM / Key / Spectral / Structure
Step 2: separate_audio          → Demucs v4 vocals + instrumental (async)
Step 3: audio_transcribe        → FFT pitch from clean vocals → MIDI notes
                                 → Chroma chord recognition
Step 4: auto accompaniment       → Chord arpeggios + bass
Step 5: render_final             → SoundFont/oscillator → WAV
```

See [Releases](https://github.com/cuteandevil/CantioDAW/releases) for download.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `CANTIODAW_PYTHON` | `python` | Python executable path |
| `CANTIODAW_ROOT` | auto-detect | CantioDAW project root |
| `OLLAMA_API_KEY` | built-in | Ollama Cloud API key |
| `OLLAMA_MODEL` | `gemma4:31b` | Ollama model name |
| `OPENAI_API_KEY` | — | OpenAI API key (optional) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI default model |

## Requirements

- Python 3.9+, PyTorch 2.0+, Node.js 18+
- `pip install torch torchaudio soundfile numpy mido scipy`
- Optional: `pyfluidsynth` for SoundFont real-instrument synthesis
- Optional: CUDA-capable GPU for faster Demucs inference

---

<div align="center">

© 2025-2026 CantioDAW. All Rights Reserved.

</div>
