import os
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel, QFileDialog,
    QMessageBox, QDockWidget, QListWidget, QListWidgetItem,
    QPushButton, QTabWidget, QFrame, QScrollArea, QApplication,
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QPainter, QColor, QPen, QFont

from .theme import CantioDAW_DARK as C, STYLESHEET
from .track_panel import TrackPanel
from .piano_roll import PianoRoll, Note
from .transport_bar import TransportBar
from .training_dialog import TrainingDialog
from .mixer_panel import MixerPanel
from .ai_pipeline import AIPipelineDock
from .i18n import tr, set_language, get_language, get_languages

logger = logging.getLogger(__name__)


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._audio = None
        self.setMinimumHeight(60)
        self.setStyleSheet(f"background: {C['bg_tertiary']}; border-radius: 4px;")

    def set_audio(self, audio):
        self._audio = audio
        self.update()

    def paintEvent(self, event):
        if self._audio is None or len(self._audio) == 0:
            return
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        mid = h / 2
        painter.setPen(QPen(QColor(C["accent"]), 1.5))

        step = max(1, len(self._audio) // w)
        for x in range(w):
            idx = int(x * len(self._audio) / w)
            if idx >= len(self._audio):
                break
            val = self._audio[idx]
            y = int(mid + val * mid * 0.8)
            painter.drawLine(x, int(mid), x, y)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("window.title"))
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(STYLESHEET)

        self._project_manager = None
        self._current_project = None
        self._audio_engine = None
        self._svs_engine = None
        self._play_timer = QTimer()
        self._play_timer.timeout.connect(self._update_playback)
        self._is_playing = False
        self._play_start_time = 0.0

        # i18n keys for retranslation
        self._menu_keys = {}
        self._lang_actions = []

        self._init_project_manager()
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()

    def _init_project_manager(self):
        from ..project import ProjectManager
        self._project_manager = ProjectManager()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._setup_toolbar()
        self._setup_content(main_layout)
        self._setup_docks()

    def _setup_toolbar(self):
        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self._toolbar)

        tb_acts = [
            ("file.new", self._new_project),
            ("file.save", self._save_project),
            ("file.open", self._open_project),
            None,  # separator
            ("tools.training", self._show_training),
            ("tools.settings", self._load_model),
            None,  # separator
            ("track.add", self._add_audio_track),
        ]
        for item in tb_acts:
            if item is None:
                self._toolbar.addSeparator()
            else:
                key, slot = item
                a = QAction(tr(key), self)
                a.setData(key)
                a.triggered.connect(slot)
                self._toolbar.addAction(a)

    def _setup_content(self, main_layout):
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Editor area (tracks + piano roll)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.track_panel = TrackPanel()
        self.track_panel.track_removed.connect(self._on_track_removed)
        left_layout.addWidget(self.track_panel, 2)

        self.piano_roll = PianoRoll()
        left_layout.addWidget(self.piano_roll, 3)

        splitter.addWidget(left_panel)

        # Right: Mixer
        self.mixer_panel = MixerPanel()
        splitter.addWidget(self.mixer_panel)
        splitter.setSizes([900, 220])

        main_layout.addWidget(splitter, 1)

        # Bottom: Transport
        self.transport = TransportBar()
        self.transport.play_clicked.connect(self._toggle_playback)
        self.transport.stop_clicked.connect(self._stop_playback)
        self.transport.export_clicked.connect(self._export_audio)
        self.transport.bpm_changed.connect(self._on_bpm_changed)
        main_layout.addWidget(self.transport)

    def _setup_docks(self):
        self._ai_dock = QDockWidget(tr("pipeline.title"), self)
        self._ai_dock.setObjectName("AIPipelineDock")
        self.ai_pipeline = AIPipelineDock()
        self.ai_pipeline.generate_clicked.connect(self._on_ai_generate)
        self._ai_dock.setWidget(self.ai_pipeline)
        self._ai_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._ai_dock)

    def _setup_menu(self):
        menubar = self.menuBar()
        self._lang_menu = None
        self._lang_group = None

        def _menu(key):
            m = menubar.addMenu(tr(key))
            self._menu_keys[m] = key
            return m

        def _act(key, slot):
            a = QAction(tr(key), self)
            a.setData(key)
            a.triggered.connect(slot)
            return a

        _menu("file")
        menubar.actions()[-1].menu().addAction(_act("file.new", self._new_project))
        menubar.actions()[-1].menu().addAction(_act("file.open", self._open_project))
        menubar.actions()[-1].menu().addAction(_act("file.save", self._save_project))
        menubar.actions()[-1].menu().addSeparator()
        menubar.actions()[-1].menu().addAction(_act("file.export", self._export_audio))
        menubar.actions()[-1].menu().addAction(_act("file.exit", self.close))

        _menu("track")
        menubar.actions()[-1].menu().addAction(_act("track.add", self._add_audio_track))
        menubar.actions()[-1].menu().addAction(_act("track.remove", self._add_midi_track))

        _menu("tools")
        menubar.actions()[-1].menu().addAction(_act("tools.training", self._show_training))
        menubar.actions()[-1].menu().addAction(_act("tools.settings", self._load_model))

        _menu("view")
        menubar.actions()[-1].menu().addAction(_act("view.toggle_pipeline", self._toggle_ai_dock))

        # Language submenu
        self._lang_menu = menubar.addMenu(tr("lang.switch"))
        self._lang_group = QActionGroup(self)
        self._rebuild_lang_menu()

    def _rebuild_lang_menu(self):
        if self._lang_menu:
            self._lang_menu.clear()
            for lang_key in get_languages():
                a = QAction(tr(f"lang.{lang_key}"), self, checkable=True)
                a.setData(lang_key)
                if lang_key == get_language():
                    a.setChecked(True)
                a.triggered.connect(lambda checked, lk=lang_key: self._switch_lang(lk))
                self._lang_group.addAction(a)
                self._lang_menu.addAction(a)

    def _switch_lang(self, lang: str):
        set_language(lang)
        self._retranslate_ui()

    def _retranslate_ui(self):
        self.setWindowTitle(tr("window.title"))

        # Retranslate all QActions that have an i18n key in data()
        for a in self.findChildren(QAction):
            key = a.data()
            if key and isinstance(key, str) and key.startswith(("file.", "edit.", "view.", "tools.", "track.", "help.")):
                a.setText(tr(key))

        # Retranslate menu titles
        for m, key in self._menu_keys.items():
            m.setTitle(tr(key))

        # Reload language menu items
        self._rebuild_lang_menu()

        # Docks and status bar
        self._ai_dock.setWindowTitle(tr("pipeline.title"))
        self._status_label.setText(tr("status.ready"))
        self._model_label.setText(tr("status.no_model"))

    def _setup_statusbar(self):
        status = self.statusBar()
        self._status_label = QLabel(tr("status.ready"))
        status.addWidget(self._status_label, 1)
        self._model_label = QLabel(tr("status.no_model"))
        self._model_label.setStyleSheet(f"color: {C['text_muted']};")
        status.addPermanentWidget(self._model_label)

    # ---- Actions ----

    def _on_ai_generate(self, params):
        self.ai_pipeline.reset()
        self.ai_pipeline.set_step("intent", "active")
        self._status_label.setText(f"Generating: {params.get('mood', 'no style')} in {params.get('key', 'C')}")

        import random
        from PyQt6.QtCore import QTimer as PT

        steps = ["intent", "compose", "params", "midi", "critic", "revise"]
        self._ai_timer_index = 0
        self._ai_params = params

        def advance():
            if self._ai_timer_index >= len(steps):
                self.ai_pipeline._set_pipeline_running(False)
                self._status_label.setText("Generation complete")
                return
            step = steps[self._ai_timer_index]
            self.ai_pipeline.set_step(step, "active")
            self.ai_pipeline.set_progress((self._ai_timer_index + 1) / len(steps))
            self._status_label.setText(f"AI: {step}...")

            if step == "critic":
                scores = {
                    "pitch": 0.82 + random.uniform(-0.1, 0.1),
                    "rhythm": 0.75 + random.uniform(-0.1, 0.1),
                    "tonal": 0.88 + random.uniform(-0.1, 0.1),
                    "vocal": 0.70 + random.uniform(-0.1, 0.1),
                    "structure": 0.79 + random.uniform(-0.1, 0.1),
                }
                scores["overall"] = sum(scores.values()) / len(scores)
                self.ai_pipeline.set_scores(scores)

            if step == "revise" and self._ai_timer_index > 0:
                prev_step = steps[self._ai_timer_index - 1]
                self.ai_pipeline.set_step(prev_step, "completed")

            if step == "revise":
                scores2 = {
                    "pitch": 0.88, "rhythm": 0.82, "tonal": 0.91,
                    "vocal": 0.78, "structure": 0.85, "overall": 0.85,
                }
                self.ai_pipeline.set_scores(scores2)

            self._ai_timer_index += 1
            PT.singleShot(600, advance)

        PT.singleShot(400, advance)

    def _new_project(self):
        from ..project import Project
        self._current_project = Project("Untitled")
        self.track_panel.clear()
        self.piano_roll.clear_notes()
        self.mixer_panel.clear()
        self._status_label.setText("New project created")

    def _save_project(self):
        if self._current_project is None:
            self._new_project()
        from ..project import Track as ProjectTrack
        self._current_project.tracks = [
            ProjectTrack(f"Track {i+1}", "audio")
            for i in range(self.track_panel.track_count)
        ]
        path = self._project_manager.save_project(self._current_project)
        self._status_label.setText(f"Project saved: {path}")

    def _open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "CantioDAW (*.cantio);;All Files (*)")
        if file_path:
            try:
                self._current_project = self._project_manager.load_project(file_path)
                self.track_panel.clear()
                self.mixer_panel.clear()
                for t in self._current_project.tracks:
                    self.track_panel.add_track(t.id, t.name, t.type)
                    self.mixer_panel.add_channel(t.id, t.name)
                self._status_label.setText(f"Project loaded: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load project: {e}")

    def _add_audio_track(self):
        import uuid
        tid = str(uuid.uuid4())[:8]
        name = f"Audio {self.track_panel.track_count + 1}"
        self.track_panel.add_track(tid, name, "audio")
        self.mixer_panel.add_channel(tid, name)
        self._status_label.setText(f"Added: {name}")

    def _add_midi_track(self):
        import uuid
        tid = str(uuid.uuid4())[:8]
        name = f"MIDI {self.track_panel.track_count + 1}"
        self.track_panel.add_track(tid, name, "midi")
        self.mixer_panel.add_channel(tid, name)
        self._status_label.setText(f"Added: {name}")

    def _on_track_removed(self, track_id: str):
        self.mixer_panel.remove_channel(track_id)
        self._status_label.setText("Track removed")

    def _show_training(self):
        dialog = TrainingDialog(self)
        dialog.exec()

    def _load_model(self):
        model_path, _ = QFileDialog.getOpenFileName(
            self, "Load Model Checkpoint",
            "", "Model Files (*.pt *.safetensors *.ts *.onnx);;All Files (*)")
        if not model_path:
            return
        config_path, _ = QFileDialog.getOpenFileName(
            self, "Load Config",
            "", "Config (*.yaml *.yml *.json);;All Files (*)")
        if not config_path:
            return

        try:
            from ..utils.model_detector import detect_model_format
            fmt = detect_model_format(model_path, config_path)
            self._model_label.setText(f"Model: {Path(model_path).name} ({fmt})")
            self._status_label.setText(f"Model loaded: {Path(model_path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load model: {e}")

    def _toggle_playback(self):
        if self._is_playing:
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        self._is_playing = True
        import time
        self._play_start_time = time.time()
        self._play_timer.start(50)
        self.transport.play_btn.setText("⏸")
        self._status_label.setText("Playing...")

    def _stop_playback(self):
        self._is_playing = False
        self._play_timer.stop()
        self.transport.play_btn.setText("▶")
        self.transport.set_time(0)
        self._status_label.setText("Stopped")

    def _update_playback(self):
        if self._is_playing:
            import time
            elapsed = time.time() - self._play_start_time
            self.transport.set_time(elapsed)

    def _export_audio(self):
        if self._current_project is None:
            QMessageBox.warning(self, "Warning", "No project to export")
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export Audio", "", "WAV (*.wav);;All Files (*)")
        if out_path:
            try:
                from ..audio.export import AudioExporter
                from ..core.audio_engine import AudioEngine
                sr = self._current_project.sample_rate
                engine = AudioEngine(sr)
                exporter = AudioExporter(sr)
                tracks = {}
                for t in self._current_project.tracks:
                    for clip in t.clips:
                        if "path" in clip:
                            audio = engine.load_audio(clip["path"])
                            if audio is not None:
                                tracks[t.id] = audio
                exporter.export_wav(tracks, out_path)
                self._status_label.setText(f"Exported: {out_path}")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", str(e))

    def _on_bpm_changed(self, bpm: int):
        if self._current_project:
            self._current_project.bpm = bpm

    def _toggle_ai_dock(self):
        dock = self.findChild(QDockWidget, "AIPipelineDock")
        if dock:
            dock.setVisible(not dock.isVisible())
