export interface MIDINoteData {
  pitch: number;
  start: number;
  duration: number;
  velocity?: number;
  lyric?: string;
  phonemes?: string;
  breathiness?: number;
  vibrato?: number;
}

export interface MIDITrack {
  channel: number;
  notes: MIDINoteData[];
  program?: number;
  name?: string;
}

export interface F0Contour {
  frameRate: number;
  totalFrames: number;
  values: number[];
  timesteps: number[];
}

export interface LyricsSegment {
  text: string;
  phonemes: string;
  start: number;
  duration: number;
}

export interface MIDIFileImport {
  filePath: string;
  tracks?: number[];
}
