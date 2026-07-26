from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
import copy
from pathlib import Path
from .project import Project


@dataclass
class VersionSnapshot:
    version_id: str
    project_id: str
    project_state: Dict
    timestamp: str
    parent_version: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class VersionManager:
    def __init__(self, versions_dir: str = "data/versions"):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.history: Dict[str, List[VersionSnapshot]] = {}
        self._version_counter: Dict[str, int] = {}

    def _next_version_id(self, project_id: str) -> str:
        if project_id in self._version_counter:
            self._version_counter[project_id] += 1
            return f"{project_id}_v{self._version_counter[project_id]:03d}"
        existing = sorted(self.versions_dir.glob(f"{project_id}_v*.json"))
        if existing:
            last = existing[-1].stem
            parts = last.rsplit("_v", 1)
            if len(parts) == 2 and parts[1].isdigit():
                self._version_counter[project_id] = int(parts[1])
            else:
                self._version_counter[project_id] = 0
        else:
            self._version_counter[project_id] = 0
        self._version_counter[project_id] += 1
        return f"{project_id}_v{self._version_counter[project_id]:03d}"

    def snapshot(self, project: Project) -> str:
        project_id = project.name
        v_id = self._next_version_id(project_id)

        snapshot = VersionSnapshot(
            version_id=v_id,
            project_id=project_id,
            project_state=copy.deepcopy(project.to_dict()),
            timestamp=datetime.now().isoformat(),
            parent_version=None,
        )

        if project_id in self.history and self.history[project_id]:
            snapshot.parent_version = self.history[project_id][-1].version_id

        if project_id not in self.history:
            self.history[project_id] = []
        self.history[project_id].append(snapshot)

        path = self.versions_dir / f"{v_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot.__dict__, f, indent=2, default=str)

        return v_id

    def diff(self, project_id: str, v1_id: str, v2_id: str) -> Dict:
        v1 = self._load_snapshot(v1_id)
        v2 = self._load_snapshot(v2_id)
        if not v1 or not v2:
            return {"error": "Version not found"}

        state1 = v1.project_state
        state2 = v2.project_state

        diffs: Dict[str, Dict] = {}

        for key in state1:
            if key in ("updated_at", "tracks"):
                continue
            if state1.get(key) != state2.get(key):
                diffs[key] = {"from": state1.get(key), "to": state2.get(key)}

        tracks1 = {t["id"]: t for t in state1.get("tracks", [])}
        tracks2 = {t["id"]: t for t in state2.get("tracks", [])}
        ids1, ids2 = set(tracks1), set(tracks2)

        track_changes = []
        for tid in sorted(ids1 & ids2):
            t1, t2 = tracks1[tid], tracks2[tid]
            field_diffs = {}
            for k in t1:
                if t1[k] != t2[k]:
                    field_diffs[k] = {"from": t1[k], "to": t2[k]}
            if field_diffs:
                track_changes.append({"track_id": tid, "track_name": t1.get("name", ""), "changes": field_diffs})

        for tid in sorted(ids2 - ids1):
            t = tracks2[tid]
            track_changes.append({
                "track_id": tid, "track_name": t.get("name", ""), "changes": "added",
            })

        for tid in sorted(ids1 - ids2):
            t = tracks1[tid]
            track_changes.append({
                "track_id": tid, "track_name": t.get("name", ""), "changes": "removed",
            })

        if track_changes:
            diffs["tracks"] = track_changes

        return {
            "v1": v1_id,
            "v2": v2_id,
            "changes": diffs,
            "track_count_change": len(tracks2) - len(tracks1),
        }

    def rollback(self, project: Project, version_id: str) -> bool:
        snapshot = self._load_snapshot(version_id)
        if not snapshot:
            return False

        old_state = snapshot.project_state
        project.name = old_state.get("name", project.name)
        project.bpm = old_state.get("bpm", project.bpm)
        project.sample_rate = old_state.get("sample_rate", project.sample_rate)
        project.time_signature = old_state.get("time_signature", project.time_signature)
        project.voice_model = old_state.get("voice_model")
        from .project import Track
        project.tracks = [Track.from_dict(td) for td in old_state.get("tracks", [])]
        return True

    def get_version(self, version_id: str) -> Optional[VersionSnapshot]:
        return self._load_snapshot(version_id)

    def list_versions(self, project_id: str) -> List[VersionSnapshot]:
        versions = list(self.history.get(project_id, []))
        seen = {v.version_id for v in versions}
        for f in sorted(self.versions_dir.glob(f"{project_id}_v*.json")):
            vid = f.stem
            if vid not in seen:
                snap = self._load_snapshot(vid)
                if snap:
                    versions.append(snap)
                    seen.add(vid)
        return versions

    def _load_snapshot(self, version_id: str) -> Optional[VersionSnapshot]:
        path = self.versions_dir / f"{version_id}.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return VersionSnapshot(**data)
