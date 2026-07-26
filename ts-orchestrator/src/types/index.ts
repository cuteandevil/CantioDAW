export type {
  ProjectConfig, TrackClip, Track, Project, ProjectSummary, ExportOptions,
} from './project.js';
export type {
  MIDINoteData, MIDITrack, F0Contour, LyricsSegment, MIDIFileImport,
} from './midi.js';
export type {
  AudioClipInfo, EffectParams, MixerChannel, MixDownOptions,
} from './audio.js';
export type {
  TrainingConfig, TrainingStatus, DatasetInfo, DatasetSample,
} from './training.js';
export type {
  SynthesisConfig, SVSConfig, SynthesisResult, VoiceModel,
} from './synthesis.js';

// ── Music IR Types ──
export type {
  EmotionVector, EnergyCurve, StyleVector, SceneTags,
  ArrangementSpec, SectionSpec, StructurePlan, MusicIR, ParameterDelta,
} from '../music/ir.js';

// ── Critic Types ──
export type { CriticOutput, RevisionPlan } from '../orchestrator/revision.js';
