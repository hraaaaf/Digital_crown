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

  it('reuses a verified historical revision without mutating identical signed science', async () => {
    const save = vi.fn(async () => {});
    const local = { landmarks: [{ id: 'S', x: 10, y: 20 }, { id: 'N', x: 30, y: 40 }], mmPerPixel: 0.2 };
    getAnalysis.mockResolvedValue({
      id: 15, landmarks_data: [{ id: 'N', x: 30, y: 40 }, { id: 'S', x: 10, y: 20 }],
      mm_per_pixel: 0.2, angles_data: { scientific_read_path: { revision: 2 } },
    });
    const source = await prepareBoundCephaloDocumentSource(3, 15, () => true, save, () => local);
    expect(source).toEqual({ analysis_id: 15, expected_revision: 2 });
    expect(save).not.toHaveBeenCalled();
    expect(getAnalysis).toHaveBeenCalledExactlyOnceWith(15);
  });

  it('keeps strict save when scientific landmarks or calibration diverge', async () => {
    const saved = { id: 15, landmarks_data: [{ id: 'S', x: 10, y: 20 }],
      mm_per_pixel: 0.2, angles_data: { scientific_read_path: { revision: 2 } } };
    getAnalysis.mockResolvedValue(saved);
    const save = vi.fn(async () => {});
    const landmarks = [{ id: 'S', x: 11, y: 20 }];
    await prepareBoundCephaloDocumentSource(3, 15, () => true, save,
      () => ({ landmarks, mmPerPixel: 0.2 }));
    expect(save).toHaveBeenCalledTimes(1);
    getAnalysis.mockClear();
    save.mockClear();
    await prepareBoundCephaloDocumentSource(3, 15, () => true, save,
      () => ({ landmarks: [{ id: 'S', x: 10, y: 20 }], mmPerPixel: 0.21 }));
    expect(save).toHaveBeenCalledTimes(1);
  });

  it('refuses a transient saved-study mismatch instead of silently exporting', async () => {
    const save = vi.fn(async () => { throw Error('scientific revision conflict 409'); });
    getAnalysis.mockResolvedValue({
      id: 15, landmarks_data: [{ id: 'S', x: 10, y: 20 }],
      mm_per_pixel: 0.2, angles_data: { scientific_read_path: { revision: 2 } },
    });
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => true, save,
      () => ({ landmarks: [{ id: 'S', x: 11, y: 20 }], mmPerPixel: 0.2 })))
      .rejects.toThrow(/scientific revision conflict/);
    expect(save).toHaveBeenCalledTimes(1);
  });

  it('refuses unverified existing revision even if the landmarks are identical', async () => {
    const save = vi.fn(async () => {});
    getAnalysis.mockResolvedValue({
      id: 15, landmarks_data: [{ id: 'S', x: 10, y: 20 }],
      mm_per_pixel: 0.2, angles_data: { scientific_read_path: { revision: 0 } },
    });
    await expect(prepareBoundCephaloDocumentSource(3, 15, () => true, save,
      () => ({ landmarks: [{ id: 'S', x: 10, y: 20 }], mmPerPixel: 0.2 })))
      .rejects.toThrow(/révision scientifique/);
    expect(save).not.toHaveBeenCalled();
  });

  it('rejects invalid or absent patient/study identifiers before any I/O', async () => {
    await expect(prepareBoundCephaloDocumentSource(3, 0, () => true, async () => {}))
      .rejects.toThrow(/Identité/);
    await expect(prepareBoundCephaloDocumentSource(0, 15, () => true, async () => {}))
      .rejects.toThrow(/Identité/);
    expect(getAnalysis).not.toHaveBeenCalled();
  });
});
