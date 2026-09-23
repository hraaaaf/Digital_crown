import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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
  default: { success: vi.fn(), error: vi.fn() },
}));

const trial = {
  id: 5,
  code: 'DC-TRIAL-5',
  email: 'dentiste@example.com',
  nom_complet: 'Dr Test',
  cabinet_name: 'Cabinet Test',
  trial_days: 30,
  expires_at: '2030-01-01T00:00:00Z',
  consumed_at: null,
  revoked_at: null,
  activation_url: 'https://digitalcrown.ma/activate?code=DC-TRIAL-5',
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/superadmin/clients') return { data: [] } as never;
    if (url === '/superadmin/trial-codes') return { data: [trial] } as never;
    throw new Error('unexpected GET '+url);
  });
  vi.mocked(api.post).mockResolvedValue({ data: trial } as never);
  vi.mocked(api.patch).mockResolvedValue({ data: {} } as never);
  Object.assign(navigator, {
    clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
});

afterEach(() => cleanup());

async function renderDashboard() {
  render(<MemoryRouter><SuperAdminDashboard /></MemoryRouter>);
  await screen.findByText('DC-TRIAL-5');
}

describe('SuperAdmin trial-code G6 matrix', () => {
  it('creates a trial code with exact form payload and copies link only after backend ACK', async () => {
    await renderDashboard();

    fireEvent.change(screen.getByPlaceholderText('Email professionnel'), { target: { value: 'new@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Nom complet'), { target: { value: 'Dr New' } });
    fireEvent.change(screen.getByPlaceholderText('Nom du cabinet'), { target: { value: 'Cabinet New' } });
    fireEvent.change(screen.getByPlaceholderText('Notes internes'), { target: { value: 'Prospect salon' } });

    const numberInputs = screen.getAllByRole('spinbutton');
    fireEvent.change(numberInputs[0], { target: { value: '45' } });
    fireEvent.change(numberInputs[1], { target: { value: '10' } });

    fireEvent.click(screen.getByRole('button', { name: /Générer Et Copier Le Lien/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/superadmin/trial-codes', {
      email: 'new@example.com',
      nom_complet: 'Dr New',
      cabinet_name: 'Cabinet New',
      trial_days: 45,
      expires_in_days: 10,
      notes: 'Prospect salon',
    }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(trial.activation_url);
    expect(toast.success).toHaveBeenCalledWith("Code créé. Lien d'activation copié.");
  });

  it('does not copy or claim success when trial creation is refused', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('create refused'));
    await renderDashboard();

    fireEvent.change(screen.getByPlaceholderText('Email professionnel'), { target: { value: 'refused@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /Générer Et Copier Le Lien/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    expect(navigator.clipboard.writeText).not.toHaveBeenCalled();
    expect(toast.success).not.toHaveBeenCalledWith("Code créé. Lien d'activation copié.");
    expect(toast.error).toHaveBeenCalledWith("Erreur lors de la création du code.");
  });

  it('copies an existing activation link and reports clipboard failure truthfully', async () => {
    await renderDashboard();
    fireEvent.click(screen.getByRole('button', { name: /^Copier Le Lien$/i }));
    await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledWith(trial.activation_url));

    vi.mocked(navigator.clipboard.writeText).mockRejectedValueOnce(new Error('clipboard denied'));
    fireEvent.click(screen.getByRole('button', { name: /^Copier Le Lien$/i }));
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Impossible de copier le lien.'));
  });

  it('revokes an unused trial code then reloads server truth', async () => {
    await renderDashboard();
    const beforeReads = vi.mocked(api.get).mock.calls.filter(([url]) => url === '/superadmin/trial-codes').length;

    fireEvent.click(screen.getByRole('button', { name: 'Révoquer' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/superadmin/trial-codes/5/revoke'));
    await waitFor(() => expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/superadmin/trial-codes').length
    ).toBeGreaterThan(beforeReads));
  });

  it('surfaces precise revoke refusal without false success', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'Code déjà utilisé' } } });
    await renderDashboard();

    fireEvent.click(screen.getByRole('button', { name: 'Révoquer' }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Code déjà utilisé'));
    expect(toast.success).not.toHaveBeenCalledWith('Code révoqué.');
  });

  it('refreshes trial codes from the server on explicit Actualiser', async () => {
    await renderDashboard();
    const before = vi.mocked(api.get).mock.calls.filter(([url]) => url === '/superadmin/trial-codes').length;
    fireEvent.click(screen.getByRole('button', { name: 'Actualiser' }));
    await waitFor(() => expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/superadmin/trial-codes').length
    ).toBeGreaterThan(before));
  });
});
