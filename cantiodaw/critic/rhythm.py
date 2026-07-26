from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from ..music.ir import ParameterDelta


@dataclass
class RhythmDiagnosis:
    issue: str
    severity: float
    details: List[str] = field(default_factory=list)


@dataclass
class RhythmAnalysis:
    swing_amount: float = 0.0
    note_density: float = 0.0
    rest_ratio: float = 0.0
    tempo_stability: float = 0.0
    downlock_stability: float = 0.0
    syncopation_density: float = 0.0
    diagnoses: List[RhythmDiagnosis] = field(default_factory=list)


class RhythmCritic:
    def analyze(self, note_starts: List[float], note_durations: List[float], bpm: float = 120.0) -> RhythmAnalysis:
        analysis = RhythmAnalysis()
        if not note_starts:
            return analysis

        total_duration = max(note_starts) + sum(note_durations) / len(note_durations) if note_durations else 1.0
        total_notes_time = sum(note_durations)
        analysis.note_density = total_notes_time / max(total_duration, 1)
        analysis.rest_ratio = 1.0 - analysis.note_density

        analysis.swing_amount = self._calc_swing(note_starts, bpm)
        analysis.syncopation_density = self._calc_syncopation(note_starts, bpm)
        analysis.tempo_stability = self._calc_stability(note_starts)
        analysis.downlock_stability = self._calc_downlock(note_starts, bpm)

        if analysis.syncopation_density > 0.5:
            analysis.diagnoses.append(RhythmDiagnosis(
                issue="切分节奏过多",
                severity=0.4,
                details=[f"切分密度 {analysis.syncopation_density:.0%}"],
            ))
        if analysis.note_density < 0.2:
            analysis.diagnoses.append(RhythmDiagnosis(
                issue="音符密度偏低",
                severity=0.4,
                details=[f"密度 {analysis.note_density:.0%}"],
            ))
        if analysis.tempo_stability < 0.5:
            analysis.diagnoses.append(RhythmDiagnosis(
                issue="节奏稳定性差",
                severity=0.5,
                details=[f"稳定度 {analysis.tempo_stability:.0%}"],
            ))
        if analysis.rest_ratio > 0.7:
            analysis.diagnoses.append(RhythmDiagnosis(
                issue="休止符过多",
                severity=0.3,
                details=[f"休止比例 {analysis.rest_ratio:.0%}"],
            ))

        return analysis

    def generate_suggestions(self, diagnoses: List[RhythmDiagnosis]) -> List[ParameterDelta]:
        suggestions = []
        for d in diagnoses:
            if "切分" in d.issue:
                suggestions.append(ParameterDelta(
                    target="rhythm.syncopation", delta=-0.2, domain="rhythm", bounds=[0.0, 1.0],
                ))
            if "密度偏低" in d.issue:
                suggestions.append(ParameterDelta(
                    target="rhythm.density", delta=0.2, domain="rhythm", bounds=[0.0, 1.0],
                ))
            if "稳定性" in d.issue:
                suggestions.append(ParameterDelta(
                    target="rhythm.stability", delta=0.2, domain="rhythm", bounds=[0.0, 1.0],
                ))
        return suggestions

    def _calc_swing(self, starts: List[float], bpm: float) -> float:
        beat_duration = 60.0 / bpm
        eighth = beat_duration / 2
        offsets = []
        for s in starts:
            pos_in_beat = s % beat_duration
            if 0.4 * beat_duration < pos_in_beat < 0.6 * beat_duration:
                offsets.append(abs(pos_in_beat - eighth * 1.5))
        if not offsets:
            return 0.0
        return min(sum(offsets) / (len(offsets) * eighth * 0.5), 1.0)

    def _calc_syncopation(self, starts: List[float], bpm: float) -> float:
        beat_duration = 60.0 / bpm
        syncopated = 0
        for s in starts:
            pos_in_beat = s % beat_duration
            if 0.05 * beat_duration < pos_in_beat < 0.45 * beat_duration:
                syncopated += 1
        return syncopated / max(len(starts), 1)

    def _calc_stability(self, starts: List[float]) -> float:
        if len(starts) < 3:
            return 1.0
        gaps = [starts[i] - starts[i - 1] for i in range(1, len(starts))]
        mean_gap = sum(gaps) / len(gaps)
        variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        cv = (variance ** 0.5) / max(mean_gap, 0.001)
        return max(0.0, 1.0 - min(cv, 1.0))

    def _calc_downlock(self, starts: List[float], bpm: float) -> float:
        beat_duration = 60.0 / bpm
        on_beat = sum(1 for s in starts if abs(s % beat_duration) < 0.05 * beat_duration)
        return on_beat / max(len(starts), 1)
