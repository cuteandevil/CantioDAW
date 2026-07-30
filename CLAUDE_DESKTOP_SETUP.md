# Using CantioDAW with Claude Desktop

CantioDAW exposes all 80+ DAW tools as an MCP (Model Context Protocol) server, allowing Claude Desktop to directly compose, arrange, produce, and refine music.

## Setup

### 1. Install Dependencies

```bash
pip install torch torchaudio soundfile numpy mido scipy
```

Optional — for source separation:
```bash
pip install demucs
```

### 2. Configure Claude Desktop

Edit `claude_desktop_config.json` (Claude Desktop → Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "cantiodaw": {
      "command": "D:\\path\\to\\cantiodaw-mcp.exe",
      "args": [],
      "env": {
        "CANTIODAW_PYTHON": "python",
        "CANTIODAW_ROOT": "D:\\CantioDAW"
      }
    }
  }
}
```

### 3. LLM Provider

Choose one of three providers and set the corresponding environment variable. Create a `.env` file alongside `cantiodaw-mcp.exe`:

```env
# Ollama (free tier available)
OLLAMA_API_KEY=your_key_here
OLLAMA_MODEL=gemma4:31b

# OR OpenAI-compatible
# OPENAI_API_KEY=sk-...

# OR Anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Choose active provider
LLM_PROVIDER=ollama
```

## Usage Examples

Once connected, ask Claude to do things like:

> "Compose a cinematic piano piece in C minor, emotional and slow."
>
> "Add a string ensemble track and mix it with the piano."
>
> "Analyze the harmony and suggest improvements."
>
> "Convert this electronic track to an acoustic arrangement."
>
> "Add a vocal track, train a voice on these samples, and synthesize the lyrics."

## Tools Overview

| Category | Example Tools |
|----------|--------------|
| Project & Track | create, add, track clips |
| MIDI Synthesis | SoundFont rendering, F0 contour, phoneme conversion |
| Audio Analysis | deep analyze, transcribe, Demucs separate |
| Performance Expression | dynamics, articulation, vibrato, swing, rubato |
| AI Composition | compose from description, piano arrangement, lyrics generation |
| Revision System | diagnose, fix, verify with convergence control |
| Voice Training | train from audio samples, synthesize singing |
| Version Control | snapshot, diff, rollback, A/B test |
| Electro → Acoustic | full pipeline: separate → re-orchestrate → render |

Run `cantiodaw-mcp.exe toollist` for the complete list.

## Troubleshooting

- **"python_bridge.py not found"**: Set `CANTIODAW_ROOT` to the directory containing `python_bridge.py`.
- **"Connection refused"**: Ensure `cantiodaw-mcp.exe` path in `claude_desktop_config.json` is correct.
- **"Model not available"**: Check your `LLM_PROVIDER` setting and corresponding API key.
- **FluidSynth errors**: Ensure `data/soundfonts/FluidR3_GM.sf2` exists or run `cantiodaw-mcp.exe download-soundfont`.
