import sys
import argparse
import logging
from .version import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="cantiodaw",
        description="CantioDAW - AI-Powered Singing Voice Production DAW",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--host", default="127.0.0.1", help="Web UI host")
    parser.add_argument("--port", type=int, default=8080, help="Web UI port")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING"])

    sub = parser.add_subparsers(dest="command")

    proj = sub.add_parser("project", help="Project management")
    proj.add_argument("action", choices=["create", "list", "info", "export"])
    proj.add_argument("--name", default="Untitled", help="Project name")
    proj.add_argument("--output", "-o", default=None, help="Output path for export")

    train = sub.add_parser("train", help="Train a voice model")
    train.add_argument("--voice", required=True, help="Voice name")
    train.add_argument("--data-dir", required=True, help="Dataset directory")
    train.add_argument("--epochs", type=int, default=10, help="Training epochs")
    train.add_argument("--lora", action="store_true", help="Use LoRA")
    train.add_argument("--checkpoint-dir", default=None, help="Checkpoint output dir")

    synth = sub.add_parser("synthesize", help="Synthesize singing voice")
    synth.add_argument("--model", required=True, help="Model checkpoint path")
    synth.add_argument("--config", required=True, help="Config YAML path")
    synth.add_argument("--midi", default=None, help="MIDI file (optional)")
    synth.add_argument("--output", "-o", required=True, help="Output WAV path")
    synth.add_argument("--pitch", type=int, default=60, help="MIDI pitch")
    synth.add_argument("--duration", type=float, default=2.0, help="Note duration")

    export_p = sub.add_parser("export", help="Export project to audio")
    export_p.add_argument("--project", required=True, help="Project name")
    export_p.add_argument("--output", "-o", default=None, help="Output path")

    serve = sub.add_parser("serve", help="Start the web UI")

    gui_cmd = sub.add_parser("gui", help="Launch desktop GUI")

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command == "project":
        _handle_project(args)
    elif args.command == "train":
        _handle_train(args)
    elif args.command == "synthesize":
        _handle_synthesize(args)
    elif args.command == "export":
        _handle_export(args)
    elif args.command == "gui":
        _launch_gui(args)
    elif args.command == "serve" or args.command is None:
        from .webui.app import run as run_webui
        run_webui(host=args.host, port=args.port, debug=args.debug)
    else:
        parser.print_help()


def _handle_project(args):
    from .project import ProjectManager
    pm = ProjectManager()
    if args.action == "create":
        proj = pm.create_project(args.name)
        print(f"Created project: {proj.name}")
    elif args.action == "list":
        for p in pm.list_projects():
            print(f"  {p['name']:20s}  {p.get('tracks', 0)} tracks  {p.get('updated_at', '')[:19]}")
    elif args.action == "info":
        proj = pm.load_project(args.name)
        d = proj.to_dict()
        print(f"Project: {d['name']}")
        print(f"  BPM: {d['bpm']}  SR: {d['sample_rate']}")
        print(f"  Tracks: {len(d['tracks'])}")
        for t in d['tracks']:
            print(f"    {t['name']} ({t['type']}) - {len(t['clips'])} clips")
    elif args.action == "export":
        from .audio.export import AudioExporter
        from .core.audio_engine import AudioEngine
        proj = pm.load_project(args.name)
        engine = AudioEngine(proj.sample_rate)
        exporter = AudioExporter(proj.sample_rate)
        tracks = {}
        for t in proj.tracks:
            for clip in t.clips:
                if "path" in clip:
                    audio = engine.load_audio(clip["path"])
                    if audio is not None:
                        tracks[t.id] = audio
        out = args.output or f"{proj.name}.wav"
        exporter.export_wav(tracks, out)
        print(f"Exported to: {out}")


def _handle_train(args):
    from .training.voice_trainer import VoiceTrainer, TrainingConfig
    cfg = TrainingConfig(
        voice_name=args.voice,
        epochs=args.epochs,
        lora_enabled=args.lora,
    )
    ckpt_dir = args.checkpoint_dir or f"checkpoints/{args.voice}"
    trainer = VoiceTrainer(cfg)
    result = trainer.train(args.data_dir, ckpt_dir)
    print(f"Training {result['status']}: best_loss={result.get('best_loss', 'N/A'):.4f}")


def _handle_synthesize(args):
    import numpy as np
    from .core.midi_engine import MIDINote
    from .synthesis.svs_engine import SVSEngine, SVSConfig
    cfg = SVSConfig(model_path=args.model, config_path=args.config)
    engine = SVSEngine(cfg)
    engine.load_model(args.model, args.config)
    notes = [MIDINote(pitch=args.pitch, duration=args.duration)]
    audio = engine.synthesize_notes(notes)
    from .core.audio_engine import AudioEngine
    ae = AudioEngine()
    ae.save_audio(args.output, audio)
    print(f"Synthesized {len(audio)} samples -> {args.output}")


def _handle_export(args):
    _handle_project(args)


def _launch_gui(args):
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("PyQt6 is required for the GUI. Install with: pip install PyQt6")
        sys.exit(1)
    app = QApplication(sys.argv)
    from .gui import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
