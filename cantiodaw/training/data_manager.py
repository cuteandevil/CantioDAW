import os
import json
import uuid
import shutil
import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class VoiceSample:
    path: str
    duration: float
    speaker_id: int = 0
    text: str = ""
    quality: str = "good"
    sample_rate: int = 44100


class VoiceDatasetManager:
    def __init__(self, voices_dir: Optional[str] = None):
        from ..config import DEFAULT_CONFIG
        self.voices_dir = Path(voices_dir or DEFAULT_CONFIG["paths"]["voices_dir"])
        self.voices_dir.mkdir(parents=True, exist_ok=True)

    def list_voices(self) -> List[Dict]:
        results = []
        for d in sorted(self.voices_dir.iterdir()):
            if d.is_dir():
                meta_file = d / "meta.json"
                if meta_file.exists():
                    with open(meta_file) as f:
                        meta = json.load(f)
                else:
                    meta = {"name": d.name}
                wavs = list(d.glob("*.wav")) + list(d.glob("*.flac")) + list(d.glob("*.mp3"))
                meta["sample_count"] = len(wavs)
                meta["path"] = str(d)
                results.append(meta)
        return results

    def create_voice(self, name: str) -> Path:
        voice_dir = self.voices_dir / name
        voice_dir.mkdir(parents=True, exist_ok=True)
        meta = {"name": name, "created": __import__("datetime").datetime.now().isoformat(),
                "samples": [], "speaker_id": 0}
        with open(voice_dir / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Voice dataset created: {voice_dir}")
        return voice_dir

    def add_sample(self, voice_name: str, src_path: str, text: str = "",
                   speaker_id: int = 0) -> Optional[VoiceSample]:
        voice_dir = self.voices_dir / voice_name
        if not voice_dir.exists():
            logger.error(f"Voice {voice_name} not found")
            return None

        src = Path(src_path)
        if not src.exists():
            logger.error(f"Source file not found: {src_path}")
            return None

        import soundfile as sf
        data, sr = sf.read(str(src))
        duration = len(data) / sr

        dest = voice_dir / f"{uuid.uuid4().hex[:12]}{src.suffix}"
        shutil.copy2(str(src), str(dest))

        sample = VoiceSample(
            path=str(dest), duration=duration,
            speaker_id=speaker_id, text=text,
        )

        meta_path = voice_dir / "meta.json"
        with open(meta_path) as f:
            meta = json.load(f)
        meta.setdefault("samples", []).append(asdict(sample))
        meta["speaker_id"] = speaker_id
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"Sample added to {voice_name}: {dest.name} ({duration:.1f}s)")
        return sample

    def remove_sample(self, voice_name: str, sample_path: str) -> bool:
        voice_dir = self.voices_dir / voice_name
        meta_path = voice_dir / "meta.json"
        if not meta_path.exists():
            return False

        sample_file = Path(sample_path)
        if sample_file.exists():
            sample_file.unlink()

        with open(meta_path) as f:
            meta = json.load(f)
        meta["samples"] = [s for s in meta["samples"] if s.get("path") != sample_path]
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        return True

    def get_voice_meta(self, voice_name: str) -> Optional[Dict]:
        meta_path = self.voices_dir / voice_name / "meta.json"
        if meta_path.exists():
            with open(meta_path) as f:
                return json.load(f)
        return None

    def delete_voice(self, voice_name: str) -> bool:
        voice_dir = self.voices_dir / voice_name
        if voice_dir.exists():
            shutil.rmtree(voice_dir)
            logger.info(f"Voice dataset deleted: {voice_name}")
            return True
        return False

    def prepare_features(self, voice_name: str, output_dir: Optional[str] = None) -> Optional[Path]:
        from src.data.preprocess import extract_features
        meta = self.get_voice_meta(voice_name)
        if not meta:
            return None

        out = Path(output_dir) if output_dir else (self.voices_dir / voice_name / "features")
        out.mkdir(parents=True, exist_ok=True)

        features_list = []
        for sample in meta.get("samples", []):
            wav_path = sample["path"]
            if not Path(wav_path).exists():
                continue
            try:
                feats = extract_features(wav_path)
                features_list.append(feats)
            except Exception as e:
                logger.warning(f"Feature extraction failed for {wav_path}: {e}")

        import numpy as np
        if features_list:
            npz_path = out / "features.npz"
            np.savez(npz_path, *features_list)
            logger.info(f"Features saved: {npz_path} ({len(features_list)} samples)")
            return npz_path
        return None
