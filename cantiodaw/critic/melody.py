from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from ..music.ir import ParameterDelta


@dataclass
class MelodyDiagnosis:
    issue: str
    severity: float
    details: List[str] = field(default_factory=list)


@dataclass
class MelodyAnalysis:
    motif_repetition_score: float = 0.0
    contour_variety: float = 0.0
    interval_variety: float = 0.0
    low_register_ratio: float = 0.0
    high_register_ratio: float = 0.0
    optimal_register_ratio: float = 0.0
    large_leap_ratio: float = 0.0
    small_step_ratio: float = 0.0
    diagnoses: List[MelodyDiagnosis] = field(default_factory=list)


class MotifDetector:
    def detect_repetitions(self, pitches: List[int], min_len: int = 3) -> List[List[int]]:
        repetitions = []
        for start in range(len(pitches)):
            for length in range(min_len, (len(pitches) - start) // 2 + 1):
                pattern = pitches[start:start + length]
                for check_start in range(start + length, len(pitches) - length + 1):
                    if pitches[check_start:check_start + length] == pattern:
                        repetitions.append(pattern)
                        break
        return repetitions


class MelodyCritic:
    def __init__(self):
        self.motif_detector = MotifDetector()

    def analyze(self, pitches: List[int]) -> MelodyAnalysis:
        analysis = MelodyAnalysis()
        if not pitches:
            return analysis

        analysis.contour_variety = self._calc_contour_variety(pitches)
        analysis.interval_variety = self._calc_interval_variety(pitches)
        self._calc_register(pitches, analysis)

        intervals = self._get_intervals(pitches)
        leaps = sum(1 for i in intervals if abs(i) >= 5)
        steps = sum(1 for i in intervals if abs(i) <= 2)
        analysis.large_leap_ratio = leaps / max(len(intervals), 1)
        analysis.small_step_ratio = steps / max(len(intervals), 1)

        motifs = self.motif_detector.detect_repetitions(pitches)
        analysis.motif_repetition_score = min(len(motifs) * 0.15, 1.0)

        if analysis.motif_repetition_score < 0.15:
            analysis.diagnoses.append(MelodyDiagnosis(
                issue="动机重复不足",
                severity=0.5,
                details=["旋律缺少重复动机，建议建立 1-2 个核心动机"],
            ))
        if analysis.large_leap_ratio > 0.4:
            analysis.diagnoses.append(MelodyDiagnosis(
                issue="大跳比例过高",
                severity=0.4,
                details=[f"大跳占比 {analysis.large_leap_ratio:.0%}"],
            ))
        if analysis.contour_variety < 0.2:
            analysis.diagnoses.append(MelodyDiagnosis(
                issue="旋律轮廓变化不足",
                severity=0.3,
                details=["旋律走向单一，建议增加起伏"],
            ))
        if analysis.low_register_ratio > 0.5:
            analysis.diagnoses.append(MelodyDiagnosis(
                issue="音域过低",
                severity=0.3,
                details=[f"低音区占比 {analysis.low_register_ratio:.0%}"],
            ))
        if analysis.high_register_ratio > 0.5:
            analysis.diagnoses.append(MelodyDiagnosis(
                issue="音域过高",
                severity=0.3,
                details=[f"高音区占比 {analysis.high_register_ratio:.0%}"],
            ))

        return analysis

    def generate_suggestions(self, diagnoses: List[MelodyDiagnosis]) -> List[ParameterDelta]:
        suggestions = []
        for d in diagnoses:
            if "动机" in d.issue:
                suggestions.append(ParameterDelta(
                    target="melody.contour_variety", delta=0.2, domain="melody", bounds=[0.0, 1.0],
                ))
            if "大跳" in d.issue:
                suggestions.append(ParameterDelta(
                    target="melody.step_ratio", delta=0.2, domain="melody", bounds=[0.0, 1.0],
                ))
            if "轮廓" in d.issue:
                suggestions.append(ParameterDelta(
                    target="melody.contour", delta=0.2, domain="melody", bounds=[-1.0, 1.0],
                ))
        return suggestions

    def _calc_contour_variety(self, pitches: List[int]) -> float:
        if len(pitches) < 3:
            return 0.0
        directions = []
        for i in range(1, len(pitches)):
            d = pitches[i] - pitches[i - 1]
            if d > 0:
                directions.append(1)
            elif d < 0:
                directions.append(-1)
            else:
                directions.append(0)
        changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])
        return changes / max(len(directions) - 1, 1)

    def _calc_interval_variety(self, pitches: List[int]) -> float:
        intervals = self._get_intervals(pitches)
        if not intervals:
            return 0.0
        unique = len(set(abs(i) for i in intervals))
        return min(unique / 7.0, 1.0)

    def _calc_register(self, pitches: List[int], analysis: MelodyAnalysis) -> None:
        if not pitches:
            return
        low = min(pitches)
        high = max(pitches)
        c4 = 60
        c5 = 72
        for p in pitches:
            if p < c4 - 12:
                analysis.low_register_ratio += 1
            elif p > c5 + 12:
                analysis.high_register_ratio += 1
            else:
                analysis.optimal_register_ratio += 1
        n = len(pitches)
        analysis.low_register_ratio /= n
        analysis.high_register_ratio /= n
        analysis.optimal_register_ratio /= n

    def _get_intervals(self, pitches: List[int]) -> List[int]:
        return [pitches[i] - pitches[i - 1] for i in range(1, len(pitches))]
