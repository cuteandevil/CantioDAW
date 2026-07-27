# CantioDAW

AI Agent Music Production Framework — offline batch processing: generates MIDI + audio for import into DAWs.

## Download

**[Download v0.2.0](https://github.com/cuteandevil/CantioDAW/releases/tag/v0.2.0)**

| File | Description |
|------|-------------|
| `cantiodaw-mcp.exe` | Obfuscated MCP server executable (66 tools) |
| `python_bridge.py` | Python bridge (56 DAW methods + Demucs v4) |
| `demucs.zip` | Integrated Demucs v4 source separation (35 .py) |

## Requirements
- Python 3.9+, torch, torchaudio, numpy, soundfile
- Optional: scipy, pyfluidsynth

## Quick Start
```bash
pip install torch torchaudio soundfile numpy mido
unzip demucs.zip
cantiodaw-mcp.exe --test
```
