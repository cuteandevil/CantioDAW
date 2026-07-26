from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from .ir import MusicIR, ParameterDelta


EMOTION_HARMONY_MAP: Dict[str, List[Tuple[str, float]]] = {
    "loneliness": [("minor_ratio", 0.4), ("suspension_ratio", 0.3), ("seventh_ratio", 0.2)],
    "hope": [("ascending_contour", 0.5), ("resolution", 0.6), ("major_ratio", 0.3)],
    "nostalgia": [("suspension_ratio", 0.3), ("seventh_ratio", 0.3), ("minor_ratio", 0.2)],
    "tension": [("dissonance", 0.4), ("dominant_frequency", 0.4), ("mode_shift", 0.3)],
    "calmness": [("resolution", 0.4), ("consonance", 0.3), ("dissonance", -0.3)],
    "sadness": [("minor_ratio", 0.5), ("dissonance", 0.2), ("suspension_ratio", 0.2)],
    "joy": [("major_ratio", 0.5), ("consonance", 0.4), ("resolution", 0.3)],
    "anger": [("dissonance", 0.5), ("dominant_frequency", 0.3), ("mode_shift", 0.3)],
    "fear": [("dissonance", 0.4), ("minor_ratio", 0.3), ("suspension_ratio", 0.3)],
    "romance": [("major_ratio", 0.3), ("seventh_ratio", 0.2), ("resolution", 0.3)],
}

EMOTION_MELODY_MAP: Dict[str, List[Tuple[str, float]]] = {
    "loneliness": [("contour", -0.3), ("interval_size", -0.2), ("step_ratio", 0.3)],
    "hope": [("ascending_contour", 0.5), ("interval_size", 0.2)],
    "nostalgia": [("contour", -0.2), ("step_ratio", 0.2)],
    "tension": [("interval_size", 0.3), ("contour_variety", 0.3)],
    "calmness": [("contour", -0.2), ("step_ratio", 0.3), ("rest_ratio", 0.2)],
    "sadness": [("contour", -0.3), ("interval_size", -0.2), ("step_ratio", 0.3)],
    "joy": [("contour", 0.4), ("interval_size", 0.2), ("rhythmic_variety", 0.3)],
    "anger": [("interval_size", 0.4), ("contour_variety", 0.3), ("density", 0.3)],
    "fear": [("interval_size", 0.3), ("contour_variety", 0.3), ("step_ratio", -0.2)],
    "romance": [("contour", 0.2), ("step_ratio", 0.3), ("legato_ratio", 0.4)],
}

EMOTION_RHYTHM_MAP: Dict[str, List[Tuple[str, float]]] = {
    "loneliness": [("density", -0.3), ("syncopation", -0.2)],
    "hope": [("density", 0.2), ("bpm", 0.1)],
    "nostalgia": [("density", -0.2), ("swing", 0.2)],
    "tension": [("syncopation", 0.3), ("density", 0.2), ("bpm", 0.2)],
    "calmness": [("density", -0.3), ("bpm", -0.2), ("syncopation", -0.2)],
    "sadness": [("density", -0.3), ("bpm", -0.1)],
    "joy": [("density", 0.3), ("bpm", 0.2), ("syncopation", 0.2)],
    "anger": [("density", 0.4), ("bpm", 0.3), ("syncopation", 0.3)],
    "fear": [("syncopation", 0.3), ("density", 0.2), ("stability", -0.3)],
    "romance": [("density", -0.1), ("swing", 0.2)],
}

EMOTION_INSTRUMENT_MAP: Dict[str, List[Tuple[str, float]]] = {
    "loneliness": [("solo_instrument", 0.5), ("high_register", -0.3)],
    "hope": [("strings", 0.4), ("bright_timbre", 0.3)],
    "nostalgia": [("warm_timbre", 0.4), ("analog", 0.3)],
    "tension": [("percussion", 0.3), ("distortion", 0.3)],
    "calmness": [("piano", 0.4), ("pad", 0.3), ("acoustic", 0.3)],
    "sadness": [("strings", 0.3), ("solo_instrument", 0.3)],
    "joy": [("bright_timbre", 0.4), ("percussion", 0.2), ("acoustic", 0.2)],
    "anger": [("distortion", 0.5), ("percussion", 0.4), ("brass", 0.3)],
    "fear": [("atonal", 0.3), ("percussion", 0.3), ("sub_bass", 0.3)],
    "romance": [("strings", 0.4), ("warm_timbre", 0.3), ("acoustic", 0.2)],
}

EMOTION_MIX_MAP: Dict[str, List[Tuple[str, float]]] = {
    "loneliness": [("reverb", 0.4), ("brightness", -0.3)],
    "hope": [("brightness", 0.3), ("compression", 0.1)],
    "nostalgia": [("reverb", 0.3), ("brightness", -0.2), ("warmth", 0.3)],
    "tension": [("compression", 0.3), ("brightness", 0.2)],
    "calmness": [("reverb", 0.3), ("dynamic_range", -0.2)],
    "sadness": [("reverb", 0.4), ("brightness", -0.3)],
    "joy": [("brightness", 0.3), ("compression", 0.2)],
    "anger": [("compression", 0.4), ("brightness", 0.3), ("distortion", 0.4)],
    "fear": [("reverb", 0.3), ("sub_bass", 0.3), ("brightness", -0.2)],
    "romance": [("reverb", 0.2), ("warmth", 0.3), ("compression", 0.1)],
}


class ParameterMapper:
    def __init__(self):
        self.bounds: Dict[str, Tuple[float, float]] = {
            "harmony.minor_ratio": (0.0, 1.0),
            "harmony.major_ratio": (0.0, 1.0),
            "harmony.dissonance": (0.0, 1.0),
            "harmony.consonance": (0.0, 1.0),
            "harmony.resolution": (0.0, 1.0),
            "harmony.suspension_ratio": (0.0, 1.0),
            "harmony.seventh_ratio": (0.0, 1.0),
            "harmony.dominant_frequency": (0.0, 1.0),
            "harmony.mode_shift": (0.0, 1.0),
            "melody.contour": (-1.0, 1.0),
            "melody.ascending_contour": (0.0, 1.0),
            "melody.interval_size": (0.0, 1.0),
            "melody.step_ratio": (0.0, 1.0),
            "melody.contour_variety": (0.0, 1.0),
            "melody.legato_ratio": (0.0, 1.0),
            "melody.rest_ratio": (0.0, 1.0),
            "melody.rhythmic_variety": (0.0, 1.0),
            "rhythm.density": (0.0, 1.0),
            "rhythm.bpm": (0.0, 1.0),
            "rhythm.syncopation": (0.0, 1.0),
            "rhythm.swing": (0.0, 1.0),
            "rhythm.stability": (0.0, 1.0),
            "sound.reverb": (0.0, 1.0),
            "sound.brightness": (0.0, 1.0),
            "sound.distortion": (0.0, 1.0),
            "sound.warmth": (0.0, 1.0),
            "sound.sub_bass": (0.0, 1.0),
            "mix.compression": (0.0, 1.0),
            "mix.dynamic_range": (0.0, 1.0),
            "arrangement.density": (0.0, 1.0),
            "instrument.solo_instrument": (0.0, 1.0),
            "instrument.high_register": (0.0, 1.0),
            "instrument.strings": (0.0, 1.0),
            "instrument.bright_timbre": (0.0, 1.0),
            "instrument.warm_timbre": (0.0, 1.0),
            "instrument.analog": (0.0, 1.0),
            "instrument.percussion": (0.0, 1.0),
            "instrument.distortion": (0.0, 1.0),
            "instrument.piano": (0.0, 1.0),
            "instrument.pad": (0.0, 1.0),
            "instrument.acoustic": (0.0, 1.0),
            "instrument.brass": (0.0, 1.0),
            "instrument.atonal": (0.0, 1.0),
            "instrument.sub_bass": (0.0, 1.0),
        }

    def map_emotion_to_harmony(self, emotion_name: str, intensity: float = 1.0) -> List[ParameterDelta]:
        return self._lookup(EMOTION_HARMONY_MAP, emotion_name, intensity, "harmony")

    def map_emotion_to_melody(self, emotion_name: str, intensity: float = 1.0) -> List[ParameterDelta]:
        return self._lookup(EMOTION_MELODY_MAP, emotion_name, intensity, "melody")

    def map_emotion_to_rhythm(self, emotion_name: str, intensity: float = 1.0) -> List[ParameterDelta]:
        return self._lookup(EMOTION_RHYTHM_MAP, emotion_name, intensity, "rhythm")

    def map_emotion_to_instrument(self, emotion_name: str, intensity: float = 1.0) -> List[ParameterDelta]:
        return self._lookup(EMOTION_INSTRUMENT_MAP, emotion_name, intensity, "instrument")

    def map_emotion_to_mix(self, emotion_name: str, intensity: float = 1.0) -> List[ParameterDelta]:
        return self._lookup(EMOTION_MIX_MAP, emotion_name, intensity, "mix")

    def map_emotion_all(self, emotion_name: str, intensity: float = 1.0) -> List[ParameterDelta]:
        return (
            self.map_emotion_to_harmony(emotion_name, intensity)
            + self.map_emotion_to_melody(emotion_name, intensity)
            + self.map_emotion_to_rhythm(emotion_name, intensity)
            + self.map_emotion_to_instrument(emotion_name, intensity)
            + self.map_emotion_to_mix(emotion_name, intensity)
        )

    def map_ir(self, ir: MusicIR) -> List[ParameterDelta]:
        deltas: List[ParameterDelta] = []
        for emotion_name, intensity in ir.emotion.to_dict().items():
            if intensity > 0.05:
                deltas.extend(self.map_emotion_all(emotion_name, intensity))
        return self._merge_and_clamp(deltas)

    def _lookup(self, table: Dict, name: str, intensity: float, domain: str) -> List[ParameterDelta]:
        deltas = []
        for target, delta in table.get(name, []):
            full_target = f"{domain}.{target}"
            clamped = self._clamp(full_target, delta * intensity)
            deltas.append(ParameterDelta(
                target=full_target,
                delta=clamped,
                domain=domain,
                bounds=list(self.bounds.get(full_target, (0.0, 1.0))),
            ))
        return deltas

    def _clamp(self, target: str, value: float) -> float:
        lo, hi = self.bounds.get(target, (0.0, 1.0))
        return max(lo, min(hi, value))

    def _merge_and_clamp(self, deltas: List[ParameterDelta]) -> List[ParameterDelta]:
        merged: Dict[str, float] = {}
        domain_map: Dict[str, str] = {}
        bounds_map: Dict[str, List[float]] = {}
        for d in deltas:
            merged[d.target] = merged.get(d.target, 0.0) + d.delta
            domain_map[d.target] = d.domain
            bounds_map[d.target] = d.bounds or list(self.bounds.get(d.target, (0.0, 1.0)))
        result = []
        for target, total in merged.items():
            clamped = self._clamp(target, total)
            result.append(ParameterDelta(
                target=target,
                delta=clamped,
                domain=domain_map.get(target, ""),
                bounds=bounds_map.get(target),
            ))
        return result

    def style_to_arrangement(self, ir: MusicIR) -> ArrangementConfig:
        return ArrangementConfig.from_ir(ir)


class ArrangementConfig:
    def __init__(self):
        self.density: float = 0.5
        self.instruments: List[str] = []
        self.texture: str = "homophonic"
        self.bpm_factor: float = 1.0
        self.complexity: float = 0.5

    @classmethod
    def from_ir(cls, ir: MusicIR) -> ArrangementConfig:
        cfg = cls()
        cfg.density = ir.arrangement.density
        if ir.style.cinematic > 0.5:
            cfg.instruments.extend(["strings", "brass", "percussion"])
            cfg.texture = "hybrid"
        if ir.style.electronic > 0.5:
            cfg.instruments.extend(["synth", "drums", "bass"])
            cfg.complexity = 0.7
        if ir.style.orchestral > 0.5:
            cfg.instruments.extend(["strings", "woodwinds", "brass", "percussion"])
            cfg.texture = "orchestral"
        if ir.style.ambient > 0.5:
            cfg.instruments.extend(["pad", "texture"])
            cfg.complexity = 0.3
        if ir.style.pop > 0.5:
            cfg.instruments.extend(["drums", "bass", "guitar", "keys"])
            cfg.texture = "pop"
        if ir.arrangement.instrument_focus:
            cfg.instruments = ir.arrangement.instrument_focus
        cfg.density = ir.arrangement.density
        if ir.energy.end > 0.7:
            cfg.bpm_factor = 1.0 + (ir.energy.end - 0.7) * 0.3
        elif ir.energy.end < 0.3:
            cfg.bpm_factor = 1.0 - (0.3 - ir.energy.end) * 0.2
        return cfg
