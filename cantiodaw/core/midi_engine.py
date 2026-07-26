import numpy as np
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MIDINote:
    pitch: int
    velocity: int = 100
    start: float = 0.0
    duration: float = 1.0
    lyric: str = ""
    phonemes: str = ""

    @property
    def frequency(self) -> float:
        return 440.0 * (2.0 ** ((self.pitch - 69) / 12.0))

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass
class MIDITrack:
    notes: List[MIDINote]
    program: int = 0
    name: str = "MIDI Track"


class MIDIEngine:
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    @staticmethod
    def pitch_to_name(pitch: int) -> str:
        octave = pitch // 12 - 1
        note = MIDIEngine.NOTE_NAMES[pitch % 12]
        return f"{note}{octave}"

    @staticmethod
    def name_to_pitch(name: str) -> int:
        name = name.strip().upper()
        note_part = name.rstrip("0123456789")
        octave_part = name[len(note_part):]
        if note_part in MIDIEngine.NOTE_NAMES:
            semitone = MIDIEngine.NOTE_NAMES.index(note_part)
        else:
            raise ValueError(f"Unknown note: {name}")
        octave = int(octave_part) + 1 if octave_part else 4
        return octave * 12 + semitone

    @staticmethod
    def frequency_to_pitch(freq: float) -> float:
        return 12 * np.log2(freq / 440.0) + 69

    def notes_to_f0(self, notes: List[MIDINote], frame_rate: float = 200,
                    total_frames: Optional[int] = None) -> np.ndarray:
        if not notes:
            return np.zeros(total_frames or 0, dtype=np.float32)
        if total_frames is None:
            max_end = max(n.end for n in notes)
            total_frames = int(max_end * frame_rate) + 1

        f0 = np.zeros(total_frames, dtype=np.float32)
        for note in notes:
            start_frame = max(0, int(note.start * frame_rate))
            end_frame = min(total_frames, int(note.end * frame_rate))
            f0[start_frame:end_frame] = note.frequency
        return f0

    def create_silence(self, duration: float, sample_rate: int = 44100) -> np.ndarray:
        return np.zeros(int(sample_rate * duration), dtype=np.float32)
