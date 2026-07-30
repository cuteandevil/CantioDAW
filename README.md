<div align="center">

# CantioDAW · The AI Producer

**Describe a song. The AI writes the arrange
ment, performs with neural-expressive instru
ments, and criticizes its own output until i
t's ready. No piano roll, no timeline, no ma
nual mixing — just your idea and one command.**

[![GitHub release](http
s://img.shields.io/github/v/release/cuteandev
il/CantioDAW?color=76bad9)](https://github.co
m/cuteandevil/CantioDAW/releases/latest)
[![P
ython](https://img.shields.io/badge/python-3.
9+-blue.svg)](https://www.python.org/)
[![Nod
e](https://img.shields.io/badge/node-18+-gree
n.svg)](https://nodejs.org/)
[![License](http
s://img.shields.io/badge/license-Proprietary-
red.svg)](LICENSE)

<br>

<a href="README.md"
>English</a> | <a href="README_zh.md">简体�
��文</a>

<br>

<a href="#quick-start">Quick
 Start</a> |
<a href="#download">Download</a>
 |
<a href="#features">Features</a> |
<a href
="#tools">Tools (80)</a> |
<a href="https://g
ithub.com/cuteandevil/CantioDAW/releases">Rel
eases</a>

</div>

---

## Download

**[Downl
oad v0.2.0](https://github.com/cuteandevil/Ca
ntioDAW/releases/tag/v0.2.0)** — All-in-one
 package, no external downloads needed.

| Fi
le | Size | Description |
|------|------|---
----------|
| CantioDAW.exe | 128 MB | Stand
alone DAW desktop application (PyQt GUI) |
|
 cantiodaw-mcp.exe | 88 MB | Obfuscated MCP s
erver (80 tools) |
| python_bridge.py | 95 K
B | Python bridge (56 DAW methods + Demucs v4
 + FluidSynth) |
| demucs.zip | 79 KB | Demu
cs v4 HTDemucs source separation (35 .py) |

| soundfonts.zip | 29.8 MB | GeneralUser GS S
oundFont (145 real instruments) |
| fluidsyn
th_dlls.zip | 11 DLLs | FluidSynth runtime li
braries |

## Quick Start

`ash
# 1. Install
 Python dependencies
pip install torch torcha
udio soundfile numpy mido scipy

# 2. Extract
 all zip files
unzip demucs.zip
unzip soundfo
nts.zip
unzip fluidsynth_dlls.zip

# 3. Run
c
antiodaw-mcp.exe --test    # Self-test (28/28
)
cantiodaw-mcp.exe            # Start MCP se
rver
cantiodaw-mcp.exe toollist   # List all 
80 tools
`

## Features

### Real Instrument 
Synthesis
Built-in **FluidSynth** + **General
User GS** SoundFont (145 instruments). All MI
DI tracks automatically rendered through real
 sampled instruments — acoustic grand piano
, nylon guitar, violin, cello, string ensembl
e, flute, acoustic bass, and more.

### Elect
ro → Acoustic Adaptation
`ash
# Step 1: Se
parate vocals
separate_audio { "audio_path": 
"song.flac" }

# Step 2: Adapt with clean voc
al track
llm_adapt_to_acoustic {
  "audio_pat
h": "song.flac",
  "vocal_path": "separated/s
ong_vocals.wav"
}
`
Pipeline: analyze → Dem
ucs v4 separation → FFT transcription → a
uto arrangement → SoundFont render

### AI 
Composition
`ash
llm_compose_music { "descri
ption": "cinematic piano piece, emotional, C 
minor" }
`

### Voice Synthesis
`ash
train_v
oice_from_audio { "voice_name": "my_voice", "
data_dir": "samples" }
synthesize { "model_pa
th": "model.pth", "config_path": "config.yaml
" }
`

## Tools (80)

| Category | Count | 
Key Tools |
|----------|-------|-----------|

| DAW Desktop App | 1 | CantioDAW.exe (PyQt
 GUI) |
| Project & Track | 9 | create, add,
 update, clip |
| MIDI & Synthesis | 6 | f0,
 phonemes, SoundFont synth |
| Audio Analysi
s | 6 | deep analyze, transcribe, Demucs sepa
rate |
| Parameter Adjust | 7 | dynamics, ar
ticulation, vibrato, swing |
| Version & Fee
dback | 9 | snapshot, diff, rollback, ratings
 |
| Render | 2 | preview, final |
| LLM | 
17 | compose, lyrics, analyze, adapt, chat, s
tream |
| MCP Utility | 11 | soundfonts, dow
nload, reference, list models |

Full list: s
ee [Releases](https://github.com/cuteandevil/
CantioDAW/releases) or run cantiodaw-mcp.exe 
toollist.

## System Requirements

| Componen
t | Version | Notes |
|-----------|---------|
-------|
| Python | 3.9+ | Required |
| PyTor
ch | 2.0+ | pip install torch torchaudio |
| 
RAM | 8 GB+ | 16 GB recommended |
| Disk | 2 
GB+ | Model cache + audio |
| CUDA GPU | opti
onal | Faster Demucs |

## Environment Variab
les

| Variable | Default | Description |
|--
--------|---------|-------------|
| OLLAMA_AP
I_KEY | — | Ollama Cloud key (required for 
LLM) |
| OLLAMA_MODEL | gemma4:31b | Ollama m
odel |
| OPENAI_API_KEY | — | OpenAI key (o
ptional) |
| ANTHROPIC_API_KEY | — | Anthro
pic key (optional) |

Create a .env file alon
gside cantiodaw-mcp.exe for API keys.

---

<
div align="center">

(c) 2025-2026 CantioDAW.
 All Rights Reserved.

</div>


