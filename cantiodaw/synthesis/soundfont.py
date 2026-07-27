"""SoundFont-based synthesis engine with oscillator fallback."""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────
GM_INSTRUMENTS: Dict[int, str] = {
    0: "Acoustic Grand Piano",
    1: "Bright Acoustic Piano",
    24: "Acoustic Guitar (nylon)",
    25: "Acoustic Guitar (steel)",
    40: "Violin",
    41: "Viola",
    42: "Cello",
    48: "String Ensemble 1",
    49: "String Ensemble 2",
    56: "Trumpet",
    66: "Tenor Sax",
    68: "Oboe",
    73: "Flute",
    88: "Pad 1 (new age)",
    89: "Pad 2 (warm)",
    90: "Pad 3 (polysynth)",
}

DEFAULT_SF2_URL = (
    "https://musical-artifacts.com/artifacts/516/FluidR3_GM.sf2"
)
DEFAULT_SF2_FILENAME = "FluidR3_GM.sf2"


# ── Utility ────────────────────────────────────────
def _find_sf2_paths(config_soundfonts_dir: Optional[str] = None) -> List[Path]:
    candidates = []
    if config_soundfonts_dir:
        candidates.append(Path(config_soundfonts_dir))
    candidates.extend([
        Path("data/soundfonts"),
        Path.home() / ".cantiodaw" / "soundfonts",
        Path(os.environ.get("CANTIODAW_ROOT", ".")) / "data" / "soundfonts",
    ])
    sf2_files = []
    for d in candidates:
        if d.is_dir():
            for f in d.glob("*.sf2"):
                sf2_files.append(f)
            for f in d.glob("*.sf3"):
                sf2_files.append(f)
    return sf2_files


def _try_load_soundfont(path: str) -> object:
    for mod_name in ("fluidsynth", "pyfluidsynth"):
        try:
            fs = __import__(mod_name)
            synth = fs.Synth()
            synth.start()
            sfid = synth.sfload(path)
            if sfid < 0:
                synth.delete()
                raise RuntimeError(f"Failed to load SoundFont: {path}")
            return synth
        except ImportError:
            continue
        except Exception:
            continue
    return None


# ── SoundFont Synth ──────────────────────────────
class SoundFontSynth:
    def __init__(self, soundfont_path: Optional[str] = None, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self._synth = None
        self._sfid = -1
        self._available = False
        self.soundfont_path = soundfont_path

        if soundfont_path:
            self._load(soundfont_path)

    def _load(self, path: str) -> bool:
        if not os.path.isfile(path):
            logger.warning(f"SoundFont not found: {path}")
            return False
        synth = _try_load_soundfont(path)
        if synth is not None:
            self._synth = synth
            self._sfid = synth.sfload(path)
            self.soundfont_path = path
            self._available = True
            logger.info(f"Loaded SoundFont: {path}")
            return True
        logger.warning("pyfluidsynth/fluidsynth not available; using oscillator fallback")
        return False

    @property
    def available(self) -> bool:
        return self._available

    def list_instruments(self) -> List[Dict]:
        if not self._available:
            return [{"program": p, "name": n} for p, n in sorted(GM_INSTRUMENTS.items())]
        result = []
        try:
            for bank in range(0, 2):
                for prog in range(0, 128):
                    name = self._synth.sfpreset_name(self._sfid, bank, prog)
                    if name and name.strip():
                        result.append({"program": prog, "bank": bank, "name": name})
        except Exception:
            pass
        return result

    def render(
        self,
        notes: List[Dict],
        tempo: float = 120.0,
        program: int = 0,
        bank: int = 0,
    ) -> np.ndarray:
        if self._available:
            return self._render_fluidsynth(notes, tempo, program, bank)
        return self._render_oscillator(notes, tempo)

    def _render_fluidsynth(
        self,
        notes: List[Dict],
        tempo: float,
        program: int,
        bank: int,
    ) -> np.ndarray:
        beats_per_sec = tempo / 60.0
        total_duration = 0.0
        note_events = []
        for n in notes:
            pitch = int(n.get("pitch", 60))
            start_beats = float(n.get("start", 0))
            dur_beats = float(n.get("duration", 1))
            velocity = int(n.get("velocity", 80))
            start_sec = start_beats / beats_per_sec
            dur_sec = dur_beats / beats_per_sec
            end_sec = start_sec + dur_sec
            note_events.append((start_sec, dur_sec, pitch, velocity))
            if end_sec > total_duration:
                total_duration = end_sec

        total_samples = max(int(total_duration * self.sample_rate) + self.sample_rate, self.sample_rate)
        audio = np.zeros((total_samples, 2), dtype=np.float32)

        self._synth.program_select(0, self._sfid, bank, program)
        frames_per_chunk = 512

        # Schedule all notes upfront
        for start_sec, dur_sec, pitch, velocity in note_events:
            self._synth.noteon(0, pitch, velocity)

        for chunk_start in range(0, total_samples, frames_per_chunk):
            chunk_end = min(chunk_start + frames_per_chunk, total_samples)
            chunk_size = chunk_end - chunk_start
            chunk_time = chunk_start / self.sample_rate

            l_arr = np.zeros(chunk_size, dtype=np.float32)
            r_arr = np.zeros(chunk_size, dtype=np.float32)
            self._synth.write_float(chunk_time, chunk_size, l_arr, 0, 1, r_arr, 0, 1)
            chunk = np.column_stack([l_arr, r_arr])
            audio[chunk_start:chunk_end] = chunk.astype(np.float32)

            for start_sec, dur_sec, pitch, velocity in note_events:
                note_end = start_sec + dur_sec
                if chunk_time <= note_end < chunk_time + chunk_size / self.sample_rate:
                    self._synth.noteoff(0, pitch)

        # Normalize
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.95
        return audio

    def _render_oscillator(self, notes: List[Dict], tempo: float) -> np.ndarray:
        sr = self.sample_rate
        beats_per_sec = tempo / 60.0
        total_duration = 0.0
        note_events = []
        for n in notes:
            pitch = int(n.get("pitch", 60))
            start_beats = float(n.get("start", 0))
            dur_beats = float(n.get("duration", 1))
            velocity = int(n.get("velocity", 80))
            ntype = str(n.get("type", n.get("track", "melody")))
            freq = 440.0 * (2.0 ** ((pitch - 69) / 12.0))
            start_sec = start_beats / beats_per_sec
            dur_sec = dur_beats / beats_per_sec
            end_sec = start_sec + dur_sec
            note_events.append((start_sec, end_sec, freq, velocity / 127.0, ntype))
            if end_sec > total_duration:
                total_duration = end_sec

        total_samples = int(total_duration * sr) + sr
        audio = np.zeros(total_samples, dtype=np.float64)
        t = np.arange(total_samples) / sr

        for start_sec, end_sec, freq, amp, ntype in note_events:
            start_idx = int(start_sec * sr)
            end_idx = int(end_sec * sr)
            if end_idx > len(audio):
                end_idx = len(audio)
            n_len = end_idx - start_idx
            if n_len <= 0:
                continue
            local_t = t[:n_len]

            if "bass" in ntype:
                tone = np.sin(2 * np.pi * freq * local_t)
                amp *= 0.5
                env_attack = int(0.01 * sr)
                env_release = int(0.1 * sr)
            elif "chord" in ntype:
                tone = (0.4 * np.sin(2 * np.pi * freq * local_t)
                      + 0.3 * np.sin(2 * np.pi * freq * 2 * local_t)
                      + 0.2 * np.sin(2 * np.pi * freq * 3 * local_t))
                amp *= 0.25
                env_attack = int(0.05 * sr)
                env_release = int(0.2 * sr)
            else:
                tone = 2 * np.abs(2 * (local_t * freq - np.floor(local_t * freq + 0.5))) - 1
                amp *= 0.4
                env_attack = int(0.02 * sr)
                env_release = int(0.05 * sr)

            envelope = np.ones(n_len, dtype=np.float64)
            if env_attack < n_len:
                envelope[:env_attack] = np.linspace(0, 1, env_attack)
            if env_release < n_len:
                envelope[-env_release:] = np.linspace(1, 0, env_release)

            audio[start_idx:end_idx] += tone * amp * envelope

        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.95
        return audio.astype(np.float32)

    @classmethod
    def create(
        cls,
        soundfont_path: Optional[str] = None,
        config_soundfonts_dir: Optional[str] = None,
        sample_rate: int = 44100,
    ) -> SoundFontSynth:
        if soundfont_path and os.path.isfile(soundfont_path):
            return cls(soundfont_path=soundfont_path, sample_rate=sample_rate)

        sf2_files = _find_sf2_paths(config_soundfonts_dir)
        if sf2_files:
            for sf2 in sf2_files:
                synth = cls(soundfont_path=str(sf2), sample_rate=sample_rate)
                if synth.available:
                    return synth

        return cls(soundfont_path=None, sample_rate=sample_rate)
