"""Model adapter for CantioDAW — unified inference across SVC, RVC, and HybridSVC formats."""

import json
import os
import logging
import numpy as np
import torch
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union

from .model_detector import detect_model_format, detect_model_info, get_config_path

logger = logging.getLogger(__name__)


def adapt_config(model_path: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """Detect model format and produce a CantioDAW-compatible config dict."""
    fmt = detect_model_format(model_path, config_path)
    info = detect_model_info(model_path, config_path)

    cantiodaw_cfg = {
        "model": {
            "phoneme_feature_dim": 32,
            "spectral_envelope_dim": 60,
            "speaker_embed_dim": 128,
            "n_speakers": max(info.get("speaker_count", 1), 1),
            "use_pitch_quantizer": True,
        },
        "feature": {
            "sample_rate": info.get("sample_rate", 44100),
            "frame_period": 5.0,
            "fft_size": 1024,
        },
        "inference": {
            "default_f0_hz": 220.0,
        },
        "_format": fmt,
        "_format_name": info.get("format_name", "Unknown"),
        "_model_path": model_path,
        "_config_path": config_path or "",
    }

    if fmt == "so_vits_svc" and config_path and os.path.isfile(config_path):
        _adapt_svc_config(config_path, cantiodaw_cfg)
    elif fmt.startswith("rvc") and config_path and os.path.isfile(config_path):
        _adapt_rvc_config(config_path, cantiodaw_cfg, fmt)
    elif fmt == "ddsp_svc" and config_path and os.path.isfile(config_path):
        _adapt_ddsp_config(config_path, cantiodaw_cfg)

    return cantiodaw_cfg


def _adapt_svc_config(config_path: str, cfg: Dict[str, Any]) -> None:
    """Map so-vits-svc config.json keys into CantioDAW config."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            src = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    src_model = src.get("model", {})
    if isinstance(src_model, dict):
        m = cfg.setdefault("model", {})
        m["phoneme_feature_dim"] = src_model.get("inter_channels", 256)
        m["spectral_envelope_dim"] = src_model.get("filter_channels", 512)
        m["n_heads"] = src_model.get("n_heads", 2)
        m["n_layers"] = src_model.get("n_layers", 6)
        m["_source"] = "so_vits_svc"

    src_data = src.get("data", {})
    if isinstance(src_data, dict):
        feat = cfg.setdefault("feature", {})
        if "sampling_rate" in src_data:
            feat["sample_rate"] = src_data["sampling_rate"]
        if "hop_length" in src_data:
            feat["hop_length"] = src_data["hop_length"]

    src_train = src.get("train", {})
    if isinstance(src_train, dict):
        if "log_interval" in src_train:
            train = cfg.setdefault("training", {})
            train["log_interval"] = src_train["log_interval"]
            train["eval_interval"] = src_train.get("eval_interval", 1000)
            train["fp16_run"] = src_train.get("fp16_run", False)
            train["_source"] = "so_vits_svc"

    cfg.setdefault("spk", {}).update(src.get("spk", {}))
    cfg.setdefault("emo", {}).update(src.get("emo", {}))


def _adapt_rvc_config(config_path: str, cfg: Dict[str, Any], fmt: str) -> None:
    """Map RVC config.json keys into CantioDAW config."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            src = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    m = cfg.setdefault("model", {})
    m["n_speakers"] = src.get("n_speakers", 1)
    version = "v2" if "v2" in fmt else "v1"
    feat_dim = 768 if "v2" in fmt else 256
    m["phoneme_feature_dim"] = feat_dim
    m["_source"] = "rvc"
    m["_rvc_version"] = version

    pth = src.get("pth_path", "")
    if pth:
        cfg.setdefault("paths", {})["pth_path"] = pth
    index = src.get("index_path", "")
    if index:
        cfg.setdefault("paths", {})["index_path"] = index

    cfg.setdefault("inference", {})["f0_method"] = src.get("f0method", "harvest")

    feat = cfg.setdefault("feature", {})
    feat["sample_rate"] = src.get("sample_rate", 40000)

    if "hop_bytes" in src:
        feat["hop_length"] = src["hop_bytes"]


def _adapt_ddsp_config(config_path: str, cfg: Dict[str, Any]) -> None:
    """Map DDSP-SVC config.yaml keys into CantioDAW config."""
    try:
        ext = Path(config_path).suffix.lower()
        with open(config_path, "r", encoding="utf-8") as f:
            if ext == ".yaml":
                import yaml
                src = yaml.safe_load(f)
            else:
                src = json.load(f)
    except (json.JSONDecodeError, IOError, ImportError):
        return

    m = cfg.setdefault("model", {})
    m["_source"] = "ddsp_svc"
    m["_ddsp_type"] = src.get("model", {}).get("type", "Sins")

    src_data = src.get("data", {})
    feat = cfg.setdefault("feature", {})
    if "sampling_rate" in src_data:
        feat["sample_rate"] = src_data["sampling_rate"]
    if "block_size" in src_data:
        feat["hop_length"] = src_data["block_size"]
    if "encoder_out_channels" in src_data:
        m["phoneme_feature_dim"] = src_data["encoder_out_channels"]

    src_model = src.get("model", {})
    if "n_spk" in src_model:
        m["n_speakers"] = src_model["n_spk"]


class _HybridSVCAdapter:
    """Adapter for CantioDAW-native HybridSVC models."""

    def __init__(self, model_path: str, config_path: str, device: Optional[str] = None):
        self.model_path = model_path
        self.config_path = config_path
        self.device = device
        self._inferencer = None

    def load(self):
        from src.inference.synthesizer import VocoderInference
        self._inferencer = VocoderInference(
            model_path=self.model_path,
            config_path=self.config_path,
            device=self.device,
        )

    def synthesize(
        self,
        phoneme_features: np.ndarray,
        f0: np.ndarray,
        spk_id: np.ndarray,
        f0_is_hz: bool = True,
    ) -> np.ndarray:
        if self._inferencer is None:
            self.load()
        return self._inferencer.synthesize(phoneme_features, f0, spk_id, f0_is_hz=f0_is_hz)

    @property
    def sample_rate(self) -> int:
        if self._inferencer is not None:
            return getattr(self._inferencer, "vocoder_sample_rate", 24000)
        return 24000


class _SVCAdapter:
    """Adapter for so-vits-svc models — native inference."""

    def __init__(self, model_path: str, config_path: str, device: Optional[str] = None):
        self.model_path = model_path
        self.config_path = config_path
        self.device = device
        self._svc_model = None
        self._config = None

    def load(self):
        from .native_inference import SVCInference
        self._svc_model = SVCInference(self.model_path, self.config_path, self.device)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def synthesize(
        self,
        phoneme_features: np.ndarray,
        f0: np.ndarray,
        spk_id: np.ndarray,
        f0_is_hz: bool = True,
    ) -> np.ndarray:
        if self._svc_model is None:
            self.load()
        sid = int(spk_id[0]) if spk_id is not None and spk_id.size > 0 else None
        if not f0_is_hz:
            f0 = 440.0 * (2.0 ** ((f0 - 69) / 12.0))
        return self._svc_model.synthesize(phoneme_features, f0, sid)

    @property
    def sample_rate(self) -> int:
        if self._config:
            data = self._config.get("data", {})
            if isinstance(data, dict) and "sampling_rate" in data:
                return data["sampling_rate"]
        return 44100


class _DDSPSVCAdapter:
    """Adapter for DDSP-SVC models — import-based from ddsp.vocoder."""

    def __init__(self, model_path: str, config_path: str, device: Optional[str] = None):
        self.model_path = model_path
        self.config_path = config_path
        self.device = device
        self._model = None
        self._args = None
        self._sample_rate = 44100

    def load(self):
        if self.device is None or self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            from ddsp.vocoder import load_model
        except ImportError:
            raise ImportError(
                "DDSP-SVC package not found. Install it from https://github.com/yxlllc/DDSP-SVC "
                "or add its parent directory to PYTHONPATH."
            )
        self._model, self._args = load_model(self.model_path, device=self.device)
        src_data = getattr(self._args, "data", {})
        if isinstance(src_data, dict):
            self._sample_rate = int(src_data.get("sampling_rate", 44100))
        else:
            self._sample_rate = 44100

    def synthesize(
        self,
        phoneme_features: np.ndarray,
        f0: np.ndarray,
        spk_id: np.ndarray,
        f0_is_hz: bool = True,
    ) -> np.ndarray:
        if self._model is None:
            self.load()

        device = next(self._model.parameters()).device

        units = torch.from_numpy(phoneme_features).float().unsqueeze(0).to(device)
        f = torch.from_numpy(f0).float().unsqueeze(0).to(device)
        if not f0_is_hz:
            f = 440.0 * (2.0 ** ((f - 69) / 12.0))

        n_frames = units.size(1)
        volume = torch.ones(1, n_frames, 1, device=device)

        sid = None
        if spk_id is not None and spk_id.size > 0:
            sid = torch.LongTensor([[int(spk_id[0])]]).to(device)

        with torch.no_grad():
            audio, _, _ = self._model(units, f, volume, spk_id=sid)

        audio_np = audio.squeeze().cpu().numpy().astype(np.float32)
        peak = np.max(np.abs(audio_np))
        if peak > 0:
            audio_np = audio_np / peak
        return audio_np

    @property
    def sample_rate(self) -> int:
        return self._sample_rate


class _RVCAdapter:
    """Adapter for RVC models (v1 and v2) — native inference."""

    def __init__(self, model_path: str, config_path: str, device: Optional[str] = None):
        self.model_path = model_path
        self.config_path = config_path
        self.device = device
        self._rvc_model = None
        self._config = None
        self._fmt = detect_model_format(model_path, config_path)

    def load(self):
        from .native_inference import RVCInference
        self._rvc_model = RVCInference(self.model_path, self.config_path, self.device)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def synthesize(
        self,
        phoneme_features: np.ndarray,
        f0: np.ndarray,
        spk_id: np.ndarray,
        f0_is_hz: bool = True,
    ) -> np.ndarray:
        if self._rvc_model is None:
            self.load()
        sid = int(spk_id[0]) if spk_id is not None and spk_id.size > 0 else None
        if not f0_is_hz:
            f0 = 440.0 * (2.0 ** ((f0 - 69) / 12.0))
        return self._rvc_model.synthesize(phoneme_features, f0, sid)

    @property
    def sample_rate(self) -> int:
        if self._config:
            return self._config.get("sample_rate", 40000)
        return 40000


_ADAPTER_MAP = {
    "cantiodaw_hybrid_svc": _HybridSVCAdapter,
    "so_vits_svc": _SVCAdapter,
    "rvc_v1": _RVCAdapter,
    "rvc_v2": _RVCAdapter,
    "applio_rvc": _RVCAdapter,
    "ddsp_svc": _DDSPSVCAdapter,
}


def create_adapter(model_path: str, config_path: Optional[str] = None,
                   device: Optional[str] = None) -> object:
    """Factory: detect format and return the correct model adapter.

    The returned adapter provides a unified interface:
      - load()
      - synthesize(phoneme_features, f0, spk_id, f0_is_hz) -> np.ndarray
      - sample_rate -> int

    Args:
        model_path: Path to the model file (.pth, .pt, .safetensors, etc.)
        config_path: Path to config file (auto-detected if None)
        device: Torch device string ("cpu", "cuda", "auto")

    Returns:
        An adapter instance with a standardized inference interface.

    Raises:
        FileNotFoundError: If model file does not exist.
    """
    model_path = os.path.abspath(model_path)
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if config_path is None:
        config_path = get_config_path(model_path)

    fmt = detect_model_format(model_path, config_path)
    logger.info(f"Detected model format: {fmt} at {model_path}")

    adapter_cls = _ADAPTER_MAP.get(fmt, _HybridSVCAdapter)
    return adapter_cls(model_path, config_path or "", device=device)
