from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QCheckBox, QProgressBar, QFileDialog,
    QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from ..training.voice_trainer import VoiceTrainer, TrainingConfig


class TrainingWorker(QThread):
    progress = pyqtSignal(dict)
    finished = pyqtSignal(dict)

    def __init__(self, config: TrainingConfig, data_dir: str, checkpoint_dir: str):
        super().__init__()
        self.config = config
        self.data_dir = data_dir
        self.checkpoint_dir = checkpoint_dir

    def run(self):
        self.config.progress_callback = lambda p: self.progress.emit(p)
        trainer = VoiceTrainer(self.config)
        result = trainer.train(self.data_dir, self.checkpoint_dir)
        self.finished.emit(result)


class TrainingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Voice Training")
        self.setMinimumWidth(500)
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.name_edit = QLineEdit("MyVoice")
        form.addRow("Voice Name:", self.name_edit)

        data_layout = QHBoxLayout()
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("Select dataset directory...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_data)
        data_layout.addWidget(self.data_edit)
        data_layout.addWidget(browse_btn)
        form.addRow("Data Dir:", data_layout)

        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 10000)
        self.epochs_spin.setValue(50)
        form.addRow("Epochs:", self.epochs_spin)

        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 256)
        self.batch_spin.setValue(16)
        form.addRow("Batch Size:", self.batch_spin)

        self.lora_check = QCheckBox("Enable LoRA (parameter-efficient fine-tuning)")
        form.addRow(self.lora_check)

        layout.addLayout(form)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #8899aa; font-size: 12px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        self.train_btn = QPushButton("Start Training")
        self.train_btn.setObjectName("accent")
        self.train_btn.clicked.connect(self._start_training)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addStretch()
        btn_layout.addWidget(self.train_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse_data(self):
        path = QFileDialog.getExistingDirectory(self, "Select Dataset Directory")
        if path:
            self.data_edit.setText(path)

    def _start_training(self):
        import os
        data_dir = self.data_edit.text()
        if not os.path.isdir(data_dir):
            self.status_label.setText("Invalid data directory")
            self.status_label.setVisible(True)
            return

        config = TrainingConfig(
            voice_name=self.name_edit.text(),
            epochs=self.epochs_spin.value(),
            batch_size=self.batch_spin.value(),
            lora_enabled=self.lora_check.isChecked(),
        )
        ckpt_dir = f"checkpoints/{config.voice_name}"

        self._worker = TrainingWorker(config, data_dir, ckpt_dir)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

        self.train_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Training started...")

    def _on_progress(self, progress: dict):
        if progress.get("total", 0) > 0:
            pct = int(progress["epoch"] / progress["total"] * 100)
            self.progress_bar.setValue(pct)
            loss = progress.get("loss", 0)
            val_loss = progress.get("val_loss", 0)
            self.status_label.setText(
                f"Epoch {progress['epoch']}/{progress['total']}  "
                f"loss: {loss:.4f}  val_loss: {val_loss:.4f}"
            )

    def _on_finished(self, result: dict):
        self.train_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        status = result.get("status", "completed")
        if status == "completed":
            best = result.get("best_loss", 0)
            self.status_label.setText(f"Training complete! Best loss: {best:.4f}")
        else:
            self.status_label.setText(f"Training failed: {result.get('message', 'Unknown')}")
