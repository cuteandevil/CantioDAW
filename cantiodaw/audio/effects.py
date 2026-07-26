import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    try:
        import librosa
        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except ImportError:
        ratio = target_sr / orig_sr
        n = int(len(audio) * ratio)
        return np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio)


def apply_reverb(audio: np.ndarray, sr: int, room_size: float = 0.5,
                 decay: float = 0.5, wet: float = 0.3) -> np.ndarray:
    delay_samples = int(sr * 0.03 * room_size)
    if delay_samples < 1:
        return audio
    wet_signal = np.zeros_like(audio)
    for i in range(3):
        offset = delay_samples * (i + 1)
        if offset >= len(audio):
            break
        wet_signal[offset:] += audio[:-offset] * (decay ** (i + 1))
    return audio * (1 - wet) + wet_signal * wet


def apply_eq(audio: np.ndarray, sr: int, low_gain: float = 0.0,
             mid_gain: float = 0.0, high_gain: float = 0.0) -> np.ndarray:
    try:
        import scipy.signal as sig
        nyquist = sr / 2
        sos_low = sig.butter(2, 300 / nyquist, btype="low", output="sos")
        sos_high = sig.butter(2, 3000 / nyquist, btype="high", output="sos")
        low = sig.sosfilt(sos_low, audio)
        high = sig.sosfilt(sos_high, audio)
        mid = audio - low - high
        out = low * (10 ** (low_gain / 20)) + mid * (10 ** (mid_gain / 20)) + high * (10 ** (high_gain / 20))
        return out
    except ImportError:
        return audio


def apply_compressor(audio: np.ndarray, threshold: float = 0.5,
                     ratio: float = 4.0, attack: float = 0.002,
                     release: float = 0.1, sr: int = 44100) -> np.ndarray:
    n = len(audio)
    out = audio.copy()
    envelope = np.zeros(n)
    alpha_attack = np.exp(-1 / (attack * sr))
    alpha_release = np.exp(-1 / (release * sr))
    abs_signal = np.abs(audio)

    env = 0.0
    for i in range(n):
        if abs_signal[i] > env:
            env = alpha_attack * env + (1 - alpha_attack) * abs_signal[i]
        else:
            env = alpha_release * env + (1 - alpha_release) * abs_signal[i]
        envelope[i] = env

    for i in range(n):
        if envelope[i] > threshold:
            gain_reduction = threshold + (envelope[i] - threshold) / ratio
            out[i] *= gain_reduction / max(envelope[i], 1e-10)

    return out


class AudioEffects:
    @staticmethod
    def chain(audio: np.ndarray, sr: int,
              effects: list) -> np.ndarray:
        for eff in effects:
            etype = eff.get("type")
            params = eff.get("params", {})
            if etype == "reverb":
                audio = apply_reverb(audio, sr, **params)
            elif etype == "eq":
                audio = apply_eq(audio, sr, **params)
            elif etype == "compressor":
                audio = apply_compressor(audio, sr, **params)
            elif etype == "gain":
                audio = audio * params.get("gain", 1.0)
            elif etype == "normalize":
                p = np.max(np.abs(audio))
                if p > 0:
                    audio = audio / p * params.get("level", 0.95)
        return audio
