from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class UserFeedback:
    version_id: str
    project_id: str
    score: int
    comment: Optional[str] = None
    timestamp: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ABTestResult:
    session_id: str
    version_a: str
    version_b: str
    preferred: str
    project_id: str
    comment: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class PreferenceCollector:
    def __init__(self, data_dir: str = "data/preferences"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.data_dir / "feedback.jsonl"
        self.abtest_file = self.data_dir / "abtest.jsonl"
        self.adoption_file = self.data_dir / "adoption.jsonl"
        self.replay_file = self.data_dir / "replays.jsonl"
        self.favorite_file = self.data_dir / "favorites.jsonl"

    def record_feedback(self, feedback: UserFeedback) -> None:
        with open(self.feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback.__dict__, ensure_ascii=False) + "\n")

    def record_abtest(self, result: ABTestResult) -> None:
        with open(self.abtest_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result.__dict__, ensure_ascii=False) + "\n")

    def record_adoption(self, version_id: str, project_id: str, accepted: bool, suggestion: str) -> None:
        record = {
            "version_id": version_id,
            "project_id": project_id,
            "accepted": accepted,
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.adoption_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_feedback_for_version(self, version_id: str) -> List[UserFeedback]:
        results = []
        if not self.feedback_file.exists():
            return results
        with open(self.feedback_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("version_id") == version_id:
                    results.append(UserFeedback(**record))
        return results

    def get_average_score(self, project_id: str) -> float:
        scores = []
        if not self.feedback_file.exists():
            return 0.0
        with open(self.feedback_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("project_id") == project_id:
                    scores.append(record.get("score", 0))
        return sum(scores) / max(len(scores), 1)

    def get_adoption_rate(self, project_id: str) -> float:
        accepted = 0
        total = 0
        if not self.adoption_file.exists():
            return 0.0
        with open(self.adoption_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("project_id") == project_id:
                    total += 1
                    if record.get("accepted"):
                        accepted += 1
        return accepted / max(total, 1)

    def record_replay(self, version_id: str, project_id: str) -> None:
        record = {
            "version_id": version_id,
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.replay_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def record_favorite(self, version_id: str, project_id: str, favorited: bool = True) -> None:
        record = {
            "version_id": version_id,
            "project_id": project_id,
            "favorited": favorited,
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.favorite_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_replay_count(self, version_id: str) -> int:
        if not self.replay_file.exists():
            return 0
        count = 0
        with open(self.replay_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("version_id") == version_id:
                    count += 1
        return count

    def is_favorited(self, version_id: str) -> bool:
        if not self.favorite_file.exists():
            return False
        with open(self.favorite_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("version_id") == version_id and record.get("favorited"):
                    return True
        return False
