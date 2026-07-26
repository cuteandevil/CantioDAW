from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QFont
from .theme import CantioDAW_DARK as C


class VUMeter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(12)
        self.setMinimumHeight(80)
        self._level = 0.0
        self._peak = 0.0

    def set_level(self, level: float):
        self._level = max(0.0, min(1.0, level))
        self._peak = max(self._peak, self._level)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(C["bg_tertiary"]))
        painter.drawRoundedRect(0, 0, w, h, 2, 2)

        fill_h = int(h * self._level)
        color = C["success"]
        if self._level > 0.8:
            color = C["error"]
        elif self._level > 0.6:
            color = C["warning"]
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(2, h - fill_h, w - 4, fill_h, 1, 1)


class ChannelStrip(QFrame):
    volume_changed = pyqtSignal(str, float)
    pan_changed = pyqtSignal(str, float)
    mute_toggled = pyqtSignal(str, bool)
    solo_toggled = pyqtSignal(str, bool)

    def __init__(self, channel_id: str, name: str, color: str, parent=None):
        super().__init__(parent)
        self.channel_id = channel_id
        self.setFixedWidth(72)
        self.setStyleSheet(f"""
            ChannelStrip {{
                background: {C['bg_tertiary']};
                border: 1px solid {C['border']};
                border-radius: 4px;
                margin: 1px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(4)

        name_label = QLabel(name[:10])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"color: {C['text_primary']}; font-size: 10px;")
        layout.addWidget(name_label)

        self._vu = VUMeter()
        layout.addWidget(self._vu, 1)

        self._fader = QSlider(Qt.Orientation.Vertical)
        self._fader.setRange(0, 100)
        self._fader.setValue(80)
        self._fader.setStyleSheet(f"""
            QSlider::groove:vertical {{
                background: {C['bg_primary']}; width: 4px; border-radius: 2px;
            }}
            QSlider::handle:vertical {{
                background: {color}; width: 14px; height: 4px;
                margin: 0 -5px; border-radius: 2px;
            }}
            QSlider::sub-page:vertical {{
                background: {color}; border-radius: 2px;
            }}
        """)
        self._fader.valueChanged.connect(
            lambda v: self.volume_changed.emit(self.channel_id, v / 100.0))
        layout.addWidget(self._fader)

        vol_label = QLabel("80")
        vol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vol_label.setStyleSheet(f"color: {C['text_muted']}; font-size: 9px; font-family: {C['mono_font']};")
        self._fader.valueChanged.connect(lambda v: vol_label.setText(str(v)))
        layout.addWidget(vol_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(2)

        mute_btn = QPushButton("M")
        mute_btn.setFixedSize(22, 18)
        mute_btn.setCheckable(True)
        mute_btn.setStyleSheet(f"""
            QPushButton {{ background: {C['bg_primary']}; color: {C['text_muted']};
                border: none; border-radius: 2px; font-size: 9px; font-weight: bold; }}
            QPushButton:checked {{ background: {C['accent']}; color: white; }}
        """)
        mute_btn.toggled.connect(lambda v: self.mute_toggled.emit(self.channel_id, v))
        btn_row.addWidget(mute_btn)

        solo_btn = QPushButton("S")
        solo_btn.setFixedSize(22, 18)
        solo_btn.setCheckable(True)
        solo_btn.setStyleSheet(f"""
            QPushButton {{ background: {C['bg_primary']}; color: {C['text_muted']};
                border: none; border-radius: 2px; font-size: 9px; font-weight: bold; }}
            QPushButton:checked {{ background: {C['warning']}; color: white; }}
        """)
        solo_btn.toggled.connect(lambda v: self.solo_toggled.emit(self.channel_id, v))
        btn_row.addWidget(solo_btn)

        layout.addLayout(btn_row)

    def set_level(self, level: float):
        self._vu.set_level(level)


class MixerPanel(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._channels = {}

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"QScrollArea {{ background: {C['bg_secondary']}; border: none; }}")

        container = QWidget()
        self._layout = QHBoxLayout(container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)
        self._layout.addStretch()
        self.setWidget(container)

        title_bar = QLabel("Mixer")
        title_bar.setStyleSheet(f"color: {C['text_secondary']}; font-size: 12px; font-weight: bold; padding: 4px;")

    def add_channel(self, channel_id: str, name: str, color: str = C["accent"]):
        strip = ChannelStrip(channel_id, name, color)
        self._channels[channel_id] = strip
        self._layout.insertWidget(self._layout.count() - 1, strip)

    def remove_channel(self, channel_id: str):
        if channel_id in self._channels:
            strip = self._channels.pop(channel_id)
            self._layout.removeWidget(strip)
            strip.deleteLater()

    def set_level(self, channel_id: str, level: float):
        if channel_id in self._channels:
            self._channels[channel_id].set_level(level)

    def clear(self):
        for cid in list(self._channels.keys()):
            self.remove_channel(cid)
