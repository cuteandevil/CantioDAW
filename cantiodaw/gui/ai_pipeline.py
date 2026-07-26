from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QScrollArea, QLineEdit, QComboBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QFont
from .theme import CantioDAW_DARK as C


class CriticBar(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self._name = name
        self._score = 0.0
        self._color = C["accent"]

    def set_score(self, score: float):
        self._score = max(0.0, min(1.0, score))
        if score >= 0.8:
            self._color = C["success"]
        elif score >= 0.6:
            self._color = C["warning"]
        else:
            self._color = C["error"]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(C["bg_tertiary"]))
        painter.drawRoundedRect(0, 0, w, h, 3, 3)

        bar_w = int((w - 100) * self._score)
        painter.setBrush(QColor(self._color))
        painter.drawRoundedRect(80, 4, max(bar_w, 2), h - 8, 2, 2)

        painter.setPen(QColor(C["text_secondary"]))
        font = QFont(C["font_family"], 10)
        painter.setFont(font)
        painter.drawText(4, int(h * 0.7), self._name)

        painter.setPen(QColor(C["text_primary"]))
        pfont = QFont(C["mono_font"], 10)
        painter.setFont(pfont)
        painter.drawText(w - 44, int(h * 0.7), f"{self._score:.2f}")


class AIPipelineDock(QWidget):
    generate_clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("AI Composer")
        title.setStyleSheet(f"color: {C['accent']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Input section
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(6)

        self._bpm_input = QLineEdit("120")
        self._bpm_input.setPlaceholderText("BPM")
        input_layout.addWidget(QLabel("BPM:"))
        input_layout.addWidget(self._bpm_input)

        self._key_combo = QComboBox()
        self._key_combo.addItems(["C Major", "A Minor", "G Major", "E Minor", "D Major", "F Major", "D Minor"])
        input_layout.addWidget(QLabel("Key:"))
        input_layout.addWidget(self._key_combo)

        self._mood_input = QLineEdit()
        self._mood_input.setPlaceholderText("cinematic pop, upbeat, ...")
        input_layout.addWidget(QLabel("Mood:"))
        input_layout.addWidget(self._mood_input)

        gen_btn = QPushButton("Generate")
        gen_btn.setObjectName("accent")
        gen_btn.clicked.connect(self._on_generate)
        input_layout.addWidget(gen_btn)
        layout.addWidget(input_group)

        # Pipeline steps
        steps_group = QGroupBox("Pipeline")
        steps_layout = QVBoxLayout(steps_group)
        steps_layout.setSpacing(4)
        self._step_labels = {}
        for s in ["Intent", "Compose", "Params", "MIDI", "Critic", "Revise"]:
            row = QHBoxLayout()
            dot = QLabel("○")
            dot.setStyleSheet(f"color: {C['text_muted']};")
            label = QLabel(s)
            label.setStyleSheet(f"color: {C['text_muted']}; font-size: 12px;")
            row.addWidget(dot)
            row.addWidget(label)
            row.addStretch()
            steps_layout.addLayout(row)
            self._step_labels[s.lower()] = (dot, label)
        layout.addWidget(steps_group)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

        # Critic scores
        critic_group = QGroupBox("Critic Scores")
        critic_layout = QVBoxLayout(critic_group)
        critic_layout.setSpacing(4)
        self._critic_bars = {}
        for name in ["Pitch", "Rhythm", "Tonal", "Vocal", "Structure", "Overall"]:
            bar = CriticBar(name)
            critic_layout.addWidget(bar)
            self._critic_bars[name.lower()] = bar
        layout.addWidget(critic_group)

        layout.addStretch()

    def _on_generate(self):
        params = {
            "bpm": int(self._bpm_input.text() or 120),
            "key": self._key_combo.currentText().split()[0],
            "mood": self._mood_input.text(),
        }
        self.generate_clicked.emit(params)
        self._set_pipeline_running(True)

    def _set_pipeline_running(self, running: bool):
        self._progress.setVisible(running)

    def set_step(self, name: str, status: str):
        if name not in self._step_labels:
            return
        dot, label = self._step_labels[name]
        if status == "active":
            dot.setText("●")
            dot.setStyleSheet(f"color: {C['accent']};")
            label.setStyleSheet(f"color: {C['accent']}; font-size: 12px; font-weight: bold;")
        elif status in ("completed", "done"):
            dot.setText("✓")
            dot.setStyleSheet(f"color: {C['success']};")
            label.setStyleSheet(f"color: {C['success']}; font-size: 12px;")
        else:
            dot.setText("○")
            dot.setStyleSheet(f"color: {C['text_muted']};")
            label.setStyleSheet(f"color: {C['text_muted']}; font-size: 12px;")

    def set_progress(self, value: float):
        self._progress.setVisible(True)
        self._progress.setValue(int(value * 100))

    def set_scores(self, scores: dict):
        for k, v in scores.items():
            if k in self._critic_bars:
                self._critic_bars[k].set_score(v)

    def reset(self):
        for name in self._step_labels:
            self.set_step(name, "idle")
        self._progress.setVisible(False)
        for bar in self._critic_bars.values():
            bar.set_score(0.0)
