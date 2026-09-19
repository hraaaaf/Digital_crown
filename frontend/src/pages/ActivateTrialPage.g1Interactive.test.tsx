import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ActivateTrialPage } from './ActivateTrialPage';
import { authService } from '../services/auth';

vi.mock('../services/auth', () => ({
  authService: {
    previewTrialCode: vi.fn(),
    activateTrial: vi.fn(),
  },
}));

function renderPage(entry = '/activate') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <ActivateTrialPage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(authService.previewTrialCode).mockResolvedValue({
    email: 'invite@example.com',
    nom_complet: 'Dr Invite',
    cabinet_name: 'Cabinet Invite',
    trial_days: 30,
    expires_at: '2026-10-19T00:00:00Z',
  } as never);
  vi.mocked(authService.activateTrial).mockResolvedValue({ message: 'Activation OK' } as never);
});

afterEach(() => cleanup());

describe('ActivateTrialPage G1 interactive matrix', () => {
  it('previews a URL activation code and prefills backend truth', async () => {
    renderPage('/activate?code=dc-ab12');

    await waitFor(() => expect(authService.previewTrialCode).toHaveBeenCalledWith('dc-ab12'));
    expect(screen.getByDisplayValue('invite@example.com')).toBeTruthy();
    expect(screen.getByDisplayValue('Dr Invite')).toBeTruthy();
    expect(screen.getByDisplayValue('Cabinet Invite')).toBeTruthy();
  });

  it('submits exact activation payload and shows success only after ACK', async () => {
    renderPage('/activate?code=DC-AB12');
    await screen.findByDisplayValue('invite@example.com');

    const password = screen.getByPlaceholderText('8 caractères minimum');
    fireEvent.change(password, { target: { value: 'Secret123!' } });
    const checks = screen.getAllByRole('checkbox');
    fireEvent.click(checks[0]);
    fireEvent.click(checks[1]);
    fireEvent.click(screen.getByRole('button', { name: /Activer Mon Essai/i }));

    await waitFor(() => expect(authService.activateTrial).toHaveBeenCalledWith({
      code: 'DC-AB12',
      email: 'invite@example.com',
      password: 'Secret123!',
      nom_complet: 'Dr Invite',
      cabinet_name: 'Cabinet Invite',
      accept_terms: true,
      accept_privacy: true,
    }));
    expect(await screen.findByText('Activation OK')).toBeTruthy();
    expect(screen.getByText('Essai activé')).toBeTruthy();
  });

  it('surfaces preview failure without calling activation', async () => {
    vi.mocked(authService.previewTrialCode).mockRejectedValueOnce({
      response: { data: { detail: "Code d'activation expiré." } },
    } as never);

    renderPage('/activate?code=EXPIRED');

    expect(await screen.findByText("Code d'activation expiré.")).toBeTruthy();
    expect(authService.activateTrial).not.toHaveBeenCalled();
  });

  it('surfaces activation refusal without false success', async () => {
    vi.mocked(authService.activateTrial).mockRejectedValueOnce({
      response: { data: { detail: 'Code déjà utilisé.' } },
    } as never);

    renderPage('/activate?code=DC-AB12');
    await screen.findByDisplayValue('invite@example.com');
    fireEvent.change(screen.getByPlaceholderText('8 caractères minimum'), { target: { value: 'Secret123!' } });
    const checks = screen.getAllByRole('checkbox');
    fireEvent.click(checks[0]);
    fireEvent.click(checks[1]);
    fireEvent.click(screen.getByRole('button', { name: /Activer Mon Essai/i }));

    expect(await screen.findByText('Code déjà utilisé.')).toBeTruthy();
    expect(screen.queryByText('Essai activé')).toBeNull();
  });
});
