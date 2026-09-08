import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DentistsView } from './DentistsView';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

vi.mock('../../../../services/zka/mobileFetch', () => ({
  mobileFetch: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.mocked(mobileFetch).mockReset();
});

describe('MOB-5A DentistsView', () => {
  it('loads the tenant-scoped mobile dentists surface from paired credentials', async () => {
    vi.spyOn(MobileStorage, 'getCredentials').mockResolvedValue({
      publicId: 'cabinet-1',
      masterKey: 'master-key',
      access_token: 'mobile-token',
      api_base_url: 'http://127.0.0.1:8005',
    });
    vi.mocked(mobileFetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({
        dentists: [
          { id: 7, name: 'Dr Alice', email: 'alice@example.test', today_appointments: 2 },
        ],
      }),
    } as unknown as Response);

    render(
      <MemoryRouter>
        <DentistsView embedded />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Dr Alice')).toBeTruthy();
    expect(screen.getByText('alice@example.test')).toBeTruthy();
    expect(screen.getByText('2 RDV')).toBeTruthy();
    expect(screen.getByText('Praticien principal')).toBeTruthy();

    await waitFor(() => expect(mobileFetch).toHaveBeenCalledTimes(1));
    const [url, init] = vi.mocked(mobileFetch).mock.calls[0];
    expect(String(url)).toBe('http://127.0.0.1:8005/api/mobile/dentists');
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer mobile-token');
  });

  it('fails explicitly when the mobile device is not paired', async () => {
    vi.spyOn(MobileStorage, 'getCredentials').mockResolvedValue(null);

    render(
      <MemoryRouter>
        <DentistsView embedded />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Non appairé')).toBeTruthy();
    expect(mobileFetch).not.toHaveBeenCalled();
  });
});
