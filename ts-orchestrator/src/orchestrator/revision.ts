export interface CriticOutput {
  domain: string;
  problem: string;
  severity: number;
  diagnosis: string[];
  suggestions: Array<{
    action: string;
    params: Record<string, unknown>;
  }>;
}

export interface RevisionPlan {
  priority: number;
  domain: string;
  problem: string;
  actions: Array<{
    tool: string;
    params: Record<string, unknown>;
  }>;
  expectedImprovement: number;
}

export class RevisionAgent {
  private maxIterations = 5;
  private qualityThreshold = 0.8;
  private noImprovementLimit = 3;

  prioritize(criticOutputs: CriticOutput[]): RevisionPlan[] {
    const sorted = [...criticOutputs].sort((a, b) => b.severity - a.severity);
    return sorted.map((c, i) => ({
      priority: i + 1,
      domain: c.domain,
      problem: c.problem,
      actions: c.suggestions.map((s) => ({
        tool: s.action,
        params: s.params,
      })),
      expectedImprovement: c.severity,
    }));
  }

  shouldStop(params: {
    iteration: number;
    currentScore: number;
    previousScore: number;
    noImprovementCount: number;
  }): { stop: boolean; reason: string } {
    if (params.iteration >= this.maxIterations) {
      return { stop: true, reason: `达到最大迭代次数 (${this.maxIterations})` };
    }
    if (params.currentScore >= this.qualityThreshold) {
      return { stop: true, reason: `质量达标 (${params.currentScore.toFixed(2)} >= ${this.qualityThreshold})` };
    }
    if (params.noImprovementCount >= this.noImprovementLimit) {
      return { stop: true, reason: `连续 ${this.noImprovementLimit} 轮无改善` };
    }
    return { stop: false, reason: '' };
  }
}
