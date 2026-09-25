import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LoginPage } from './LoginPage';
import { authService } from '../services/auth';
import { api, resetAuthState } from '../services/api';

const checkAuthMock = vi.fn();

vi.mock('../services/auth', () => ({
  authService: {
    isAuthenticated: vi.fn(),
    login: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
  },
}));

vi.mock('../services/api', () => ({
  api: {
    post: vi.fn(),
  },
  resetAuthState: vi.fn(),
}));

vi.mock('../stores/useAuthStore', () => ({
  useAuthStore: (selector: (state: { checkAuth: typeof checkAuthMock }) => unknown) =>
    selector({ checkAuth: checkAuthMock }),
}));

function renderLogin(initialEntry = '/login') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<div>Dashboard destination</div>} />
        <Route path="/register" element={<div>Register destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(authService.isAuthenticated).mockResolvedValue(false);
  vi.mocked(authService.login).mockResolvedValue(undefined as never);
  vi.mocked(authService.logout).mockResolvedValue(undefined as never);
  checkAuthMock.mockResolvedValue(undefined);
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
});

afterEach(() => cleanup());

describe('LoginPage G1 interactive matrix', () => {
  it('submits credentials, rearms auth state and navigates only after successful login', async () => {
    renderLogin();

    fireEvent.change(screen.getByPlaceholderText('nom@cabinet.com'), {
      target: { value: 'dentist@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'Secret123!' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Se connecter' }));

    await waitFor(() => expect(resetAuthState).toHaveBeenCalledTimes(1));
    expect(authService.login).toHaveBeenCalledWith('dentist@example.com', 'Secret123!');
    expect(await screen.findByText('Dashboard destination')).toBeTruthy();
  });

  it('surfaces the precise backend refusal and does not navigate on failed login', async () => {
    vi.mocked(authService.login).mockRejectedValueOnce({
      response: { data: { detail: 'Identifiants invalides.' } },
    } as never);

    renderLogin();
    fireEvent.change(screen.getByPlaceholderText('nom@cabinet.com'), {
      target: { value: 'dentist@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'bad-pass' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Se connecter' }));

    expect(await screen.findByText('Identifiants invalides.')).toBeTruthy();
    expect(screen.queryByText('Dashboard destination')).toBeNull();
    expect(authService.login).toHaveBeenCalledTimes(1);
  });

  it('wires Create account and Google controls to their intended actions', async () => {
    renderLogin();

    fireEvent.click(screen.getByRole('button', { name: 'Google' }));
    expect(authService.loginWithGoogle).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Créer un compte' }));
    expect(await screen.findByText('Register destination')).toBeTruthy();
  });

  it('handles locked authenticated licence recheck success and logout', async () => {
    vi.mocked(authService.isAuthenticated).mockResolvedValue(true);
    renderLogin('/login?locked=true');

    expect(await screen.findByRole('button', { name: 'Revérifier la licence' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Revérifier la licence' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/clinics/recheck-license'));
    expect(checkAuthMock).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('Dashboard destination')).toBeTruthy();
  });

  it('keeps locked user on login and shows explicit 402 licence refusal', async () => {
    vi.mocked(authService.isAuthenticated).mockResolvedValue(true);
    vi.mocked(api.post).mockRejectedValueOnce({ response: { status: 402 } } as never);
    renderLogin('/login?locked=true');

    fireEvent.click(await screen.findByRole('button', { name: 'Revérifier la licence' }));

    expect(await screen.findByText(/licence est toujours invalide/i)).toBeTruthy();
    expect(screen.queryByText('Dashboard destination')).toBeNull();
  });

  it('logs out from the locked authenticated state without false navigation', async () => {
    vi.mocked(authService.isAuthenticated).mockResolvedValue(true);
    renderLogin('/login?locked=true');

    fireEvent.click(await screen.findByRole('button', { name: 'Se déconnecter' }));
    await waitFor(() => expect(authService.logout).toHaveBeenCalledTimes(1));

    expect(screen.getByRole('button', { name: 'S\'authentifier en tant qu\'Admin' })).toBeTruthy();
    expect(screen.queryByText('Dashboard destination')).toBeNull();
  });

  it('honors Google success callback only after local auth-store refresh succeeds', async () => {
    renderLogin('/login?google=success');

    await waitFor(() => expect(checkAuthMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('Dashboard destination')).toBeTruthy();
  });

  it('surfaces Google callback failure instead of claiming a session exists', async () => {
    checkAuthMock.mockRejectedValueOnce(new Error('missing local session'));
    renderLogin('/login?google=success');

    expect(await screen.findByText(/session locale introuvable/i)).toBeTruthy();
    expect(screen.queryByText('Dashboard destination')).toBeNull();
  });
});
