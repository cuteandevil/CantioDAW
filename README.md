# CantioDAW · AI Agent Music Production Framework

**AI agent-driven vocal/music production pipeline** with project + track workflow, multi-agent composition, automated critique and revision, voice synthesis, and real-instrument SoundFont rendering — built on TypeScript MCP orchestrator + Python audio core.

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
    MIDI Generation /          ← 57 DAW/MIDI tools
    Track Management
              ↓
┌─────────────────────────────┐
│  Critic Agent (5 modules)  │  Harmony / Melody / Rhythm / Audio / Vocal
│  (critic/*.py)              │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Revision Agent             │  Diagnosis → fix plan → apply → re-check (auto-loop)
│  (revision_execute)         │
└─────────────┬───────────────┘
              ↓
        Optimization Loop      ← iteration with convergence control
              ↓
       Human Preference        ← ratings / A-B tests / adoption tracking / favorites
```

## Pipeline

```
Audio Dataset → Voice Training → Load Model → Compose MIDI + Lyrics → Synthesize → Mix → Export
                          ↑                          ↑
                      SVC / RVC  ← auto-detect — Model Format Adapter
                                         ↑
                                   SoundFont (SF2/FluidSynth) — real instrument synthesis
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

## TS Orchestrator — 70 Tools

The orchestrator runs as an MCP server over stdio, exposing 70 tools (57 DAW/MIDI + 13 LLM) for project management, music generation, analysis, and export. All tools are tagged with category labels: `[生成]` (generation), `[评价]` (evaluation), `[执行]` (execution), `[编排]` (orchestration).

### Project & Track Tools (9)

| Tool | Category | Description |
|------|----------|-------------|
| `project_create` | `[执行]` | Create a new project |
| `project_list` | `[执行]` | List all projects |
| `project_load` | `[执行]` | Load project details |
| `project_delete` | `[执行]` | Delete a project |
| `project_export` | `[执行]` | Export project to audio |
| `track_add` | `[执行]` | Add audio/MIDI track |
| `track_remove` | `[执行]` | Remove a track |
| `track_update` | `[执行]` | Update track properties (volume, mute, name) |
| `track_add_clip` | `[执行]` | Add clip (MIDI notes, chords, or audio) to a track |

### MIDI & Synthesis Tools (6)

| Tool | Category | Description |
|------|----------|-------------|
| `midi_notes_to_f0` | `[执行]` | Convert MIDI notes to F0 contour for synthesis |
| `midi_lyrics_to_phonemes` | `[执行]` | Convert lyrics text to phonemes |
| `synthesize` | `[生成]` | Synthesize singing voice from MIDI + model |
| `synthesize_midi` | `[生成]` | Synthesize multi-track arrangement via SoundFont or oscillator fallback |
| `list_soundfonts` | `[执行]` | List available SoundFont (.sf2/.sf3) files and instruments |
| `download_soundfont` | `[执行]` | Download FluidR3_GM.sf2 (144 MB) for real instrument synthesis |

### Audio Processing Tools (3)

| Tool | Category | Description |
|------|----------|-------------|
| `effect_apply` | `[执行]` | Apply audio effect (reverb, EQ, compressor) |
| `mix_tracks` | `[执行]` | Mix multiple tracks to single audio (MIDI tracks auto-synthesized via SoundFont) |
| `export_stems` | `[执行]` | Export each track as separate stem |

### Voice Training Tools (3)

| Tool | Category | Description |
|------|----------|-------------|
| `train_prepare` | `[执行]` | Prepare voice dataset from audio directory |
| `train_start` | `[执行]` | Start voice model training |
| `train_voice_from_audio` | `[执行]` | Full workflow: prepare → train voice model |

### Orchestration Tools (4)

| Tool | Category | Description |
|------|----------|-------------|
| `compose_song` | `[生成]` | End-to-end: create project → add tracks → synthesize |
| `apply_voice_to_midi` | `[执行]` | Apply voice model to MIDI notes → singing audio |
| `revision_execute` | `[编排]` | Critic→fix→re-check revision loop with convergence control |
| `parameter_reference` | `[执行]` | Query physical parameter mappings (MIDI CC→DAW, instrument→GM program) |

### Parameter Adjustment Tools (7)

| Tool | Category | Description |
|------|----------|-------------|
| `adjust_dynamics` | `[执行]` | Adjust dynamics curve for a track section |
| `adjust_articulation` | `[执行]` | Adjust articulation (legato/staccato) and attack |
| `adjust_vibrato` | `[执行]` | Adjust vibrato depth and rate |
| `adjust_micro_timing` | `[执行]` | Adjust micro-timing offsets per note |
| `adjust_harmonic_color` | `[执行]` | Adjust harmonic quality/mode |
| `apply_swing` | `[执行]` | Apply swing feel to a track |
| `apply_rubato` | `[执行]` | Apply tempo rubato curve |

### Version Management Tools (4)

| Tool | Category | Description |
|------|----------|-------------|
| `project_snapshot` | `[执行]` | Create version snapshot |
| `diff_versions` | `[执行]` | Compare two project versions (shows only changed tracks) |
| `rollback_to_version` | `[执行]` | Rollback to a specific version |
| `list_versions` | `[执行]` | List all version snapshots (merged from disk + memory) |

### Render Tools (2)

| Tool | Category | Description |
|------|----------|-------------|
| `render_preview` | `[执行]` | Quick low-quality preview render (MIDI tracks auto-synthesized) |
| `render_final` | `[执行]` | Full-quality final render (MIDI tracks auto-synthesized) |

### Preference & Feedback Tools (5)

| Tool | Category | Description |
|------|----------|-------------|
| `feedback_submit` | `[执行]` | Submit user rating (1-5) for a version |
| `feedback_ab_test` | `[执行]` | Submit A/B test preference |
| `list_feedback` | `[执行]` | List all feedback with scores, AB tests, adoption rate, replay counts |
| `track_replay` | `[执行]` | Record a replay event for a version |
| `track_favorite` | `[执行]` | Record/toggle favorite status for a version |

### Critic Analysis Tools (6)

| Tool | Category | Description |
|------|----------|-------------|
| `analyze_harmony` | `[评价]` | Harmonic function, tension curve analysis |
| `analyze_melody` | `[评价]` | Motif, contour, interval analysis |
| `analyze_rhythm` | `[评价]` | Groove, density, stability analysis |
| `analyze_audio` | `[评价]` | Spectral, dynamic, spatial analysis |
| `analyze_vocal_quality` | `[评价]` | Pitch deviation vs target MIDI, electrical/robotic artifacts, voicing breaks |
| `adjust_synthesized_pitch` | `[执行]` | Localized pitch correction on synthesized audio segment |

### LLM Tools (13)

| Tool | Category | Purpose |
|------|----------|---------|
| `llm_chat` | `[执行]` | General LLM chat (auto-routing) |
| `llm_stream` | `[执行]` | Streaming LLM chat |
| `llm_generate_lyrics` | `[生成]` | Lyrics generation |
| `llm_compose_song` | `[生成]` | End-to-end song composition with synthesis |
| `llm_suggest_arrangement` | `[编排]` | Arrangement suggestions |
| `llm_analyze_lyrics` | `[评价]` | Lyric analysis (sentiment, themes) |
| `llm_compose_music` | `[生成]` | Direct MIDI composition from description |
| `llm_list_providers` | `[执行]` | Provider listing |
| `llm_list_models` | `[执行]` | Model listing |
| `llm_usage_stats` | `[执行]` | Usage statistics (persistent across restarts) |
| `llm_parse_intent` | `[编排]` | NL → Music Semantic IR |
| `llm_query_knowledge_graph` | `[编排]` | Knowledge graph concept → parameter mapping |
| `llm_compose_from_intent` | `[生成]` | IR → Arrangement with MIDI notes |
| `llm_analyze_music` | `[评价]` | Multi-domain music critic (aggregates all 4 modules) |
| `llm_request_checkpoint` | `[执行]` | Human checkpoint request (mandatory/optional) |

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

## Parameter Mapping

Physical parameter reference for AI agents — query via `parameter_reference` tool:

```python
from cantiodaw.music.parameter_mapping import (
    MIDI_CC_MAP,           # MIDI CC → DAW tool mapping (10 standard CCs)
    INSTRUMENT_TO_PROGRAM, # Instrument name → GM program number (80+ instruments)
    PARAMETER_REFERENCE,   # adjust_* tool input → physical effect reference
    resolve_instrument,    # Resolve name to program: "violin" → 40
)
```

## SoundFont Real-Instrument Synthesis

MIDI tracks can be rendered through SoundFont (.sf2/.sf3) files via FluidSynth for real instrument sounds, with automatic oscillator fallback:

```python
from cantiodaw.synthesis.soundfont import SoundFontSynth

# Auto-detect SoundFont files from data/soundfonts/
synth = SoundFontSynth.create()

# Render MIDI notes with GM program (0=piano, 40=violin, 48=strings)
audio = synth.render(notes, tempo=120, program=0)

# Check if FluidSynth is available
print(synth.available)  # True if pyfluidsynth loaded, False uses oscillator fallback
```

SoundFont support:
- **FluidSynth path**: Install `pyfluidsynth` + native FluidSynth library → real instrument rendering
- **Oscillator fallback**: If FluidSynth unavailable → sine/triangle/sawtooth oscillators
- **Auto-download**: `download_soundfont` tool → FluidR3_GM.sf2 (144 MB, 128 GM instruments)
- **Per-clip program**: Each MIDI clip can specify its own GM program for multi-instrument tracks

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
| `critic_revise` | Snapshot → Revision loop (auto-analyze→fix→re-check) → Snapshot → Preview |
| `full_pipeline` | NL → IR → Compose → Critic → Revision (auto-loop) → Diff → Final export |

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
Generate → Critic → revision_execute (auto-loop: analyze→fix→re-check) → Preview
→ Iteration with convergence control (max 5 rounds, threshold 0.8)
```

### Full Pipeline
```
"凌晨三点开车…孤独但希望"
→ Auto compose → Auto critique → Auto revise (convergence loop) → Final export
→ Human feedback collected (ratings, favorites, replays)
```

## Convergence Control (Revision Loop)

The `revision_execute` tool runs the critic→fix→re-check loop automatically:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Max iterations | 5 | Hard stop after this many rounds |
| Quality threshold | 0.8 (severity) | If average severity drops below threshold, stop |
| No-improvement limit | 3 consecutive rounds | If severity doesn't decrease for 3 rounds, stop |
| Re-check | per-iteration | After each fix round, re-run all critics and compare |

When the loop stops but hasn't converged:
- If a `request_checkpoint` (type=`mandatory`) was placed, pause and wait for human decision
- Otherwise, output the **best version seen so far**

## Preference Feedback

Collected data flows through:

```
User rating (1-5) / A/B test / Replay / Favorite
         ↓
PreferenceCollector  →  JSONL storage (feedback.jsonl / abtest.jsonl / replays.jsonl / favorites.jsonl)
         ↓
list_feedback  →  returns all data (scores, AB tests, replay counts, favorite status)
         ↓
PreferenceModel.train(samples)  →  learns feature weights
         ↓
PreferenceModel.adjust_critic_score(critic_score, features)
         ↓
Weighted score used in Revision Agent's convergence check
```

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

### Scenario 2: Iterative Arrangement

```
1. Run full_pipeline: compose → critic → revision_execute (auto-loop) → export .mid
2. Open in DAW, listen
3. If a section's chord progression is wrong:
   - Option A: adjust prompt and regenerate that section only
   - Option B: edit MIDI directly in DAW, keep the rest
4. Repeat until structure is right
```

### Scenario 3: Vocal Synthesis Front-End

```
1. CantioDAW composes + generates lyric phonemes
2. synthesize → raw vocal WAV stem
3. Import vocal stem into DAW as an audio track
4. Build accompaniment around it in DAW
5. Use adjust_synthesized_pitch for pitch correction without retraining
```

### Scenario 4: Analysis Assistant

```
DAW: Export your finished MIDI arrangement
CantioDAW: Run analyze_harmony / analyze_melody / analyze_rhythm
           → "Bridge section: dominant chord ratio too low (12%)"
           → "Melody: large leaps in bars 17-20"
DAW: Go back and fix those specific bars
```

### Summary

| CantioDAW does (offline) | DAW does (real-time) |
|--------------------------|----------------------|
| NL → structured arrangement | VST instrument playback |
| Multi-track MIDI generation | Audio recording & editing |
| Harmony/melody/rhythm/audio/vocal analysis | Mixing, FX, mastering |
| Voice synthesis (raw WAV) | Arrangement fine-tuning |
| Version diff & rollback | Live performance |
| SoundFont real-instrument rendering | |

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
| **WAV — SoundFont** (`.wav`) | `synthesize_midi` via FluidSynth | Real instrument sound via GM SoundFont (.sf2). Requires pyfluidsynth + .sf2 file |
| **WAV — Synth Preview** (`.wav`) | `synthesize_midi` oscillator fallback | Basic waveform (sine/triangle/sawtooth oscillators). Quick preview when no SoundFont available |
| **WAV — Neural SVC** (`.wav`) | `synthesize` with trained SVC/RVC model | Neural vocoder singing voice output. Quality depends on voice model training |
| **JSON** | Critics, IR, version diff, feedback tools | Analysis results, IR data, version diffs, preference records |

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
- Optional: `pip install pyfluidsynth` for SoundFont real-instrument synthesis

## Project Structure

```
cantiodaw/
├── music/                     # Music IR, Knowledge Graph, Parameter Mapping
│   ├── ir.py                 # MusicIR data structures (Python truth source)
│   ├── knowledge_graph.py    # Graph query engine
│   ├── knowledge_graph.yaml  # 11 concept nodes
│   ├── parameter_mapper.py   # Emotion → parameter mapping tables
│   ├── parameter_mapping.py  # MIDI CC→DAW, instrument→GM, adjust_* reference
│   └── labels.py             # Emotion/Scene/Style label taxonomies
├── critic/                    # 5-module music analysis
│   ├── harmony.py            # Chord function, tension curve
│   ├── melody.py             # Motif detection, interval analysis
│   ├── rhythm.py             # Groove, density, stability
│   ├── audio.py              # Spectral, dynamic, spatial analysis
│   └── vocal.py              # Pitch deviation, electrical artifacts, voicing breaks
├── synthesis/                 # Audio synthesis
│   ├── svs_engine.py         # Singing voice synthesis engine
│   ├── lyrics_aligner.py     # Lyrics-to-phoneme alignment
│   ├── soundfont.py          # SoundFontSynth (FluidSynth + oscillator fallback)
│   └── sf2_download.py       # FluidR3_GM.sf2 auto-download
├── preference/                # Human feedback learning
│   ├── collector.py          # Rating, A/B test, adoption, replay, favorite tracking
│   └── model.py              # Preference weighting model
├── versioning/                # Project version management
│   └── version.py            # Version snapshots, diff, rollback (disk + memory)
└── config.yaml               # Project configuration (paths, synthesis, training, webui)

ts-orchestrator/
├── src/
│   ├── mcp/tools.ts          # 57 DAW/MIDI tool definitions
│   ├── llm/tools.ts          # 13 LLM tool definitions
│   ├── llm/prompts/          # Intent parser + composer prompts
│   ├── music/ir.ts           # TypeScript MusicIR mirror + labels
│   ├── orchestrator/
│   │   ├── composer.ts       # Composer Agent (IR → arrangement)
│   │   ├── revision.ts       # Revision Agent (prioritize + fix)
│   │   ├── workflows.ts      # 7 predefined workflows
│   │   └── engine.ts         # Workflow execution engine
│   └── bridge/               # Python ↔ TypeScript bridge (stdio JSON-RPC)
```

## Limitations

- **Not a real-time DAW** — all processing is offline/batch. Does not replace Ableton, REAPER, FL Studio, or similar for live recording, mixing, or real-time production.
- **WAV synthesis has multiple quality tiers**: SoundFont (FluidSynth + .sf2 = real instruments) > Neural SVC (trained model dependent) > Oscillator (basic waveforms for preview).
- **LLM-dependent composition** — arrangement quality varies by model and prompt. Results require human review and editing.
- **Research-grade** — suitable for experimentation with AI-driven composition and voice synthesis, not for commercial music production out of the box.

## License

Apache 2.0
