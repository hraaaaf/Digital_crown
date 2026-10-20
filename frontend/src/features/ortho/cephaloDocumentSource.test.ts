import { describe, expect, it, vi, beforeEach } from 'vitest';
import { prepareBoundCephaloDocumentSource } from './cephaloDocumentSource';
import { cephaloRepository } from './cephaloRepository';

vi.mock('./cephaloRepository', () => ({
  cephaloRepository: { getAnalysis: vi.fn() },
}));

const getAnalysis = vi.mocked(cephaloRepository.getAnalysis);

describe('P2ter study-bound document source', () => {
  beforeEach(() => { vi.resetAllMocks(); });

  it('persists and reads exactly the selected historical study revision', async () => {
    const save = vi.fn(async () => {});
    getAnalysis.mockResolvedValue({
      id: 15, angles_data: { scientific_read_path: { revision: 2 } },
    });
    const chosen = await prepareBoundCephaloDocumentSource(3, 15, () => true, save);
    expect(chosen).toEqual({ analysis_id: 15, expected_revision: 2 });
    expect(getAnalysis).toHaveBeenCalledExactlyOnceWith(15);
    expect(save).toHaveBeenCalledTimes(1);
  });

  it('rejects a stale in-flight switch of study or patient after save', async () => {
    let stillSelected = true;
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => stillSelected, async () => {
      stillSelected = false;
    })).rejects.toThrow(/sélectionnée a changé/);
    expect(getAnalysis).not.toHaveBeenCalled();
  });

  it('rejects a switch while the source GET is pending', async () => {
    let stillSelected = true;
    getAnalysis.mockImplementation(async () => {
      stillSelected = false;
      return { id: 15, angles_data: { scientific_read_path: { revision: 1 } } };
    });
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => stillSelected, async () => {}))
      .rejects.toThrow(/étude sélectionnée a changé/);
  });

  it('refuses forged or missing API identity and unverified revision', async () => {
    getAnalysis.mockResolvedValue({
      id: 16, angles_data: { scientific_read_path: { revision: 2 } },
    });
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => true, async () => {}))
      .rejects.toThrow(/a changé/);
    getAnalysis.mockResolvedValue({ id: 15, angles_data: {} });
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => true, async () => {}))
      .rejects.toThrow(/révision scientifique/);
    getAnalysis.mockResolvedValue({ id: 15, angles_data: { scientific_read_path: { revision: 0 } } });
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => true, async () => {}))
      .rejects.toThrow(/révision scientifique/);
  });

  it('aborts when save fails, before fetching or exporting an unpersisted study', async () => {
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => true, async () => {
      throw new Error('save unavailable');
    })).rejects.toThrow('save unavailable');
    expect(getAnalysis).not.toHaveBeenCalled();
  });

  it('rejects invalid or absent patient/study identifiers before any I/O', async () => {
    await expect(prepareBoundCephaloDocumentSource(3, 0, () => true, async () => {}))
      .rejects.toThrow(/Identité/);
    await expect(prepareBoundCephaloDocumentSource(0, 15, () => true, async () => {}))
      .rejects.toThrow(/Identité/);
    expect(getAnalysis).not.toHaveBeenCalled();
  });
});
