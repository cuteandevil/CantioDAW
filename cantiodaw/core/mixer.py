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

    def mix(self, tracks: Dict[str, np.ndarray]) -> np.ndarray:
        max_len = max((len(a) for a in tracks.values()), default=0)
        if max_len == 0:
            return np.zeros(0, dtype=np.float32)

        master = np.zeros(max_len, dtype=np.float32)
        for tid, audio in tracks.items():
            ch = self.channels.get(tid, {})
            if ch.get("mute", False):
                continue
            vol = ch.get("volume", 1.0)
            pan = ch.get("pan", 0.0)
            if len(audio) < max_len:
                audio = np.pad(audio, (0, max_len - len(audio)))
            master += audio * vol * self.master_volume

        peak = np.max(np.abs(master))
        if peak > 1.0:
            master = master / peak * 0.95
        return master

    def set_channel(self, track_id: str, volume: float = 1.0,
                    pan: float = 0.0, mute: bool = False):
        self.channels[track_id] = {"volume": volume, "pan": pan, "mute": mute}
