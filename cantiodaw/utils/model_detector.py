"""Model format detector for CantioDAW — SVC, RVC, and HybridSVC format detection."""

import json
import os
import struct
from pathlib import Path
from typing import Optional, Dict, Any, Tuple


MODEL_FORMATS = {
    "cantiodaw_hybrid_svc": "CantioDAW MultiTaskHybridSVC",
    "so_vits_svc": "so-vits-svc (SoftVC VITS)",
    "rvc_v1": "RVC v1 (256-dim)",
    "rvc_v2": "RVC v2 (768-dim)",
    "applio_rvc": "Applio RVC (wrapped RVC v2)",
    "ddsp_svc": "DDSP-SVC (Differentiable Digital Signal Processing SVC)",
    "unknown": "Unknown format",
}


def detect_model_format(model_path: str, config_path: Optional[str] = None) -> str:
    """Detect model format from model file and optional config."""
    if not os.path.isfile(model_path):
        return "unknown"

    ext = Path(model_path).suffix.lower()

    if ext == ".safetensors":
        return _detect_safetensors(model_path) or _detect_from_config(config_path)

    if ext == ".pt" or ext == ".pth":
        return _detect_pytorch(model_path, config_path)

    if ext == ".onnx":
        return _detect_onnx(model_path)

    if ext == ".ts":
        return "cantiodaw_hybrid_svc"  # TorchScript assumed CantioDAW

    return _detect_from_config(config_path)


def detect_model_info(model_path: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """Return detailed model info including format, sample rate, speaker info, etc."""
    fmt = detect_model_format(model_path, config_path)
    info = {
        "format": fmt,
        "format_name": MODEL_FORMATS.get(fmt, "Unknown"),
        "model_path": model_path,
        "config_path": config_path or "",
        "sample_rate": 44100,
        "speaker_count": 1,
        "feature_dim": 0,
        "supports_f0": True,
        "version": "",
    }

    if config_path and os.path.isfile(config_path):
        config_info = _parse_config(config_path)
        info.update(config_info)

    if fmt.startswith("rvc") or fmt == "applio_rvc":
        info["version"] = "v2" if "v2" in fmt or fmt == "applio_rvc" else "v1"
        info["feature_dim"] = 768 if "v2" in fmt or fmt == "applio_rvc" else 256

    if fmt == "ddsp_svc":
        info["feature_dim"] = info.get("feature_dim") or 256

    return info


def _detect_from_config(config_path: Optional[str]) -> str:
    if not config_path or not os.path.isfile(config_path):
        return "unknown"

    ext = Path(config_path).suffix.lower()
    cfg: Dict[str, Any] = {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if ext == ".yaml":
                import yaml
                cfg = yaml.safe_load(f)
            else:
                cfg = json.load(f)
    except (json.JSONDecodeError, IOError, ImportError):
        return "unknown"

    return _classify_config(cfg or {})


def _classify_config(cfg: Dict[str, Any]) -> str:
    # DDSP-SVC YAML config: has "model.type" set to Sins/CombSub/CombSubFast/CombSubSuperFast
    model_section = cfg.get("model", {})
    if isinstance(model_section, dict) and model_section.get("type") in (
        "Sins", "CombSub", "CombSubFast", "CombSubSuperFast"
    ):
        return "ddsp_svc"

    # Applio RVC: has "pth_path" + "f0method"/"f0_method" at root level
    if "pth_path" in cfg and ("f0method" in cfg or "f0_method" in cfg):
        return "applio_rvc"

    # RVC config: has "pth_path" or specific train keys
    if "pth_path" in cfg:
        return "rvc_v2"

    if "train" in cfg and isinstance(cfg["train"], dict):
        train = cfg["train"]
        if any(k in train for k in ("log_interval", "eval_interval", "fp16_run")):
            return _detect_rvc_version(cfg)

    # so-vits-svc config: has "model" with "inter_channels" etc.
    if "model" in cfg and isinstance(cfg["model"], dict):
        model_cfg = cfg["model"]
        if any(k in model_cfg for k in ("inter_channels", "filter_channels", "n_heads", "n_layers")):
            return "so_vits_svc"

    # CantioDAW config: has "model.phoneme_feature_dim" or "model.spectral_envelope_dim"
    if "model" in cfg:
        model_cfg = cfg["model"]
        if "phoneme_feature_dim" in model_cfg or "spectral_envelope_dim" in model_cfg:
            return "cantiodaw_hybrid_svc"

    return "unknown"


def _detect_rvc_version(cfg: Dict[str, Any]) -> str:
    """Detect RVC v1 vs v2 from config."""
    model_cfg = cfg.get("model", {})
    if "inter_channels" in model_cfg and model_cfg.get("inter_channels", 0) == 768:
        return "rvc_v2"
    if any("768" in str(v) for v in model_cfg.values()):
        return "rvc_v2"
    return "rvc_v1"


def _detect_safetensors(model_path: str) -> Optional[str]:
    """Detect format by inspecting safetensors metadata header."""
    try:
        with open(model_path, "rb") as f:
            header_len = struct.unpack("<Q", f.read(8))[0]
            header = json.loads(f.read(header_len))
        metadata = header.get("__metadata__", {}) or {}
        if "model_format" in metadata:
            return metadata["model_format"]
        if any("hybrid" in k.lower() for k in header.keys()):
            return "cantiodaw_hybrid_svc"
        return None
    except Exception:
        return None


def _detect_pytorch(model_path: str, config_path: Optional[str] = None) -> str:
    """Detect format from PyTorch checkpoint keys."""
    try:
        import torch
        ckpt = torch.load(model_path, map_location="cpu", weights_only=True)
    except Exception:
        return _detect_from_config(config_path) or "unknown"

    keys = set(ckpt.keys()) if isinstance(ckpt, dict) else set()

    if isinstance(ckpt, dict) and "state_dict" in ckpt and isinstance(ckpt["state_dict"], dict):
        keys = set(ckpt["state_dict"].keys())

    key_str = " ".join(list(keys)[:50]).lower()

    # RVC patterns: "generator.", "emb_g", "dec."
    if any(k.startswith(("generator.", "emb_g")) for k in keys):
        if "dec.4" in key_str or "794" in key_str:
            return "rvc_v2"
        return "rvc_v1"

    # Applio RVC: generator keys without standard RVC prefix, check for known Applio patterns
    if any("applio" in k.lower() for k in keys):
        return "applio_rvc"

    # so-vits-svc: "enc_q.", "flow.", "dec."
    if any(k.startswith(("enc_q", "flow.", "dec")) for k in keys):
        return "so_vits_svc"

    # DDSP-SVC: "unit2ctrl." is the core prediction module
    if any(k.startswith("unit2ctrl.") for k in keys):
        return "ddsp_svc"

    # CantioDAW HybridSVC
    if any(k.startswith(("hybrid_svc", "multitask", "content_encoder", "pitch_encoder")) for k in keys):
        return "cantiodaw_hybrid_svc"

    return _detect_from_config(config_path) or "unknown"


def _detect_onnx(model_path: str) -> str:
    """Detect format from ONNX metadata."""
    try:
        import onnx
        model = onnx.load(model_path)
        for prop in model.producer_name or []:
            pass
        for meta in model.metadata_props:
            if meta.key == "model_format":
                return meta.value
    except Exception:
        pass
    return "cantiodaw_hybrid_svc"


def _parse_config(config_path: str) -> Dict[str, Any]:
    """Parse config file for metadata."""
    info: Dict[str, Any] = {}
    ext = Path(config_path).suffix.lower()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if ext == ".yaml":
                import yaml
                cfg = yaml.safe_load(f)
            else:
                cfg = json.load(f)
    except (json.JSONDecodeError, IOError, ImportError):
        return info

    if not cfg:
        return info

    if "model" in cfg:
        m = cfg["model"]
        if isinstance(m, dict):
            info["feature_dim"] = m.get("inter_channels") or m.get("phoneme_feature_dim") or m.get("encoder_out_channels", 0)
            info["speaker_count"] = m.get("n_speakers", m.get("num_speakers", 1))

    if "data" in cfg:
        d = cfg["data"]
        info["sample_rate"] = d.get("sampling_rate", d.get("sample_rate", 44100))

    if "train" in cfg:
        t = cfg["train"]
        if "sampling_rate" in t:
            info["sample_rate"] = t["sampling_rate"]

    return info


def get_config_path(model_path: str) -> Optional[str]:
    """Auto-discover config path for a given model path."""
    p = Path(model_path)
    candidates = [
        p.parent / "config.yaml",
        p.parent / "config.json",
        p.parent / f"{p.stem}.yaml",
        p.parent / f"{p.stem}.json",
        p.parent.parent / "configs" / "config.yaml",
        p.parent.parent / "configs" / "config.json",
        p.parent.parent / "config.json",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None
