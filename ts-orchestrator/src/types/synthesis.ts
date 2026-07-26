import type { MIDINoteData } from './midi.js';

export interface SynthesisConfig {
  modelPath: string;
  configPath: string;
  outputPath: string;
  pitch?: number;
  duration?: number;
  midiNotes?: MIDINoteData[];
  midiFile?: string;
  lyrics?: string;
  speakerId?: number;
  emotion?: string;
  vibrato?: number;
  breathiness?: number;
}

export interface SVSConfig {
  f0Method?: 'dio' | 'harvest' | 'crepe';
  pitchShift?: number;
  formantShift?: number;
  noiseScale?: number;
  lengthScale?: number;
  useGPU?: boolean;
}

export interface SynthesisResult {
  outputPath: string;
  duration: number;
  sampleRate: number;
  channels: number;
}

export interface VoiceModel {
  name: string;
  path: string;
  type: 'full' | 'lora';
  trainedEpochs: number;
  lossHistory: number[];
}
