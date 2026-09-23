import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const source = fs.readFileSync(
  path.resolve(__dirname, 'PatientCompanionStorage.ts'),
  'utf8',
);

describe('PatientCompanionStorage PC-08 encrypted messaging contract', () => {
  it('writes messaging state only through the encrypted vault envelope', () => {
    expect(source).toContain('async saveMessagingState(');
    expect(source).toContain('writeValue(STATE_ID, await encryptState(next));');
    expect(source).toContain("name: 'AES-GCM'");
    expect(source).not.toContain('localStorage.setItem');
    expect(source).not.toContain('sessionStorage.setItem');
  });

  it('preserves messaging state when other wallet syncs replace canonical projections', () => {
    expect(source).toContain('snapshot.secureMessages === undefined');
    expect(source).toContain('snapshot.pendingMessages === undefined');
    expect(source).toContain('snapshot.pendingMessageReceipts === undefined');
    expect(source).toContain('snapshot.messageBeforeCursor === undefined');
    expect(source).toContain('snapshot.messageHasMore === undefined');
  });
});
