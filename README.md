# CantioDAW · AI Agent Music Production Framework

**AI agent-driven vocal/music production pipeline** with project + track workflow, multi-agent composition, automated critique and revision, and voice synthesis — built on TypeScript MCP orchestrator + Python audio core.

> **Offline batch processing** — generates MIDI and audio files for import into DAWs. Does not replace Ableton, REAPER, FL Studio, or any DAW for real-time recording, mixing, or live production.

## Architecture

```
Natural Language
   ↓
┌─────────────────────────────┐
│  Intent Agent               │  NL → Music Semantic IR
│  (llm_parse_intent)         │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Composer Agent             │  IR → Arrangement (structure/melody/harmony/orchestration)
│  (llm_compose_from_intent)  │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Parameter Agent            │  IR → Parameter Delta
│  (parameter_mapper.py)      │
└─────────────┬───────────────┘
              ↓
    MIDI Generation /          ← 41 processing tools
    Track Management
              ↓
┌─────────────────────────────┐
│  Critic Agent (4 modules)  │  Harmony / Melody / Rhythm / Audio
│  (critic/*.py)              │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Revision Agent             │  Diagnosis → fix plan → apply → verify
│  (revision.ts)             │
└─────────────┬───────────────┘
              ↓
       Optimization Loop      ← iteration with convergence control
              ↓
      Human Preference        ← ratings / A-B tests / adoption tracking
```

## Pipeline

```
Audio Dataset → Voice Training → Load Model → Compose MIDI + Lyrics → Synthesize → Mix → Export
                          ↑                          ↑
                     SVC / RVC  ← auto-detect — Model Format Adapter
```

## Quick Start

```bash
# Install Python package
pip install -e .

# Start TS Orchestrator MCP server (AI composition pipeline over stdio)
npm run build --prefix ts-orchestrator
node ts-orchestrator/dist/index.js

# Start web UI (dataset management + voice training)
python -m cantiodaw serve
# Open http://127.0.0.1:8080
```

## TS Orchestrator — 56 Tools

The orchestrator runs as an MCP server over stdio, exposing 56 tools (41 DAW/MIDI + 15 LLM) for project management, music generation, analysis, and export:

### Project & Track Tools (8)

| Tool | Description |
|------|-------------|
| `project_create` | Create a new project |
| `project_list` | List all projects |
| `project_load` | Load project details |
| `project_delete` | Delete a project |
| `project_export` | Export project to audio |
| `track_add` | Add audio/MIDI track |
| `track_remove` | Remove a track |
| `track_update` | Update track properties (volume, mute, name) |

### MIDI & Synthesis Tools (4)

| Tool | Description |
|------|-------------|
| `midi_notes_to_f0` | Convert MIDI notes to F0 contour for synthesis |
| `midi_lyrics_to_phonemes` | Convert lyrics text to phonemes |
| `synthesize` | Synthesize singing voice from MIDI + model |
| `synthesize_midi` | Synthesize multi-track arrangement to WAV/MIDI |

### Audio Processing Tools (3)

| Tool | Description |
|------|-------------|
| `effect_apply` | Apply audio effect (reverb, EQ, compressor) |
| `mix_tracks` | Mix multiple tracks to single audio |
| `export_stems` | Export each track as separate stem |

### Voice Training Tools (2)

| Tool | Description |
|------|-------------|
| `train_prepare` | Prepare voice dataset from audio directory |
| `train_start` | Start voice model training |

### Orchestration Tools (3)

| Tool | Description |
|------|-------------|
| `compose_song` | End-to-end: create project → add tracks → synthesize |
| `train_voice_from_audio` | Full workflow: prepare → train voice model |
| `apply_voice_to_midi` | Apply voice model to MIDI notes → singing audio |

### Parameter Adjustment Tools (7)

| Tool | Description |
|------|-------------|
| `adjust_dynamics` | Adjust dynamics curve for a track section |
| `adjust_articulation` | Adjust articulation (legato/staccato) and attack |
| `adjust_vibrato` | Adjust vibrato depth and rate |
| `adjust_micro_timing` | Adjust micro-timing offsets per note |
| `adjust_harmonic_color` | Adjust harmonic quality/mode |
| `apply_swing` | Apply swing feel to a track |
| `apply_rubato` | Apply tempo rubato curve |

### Version Management Tools (4)

| Tool | Description |
|------|-------------|
| `project_snapshot` | Create version snapshot |
| `diff_versions` | Compare two project versions |
| `rollback_to_version` | Rollback to a specific version |
| `list_versions` | List all version snapshots |

### Render Tools (2)

| Tool | Description |
|------|-------------|
| `render_preview` | Quick low-quality preview render |
| `render_final` | Full-quality final render |

### Feedback Tools (2)

| Tool | Description |
|------|-------------|
| `feedback_submit` | Submit user rating (1-5) for a version |
| `feedback_ab_test` | Submit A/B test preference |

### Critic Analysis Tools (5)

| Tool | Description |
|------|-------------|
| `analyze_harmony` | Harmonic function, tension curve analysis |
| `analyze_melody` | Motif, contour, interval analysis |
| `analyze_rhythm` | Groove, density, stability analysis |
| `analyze_audio` | Spectral, dynamic, spatial analysis |
| `analyze_vocal_quality` | Synthesized vocal F0 deviation vs target MIDI, electrical/robotic artifacts, voicing breaks |

### Audio Correction Tools (1)

*Post-synthesis (音频层) — operates on rendered audio, unlike Pre-Synthesis adjust_* tools which operate on score parameters.*

| Tool | Description |
|------|-------------|
| `adjust_synthesized_pitch` | Localized pitch correction on synthesized audio segment without re-rendering the whole track |

### LLM Tools (15)

| Tool | Purpose |
|------|---------|
| `llm_chat` | General LLM chat |
| `llm_stream` | Streaming LLM chat |
| `llm_generate_lyrics` | Lyrics generation |
| `llm_compose_song` | End-to-end song composition |
| `llm_suggest_arrangement` | Arrangement suggestions |
| `llm_analyze_lyrics` | Lyric analysis |
| `llm_compose_music` | Direct MIDI composition |
| `llm_list_providers` | Provider listing |
| `llm_list_models` | Model listing |
| `llm_usage_stats` | Usage statistics |
| `llm_parse_intent` | NL → Music Semantic IR |
| `llm_query_knowledge_graph` | Knowledge graph query |
| `llm_compose_from_intent` | IR → Arrangement |
| `llm_analyze_music` | Multi-domain music critic |
| `llm_request_checkpoint` | Human checkpoint request |

## Music Semantic IR

The core intermediate representation between natural language and musical parameters:

```python
from cantiodaw.music.ir import MusicIR, EmotionVector

# "凌晨三点开车，一个人在城市里，很孤独但最后看到希望"
ir = MusicIR(
    emotion=EmotionVector(loneliness=0.8, hope=0.6, nostalgia=0.7),
    scene=SceneTags(tags=["night", "urban", "driving"]),
    energy=EnergyCurve(start=0.2, end=0.8, shape="linear"),
    style=StyleVector(cinematic=0.8, ambient=0.6),
)
print(ir.to_dict())
```

## Knowledge Graph

11 music expression concepts mapped to parameter deltas (YAML-defined):

```yaml
- id: tension
  label: 紧张感
  affects:
    - target: harmony.dissonance; delta: 0.3
    - target: rhythm.syncopation; delta: 0.3
```

```python
from cantiodaw.music.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph.load("cantiodaw/music/knowledge_graph.yaml")
effects = kg.query("tension")
concepts = kg.reverse_query("harmony.dissonance")
```

## Critic System (5 Analysis Modules)

| Module | Analysis Scope | Diagnostics |
|--------|----------------|-------------|
| **Harmony** | Chord function distribution (T/SD/D), dissonance curve, resolution rate | "Transition section lacks tension" |
| **Melody** | Motif repetition, contour variety, register distribution, interval profile | "Large leaps too frequent" |
| **Rhythm** | Swing amount, note density, tempo stability, downlock | "Syncopation density too high" |
| **Audio** | RMS energy curve, spectral brightness, crest factor, stereo width | "High-frequency brightness insufficient" |
| **Vocal** | Pitch deviation vs target MIDI, electrical/robotic artifacts, voicing breaks | "Mean pitch deviation 68 cents — out of tune" |

> **Note on `llm_analyze_music`**: This LLM tool provides **supplementary interpretation** of the rule-based critic outputs, not a parallel evaluation path. The workflow is: rule-based critics (harmonic/melody/rhythm/audio/vocal) produce structured numerical diagnostics → `llm_analyze_music` reads those diagnostics and generates natural-language suggestions for revision. The rule-based scores determine severity and priority; the LLM adds context. If the LLM disagrees with a critic diagnosis, the rule-based score takes precedence unless overridden by human judgment.

### Unified Output Format

```json
{
  "domain": "harmony",
  "problem": "过渡段张力不够",
  "severity": 0.6,
  "diagnosis": ["dominant 和弦占比过低 (12%)"],
  "suggestions": [
    { "action": "adjust_harmonic_color", "params": {"section": "bridge", "quality_delta": "+dominant"} }
  ]
}
```

## Workflows (7)

| Workflow | Steps |
|----------|-------|
| `compose_song` | Create project → Add track → Phonemes → Synthesize → Export |
| `train_voice` | Prepare dataset → Train model |
| `apply_voice` | Convert lyrics → F0 contour → Synthesize |
| `mix_export` | Mix tracks → Export stems |
| `compose_from_intent` | Parse NL intent → Compose from IR → MIDI preview |
| `critic_revise` | Snapshot → Analyze → Snapshot → Preview |
| `full_pipeline` | NL → IR → Compose → Critic → Diff → Final export |

```bash
node ts-orchestrator/dist/index.js worklist
```

## End-to-End Scenarios

### NL → MIDI
```
Input: "一段宁静的钢琴曲"
→ llm_parse_intent → MusicIR
→ llm_compose_from_intent → Arrangement with MIDI notes
→ export_midi → .mid file (import into DAW for proper playback)
```

### Evaluation Loop
```
Generated MIDI → analyze_harmony + analyze_melody
→ Critic discovers ≥1 issue → Suggests fixes
```

### Self-Correction
```
Generate → Critic → Revise Agent → apply adjust_* → Preview
→ Iteration with convergence control (max 5 rounds)
```

### Full Pipeline
```
"凌晨三点开车…孤独但希望"
→ Auto compose → Auto critique → Auto revise → Final export
→ Human feedback collected
```

## Convergence Control (Revision Loop)

When the Revision Agent runs iteratively, it follows these rules:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Max iterations | 5 | Hard stop after this many rounds |
| Quality threshold | 0.8 (score) | If critic score ≥ 0.8, stop even if iterations remain |
| No-improvement limit | 3 consecutive rounds | If critic score doesn't improve for 3 rounds, stop and emit warning |
| Convergence check | per-iteration | After each revision, re-run critics and compare scores |

When the loop stops but hasn't converged (score < 0.8):
- If a `request_checkpoint` was placed, pause and wait for human decision
- Otherwise, output the **best version seen so far** (not the final iteration)

These limits are **global defaults**. Per-project overrides can be set via `request_checkpoint` tool parameters.

## Preference Feedback

Collected data flows through:

```
User rating (1-5) / A/B test
        ↓
PreferenceCollector  →  JSONL storage (feedback.jsonl / abtest.jsonl / adoption.jsonl)
        ↓
PreferenceModel.train(samples)  →  learns feature weights
        ↓
PreferenceModel.adjust_critic_score(critic_score, features)
        ↓
Weighted score used in Revision Agent's convergence check
```

**Status**: Data collection is fully implemented. The preference model's output currently adjusts critic scores during revision convergence. It is **not yet** consumed by the Composer Agent or Intent Agent at generation time — that is planned future work.

## DAW Collaboration

CantioDAW generates structured MIDI — DAWs do everything else. The workflow:

```
CantioDAW                                 DAW (Ableton / REAPER / FL Studio / Logic)
──────────                                ───────────────────────────────────────────
NL description → AI arrangement
       ↓
Generate .mid (multi-track)
       ↓                                         Import .mid file
(optional) Run Critic → Revision                Assign VST instruments
       ↓                                         Edit MIDI notes, quantize
Iterate until satisfied                        Record live parts, mix, add FX
       ↓                                         Master → final export
Export .mid ──────────────────────────►
```

### Scenario 1: Idea Kickstart

```
You: "一段 cinematic 管弦乐，紧张→恢弘"
CantioDAW: .mid file with 7-section arrangement
DAW: Open .mid → assign BBCSO/Spitfire → listen immediately
     Like it? Keep. Don't? Rewrite prompt, regenerate.
```

No blank page anxiety — AI gives you a structured starting point in seconds.

### Scenario 2: Iterative Arrangement

```
1. Run full_pipeline: compose → critic → revise → export .mid
2. Open in DAW, listen
3. If a section's chord progression is wrong:
   - Option A: adjust prompt and regenerate that section only
   - Option B: edit MIDI directly in DAW, keep the rest
4. Repeat until structure is right
```

CantioDAW handles the **macro structure** (form, harmony, emotion arc). DAW handles the **micro details** (timbre, articulation, mix).

### Scenario 3: Vocal Synthesis Front-End

```
1. CantioDAW composes + generates lyric phonemes
2. synthesize → raw vocal WAV stem
3. Import vocal stem into DAW as an audio track
4. Build accompaniment around it in DAW
5. Use adjust_* tools for pitch/timing correction without retraining
```

### Scenario 4: Analysis Assistant

```
DAW: Export your finished MIDI arrangement
CantioDAW: Run analyze_harmony / analyze_melody / analyze_rhythm
           → "Bridge section: dominant chord ratio too low (12%)"
           → "Melody: large leaps in bars 17-20"
DAW: Go back and fix those specific bars
```

The Critic system provides **objective diagnostics** you can act on in your DAW.

### Summary

| CantioDAW does (offline) | DAW does (real-time) |
|--------------------------|----------------------|
| NL → structured arrangement | VST instrument playback |
| Multi-track MIDI generation | Audio recording & editing |
| Harmony/melody/rhythm analysis | Mixing, FX, mastering |
| Voice synthesis (raw WAV) | Arrangement fine-tuning |
| Version diff & rollback | Live performance |

## CLI Usage

```bash
# Create a project
cantiodaw project create --name MySong

# Train a voice model
cantiodaw train --voice MyVoice --data-dir data/voices/my_voice --epochs 50

# Synthesize with auto-detected format
cantiodaw synthesize --model checkpoints/MyVoice/best_model.safetensors \
  --config config.yaml --pitch 60 --duration 2.0 -o output.wav

# Detect model format
cantiodaw detect --model so-vits-svc/G_10000.pth
```

## Output Formats

| Format | Source | Usage |
|--------|--------|-------|
| **MIDI** (`.mid`) | Composer Agent → `export_midi` | Multi-track arrangement. Import into DAW with VST instruments for proper playback |
| **WAV — Synth Preview** (`.wav`) | `synthesize_midi` | Basic waveform (sine/triangle/sawtooth oscillators per track type). Quick preview of arrangement structure, not suitable for production |
| **WAV — Neural SVC** (`.wav`) | `synthesize` with trained SVC/RVC model | Neural vocoder singing voice output. Quality depends on voice model training |
| **JSON** | Critics, IR, version diff tools | Analysis results, IR data, version diffs |

## Environment

```
CANTIODAW_PYTHON    Python executable path (default: python)
CANTIODAW_ROOT      CantioDAW project root (default: parent dir)
OLLAMA_API_KEY      Ollama Cloud API key
OLLAMA_MODEL        Ollama model name (default: gemma4:31b)
OPENAI_API_KEY      OpenAI API key (optional)
```

## Supported Model Formats (Voice Synthesis)

| Format | Detection | Config |
|--------|-----------|--------|
| **CantioDAW HybridSVC** (.safetensors/.pt) | `phoneme_feature_dim` / `spectral_envelope_dim` | `config.yaml` |
| **so-vits-svc** (.pth) | `inter_channels` / `filter_channels` / `n_heads` | `config.json` |
| **RVC v1** (.pth, 256-dim) | `generator.` / `emb_g` keys | `config.json` |
| **RVC v2** (.pth, 768-dim) | `generator.` / `dec.4` / `794` keys | `config.json` |

## Requirements

- Python 3.9+, PyTorch 2.0+, Node.js 18+
- `pip install -e .` for Python
- `npm install` in `ts-orchestrator/` for TypeScript

## Project Structure

```
cantiodaw/
├── music/                  # Music IR, Knowledge Graph, Parameter Mapper
│   ├── ir.py              # MusicIR data structures (Python truth source)
│   ├── knowledge_graph.py # Graph query engine
│   ├── knowledge_graph.yaml # 11 concept nodes
│   ├── parameter_mapper.py # Emotion → parameter mapping tables
│   └── labels.py          # Emotion/Scene/Style label taxonomies
├── critic/                 # 4-module music analysis
│   ├── harmony.py         # Chord function, tension curve
│   ├── melody.py          # Motif detection, interval analysis
│   ├── rhythm.py          # Groove, density, stability
│   └── audio.py           # Spectral, dynamic, spatial analysis
├── preference/             # Human feedback learning
│   ├── collector.py       # Rating, A/B test, adoption tracking
│   └── model.py           # Preference weighting model
└── project_version.py     # Version snapshots, diff, rollback

ts-orchestrator/
├── src/
│   ├── mcp/tools.ts       # 41 processing tool definitions
│   ├── llm/tools.ts       # 15 LLM tool definitions
│   ├── llm/prompts/       # Intent parser + composer prompts
│   ├── music/ir.ts        # TypeScript MusicIR mirror
│   ├── orchestrator/
│   │   ├── composer.ts    # Composer Agent (IR → arrangement)
│   │   ├── revision.ts    # Revision Agent (prioritize + fix)
│   │   └── workflows.ts   # 7 predefined workflows
│   └── bridge/            # Python ↔ TypeScript bridge
```

## Limitations

- **Not a real-time DAW** — all processing is offline/batch. Does not replace Ableton, REAPER, FL Studio, or similar for live recording, mixing, or real-time production.
- **WAV synthesis quality is dual-track**: `synthesize_midi` uses basic oscillators (sine/triangle/sawtooth) for arrangement preview. Neural SVC `synthesize` quality depends entirely on the trained voice model. These are separate paths with different quality characteristics.
- **LLM-dependent composition** — arrangement quality varies by model and prompt. Results require human review and editing.
- **Research-grade** — suitable for experimentation with AI-driven composition and voice synthesis, not for commercial music production out of the box.

## License

Apache 2.0
