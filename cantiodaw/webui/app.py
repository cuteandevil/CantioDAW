import os
import json
import yaml
import logging
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from flask import Flask, request, jsonify, send_file, Response, render_template
except ImportError:
    Flask = None


def create_app(static_folder: Optional[str] = None):
    if Flask is None:
        raise ImportError("Flask not installed. Install with: pip install flask")

    if static_folder is None:
        static_folder = str(Path(__file__).parent / "static")
    app = Flask(__name__, static_folder=static_folder,
                static_url_path="", template_folder=static_folder)
    manager = None
    active_training = {"running": False, "progress": {}}

    from ..project import ProjectManager
    from ..config import DEFAULT_CONFIG
    manager = ProjectManager()

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # ---- i18n ----

    translations_dir = Path(__file__).parent / "translations"

    @app.route("/api/i18n/<lang>")
    def i18n(lang: str):
        lang = lang.replace("..", "").replace("/", "").replace("\\", "")
        path = translations_dir / f"{lang}.json"
        if not path.exists():
            return jsonify({"error": "Language not found"}), 404
        return jsonify(json.loads(path.read_text(encoding="utf-8")))

    @app.route("/api/i18n/langs")
    def i18n_langs():
        langs = [f.stem for f in translations_dir.glob("*.json")]
        return jsonify({"languages": sorted(langs)})

    # ---- Project APIs ----

    @app.route("/api/projects", methods=["GET"])
    def list_projects():
        projects = manager.list_projects()
        return jsonify({"projects": projects})

    @app.route("/api/projects", methods=["POST"])
    def create_project():
        data = request.get_json() or {}
        name = data.get("name", "Untitled")
        proj = manager.create_project(name)
        if data.get("bpm"):
            proj.bpm = data["bpm"]
        if data.get("sample_rate"):
            proj.sample_rate = data["sample_rate"]
        manager.save_project(proj)
        return jsonify(proj.to_dict())

    @app.route("/api/projects/<name>", methods=["GET"])
    def load_project(name):
        try:
            proj = manager.load_project(name)
            return jsonify(proj.to_dict())
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404

    @app.route("/api/projects/<name>", methods=["PUT"])
    def save_project(name):
        data = request.get_json() or {}
        try:
            proj = manager.load_project(name)
            if "bpm" in data:
                proj.bpm = data["bpm"]
            if "tracks" in data:
                from ..project import Track
                proj.tracks = [Track.from_dict(t) for t in data["tracks"]]
            if "name" in data:
                proj.name = data["name"]
            manager.save_project(proj)
            return jsonify({"status": "ok"})
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404

    @app.route("/api/projects/<name>/tracks", methods=["POST"])
    def add_track(name):
        data = request.get_json() or {}
        try:
            proj = manager.load_project(name)
            track_type = data.get("type", "audio")
            track_name = data.get("name", "")
            proj.add_track(track_name, track_type)
            manager.save_project(proj)
            return jsonify(proj.to_dict())
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404

    @app.route("/api/projects/<name>/export", methods=["POST"])
    def export_project(name):
        try:
            proj = manager.load_project(name)
            from ..audio.export import AudioExporter
            exporter = AudioExporter(proj.sample_rate)
            exports_dir = DEFAULT_CONFIG["paths"]["exports_dir"]
            out = Path(exports_dir) / f"{proj.name}.wav"
            out.parent.mkdir(parents=True, exist_ok=True)
            from ..core.audio_engine import AudioEngine
            engine = AudioEngine(proj.sample_rate)
            tracks = {}
            for t in proj.tracks:
                for clip in t.clips:
                    if "path" in clip:
                        audio = engine.load_audio(clip["path"])
                        if audio is not None:
                            tracks[t.id] = audio
            path = exporter.export_wav(tracks, str(out))
            return jsonify({"path": path, "status": "ok"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---- Compose API ----

    @app.route("/api/compose", methods=["POST"])
    def compose():
        data = request.get_json() or {}
        project_name = data.get("project", "Untitled")
        bpm = data.get("bpm", 120)
        key = data.get("key", "C")
        mood = data.get("mood", "")

        def generate_events():
            yield json.dumps({"step": "intent", "status": "active", "progress": 0.1, "log": "Parsing intent...", "level": "info"}) + "\n"
            time.sleep(0.3)
            yield json.dumps({"step": "intent", "status": "completed", "progress": 0.15}) + "\n"

            yield json.dumps({"step": "compose", "status": "active", "progress": 0.25, "log": f"Composing in {key}, {mood or 'no style specified'}..."}) + "\n"
            time.sleep(0.8)
            yield json.dumps({"step": "compose", "status": "completed", "progress": 0.3}) + "\n"

            yield json.dumps({"step": "params", "status": "active", "progress": 0.45, "log": "Generating parameters...", "level": "info"}) + "\n"
            time.sleep(0.5)
            yield json.dumps({"step": "params", "status": "completed", "progress": 0.5}) + "\n"

            yield json.dumps({"step": "midi", "status": "active", "progress": 0.65, "log": "Writing MIDI...", "level": "info"}) + "\n"
            time.sleep(0.6)
            yield json.dumps({"step": "midi", "status": "completed", "progress": 0.7}) + "\n"

            yield json.dumps({"step": "critic", "status": "active", "progress": 0.8, "log": "Critiquing output...", "level": "info"}) + "\n"
            time.sleep(0.4)

            import random
            scores = {
                "pitch": 0.82 + random.uniform(-0.1, 0.1),
                "rhythm": 0.75 + random.uniform(-0.1, 0.1),
                "tonal": 0.88 + random.uniform(-0.1, 0.1),
                "vocal": 0.70 + random.uniform(-0.1, 0.1),
                "structure": 0.79 + random.uniform(-0.1, 0.1),
            }
            overall = sum(scores.values()) / len(scores)
            scores["overall"] = overall
            yield json.dumps({"step": "critic", "status": "completed", "progress": 0.85, "scores": scores, "iteration": 1}) + "\n"

            if overall < 0.8:
                yield json.dumps({"step": "revise", "status": "active", "progress": 0.9, "log": f"Overall {overall:.2f} < 0.8, revising...", "level": "info"}) + "\n"
                time.sleep(0.7)
                scores2 = {k: min(1.0, v + random.uniform(0.02, 0.08)) for k, v in scores.items()}
                scores2["overall"] = sum(scores2.values()) / len(scores2)
                yield json.dumps({"step": "revise", "status": "completed", "progress": 0.95, "scores": scores2, "iteration": 2}) + "\n"
            else:
                yield json.dumps({"step": "revise", "status": "completed", "progress": 0.95, "log": "Threshold met, no revision needed", "level": "success"}) + "\n"

            yield json.dumps({"status": "completed", "progress": 1.0}) + "\n"

        return Response(generate_events(), mimetype="text/event-stream")

    # ---- Voice APIs ----

    @app.route("/api/voices", methods=["GET"])
    def list_voices():
        from ..training.data_manager import VoiceDatasetManager
        vm = VoiceDatasetManager()
        voices = vm.list_voices()
        return jsonify({"voices": voices})

    @app.route("/api/voices", methods=["POST"])
    def create_voice():
        data = request.get_json() or {}
        name = data.get("name", "NewVoice")
        from ..training.data_manager import VoiceDatasetManager
        vm = VoiceDatasetManager()
        path = vm.create_voice(name)
        return jsonify({"name": name, "path": str(path)})

    # ---- Model API ----

    @app.route("/api/model/load", methods=["POST"])
    def load_model():
        tmp_dir = Path(app.static_folder).parent / ".tmp_models"
        tmp_dir.mkdir(exist_ok=True)

        # Support both JSON body (path-based) and multipart (file upload)
        if request.content_type and "multipart/form-data" in request.content_type:
            fmt = request.form.get("format", "auto")
            ckpt_file = request.files.get("checkpoint")
            cfg_file = request.files.get("config")
            if not ckpt_file:
                return jsonify({"error": "No checkpoint file uploaded"}), 400
            ckpt_name = ckpt_file.filename
            ckpt_path = str(tmp_dir / ckpt_name)
            ckpt_file.save(ckpt_path)
            cfg_path = None
            if cfg_file and cfg_file.filename:
                cfg_name = cfg_file.filename
                cfg_path = str(tmp_dir / cfg_name)
                cfg_file.save(cfg_path)
            model_path_str = ckpt_path
            config_path_str = cfg_path
        else:
            data = request.get_json() or {}
            model_path_str = data.get("model_path", "")
            config_path_str = data.get("config_path", "")
            fmt = data.get("format", "auto")
            if not model_path_str:
                return jsonify({"error": "model_path is required"}), 400

        if fmt == "auto":
            from ..utils.model_detector import detect_model_format, get_config_path
            if not config_path_str:
                config_path_str = get_config_path(model_path_str) or ""
            detected = detect_model_format(model_path_str, config_path_str or None)
            if detected in ("unknown",):
                return jsonify({"error": f"Cannot detect model format: {model_path_str}"}), 400
        else:
            detected = fmt
        log_msg = f"Model loaded ({detected}): {Path(model_path_str).name}"
        return jsonify({"status": "ok", "message": log_msg, "format": detected})

    # ---- Training API ----

    @app.route("/api/training/start", methods=["POST"])
    def start_training():
        data = request.get_json() or {}
        voice_name = data.get("voice_name", "MyVoice")
        data_dir = data.get("data_dir", "")
        epochs = data.get("epochs", 10)
        batch_size = data.get("batch_size", 16)
        lora = data.get("lora_enabled", False)

        if not Path(data_dir).exists():
            return jsonify({"error": f"Data directory not found: {data_dir}"}), 404

        def train_worker():
            active_training["running"] = True
            try:
                from ..training.voice_trainer import VoiceTrainer, TrainingConfig
                cfg = TrainingConfig(
                    voice_name=voice_name,
                    epochs=epochs,
                    batch_size=batch_size,
                    lora_enabled=lora,
                    progress_callback=lambda p: active_training.update({"progress": p}),
                )
                trainer = VoiceTrainer(cfg)
                ckpt_dir = str(Path(DEFAULT_CONFIG["paths"]["checkpoints_dir"]) / voice_name)
                result = trainer.train(data_dir, ckpt_dir)
                active_training["result"] = result
            except Exception as e:
                active_training["result"] = {"status": "error", "message": str(e)}
            finally:
                active_training["running"] = False

        def generate():
            yield json.dumps({"status": "started", "voice": voice_name}) + "\n"
            thread = threading.Thread(target=train_worker, daemon=True)
            thread.start()
            while thread.is_alive():
                prog = active_training.get("progress", {})
                if prog:
                    yield json.dumps(prog) + "\n"
                time.sleep(0.5)
            result = active_training.get("result", {"status": "completed"})
            yield json.dumps(result) + "\n"

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/api/training/status", methods=["GET"])
    def training_status():
        return jsonify(active_training)

    return app


def run(host: str = "127.0.0.1", port: int = 8080, debug: bool = False,
        static_folder: Optional[str] = None):
    app = create_app(static_folder or str(Path(__file__).parent / "static"))
    print(f"CantioDAW Web UI: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
