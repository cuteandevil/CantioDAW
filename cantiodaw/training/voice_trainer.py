import os
import json
import yaml
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    voice_name: str = ""
    model_type: str = "hybrid_svc"
    epochs: int = 100
    batch_size: int = 16
    learning_rate: float = 0.001
    checkpoint_format: str = "safetensors"
    lora_enabled: bool = False
    lora_r: int = 8
    lora_alpha: float = 1.0
    use_amp: bool = False
    val_split: float = 0.1
    progress_callback: Optional[Callable] = None

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if k != "progress_callback"}

    @classmethod
    def from_dict(cls, d: Dict) -> "TrainingConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class VoiceTrainer:
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.current_epoch = 0
        self.total_epochs = config.epochs
        self.best_loss = float("inf")
        self.history: Dict[str, list] = {"loss": [], "val_loss": []}
        self._model = None
        self._trainer = None

    def train(self, data_dir: str, checkpoint_dir: str) -> Dict:
        logger.info(f"Starting training for voice: {self.config.voice_name}")
        logger.info(f"  Data: {data_dir}, Epochs: {self.config.epochs}, Batch: {self.config.batch_size}")

        from src.models.hybrid_svc import MultiTaskHybridSVC as HybridSVC
        from src.training.trainer import CantioAITrainer
        from src.data.dataset import CantioAIDataset
        import torch
        import torch.utils.data as data_utils

        data_path = Path(data_dir)
        train_ds = CantioAIDataset(data_path, split="train",
                                   phoneme_feature_dim=32, spectral_envelope_dim=60)
        val_ds = CantioAIDataset(data_path, split="val",
                                 phoneme_feature_dim=32, spectral_envelope_dim=60)

        if len(train_ds) == 0:
            logger.warning("No training samples found, using synthetic data")
            return {"status": "no_data", "message": "No training data available"}

        train_loader = data_utils.DataLoader(train_ds, batch_size=self.config.batch_size, shuffle=True)
        val_loader = data_utils.DataLoader(val_ds, batch_size=self.config.batch_size)

        train_config = {
            "model": {"phoneme_feature_dim": 32, "spectral_envelope_dim": 60,
                      "speaker_embed_dim": 128, "n_speakers": 10, "use_pitch_quantizer": True},
            "training": {"batch_size": self.config.batch_size,
                         "learning_rate": self.config.learning_rate,
                         "weight_decay": 1e-5, "epochs": self.config.epochs,
                         "optimizer": "adam", "lr_scheduler": "none",
                         "use_amp": self.config.use_amp, "device": "auto",
                         "checkpoint_format": self.config.checkpoint_format},
            "loss": {"sp_loss_weight": 1.0, "f0_loss_weight": 0.1},
            "experiment": {"name": self.config.voice_name,
                           "checkpoint_dir": checkpoint_dir},
        }
        if self.config.lora_enabled:
            train_config["training"]["lora"] = {
                "enabled": True, "r": self.config.lora_r, "alpha": self.config.lora_alpha,
                "dropout": 0.0, "auto_scan": True,
            }

        model = HybridSVC(**train_config["model"])
        self._trainer = CantioAITrainer(
            model=model, train_loader=train_loader, val_loader=val_loader,
            config=train_config, device="auto",
        )

        for epoch in range(1, self.config.epochs + 1):
            metrics = self._trainer.train_epoch(epoch=epoch)
            loss = metrics.get("loss", 0)
            val_loss = metrics.get("val_loss", loss)
            self.history["loss"].append(loss)
            self.history["val_loss"].append(val_loss)
            self.current_epoch = epoch

            if val_loss < self.best_loss:
                self.best_loss = val_loss
                self._trainer.save_checkpoint(epoch, is_best=True)

            if epoch % 10 == 0 or epoch == 1:
                logger.info(f"Epoch {epoch}/{self.config.epochs}: loss={loss:.4f}, val_loss={val_loss:.4f}")

            if self.config.progress_callback:
                self.config.progress_callback({
                    "epoch": epoch, "total": self.config.epochs,
                    "loss": loss, "val_loss": val_loss,
                    "best_loss": self.best_loss,
                })

        self._trainer.save_checkpoint(epoch=self.config.epochs, is_best=False)
        logger.info(f"Training complete! Best loss: {self.best_loss:.4f}")

        return {
            "status": "completed",
            "voice": self.config.voice_name,
            "epochs": self.current_epoch,
            "best_loss": self.best_loss,
            "checkpoint_dir": checkpoint_dir,
            "history": self.history,
        }

    def resume(self, checkpoint_path: str, data_dir: str, checkpoint_dir: str) -> Dict:
        logger.info(f"Resuming training from: {checkpoint_path}")
        self.train(data_dir, checkpoint_dir)
        return self.history


from dataclasses import asdict
