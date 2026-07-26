from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent
from typing import List, Optional
from .theme import CantioDAW_DARK as C


class Note:
    def __init__(self, pitch: int = 60, start: float = 0.0,
                 duration: float = 1.0, velocity: int = 100,
                 lyric: str = ""):
        self.pitch = pitch
        self.start = start
        self.duration = duration
        self.velocity = velocity
        self.lyric = lyric
        self.selected = False

    @property
    def end(self) -> float:
        return self.start + self.duration


class PianoRoll(QWidget):
    notes_changed = pyqtSignal(list)

    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    WHITE_KEYS = [0, 2, 4, 5, 7, 9, 11]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notes: List[Note] = []
        self._start_pitch = 36
        self._end_pitch = 84
        self._pixels_per_beat = 80
        self._beats = 16
        self._key_width = 50
        self._beat_height = 48
        self._current_beat = 0.0
        self._dragging = False
        self._drag_note = None
        self.setMinimumHeight(300)
        self.setMouseTracking(True)

    def set_notes(self, notes: List[Note]):
        self._notes = notes
        self.update()

    def add_note(self, pitch: int, beat: float, duration: float = 1.0):
        n = Note(pitch=pitch, start=beat, duration=duration)
        self._notes.append(n)
        self.notes_changed.emit(self._notes)
        self.update()

    def clear_notes(self):
        self._notes.clear()
        self.notes_changed.emit(self._notes)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        total_keys = self._end_pitch - self._start_pitch
        key_height = h / total_keys
        grid_left = self._key_width
        grid_width = w - grid_left

        # Background
        painter.fillRect(0, 0, w, h, QColor(C["bg_tertiary"]))

        # Piano keys (left column)
        for i in range(total_keys):
            pitch = self._end_pitch - 1 - i
            y = i * key_height
            is_white = (pitch % 12) in self.WHITE_KEYS
            color = QColor("#ffffff" if is_white else "#333333")
            painter.fillRect(0, int(y), self._key_width, int(key_height) + 1, color)
            if is_white:
                painter.setPen(QPen(QColor("#555555"), 0.5))
                painter.drawLine(0, int(y), self._key_width, int(y))

            # Note names
            if is_white and pitch % 12 == 0:
                octave = pitch // 12 - 1
                name = f"C{octave}"
                painter.setPen(QColor("#666666"))
                font = QFont(C["font_family"], 8)
                painter.setFont(font)
                painter.drawText(4, int(y + key_height * 0.7), name)

        # Grid lines
        beats_px = grid_width / max(self._beats, 1)
        for beat in range(self._beats + 1):
            x = int(grid_left + beat * beats_px)
            painter.setPen(QPen(QColor(C["border"]), 0.5 if beat % 4 != 0 else 1))
            painter.drawLine(x, 0, x, h)

        # Beat numbers
        painter.setPen(QColor(C["text_muted"]))
        font = QFont(C["font_family"], 9)
        painter.setFont(font)
        for beat in range(self._beats):
            x = int(grid_left + beat * beats_px + 4)
            painter.drawText(x, 12, str(beat + 1))

        # Notes
        for note in self._notes:
            x = int(grid_left + note.start * beats_px)
            note_width = int(max(note.duration * beats_px, 4))
            pitch_offset = self._end_pitch - 1 - note.pitch
            y = int(pitch_offset * key_height + 2)
            nh = int(key_height - 4)

            color = QColor(C["accent"] if not note.selected else "#ff6b81")
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#ffffff"), 0.5))
            painter.drawRoundedRect(x, y, note_width, nh, 3, 3)

            # Lyric
            if note.lyric:
                painter.setPen(QColor("#ffffff"))
                font = QFont(C["font_family"], 8)
                painter.setFont(font)
                painter.drawText(x + 4, y + nh * 0.7, note.lyric[:3])

        # Playhead
        if self._current_beat > 0:
            x = int(grid_left + self._current_beat * beats_px)
            painter.setPen(QPen(QColor(C["accent"]), 2))
            painter.drawLine(x, 0, x, h)

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()
        if pos.x() < self._key_width:
            pitch_offset = int((pos.y() / self.height()) * (self._end_pitch - self._start_pitch))
            pitch = self._end_pitch - 1 - pitch_offset
            pitch = max(0, min(127, pitch))
            return

        beats_px = (self.width() - self._key_width) / max(self._beats, 1)
        beat = (pos.x() - self._key_width) / beats_px
        if beat < 0:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            pitch_offset = int((pos.y() / self.height()) * (self._end_pitch - self._start_pitch))
            pitch = self._end_pitch - 1 - pitch_offset
            pitch = max(0, min(127, pitch))
            self.add_note(pitch, beat)

    def mouseMoveEvent(self, event):
        pos = event.position()
        if pos.x() >= self._key_width:
            beats_px = (self.width() - self._key_width) / max(self._beats, 1)
            self._current_beat = (pos.x() - self._key_width) / beats_px
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self._notes = [n for n in self._notes if not n.selected]
            self.notes_changed.emit(self._notes)
            self.update()
        elif event.key() == Qt.Key.Key_A and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            for n in self._notes:
                n.selected = True
            self.update()
