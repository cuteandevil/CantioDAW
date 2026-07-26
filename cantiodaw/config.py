import os
from pathlib import Path

CANTIODAW_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "project": {
        "default_sample_rate": 44100,
        "default_bpm": 120,
        "default_time_signature": [4, 4],
        "audio_format": "wav",
        "bit_depth": 16,
    },
    "paths": {
        "projects_dir": str(CANTIODAW_ROOT / "data" / "projects"),
        "voices_dir": str(CANTIODAW_ROOT / "data" / "voices"),
        "exports_dir": str(CANTIODAW_ROOT / "data" / "exports"),
        "checkpoints_dir": str(CANTIODAW_ROOT / "checkpoints"),
    },
    "synthesis": {
        "default_f0": 261.63,
        "vibrato_depth": 0.5,
        "vibrato_rate": 5.0,
        "breathiness": 0.1,
        "silence_before": 0.1,
        "silence_after": 0.15,
    },
    "training": {
        "default_epochs": 100,
        "default_batch_size": 16,
        "default_learning_rate": 0.001,
        "default_checkpoint_format": "safetensors",
        "lora": {"enabled": False, "r": 8, "alpha": 1.0},
    },
    "webui": {
        "host": "127.0.0.1",
        "port": 8080,
        "debug": False,
    },
}
