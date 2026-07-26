import json
import uuid
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .config import DEFAULT_CONFIG


class Track:
    def __init__(self, name: str = "", track_type: str = "audio"):
        self.id = str(uuid.uuid4())[:8]
        self.name = name or f"Track_{self.id}"
        self.type = track_type
        self.volume = 1.0
        self.pan = 0.0
        self.mute = False
        self.solo = False
        self.clips: List[Dict[str, Any]] = []
        self.effects: List[Dict[str, Any]] = []
        self.color = "#4A90D9"

    def add_clip(self, clip: Dict[str, Any]) -> str:
        clip["id"] = str(uuid.uuid4())[:8]
        self.clips.append(clip)
        return clip["id"]

    def add_effect(self, effect_type: str, params: Optional[Dict] = None) -> str:
        eff = {"id": str(uuid.uuid4())[:8], "type": effect_type, "params": params or {}}
        self.effects.append(eff)
        return eff["id"]

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "type": self.type,
            "volume": self.volume, "pan": self.pan,
            "mute": self.mute, "solo": self.solo,
            "clips": self.clips, "effects": self.effects, "color": self.color,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Track":
        t = cls(d.get("name", ""), d.get("type", "audio"))
        t.id = d.get("id", t.id)
        t.volume = d.get("volume", 1.0)
        t.pan = d.get("pan", 0.0)
        t.mute = d.get("mute", False)
        t.solo = d.get("solo", False)
        t.clips = d.get("clips", [])
        t.effects = d.get("effects", [])
        t.color = d.get("color", "#4A90D9")
        return t


class Project:
    def __init__(self, name: str = "Untitled"):
        self.name = name
        self.sample_rate = DEFAULT_CONFIG["project"]["default_sample_rate"]
        self.bpm = DEFAULT_CONFIG["project"]["default_bpm"]
        self.time_signature = DEFAULT_CONFIG["project"]["default_time_signature"]
        self.tracks: List[Track] = []
        self.voice_model: Optional[str] = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def add_track(self, name: str = "", track_type: str = "audio") -> Track:
        t = Track(name, track_type)
        self.tracks.append(t)
        return t

    def remove_track(self, track_id: str) -> bool:
        for i, t in enumerate(self.tracks):
            if t.id == track_id:
                self.tracks.pop(i)
                return True
        return False

    def to_dict(self) -> Dict:
        return {
            "name": self.name, "sample_rate": self.sample_rate,
            "bpm": self.bpm, "time_signature": self.time_signature,
            "voice_model": self.voice_model,
            "tracks": [t.to_dict() for t in self.tracks],
            "created_at": self.created_at, "updated_at": datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Project":
        p = cls(d.get("name", "Untitled"))
        p.sample_rate = d.get("sample_rate", 44100)
        p.bpm = d.get("bpm", 120)
        p.time_signature = d.get("time_signature", [4, 4])
        p.voice_model = d.get("voice_model")
        p.tracks = [Track.from_dict(td) for td in d.get("tracks", [])]
        p.created_at = d.get("created_at", p.created_at)
        return p


class ProjectManager:
    def __init__(self, projects_dir: Optional[str] = None):
        cfg = DEFAULT_CONFIG["paths"]
        self.projects_dir = Path(projects_dir or cfg["projects_dir"])
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> List[Dict]:
        results = []
        for f in sorted(self.projects_dir.glob("*.cantio")):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                results.append({
                    "name": data.get("name", f.stem),
                    "file": f.name,
                    "tracks": len(data.get("tracks", [])),
                    "updated_at": data.get("updated_at", ""),
                    "voice_model": data.get("voice_model"),
                })
            except Exception:
                results.append({"name": f.stem, "file": f.name, "error": True})
        return results

    def create_project(self, name: str) -> Project:
        p = Project(name)
        self.save_project(p)
        return p

    def save_project(self, project: Project) -> Path:
        path = self._project_path(project.name)
        with open(path, "w") as f:
            json.dump(project.to_dict(), f, indent=2)
        return path

    def load_project(self, name_or_path: str) -> Project:
        path = Path(name_or_path)
        if not path.exists():
            path = self._project_path(name_or_path)
        if not path.exists():
            raise FileNotFoundError(f"Project not found: {name_or_path}")
        with open(path) as f:
            data = json.load(f)
        return Project.from_dict(data)

    def delete_project(self, name: str) -> bool:
        path = self._project_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def _project_path(self, name: str) -> Path:
        name = Path(name).stem if Path(name).suffix else name
        return self.projects_dir / f"{name}.cantio"

    def duplicate_project(self, name: str, new_name: str) -> Project:
        proj = self.load_project(name)
        proj.name = new_name
        return self.save_project(proj) and proj
