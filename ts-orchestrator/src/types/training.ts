export interface TrainingConfig {
  voiceName: string;
  dataDir: string;
  epochs: number;
  batchSize?: number;
  learningRate?: number;
  useLoRA?: boolean;
  loraRank?: number;
  checkpointDir?: string;
  validationSplit?: number;
  resumeFrom?: string;
}

export interface TrainingStatus {
  state: 'idle' | 'preparing' | 'training' | 'completed' | 'error';
  currentEpoch: number;
  totalEpochs: number;
  currentLoss?: number;
  bestLoss?: number;
  elapsedSeconds: number;
  estimatedRemaining?: number;
  checkpointPath?: string;
  error?: string;
}

export interface DatasetInfo {
  voiceName: string;
  sampleCount: number;
  totalDuration: number;
  sampleRate: number;
  samples: DatasetSample[];
}

export interface DatasetSample {
  path: string;
  duration: number;
  sampleRate: number;
  text?: string;
  speaker?: string;
}
