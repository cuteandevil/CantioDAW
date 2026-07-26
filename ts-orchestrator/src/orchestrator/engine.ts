export type WorkflowStepStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface WorkflowStep {
  id: string;
  name: string;
  tool: string;
  params: Record<string, unknown>;
  status: WorkflowStepStatus;
  result?: unknown;
  error?: string;
}

export type WorkflowEventHandler = (event: WorkflowEvent) => void;

export interface WorkflowEvent {
  workflowId: string;
  type: 'step_start' | 'step_complete' | 'step_fail' | 'workflow_complete' | 'workflow_fail';
  step?: WorkflowStep;
  message: string;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStepConfig[];
}

export interface WorkflowStepConfig {
  id: string;
  name: string;
  tool: string;
  params: Record<string, unknown> | ((ctx: Record<string, unknown>) => Record<string, unknown>);
}

export class OrchestrationEngine {
  private handlers: WorkflowEventHandler[] = [];

  on(handler: WorkflowEventHandler): void {
    this.handlers.push(handler);
  }

  private emit(event: WorkflowEvent): void {
    for (const h of this.handlers) h(event);
  }

  async execute(
    workflow: WorkflowDefinition,
    executeTool: (name: string, params: Record<string, unknown>) => Promise<{ success: boolean; data?: unknown; error?: string }>,
  ): Promise<WorkflowStep[]> {
    const steps: WorkflowStep[] = workflow.steps.map((s) => ({
      id: s.id,
      name: s.name,
      tool: s.tool,
      params: {},
      status: 'pending' as WorkflowStepStatus,
    }));

    const ctx: Record<string, unknown> = {};
    let failed = false;

    for (let i = 0; i < steps.length; i++) {
      if (failed) {
        steps[i].status = 'pending';
        continue;
      }

      const config = workflow.steps[i];
      const step = steps[i];

      const resolvedParams = typeof config.params === 'function'
        ? config.params(ctx)
        : { ...config.params };

      step.params = resolvedParams;
      step.status = 'running';
      this.emit({
        workflowId: workflow.id,
        type: 'step_start',
        step,
        message: `[${workflow.id}] Step ${i + 1}/${steps.length}: ${config.name}`,
      });

      try {
        const result = await executeTool(config.tool, resolvedParams);
        if (result.success) {
          step.status = 'completed';
          step.result = result.data;
          ctx[config.id] = result.data;
          this.emit({
            workflowId: workflow.id,
            type: 'step_complete',
            step,
            message: `[${workflow.id}] Step ${i + 1}/${steps.length} completed`,
          });
        } else {
          step.status = 'failed';
          step.error = result.error;
          failed = true;
          this.emit({
            workflowId: workflow.id,
            type: 'step_fail',
            step,
            message: `[${workflow.id}] Step ${i + 1}/${steps.length} failed: ${result.error}`,
          });
        }
      } catch (err: unknown) {
        step.status = 'failed';
        step.error = err instanceof Error ? err.message : String(err);
        failed = true;
        this.emit({
          workflowId: workflow.id,
          type: 'step_fail',
          step,
          message: `[${workflow.id}] Step failed: ${step.error}`,
        });
      }
    }

    this.emit({
      workflowId: workflow.id,
      type: failed ? 'workflow_fail' : 'workflow_complete',
      message: `[${workflow.id}] ${failed ? 'Failed' : 'Completed'}`,
    });

    return steps;
  }
}
