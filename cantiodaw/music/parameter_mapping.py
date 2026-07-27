"""Physical parameter mapping: MIDI CC → DAW parameters, instrument → SoundFont programs."""

# ── MIDI CC → Physical Parameter Mapping ──────────────────
# Maps standard MIDI CC numbers to CantioDAW tool calls
MIDI_CC_MAP = {
    1: {"name": "Modulation Wheel", "tool": "adjust_vibrato", "params": {"depth_delta": "cc_value / 127"}},
    7: {"name": "Volume", "tool": "track_update", "params": {"volume": "cc_value / 127"}},
    10: {"name": "Pan", "tool": "track_update", "params": {"pan": "(cc_value - 64) / 64"}},
    11: {"name": "Expression", "tool": "adjust_dynamics", "params": {"curve_delta": "(cc_value - 64) / 64"}},
    64: {"name": "Sustain Pedal", "tool": "adjust_articulation", "params": {"overlap_delta": "cc_value / 127"}},
    72: {"name": "Release Time", "tool": "adjust_articulation", "params": {"attack_delta_ms": "-cc_value * 5"}},
    73: {"name": "Attack Time", "tool": "adjust_articulation", "params": {"attack_delta_ms": "cc_value * 5"}},
    74: {"name": "Brightness/Cutoff", "tool": "effect_apply", "params": {"effect": "eq", "high_shelf_gain_db": "(cc_value - 64) / 10"}},
    91: {"name": "Reverb Send", "tool": "effect_apply", "params": {"effect": "reverb", "wet": "cc_value / 127"}},
    93: {"name": "Chorus Send", "tool": "effect_apply", "params": {"effect": "chorus", "depth": "cc_value / 127"}},
}

# ── Note Offset → Timing Adjustment ─────────────────
def velocity_to_dynamics(velocity: int) -> dict:
    """Convert MIDI velocity (0-127) to adjust_dynamics params."""
    normalized = velocity / 127.0
    return {"curve_delta": normalized - 0.5}

def note_offset_to_micro_timing(offset_ms: float) -> dict:
    """Convert note timing offset (ms) to adjust_micro_timing params."""
    return {"adjustments": [{"offset_delta_ms": offset_ms}]}

# ── Instrument Category → GM SoundFont Program ──────
INSTRUMENT_TO_PROGRAM = {
    "piano": 0,
    "bright_piano": 1,
    "electric_piano": 4,
    "harpsichord": 6,
    "clavinet": 7,
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubular_bells": 14,
    "dulcimer": 15,
    "organ": 19,
    "accordion": 21,
    "guitar_nylon": 24,
    "guitar_steel": 25,
    "guitar_electric": 29,
    "guitar_muted": 28,
    "bass_acoustic": 32,
    "bass_electric": 33,
    "bass_slap": 36,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "harp": 46,
    "timpani": 47,
    "strings": 48,
    "strings_slow": 49,
    "synth_strings": 50,
    "choir": 52,
    "voice_oohs": 53,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "horn": 60,
    "sax_alto": 65,
    "sax_tenor": 66,
    "sax_baritone": 67,
    "oboe": 68,
    "bassoon": 70,
    "clarinet": 71,
    "flute": 73,
    "recorder": 74,
    "pan_flute": 75,
    "lead_square": 80,
    "lead_sawtooth": 81,
    "pad_warm": 89,
    "pad_polysynth": 90,
    "fx_rain": 96,
    "fx_soundtrack": 97,
    "fx_crystal": 98,
    "sitar": 104,
    "banjo": 105,
    "shamisen": 106,
    "koto": 107,
    "kalimba": 108,
    "bagpipe": 109,
    "fiddle": 110,
    "shanai": 111,
    "steel_drums": 114,
    "woodblock": 115,
    "taiko_drum": 116,
    "melodic_tom": 117,
    "synth_drum": 118,
    "drum_kit": 0,
}

# ── Parameter Reference: adjust_* tools input → physical effect ──
PARAMETER_REFERENCE = {
    "adjust_dynamics": {
        "parameters": {
            "curve_delta": "Energy curve shift (-1.0 softer → +1.0 louder). Affects RMS amplitude envelope.",
        },
        "domain": "dynamics",
        "physical_units": "dimensionless [-1.0, 1.0]",
    },
    "adjust_articulation": {
        "parameters": {
            "style": "Articulation style: legato, staccato, normal, varied",
            "overlap_delta": "Note overlap change (-1.0 detached → +1.0 overlapping). Affects note transition smoothness.",
            "attack_delta_ms": "Attack time delta in milliseconds. Negative = faster attack.",
        },
        "domain": "articulation",
        "physical_units": "ms for attack, dimensionless for overlap",
    },
    "adjust_vibrato": {
        "parameters": {
            "depth_delta": "Vibrato depth change (-1.0 no vibrato → +1.0 intense). Affects pitch modulation amplitude.",
            "rate_delta": "Vibrato rate change in Hz. Typical range 4-8 Hz.",
        },
        "domain": "expression",
        "physical_units": "Hz for rate, dimensionless for depth",
    },
    "adjust_micro_timing": {
        "parameters": {
            "adjustments": "Array of {note_index, offset_delta_ms}. Micro-timing offset per note in milliseconds.",
        },
        "domain": "timing",
        "physical_units": "ms",
    },
    "adjust_harmonic_color": {
        "parameters": {
            "quality_delta": "Chord quality shift: +dominant, +resolution, -dissonance, +suspension",
            "mode_shift": "Mode shift: positive = brighter/major, negative = darker/minor",
        },
        "domain": "harmony",
        "physical_units": "dimensionless",
    },
    "apply_swing": {
        "parameters": {
            "ratio": "Swing ratio (0.0 = straight → 1.0 = triplet swing). Affects off-beat timing.",
        },
        "domain": "timing",
        "physical_units": "dimensionless [0.0, 1.0]",
    },
    "apply_rubato": {
        "parameters": {
            "curve": "Array of {beat, tempo_factor}. Tempo variation curve per beat.",
        },
        "domain": "timing",
        "physical_units": "beat index, tempo multiplier",
    },
}

def resolve_instrument(name: str) -> int:
    """Resolve an instrument name to a GM program number. Returns 0 (piano) if unknown."""
    name_lower = name.lower().replace(" ", "_").replace("-", "_")
    for key, prog in INSTRUMENT_TO_PROGRAM.items():
        if key in name_lower or name_lower in key:
            return prog
    return 0

from typing import Optional, Dict

def map_cc_to_tool(cc_number: int, cc_value: int) -> Optional[Dict]:
    """Map a MIDI CC event to a CantioDAW tool call. Returns {tool, params} or None."""
    entry = MIDI_CC_MAP.get(cc_number)
    if not entry:
        return None
    return {"tool": entry["tool"], "cc_name": entry["name"], "value": cc_value}
