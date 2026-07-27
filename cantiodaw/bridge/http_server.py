"""HTTP bridge — exposes CantioDAW MCP tools as OpenAI-compatible function calling endpoints.

Start with:
    python -m cantiodaw.bridge.http_server --port 9876

Supports:
    GET  /v1/tools          List all tools in OpenAI function format
    POST /v1/chat/completions  OpenAI API-compatible endpoint (tools-only, no chat)
"""

from __future__ import annotations

import sys
import os
import json
import logging
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Tool schema builder ────────────────────────────

_TOOLS = []


def register_tool(name: str, description: str, parameters: dict):
    _TOOLS.append({
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    })


def _build_tools():
    """Register all CantioDAW tools."""
    register_tool("project_create", "[执行] Create a new CantioDAW project", {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Project name"},
            "bpm": {"type": "number", "description": "Tempo in BPM (default 120)", "default": 120},
        },
        "required": ["name"],
    })
    register_tool("project_list", "[执行] List all CantioDAW projects", {
        "type": "object", "properties": {},
    })
    register_tool("project_load", "[执行] Load project details", {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Project name"}},
        "required": ["name"],
    })
    register_tool("project_delete", "[执行] Delete a project", {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    })
    register_tool("project_export", "[执行] Export a project to audio files", {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Project name"},
            "output": {"type": "string", "description": "Output directory or file path"},
            "format": {"type": "string", "enum": ["wav", "flac"], "default": "wav"},
        },
        "required": ["name"],
    })
    register_tool("track_add", "[执行] Add a track to a project", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "name": {"type": "string", "description": "Track name"},
            "type": {"type": "string", "enum": ["audio", "midi"], "default": "audio"},
            "color": {"type": "string", "description": "Hex color"},
        },
        "required": ["project", "name"],
    })
    register_tool("track_remove", "[执行] Remove a track from a project", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
        },
        "required": ["project", "track_id"],
    })
    register_tool("track_update", "[执行] Update track properties (volume, mute, name)", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "name": {"type": "string"},
            "volume": {"type": "number", "minimum": 0, "maximum": 2},
            "muted": {"type": "boolean"},
        },
        "required": ["project", "track_id"],
    })
    register_tool("track_add_clip", "[执行] Add a clip (MIDI notes, chords, or audio reference) to a track", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "notes": {"type": "array", "items": {"type": "object"}},
            "chords": {"type": "array", "items": {"type": "string"}},
            "path": {"type": "string"},
            "start": {"type": "number", "default": 0},
            "duration": {"type": "number"},
        },
        "required": ["project", "track_id"],
    })
    register_tool("synthesize_midi", "[生成] Synthesize multi-track arrangement to WAV via SoundFont or oscillator", {
        "type": "object",
        "properties": {
            "notes": {"type": "array", "items": {"type": "object"}},
            "tempo": {"type": "number", "default": 120},
            "output_path": {"type": "string", "default": "synthesized.wav"},
            "sample_rate": {"type": "integer", "default": 24000},
            "soundfont_path": {"type": "string"},
            "program": {"type": "integer", "default": 0},
            "bank": {"type": "integer", "default": 0},
        },
        "required": ["notes"],
    })
    register_tool("mix_tracks", "[执行] Mix multiple tracks in a project to a single audio file", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_ids": {"type": "array", "items": {"type": "string"}},
            "output_path": {"type": "string", "default": "mixdown.wav"},
            "soundfont_path": {"type": "string"},
        },
        "required": ["project"],
    })
    register_tool("export_stems", "[执行] Export each track in a project as a separate audio stem", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "output_dir": {"type": "string"},
        },
        "required": ["project", "output_dir"],
    })
    register_tool("effect_apply", "[执行] Apply an audio effect (reverb, EQ, compressor) to audio data", {
        "type": "object",
        "properties": {
            "audio": {"type": "array", "items": {"type": "number"}},
            "sample_rate": {"type": "integer", "default": 24000},
            "type": {"type": "string", "enum": ["reverb", "eq", "compressor"]},
        },
        "required": ["audio", "type"],
    })
    register_tool("render_preview", "[执行] Quick preview render at low quality", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "output_path": {"type": "string", "default": "preview.wav"},
            "soundfont_path": {"type": "string"},
        },
        "required": ["project"],
    })
    register_tool("render_final", "[执行] Full quality final render", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "output_path": {"type": "string", "default": "final.wav"},
            "sample_rate": {"type": "integer", "default": 44100},
            "soundfont_path": {"type": "string"},
        },
        "required": ["project"],
    })
    register_tool("project_snapshot", "[执行] Create a version snapshot", {
        "type": "object",
        "properties": {"project": {"type": "string"}},
        "required": ["project"],
    })
    register_tool("list_versions", "[执行] List all version snapshots", {
        "type": "object",
        "properties": {"project": {"type": "string"}},
        "required": ["project"],
    })
    register_tool("diff_versions", "[执行] Compare two project versions", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "v1": {"type": "string"},
            "v2": {"type": "string"},
        },
        "required": ["project", "v1", "v2"],
    })
    register_tool("rollback_to_version", "[执行] Rollback to a specific version", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "version": {"type": "string"},
        },
        "required": ["project", "version"],
    })
    register_tool("analyze_harmony", "[评价] Run harmony analysis on a project track", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "chords": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["project"],
    })
    register_tool("analyze_melody", "[评价] Run melody analysis on a project track", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "pitches": {"type": "array", "items": {"type": "integer"}},
        },
        "required": ["project"],
    })
    register_tool("analyze_rhythm", "[评价] Run rhythm analysis on a project track", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
        },
        "required": ["project"],
    })
    register_tool("analyze_audio", "[评价] Run audio quality analysis on a project track or audio file", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "audio_path": {"type": "string"},
        },
    })
    register_tool("analyze_vocal_quality", "[评价] Analyze synthesized vocal quality", {
        "type": "object",
        "properties": {
            "audio_path": {"type": "string"},
            "target_pitches": {"type": "array"},
            "sample_rate": {"type": "integer", "default": 44100},
        },
        "required": ["audio_path"],
    })
    register_tool("adjust_dynamics", "[执行] Adjust dynamics curve for a track section", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "section": {"type": "string"},
            "curve_delta": {"type": "number"},
        },
        "required": ["project", "track_id", "section", "curve_delta"],
    })
    register_tool("adjust_articulation", "[执行] Adjust articulation style and overlap for a note range", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "start": {"type": "number"},
            "end": {"type": "number"},
            "style": {"type": "string", "enum": ["legato", "staccato", "portato", "normal"]},
            "overlap_delta": {"type": "number"},
            "attack_delta_ms": {"type": "number"},
        },
        "required": ["project", "track_id", "start", "end"],
    })
    register_tool("adjust_vibrato", "[执行] Adjust vibrato depth and rate for a note range", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "start": {"type": "number"},
            "end": {"type": "number"},
            "depth_delta": {"type": "number"},
            "rate_delta": {"type": "number"},
        },
        "required": ["project", "track_id", "start", "end"],
    })
    register_tool("adjust_micro_timing", "[执行] Adjust micro-timing offsets for individual notes", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "adjustments": {"type": "array"},
        },
        "required": ["project", "track_id", "adjustments"],
    })
    register_tool("adjust_harmonic_color", "[执行] Adjust harmonic color (quality, mode) for a section", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "section": {"type": "string"},
            "quality_delta": {"type": "string"},
            "mode_shift": {"type": "number"},
        },
        "required": ["project", "section"],
    })
    register_tool("apply_swing", "[执行] Apply swing feel to a track", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "ratio": {"type": "number"},
        },
        "required": ["project", "track_id", "ratio"],
    })
    register_tool("apply_rubato", "[执行] Apply tempo rubato curve to a track", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "track_id": {"type": "string"},
            "curve": {"type": "array"},
        },
        "required": ["project", "track_id", "curve"],
    })
    register_tool("feedback_submit", "[执行] Submit user feedback (score 1-5) for a project version", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "version_id": {"type": "string"},
            "score": {"type": "integer", "minimum": 1, "maximum": 5},
            "comment": {"type": "string"},
        },
        "required": ["project", "version_id", "score"],
    })
    register_tool("list_feedback", "[执行] List all recorded feedback for a project", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
        },
    })
    register_tool("revision_execute", "[编排] Run critic->fix->re-check revision loop with convergence control", {
        "type": "object",
        "properties": {
            "project": {"type": "string"},
            "domains": {"type": "array", "items": {"type": "string"}},
            "max_iterations": {"type": "integer", "default": 5},
            "quality_threshold": {"type": "number", "default": 0.8},
        },
        "required": ["project"],
    })
    register_tool("parameter_reference", "[执行] Query physical parameter mappings", {
        "type": "object",
        "properties": {
            "tool": {"type": "string"},
            "instrument": {"type": "string"},
            "list_instruments": {"type": "boolean"},
        },
    })
    register_tool("list_soundfonts", "[执行] List available SoundFont (.sf2/.sf3) files", {
        "type": "object", "properties": {},
    })
    register_tool("download_soundfont", "[执行] Download FluidR3_GM.sf2 SoundFont file", {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "dest_dir": {"type": "string"},
            "filename": {"type": "string", "default": "FluidR3_GM.sf2"},
        },
    })
    register_tool("midi_notes_to_f0", "[执行] Convert MIDI notes to an F0 contour for synthesis", {
        "type": "object",
        "properties": {
            "notes": {"type": "array", "items": {"type": "object"}},
            "frame_rate": {"type": "integer", "default": 100},
            "total_frames": {"type": "integer", "default": 1000},
        },
        "required": ["notes"],
    })


_build_tools()


# ── Tool executor ─────────────────────────────────

def _get_handler():
    """Import the Python bridge handler."""
    root = os.environ.get("CANTIODAW_ROOT", os.getcwd())
    if root not in sys.path:
        sys.path.insert(0, root)
    bridge_path = os.path.join(root, "ts-orchestrator", "src", "bridge", "python_bridge.py")
    if os.path.isfile(bridge_path):
        # Execute the bridge module to get handle function
        import importlib.util
        spec = importlib.util.spec_from_file_location("python_bridge", bridge_path)
        # Need to set up the environment before importing
        old_argv = sys.argv[:]
        sys.argv = [bridge_path, root]
        try:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.handle
        finally:
            sys.argv = old_argv
    # Fallback: try importing from cantiodaw
    raise RuntimeError(f"Bridge not found. Set CANTIODAW_ROOT. Tried: {bridge_path}")


def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a CantioDAW tool via the Python bridge."""
    handle = _HANDLER
    try:
        result = handle(name, arguments, "")
        return result
    except Exception:
        return {"success": False, "data": None, "error": traceback.format_exc()}


_HANDLER = None


def _init_handler():
    global _HANDLER
    if _HANDLER is None:
        _HANDLER = _get_handler()


# ── Flask app ──────────────────────────────────────

def create_app():
    _init_handler()
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route("/v1/tools", methods=["GET"])
    def list_tools():
        return jsonify({"tools": _TOOLS, "count": len(_TOOLS)})

    @app.route("/v1/chat/completions", methods=["POST"])
    def chat_completions():
        body = request.get_json(force=True, silent=True) or {}
        messages = body.get("messages", [])
        tool_calls = body.get("tool_calls", [])

        if tool_calls:
            results = []
            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                res = execute_tool(name, args)
                results.append({
                    "id": tc.get("id", "call_0"),
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps(args, ensure_ascii=False),
                    },
                    "output": json.dumps(res, ensure_ascii=False),
                })
            return jsonify({
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "tool",
                        "tool_calls": results,
                    },
                }],
            })

        # For direct tool invocation without chat
        last_msg = messages[-1] if messages else {}
        tool_name = body.get("tool")
        if tool_name:
            args = body.get("arguments", {})
            res = execute_tool(tool_name, args)
            return jsonify(res)

        return jsonify({
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "CantioDAW HTTP Bridge ready. Use /v1/tools to list tools, POST tool/arguments for direct calls, or use OpenAI-compatible tool_calls format.",
                },
            }],
        })

    @app.route("/v1/execute", methods=["POST"])
    def execute():
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("tool", body.get("name", ""))
        args = body.get("arguments", body.get("params", {}))
        if not name:
            return jsonify({"error": "Missing tool name"}), 400
        res = execute_tool(name, args)
        return jsonify(res)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "tools": len(_TOOLS)})

    return app


# ── CLI entry point ────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CantioDAW HTTP Bridge")
    parser.add_argument("--port", type=int, default=9876, help="HTTP port (default: 9876)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host (default: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    args = parser.parse_args()

    app = create_app()
    print(f"CantioDAW HTTP Bridge running on http://{args.host}:{args.port}")
    print(f"  Tools: {len(_TOOLS)}")
    print(f"  Endpoints: GET /v1/tools  |  POST /v1/execute  |  POST /v1/chat/completions")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
