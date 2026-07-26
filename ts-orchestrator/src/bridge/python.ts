import { spawn, execSync, type ChildProcess } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, writeFileSync, readFileSync, unlinkSync, rmSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { tmpdir } from 'node:os';

/* c8 ignore next 3 */
const _filename: string = typeof __filename !== 'undefined' ? __filename : '';
const _dirname: string = typeof __dirname !== 'undefined' ? __dirname : dirname(_filename);

export interface PythonResult {
  success: boolean;
  data: unknown;
  error?: string;
}

export interface PythonBridgeOptions {
  pythonPath?: string;
  projectRoot?: string;
}

function findBridgeScript(): string {
  const candidates = [
    join(_dirname, 'python_bridge.py'),
    join(_dirname, '..', '..', 'src', 'bridge', 'python_bridge.py'),
  ];
  for (const p of candidates) {
    if (existsSync(p)) return p;
  }
  return candidates[0];
}

export class PythonBridge {
  private pythonPath: string;
  private projectRoot: string;
  private bridgeScript: string;
  private child: ChildProcess | null = null;
  private requestId = 0;
  private pending = new Map<string, { resolve: (v: PythonResult) => void }>();

  constructor(options: PythonBridgeOptions = {}) {
    this.pythonPath = options.pythonPath ?? 'python';
    this.projectRoot = options.projectRoot ?? resolve(_dirname, '..', '..', '..');
    this.bridgeScript = findBridgeScript();
  }

  async ensureRunning(): Promise<void> {
    if (this.child && !this.child.killed) return;
    await this.startDaemon();
  }

  private startDaemon(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.child = spawn(this.pythonPath, [this.bridgeScript, this.projectRoot], {
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
      });

      let buffer = '';
      const onData = (chunk: string) => {
        buffer += chunk;
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const msg = JSON.parse(line);
            const pending = this.pending.get(msg.id);
            if (pending) {
              pending.resolve(msg as PythonResult);
              this.pending.delete(msg.id);
            }
          } catch {
            // ignore partial lines
          }
        }
      };

      this.child.stdout?.on('data', (d: Buffer) => onData(d.toString()));
      this.child.stderr?.on('data', (d: Buffer) => {
        const line = d.toString().trim();
        if (line) console.error('[py-bridge]', line);
      });
      this.child.on('exit', (code) => {
        console.error(`[py-bridge] exited with code ${code}`);
        this.child = null;
        for (const [, p] of this.pending) {
          p.resolve({ success: false, data: null, error: 'Bridge process exited' });
        }
        this.pending.clear();
      });
      this.child.on('error', (err) => {
        reject(err);
      });

      resolve();
    });
  }

  async call(method: string, params: Record<string, unknown> = {}): Promise<PythonResult> {
    await this.ensureRunning();
    const id = `${++this.requestId}-${createHash('md5').update(method + JSON.stringify(params)).digest('hex').slice(0, 8)}`;

    return new Promise((resolve) => {
      this.pending.set(id, { resolve });
      const msg = JSON.stringify({ id, method, params }) + '\n';
      this.child?.stdin?.write(msg);

      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          resolve({ success: false, data: null, error: 'Request timed out' });
        }
      }, 120_000);
    });
  }

  async execScript(script: string): Promise<PythonResult> {
    const dir = mkdtempSync(join(tmpdir(), 'cantiodaw-ts-'));
    const filePath = join(dir, 'script.py');
    try {
      writeFileSync(filePath, script, 'utf-8');
      const stdout = execSync(`${this.pythonPath} "${filePath}"`, {
        cwd: this.projectRoot,
        encoding: 'utf-8',
        timeout: 120_000,
        windowsHide: true,
      });
      return { success: true, data: stdout.trim() };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, data: null, error: msg };
    } finally {
      try { unlinkSync(filePath); rmSync(dir, { recursive: true }); } catch { /* ignore */ }
    }
  }

  async close(): Promise<void> {
    if (this.child && !this.child.killed) {
      try {
        this.child.stdin?.write(JSON.stringify({ id: 'shutdown', method: '__shutdown__', params: {} }) + '\n');
      } catch { /* ignore */ }
      await new Promise((r) => setTimeout(r, 500));
      try { this.child.kill(); } catch { /* ignore */ }
      this.child = null;
    }
  }
}
