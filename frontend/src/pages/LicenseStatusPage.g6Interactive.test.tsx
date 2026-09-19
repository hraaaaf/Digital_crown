import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { LicenseStatusPage } from './LicenseStatusPage';

const state = vi.hoisted(() => ({
  user: {
    id: 77,
    license_expires_at: '2025-01-01T00:00:00Z',
  } as any,
  logout: vi.fn(),
}));

vi.mock('../stores/useAuthStore', () => ({
  useAuthStore: () => ({ user: state.user, logout: state.logout }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  state.user = { id: 77, license_expires_at: '2025-01-01T00:00:00Z' };
  vi.spyOn(window, 'open').mockImplementation(() => null);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('LicenseStatusPage G6 interactive matrix', () => {
  it('renders expired licence truth without inventing a plan name', () => {
    render(<LicenseStatusPage />);

    expect(screen.getByRole('heading', { name: 'Licence Expirée' })).toBeTruthy();
    expect(screen.getByText(/Votre licence a expiré le/i)).toBeTruthy();
    expect(screen.queryByText(/licence Elite/i)).toBeNull();
    expect(screen.getByText('Inactif')).toBeTruthy();
  });

  it('opens the canonical renewal destination and logs out only through the explicit return action', () => {
    render(<LicenseStatusPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Renouveler maintenant' }));
    expect(window.open).toHaveBeenCalledWith('https://digitalcrown.ma/pricing', '_blank');
    expect(state.logout).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Retour à la connexion' }));
    expect(state.logout).toHaveBeenCalledTimes(1);
  });

  it('renders waiting mode distinctly when the licence is not expired', () => {
    state.user = { id: 77, license_expires_at: '2099-01-01T00:00:00Z' };
    render(<LicenseStatusPage />);

    expect(screen.getByRole('heading', { name: 'Activation en cours' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Contacter le support' })).toBeTruthy();
    expect(screen.getByText('En attente')).toBeTruthy();
    expect(screen.queryByText(/Licence Expirée/i)).toBeNull();
  });
});
