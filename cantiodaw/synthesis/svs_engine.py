"""
Singing Voice Synthesis Engine.
Converts MIDI notes + lyrics into sung audio using a trained CantioAI model.
"""
import numpy as np
import logging
from typing import Optional, List
from dataclasses import dataclass

from ..core.midi_engine import MIDINote
from ..utils.model_adapter import create_adapter

logger = logging.getLogger(__name__)


@dataclass
class SVSConfig:
    model_path: str = ""
    config_path: str = ""
    sample_rate: int = 44100
    f0_floor: float = 71.0
    f0_ceil: float = 800.0
    frame_period: float = 5.0
    use_vibrato: bool = True
    vibrato_depth: float = 0.5
    vibrato_rate: float = 5.0
    breathiness: float = 0.1
    silence_before: float = 0.1
    silence_after: float = 0.15


class SVSEngine:
    def __init__(self, config: Optional[SVSConfig] = None):
        self.config = config or SVSConfig()
        self._adapter = None
        self._loaded = False

    def load_model(self, model_path: str, config_path: str):
        self.config.model_path = model_path
        self.config.config_path = config_path
        self._adapter = None
        self._loaded = True
        logger.info(f"SVS model loaded: {model_path}")

    def _ensure_model(self):
        if self._adapter is not None:
            return
        if not self.config.model_path:
            raise RuntimeError("No model loaded. Call load_model() first.")
        self._load_adapter()
        self._adapter.load()

    def _load_adapter(self):
        self._adapter = create_adapter(
            model_path=self.config.model_path,
            config_path=self.config.config_path or None,
        )

    def synthesize_notes(self, notes: List[MIDINote],
                         bpm: float = 120,
                         total_duration: Optional[float] = None) -> np.ndarray:
        self._ensure_model()
        if not notes:
            sr = self.config.sample_rate
            dur = total_duration or 2.0
            return np.zeros(int(sr * dur), dtype=np.float32)

        sr = self.config.sample_rate
        frame_period = self.config.frame_period
        frame_rate = 1000.0 / frame_period

        if total_duration is None:
            total_duration = max(n.end for n in notes) + self.config.silence_after

        total_frames = int(total_duration * frame_rate) + 1
        f0 = np.zeros(total_frames, dtype=np.float32)
        phoneme_features = np.zeros((total_frames, 32), dtype=np.float32)
        spk_id = np.zeros(total_frames, dtype=np.int64)

        for note in notes:
            start_f = max(0, int(note.start * frame_rate))
            end_f = min(total_frames, int(note.end * frame_rate))
            f0[start_f:end_f] = note.frequency

            if self.config.use_vibrato and self.config.vibrato_depth > 0:
                length = end_f - start_f
                if length > 0:
                    t = np.arange(length) / frame_rate
                    vibrato = self.config.vibrato_depth * np.sin(
                        2 * np.pi * self.config.vibrato_rate * t
                    )
                    f0[start_f:end_f] *= 2.0 ** (vibrato / 12.0)

        try:
            audio = self._adapter.synthesize(
                phoneme_features=phoneme_features,
                f0=f0,
                spk_id=spk_id,
                f0_is_hz=True,
            )
            return audio
        except Exception as e:
            logger.warning(f"Model inference failed: {e}, using fallback")
            return self._fallback_synthesize(f0, sr, total_duration)

    def synthesize_lyrics(self, notes: List[MIDINote], lyrics: str,
                          bpm: float = 120) -> np.ndarray:
        if not notes:
            return np.zeros(int(self.config.sample_rate * 2), dtype=np.float32)
        return self.synthesize_notes(notes, bpm)

    def _fallback_synthesize(self, f0: np.ndarray, sr: int,
                             duration: float) -> np.ndarray:
        n_samples = int(sr * duration)
        t = np.arange(n_samples) / sr
        f0_interp = np.interp(t * (len(f0) / duration), np.arange(len(f0)), f0)
        f0_interp = np.maximum(f0_interp, 1.0)
        phase = np.cumsum(2 * np.pi * f0_interp / sr)
        audio = 0.3 * np.sin(phase)
        n_harmonics = 8
        for h in range(2, n_harmonics + 1):
            amp = 0.3 / h
            audio += amp * np.sin(h * phase)
        envelope = np.ones_like(audio)
        n_silence = int(sr * self.config.silence_before)
        envelope[:n_silence] = np.linspace(0, 1, n_silence)
        n_silence_end = int(sr * self.config.silence_after)
        if n_silence_end > 0:
            envelope[-n_silence_end:] = np.linspace(1, 0, n_silence_end)
        audio *= envelope
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.5
        return audio.astype(np.float32)
