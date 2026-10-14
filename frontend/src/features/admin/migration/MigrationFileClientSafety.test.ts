import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../../services/api';
import { downloadOfficialSyntheticFile, dryrunOfficialSyntheticFile } from './migrationGateway';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));
afterEach(() => { vi.clearAllMocks(); vi.unstubAllGlobals(); });

describe('LOT05.6 never sends a changed local file', () => {
  it('rejects modified official fixture before any HTTP POST', async () => {
    vi.stubGlobal('crypto', { subtle: { digest: vi.fn(async () => new Uint8Array(32).buffer) } });
    const file = new File([new Uint8Array(1024)], 'digital-crown-synthetic-100x200.db');
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new ArrayBuffer(1024) });
    await expect(dryrunOfficialSyntheticFile(file, 'a'.repeat(64)))
      .rejects.toThrow('ONLY_DOWNLOADED_SYNTHETIC_FIXTURE');
    expect(api.post).not.toHaveBeenCalled();
  });
  it('rejects extension and size before reading selected bytes', async () => {
    const file = new File(['x'], 'legacy.sqlite');
    await expect(dryrunOfficialSyntheticFile(file, 'a'.repeat(64)))
      .rejects.toThrow('ONLY_OFFICIAL_SYNTHETIC_FILE');
    expect(api.post).not.toHaveBeenCalled();
  });
  it('refuses upload when browser does not provide WebCrypto', async () => {
    vi.stubGlobal('crypto', {});
    const file = new File([new Uint8Array(1024)], 'synthetic.db');
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new ArrayBuffer(1024) });
    await expect(dryrunOfficialSyntheticFile(file, 'a'.repeat(64)))
      .rejects.toThrow('WEBCRYPTO_REQUIRED');
    expect(api.post).not.toHaveBeenCalled();
  });
  it('rejects a downloadable fixture missing the SQLite header', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: new ArrayBuffer(1024) });
    await expect(downloadOfficialSyntheticFile())
      .rejects.toThrow('INVALID_OFFICIAL_FIXTURE');
    expect(api.post).not.toHaveBeenCalled();
  });
});
