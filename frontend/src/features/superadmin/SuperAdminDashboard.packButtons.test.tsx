import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import toast from 'react-hot-toast';
import { api } from '../../services/api';
import { SuperAdminDashboard } from './SuperAdminDashboard';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const future = '2030-01-01T00:00:00.000Z';

const clients = [
  {
    id: 101,
    nom_complet: 'Dr Gold',
    email: 'gold@example.com',
    telephone: '0600000101',
    cabinet_name: 'Cabinet Gold',
    is_licensed: true,
    license_expires_at: future,
    created_at: future,
    is_archived: false,
    is_suspended: false,
    internal_notes: 'Gold note',
    last_login_at: null,
    subscription_plan: 'GOLD',
    stats: { total_patients: 1, total_ia_panoramique: 0, total_ia_cephalo: 0 },
  },
  {
    id: 102,
    nom_complet: 'Dr Premium',
    email: 'premium@example.com',
    telephone: '0600000102',
    cabinet_name: 'Cabinet Premium',
    is_licensed: true,
    license_expires_at: future,
    created_at: future,
    is_archived: false,
    is_suspended: false,
    internal_notes: null,
    last_login_at: null,
    subscription_plan: 'PREMIUM',
    stats: { total_patients: 2, total_ia_panoramique: 0, total_ia_cephalo: 0 },
  },
  {
    id: 103,
    nom_complet: 'Dr Elite',
    email: 'elite@example.com',
    telephone: '0600000103',
    cabinet_name: 'Cabinet Elite',
    is_licensed: true,
    license_expires_at: future,
    created_at: future,
    is_archived: false,
    is_suspended: false,
    internal_notes: null,
    last_login_at: null,
    subscription_plan: 'ELITE',
    stats: { total_patients: 3, total_ia_panoramique: 0, total_ia_cephalo: 0 },
  },
];

function installGetMock() {
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/superadmin/clients') return { data: clients } as never;
    if (url === '/superadmin/trial-codes') return { data: [] } as never;
    if (url.endsWith('/license-history')) {
      return { data: [{ action: 'grant', duration: 30, timestamp: future }] } as never;
    }
    throw new Error(`Unexpected GET ${url}`);
  });
}

async function renderDashboard() {
  render(
    <MemoryRouter>
      <SuperAdminDashboard />
    </MemoryRouter>,
  );
  await screen.findByText('Dr Gold');
}

beforeEach(() => {
  vi.clearAllMocks();
  installGetMock();
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.patch).mockResolvedValue({ data: {} } as never);
  vi.stubGlobal('confirm', vi.fn(() => true));
  Object.assign(navigator, {
    clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('SuperAdminDashboard commercial pack buttons', () => {
  it.each([
    ['GOLD', 'PREMIUM', 101],
    ['PREMIUM', 'ELITE', 102],
    ['ELITE', 'GOLD', 103],
  ])('wires desktop pack change %s -> %s to the server contract', async (from, to, id) => {
    await renderDashboard();

    const select = screen.getByDisplayValue(from) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: to } });

    await waitFor(() => expect(vi.mocked(api.patch)).toHaveBeenCalledWith(
      `/superadmin/clients/${id}/plan`,
      {},
      { params: { plan: to } },
    ));
    expect(vi.mocked(toast.success)).toHaveBeenCalledWith(`Pack ${to} attribué.`);
  });

  it('surfaces the precise server reason when a downgrade is refused', async () => {
    vi.mocked(api.patch).mockRejectedValueOnce({
      response: {
        status: 409,
        data: { detail: 'Passage au pack GOLD impossible : équipe réservée 2 dentiste(s) / 3 assistante(s).' },
      },
    });

    await renderDashboard();
    fireEvent.change(screen.getByDisplayValue('ELITE'), { target: { value: 'GOLD' } });

    await waitFor(() => expect(vi.mocked(toast.error)).toHaveBeenCalledWith(
      expect.stringContaining('équipe réservée'),
    ));
  });

  it('enforces archived/suspended desktop states without exposing mutable pack actions', async () => {
    const archivedSuspended = {
      ...clients[0],
      is_archived: true,
      is_suspended: true,
    };
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/superadmin/clients') return { data: [archivedSuspended] } as never;
      if (url === '/superadmin/trial-codes') return { data: [] } as never;
      if (url.endsWith('/license-history')) return { data: [] } as never;
      throw new Error(`Unexpected GET ${url}`);
    });

    await renderDashboard();
    const card = screen.getByText('Dr Gold').closest('.group');
    if (!card) throw new Error('Archived Gold client card not found');
    const scoped = within(card as HTMLElement);

    expect((scoped.getByDisplayValue('GOLD') as HTMLSelectElement).disabled).toBe(true);
    for (const label of ['+ 1 MOIS', '+ 3 MOIS', '+ 6 MOIS', '+ 1 AN']) {
      expect((scoped.getByRole('button', { name: new RegExp(label.replace('+', '\\+')) }) as HTMLButtonElement).disabled).toBe(true);
    }
    expect((scoped.getByTitle('WhatsApp de relance') as HTMLButtonElement).disabled).toBe(true);
    expect(scoped.getByTitle('Réactiver')).toBeTruthy();
    expect(scoped.getByTitle('Désarchiver')).toBeTruthy();
  });

  it('wires licence, notes, history, renewal, suspend and archive buttons on desktop', async () => {
    await renderDashboard();

    const card = screen.getByText('Dr Gold').closest('.group');
    if (!card) throw new Error('Gold client card not found');
    const scoped = within(card as HTMLElement);

    for (const [label, action] of [
      ['+ 1 MOIS', '1m'],
      ['+ 3 MOIS', '3m'],
      ['+ 6 MOIS', '6m'],
      ['+ 1 AN', '1y'],
    ] as const) {
      vi.mocked(api.post).mockClear();
      fireEvent.click(scoped.getByRole('button', { name: new RegExp(label.replace('+', '\\+')) }));
      await waitFor(() => expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/superadmin/clients/101/grant-license',
        null,
        { params: { action } },
      ));
    }

    fireEvent.click(scoped.getByTitle('Notes internes'));
    fireEvent.change(screen.getByPlaceholderText(/Notes sur ce client/), { target: { value: 'Audit note' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
    await waitFor(() => expect(vi.mocked(api.patch)).toHaveBeenCalledWith(
      '/superadmin/clients/101/notes',
      { internal_notes: 'Audit note' },
    ));

    fireEvent.click(scoped.getByTitle('Historique Licences'));
    expect(await screen.findByText('Historique Licences')).toBeTruthy();
    expect(screen.getByText('grant')).toBeTruthy();

    vi.mocked(api.post).mockClear();
    fireEvent.click(scoped.getByTitle('WhatsApp de relance'));
    await waitFor(() => expect(vi.mocked(api.post)).toHaveBeenCalledWith(
      '/superadmin/clients/101/send-renewal-email',
      { message: 'Votre licence expire bientôt.' },
    ));

    const confirmMock = vi.mocked(confirm);
    confirmMock.mockReturnValueOnce(false);
    vi.mocked(api.patch).mockClear();
    fireEvent.click(scoped.getByTitle('Suspendre'));
    expect(api.patch).not.toHaveBeenCalled();

    confirmMock.mockReturnValueOnce(true);
    fireEvent.click(scoped.getByTitle('Suspendre'));
    await waitFor(() => expect(vi.mocked(api.patch)).toHaveBeenCalledWith('/superadmin/clients/101/suspend'));

    vi.mocked(api.patch).mockClear();
    confirmMock.mockReturnValueOnce(false);
    fireEvent.click(scoped.getByTitle('Archiver'));
    expect(api.patch).not.toHaveBeenCalled();

    confirmMock.mockReturnValueOnce(true);
    fireEvent.click(scoped.getByTitle('Archiver'));
    await waitFor(() => expect(vi.mocked(api.patch)).toHaveBeenCalledWith('/superadmin/clients/101/archive'));
  });
});


describe('SuperAdmin renewal feedback truth', () => {
  it('uses WhatsApp wording and surfaces the backend transport detail', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { detail: "Aucun numéro de téléphone trouvé pour l'envoi WhatsApp." } },
    } as never);
    await renderDashboard();

    const card = screen.getByText('Dr Gold').closest('.group');
    if (!card) throw new Error('Gold client card not found');
    fireEvent.click(within(card as HTMLElement).getByTitle('WhatsApp de relance'));

    await waitFor(() => expect(vi.mocked(toast.error)).toHaveBeenCalledWith(
      "Aucun numéro de téléphone trouvé pour l'envoi WhatsApp.",
    ));
  });
});
