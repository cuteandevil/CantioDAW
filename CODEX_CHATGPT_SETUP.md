# Using CantioDAW with Codex CLI & ChatGPT Desktop

CantioDAW's 80+ DAW tools can be accessed from Codex CLI and ChatGPT Desktop through its MCP server and HTTP bridge.

## Codex CLI

Codex CLI (by OpenAI) runs in the terminal and supports custom tool configurations.

### Via MCP (stdio)

Codex CLI supports MCP servers via its `.codexclirc` config. Add to your `~/.codexclirc` or project-local config:

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

### Via Direct CLI

Or invoke tools directly in your Codex CLI session:

```
!cantiodaw-mcp.exe toollist
```

Create a `.env` file alongside `cantiodaw-mcp.exe` with your LLM provider key:

```env
OLLAMA_API_KEY=your_key_here
LLM_PROVIDER=ollama
```

### Usage in Codex CLI

Once connected, ask Codex to do things like:

> "Compose a piano melody in C major, 120 BPM, 16 bars, and render it to WAV."
>
> "Run `cantiodaw-mcp.exe toollist` to see what tools are available, then create a new project with a synth pad track."

---

## ChatGPT Desktop

ChatGPT Desktop does not support MCP natively, but CantioDAW provides an **HTTP bridge** with an OpenAI-compatible API.

### Start the HTTP Server

```bash
python -m cantiodaw serve
```

This starts a Flask server at `http://127.0.0.1:8080` with:
- OpenAI-compatible `/v1/chat/completions` endpoint
- Web UI for project management, dataset prep, and voice training
- All 80 MCP tools exposed as API endpoints

### Use as a Custom GPT Action

1. In ChatGPT Desktop, create a **Custom GPT**
2. Add an **Action** with the following OpenAPI schema:

```yaml
openapi: 3.0.0
info:
  title: CantioDAW
  version: 1.0.0
servers:
  - url: http://localhost:8080
paths:
  /api/compose:
    post:
      summary: Compose a musical arrangement
      operationId: compose
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                description:
                  type: string
                style:
                  type: string
                tempo:
                  type: integer
      responses:
        '200':
          description: Composition result
  /api/render:
    post:
      summary: Render project to audio
      operationId: render
      responses:
        '200':
          description: Audio file URL
```

3. Custom GPT can now compose and render music through your local CantioDAW instance.

### Via Web UI

Open `http://127.0.0.1:8080` in any browser for the full Web UI — works from ChatGPT Desktop's built-in browser view, no API key needed.

---

## Requirements

| Component | Notes |
|-----------|-------|
| Python 3.9+ | `pip install torch torchaudio soundfile numpy mido scipy` |
| cantiodaw-mcp.exe | From the [Releases page](https://github.com/cuteandevil/CantioDAW/releases) |
| python_bridge.py | Included in release bundle |
| .env file | API keys for LLM provider |
| SoundFont | Runs `cantiodaw-mcp.exe download-soundfont` or use bundled `soundfonts.zip` |
| Demucs (optional) | `pip install demucs` for source separation |
