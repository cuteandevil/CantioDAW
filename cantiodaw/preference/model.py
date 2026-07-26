from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path


@dataclass
class FeedbackSample:
    features: Dict[str, float]
    score: float
    version_id: str
    project_id: str


class PreferenceModel:
    def __init__(self, model_path: Optional[str] = None):
        self.weights: Dict[str, float] = {}
        self.model_path = Path(model_path) if model_path else None
        if self.model_path and self.model_path.exists():
            self.load()

    def train(self, samples: List[FeedbackSample]) -> None:
        if not samples:
            return

        feature_scores: Dict[str, List[float]] = {}
        feature_weights: Dict[str, float] = {}

        for sample in samples:
            for feature, value in sample.features.items():
                if feature not in feature_scores:
                    feature_scores[feature] = []
                feature_scores[feature].append(value * (sample.score / 5.0))

        for feature, vals in feature_scores.items():
            if vals:
                feature_weights[feature] = sum(vals) / len(vals)

        self.weights = feature_weights

    def predict(self, features: Dict[str, float]) -> float:
        if not self.weights:
            return sum(features.values()) / max(len(features), 1)

        total_weight = 0.0
        total = 0.0
        for feature, value in features.items():
            w = self.weights.get(feature, 0.5)
            total += value * w
            total_weight += w

        return total / max(total_weight, 0.001)

    def adjust_critic_score(self, critic_score: float, features: Dict[str, float]) -> float:
        pref_score = self.predict(features)
        return 0.7 * critic_score + 0.3 * pref_score

    def save(self, path: str) -> None:
        data = {"weights": self.weights}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: Optional[str] = None) -> None:
        p = Path(path) if path else self.model_path
        if p and p.exists():
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            self.weights = data.get("weights", {})
