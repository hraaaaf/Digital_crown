import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../services/api';
import { cephaloRepository } from './cephaloRepository';

vi.mock('../../services/api', () => ({ api: { post: vi.fn() } }));
const post = vi.mocked(api.post);
const source = { analysis_id: 7, expected_revision: 3, archive: false };

describe('P2ter PDF response evidence', () => {
  beforeEach(() => vi.resetAllMocks());

  it('accepts only a response matching the requested study and revision', async () => {
    const blob = new Blob(['%PDF synthetic'], { type: 'application/pdf' });
    post.mockResolvedValue({
      data: blob,
      headers: { 'x-cephalo-analysis-id': '7', 'x-cephalo-revision': '3' },
    });
    await expect(cephaloRepository.generatePDF(5, source)).resolves.toBe(blob);
    expect(post).toHaveBeenCalledWith('/patients/5/pdf', source, { responseType: 'blob' });
  });

  it('rejects wrong study, wrong revision and missing headers', async () => {
    for (const headers of [
      { 'x-cephalo-analysis-id': '8', 'x-cephalo-revision': '3' },
      { 'x-cephalo-analysis-id': '7', 'x-cephalo-revision': '4' },
      {},
    ]) {
      post.mockResolvedValue({ data: new Blob(['fake']), headers });
      await expect(cephaloRepository.generatePDF(5, source))
        .rejects.toThrow(/ne correspond pas/);
    }
  });

  it('rejects absent ID and unverified revision without an HTTP call', async () => {
    await expect(cephaloRepository.generatePDF(5, { ...source, analysis_id: 0 }))
      .rejects.toThrow(/révision/);
    await expect(cephaloRepository.generatePDF(5, { ...source, expected_revision: 0 }))
      .rejects.toThrow(/révision/);
    expect(post).not.toHaveBeenCalled();
  });
});
