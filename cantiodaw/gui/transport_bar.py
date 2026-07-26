from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSlider, QSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from .theme import CantioDAW_DARK as C


class TransportBar(QWidget):
    play_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    record_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    bpm_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setStyleSheet(f"background: {C['bg_secondary']}; border-top: 1px solid {C['border']};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("transport")
        self.play_btn.clicked.connect(self.play_clicked.emit)
        layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("■")
        self.stop_btn.setObjectName("transport")
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self.stop_btn)

        self.record_btn = QPushButton("●")
        self.record_btn.setObjectName("transport")
        self.record_btn.setObjectName("record")
        self.record_btn.clicked.connect(self.record_clicked.emit)
        layout.addWidget(self.record_btn)

        layout.addSpacing(16)

        bpm_label = QLabel("BPM")
        bpm_label.setStyleSheet(f"color: {C['text_secondary']}; font-size: {C['font_size_small']}px;")
        layout.addWidget(bpm_label)

        self.bpm_spin = QSpinBox()
        self.bpm_spin.setRange(20, 400)
        self.bpm_spin.setValue(120)
        self.bpm_spin.setFixedWidth(56)
        self.bpm_spin.valueChanged.connect(self.bpm_changed.emit)
        layout.addWidget(self.bpm_spin)

        self.time_label = QLabel("0:00.000")
        self.time_label.setStyleSheet(f"""
            color: {C['accent']}; font-size: 18px; font-weight: bold;
            font-family: 'Consolas', monospace; padding: 0 12px;
        """)
        layout.addWidget(self.time_label)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setValue(0)
        self.position_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {C['bg_tertiary']}; height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {C['accent']}; width: 10px; height: 16px;
                margin: -6px 0; border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {C['accent']}; border-radius: 2px;
            }}
        """)
        layout.addWidget(self.position_slider, 1)

        export_btn = QPushButton("🎵 Export")
        export_btn.setObjectName("accent")
        export_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(export_btn)

    def set_time(self, seconds: float):
        mins = int(seconds // 60)
        secs = seconds % 60
        self.time_label.setText(f"{mins}:{secs:06.3f}")
