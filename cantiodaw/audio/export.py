import numpy as np
import logging
from pathlib import Path
from typing import Optional, List, Dict

from ..core.mixer import Mixer

logger = logging.getLogger(__name__)


class AudioExporter:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.mixer = Mixer(sample_rate)

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

    def export_stems(self, tracks: Dict[str, np.ndarray],
                     output_dir: str, prefix: str = "stem") -> List[str]:
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
