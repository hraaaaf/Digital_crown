import { describe, expect, it } from 'vitest';
import { canArchiveCephaloValidation, cephaloArchiveErrorMessage } from './cephaloArchiveGate';

describe('P2ter+ archive wire contract and clinical refusal', () => {
  it('accepts the exact backend valid=true contract but never is_valid or missing data', () => {
    expect(canArchiveCephaloValidation({ valid: true, fatals: [], warnings: ['synthetic warning'] })).toBe(true);
    expect(canArchiveCephaloValidation({ valid: false, fatals: [], warnings: [] })).toBe(false);
    expect(canArchiveCephaloValidation({ valid: true, fatals: ['contradiction'], warnings: [] })).toBe(false);
    expect(canArchiveCephaloValidation({ is_valid: true, fatals: [], warnings: [] } as any)).toBe(false);
    expect(canArchiveCephaloValidation(null)).toBe(false);
  });
  it('extracts a 422 clinical refusal from actual PDF blob transport', async () => {
    const detail = { message: 'Archivage refusé', fatals: ['SNA/SNB incompatibles'], warnings: [] };
    const error = { response: { status: 422, data: new Blob([JSON.stringify({ detail })], { type: 'application/json' }) } };
    expect(await cephaloArchiveErrorMessage(error)).toContain('SNA/SNB incompatibles');
  });
  it('makes 409 stale revision and 403 authorization explicit', async () => {
    expect(await cephaloArchiveErrorMessage({ response: { status: 409, data: new Blob(['invalid JSON']) } })).toContain('changé');
    expect(await cephaloArchiveErrorMessage({ response: { status: 403, data: null } })).toContain('autorisation');
  });
});
