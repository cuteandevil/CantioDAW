import { randomBytes, createHmac } from 'node:crypto';

let _sessionId = '';
let _hmacKey = Buffer.alloc(0);

export function initSession(): void {
  _sessionId = `ses_${randomBytes(12).toString('base64url')}`;
  _hmacKey = randomBytes(32);
}

export function createToken(tool: string, caps: string[] = []): string {
  const payload = {
    sub: _sessionId,
    tool,
    caps,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 300,
  };
  const encoded = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = createHmac('sha256', _hmacKey).update(encoded).digest('base64url');
  return `${encoded}.${sig}`;
}

export function verifyToken(token: string, tool?: string): Record<string, unknown> | null {
  const dotIdx = token.lastIndexOf('.');
  if (dotIdx === -1) return null;
  const encoded = token.slice(0, dotIdx);
  const sig = token.slice(dotIdx + 1);
  const expected = createHmac('sha256', _hmacKey).update(encoded).digest('base64url');
  if (sig !== expected) return null;
  const payload = JSON.parse(Buffer.from(encoded, 'base64url').toString());
  if (payload.exp * 1000 < Date.now()) return null;
  if (tool && payload.tool !== tool) return null;
  return payload;
}

export function getSessionKey(): string {
  return _hmacKey.toString('base64');
}

export function getSessionId(): string {
  return _sessionId;
}
