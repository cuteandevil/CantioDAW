export interface ProjectConfig {
  name: string;
  bpm?: number;
  sampleRate?: number;
  timeSignature?: [number, number];
  tags?: string[];
}

export interface TrackClip {
  path: string;
  start: number;
  duration: number;
  offset?: number;
  fadeIn?: number;
  fadeOut?: number;
  gain?: number;
}

export interface Track {
  id: string;
  name: string;
  type: 'audio' | 'midi' | 'group';
  clips: TrackClip[];
  muted: boolean;
  solo: boolean;
  volume: number;
  pan: number;
  color?: string;
}

export interface Project {
  name: string;
  path: string;
  bpm: number;
  sampleRate: number;
  timeSignature: [number, number];
  tracks: Track[];
  created: string;
  modified: string;
  tags: string[];
}

export interface ProjectSummary {
  name: string;
  path: string;
  trackCount: number;
  modified: string;
}

export interface ExportOptions {
  projectName: string;
  outputPath: string;
  format?: 'wav' | 'flac' | 'mp3';
  stem?: boolean;
  tracks?: string[];
}
