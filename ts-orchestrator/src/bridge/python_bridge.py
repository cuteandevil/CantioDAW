"""Python daemon bridge for CantioDAW TS orchestrator."""
import sys
import json
import os
import hmac
import hashlib
import base64
import time
import traceback
from pathlib import Path

root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
sys.path.insert(0, root)
os.environ["CANTIODAW_ROOT"] = root

# Add CantioAI for training/synthesis dependencies
_cantio_ai = os.path.join(os.path.dirname(root), "CantioAI") if os.path.basename(root) == "CantioDAW" else os.path.join(root, "..", "CantioAI")
_cantio_ai = os.path.abspath(_cantio_ai)
if os.path.isdir(_cantio_ai):
    sys.path.insert(0, _cantio_ai)
    os.environ["CANTIOAI_ROOT"] = _cantio_ai

from cantiodaw import (
    __version__,
    ProjectManager,
    Project,
    MIDIEngine,
    MIDINote,
    Mixer,
    AudioExporter,
    AudioEffects,
    VoiceTrainer,
    VoiceDatasetManager,
    TrainingConfig as PyTrainingConfig,
    SVSEngine,
    SVSConfig as PySVSConfig,
    LyricsAligner,
    apply_reverb,
    apply_eq,
    apply_compressor,
)

from cantiodaw.utils import (
    detect_model_format,
    detect_model_info,
    adapt_config,
    create_adapter,
)

from cantiodaw.music.ir import MusicIR, EmotionVector, EnergyCurve, StyleVector, SceneTags, ArrangementSpec, StructurePlan, SectionSpec
from cantiodaw.music.knowledge_graph import KnowledgeGraph
from cantiodaw.music.parameter_mapper import ParameterMapper
from cantiodaw.music.labels import EMOTION_LABELS, SCENE_LABELS, STYLE_LABELS
from cantiodaw.critic.harmony import HarmonyCritic
from cantiodaw.critic.melody import MelodyCritic
from cantiodaw.critic.rhythm import RhythmCritic
from cantiodaw.critic.audio import AudioCritic, AudioAnalysis, AudioDiagnosis
from cantiodaw.critic.vocal import VocalCritic, VocalAnalysis
from cantiodaw.preference.collector import PreferenceCollector, UserFeedback, ABTestResult
from cantiodaw.project_version import VersionManager

import numpy as np

# Session auth globals
_session_key = b""
_session_id = ""

def _verify_token(token: str, expected_tool: str = "") -> bool:
    if not _session_key or not token:
        return False
    try:
        dot_idx = token.rfind(".")
        if dot_idx == -1:
            return False
        encoded = token[:dot_idx].encode("ascii")
        sig = token[dot_idx + 1:]
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(_session_key, encoded, hashlib.sha256).digest()
        ).decode("ascii").rstrip("=")
        if sig != expected_sig:
            return False
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += b"=" * padding
        payload = json.loads(base64.urlsafe_b64decode(encoded))
        if payload.get("exp", 0) < time.time():
            return False
        return True
    except Exception:
        return False

manager = ProjectManager()
version_manager = VersionManager()
preference_collector = PreferenceCollector()
knowledge_graph = KnowledgeGraph.load(str(Path(root) / "cantiodaw" / "music" / "knowledge_graph.yaml"))
mapper = ParameterMapper()


def _extract_track_data(project_name: str, track_id: str):
    """Find a track by ID in a project. Returns None if not found."""
    p = manager.load_project(project_name)
    for t in p.tracks:
        if t.id == track_id:
            return t
    return None


def _extract_track_notes(project_name: str, track_id: str) -> list:
    """Extract MIDI notes from a track's clips."""
    t = _extract_track_data(project_name, track_id)
    if t is None:
        return []
    notes = []
    for clip in t.clips:
        clip_notes = clip.get("notes", [])
        for n in clip_notes:
            notes.append({
                "pitch": n.get("pitch", 60),
                "start": n.get("start", 0.0),
                "duration": n.get("duration", 0.5),
            })
    return notes


def _extract_track_pitches(project_name: str, track_id: str) -> list:
    """Extract pitch list from a track's MIDI notes."""
    notes = _extract_track_notes(project_name, track_id)
    return [n["pitch"] for n in notes]


def _extract_track_rhythm(project_name: str, track_id: str) -> tuple:
    """Extract note_starts and note_durations from a track's MIDI notes."""
    notes = _extract_track_notes(project_name, track_id)
    starts = [n["start"] for n in notes]
    durs = [n["duration"] for n in notes]
    return starts, durs


def _extract_track_chords(project_name: str, track_id: str) -> list:
    """Extract chord name strings from a track's clips."""
    t = _extract_track_data(project_name, track_id)
    if t is None:
        return []
    chords = []
    for clip in t.clips:
        clip_chords = clip.get("chords", [])
        for c in clip_chords:
            if isinstance(c, str):
                chords.append(c)
            elif isinstance(c, dict):
                chords.append(c.get("name", ""))
    return chords


def _extract_track_audio_path(project_name: str, track_id: str):
    """Extract first audio path from a track's clips."""
    t = _extract_track_data(project_name, track_id)
    if t is None:
        return None
    for clip in t.clips:
        path = clip.get("path", "")
        if path:
            return path
    return None


def _load_audio_data(params: dict, project_name: str, track_id: str = None):
    """Load audio from params or track. Returns (audio_arr, sample_rate, stereo_width)."""
    audio_arr = params.get("audio", None)
    audio_path = params.get("audio_path", None)
    sr = params.get("sample_rate", 44100)
    if audio_path is None and audio_arr is None and track_id:
        audio_path = _extract_track_audio_path(project_name, track_id)
    if audio_path and audio_arr is None:
        import soundfile as sf
        audio_arr, sr = sf.read(audio_path)
    if audio_arr is None:
        return None, sr, 0.0
    audio_arr = np.array(audio_arr)
    stereo_width = 0.0
    if audio_arr.ndim > 1 and audio_arr.shape[1] >= 2:
        l, r = audio_arr[:, 0], audio_arr[:, 1]
        if len(l) > 1:
            corr = float(np.corrcoef(l, r)[0, 1])
            stereo_width = max(0.0, 1.0 - abs(corr))
        audio_arr = audio_arr.mean(axis=1)
    return audio_arr, sr, stereo_width


def _to_dict(obj):
    """Convert dataclass/nested object to JSON-safe dict."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: _to_dict(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    return obj

def _mix_project(project_name: str, track_ids=None, soundfont_path=None):
    """Shared helper: load project, create mixer, add audio/MIDI clips. Returns mixer or None."""
    p = manager.load_project(project_name)
    mixer = Mixer(p.sample_rate)
    for t in p.tracks:
        if track_ids is not None and t.id not in track_ids:
            continue
        if t.type == "midi":
            _add_midi_track_to_mixer(mixer, t, p, soundfont_path)
            continue
        for clip in t.clips:
            path = clip.get("path", "")
            if not path:
                continue
            mixer.add_track(path, volume=t.volume)
    if not mixer.channels:
        return None
    return mixer


def _add_midi_track_to_mixer(mixer, track, project, soundfont_path=None):
    from cantiodaw.synthesis.soundfont import SoundFontSynth
    track_program = getattr(track, "program", 0) or 0
    # Group notes by program for per-clip instrument support
    programs: dict = {}
    for clip in track.clips:
        if "notes" not in clip:
            continue
        prog = clip.get("program", track_program)
        if prog not in programs:
            programs[prog] = []
        programs[prog].extend(clip["notes"])
    if not programs:
        return
    channel_idx = 0
    for prog, notes in programs.items():
        synth = SoundFontSynth.create(
            soundfont_path=soundfont_path,
            sample_rate=mixer.sample_rate,
        )
        audio = synth.render(notes, project.bpm, prog, 0)
        tid = f"_synth_{track.id}_{prog}" if len(programs) > 1 else f"_synth_{track.id}"
        mixer.set_channel(tid, volume=getattr(track, "volume", 1.0))
        mixer.channels[tid]["audio"] = audio.astype(np.float32)
        mixer.channels[tid]["mute"] = getattr(track, "mute", False)
        channel_idx += 1

def handle(method: str, params: dict, token: str = "") -> dict:
    try:
        if method == "__init_session__":
            global _session_key, _session_id
            _session_key = base64.urlsafe_b64decode(params.get("key", ""))
            _session_id = params.get("session_id", "")
            return {"success": True, "data": {"session_id": _session_id}}

        if token and method not in ("ping", "version", "__init_session__"):
            if not _verify_token(token, method):
                return {"success": False, "data": None, "error": "Unauthorized: invalid or expired session token"}

        if method == "ping":
            return {"success": True, "data": "pong"}

        elif method == "version":
            return {"success": True, "data": __version__}

        elif method == "project_create":
            p = Project(params["name"])
            if "bpm" in params:
                p.bpm = params["bpm"]
            manager.save_project(p)
            return {"success": True, "data": {"name": p.name, "path": p.path}}

        elif method == "project_list":
            names = manager.list_projects()
            return {"success": True, "data": names}

        elif method == "project_load":
            p = manager.load_project(params["name"])
            return {"success": True, "data": {
                "name": p.name, "path": p.path, "bpm": p.bpm,
                "tracks": [{"id": t.id, "name": t.name, "type": t.type} for t in p.tracks],
            }}

        elif method == "project_delete":
            manager.delete_project(params["name"])
            return {"success": True, "data": None}

        elif method == "project_export":
            p = manager.load_project(params["name"])
            exporter = AudioExporter(p.sample_rate)
            exporter.project = p
            result = exporter.export_mixdown(str(params.get("output", "")))
            return {"success": True, "data": result}

        elif method == "track_add":
            p = manager.load_project(params["project"])
            t = p.add_track(params["name"], params.get("type", "audio"))
            if "color" in params:
                t.color = params["color"]
            manager.save_project(p)
            return {"success": True, "data": {"id": t.id, "name": t.name}}

        elif method == "track_remove":
            p = manager.load_project(params["project"])
            tid = params["track_id"]
            p.remove_track(tid)
            manager.save_project(p)
            return {"success": True, "data": {"removed": True, "track_id": tid}}

        elif method == "track_update":
            p = manager.load_project(params["project"])
            tid = params["track_id"]
            changed = []
            for t in p.tracks:
                if t.id == tid:
                    if "name" in params:
                        t.name = params["name"]
                        changed.append("name")
                    if "volume" in params:
                        t.volume = params["volume"]
                        changed.append("volume")
                    if "muted" in params:
                        t.muted = params["muted"]
                        changed.append("muted")
                    break
            manager.save_project(p)
            return {"success": True, "data": {"updated": True, "track_id": tid, "changed": changed}}

        elif method == "track_add_clip":
            p = manager.load_project(params["project"])
            for t in p.tracks:
                if t.id == params["track_id"]:
                    clip = {}
                    if "path" in params:
                        clip["path"] = params["path"]
                    if "notes" in params:
                        clip["notes"] = params["notes"]
                    if "chords" in params:
                        clip["chords"] = params["chords"]
                    if "start" in params:
                        clip["start"] = params["start"]
                    if "duration" in params:
                        clip["duration"] = params["duration"]
                    clip_id = t.add_clip(clip)
                    manager.save_project(p)
                    return {"success": True, "data": {"id": clip_id}}
            return {"success": False, "data": None, "error": f"Track {params['track_id']} not found"}

        elif method == "midi_notes_to_f0":
            notes = [MIDINote(pitch=n["pitch"], duration=n["duration"], start=n.get("start", 0))
                     for n in params["notes"]]
            f0 = MIDIEngine.notes_to_f0(notes, params.get("frame_rate", 100), params.get("total_frames", 1000))
            return {"success": True, "data": f0.tolist()}

        elif method == "midi_lyrics_to_phonemes":
            result = LyricsAligner.to_phonemes(params["text"])
            return {"success": True, "data": result}

        elif method == "detect_model":
            model_path = params["model_path"]
            config_path = params.get("config_path")
            info = detect_model_info(model_path, config_path)
            return {"success": True, "data": info}

        elif method == "adapter_info":
            model_path = params["model_path"]
            config_path = params.get("config_path")
            adapted = adapt_config(model_path, config_path)
            return {"success": True, "data": adapted}

        elif method == "synthesize":
            model_path = params["model_path"]
            config_path = params.get("config_path", "")
            midi_notes = params.get("midi_notes")
            pitch = params.get("pitch", 60)
            duration = params.get("duration", 2.0)
            bpm = params.get("bpm", 120)

            if midi_notes:
                notes = [MIDINote(
                    pitch=n.get("pitch", pitch),
                    duration=n.get("duration", duration),
                    start=n.get("start", 0),
                    velocity=n.get("velocity", 100),
                ) for n in midi_notes]
            else:
                notes = [MIDINote(pitch=pitch, duration=duration)]

            engine = SVSEngine(PySVSConfig())
            engine.load_model(model_path, config_path)
            audio = engine.synthesize_notes(notes, bpm=bpm)

            out = params.get("output_path")
            if out:
                import soundfile as sf
                sf.write(out, audio, engine.config.sample_rate)
                return {"success": True, "data": {"output_path": out, "samples": len(audio)}}
            return {"success": True, "data": {"samples": len(audio)}}

        elif method == "effect_apply":
            audio_arr = np.array(params["audio"]) if isinstance(params["audio"], list) else params["audio"]
            sr = params.get("sample_rate", 24000)
            etype = params["type"]
            if etype == "reverb":
                result = apply_reverb(audio_arr, sr)
            elif etype == "eq":
                result = apply_eq(audio_arr, sr)
            elif etype == "compressor":
                result = apply_compressor(audio_arr, sr)
            else:
                return {"success": False, "data": None, "error": f"Unknown effect: {etype}"}
            return {"success": True, "data": result.tolist()}

        elif method == "train_prepare":
            dm = VoiceDatasetManager()
            voice_name = params["voice_name"]
            data_dir = params["data_dir"]
            dm.create_voice(voice_name)
            count = 0
            total_dur = 0.0
            for f in Path(data_dir).iterdir():
                if f.suffix.lower() in (".wav", ".flac", ".mp3"):
                    sample = dm.add_sample(voice_name, str(f))
                    if sample:
                        count += 1
                        total_dur += sample.duration
            return {"success": True, "data": {
                "voice_name": voice_name,
                "sample_count": count,
                "total_duration": total_dur,
            }}

        elif method == "train_start":
            cfg = PyTrainingConfig(
                voice_name=params["voice_name"],
                epochs=params.get("epochs", 10),
                lora_enabled=params.get("use_lora", False),
            )
            trainer = VoiceTrainer(cfg)
            trainer.history["loss"] = [0.0]
            trainer.history["val_loss"] = [0.0]
            return {"success": True, "data": {
                "voice_name": cfg.voice_name,
                "epochs": cfg.epochs,
                "loss_history": trainer.history,
                "note": "Training requires actual model files and GPU.",
            }}

        elif method == "mix_tracks":
            mixer = _mix_project(params["project"], params.get("track_ids", None),
                                 params.get("soundfont_path", None))
            if mixer is None:
                return {"success": False, "data": None, "error": "No audio clips to mix"}
            out = params.get("output_path", "mixdown.wav")
            mixer.mix_down(out)
            return {"success": True, "data": {"output_path": out}}

        elif method == "export_stems":
            p = manager.load_project(params["project"])
            exporter = AudioExporter(p.sample_rate)
            exporter.project = p
            result = exporter.export_stems(output_dir=params["output_dir"])
            return {"success": True, "data": result}

        elif method == "synthesize_midi":
            notes = params.get("notes", [])
            tempo = params.get("tempo", 120)
            sr = params.get("sample_rate", 24000)
            soundfont_path = params.get("soundfont_path", None)
            program = params.get("program", params.get("instrument", 0))
            bank = params.get("bank", 0)

            from cantiodaw.synthesis.soundfont import SoundFontSynth
            synth = SoundFontSynth.create(
                soundfont_path=soundfont_path,
                sample_rate=sr,
            )
            audio = synth.render(notes, tempo, program, bank)

            out_path = params.get("output_path", "")
            if out_path:
                import soundfile as sf
                sf.write(out_path, audio.astype(np.float32), sr)
                return {"success": True, "data": {
                    "output_path": out_path,
                    "samples": len(audio),
                    "sample_rate": sr,
                    "duration": len(audio) / sr,
                    "note_count": len(notes),
                    "engine": "soundfont" if synth.available else "oscillator",
                    "soundfont_loaded": synth.soundfont_path,
                }}
            return {"success": True, "data": {
                "samples": len(audio),
                "sample_rate": sr,
                "duration": len(audio) / sr,
                "note_count": len(notes),
                "engine": "soundfont" if synth.available else "oscillator",
                "soundfont_loaded": synth.soundfont_path,
                "audio_preview": audio[:100].tolist(),
            }}
            return {"success": True, "data": {
                "samples": len(audio),
                "sample_rate": sr,
                "duration": len(audio) / sr,
                "audio_preview": audio.tolist()[:100],
            }}

        elif method == "export_midi":
            notes = sorted(params.get("notes", []), key=lambda n: n.get("start", 0))
            tempo = params.get("tempo", 120)
            output_path = params.get("output_path", "output.mid")
            track_name = params.get("track_name", "CantioDAW Composition")

            import mido
            from mido import MidiFile, MidiTrack, MetaMessage, Message

            mid = MidiFile(ticks_per_beat=480)
            track = MidiTrack()
            mid.tracks.append(track)

            track.append(MetaMessage('track_name', name=track_name, time=0))
            track.append(MetaMessage('time_signature', numerator=4, denominator=4, clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))
            track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))

            tick = mid.ticks_per_beat
            events = []
            for n in notes:
                pitch = n["pitch"]
                start_beats = n.get("start", 0)
                dur_beats = max(0.25, n.get("duration", 1))
                velocity = n.get("velocity", 80)
                start_tick = int(start_beats * tick)
                end_tick = start_tick + int(dur_beats * tick)
                events.append((start_tick, 'note_on', pitch, velocity))
                events.append((end_tick, 'note_off', pitch, 0))

            events.sort(key=lambda e: (e[0], 0 if e[1] == 'note_off' else 1))

            last_tick = 0
            for tick_pos, evtype, pitch, vel in events:
                delta = tick_pos - last_tick
                last_tick = tick_pos
                if evtype == 'note_on':
                    track.append(Message('note_on', note=pitch, velocity=vel, time=delta))
                else:
                    track.append(Message('note_off', note=pitch, velocity=0, time=delta))

            mid.save(output_path)
            return {"success": True, "data": {
                "output_path": output_path,
                "note_count": len(notes),
                "tempo": tempo,
            }}

        # ── Phase 5: Delta Parameter Tools ──
        elif method == "adjust_dynamics":
            p = manager.load_project(params["project"])
            for t in p.tracks:
                if t.id == params.get("track_id"):
                    section = params.get("section", "")
                    curve_delta = params.get("curve_delta", 0.0)
                    if "effects" not in vars(t):
                        t.effects = []
                    t.effects.append({
                        "type": "dynamics",
                        "section": section,
                        "curve_delta": curve_delta,
                    })
                    break
            manager.save_project(p)
            return {"success": True, "data": {"applied": True}}

        elif method == "adjust_articulation":
            p = manager.load_project(params["project"])
            for t in p.tracks:
                if t.id == params.get("track_id"):
                    if "effects" not in vars(t):
                        t.effects = []
                    t.effects.append({
                        "type": "articulation",
                        "start": params.get("start", 0),
                        "end": params.get("end", 0),
                        "style": params.get("style", "normal"),
                        "overlap_delta": params.get("overlap_delta", 0.0),
                        "attack_delta_ms": params.get("attack_delta_ms", 0.0),
                    })
                    break
            manager.save_project(p)
            return {"success": True, "data": {"applied": True}}

        elif method == "adjust_vibrato":
            p = manager.load_project(params["project"])
            for t in p.tracks:
                if t.id == params.get("track_id"):
                    if "effects" not in vars(t):
                        t.effects = []
                    t.effects.append({
                        "type": "vibrato",
                        "start": params.get("start", 0),
                        "end": params.get("end", 0),
                        "depth_delta": params.get("depth_delta", 0.0),
                        "rate_delta": params.get("rate_delta", 0.0),
                    })
                    break
            manager.save_project(p)
            return {"success": True, "data": {"applied": True}}

        elif method == "adjust_micro_timing":
            p = manager.load_project(params["project"])
            for t in p.tracks:
                if t.id == params.get("track_id"):
                    if "micro_timing" not in vars(t):
                        t.micro_timing = []
                    t.micro_timing.extend(params.get("adjustments", []))
                    break
            manager.save_project(p)
            return {"success": True, "data": {"applied": True, "count": len(params.get("adjustments", []))}}

        elif method == "adjust_harmonic_color":
            p = manager.load_project(params["project"])
            if not hasattr(p, 'harmonic_adjustments'):
                p.harmonic_adjustments = []
            p.harmonic_adjustments.append({
                "section": params.get("section", ""),
                "quality_delta": params.get("quality_delta", ""),
                "mode_shift": params.get("mode_shift", 0.0),
            })
            manager.save_project(p)
            return {"success": True, "data": {"applied": True}}

        elif method == "apply_swing":
            p = manager.load_project(params["project"])
            for t in p.tracks:
                if t.id == params.get("track_id"):
                    t.swing_ratio = params.get("ratio", 0.0)
                    break
            manager.save_project(p)
            return {"success": True, "data": {"applied": True}}

        elif method == "apply_rubato":
            p = manager.load_project(params["project"])
            for t in p.tracks:
                if t.id == params.get("track_id"):
                    t.rubato_curve = params.get("curve", [])
                    break
            manager.save_project(p)
            return {"success": True, "data": {"applied": True}}

        # ── Phase 7: Version / Checkpoint Tools ──
        elif method == "project_snapshot":
            p = manager.load_project(params["project"])
            vid = version_manager.snapshot(p)
            return {"success": True, "data": {"version_id": vid, "project": params["project"]}}

        elif method == "diff_versions":
            diff = version_manager.diff(params["project"], params["v1"], params["v2"])
            return {"success": True, "data": diff}

        elif method == "rollback_to_version":
            p = manager.load_project(params["project"])
            ok = version_manager.rollback(p, params["version"])
            if ok:
                manager.save_project(p)
            return {"success": True, "data": {"rolled_back": ok, "version": params["version"]}}

        elif method == "list_versions":
            versions = version_manager.list_versions(params["project"])
            return {"success": True, "data": [v.__dict__ for v in versions]}

        elif method == "request_checkpoint":
            p = manager.load_project(params["project"])
            versions = version_manager.list_versions(params["project"])
            if len(versions) >= 2:
                v_prev = versions[-2]
                diff = version_manager.diff(params["project"], v_prev.version_id, versions[-1].version_id)
            else:
                diff = {"changes": {}, "track_count_change": 0}
            msg = params.get("message", "")
            if isinstance(msg, str):
                msg = msg.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace')
            return {"success": True, "data": {
                "checkpoint": True,
                "checkpoint_type": params.get("checkpoint_type", "optional"),
                "message": msg,
                "project": params["project"],
                "track_count": len(p.tracks),
                "version_count": len(versions),
                "diff_vs_previous": diff,
            }}

        # ── Phase 8: Render Tools ──
        elif method == "render_preview":
            mixer = _mix_project(params["project"], soundfont_path=params.get("soundfont_path", None))
            if mixer is None:
                return {"success": False, "data": None, "error": "No audio clips to render"}
            out = params.get("output_path", "preview.wav")
            mixer.mix_down(out)
            return {"success": True, "data": {"output_path": out, "quality": "preview"}}

        elif method == "render_final":
            mixer = _mix_project(params["project"], soundfont_path=params.get("soundfont_path", None))
            if mixer is None:
                return {"success": False, "data": None, "error": "No audio clips to render"}
            out = params.get("output_path", "final.wav")
            sr = params.get("sample_rate", 44100)
            mixer.mix_down(out)
            return {"success": True, "data": {"output_path": out, "quality": "final", "sample_rate": sr}}

        # ── Phase 9: Preference Tools ──
        elif method == "feedback_submit":
            comment = params.get("comment", "")
            if isinstance(comment, str):
                comment = comment.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace')
            fb = UserFeedback(
                version_id=params["version_id"],
                project_id=params["project"],
                score=params["score"],
                comment=comment,
            )
            preference_collector.record_feedback(fb)
            avg = preference_collector.get_average_score(params["project"])
            return {"success": True, "data": {"recorded": True, "average_score": avg}}

        elif method == "feedback_ab_test":
            result = ABTestResult(
                session_id=f"ab_{params['project']}_{params['version_a']}_{params['version_b']}",
                version_a=params["version_a"],
                version_b=params["version_b"],
                preferred=params["preferred"],
                project_id=params["project"],
            )
            preference_collector.record_abtest(result)
            return {"success": True, "data": {"recorded": True}}

        elif method == "list_feedback":
            project_id = params.get("project", "")
            feedback_list = []
            if preference_collector.feedback_file.exists():
                with open(preference_collector.feedback_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        if not project_id or record.get("project_id") == project_id:
                            feedback_list.append(record)
            abtest_list = []
            if preference_collector.abtest_file.exists():
                with open(preference_collector.abtest_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        if not project_id or record.get("project_id") == project_id:
                            abtest_list.append(record)
            avg_score = preference_collector.get_average_score(project_id) if project_id else 0.0
            adoption_rate = preference_collector.get_adoption_rate(project_id) if project_id else 0.0

            # Enrich feedback with replay counts and favorite status
            for fb in feedback_list:
                vid = fb.get("version_id", "")
                fb["replay_count"] = preference_collector.get_replay_count(vid)
                fb["is_favorited"] = preference_collector.is_favorited(vid)

            return {"success": True, "data": {
                "project": project_id,
                "feedback_count": len(feedback_list),
                "feedback": feedback_list,
                "ab_tests": abtest_list,
                "average_score": avg_score,
                "adoption_rate": adoption_rate,
            }}

        elif method == "track_replay":
            preference_collector.record_replay(
                version_id=params.get("version_id", params.get("project", "")),
                project_id=params["project"],
            )
            return {"success": True, "data": {"recorded": True}}

        elif method == "track_favorite":
            preference_collector.record_favorite(
                version_id=params.get("version_id", params.get("project", "")),
                project_id=params["project"],
                favorited=params.get("favorited", True),
            )
            return {"success": True, "data": {"recorded": True}}

        # ── Phase 6: Critic Tools ──
        elif method == "analyze_music":
            p = manager.load_project(params["project"])
            domains = params.get("domains", ["harmony", "melody", "rhythm", "audio"])
            track_id = params.get("track_id", None)
            results = {}
            if "harmony" in domains:
                critic = HarmonyCritic()
                chords = params.get("chords", None)
                if chords is None and track_id:
                    chords = _extract_track_chords(params["project"], track_id)
                if not chords:
                    chords = []
                results["harmony"] = _to_dict(critic.analyze(chords))
            if "melody" in domains:
                critic = MelodyCritic()
                pitches = params.get("pitches", None)
                if not pitches and track_id:
                    pitches = _extract_track_pitches(params["project"], track_id)
                if not pitches:
                    pitches = []
                results["melody"] = _to_dict(critic.analyze(pitches))
            if "rhythm" in domains:
                critic = RhythmCritic()
                starts = params.get("note_starts", None)
                durs = params.get("note_durations", None)
                if (starts is None or durs is None) and track_id:
                    starts, durs = _extract_track_rhythm(params["project"], track_id)
                if not starts:
                    starts = []
                if not durs:
                    durs = []
                bpm = params.get("bpm", p.bpm)
                results["rhythm"] = _to_dict(critic.analyze(starts, durs, bpm))
            if "audio" in domains:
                critic = AudioCritic()
                audio_arr, sr, stereo_width = _load_audio_data(params, params["project"], track_id)
                if audio_arr is not None:
                    analysis = critic.analyze(audio_arr, sr)
                    analysis.stereo_width = stereo_width
                    results["audio"] = _to_dict({
                        "analysis": analysis,
                        "suggestions": critic.generate_suggestions(analysis.diagnoses),
                    })
                else:
                    results["audio"] = _to_dict(
                        AudioAnalysis(
                            diagnoses=[AudioDiagnosis("No audio data found for the given track.", 1.0)],
                        )
                    )
            return {"success": True, "data": results}

        elif method == "revision_execute":
            project_name = params["project"]
            domains = params.get("domains", ["harmony", "melody", "rhythm", "audio"])
            max_iterations = min(params.get("max_iterations", 5), 10)
            quality_threshold = params.get("quality_threshold", 0.8)
            no_improvement_limit = params.get("no_improvement_limit", 3)

            iteration_history = []
            previous_avg = 1.0
            no_improvement_count = 0

            for it in range(1, max_iterations + 1):
                analysis = handle("analyze_music", {"project": project_name, "domains": domains}, "")["data"]
                all_diagnoses = []
                for domain, result in analysis.items():
                    diags = result.get("diagnoses", [])
                    for d in diags:
                        all_diagnoses.append({
                            "domain": domain,
                            "issue": d.get("issue", d.get("problem", "")),
                            "severity": d.get("severity", 0),
                        })
                if not all_diagnoses:
                    iteration_history.append({"iteration": it, "avg_severity": 0, "status": "no issues"})
                    break

                current_avg = sum(d["severity"] for d in all_diagnoses) / len(all_diagnoses)

                if current_avg <= quality_threshold:
                    iteration_history.append({"iteration": it, "avg_severity": current_avg, "status": "quality met"})
                    break
                if current_avg >= previous_avg:
                    no_improvement_count += 1
                else:
                    no_improvement_count = 0
                if no_improvement_count >= no_improvement_limit:
                    iteration_history.append({"iteration": it, "avg_severity": current_avg, "status": "no improvement"})
                    break

                previous_avg = current_avg

                sorted_diags = sorted(all_diagnoses, key=lambda d: d["severity"], reverse=True)
                fixes = []

                # target → (tool, params_builder)
                def _build_tool_call(diag):
                    domain = diag["domain"]
                    issue = diag["issue"]
                    tools = []
                    if domain == "harmony":
                        if "dominant" in issue:
                            tools.append(("adjust_harmonic_color", {"project": project_name, "quality_delta": "+dominant"}))
                        if "解决" in issue or "resolution" in issue.lower():
                            tools.append(("adjust_harmonic_color", {"project": project_name, "quality_delta": "+resolution"}))
                        if "不协和" in issue or "dissonance" in issue.lower():
                            tools.append(("adjust_harmonic_color", {"project": project_name, "quality_delta": "-dissonance"}))
                    elif domain == "melody":
                        if "动机" in issue or "contour" in issue.lower():
                            tools.append(("adjust_articulation", {"project": project_name, "style": "varied", "overlap_delta": 0.2}))
                        if "大跳" in issue or "step" in issue.lower():
                            tools.append(("adjust_articulation", {"project": project_name, "style": "legato", "overlap_delta": 0.15}))
                        if "轮廓" in issue:
                            tools.append(("adjust_micro_timing", {"project": project_name, "adjustments": [{"start": 0, "end": 0, "offset_delta_ms": -5}]}))
                    elif domain == "rhythm":
                        if "切分" in issue or "syncopation" in issue.lower():
                            tools.append(("apply_swing", {"project": project_name, "ratio": 0.3}))
                        if "密度偏" in issue or "density" in issue.lower():
                            tools.append(("adjust_dynamics", {"project": project_name, "curve_delta": 0.2}))
                        if "稳定性" in issue or "stability" in issue.lower():
                            tools.append(("adjust_micro_timing", {"project": project_name, "adjustments": [{"start": 0, "end": 0, "offset_delta_ms": 3}]}))
                    elif domain == "audio":
                        if "动态" in issue or "dynamic" in issue.lower():
                            tools.append(("effect_apply", {"project": project_name, "effect": "compressor", "ratio": 4.0, "threshold": -20}))
                        if "亮度" in issue or "bright" in issue.lower():
                            tools.append(("effect_apply", {"project": project_name, "effect": "eq", "high_shelf_gain_db": 2}))
                        if "低频" in issue or "sub" in issue.lower() or "bass" in issue.lower():
                            tools.append(("effect_apply", {"project": project_name, "effect": "eq", "low_shelf_gain_db": -3}))
                    return tools

                for diag in sorted_diags[:3]:
                    for tool_name, tool_params in _build_tool_call(diag):
                        try:
                            r = handle(tool_name, tool_params, "")
                            fixes.append({"tool": tool_name, "success": r.get("success", False), "issue": diag["issue"]})
                        except Exception:
                            fixes.append({"tool": tool_name, "success": False})

                iteration_history.append({
                    "iteration": it,
                    "avg_severity": current_avg,
                    "diagnoses_count": len(all_diagnoses),
                    "fixes": fixes,
                })

            final = iteration_history[-1] if iteration_history else {}
            return {"success": True, "data": {
                "project": project_name,
                "iterations": iteration_history,
                "total_iterations": len(iteration_history),
                "final_severity": final.get("avg_severity", 1.0),
                "converged": "status" in final,
            }}

        elif method == "analyze_harmony":
            p = manager.load_project(params["project"])
            chords = params.get("chords", None)
            if chords is None and params.get("track_id"):
                chords = _extract_track_chords(params["project"], params["track_id"])
            if not chords:
                chords = []
            critic = HarmonyCritic()
            analysis = critic.analyze(chords)
            return {"success": True, "data": _to_dict({
                "analysis": analysis,
                "suggestions": critic.generate_suggestions(analysis.diagnoses),
            })}

        elif method == "analyze_melody":
            p = manager.load_project(params["project"])
            pitches = params.get("pitches", None)
            if not pitches and params.get("track_id"):
                pitches = _extract_track_pitches(params["project"], params["track_id"])
            if not pitches:
                pitches = []
            critic = MelodyCritic()
            analysis = critic.analyze(pitches)
            return {"success": True, "data": _to_dict({
                "analysis": analysis,
                "suggestions": critic.generate_suggestions(analysis.diagnoses),
            })}

        elif method == "analyze_rhythm":
            p = manager.load_project(params["project"])
            starts = params.get("note_starts", None)
            durs = params.get("note_durations", None)
            bpm = params.get("bpm", p.bpm)
            if (starts is None or durs is None) and params.get("track_id"):
                starts, durs = _extract_track_rhythm(params["project"], params["track_id"])
            if not starts:
                starts = []
            if not durs:
                durs = []
            critic = RhythmCritic()
            analysis = critic.analyze(starts, durs, bpm)
            return {"success": True, "data": _to_dict({
                "analysis": analysis,
                "suggestions": critic.generate_suggestions(analysis.diagnoses),
            })}

        elif method == "analyze_audio":
            critic = AudioCritic()
            audio_arr, sr, stereo_width = _load_audio_data(params, params["project"], params.get("track_id"))
            if audio_arr is not None:
                analysis = critic.analyze(audio_arr, sr)
                analysis.stereo_width = stereo_width
                return {"success": True, "data": _to_dict({
                    "analysis": analysis,
                    "suggestions": critic.generate_suggestions(analysis.diagnoses),
                })}
            return {"success": True, "data": _to_dict({
                "analysis": AudioAnalysis(),
                "suggestions": [],
            })}

        elif method == "list_soundfonts":
            from cantiodaw.synthesis.soundfont import _find_sf2_paths, SoundFontSynth
            sf2_files = _find_sf2_paths()
            found = []
            for sf2 in sf2_files:
                synth = SoundFontSynth(soundfont_path=str(sf2))
                found.append({
                    "path": str(sf2),
                    "loaded": synth.available,
                    "instruments": len(synth.list_instruments()),
                })
            return {"success": True, "data": {
                "soundfonts": found,
                "count": len(found),
                "tip": "Place .sf2 files in data/soundfonts/ or install pyfluidsynth",
            }}

        elif method == "download_soundfont":
            from cantiodaw.synthesis.sf2_download import download_soundfont
            result = download_soundfont(
                url=params.get("url", None),
                dest_dir=params.get("dest_dir", None),
                filename=params.get("filename", "FluidR3_GM.sf2"),
            )
            return {"success": True, "data": result}

        elif method == "parameter_reference":
            from cantiodaw.music.parameter_mapping import (
                PARAMETER_REFERENCE, INSTRUMENT_TO_PROGRAM, MIDI_CC_MAP,
                resolve_instrument,
            )
            tool_name = params.get("tool", "")
            instrument = params.get("instrument", "")
            result = {}
            if tool_name and tool_name in PARAMETER_REFERENCE:
                result["tool"] = {tool_name: PARAMETER_REFERENCE[tool_name]}
            elif not tool_name:
                result["tools"] = PARAMETER_REFERENCE
            if instrument:
                prog = resolve_instrument(instrument)
                result["instrument"] = {"name": instrument, "program": prog}
            elif "list_instruments" in params:
                result["instruments"] = {
                    k: v for k, v in sorted(INSTRUMENT_TO_PROGRAM.items())[:50]
                }
            result["midi_cc_map"] = {
                str(cc): info["name"] for cc, info in MIDI_CC_MAP.items()
            }
            result["reference_note"] = (
                "All adjust_* tools use delta values (relative), not absolute. "
                "Meaning: curve_delta=0.2 adds 20% more energy, NOT sets energy to 0.2."
            )
            return {"success": True, "data": result}

        elif method == "analyze_vocal_quality":
            audio_data = params.get("audio", None)
            audio_path = params.get("audio_path", None)
            target_pitches = params.get("target_pitches", None)
            sr = params.get("sample_rate", 44100)

            if audio_path and audio_data is None:
                import soundfile as sf
                audio_data, sr = sf.read(audio_path)

            critic = VocalCritic()
            if audio_data is not None:
                audio_arr = np.array(audio_data)
                if audio_arr.ndim > 1:
                    audio_arr = audio_arr.mean(axis=1)
                analysis = critic.analyze(audio_arr, sr, target_pitches)
            else:
                analysis = VocalAnalysis()
                analysis.diagnoses.append(VocalDiagnosis(
                    problem="No audio provided",
                    severity=1.0,
                    details=["Provide audio data or audio_path"],
                ))

            return {"success": True, "data": {
                "pitch_deviation_mean_cents": analysis.pitch_deviation_mean_cents,
                "pitch_deviation_max_cents": analysis.pitch_deviation_max_cents,
                "pitch_deviation_std_cents": analysis.pitch_deviation_std_cents,
                "on_pitch_ratio": analysis.on_pitch_ratio,
                "artifact_electricity": analysis.artifact_electricity,
                "artifact_breathiness": analysis.artifact_breathiness,
                "artifact_breaks": analysis.artifact_breaks,
                "score": analysis.score(),
                "diagnoses": [d.__dict__ for d in analysis.diagnoses],
                "suggestions": [s for d in analysis.diagnoses for s in critic.generate_suggestions([d])],
            }}

        elif method == "adjust_synthesized_pitch":
            audio_path = params.get("audio_path", "")
            start_sec = params.get("start", 0.0)
            end_sec = params.get("end", 0.0)
            correction_cents = params.get("correction_cents", 0)
            output_path = params.get("output_path", audio_path)

            import soundfile as sf
            audio, sr = sf.read(audio_path)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)

            start_idx = int(start_sec * sr)
            end_idx = int(end_sec * sr)
            if end_idx > len(audio):
                end_idx = len(audio)
            if start_idx >= end_idx:
                return {"success": False, "error": "Invalid time range"}

            # Pitch shift using linear resampling over the target segment
            shift_ratio = 2.0 ** (correction_cents / 1200.0)
            segment = audio[start_idx:end_idx]
            orig_len = len(segment)
            new_len = int(orig_len / shift_ratio)

            if new_len > 0 and orig_len > 0:
                shifted = np.interp(
                    np.linspace(0, orig_len - 1, new_len),
                    np.arange(orig_len),
                    segment,
                )
                # Stretch back to original length to preserve timing
                stretched = np.interp(
                    np.linspace(0, new_len - 1, orig_len),
                    np.arange(new_len),
                    shifted,
                )
                audio[start_idx:end_idx] = stretched

            sf.write(output_path, audio.astype(np.float32), sr)
            return {"success": True, "data": {
                "output_path": output_path,
                "correction_cents": correction_cents,
                "segment_start": start_sec,
                "segment_end": end_sec,
                "samples_modified": end_idx - start_idx,
            }}

        # ── Knowledge Graph Tools ──
        elif method == "knowledge_graph_query":
            concept = params.get("concept", "")
            direction = params.get("direction", "affects")
            results = knowledge_graph.query(concept, direction)
            return {"success": True, "data": {
                "concept": concept,
                "direction": direction,
                "effects": [{"target": e.target, "delta": e.delta} for e in results],
            }}

        # ── Parameter Mapping Tools ──
        elif method == "parameter_map_intent":
            ir_dict = params.get("ir", {})
            ir = MusicIR.from_dict(ir_dict)
            deltas = mapper.map_ir(ir)
            return {"success": True, "data": {
                "deltas": [d.__dict__ for d in deltas],
                "count": len(deltas),
            }}

        else:
            return {"success": False, "data": None, "error": f"Unknown method: {method}"}

    except Exception as e:
        tb = traceback.format_exc()
        return {"success": False, "data": None, "error": f"{type(e).__name__}: {e}\n{tb}"}


def main():
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("method") == "__shutdown__":
            break
        token = msg.get("token", "")
        result = handle(msg["method"], msg.get("params", {}), token)
        result["id"] = msg["id"]
        sys.stdout.write(json.dumps(result) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
