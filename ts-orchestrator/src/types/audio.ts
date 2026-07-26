export interface AudioClipInfo {
  path: string;
  duration: number;
  sampleRate: number;
  channels: number;
}

export interface EffectParams {
  type: 'reverb' | 'eq' | 'compressor' | 'delay' | 'chorus' | 'distortion' | 'normalize' | 'fade' | 'noiseGate';
  enabled?: boolean;
  mix?: number;
  [key: string]: unknown;
}

export interface MixerChannel {
  trackId: string;
  volume: number;
  pan: number;
  mute: boolean;
  solo: boolean;
  effects: EffectParams[];
}

export interface MixDownOptions {
  tracks: string[];
  outputPath: string;
  format?: 'wav' | 'flac';
  sampleRate?: number;
}
