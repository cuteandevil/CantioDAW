import numpy as np
import logging
from typing import Optional, List, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    logger.warning("sounddevice not installed. Install with: pip install sounddevice")


class AudioEngine:
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.is_playing = False
        self.is_recording = False
        self.current_position = 0.0
        self._recording_buffer: List[np.ndarray] = []

    def play(self, audio: np.ndarray, blocking: bool = False):
        if not HAS_SOUNDDEVICE:
            logger.warning("sounddevice unavailable, cannot play audio")
            return
        self.is_playing = True
        try:
            sd.play(audio, samplerate=self.sample_rate, blocking=blocking)
        except Exception as e:
            logger.error(f"Playback failed: {e}")
        finally:
            self.is_playing = False

    def stop(self):
        if HAS_SOUNDDEVICE:
            sd.stop()
        self.is_playing = False

    def record(self, duration: float = 5.0) -> np.ndarray:
        if not HAS_SOUNDDEVICE:
            logger.warning("sounddevice unavailable, generating silence")
            return np.zeros(int(self.sample_rate * duration), dtype=np.float32)
        self.is_recording = True
        try:
            audio = sd.rec(
                int(self.sample_rate * duration),
                samplerate=self.sample_rate,
                channels=1,
                blocking=True,
            )
            return audio.flatten().astype(np.float32)
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return np.zeros(int(self.sample_rate * duration), dtype=np.float32)
        finally:
            self.is_recording = False

    def load_audio(self, path: str) -> Optional[np.ndarray]:
        path = Path(path)
        if not path.exists():
            logger.error(f"Audio file not found: {path}")
            return None
        try:
            import soundfile as sf
            data, sr = sf.read(str(path))
            if sr != self.sample_rate:
                from ..audio.effects import resample
                data = resample(data, sr, self.sample_rate)
            if data.ndim > 1:
                data = data.mean(axis=1)
            return data.astype(np.float32)
        except ImportError:
            try:
                import librosa
                data, _ = librosa.load(str(path), sr=self.sample_rate, mono=True)
                return data.astype(np.float32)
            except ImportError:
                logger.error("Need soundfile or librosa to load audio")
                return None

    def save_audio(self, path: str, audio: np.ndarray):
        import soundfile as sf
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), audio, self.sample_rate)
        logger.info(f"Audio saved: {path}")

    def get_playback_position(self) -> float:
        if HAS_SOUNDDEVICE and self.is_playing:
            return sd.get_stream().time if hasattr(sd, "get_stream") else 0.0
        return self.current_position

    def apply_fade(self, audio: np.ndarray, fade_in: float = 0.0, fade_out: float = 0.0) -> np.ndarray:
        n = len(audio)
        if fade_in > 0:
            n_in = int(fade_in * self.sample_rate)
            audio[:n_in] *= np.linspace(0, 1, min(n_in, n))
        if fade_out > 0:
            n_out = int(fade_out * self.sample_rate)
            audio[-n_out:] *= np.linspace(1, 0, min(n_out, n))
        return audio
