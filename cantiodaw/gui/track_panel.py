from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QCheckBox, QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from .theme import CantioDAW_DARK as C

COLORS = C["track_colors"]


class TrackWidget(QFrame):
    remove_clicked = pyqtSignal(str)
    mute_toggled = pyqtSignal(str, bool)
    solo_toggled = pyqtSignal(str, bool)
    volume_changed = pyqtSignal(str, float)
    pan_changed = pyqtSignal(str, float)

    def __init__(self, track_id: str, name: str, track_type: str = "audio",
                 color_idx: int = 0, parent=None):
        super().__init__(parent)
        self.track_id = track_id
        self.color = COLORS[color_idx % len(COLORS)]
        self.setFixedHeight(52)
        self.setStyleSheet(f"""
            TrackWidget {{
                background-color: {C['bg_tertiary']};
                border: 1px solid {C['border']};
                border-radius: {C['corner_radius']}px;
                margin: 1px 0;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        color_bar = QFrame()
        color_bar.setFixedWidth(3)
        color_bar.setStyleSheet(f"background: {self.color}; border-radius: 1px;")
        layout.addWidget(color_bar)

        info = QVBoxLayout()
        info.setSpacing(0)
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {C['text_primary']}; font-size: {C['font_size_normal']}px;")
        type_label = QLabel(track_type)
        type_label.setStyleSheet(f"color: {C['text_muted']}; font-size: {C['font_size_small']}px;")
        info.addWidget(name_label)
        info.addWidget(type_label)
        layout.addLayout(info)
        layout.addStretch()

        self.mute_btn = QPushButton("M")
        self.mute_btn.setFixedSize(28, 28)
        self.mute_btn.setCheckable(True)
        self.mute_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['bg_tertiary']}; color: {C['text_secondary']};
                border: 1px solid {C['border']}; border-radius: 3px;
                font-size: 11px; font-weight: bold;
            }}
            QPushButton:checked {{
                background: {C['accent']}; color: white; border-color: {C['accent']};
            }}
        """)
        self.mute_btn.toggled.connect(lambda v: self.mute_toggled.emit(self.track_id, v))
        layout.addWidget(self.mute_btn)

        self.solo_btn = QPushButton("S")
        self.solo_btn.setFixedSize(28, 28)
        self.solo_btn.setCheckable(True)
        self.solo_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['bg_tertiary']}; color: {C['text_secondary']};
                border: 1px solid {C['border']}; border-radius: 3px;
                font-size: 11px; font-weight: bold;
            }}
            QPushButton:checked {{
                background: {C['warning']}; color: white; border-color: {C['warning']};
            }}
        """)
        self.solo_btn.toggled.connect(lambda v: self.solo_toggled.emit(self.track_id, v))
        layout.addWidget(self.solo_btn)

        vol_layout = QVBoxLayout()
        vol_layout.setSpacing(0)
        vol_label = QLabel("Vol")
        vol_label.setStyleSheet(f"color: {C['text_muted']}; font-size: 9px;")
        vol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.setFixedWidth(60)
        self.vol_slider.valueChanged.connect(
            lambda v: self.volume_changed.emit(self.track_id, v / 100.0))
        vol_layout.addWidget(vol_label)
        vol_layout.addWidget(self.vol_slider)
        layout.addLayout(vol_layout)

        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C['text_muted']};
                border: none; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ color: {C['accent']}; }}
        """)
        remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.track_id))
        layout.addWidget(remove_btn)


class TrackPanel(QScrollArea):
    track_added = pyqtSignal(str)
    track_removed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks = []
        self._widgets = {}
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {C['bg_secondary']};
                border: none;
            }}
        """)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(1)
        self._layout.addStretch()
        self.setWidget(container)

    def add_track(self, track_id: str, name: str = "", track_type: str = "audio"):
        color_idx = len(self._tracks) % len(COLORS)
        w = TrackWidget(track_id, name or f"Track {len(self._tracks)+1}",
                        track_type, color_idx)
        w.remove_clicked.connect(self._on_remove)
        self._tracks.append({"id": track_id, "name": name, "widget": w})
        self._widgets[track_id] = w

        self._layout.insertWidget(self._layout.count() - 1, w)
        self.track_added.emit(track_id)

    def remove_track(self, track_id: str):
        if track_id in self._widgets:
            w = self._widgets.pop(track_id)
            self._layout.removeWidget(w)
            w.deleteLater()
            self._tracks = [t for t in self._tracks if t["id"] != track_id]
            self.track_removed.emit(track_id)

    def _on_remove(self, track_id: str):
        self.remove_track(track_id)

    def clear(self):
        for tid in list(self._widgets.keys()):
            self.remove_track(tid)

    @property
    def track_count(self) -> int:
        return len(self._tracks)
