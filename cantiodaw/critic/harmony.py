from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from ..music.ir import ParameterDelta


@dataclass
class HarmonyDiagnosis:
    issue: str
    severity: float
    details: List[str] = field(default_factory=list)


@dataclass
class HarmonyAnalysis:
    tonic_ratio: float = 0.0
    subdominant_ratio: float = 0.0
    dominant_ratio: float = 0.0
    dissonance_density: float = 0.0
    resolution_rate: float = 0.0
    delayed_resolutions: int = 0
    modulation_score: float = 0.0
    diagnoses: List[HarmonyDiagnosis] = field(default_factory=list)


class HarmonyCritic:
    def analyze(self, chords: List[str], durations: Optional[List[float]] = None) -> HarmonyAnalysis:
        analysis = HarmonyAnalysis()
        if not chords:
            return analysis

        func_counts: Dict[str, int] = {"tonic": 0, "subdominant": 0, "dominant": 0}
        resolved = 0
        total_dom = 0

        for i, chord in enumerate(chords):
            func = self._classify_chord(chord)
            if func == "tonic":
                func_counts["tonic"] += 1
            elif func == "subdominant":
                func_counts["subdominant"] += 1
            elif func == "dominant":
                func_counts["dominant"] += 1
                total_dom += 1
                if i + 1 < len(chords):
                    next_func = self._classify_chord(chords[i + 1])
                    if next_func == "tonic":
                        resolved += 1

        total = len(chords)
        analysis.tonic_ratio = func_counts["tonic"] / max(total, 1)
        analysis.subdominant_ratio = func_counts["subdominant"] / max(total, 1)
        analysis.dominant_ratio = func_counts["dominant"] / max(total, 1)
        analysis.resolution_rate = resolved / max(total_dom, 1)
        analysis.dissonance_density = self._calc_dissonance(chords)

        if analysis.dominant_ratio < 0.15:
            analysis.diagnoses.append(HarmonyDiagnosis(
                issue="dominant 和弦占比过低",
                severity=0.5,
                details=[f"dominant 占比 {analysis.dominant_ratio:.0%}，建议增加属和弦"],
            ))
        if analysis.resolution_rate < 0.4:
            analysis.diagnoses.append(HarmonyDiagnosis(
                issue="解决感不足",
                severity=0.6,
                details=[f"V→I 解决率 {analysis.resolution_rate:.0%}"],
            ))
        if analysis.dissonance_density > 0.7:
            analysis.diagnoses.append(HarmonyDiagnosis(
                issue="不协和度过高",
                severity=0.4,
                details=[f"不协和密度 {analysis.dissonance_density:.0%}"],
            ))
        if analysis.modulation_score > 0.5:
            analysis.diagnoses.append(HarmonyDiagnosis(
                issue="离调/转调频繁",
                severity=0.3,
                details=[f"离调评分 {analysis.modulation_score:.0%}"],
            ))

        return analysis

    def analyze_tension_curve(self, chords: List[str]) -> List[float]:
        tension = []
        for chord in chords:
            t = 0.2
            if chord.endswith("dim") or chord.endswith("aug"):
                t += 0.4
            if "7" in chord:
                t += 0.3
            if "sus" in chord:
                t += 0.2
            tension.append(min(t, 1.0))
        return tension

    def generate_diagnoses(self, chords: List[str]) -> List[HarmonyDiagnosis]:
        analysis = self.analyze(chords)
        return analysis.diagnoses

    def generate_suggestions(self, diagnoses: List[HarmonyDiagnosis]) -> List[ParameterDelta]:
        suggestions = []
        for d in diagnoses:
            if "dominant" in d.issue:
                suggestions.append(ParameterDelta(
                    target="harmony.dominant_frequency",
                    delta=0.2,
                    domain="harmony",
                    bounds=[0.0, 1.0],
                ))
            if "解决" in d.issue:
                suggestions.append(ParameterDelta(
                    target="harmony.resolution",
                    delta=0.3,
                    domain="harmony",
                    bounds=[0.0, 1.0],
                ))
            if "不协和" in d.issue:
                suggestions.append(ParameterDelta(
                    target="harmony.dissonance",
                    delta=-0.2,
                    domain="harmony",
                    bounds=[0.0, 1.0],
                ))
        return suggestions

    def _classify_chord(self, chord: str) -> str:
        c = chord.lower().strip()
        if c in ("c", "am", "em", "c"):
            return "tonic"
        if c in ("d", "dm", "f"):
            return "subdominant"
        if c in ("g", "g7", "e", "e7"):
            return "dominant"
        if c.startswith("c") or c == "am":
            return "tonic"
        if c.startswith(("d", "f")):
            return "subdominant"
        if c.startswith(("g", "e")):
            return "dominant"
        return "tonic"

    def _calc_dissonance(self, chords: List[str]) -> float:
        dissonant = 0
        for chord in chords:
            c = chord.lower()
            if any(x in c for x in ("dim", "aug", "7", "sus", "m7b5")):
                dissonant += 1
        return dissonant / max(len(chords), 1)
