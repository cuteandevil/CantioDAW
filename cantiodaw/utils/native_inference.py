"""Native inference for SVC (so-vits-svc) and RVC models."""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


# ─── Common building blocks ───

class ResBlock1(nn.Module):
    """Residual block used in both SVC and RVC generators."""
    def __init__(self, channels, kernel_size=3, dilation=(1, 3, 5)):
        super().__init__()
        self.convs1 = nn.ModuleList([
            nn.Conv1d(channels, channels, kernel_size, 1, dilation=d, padding=d * (kernel_size - 1) // 2)
            for d in dilation
        ])
        self.convs2 = nn.ModuleList([
            nn.Conv1d(channels, channels, kernel_size, 1, dilation=1, padding=(kernel_size - 1) // 2)
            for _ in dilation
        ])

    def forward(self, x):
        for c1, c2 in zip(self.convs1, self.convs2):
            xt = F.leaky_relu(x, 0.1)
            xt = c1(xt)
            xt = F.leaky_relu(xt, 0.1)
            xt = c2(xt)
            x = xt + x
        return x


class ResBlock2(nn.Module):
    """Residual block with larger dilations for RVC."""
    def __init__(self, channels, kernel_size=3, dilation=(1, 3)):
        super().__init__()
        self.convs = nn.ModuleList([
            nn.Conv1d(channels, channels, kernel_size, 1, dilation=d, padding=d * (kernel_size - 1) // 2)
            for d in dilation
        ])

    def forward(self, x):
        for c in self.convs:
            xt = F.leaky_relu(x, 0.1)
            xt = c(xt)
            x = xt + x
        return x


class HiFiGANGenerator(nn.Module):
    """HiFi-GAN generator (dec) used by SVC and RVC."""
    def __init__(self, in_channels=256, out_channels=1, upsample_rates=(8, 8, 2, 2),
                 upsample_kernel_sizes=(16, 16, 4, 4), upsample_initial_channel=512,
                 resblock_kernel_sizes=(3, 7, 11), resblock_dilations=((1, 3, 5), (1, 3, 5), (1, 3, 5)),
                 use_rvc_style=False):
        super().__init__()
        self.num_kernels = len(resblock_kernel_sizes)
        self.num_upsamples = len(upsample_rates)
        self.conv_pre = nn.Conv1d(in_channels, upsample_initial_channel, 7, 1, padding=3)

        self.ups = nn.ModuleList()
        for i, (u, k) in enumerate(zip(upsample_rates, upsample_kernel_sizes)):
            self.ups.append(nn.ConvTranspose1d(
                upsample_initial_channel // (2 ** i),
                upsample_initial_channel // (2 ** (i + 1)),
                k, u, padding=(k - u) // 2
            ))

        self.resblocks = nn.ModuleList()
        resblock_cls = ResBlock2 if use_rvc_style else ResBlock1
        for i in range(len(self.ups)):
            ch = upsample_initial_channel // (2 ** (i + 1))
            for j in range(len(resblock_kernel_sizes)):
                self.resblocks.append(resblock_cls(ch, resblock_kernel_sizes[j], resblock_dilations[j]))

        self.conv_post = nn.Conv1d(ch, out_channels, 7, 1, padding=3)

    def forward(self, x):
        x = self.conv_pre(x)
        for i, up in enumerate(self.ups):
            x = F.leaky_relu(x, 0.1)
            x = up(x)
            xs = None
            for j in range(self.num_kernels):
                res_out = self.resblocks[i * self.num_kernels + j](x)
                xs = res_out if xs is None else xs + res_out
            x = xs / self.num_kernels
        x = F.leaky_relu(x)
        x = self.conv_post(x)
        x = torch.tanh(x)
        return x


class WaveNetResidualBlock(nn.Module):
    """WaveNet-style residual block for SVC's coupling layers."""
    def __init__(self, channels, kernel_size=3, dilations=(1, 3, 5)):
        super().__init__()
        self.convs = nn.ModuleList()
        for d in dilations:
            p = d * (kernel_size - 1) // 2
            self.convs.append(nn.Conv1d(channels, channels, kernel_size, 1, dilation=d, padding=p))

    def forward(self, x, x_mask):
        for conv in self.convs:
            xt = F.leaky_relu(x, 0.1)
            xt = conv(xt)
            xt = xt * x_mask
            x = x + xt
        return x


# ─── SVC-specific components ───

class TextEncoder(nn.Module):
    """SVC TextEncoder: phoneme features → latent representation."""
    def __init__(self, in_channels=256, out_channels=192, n_layers=6, kernel_size=5, p_dropout=0.1):
        super().__init__()
        self.out_channels = out_channels
        self.pre = nn.Conv1d(in_channels, out_channels, 1)
        self.enc = nn.ModuleList()
        for _ in range(n_layers):
            self.enc.append(nn.Conv1d(out_channels, out_channels, kernel_size, 1, padding=kernel_size//2))
        self.proj = nn.Conv1d(out_channels, out_channels * 2, 1)
        self.drop = nn.Dropout(p_dropout)

    def forward(self, x, x_mask):
        x = self.pre(x) * x_mask
        for conv in self.enc:
            xt = F.leaky_relu(x, 0.1)
            xt = self.drop(xt)
            xt = conv(xt) * x_mask
            x = x + xt
        stats = self.proj(x) * x_mask
        m, logs = stats.chunk(2, dim=1)
        return x, m, logs


class ResidualCouplingBlock(nn.Module):
    """Normalizing flow coupling block for SVC."""
    def __init__(self, channels, hidden_channels=192, kernel_size=5, n_layers=6, n_flows=4):
        super().__init__()
        self.flows = nn.ModuleList()
        for i in range(n_flows):
            self.flows.append(
                nn.ModuleList([
                    nn.Conv1d(channels, hidden_channels, 1),
                    WaveNetResidualBlock(hidden_channels, kernel_size, (1, 3, 5)),
                    nn.Conv1d(hidden_channels, channels * 2, 1),
                ])
            )

    def forward(self, x, x_mask):
        for pre, wnet, post in self.flows:
            xt = pre(x)
            xt = wnet(xt, x_mask)
            stats = post(xt) * x_mask
            m, logs = stats.chunk(2, dim=1)
            x = (x - m) * torch.exp(-logs) * x_mask
        return x


class SVCSynthesizer(nn.Module):
    """SVC (so-vits-svc) SynthesizerTrn for inference."""
    def __init__(self, inter_channels=256, filter_channels=512, n_heads=2,
                 n_layers=6, kernel_size=5, p_dropout=0.1, n_speakers=1,
                 sampling_rate=44100, hop_length=512, n_fft=2048):
        super().__init__()
        self.hop_length = hop_length
        self.n_speakers = n_speakers
        self.emb_g = nn.Embedding(n_speakers, inter_channels) if n_speakers > 1 else None

        self.enc_p = TextEncoder(inter_channels, filter_channels // 2, n_layers, kernel_size, p_dropout)
        self.flow = ResidualCouplingBlock(inter_channels, filter_channels // 2, kernel_size, n_layers, n_flows=4)
        self.dec = HiFiGANGenerator(
            in_channels=inter_channels,
            upsample_rates=(8, 8, 2, 2),
            upsample_kernel_sizes=(16, 16, 4, 4),
            upsample_initial_channel=filter_channels,
        )

    def forward(self, c, f0, spk_id=None, noise_scale=0.667):
        """
        Args:
            c: phoneme features (1, C, T)
            f0: F0 contour (1, 1, T) — used as mask, ignored in coupling
            spk_id: speaker ID (1,) or None
            noise_scale: random noise scale for coupling
        Returns:
            audio: waveform (samples,)
        """
        x_mask = torch.ones_like(f0)

        if self.emb_g is not None and spk_id is not None:
            g = self.emb_g(spk_id).unsqueeze(-1)
            c = c + g

        z, m_p, logs_p = self.enc_p(c, x_mask)
        z = z + torch.randn_like(z) * noise_scale
        z = self.flow(z, x_mask)
        audio = self.dec(z)
        return audio.squeeze(0).squeeze(0)


# ─── RVC-specific components ───

class RVCContentEncoder(nn.Module):
    """RVC content encoder (similar to SVC's text encoder but for HuBERT features)."""
    def __init__(self, in_channels=256, out_channels=256, n_layers=12, kernel_size=5):
        super().__init__()
        self.pre = nn.Conv1d(in_channels, out_channels, 1)
        self.enc = nn.ModuleList()
        for _ in range(n_layers):
            self.enc.append(nn.Conv1d(out_channels, out_channels, kernel_size, 1, padding=kernel_size//2))

    def forward(self, x, x_mask):
        x = self.pre(x) * x_mask
        for conv in self.enc:
            xt = F.leaky_relu(x, 0.1)
            xt = conv(xt) * x_mask
            x = x + xt
        return x


class RVCGenerator(nn.Module):
    """RVC generator: content encoder + HiFi-GAN decoder."""
    def __init__(self, inter_channels=768, filter_channels=512, n_layers=12,
                 n_speakers=1, sampling_rate=40000, hop_length=512):
        super().__init__()
        self.hop_length = hop_length
        self.n_speakers = n_speakers
        self.emb_g = nn.Embedding(n_speakers, inter_channels) if n_speakers > 1 else None

        self.enc = RVCContentEncoder(inter_channels, inter_channels, n_layers)
        self.dec = HiFiGANGenerator(
            in_channels=inter_channels,
            upsample_rates=(8, 8, 2, 2, 2) if sampling_rate >= 40000 else (8, 8, 2, 2),
            upsample_kernel_sizes=(16, 16, 4, 4, 4) if sampling_rate >= 40000 else (16, 16, 4, 4),
            upsample_initial_channel=filter_channels,
            use_rvc_style=True,
        )

    def forward(self, c, f0, spk_id=None):
        x_mask = torch.ones_like(f0)
        if self.emb_g is not None and spk_id is not None:
            g = self.emb_g(spk_id).unsqueeze(-1)
            c = c + g
        z = self.enc(c, x_mask)
        audio = self.dec(z)
        return audio.squeeze(0).squeeze(0)


# ─── Inference wrappers ───

def _load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_svc_model(config: Dict[str, Any]) -> SVCSynthesizer:
    model_cfg = config.get("model", {})
    data_cfg = config.get("data", {})
    return SVCSynthesizer(
        inter_channels=model_cfg.get("inter_channels", 256),
        filter_channels=model_cfg.get("filter_channels", 512),
        n_heads=model_cfg.get("n_heads", 2),
        n_layers=model_cfg.get("n_layers", 6),
        kernel_size=model_cfg.get("kernel_size", 5),
        p_dropout=model_cfg.get("p_dropout", 0.1),
        n_speakers=model_cfg.get("n_speakers", model_cfg.get("num_speakers", 1)),
        sampling_rate=data_cfg.get("sampling_rate", 44100),
        hop_length=data_cfg.get("hop_length", 512),
        n_fft=data_cfg.get("filter_length", 2048),
    )


def _build_rvc_model(config: Dict[str, Any]) -> RVCGenerator:
    model_cfg = config.get("model", {})
    inter_channels = model_cfg.get("inter_channels", 768)
    filter_channels = model_cfg.get("filter_channels", 512)
    return RVCGenerator(
        inter_channels=inter_channels,
        filter_channels=filter_channels,
        n_layers=model_cfg.get("n_layers", 12),
        n_speakers=config.get("n_speakers", 1),
        sampling_rate=config.get("sample_rate", 40000),
        hop_length=config.get("hop_bytes", config.get("hop_length", 512)),
    )


def _load_state_dict(model: nn.Module, model_path: str, device: torch.device,
                     prefix_remap: Optional[Dict[str, str]] = None,
                     strict: bool = False) -> None:
    """Load checkpoint with optional key remapping."""
    ckpt = torch.load(model_path, map_location="cpu", weights_only=True)

    if isinstance(ckpt, dict):
        if "state_dict" in ckpt:
            state = ckpt["state_dict"]
        elif "model" in ckpt:
            state = ckpt["model"]
        elif "net_g" in ckpt:
            state = ckpt["net_g"]
        elif "generator" in ckpt:
            state = ckpt["generator"]
        else:
            state = ckpt
    else:
        state = {"": ckpt}

    if prefix_remap:
        remapped = {}
        for k, v in state.items():
            new_k = k
            for old_p, new_p in prefix_remap.items():
                if k.startswith(old_p):
                    new_k = new_p + k[len(old_p):]
                    break
            remapped[new_k] = v
        state = remapped

    keys = set(model.state_dict().keys())
    load_keys = set(state.keys())
    missing = keys - load_keys
    extra = load_keys - keys
    if missing:
        logger.warning(f"Missing keys: {len(missing)} (e.g. {list(missing)[:3]})")
    if extra:
        logger.warning(f"Extra keys: {len(extra)} (e.g. {list(extra)[:3]})")

    incompatible = model.load_state_dict(state, strict=False)
    if incompatible.unexpected_keys:
        logger.warning(f"Unexpected keys: {incompatible.unexpected_keys[:5]}")
    model.to(device)
    model.eval()


class SVCInference:
    """Native SVC (so-vits-svc) inference wrapper."""
    def __init__(self, model_path: str, config_path: str, device: Optional[str] = None):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        config = _load_config(config_path)
        self.model = _build_svc_model(config).to(self.device)
        self.hop_length = self.model.hop_length
        self.sampling_rate = config.get("data", {}).get("sampling_rate", 44100)

        _load_state_dict(self.model, model_path, self.device, prefix_remap={
            "enc_p.": "enc_p.",
            "flow.": "flow.",
            "dec.": "dec.",
            "emb_g.": "emb_g.",
        })
        logger.info(f"SVC model loaded: {model_path}")

    def synthesize(self, phoneme_features: np.ndarray, f0: np.ndarray,
                   spk_id: Optional[int] = None) -> np.ndarray:
        c = torch.from_numpy(phoneme_features).float().unsqueeze(0).to(self.device)
        f = torch.from_numpy(f0).float().unsqueeze(0).to(self.device)
        sid = torch.tensor([spk_id or 0], dtype=torch.long).to(self.device) if self.model.n_speakers > 1 else None

        with torch.no_grad():
            audio = self.model(c, f, sid)

        audio_np = audio.cpu().numpy().astype(np.float32)
        peak = np.max(np.abs(audio_np))
        if peak > 0:
            audio_np = audio_np / peak
        return audio_np


class RVCInference:
    """Native RVC v1/v2 inference wrapper."""
    def __init__(self, model_path: str, config_path: str, device: Optional[str] = None):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        config = _load_config(config_path)
        self.model = _build_rvc_model(config).to(self.device)
        self.hop_length = self.model.hop_length
        self.sampling_rate = config.get("sample_rate", 40000)

        _load_state_dict(self.model, model_path, self.device, prefix_remap={
            "generator.": "",
            "emb_g.": "emb_g.",
            "enc.": "enc.",
        })
        logger.info(f"RVC model loaded: {model_path}")

    def synthesize(self, content_features: np.ndarray, f0: np.ndarray,
                   spk_id: Optional[int] = None) -> np.ndarray:
        c = torch.from_numpy(content_features).float().unsqueeze(0).to(self.device)
        f = torch.from_numpy(f0).float().unsqueeze(0).to(self.device)
        sid = torch.tensor([spk_id or 0], dtype=torch.long).to(self.device) if self.model.n_speakers > 1 else None

        with torch.no_grad():
            audio = self.model(c, f, sid)

        audio_np = audio.cpu().numpy().astype(np.float32)
        peak = np.max(np.abs(audio_np))
        if peak > 0:
            audio_np = audio_np / peak
        return audio_np


def create_native_inference(model_path: str, config_path: str,
                            model_format: str = "so_vits_svc",
                            device: Optional[str] = None):
    """Factory: create the correct native inference wrapper by format."""
    if model_format.startswith("rvc"):
        return RVCInference(model_path, config_path, device)
    elif model_format == "so_vits_svc":
        return SVCInference(model_path, config_path, device)
    else:
        raise ValueError(f"Unsupported format for native inference: {model_format}")
