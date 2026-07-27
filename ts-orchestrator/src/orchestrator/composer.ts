import type { MusicIR } from '../music/ir.js';
import type { LLMRouter } from '../llm/router.js';
import { COMPOSER_SYSTEM_PROMPT } from '../llm/prompts/intent_parser.js';

export interface MIDINoteEvent {
  pitch: number;
  duration: number;
  start: number;
  velocity: number;
}

export interface ComposedSection {
  name: string;
  bars: number;
  chords: string[];
  melody: MIDINoteEvent[];
  chord_voicing?: MIDINoteEvent[];
  bass?: MIDINoteEvent[];
  texture: string;
  dynamics: string;
  instruments: string[];
}

export interface ComposedArrangement {
  title: string;
  tempo: number;
  key: string;
  timeSignature: string;
  sections: ComposedSection[];
  instrumentation: Record<string, { range: string; role: string }>;
}

export async function composeFromIR(router: LLMRouter, ir: MusicIR, model?: string): Promise<ComposedArrangement> {
  const irJson = JSON.stringify(ir, null, 2);

  const result = await router.complete({
    model: model ?? '',
    messages: [
      { role: 'system', content: COMPOSER_SYSTEM_PROMPT },
      {
        role: 'user',
        content: `根据以下 MusicIR 生成编曲方案：\n\n${irJson}`,
      },
    ],
    temperature: 0.5,
    maxTokens: 6000,
  });

  const rawText = result.choices[0]?.message?.content ?? '';
  const jsonMatch = rawText.match(/```(?:json)?\s*([\s\S]*?)```/) || rawText.match(/{[\s\S]*"sections"[\s\S]*}/);
  let jsonStr = jsonMatch?.[1] ?? rawText;

  // Try to fix truncated JSON by adding missing closing brackets
  const openBraces = (jsonStr.match(/{/g) || []).length;
  const closeBraces = (jsonStr.match(/}/g) || []).length;
  const openBrackets = (jsonStr.match(/\[/g) || []).length;
  const closeBrackets = (jsonStr.match(/\]/g) || []).length;

  jsonStr += '}'.repeat(openBraces - closeBraces);
  jsonStr += ']'.repeat(openBrackets - closeBrackets);

  try {
    return JSON.parse(jsonStr) as ComposedArrangement;
  } catch {
    // Fallback: generate a basic arrangement from IR
    const tempo = 120 + Math.round((ir.energy.peak - 0.5) * 40);
    const key = 'C';
    const chords = ['C', 'G', 'Am', 'F', 'C', 'G', 'C', 'F'];
    const basePitch = 60;

    return {
      title: 'Untitled',
      tempo,
      key,
      timeSignature: '4/4',
      sections: [
        {
          name: 'section',
          bars: 16,
          chords,
          melody: chords.map((_, i) => ({
            pitch: basePitch + (i % 4) * 2,
            duration: 2,
            start: i * 8,
            velocity: 80,
          })),
          texture: 'homophonic',
          dynamics: 'mf',
          instruments: ['piano'],
        },
      ],
      instrumentation: { piano: { range: 'C3-C6', role: 'harmonic' } },
    };
  }
}

export const CHORD_TO_PITCHES: Record<string, number[]> = {
  'C':  [48, 52, 55, 60], 'Cm': [48, 51, 55, 60],
  'D':  [50, 54, 57, 62], 'Dm': [50, 53, 57, 62],
  'E':  [52, 56, 59, 64], 'Em': [52, 55, 59, 64],
  'F':  [53, 57, 60, 65], 'Fm': [53, 56, 60, 65],
  'G':  [55, 59, 62, 67], 'Gm': [55, 58, 62, 67],
  'A':  [57, 61, 64, 69], 'Am': [57, 60, 64, 69],
  'B':  [59, 63, 66, 71], 'Bm': [59, 62, 66, 71],
  'D#': [51, 55, 58, 63], 'F#': [54, 58, 61, 66],
  'F#m':[54, 57, 61, 66], 'G#': [56, 60, 63, 68],
  'A#': [58, 62, 65, 70], 'C#': [49, 53, 56, 61],
};

export function parseChordRoot(chord: string): string {
  const m = chord.match(/^[A-G][#b]?/);
  return m ? m[0] : 'C';
}

export function generateChordVoicing(chord: string, chordDuration: number, beatOffset: number, velocity: number): MIDINoteEvent[] {
  const root = parseChordRoot(chord);
  const pitches = CHORD_TO_PITCHES[root] || CHORD_TO_PITCHES['C'];
  // Target 2 notes per beat for rich accompaniment
  const numArp = Math.max(4, Math.ceil(chordDuration * 2));
  const step = chordDuration / numArp;
  const arp: MIDINoteEvent[] = [];
  for (let i = 0; i < numArp; i++) {
    const p = pitches[i % pitches.length];
    arp.push({
      pitch: p,
      duration: step * 0.6,
      start: beatOffset + i * step,
      velocity: Math.max(40, velocity - (i % pitches.length) * 3),
    });
  }
  return arp;
}

export function generateBassPattern(chord: string, beats: number, beatOffset: number, velocity: number): MIDINoteEvent[] {
  const root = parseChordRoot(chord);
  const bassPitches: Record<string, number> = {
    'C': 36, 'D': 38, 'E': 40, 'F': 41, 'G': 43, 'A': 45, 'B': 47,
    'D#': 39, 'F#': 42, 'G#': 44, 'A#': 46, 'C#': 37,
  };
  const rootPitch = bassPitches[root] || 36;
  const fifthPitch = rootPitch + 7;
  const notes: MIDINoteEvent[] = [];
  // 2 notes per bar: root on beat 1, fifth on beat 3
  const numNotes = Math.max(2, Math.ceil(beats / 2));
  for (let i = 0; i < numNotes; i++) {
    const beatInPattern = i * (beats / numNotes);
    const isRoot = i % 2 === 0;
    notes.push({
      pitch: isRoot ? rootPitch : fifthPitch,
      duration: beats / numNotes * 0.8,
      start: beatOffset + beatInPattern,
      velocity: isRoot ? velocity : velocity - 5,
    });
  }
  return notes;
}

export function arrangementToMIDINotes(arrangement: ComposedArrangement): Array<{
  pitch: number;
  duration: number;
  start: number;
  velocity: number;
  track: string;
}> {
  const allNotes: Array<{
    pitch: number;
    duration: number;
    start: number;
    velocity: number;
    track: string;
  }> = [];

  let globalBeatOffset = 0;

  for (const section of arrangement.sections) {
    const sectionBeats = section.bars * 4;
    const numChords = section.chords.length;
    const beatsPerChord = numChords > 0 ? sectionBeats / numChords : sectionBeats;

    // Chord voicing — distribute chords evenly across section, arpeggiated
    const chordVoicingNotes: MIDINoteEvent[] = [];
    if (section.chord_voicing && section.chord_voicing.length > 0) {
      chordVoicingNotes.push(...section.chord_voicing);
    } else if (numChords > 0) {
      // Each chord gets an equal slice of the section
      for (let ci = 0; ci < numChords; ci++) {
        const chordStart = (ci / numChords) * sectionBeats;
        const chordDur = sectionBeats / numChords;
        const chordNotes = generateChordVoicing(section.chords[ci], chordDur, chordStart, 65);
        chordVoicingNotes.push(...chordNotes);
      }
    }

    for (const note of chordVoicingNotes) {
      allNotes.push({
        pitch: note.pitch,
        duration: note.duration,
        start: globalBeatOffset + note.start,
        velocity: note.velocity,
        track: `chord_${section.name}`,
      });
    }

    // Fill gaps in melody (if gap > 2 beats, add stepwise filler notes)
    const filledMelody: MIDINoteEvent[] = [];
    const sortedMelody = [...(section.melody || [])].sort((a, b) => a.start - b.start);
    for (let mi = 0; mi < sortedMelody.length; mi++) {
      filledMelody.push(sortedMelody[mi]);
      if (mi < sortedMelody.length - 1) {
        const gap = sortedMelody[mi + 1].start - (sortedMelody[mi].start + sortedMelody[mi].duration);
        if (gap > 2) {
          const fromPitch = sortedMelody[mi].pitch;
          const toPitch = sortedMelody[mi + 1].pitch;
          const steps = Math.min(Math.floor(gap / 0.5), 6);
          for (let si = 1; si <= steps; si++) {
            const t = si / (steps + 1);
            filledMelody.push({
              pitch: Math.round(fromPitch + (toPitch - fromPitch) * t),
              duration: 0.25,
              start: sortedMelody[mi].start + sortedMelody[mi].duration + t * gap,
              velocity: Math.round(sortedMelody[mi].velocity * (1 - t * 0.3)),
            });
          }
        }
      }
    }

    // Melody
    for (const note of filledMelody) {
      allNotes.push({
        pitch: note.pitch,
        duration: note.duration,
        start: globalBeatOffset + note.start,
        velocity: note.velocity,
        track: `melody_${section.name}`,
      });
    }

    // Bass — rhythmic pattern across section
    const bassNotes: MIDINoteEvent[] = [];
    if (section.bass && section.bass.length > 0) {
      bassNotes.push(...section.bass);
    } else if (numChords > 0) {
      for (let ci = 0; ci < numChords; ci++) {
        const chordStart = (ci / numChords) * sectionBeats;
        const chordBeats = sectionBeats / numChords;
        const pattern = generateBassPattern(section.chords[ci], chordBeats, chordStart, 90);
        bassNotes.push(...pattern);
      }
    }

    for (const note of bassNotes) {
      allNotes.push({
        pitch: note.pitch,
        duration: note.duration,
        start: globalBeatOffset + note.start,
        velocity: note.velocity,
        track: `bass_${section.name}`,
      });
    }

    globalBeatOffset += sectionBeats;
  }

  return allNotes;
}
