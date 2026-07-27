import type { PythonBridge, PythonResult } from '../bridge/python.js';
import type {
  ProjectConfig, ExportOptions, MIDINoteData, TrainingConfig,
} from '../types/index.js';

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  handler: (bridge: PythonBridge, params: Record<string, unknown>, token?: string) => Promise<PythonResult>;
}

function ok(data: unknown): PythonResult {
  return { success: true, data };
}

function err(msg: string): PythonResult {
  return { success: false, data: null, error: msg };
}

// ──────────────────────────── Project Tools ────────────────────────────

const projectCreate: ToolDefinition = {
  name: 'project_create',
  description: '[执行] Create a new CantioDAW project',
  inputSchema: {
    type: 'object',
    properties: {
      name: { type: 'string', description: 'Project name' },
      bpm: { type: 'number', description: 'Tempo in BPM (default 120)', default: 120 },
    },
    required: ['name'],
  },
  handler: (b, p, t) => b.call('project_create', p, t),
};

const projectList: ToolDefinition = {
  name: 'project_list',
  description: '[执行] List all CantioDAW projects',
  inputSchema: { type: 'object', properties: {} },
  handler: (b, _p, _t) => b.call('project_list', _p, _t),
};

const projectLoad: ToolDefinition = {
  name: 'project_load',
  description: '[执行] Load project details',
  inputSchema: {
    type: 'object',
    properties: { name: { type: 'string' } },
    required: ['name'],
  },
  handler: (b, p, t) => b.call('project_load', p, t),
};

const projectDelete: ToolDefinition = {
  name: 'project_delete',
  description: '[执行] Delete a project',
  inputSchema: {
    type: 'object',
    properties: { name: { type: 'string' } },
    required: ['name'],
  },
  handler: async (b, p, t) => {
    await b.call('project_delete', p, t);
    return ok({ deleted: p.name });
  },
};

const projectExport: ToolDefinition = {
  name: 'project_export',
  description: '[执行] Export a project to audio files',
  inputSchema: {
    type: 'object',
    properties: {
      name: { type: 'string', description: 'Project name' },
      output: { type: 'string', description: 'Output directory or file path' },
      format: { type: 'string', enum: ['wav', 'flac'], default: 'wav' },
    },
    required: ['name'],
  },
  handler: (b, p, t) => b.call('project_export', p, t),
};

// ──────────────────────────── Track Tools ────────────────────────────

const trackAdd: ToolDefinition = {
  name: 'track_add',
  description: '[执行] Add a track to a project',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
      name: { type: 'string', description: 'Track name' },
      type: { type: 'string', enum: ['audio', 'midi'], default: 'audio' },
      color: { type: 'string', description: 'Hex color e.g. #FF0000' },
    },
    required: ['project', 'name'],
  },
  handler: (b, p, t) => b.call('track_add', p, t),
};

const trackRemove: ToolDefinition = {
  name: 'track_remove',
  description: '[执行] Remove a track from a project',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
    },
    required: ['project', 'track_id'],
  },
  handler: (b, p, t) => b.call('track_remove', p, t),
};

const trackUpdate: ToolDefinition = {
  name: 'track_update',
  description: '[执行] Update track properties (volume, mute, name)',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      name: { type: 'string' },
      volume: { type: 'number', minimum: 0, maximum: 2 },
      muted: { type: 'boolean' },
    },
    required: ['project', 'track_id'],
  },
  handler: (b, p, t) => b.call('track_update', p, t),
};

const trackAddClip: ToolDefinition = {
  name: 'track_add_clip',
  description: '[执行] Add a clip (MIDI notes, chords, or audio reference) to a track',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
      track_id: { type: 'string', description: 'Track ID to add clip to' },
      notes: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            pitch: { type: 'integer', description: 'MIDI pitch 0-127' },
            start: { type: 'number', description: 'Start time in beats' },
            duration: { type: 'number', description: 'Duration in beats' },
            velocity: { type: 'integer', description: 'Velocity 0-127', default: 80 },
          },
          required: ['pitch', 'start', 'duration'],
        },
        description: 'MIDI notes for this clip',
      },
      chords: {
        type: 'array',
        items: { type: 'string' },
        description: 'Chord names for harmony analysis (e.g. ["C", "G7", "Am"])',
      },
      path: { type: 'string', description: 'Audio file path (for audio tracks)' },
      start: { type: 'number', description: 'Clip start position in beats', default: 0 },
      duration: { type: 'number', description: 'Clip duration in beats' },
    },
    required: ['project', 'track_id'],
  },
  handler: (b, p, t) => b.call('track_add_clip', p, t),
};

// ──────────────────────────── MIDI Tools ────────────────────────────

const midiNotesToF0: ToolDefinition = {
  name: 'midi_notes_to_f0',
  description: '[执行] Convert MIDI notes to an F0 contour for synthesis',
  inputSchema: {
    type: 'object',
    properties: {
      notes: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            pitch: { type: 'integer', description: 'MIDI pitch 0-127' },
            duration: { type: 'number', description: 'Duration in seconds' },
            start: { type: 'number', description: 'Start time in seconds', default: 0 },
          },
          required: ['pitch', 'duration'],
        },
      },
      frame_rate: { type: 'integer', default: 100 },
      total_frames: { type: 'integer', default: 1000 },
    },
    required: ['notes'],
  },
  handler: (b, p, t) => b.call('midi_notes_to_f0', p, t),
};

const midiLyricsToPhonemes: ToolDefinition = {
  name: 'midi_lyrics_to_phonemes',
  description: '[执行] Convert lyrics text to phonemes for singing synthesis',
  inputSchema: {
    type: 'object',
    properties: {
      text: { type: 'string', description: 'Lyrics text to convert' },
    },
    required: ['text'],
  },
  handler: (b, p, t) => b.call('midi_lyrics_to_phonemes', p, t),
};

// ──────────────────────────── Synthesis Tools ────────────────────────────

const synthesize: ToolDefinition = {
  name: 'synthesize',
  description: '[生成] Synthesize singing voice from MIDI notes using a trained model',
  inputSchema: {
    type: 'object',
    properties: {
      model_path: { type: 'string', description: 'Path to model checkpoint' },
      config_path: { type: 'string', description: 'Path to config YAML' },
      pitch: { type: 'integer', description: 'Base MIDI pitch', default: 60 },
      duration: { type: 'number', description: 'Duration in seconds', default: 2.0 },
      midi_notes: {
        type: 'array',
        items: { type: 'object', properties: { pitch: { type: 'integer' }, duration: { type: 'number' }, start: { type: 'number' } } },
      },
      output_path: { type: 'string', description: 'Output WAV path' },
    },
    required: ['model_path', 'config_path'],
  },
  handler: (b, p, t) => b.call('synthesize', p, t),
};

// ──────────────────────────── Audio Effect Tools ────────────────────────────

const effectApply: ToolDefinition = {
  name: 'effect_apply',
  description: '[执行] Apply an audio effect (reverb, EQ, compressor) to audio data',
  inputSchema: {
    type: 'object',
    properties: {
      audio: { type: 'array', items: { type: 'number' }, description: 'Audio samples as float array' },
      sample_rate: { type: 'integer', default: 24000 },
      type: { type: 'string', enum: ['reverb', 'eq', 'compressor'] },
    },
    required: ['audio', 'type'],
  },
  handler: (b, p, t) => b.call('effect_apply', p, t),
};

const mixTracks: ToolDefinition = {
  name: 'mix_tracks',
  description: '[执行] Mix multiple tracks in a project to a single audio file. MIDI tracks are synthesized via SoundFont (if available) or oscillator fallback.',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_ids: { type: 'array', items: { type: 'string' }, description: 'Tracks to include (all if omitted)' },
      output_path: { type: 'string', default: 'mixdown.wav' },
      soundfont_path: { type: 'string', description: 'Path to .sf2 SoundFont file for MIDI track synthesis' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('mix_tracks', p, t),
};

const exportStems: ToolDefinition = {
  name: 'export_stems',
  description: '[执行] Export each track in a project as a separate audio stem',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      output_dir: { type: 'string', description: 'Output directory for stems' },
    },
    required: ['project', 'output_dir'],
  },
  handler: (b, p, t) => b.call('export_stems', p, t),
};

// ──────────────────────────── Training Tools ────────────────────────────

const trainPrepare: ToolDefinition = {
  name: 'train_prepare',
  description: '[执行] Prepare a voice dataset from a directory of audio files',
  inputSchema: {
    type: 'object',
    properties: {
      voice_name: { type: 'string', description: 'Name for the voice model' },
      data_dir: { type: 'string', description: 'Directory containing audio files' },
    },
    required: ['voice_name', 'data_dir'],
  },
  handler: (b, p, t) => b.call('train_prepare', p, t),
};

const trainStart: ToolDefinition = {
  name: 'train_start',
  description: '[执行] Start training a voice model with prepared dataset',
  inputSchema: {
    type: 'object',
    properties: {
      voice_name: { type: 'string' },
      data_dir: { type: 'string' },
      epochs: { type: 'integer', default: 10 },
      use_lora: { type: 'boolean', default: false, description: 'Use LoRA fine-tuning' },
    },
    required: ['voice_name', 'data_dir'],
  },
  handler: (b, p, t) => b.call('train_start', p, t),
};

// ──────────────────────────── Orchestration Tools ────────────────────────────

const composeSong: ToolDefinition = {
  name: 'compose_song',
  description: '[生成] End-to-end song composition: create project, add tracks, synthesize from description',
  inputSchema: {
    type: 'object',
    properties: {
      project_name: { type: 'string', description: 'Name for the new project' },
      model_path: { type: 'string', description: 'Voice model path for synthesis' },
      config_path: { type: 'string', description: 'Model config path' },
      lyrics: { type: 'string', description: 'Lyrics text' },
      bpm: { type: 'number', default: 120 },
      output_dir: { type: 'string', default: './output' },
    },
    required: ['project_name', 'model_path', 'config_path'],
  },
  handler: async (b, p, t) => {
    const name = p.project_name as string;

    const proj = await b.call('project_create', { name, bpm: p.bpm ?? 120 }, t);
    if (!proj.success) return proj;

    const trackR = await b.call('track_add', { project: name, name: 'Melody', type: 'midi', color: '#4CAF50' }, t);
    if (!trackR.success) return trackR;

    let lyrics = p.lyrics as string | undefined;
    let phonemes: string | undefined;
    if (lyrics) {
      const ph = await b.call('midi_lyrics_to_phonemes', { text: lyrics }, t);
      if (ph.success) phonemes = ph.data as string;
    }

    return ok({
      project: name,
      track: (trackR.data as { id: string }).id,
      phonemes,
      message: `Project "${name}" created. Use synthesize tool with model_path="${p.model_path}" and config_path="${p.config_path}" to generate audio.`,
    });
  },
};

const trainVoiceFromAudio: ToolDefinition = {
  name: 'train_voice_from_audio',
  description: '[执行] Complete workflow: prepare dataset and train a voice model from audio files',
  inputSchema: {
    type: 'object',
    properties: {
      voice_name: { type: 'string', description: 'Name for the voice' },
      data_dir: { type: 'string', description: 'Directory of training audio files' },
      epochs: { type: 'integer', default: 10 },
      use_lora: { type: 'boolean', default: false },
    },
    required: ['voice_name', 'data_dir'],
  },
  handler: async (b, p, t) => {
    const prep = await b.call('train_prepare', { voice_name: p.voice_name, data_dir: p.data_dir }, t);
    if (!prep.success) return prep;

    const train = await b.call('train_start', {
      voice_name: p.voice_name,
      data_dir: p.data_dir,
      epochs: p.epochs ?? 10,
      use_lora: p.use_lora ?? false,
    }, t);
    return train;
  },
};

const applyVoiceToMIDI: ToolDefinition = {
  name: 'apply_voice_to_midi',
  description: '[执行] Apply a trained voice model to MIDI notes to generate singing audio',
  inputSchema: {
    type: 'object',
    properties: {
      model_path: { type: 'string' },
      config_path: { type: 'string' },
      midi_notes: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            pitch: { type: 'integer' },
            duration: { type: 'number' },
            start: { type: 'number', default: 0 },
            lyric: { type: 'string' },
          },
          required: ['pitch', 'duration'],
        },
      },
      output_path: { type: 'string', default: 'singing_output.wav' },
    },
    required: ['model_path', 'config_path', 'midi_notes'],
  },
  handler: (b, p, t) => b.call('synthesize', p, t),
};

// ──────────────────────────── Delta Parameter Tools (Phase 5) ────────────────────────────

const adjustDynamics: ToolDefinition = {
  name: 'adjust_dynamics',
  description: '[执行] Adjust dynamics curve for a track section (delta-based)',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      section: { type: 'string' },
      curve_delta: { type: 'number', description: 'Dynamics curve delta (-1 to 1)' },
    },
    required: ['project', 'track_id', 'section', 'curve_delta'],
  },
  handler: (b, p, t) => b.call('adjust_dynamics', p, t),
};

const adjustArticulation: ToolDefinition = {
  name: 'adjust_articulation',
  description: '[执行] Adjust articulation style and overlap for a note range',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      start: { type: 'number' },
      end: { type: 'number' },
      style: { type: 'string', enum: ['legato', 'staccato', 'portato', 'normal'] },
      overlap_delta: { type: 'number', description: 'Overlap amount delta (-1 to 1)' },
      attack_delta_ms: { type: 'number', description: 'Attack time delta in ms' },
    },
    required: ['project', 'track_id', 'start', 'end'],
  },
  handler: (b, p, t) => b.call('adjust_articulation', p, t),
};

const adjustVibrato: ToolDefinition = {
  name: 'adjust_vibrato',
  description: '[执行] Adjust vibrato depth and rate for a note range',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      start: { type: 'number' },
      end: { type: 'number' },
      depth_delta: { type: 'number', description: 'Vibrato depth delta (-1 to 1)' },
      rate_delta: { type: 'number', description: 'Vibrato rate delta in Hz' },
    },
    required: ['project', 'track_id', 'start', 'end'],
  },
  handler: (b, p, t) => b.call('adjust_vibrato', p, t),
};

const adjustMicroTiming: ToolDefinition = {
  name: 'adjust_micro_timing',
  description: '[执行] Adjust micro-timing offsets for individual notes',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      adjustments: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            note_index: { type: 'integer' },
            offset_delta_ms: { type: 'number' },
          },
          required: ['note_index', 'offset_delta_ms'],
        },
      },
    },
    required: ['project', 'track_id', 'adjustments'],
  },
  handler: (b, p, t) => b.call('adjust_micro_timing', p, t),
};

const adjustHarmonicColor: ToolDefinition = {
  name: 'adjust_harmonic_color',
  description: '[执行] Adjust harmonic color (quality, mode) for a section',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      section: { type: 'string' },
      quality_delta: { type: 'string', description: 'Quality delta (e.g. +dominant, -minor)' },
      mode_shift: { type: 'number', description: 'Mode shift amount (-1 to 1)' },
    },
    required: ['project', 'section'],
  },
  handler: (b, p, t) => b.call('adjust_harmonic_color', p, t),
};

const applySwing: ToolDefinition = {
  name: 'apply_swing',
  description: '[执行] Apply swing feel to a track',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      ratio: { type: 'number', minimum: 0, maximum: 1, description: 'Swing ratio (0 = straight, 1 = heavy swing)' },
    },
    required: ['project', 'track_id', 'ratio'],
  },
  handler: (b, p, t) => b.call('apply_swing', p, t),
};

const applyRubato: ToolDefinition = {
  name: 'apply_rubato',
  description: '[执行] Apply tempo rubato curve to a track',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      curve: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            beat: { type: 'number' },
            tempo_factor: { type: 'number', description: 'Tempo multiplier (0.5 to 1.5)' },
          },
          required: ['beat', 'tempo_factor'],
        },
      },
    },
    required: ['project', 'track_id', 'curve'],
  },
  handler: (b, p, t) => b.call('apply_rubato', p, t),
};

// ──────────────────────────── Version / Checkpoint Tools (Phase 7) ────────────────────────────

const projectSnapshot: ToolDefinition = {
  name: 'project_snapshot',
  description: '[执行] Create a version snapshot of the current project state',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('project_snapshot', p, t),
};

const projectDiffVersions: ToolDefinition = {
  name: 'diff_versions',
  description: '[执行] Compare two project versions and show differences',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      v1: { type: 'string', description: 'First version ID' },
      v2: { type: 'string', description: 'Second version ID' },
    },
    required: ['project', 'v1', 'v2'],
  },
  handler: (b, p, t) => b.call('diff_versions', p, t),
};

const projectRollback: ToolDefinition = {
  name: 'rollback_to_version',
  description: '[执行] Rollback a project to a specific version snapshot',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      version: { type: 'string', description: 'Version ID to rollback to' },
    },
    required: ['project', 'version'],
  },
  handler: (b, p, t) => b.call('rollback_to_version', p, t),
};

const projectListVersions: ToolDefinition = {
  name: 'list_versions',
  description: '[执行] List all version snapshots for a project',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('list_versions', p, t),
};

// ──────────────────────────── Render Tools (Phase 8) ────────────────────────────

const renderPreview: ToolDefinition = {
  name: 'render_preview',
  description: '[执行] Quick preview render at low quality. Use during iterative workflow. MIDI tracks rendered via SoundFont if available.',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      output_path: { type: 'string', default: 'preview.wav' },
      soundfont_path: { type: 'string', description: 'Path to .sf2 SoundFont file for MIDI track synthesis' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('render_preview', p, t),
};

const renderFinal: ToolDefinition = {
  name: 'render_final',
  description: '[执行] Full quality final render. Use when the composition is finalized. MIDI tracks rendered via SoundFont if available.',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      output_path: { type: 'string', default: 'final.wav' },
      sample_rate: { type: 'integer', default: 44100 },
      soundfont_path: { type: 'string', description: 'Path to .sf2 SoundFont file for MIDI track synthesis' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('render_final', p, t),
};

// ──────────────────────────── Preference Tools (Phase 9) ────────────────────────────

const feedbackSubmit: ToolDefinition = {
  name: 'feedback_submit',
  description: '[执行] Submit user feedback (score 1-5) for a project version',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      version_id: { type: 'string' },
      score: { type: 'integer', minimum: 1, maximum: 5 },
      comment: { type: 'string' },
    },
    required: ['project', 'version_id', 'score'],
  },
  handler: (b, p, t) => b.call('feedback_submit', p, t),
};

const feedbackABTest: ToolDefinition = {
  name: 'feedback_ab_test',
  description: '[执行] Submit A/B test result choosing preferred version',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      version_a: { type: 'string' },
      version_b: { type: 'string' },
      preferred: { type: 'string', description: 'Preferred version ID' },
    },
    required: ['project', 'version_a', 'version_b', 'preferred'],
  },
  handler: (b, p, t) => b.call('feedback_ab_test', p, t),
};

const feedbackList: ToolDefinition = {
  name: 'list_feedback',
  description: '[执行] List all recorded feedback for a project, including scores, AB test results, average score, and adoption rate',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name (omit to list all)' },
    },
    required: [],
  },
  handler: (b, p, t) => b.call('list_feedback', p, t),
};

const trackReplay: ToolDefinition = {
  name: 'track_replay',
  description: '[执行] Record a replay event for a project version (user listened to this version)',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
      version_id: { type: 'string', description: 'Version ID being replayed' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('track_replay', p, t),
};

const trackFavorite: ToolDefinition = {
  name: 'track_favorite',
  description: '[执行] Record or toggle favorite status for a project version',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
      version_id: { type: 'string', description: 'Version ID' },
      favorited: { type: 'boolean', default: true, description: 'True to favorite, false to unfavorite' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('track_favorite', p, t),
};

// ──────────────────────────── Critic Tools (Phase 6) ────────────────────────────

const analyzeHarmony: ToolDefinition = {
  name: 'analyze_harmony',
  description: '[评价] Run harmony analysis on a project track',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      chords: { type: 'array', items: { type: 'string' }, description: 'Chord names to analyze (optional)' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('analyze_harmony', p, t),
};

const analyzeMelody: ToolDefinition = {
  name: 'analyze_melody',
  description: '[评价] Run melody analysis on a project track',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      pitches: { type: 'array', items: { type: 'integer' }, description: 'MIDI pitches to analyze (optional)' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('analyze_melody', p, t),
};

const analyzeRhythm: ToolDefinition = {
  name: 'analyze_rhythm',
  description: '[评价] Run rhythm analysis on a project track',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('analyze_rhythm', p, t),
};

const analyzeAudio: ToolDefinition = {
  name: 'analyze_audio',
  description: '[评价] Run audio quality analysis on a project track or audio file',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string' },
      track_id: { type: 'string' },
      audio_path: { type: 'string', description: 'Path to audio file (alternative to project/track_id)' },
    },
  },
  handler: (b, p, t) => b.call('analyze_audio', p, t),
};

const revisionExecute: ToolDefinition = {
  name: 'revision_execute',
  description: '[编排] Run critic→fix→re-check revision loop with convergence control. Analyzes project, applies top fixes, re-analyzes to confirm improvement. Stops when quality threshold met, no improvement, or max iterations reached.',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
      domains: { type: 'array', items: { type: 'string', enum: ['harmony', 'melody', 'rhythm', 'audio'] }, description: 'Domains to analyze and fix' },
      max_iterations: { type: 'integer', minimum: 1, maximum: 10, default: 5 },
      quality_threshold: { type: 'number', minimum: 0, maximum: 1, default: 0.8, description: 'Stop when average severity drops below this' },
      no_improvement_limit: { type: 'integer', default: 3, description: 'Stop after N consecutive rounds without improvement' },
    },
    required: ['project'],
  },
  handler: (b, p, t) => b.call('revision_execute', p, t),
};

// ──────────────────────────── Vocal Quality Tools (P0/P1) ────────────────────────────

const synthesizeMIDI: ToolDefinition = {
  name: 'synthesize_midi',
  description: '[生成] Synthesize multi-track arrangement to WAV using SoundFont real instruments (when available) or oscillator fallback (sine/triangle/sawtooth). Supports GM program/bank selection.',
  inputSchema: {
    type: 'object',
    properties: {
      notes: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            pitch: { type: 'integer' },
            duration: { type: 'number' },
            start: { type: 'number' },
            velocity: { type: 'integer', default: 80 },
            track: { type: 'string', description: 'Track type: melody, chord, or bass' },
          },
          required: ['pitch', 'duration'],
        },
      },
      tempo: { type: 'number', default: 120 },
      output_path: { type: 'string', default: 'synthesized.wav' },
      sample_rate: { type: 'integer', default: 24000 },
      soundfont_path: { type: 'string', description: 'Path to .sf2/.sf3 SoundFont file. If not specified, auto-detects from data/soundfonts/' },
      program: { type: 'integer', default: 0, description: 'GM MIDI program number (e.g. 0=Acoustic Grand Piano, 40=Violin, 48=String Ensemble). Only used with SoundFont.' },
      bank: { type: 'integer', default: 0, description: 'MIDI bank select (0=default). Only used with SoundFont.' },
    },
    required: ['notes'],
  },
  handler: (b, p, t) => b.call('synthesize_midi', p, t),
};

const listSoundfonts: ToolDefinition = {
  name: 'list_soundfonts',
  description: '[执行] List available SoundFont (.sf2/.sf3) files found in data/soundfonts/ and other search paths. Shows whether each is loaded and how many instruments it contains.',
  inputSchema: {
    type: 'object',
    properties: {},
  },
  handler: (b, p, t) => b.call('list_soundfonts', p, t),
};

const downloadSoundfont: ToolDefinition = {
  name: 'download_soundfont',
  description: '[执行] Download FluidR3_GM.sf2 SoundFont file (144 MB) to data/soundfonts/. Required for real instrument synthesis. Skips if already exists.',
  inputSchema: {
    type: 'object',
    properties: {
      url: { type: 'string', description: 'Custom download URL (optional, uses default FluidR3_GM.sf2 mirror)' },
      dest_dir: { type: 'string', description: 'Destination directory (default: data/soundfonts/)' },
      filename: { type: 'string', default: 'FluidR3_GM.sf2' },
    },
  },
  handler: (b, p, t) => b.call('download_soundfont', p, t),
};

const parameterReference: ToolDefinition = {
  name: 'parameter_reference',
  description: '[执行] Query physical parameter mappings: MIDI CC→DAW tools, instrument name→GM program, adjust_* tool parameter reference',
  inputSchema: {
    type: 'object',
    properties: {
      tool: { type: 'string', description: 'Specific tool name to query (optional, returns all if omitted)' },
      instrument: { type: 'string', description: 'Instrument name to resolve to GM program number' },
      list_instruments: { type: 'boolean', description: 'Set true to list all instrument→program mappings' },
    },
  },
  handler: (b, p, t) => b.call('parameter_reference', p, t),
};

const analyzeVocalQuality: ToolDefinition = {
  name: 'analyze_vocal_quality',
  description: '[评价] Analyze synthesized vocal quality: pitch deviation vs target MIDI, electrical/robotic artifacts, voicing breaks',
  inputSchema: {
    type: 'object',
    properties: {
      audio_path: { type: 'string', description: 'Path to synthesized audio file' },
      target_pitches: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            pitch: { type: 'integer', description: 'Target MIDI pitch' },
            duration: { type: 'number', description: 'Duration in seconds' },
            start: { type: 'number', description: 'Start time in seconds' },
          },
          required: ['pitch', 'duration'],
        },
        description: 'Target MIDI notes for pitch deviation comparison',
      },
      sample_rate: { type: 'integer', default: 44100 },
    },
    required: ['audio_path'],
  },
  handler: (b, p, t) => b.call('analyze_vocal_quality', p, t),
};

const adjustSynthesizedPitch: ToolDefinition = {
  name: 'adjust_synthesized_pitch',
  description: '[执行] Localized pitch correction on synthesized audio. Only re-renders the specified time segment.',
  inputSchema: {
    type: 'object',
    properties: {
      audio_path: { type: 'string', description: 'Path to the synthesized audio file (modified in-place unless output_path set)' },
      start: { type: 'number', description: 'Start time in seconds of the segment to correct' },
      end: { type: 'number', description: 'End time in seconds of the segment to correct' },
      correction_cents: { type: 'number', description: 'Pitch shift amount in cents (positive = up, negative = down)' },
      output_path: { type: 'string', description: 'Optional output path (defaults to overwriting audio_path)' },
    },
    required: ['audio_path', 'start', 'end', 'correction_cents'],
  },
  handler: (b, p, t) => b.call('adjust_synthesized_pitch', p, t),
};

// ──────────────────────────── Registry ────────────────────────────

export const ALL_TOOLS: ToolDefinition[] = [
  // Project
  projectCreate,
  projectList,
  projectLoad,
  projectDelete,
  projectExport,
  // Track
  trackAdd,
  trackRemove,
  trackUpdate,
  trackAddClip,
  // MIDI
  midiNotesToF0,
  midiLyricsToPhonemes,
  // Synthesis
  synthesize,
  // Audio
  effectApply,
  mixTracks,
  exportStems,
  // Training
  trainPrepare,
  trainStart,
  // Orchestration
  composeSong,
  trainVoiceFromAudio,
  applyVoiceToMIDI,
  // Delta Parameters (Phase 5)
  adjustDynamics,
  adjustArticulation,
  adjustVibrato,
  adjustMicroTiming,
  adjustHarmonicColor,
  applySwing,
  applyRubato,
  // Version / Checkpoint (Phase 7)
  projectSnapshot,
  projectDiffVersions,
  projectRollback,
  projectListVersions,
  // Preview / Final (Phase 8)
  renderPreview,
  renderFinal,
  // Preference (Phase 9)
  feedbackSubmit,
  feedbackABTest,
  feedbackList,
  trackReplay,
  trackFavorite,
  // Critic (Phase 6)
  analyzeHarmony,
  analyzeMelody,
  analyzeRhythm,
  analyzeAudio,
  // Revision (Phase 8)
  revisionExecute,
  // Vocal Quality (P0/P1)
  analyzeVocalQuality,
  adjustSynthesizedPitch,
  // Synthesis (was missing from registry)
  synthesizeMIDI,
  listSoundfonts,
  downloadSoundfont,
  parameterReference,
];

export function getTool(name: string): ToolDefinition | undefined {
  return ALL_TOOLS.find((t) => t.name === name);
}
