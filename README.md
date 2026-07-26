# CantioDAW

AI-Powered Singing Voice Production DAW — intelligent music production with multi-agent AI orchestration, real-time voice conversion (SVC/RVC/DDSP-SVC), and an extensible MCP plugin system.

<a href="#"><img src="https://img.shields.io/badge/Node.js-18%2B-brightgreen"></a>
<a href="#"><img src="https://img.shields.io/badge/Python-3.9%2B-blue"></a>
<a href="#"><img src="https://img.shields.io/badge/license-MIT-green"></a>

---

## Features

- **AI Multi-Agent Pipeline**: Intent → Compose → Params → MIDI → Critic → Revise — closed-loop AI-assisted composition
- **Voice Conversion**: Native adapters for SVC, RVC, DDSP-SVC
- **Dual UI**: Modern Web UI (Flask) + PyQt6 Desktop GUI with zh/en language switching
- **MCP Protocol**: 56 tools (41 DAW + 15 LLM) + 7 preset workflows
- **Preference Learning**: Human feedback collection with model fine-tuning
- **Standalone Executable**: Pre-built binary available — no build required

---

## Quick Install

### Windows (Recommended)

```powershell
# Download and run CantioDAW directly
curl -LO https://github.com/cuteandevil/CantioDAW/releases/latest/download/CantioDAW-v0.1.0-release.zip
Expand-Archive -Path CantioDAW-v0.1.0-release.zip -DestinationPath ./cantiodaw
cd cantiodaw
./cantiodaw-mcp.exe --test    # Verify installation
```

Or with winget:

```powershell
# Coming soon
```

### macOS / Linux

```bash
# Coming soon
curl -fsSL https://github.com/cuteandevil/CantioDAW/releases/latest/download/install.sh | bash
```

---

## Usage

```bash
# Run MCP server (connectable by any MCP client)
cantiodaw-mcp.exe

# Run with options
cantiodaw-mcp.exe --port 8080 --webui   # Start Web UI on port 8080

# Test mode - verify all tools and workflows
cantiodaw-mcp.exe --test

# PyQt6 Desktop GUI
cantiodaw-mcp.exe --gui

# Launch Web UI (alternative)
python -m cantiodaw.webui.app
```

### Configuration

Create `config.yaml` in the working directory:

```yaml
llm:
  provider: ollama
  model: deepseek-coder-v2
  base_url: http://localhost:11434

svc:
  model_path: ./checkpoints/svc-model.pt
  device: cuda:0
```

---

## Downloads

Latest release assets are available on the [Releases](https://github.com/cuteandevil/CantioDAW/releases) page.

| Asset | Size | Description |
|-------|------|-------------|
| `CantioDAW-v0.1.0-release.zip` | 32.5 MB | Standalone exe + python_bridge.py — no build needed |
| `CantioDAW-v0.1.0-source.zip` | 0.2 MB | Full source code (development use) |

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10+, macOS 12+, Ubuntu 20.04+ |
| Node.js | ≥ 18 (not needed for the standalone exe) |
| Python | ≥ 3.9 (for SVC/RVC inference) |
| PyTorch | ≥ 2.0 |
| GPU (optional) | CUDA 11.8+ for accelerated inference |
| AI Backend | Ollama or OpenAI-compatible API |

---

## Development

Full source code is maintained in the [CantioDAW-dev](https://github.com/cuteandevil/CantioDAW-dev) repository (private).

### Build from source

```bash
git clone https://github.com/cuteandevil/CantioDAW-dev.git
cd CantioDAW-dev
pip install -e ".[all]"

# Build standalone exe
cd ts-orchestrator
npm install
npm run release
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    MCP Client                        │
├─────────────────────────────────────────────────────┤
│                  cantiodaw-mcp                       │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Web UI   │  │ PyQt GUI │  │ Pipeline Engine  │  │
│  ├───────────┤  ├──────────┤  ├──────────────────┤  │
│  │  Flask    │  │ Desktop  │  │ Intent→Compose→  │  │
│  │  REST API │  │ Native   │  │ Params→MIDI→     │  │
│  │  SSE      │  │ Cross-   │  │ Critic→Revise    │  │
│  │           │  │ platform │  │                   │  │
│  └───────────┘  └──────────┘  └──────────────────┘  │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │   SVC     │  │   RVC    │  │   DDSP-SVC      │  │
│  │  Adapter  │  │  Adapter │  │    Adapter       │  │
│  └───────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*CantioDAW — sing with intelligence.*
