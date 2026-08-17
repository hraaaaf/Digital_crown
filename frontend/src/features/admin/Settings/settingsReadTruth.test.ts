import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { api } from '../../../services/api';
import { useCatalogStore } from './hooks/useCatalogStore';

const getMock = vi.mocked(api.get);

describe('Settings read truth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCatalogStore.setState({ specialties: [], loading: false, readError: null });
  });

  it('distinguishes catalog API failure from a genuinely empty catalog', async () => {
    getMock.mockRejectedValueOnce(new Error('catalog unavailable'));

    await useCatalogStore.getState().fetchCatalog();

    expect(useCatalogStore.getState().specialties).toEqual([]);
    expect(useCatalogStore.getState().readError).toContain('Impossible de charger le catalogue réel');
  });

  it('allows a genuinely empty catalog only after a successful backend read', async () => {
    getMock.mockResolvedValueOnce({ data: [] } as any);

    await useCatalogStore.getState().fetchCatalog();

    expect(useCatalogStore.getState().specialties).toEqual([]);
    expect(useCatalogStore.getState().readError).toBeNull();
  });

  it('blocks catalog mutations while the source-of-truth read is unavailable', async () => {
    useCatalogStore.setState({ readError: 'unavailable' });

    await useCatalogStore.getState().createSpecialty({ name: 'Test' });

    expect(api.post).not.toHaveBeenCalled();
  });
});
