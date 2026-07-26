"""
Simple lyrics-to-phoneme alignment for singing voice synthesis.
Provides a mapping between Chinese/English lyrics and phoneme sequences,
aligned to MIDI notes.
"""
import re
import logging
from typing import List, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

PHONEME_MAP = {
    # English
    "a": "AA", "e": "EH", "i": "IY", "o": "OW", "u": "UW",
    "ai": "AY", "ei": "EY", "oi": "OY", "ou": "AW",
    "b": "B", "d": "D", "f": "F", "g": "G", "h": "HH",
    "j": "JH", "k": "K", "l": "L", "m": "M", "n": "N",
    "p": "P", "r": "R", "s": "S", "t": "T", "v": "V",
    "w": "W", "y": "Y", "z": "Z",
    "sh": "SH", "ch": "CH", "th": "TH", "ng": "NG",
    # Chinese Pinyin initials
    "b ": "B", "p ": "P", "m ": "M", "f ": "F",
    "d ": "D", "t ": "T", "n ": "N", "l ": "L",
    "g ": "G", "k ": "K", "h ": "H",
    "j ": "J", "q ": "Q", "x ": "X",
    "zh": "ZH", "ch": "CH", "sh": "SH", "r ": "R",
    "z ": "Z", "c ": "C", "s ": "S",
    # Chinese finals
    "a": "A", "o": "O", "e": "E", "i": "I", "u": "U", "v": "V",
    "ai": "AI", "ei": "EI", "ui": "UI",
    "ao": "AO", "ou": "OU", "iu": "IU",
    "ie": "IE", "ve": "VE", "er": "ER",
    "an": "AN", "en": "EN", "in": "IN", "un": "UN",
    "ang": "ANG", "eng": "ENG", "ing": "ING", "ong": "ONG",
}

DEFAULT_PHONEMES = "AH"


class LyricsAligner:
    @staticmethod
    def to_phonemes(lyrics: str) -> List[str]:
        lyrics = lyrics.strip().lower()
        phonemes = []
        words = re.split(r"[\s,;.，；。、]+", lyrics)
        for word in words:
            if not word:
                continue
            matched = False
            for length in (4, 3, 2, 1):
                if len(word) >= length:
                    chunk = word[:length]
                    if chunk in PHONEME_MAP:
                        phonemes.append(PHONEME_MAP[chunk])
                        word = word[length:]
                        matched = True
                        break
            if not matched:
                phonemes.append(DEFAULT_PHONEMES)
        return phonemes or [DEFAULT_PHONEMES]

    @staticmethod
    def align_to_notes(lyrics: str, note_count: int) -> List[str]:
        words = re.split(r"[\s,;.，；。、]+", lyrics.strip().lower())
        words = [w for w in words if w]
        if not words:
            return [DEFAULT_PHONEMES] * note_count

        result = []
        for i in range(note_count):
            if i < len(words):
                word = words[i]
            else:
                word = words[-1]
            phonemes = LyricsAligner.to_phonemes(word)
            result.append(phonemes[0] if phonemes else DEFAULT_PHONEMES)
        return result

    @staticmethod
    def get_phoneme_timing(phonemes: List[str], note_durations: List[float],
                           total_duration: float) -> List[Tuple[str, float, float]]:
        result = []
        current_time = 0.0
        for i, ph in enumerate(phonemes):
            dur = note_durations[i] if i < len(note_durations) else total_duration / max(len(phonemes), 1)
            result.append((ph, current_time, current_time + dur))
            current_time += dur
        return result
