import type { WorkflowDefinition, WorkflowStepConfig } from './engine.js';

function step(id: string, name: string, tool: string, params: WorkflowStepConfig['params']): WorkflowStepConfig {
  return { id, name, tool, params };
}

// ── Compose a song from a high-level description ──
export const composeSongWorkflow: WorkflowDefinition = {
  id: 'compose_song',
  name: 'Compose Song',
  description: 'End-to-end: create project, add tracks, synthesize, and export',
  steps: [
    step('project', 'Create Project', 'project_create', (ctx) => ({
      name: ctx.project_name ?? 'NewSong',
      bpm: ctx.bpm ?? 120,
    })),
    step('melody_track', 'Add Melody Track', 'track_add', (ctx) => ({
      project: (ctx.project as { name: string })?.name ?? ctx.project_name,
      name: 'Melody',
      type: 'midi',
      color: '#4CAF50',
    })),
    step('phonemes', 'Convert Lyrics to Phonemes', 'midi_lyrics_to_phonemes', (ctx) => ({
      text: ctx.lyrics ?? 'la la la',
    })),
    step('synthesize', 'Synthesize Audio', 'synthesize', (ctx) => ({
      model_path: ctx.model_path,
      config_path: ctx.config_path,
      pitch: ctx.pitch ?? 60,
      duration: ctx.duration ?? 4.0,
      output_path: `${ctx.output_dir ?? './output'}/${ctx.project_name ?? 'song'}.wav`,
    })),
    step('export', 'Export Project', 'project_export', (ctx) => ({
      name: (ctx.project as { name: string })?.name ?? ctx.project_name,
      output: ctx.output_dir ?? './output',
    })),
  ],
};

// ── Train a voice model from audio files ──
export const trainVoiceWorkflow: WorkflowDefinition = {
  id: 'train_voice',
  name: 'Train Voice Model',
  description: 'Prepare dataset and train a voice model from audio files',
  steps: [
    step('prepare', 'Prepare Dataset', 'train_prepare', (ctx) => ({
      voice_name: ctx.voice_name,
      data_dir: ctx.data_dir,
    })),
    step('train', 'Train Model', 'train_start', (ctx) => ({
      voice_name: ctx.voice_name,
      data_dir: ctx.data_dir,
      epochs: ctx.epochs ?? 10,
      use_lora: ctx.use_lora ?? false,
    })),
  ],
};

// ── Apply a trained voice to MIDI notes ──
export const applyVoiceWorkflow: WorkflowDefinition = {
  id: 'apply_voice',
  name: 'Apply Voice to MIDI',
  description: 'Apply a trained voice model to MIDI notes and export audio',
  steps: [
    step('phonemes', 'Convert Lyrics', 'midi_lyrics_to_phonemes', (ctx) => ({
      text: ctx.lyrics ?? '',
    })),
    step('f0', 'Generate F0 Contour', 'midi_notes_to_f0', (ctx) => ({
      notes: ctx.midi_notes,
      frame_rate: 100,
      total_frames: Math.ceil((ctx.midi_notes as Array<{ start: number; duration: number }>)
        .reduce((max, n) => Math.max(max, n.start + n.duration), 0) * 100),
    })),
    step('synthesize', 'Synthesize', 'synthesize', (ctx) => ({
      model_path: ctx.model_path,
      config_path: ctx.config_path,
      midi_notes: ctx.midi_notes,
      output_path: ctx.output_path ?? 'singing.wav',
    })),
  ],
};

// ── Mix and export project stems ──
export const mixExportWorkflow: WorkflowDefinition = {
  id: 'mix_export',
  name: 'Mix and Export',
  description: 'Mix project tracks and export stems',
  steps: [
    step('mix', 'Mix Tracks', 'mix_tracks', (ctx) => ({
      project: ctx.project_name,
      output_path: `${ctx.output_dir ?? './output'}/mixdown.wav`,
    })),
    step('stems', 'Export Stems', 'export_stems', (ctx) => ({
      project: ctx.project_name,
      output_dir: `${ctx.output_dir ?? './output'}/stems`,
    })),
  ],
};

// ── Compose from Intent: NL → IR → Arrangement → MIDI ──
export const composeFromIntentWorkflow: WorkflowDefinition = {
  id: 'compose_from_intent',
  name: 'Compose from Intent',
  description: 'NL description → MusicIR → arrangement → MIDI preview (MVP Phase 1)',
  steps: [
    step('parse_intent', 'Parse Intent', 'llm_parse_intent', (ctx) => ({
      text: ctx.description ?? ctx.text ?? '',
    })),
    step('compose', 'Compose from IR', 'llm_compose_from_intent', (ctx) => ({
      ir: ctx.ir ?? (ctx.parse_intent as { ir?: unknown })?.ir,
      generate_midi: true,
    })),
  ],
};

// ── Critic & Revise: Analyze → Revise → Re-check → Preview ──
export const criticReviseWorkflow: WorkflowDefinition = {
  id: 'critic_revise',
  name: 'Critic & Revise',
  description: 'Analyze project → run critics → execute revision loop → re-check → preview (MVP Phase 2-3)',
  steps: [
    step('snapshot_before', 'Snapshot Before', 'project_snapshot', (ctx) => ({
      project: (ctx.project_name ?? ctx.project ?? '') as string,
    })),
    step('revise', 'Revision Loop', 'revision_execute', (ctx) => ({
      project: (ctx.project_name ?? ctx.project ?? '') as string,
      domains: (ctx.domains ?? ['harmony', 'melody', 'rhythm']) as string[],
    })),
    step('snapshot_after', 'Snapshot After', 'project_snapshot', (ctx) => ({
      project: (ctx.project_name ?? ctx.project ?? '') as string,
    })),
    step('preview', 'Render Preview', 'render_preview', (ctx) => ({
      project: (ctx.project_name ?? ctx.project ?? '') as string,
      output_path: `${ctx.project_name ?? 'project'}_revised.wav`,
    })),
  ],
};

// ── Full Pipeline: NL → Compose → Critic → Revise → Final ──
export const fullPipelineWorkflow: WorkflowDefinition = {
  id: 'full_pipeline',
  name: 'Full AI Pipeline',
  description: 'End-to-end: NL → IR → Compose → Critic → Revise (auto-loop) → Final render (MVP Phase 4)',
  steps: [
    step('parse_intent', 'Parse Intent', 'llm_parse_intent', (ctx) => ({
      text: (ctx.description ?? '') as string,
    })),
    step('compose', 'Compose from IR', 'llm_compose_from_intent', (ctx) => {
      const parseIntentResult = ctx.parse_intent as { ir?: unknown } | undefined;
      return {
        ir: ctx.ir ?? parseIntentResult?.ir,
        generate_midi: true,
      };
    }),
    step('snapshot_v1', 'Snapshot V1', 'project_snapshot', (ctx) => {
      const composeResult = ctx.compose as { project?: string } | undefined;
      return {
        project: (ctx.project_name ?? composeResult?.project ?? 'ai_composition') as string,
      };
    }),
    step('analyze', 'Analyze Music', 'llm_analyze_music', (ctx) => {
      const composeResult = ctx.compose as { project?: string } | undefined;
      return {
        project: (ctx.project_name ?? composeResult?.project ?? 'ai_composition') as string,
      };
    }),
    step('revise', 'Revision Loop', 'revision_execute', (ctx) => {
      const composeResult = ctx.compose as { project?: string } | undefined;
      return {
        project: (ctx.project_name ?? composeResult?.project ?? 'ai_composition') as string,
      };
    }),
    step('snapshot_v2', 'Snapshot V2', 'project_snapshot', (ctx) => {
      const composeResult = ctx.compose as { project?: string } | undefined;
      return {
        project: (ctx.project_name ?? composeResult?.project ?? 'ai_composition') as string,
      };
    }),
    step('diff', 'Diff Versions', 'diff_versions', (ctx) => {
      const composeResult = ctx.compose as { project?: string } | undefined;
      const snapshotV1 = ctx.snapshot_v1 as { version_id?: string } | undefined;
      const snapshotV2 = ctx.snapshot_v2 as { version_id?: string } | undefined;
      return {
        project: (ctx.project_name ?? composeResult?.project ?? 'ai_composition') as string,
        v1: snapshotV1?.version_id ?? '',
        v2: snapshotV2?.version_id ?? '',
      };
    }),
    step('final_render', 'Final Render', 'render_final', (ctx) => {
      const composeResult = ctx.compose as { project?: string } | undefined;
      return {
        project: (ctx.project_name ?? composeResult?.project ?? 'ai_composition') as string,
        output_path: `${ctx.project_name ?? 'ai_composition'}_final.wav`,
      };
    }),
  ],
};

export const WORKFLOWS: WorkflowDefinition[] = [
  composeSongWorkflow,
  trainVoiceWorkflow,
  applyVoiceWorkflow,
  mixExportWorkflow,
  composeFromIntentWorkflow,
  criticReviseWorkflow,
  fullPipelineWorkflow,
];

export function getWorkflow(id: string): WorkflowDefinition | undefined {
  return WORKFLOWS.find((w) => w.id === id);
}
