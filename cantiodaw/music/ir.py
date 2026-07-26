from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class EmotionVector:
    loneliness: float = 0.0
    hope: float = 0.0
    nostalgia: float = 0.0
    tension: float = 0.0
    calmness: float = 0.0
    sadness: float = 0.0
    joy: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    romance: float = 0.0

    def __add__(self, other: EmotionVector) -> EmotionVector:
        return EmotionVector(**{
            k: max(0.0, min(1.0, getattr(self, k) + getattr(other, k)))
            for k in self.__dataclass_fields__
        })

    def scale(self, factor: float) -> EmotionVector:
        return EmotionVector(**{
            k: max(0.0, min(1.0, v * factor))
            for k, v in asdict(self).items()
        })

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> EmotionVector:
        return cls(**{k: d.get(k, 0.0) for k in cls.__dataclass_fields__})


@dataclass
class EnergyCurve:
    start: float = 0.5
    end: float = 0.5
    peak: float = 0.8
    valley: float = 0.2
    shape: str = "linear"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> EnergyCurve:
        return cls(**d)


@dataclass
class StyleVector:
    cinematic: float = 0.0
    electronic: float = 0.0
    orchestral: float = 0.0
    pop: float = 0.0
    ambient: float = 0.0
    rock: float = 0.0
    jazz: float = 0.0
    classical: float = 0.0
    folk: float = 0.0
    hiphop: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> StyleVector:
        return cls(**{k: d.get(k, 0.0) for k in cls.__dataclass_fields__})


@dataclass
class SceneTags:
    tags: List[str] = field(default_factory=list)
    primary: str = ""
    secondary: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> SceneTags:
        return cls(**d)


@dataclass
class ArrangementSpec:
    density: float = 0.5
    instrument_focus: List[str] = field(default_factory=list)
    texture: str = "homophonic"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> ArrangementSpec:
        return cls(**d)


@dataclass
class SectionSpec:
    name: str = ""
    bars: int = 4
    ir_ref: Optional[Dict] = None
    energy_target: float = 0.5
    density_target: float = 0.5

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> SectionSpec:
        return cls(**d)


@dataclass
class StructurePlan:
    sections: List[SectionSpec] = field(default_factory=list)
    total_bars: int = 16

    def to_dict(self) -> Dict:
        return {"sections": [s.to_dict() for s in self.sections], "total_bars": self.total_bars}

    @classmethod
    def from_dict(cls, d: Dict) -> StructurePlan:
        return cls(
            sections=[SectionSpec.from_dict(s) for s in d.get("sections", [])],
            total_bars=d.get("total_bars", 16),
        )


@dataclass
class MusicIR:
    emotion: EmotionVector = field(default_factory=EmotionVector)
    energy: EnergyCurve = field(default_factory=EnergyCurve)
    style: StyleVector = field(default_factory=StyleVector)
    scene: SceneTags = field(default_factory=SceneTags)
    arrangement: ArrangementSpec = field(default_factory=ArrangementSpec)
    structure: StructurePlan = field(default_factory=StructurePlan)

    def to_dict(self) -> Dict:
        return {
            "emotion": self.emotion.to_dict(),
            "energy": self.energy.to_dict(),
            "style": self.style.to_dict(),
            "scene": self.scene.to_dict(),
            "arrangement": self.arrangement.to_dict(),
            "structure": self.structure.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> MusicIR:
        return cls(
            emotion=EmotionVector.from_dict(d.get("emotion", {})),
            energy=EnergyCurve.from_dict(d.get("energy", {})),
            style=StyleVector.from_dict(d.get("style", {})),
            scene=SceneTags.from_dict(d.get("scene", {})),
            arrangement=ArrangementSpec.from_dict(d.get("arrangement", {})),
            structure=StructurePlan.from_dict(d.get("structure", {})),
        )

    def merge(self, delta: MusicIR, factor: float = 1.0) -> MusicIR:
        merged = MusicIR.from_dict(self.to_dict())
        d = delta.to_dict()
        for k, v in d.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    if isinstance(subv, (int, float)):
                        current = getattr(merged, k)
                        if hasattr(current, subk):
                            old = getattr(current, subk)
                            setattr(current, subk, max(0.0, min(1.0, old + subv * factor)))
                    elif isinstance(subv, list):
                        current = getattr(merged, k)
                        if hasattr(current, subk):
                            old_list = getattr(current, subk)
                            setattr(current, subk, old_list + subv)
        return merged


@dataclass
class ParameterDelta:
    target: str
    delta: float
    domain: str = ""
    bounds: Optional[List[float]] = None

    def to_dict(self) -> Dict:
        return {"target": self.target, "delta": self.delta, "domain": self.domain}

    @classmethod
    def from_dict(cls, d: Dict) -> ParameterDelta:
        return cls(**d)
