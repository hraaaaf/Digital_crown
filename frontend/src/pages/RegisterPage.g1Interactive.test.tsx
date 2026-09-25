import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RegisterPage } from './RegisterPage';
import { authService } from '../services/auth';
import toast from 'react-hot-toast';

vi.mock('../services/auth', () => ({
  authService: { register: vi.fn() },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

function renderRegister(entry = '/register') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<div>Login destination</div>} />
        <Route path="/terms" element={<div>Terms destination</div>} />
        <Route path="/privacy" element={<div>Privacy destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function fillIdentity() {
  fireEvent.change(screen.getByPlaceholderText('Dr. Jean Dupont'), { target: { value: 'Dr Test' } });
  fireEvent.change(screen.getByPlaceholderText('votre@email.com'), { target: { value: 'test@example.com' } });
  fireEvent.change(screen.getByPlaceholderText('8 caractères minimum'), { target: { value: 'Secret123!' } });
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(authService.register).mockResolvedValue(undefined as never);
});

afterEach(() => cleanup());

describe('RegisterPage G1 interactive matrix', () => {
  it('keeps submit disabled until both legal consents are accepted', () => {
    renderRegister();
    fillIdentity();

    const submit = screen.getByRole('button', { name: /Créer mon compte/i }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);

    const checks = screen.getAllByRole('checkbox') as HTMLInputElement[];
    fireEvent.click(checks[0]);
    expect(submit.disabled).toBe(true);
    fireEvent.click(checks[1]);
    expect(submit.disabled).toBe(false);
  });

  it('submits exact registration payload and shows pending-validation success state', async () => {
    renderRegister();
    fillIdentity();
    const checks = screen.getAllByRole('checkbox');
    fireEvent.click(checks[0]);
    fireEvent.click(checks[1]);
    fireEvent.click(screen.getByRole('button', { name: /Créer mon compte/i }));

    await waitFor(() => expect(authService.register).toHaveBeenCalledWith(
      'test@example.com', 'Secret123!', 'Dr Test', true, true,
    ));
    expect(await screen.findByText('Demande Envoyée')).toBeTruthy();
    expect(screen.getByText(/en attente de validation/i)).toBeTruthy();
    expect(toast.success).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button', { name: /Créer mon compte/i })).toBeNull();
  });

  it('surfaces backend refusal and never renders a false success state', async () => {
    vi.mocked(authService.register).mockRejectedValueOnce({
      response: { data: { detail: 'Email déjà utilisé.' } },
    } as never);

    renderRegister();
    fillIdentity();
    const checks = screen.getAllByRole('checkbox');
    fireEvent.click(checks[0]);
    fireEvent.click(checks[1]);
    fireEvent.click(screen.getByRole('button', { name: /Créer mon compte/i }));

    expect(await screen.findByText('Email déjà utilisé.')).toBeTruthy();
    expect(screen.queryByText('Demande Envoyée')).toBeNull();
    expect(toast.error).toHaveBeenCalledTimes(1);
    expect(authService.register).toHaveBeenCalledTimes(1);
  });

  it('prefills invitation parameters without auto-submitting', async () => {
    renderRegister('/register?full_name=Dr%20Invite&email=invite%40example.com');

    expect(await screen.findByDisplayValue('Dr Invite')).toBeTruthy();
    expect(screen.getByDisplayValue('invite@example.com')).toBeTruthy();
    expect(authService.register).not.toHaveBeenCalled();
  });

  it('returns to login from the explicit existing-account control', async () => {
    renderRegister();
    fireEvent.click(screen.getByRole('link', { name: 'Se connecter' }));
    expect(await screen.findByText('Login destination')).toBeTruthy();
  });
});
