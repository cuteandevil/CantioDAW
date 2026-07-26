"""Vocal synthesis quality critic: pitch accuracy + artifact detection."""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class VocalDiagnosis:
    problem: str
    severity: float
    details: List[str] = field(default_factory=list)
    time_ranges: List[tuple] = field(default_factory=list)


@dataclass
class VocalAnalysis:
    pitch_deviation_mean_cents: float = 0.0
    pitch_deviation_max_cents: float = 0.0
    pitch_deviation_std_cents: float = 0.0
    on_pitch_ratio: float = 0.0
    artifact_electricity: float = 0.0
    artifact_breathiness: float = 0.0
    artifact_breaks: int = 0
    diagnoses: List[VocalDiagnosis] = field(default_factory=list)

    def score(self) -> float:
        base = 1.0
        for d in self.diagnoses:
            base -= d.severity * 0.3
        return max(0.0, base)


class VocalCritic:
    def analyze(
        self,
        audio: np.ndarray,
        sample_rate: int,
        target_pitches: Optional[List[dict]] = None,
    ) -> VocalAnalysis:
        analysis = VocalAnalysis()

        if audio is None or len(audio) == 0:
            analysis.diagnoses.append(VocalDiagnosis(
                problem="No audio data provided",
                severity=1.0,
                details=["Empty audio array"],
            ))
            return analysis

        try:
            import pyworld as pw
            f0, t = pw.dio(audio.astype(np.float64), sample_rate)
            f0 = pw.stonemask(audio.astype(np.float64), f0, t, sample_rate)
        except ImportError:
            try:
                import librosa
                f0, _, _ = librosa.pyin(audio.astype(np.float64), fmin=65, fmax=2093, sr=sample_rate)
                f0 = np.nan_to_num(f0, nan=0.0)
                t = np.arange(len(f0)) * (len(audio) / sample_rate / len(f0))
            except ImportError:
                analysis.diagnoses.append(VocalDiagnosis(
                    problem="Pitch extraction unavailable",
                    severity=0.5,
                    details=["Install pyworld or librosa for pitch analysis"],
                ))
                return analysis

        voiced = f0 > 0
        f0_time = np.linspace(0, len(audio) / sample_rate, len(f0))

        if target_pitches and np.any(voiced):
            cents_list = []
            for tp in target_pitches:
                start_s = tp.get("start", 0)
                dur_s = tp.get("duration", 1)
                target_midi = tp.get("pitch", 60)
                target_freq = 440.0 * (2.0 ** ((target_midi - 69) / 12.0))
                mask = (f0_time >= start_s) & (f0_time < start_s + dur_s) & voiced
                if np.any(mask):
                    actual_f0 = f0[mask]
                    cents = 1200 * np.log2(actual_f0 / target_freq)
                    cents_list.extend(cents.tolist())

            if cents_list:
                cents_arr = np.array(cents_list)
                analysis.pitch_deviation_mean_cents = float(np.mean(np.abs(cents_arr)))
                analysis.pitch_deviation_max_cents = float(np.max(np.abs(cents_arr)))
                analysis.pitch_deviation_std_cents = float(np.std(cents_arr))
                analysis.on_pitch_ratio = float(np.mean(np.abs(cents_arr) < 50))

                if analysis.pitch_deviation_mean_cents > 50:
                    analysis.diagnoses.append(VocalDiagnosis(
                        problem="Significant pitch deviation",
                        severity=min(1.0, analysis.pitch_deviation_mean_cents / 150),
                        details=[f"Mean deviation: {analysis.pitch_deviation_mean_cents:.1f} cents",
                                 f"On-pitch ratio (<50 cents): {analysis.on_pitch_ratio:.0%}"],
                    ))

        # artifact: electricity (excessive high-frequency energy in unvoiced regions)
        if np.any(~voiced):
            unvoiced = audio[~np.interp(np.arange(len(audio)) / sample_rate, f0_time[voiced], f0[voiced]) > 0] if np.any(voiced) else audio
            if len(unvoiced) > sr // 10:
                try:
                    import scipy.fft
                    spec = np.abs(scipy.fft.rfft(unvoiced[:sr]))
                    high_bins = spec[len(spec) // 2:]
                    low_bins = spec[:len(spec) // 2]
                    hf_ratio = float(np.sum(high_bins) / (np.sum(low_bins) + 1e-8))
                    analysis.artifact_electricity = min(1.0, hf_ratio / 3.0)
                    if analysis.artifact_electricity > 0.3:
                        analysis.diagnoses.append(VocalDiagnosis(
                            problem="Electrical/robotic artifact detected",
                            severity=analysis.artifact_electricity * 0.6,
                            details=[f"High-frequency noise ratio: {analysis.artifact_electricity:.2f}"],
                        ))
                except ImportError:
                    pass

        # artifact: voicing breaks (sudden F0 dropouts > 50ms)
        if np.any(voiced):
            voiced_binary = f0 > 0
            transitions = np.diff(voiced_binary.astype(int))
            onsets = np.where(transitions == 1)[0]
            offsets = np.where(transitions == -1)[0]
            break_durations = []
            voicing_ends = np.where(voiced_binary[:-1] & ~voiced_binary[1:])[0]
            voicing_starts = np.where(~voiced_binary[:-1] & voiced_binary[1:])[0]
            if len(voicing_ends) > 0 and len(voicing_starts) > 0:
                for end in voicing_ends:
                    next_starts = voicing_starts[voicing_starts > end]
                    if len(next_starts) > 0:
                        gap = (next_starts[0] - end) * (len(audio) / sample_rate / len(f0))
                        if 0.05 < gap < 0.5:
                            break_durations.append(gap)
            analysis.artifact_breaks = len(break_durations)
            if analysis.artifact_breaks > 2:
                analysis.diagnoses.append(VocalDiagnosis(
                    problem="Frequent voicing breaks",
                    severity=min(1.0, analysis.artifact_breaks / 10),
                    details=[f"{analysis.artifact_breaks} breaks detected, avg gap: {np.mean(break_durations)*1000:.0f}ms"],
                ))

        if not analysis.diagnoses:
            analysis.diagnoses.append(VocalDiagnosis(
                problem="No significant issues",
                severity=0.0,
                details=["Pitch deviation within acceptable range"],
            ))

        return analysis

    def generate_suggestions(self, diagnoses: List[VocalDiagnosis]) -> List[dict]:
        suggestions = []
        for d in diagnoses:
            if "pitch deviation" in d.problem.lower():
                suggestions.append({
                    "action": "adjust_synthesized_pitch",
                    "params": {"correction_cents": -d.details[0].split(":")[1].strip().split(" ")[0] if ":" in d.details[0] else -50},
                    "reason": d.problem,
                })
            elif "electrical" in d.problem.lower():
                suggestions.append({
                    "action": "effect_apply",
                    "params": {"type": "eq", "params": {"high_cut": 8000}},
                    "reason": f"Reduce high-frequency electrical artifacts (ratio: {d.details[0].split(':')[1].strip()})",
                })
            elif "voicing breaks" in d.problem.lower():
                suggestions.append({
                    "action": "adjust_articulation",
                    "params": {"style": "legato", "overlap_delta": 0.3},
                    "reason": f"Reduce {d.details[0]} by increasing note overlap",
                })
        return suggestions
