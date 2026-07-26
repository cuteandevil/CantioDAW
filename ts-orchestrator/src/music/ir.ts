export interface EmotionVector {
  loneliness: number;
  hope: number;
  nostalgia: number;
  tension: number;
  calmness: number;
  sadness: number;
  joy: number;
  anger: number;
  fear: number;
  romance: number;
}

export function createEmotionVector(values?: Partial<EmotionVector>): EmotionVector {
  return {
    loneliness: 0, hope: 0, nostalgia: 0, tension: 0, calmness: 0,
    sadness: 0, joy: 0, anger: 0, fear: 0, romance: 0,
    ...values,
  };
}

export function addEmotionVectors(a: EmotionVector, b: EmotionVector): EmotionVector {
  const result = createEmotionVector();
  for (const k of Object.keys(result) as (keyof EmotionVector)[]) {
    result[k] = Math.max(0, Math.min(1, a[k] + b[k]));
  }
  return result;
}

export interface EnergyCurve {
  start: number;
  end: number;
  peak: number;
  valley: number;
  shape: 'linear' | 'exponential' | 'logarithmic' | 'sinusoidal';
}

export function createEnergyCurve(values?: Partial<EnergyCurve>): EnergyCurve {
  return { start: 0.5, end: 0.5, peak: 0.8, valley: 0.2, shape: 'linear', ...values };
}

export interface StyleVector {
  cinematic: number;
  electronic: number;
  orchestral: number;
  pop: number;
  ambient: number;
  rock: number;
  jazz: number;
  classical: number;
  folk: number;
  hiphop: number;
}

export function createStyleVector(values?: Partial<StyleVector>): StyleVector {
  return {
    cinematic: 0, electronic: 0, orchestral: 0, pop: 0, ambient: 0,
    rock: 0, jazz: 0, classical: 0, folk: 0, hiphop: 0,
    ...values,
  };
}

export interface SceneTags {
  tags: string[];
  primary: string;
  secondary: string[];
}

export function createSceneTags(values?: Partial<SceneTags>): SceneTags {
  return { tags: [], primary: '', secondary: [], ...values };
}

export interface ArrangementSpec {
  density: number;
  instrumentFocus: string[];
  texture: string;
}

export function createArrangementSpec(values?: Partial<ArrangementSpec>): ArrangementSpec {
  return { density: 0.5, instrumentFocus: [], texture: 'homophonic', ...values };
}

export interface SectionSpec {
  name: string;
  bars: number;
  irRef?: Partial<MusicIR>;
  energyTarget: number;
  densityTarget: number;
}

export interface StructurePlan {
  sections: SectionSpec[];
  totalBars: number;
}

export function createStructurePlan(values?: Partial<StructurePlan>): StructurePlan {
  return { sections: [], totalBars: 16, ...values };
}

export interface MusicIR {
  emotion: EmotionVector;
  energy: EnergyCurve;
  style: StyleVector;
  scene: SceneTags;
  arrangement: ArrangementSpec;
  structure: StructurePlan;
}

export function createMusicIR(values?: Partial<MusicIR>): MusicIR {
  return {
    emotion: createEmotionVector(),
    energy: createEnergyCurve(),
    style: createStyleVector(),
    scene: createSceneTags(),
    arrangement: createArrangementSpec(),
    structure: createStructurePlan(),
    ...values,
  };
}

export function mergeMusicIR(base: MusicIR, delta: MusicIR, factor = 1): MusicIR {
  const result = createMusicIR(JSON.parse(JSON.stringify(base)));
  for (const k of Object.keys(delta) as (keyof MusicIR)[]) {
    const dVal = delta[k];
    if (typeof dVal === 'object' && dVal !== null) {
      const rVal = result[k] as unknown as Record<string, unknown>;
      for (const [subK, subV] of Object.entries(dVal)) {
        if (typeof subV === 'number') {
          const old = (rVal[subK] as number) ?? 0;
          rVal[subK] = Math.max(0, Math.min(1, old + subV * factor));
        } else if (Array.isArray(subV)) {
          const oldArr = (rVal[subK] as unknown[]) ?? [];
          rVal[subK] = [...oldArr, ...subV] as unknown as number;
        }
      }
    }
  }
  return result;
}

export interface ParameterDelta {
  target: string;
  delta: number;
  domain?: string;
  bounds?: [number, number];
}
