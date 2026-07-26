from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from ..music.ir import MusicIR, ParameterDelta


@dataclass
class AudioDiagnosis:
    issue: str
    severity: float
    details: List[str] = field(default_factory=list)


@dataclass
class AudioAnalysis:
    rms_energy_curve: Optional[List[float]] = None
    spectral_brightness: float = 0.0
    bass_density: float = 0.0
    mid_clarity: float = 0.0
    crest_factor: float = 0.0
    loudness_range: float = 0.0
    stereo_width: float = 0.0
    reverb_tail: float = 0.0
    diagnoses: List[AudioDiagnosis] = field(default_factory=list)

    def score(self) -> float:
        scores = []
        for d in self.diagnoses:
            scores.append(1.0 - d.severity)
        return sum(scores) / max(len(scores), 1) if scores else 1.0


class AudioCritic:
    def analyze(self, audio: np.ndarray, sample_rate: int = 44100, expected_ir: Optional[MusicIR] = None) -> AudioAnalysis:
        analysis = AudioAnalysis()
        if audio is None or len(audio) == 0:
            return analysis

        analysis.rms_energy_curve = self._calc_rms_curve(audio)
        analysis.stereo_width = self._calc_stereo_width(audio)
        analysis.crest_factor = self._calc_crest_factor(audio)
        analysis.loudness_range = self._calc_loudness_range(audio)
        analysis.spectral_brightness = self._calc_spectral_brightness(audio, sample_rate)
        analysis.bass_density = self._calc_bass_density(audio, sample_rate)
        analysis.mid_clarity = self._calc_mid_clarity(audio, sample_rate)

        if analysis.crest_factor > 0.7:
            analysis.diagnoses.append(AudioDiagnosis(
                issue="动态范围过大",
                severity=0.4,
                details=[f"Crest factor {analysis.crest_factor:.2f}"],
            ))
        if analysis.spectral_brightness < 0.2:
            analysis.diagnoses.append(AudioDiagnosis(
                issue="高频亮度不足",
                severity=0.3,
                details=[f"亮度 {analysis.spectral_brightness:.2f}"],
            ))
        if analysis.bass_density > 0.6:
            analysis.diagnoses.append(AudioDiagnosis(
                issue="低频过于密集",
                severity=0.3,
                details=[f"低频密度 {analysis.bass_density:.2f}"],
            ))
        if expected_ir:
            self._compare_with_ir(audio, expected_ir, analysis)

        return analysis

    def generate_suggestions(self, diagnoses: List[AudioDiagnosis]) -> List[ParameterDelta]:
        suggestions = []
        for d in diagnoses:
            if "动态" in d.issue:
                suggestions.append(ParameterDelta(
                    target="mix.compression", delta=0.2, domain="mix", bounds=[0.0, 1.0],
                ))
            if "亮度" in d.issue:
                suggestions.append(ParameterDelta(
                    target="sound.brightness", delta=0.2, domain="sound", bounds=[0.0, 1.0],
                ))
            if "低频" in d.issue:
                suggestions.append(ParameterDelta(
                    target="sound.sub_bass", delta=-0.2, domain="sound", bounds=[0.0, 1.0],
                ))
        return suggestions

    def _calc_rms_curve(self, audio: np.ndarray, frame_ms: int = 50) -> list:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        sr = 44100
        frame_len = int(sr * frame_ms / 1000)
        if len(audio) < frame_len:
            return [float(np.sqrt(np.mean(audio ** 2)))]
        curves = []
        for i in range(0, len(audio) - frame_len, frame_len):
            frame = audio[i:i + frame_len]
            curves.append(float(np.sqrt(np.mean(frame ** 2))))
        return curves

    def _calc_crest_factor(self, audio: np.ndarray) -> float:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        return float(peak / max(rms, 1e-10) / 10.0)

    def _calc_loudness_range(self, audio: np.ndarray) -> float:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        frame_size = len(audio) // 20
        energies = []
        for i in range(0, len(audio) - frame_size, frame_size):
            frame = audio[i:i + frame_size]
            energies.append(np.sqrt(np.mean(frame ** 2)))
        if not energies:
            return 0.0
        return float(np.std(energies) / max(np.mean(energies), 1e-10))

    def _calc_stereo_width(self, audio: np.ndarray) -> float:
        if len(audio.shape) < 2 or audio.shape[1] < 2:
            return 0.0
        l = audio[:, 0]
        r = audio[:, 1]
        correlation = float(np.corrcoef(l, r)[0, 1]) if len(l) > 1 else 0.0
        return float(max(0.0, 1.0 - abs(correlation)))

    def _calc_spectral_brightness(self, audio: np.ndarray, sr: int) -> float:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        spectrum = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), 1.0 / sr)
        cutoff = sr // 4
        bright = np.sum(spectrum[freqs > cutoff])
        total = np.sum(spectrum)
        return float(bright / max(total, 1e-10))

    def _calc_bass_density(self, audio: np.ndarray, sr: int) -> float:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        spectrum = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), 1.0 / sr)
        bass = np.sum(spectrum[freqs < 150])
        total = np.sum(spectrum)
        return float(bass / max(total, 1e-10))

    def _calc_mid_clarity(self, audio: np.ndarray, sr: int) -> float:
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        spectrum = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), 1.0 / sr)
        mid = np.sum(spectrum[(freqs >= 300) & (freqs <= 3000)])
        total = np.sum(spectrum)
        return float(mid / max(total, 1e-10))

    def _compare_with_ir(self, audio: np.ndarray, ir: MusicIR, analysis: AudioAnalysis) -> None:
        if ir.energy:
            actual_energy = float(np.sqrt(np.mean(audio ** 2)))
            if ir.energy.end > 0.7 and actual_energy < 0.3:
                analysis.diagnoses.append(AudioDiagnosis(
                    issue="能量曲线与期望不符",
                    severity=0.5,
                    details=[f"期望结尾能量 {ir.energy.end:.1f}，实际 {actual_energy:.2f}"],
                ))
