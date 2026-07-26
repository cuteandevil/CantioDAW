import numpy as np
import logging
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class EffectChain:
    def __init__(self):
        self.effects: List[Dict[str, Any]] = []

    def add(self, effect_type: str, params: Optional[Dict] = None):
        self.effects.append({"type": effect_type, "params": params or {}})

    def clear(self):
        self.effects.clear()

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        for eff in self.effects:
            etype = eff["type"]
            params = eff["params"]
            try:
                if etype == "gain":
                    audio = audio * params.get("value", 1.0)
                elif etype == "normalize":
                    peak = np.max(np.abs(audio))
                    if peak > 0:
                        target = params.get("level", 0.95)
                        audio = audio * (target / peak)
                elif etype == "fade_in":
                    n = int(params.get("duration", 0.1) * sample_rate)
                    audio[:n] *= np.linspace(0, 1, min(n, len(audio)))
                elif etype == "fade_out":
                    n = int(params.get("duration", 0.1) * sample_rate)
                    audio[-n:] *= np.linspace(1, 0, min(n, len(audio)))
                elif etype == "dc_remove":
                    audio = audio - np.mean(audio)
            except Exception as e:
                logger.warning(f"Effect {etype} failed: {e}")
        return audio


class Mixer:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.master_volume = 1.0
        self.channels: Dict[str, Dict[str, Any]] = {}

    def _to_nchannels(self, audio: np.ndarray, nch: int) -> np.ndarray:
        if audio.ndim == 1:
            if nch == 1:
                return audio
            return np.column_stack([audio] * nch)
        if audio.ndim == 2:
            if nch == 1:
                return audio.mean(axis=1)
            if audio.shape[1] == nch:
                return audio
            if audio.shape[1] < nch:
                return np.column_stack([audio[:, 0]] * nch)
            return audio[:, :nch]
        return audio

    def mix(self, tracks: Dict[str, np.ndarray]) -> np.ndarray:
        if not tracks:
            return np.zeros(0, dtype=np.float32)

        nch = 1
        for audio in tracks.values():
            if audio.ndim > 1 and audio.shape[1] > nch:
                nch = audio.shape[1]

        max_len = max((a.shape[0] for a in tracks.values()), default=0)

        master = np.zeros((max_len, nch), dtype=np.float32) if nch > 1 else np.zeros(max_len, dtype=np.float32)

        for tid, audio in tracks.items():
            ch = self.channels.get(tid, {})
            if ch.get("mute", False):
                continue
            vol = ch.get("volume", 1.0)
            processed = self._to_nchannels(audio, nch)
            if processed.shape[0] < max_len:
                if nch > 1:
                    processed = np.pad(processed, ((0, max_len - processed.shape[0]), (0, 0)))
                else:
                    processed = np.pad(processed, (0, max_len - processed.shape[0]))
            master += processed * vol * self.master_volume

        peak = np.max(np.abs(master))
        if peak > 1.0:
            master = master / peak * 0.95
        return master

    def set_channel(self, track_id: str, volume: float = 1.0,
                    pan: float = 0.0, mute: bool = False):
        self.channels[track_id] = {"volume": volume, "pan": pan, "mute": mute}

    def add_track(self, path: str, volume: float = 1.0) -> str:
        import soundfile as sf
        track_id = f"track_{len(self.channels)}"
        audio, _ = sf.read(path)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        self.channels[track_id] = {"volume": volume, "pan": 0.0, "mute": False, "audio": audio}
        return track_id

    def mix_down(self, output_path: str) -> str:
        import soundfile as sf
        track_audios = {}
        for tid, ch in self.channels.items():
            if "audio" in ch:
                track_audios[tid] = ch["audio"]
        mixed = self.mix(track_audios)
        sf.write(output_path, mixed, self.sample_rate)
        return output_path
