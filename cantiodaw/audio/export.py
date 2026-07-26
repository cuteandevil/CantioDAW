import numpy as np
import logging
from pathlib import Path
from typing import Optional, List, Dict

from ..core.mixer import Mixer

logger = logging.getLogger(__name__)


class AudioExporter:
    def __init__(self, sample_rate=44100, output_dir=None):
        if isinstance(sample_rate, (int, float)):
            self.sample_rate = int(sample_rate)
        else:
            project = sample_rate
            self.sample_rate = getattr(project, 'sample_rate', 44100)
        self.project = None
        self.output_dir = output_dir
        self.mixer = Mixer(self.sample_rate)

    def export_mixdown(self, output_path: str = None) -> str:
        if output_path is None and self.output_dir:
            output_path = self.output_dir
        if not output_path:
            raise ValueError("No output path specified")
        tracks = self._gather_tracks()
        return self.export_wav(tracks, output_path)

    def _gather_tracks(self):
        tracks = {}
        if self.project is None:
            return tracks
        for t in self.project.tracks:
            audio_path = None
            for clip in t.clips:
                if isinstance(clip, dict) and clip.get("path"):
                    audio_path = clip["path"]
                    break
            if audio_path:
                import soundfile as sf
                audio, _ = sf.read(audio_path)
                tracks[t.id] = audio
        return tracks

    def export_wav(self, tracks: Dict[str, np.ndarray], output_path: str,
                   normalize: bool = True) -> str:
        import soundfile as sf
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        mixed = self.mixer.mix(tracks)
        if normalize and np.max(np.abs(mixed)) > 0:
            mixed = mixed / np.max(np.abs(mixed)) * 0.95

        sf.write(str(output_path), mixed, self.sample_rate)
        logger.info(f"Exported: {output_path}")
        return str(output_path)

    def export_stems(self, tracks=None,
                     output_dir: str = None, prefix: str = "stem") -> List[str]:
        if tracks is None:
            tracks = self._gather_tracks()
        output_dir = output_dir or self.output_dir
        if not output_dir:
            raise ValueError("No output directory specified")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for tid, audio in tracks.items():
            path = output_dir / f"{prefix}_{tid}.wav"
            import soundfile as sf
            sf.write(str(path), audio, self.sample_rate)
            paths.append(str(path))
        return paths

    def export_midi(self, project, output_path: str) -> str:
        try:
            import mido
            mid = mido.MidiFile()
            track = mido.MidiTrack()
            mid.tracks.append(track)
            track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(project.bpm)))
            for t in project.tracks:
                for clip in t.clips:
                    if "notes" in clip:
                        for note_data in clip["notes"]:
                            pitch = note_data.get("pitch", 60)
                            velocity = note_data.get("velocity", 100)
                            start = note_data.get("start", 0)
                            duration = note_data.get("duration", 1)
                            ticks_per_beat = mid.ticks_per_beat
                            beat_duration = 60.0 / project.bpm
                            start_ticks = int(start / beat_duration * ticks_per_beat)
                            dur_ticks = int(duration / beat_duration * ticks_per_beat)
                            track.append(mido.Message("note_on", note=pitch,
                                                      velocity=velocity,
                                                      time=start_ticks))
                            track.append(mido.Message("note_off", note=pitch,
                                                      velocity=0,
                                                      time=dur_ticks))
            mid.save(output_path)
            logger.info(f"MIDI exported: {output_path}")
        except ImportError:
            logger.error("mido not installed. Install with: pip install mido")
        return output_path
