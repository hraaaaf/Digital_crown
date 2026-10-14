import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../../services/api';
import { downloadOfficialSyntheticFile, dryrunOfficialSyntheticFile } from './migrationGateway';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.clearAllMocks(); });

const expected = 'ab'.repeat(32);
function fakeDigest(value: number) {
  vi.stubGlobal('crypto', {
    subtle: { digest: vi.fn(async () => new Uint8Array(32).fill(value).buffer) },
  });
}
function fakeSQLiteBytes() {
  const bytes = new Uint8Array(200);
  new TextEncoder().encodeInto('SQLite format 3', bytes);
  return bytes.buffer;
}
function fileOf(bytes: ArrayBuffer) {
  const file = new File([bytes], 'digital-crown-synthetic-100x200.db',
                        { type: 'application/vnd.sqlite3' });
  // jsdom File lacks arrayBuffer(): supply exactly the bytes under test.
  Object.defineProperty(file, 'arrayBuffer', { value: async () => bytes });
  return file;
}
const goodResult = {
  mode: 'OFFICIAL_SYNTHETIC_SQLITE_FILE_ONLY',
  source_sha256: expected,
  source_patients: 100, source_appointments: 200,
  verified_patients: 100, verified_appointments: 200,
  verified_patient_links: 200, orphan_appointments: 0,
  cross_tenant_links: 0, after_rollback_patients: 0,
  after_rollback_appointments: 0, source_persisted: false,
  cabinet_rows_read: false, cabinet_rows_written: false,
  import_permitted: false,
};

describe('LOT05.6 file SHA checked before POST, no real uploads', () => {
  it('hashes official SQLite response without accepting arbitrary binary', async () => {
    fakeDigest(0xab);
    vi.mocked(api.get).mockResolvedValue({ data: fakeSQLiteBytes() });
    const actual = await downloadOfficialSyntheticFile();
    expect(actual.sha).toBe(expected);
    expect(actual.bytes.byteLength).toBe(200);
    expect(api.post).not.toHaveBeenCalled();
  });
  it('rejects a modified local file BEFORE any network POST', async () => {
    fakeDigest(0xcd);
    await expect(dryrunOfficialSyntheticFile(fileOf(fakeSQLiteBytes()), expected))
      .rejects.toThrow('ONLY_DOWNLOADED_SYNTHETIC_FIXTURE');
    expect(api.post).not.toHaveBeenCalled();
  });
  it('posts ONLY SHA-matching synthetic file as raw bytes, rejects bad response', async () => {
    fakeDigest(0xab);
    const bytes = fakeSQLiteBytes();
    vi.mocked(api.post).mockResolvedValueOnce({ data: goodResult });
    const result = await dryrunOfficialSyntheticFile(fileOf(bytes), expected);
    expect(result.verified_patient_links).toBe(200);
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(vi.mocked(api.post).mock.calls[0]?.[0]).toBe('/migration/synthetic-file-dryrun');
    expect(vi.mocked(api.post).mock.calls[0]?.[1]).toBeInstanceOf(ArrayBuffer);
    vi.mocked(api.post).mockResolvedValueOnce({ data: {...goodResult, import_permitted: true} });
    await expect(dryrunOfficialSyntheticFile(fileOf(bytes), expected))
      .rejects.toThrow('SYNTHETIC_FILE_RESULT_INCOHERENT');
  });
});
