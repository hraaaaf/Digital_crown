import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Header } from './Header';
import { api } from '../services/api';
import { cabinetApi } from '../services/templateApi';
import { authService } from '../services/auth';

let mockUser: any = { is_superadmin: false, nom_complet: 'Dr Test', role: 'DENTISTE', employer_id: null };

vi.mock('../stores/useAuthStore', () => ({
  useAuthStore: () => ({ user: mockUser }),
}));
vi.mock('../services/api', () => ({ api: { get: vi.fn() } }));
vi.mock('../services/templateApi', () => ({ cabinetApi: { getMine: vi.fn() } }));
vi.mock('../services/auth', () => ({ authService: { logout: vi.fn() } }));
vi.mock('../hooks/useLocalStorage', () => ({ safeStorage: { remove: vi.fn() } }));
vi.mock('../features/tutorial/VoluntaryTutorial', () => ({ TutorialHelpButton: () => <button>Aide</button> }));

function renderHeader(props: { isCrownBotOpen?: boolean; crownBotUnreadCount?: number; onToggleCrownBot?: () => void } = {}) {
  return render(<MemoryRouter><Header {...props} /></MemoryRouter>);
}

beforeEach(() => {
  vi.clearAllMocks();
  mockUser = { is_superadmin: false, nom_complet: 'Dr Test', role: 'DENTISTE', employer_id: null };
  vi.mocked(cabinetApi.getMine).mockResolvedValue({ nom_cabinet: 'Cabinet Test', header_lines_fr: ['Dr Test'] } as never);
  vi.mocked(api.get).mockResolvedValue({
    data: {
      total: 1,
      requires_attention: 1,
      delivery_semantics: 'source_state_only',
      items: [{
        id: 'a1', source: 'treasury_hub', title: 'Relance', message: 'Paiement attendu',
        destination: '/accounting?tab=treasury', priority: 'high', channel: 'in_app',
        delivery_state: 'source', delivery_verified: false,
      }],
    },
  } as never);
  vi.mocked(authService.logout).mockResolvedValue(undefined as never);
});

afterEach(() => cleanup());

describe('Header G1 interactive matrix', () => {
  it('opens and closes attention center and exposes exact destination', async () => {
    renderHeader();
    const bell = screen.getByRole('button', { name: "Ouvrir le centre d’attention" });
    fireEvent.click(bell);

    expect(await screen.findByText('Centre d’attention')).toBeTruthy();
    expect(screen.getByRole('link', { name: /Relance/i }).getAttribute('href')).toBe('/accounting?tab=treasury');
    expect(bell.getAttribute('aria-expanded')).toBe('true');

    fireEvent.click(screen.getByRole('link', { name: /Relance/i }));
    expect(screen.queryByText('Centre d’attention')).toBeNull();
  });

  it('wires CrownBot header control only when callback exists', () => {
    const toggle = vi.fn();
    renderHeader({ onToggleCrownBot: toggle, crownBotUnreadCount: 2 });

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir CrownBot' }));
    expect(toggle).toHaveBeenCalledTimes(1);
    expect(screen.getByText('2')).toBeTruthy();
  });

  it('shows super-admin destination only for super-admin identity', () => {
    mockUser = { is_superadmin: true, nom_complet: 'Admin', role: 'DENTISTE' };
    renderHeader();
    expect(screen.getAllByRole('link', { name: /Gestion des Dentistes/i }).every(link => link.getAttribute('href') === '/super-admin')).toBe(true);
  });

  it('hides Settings and Treasury shortcuts without permission and shows Settings for cabinet owner', async () => {
    mockUser = {
      is_superadmin: false,
      nom_complet: 'Restricted',
      role: 'SECRETAIRE',
      employer_id: 1,
      permissions: { settings: false, accounting: false },
    };
    const first = renderHeader();
    expect(screen.queryByTitle('Réglages')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: "Ouvrir le centre d’attention" }));
    expect(await screen.findByText('Centre d’attention')).toBeTruthy();
    expect(screen.queryByRole('link', { name: 'Trésorerie' })).toBeNull();
    await waitFor(() => expect(cabinetApi.getMine).not.toHaveBeenCalled());
    first.unmount();

    mockUser = {
      is_superadmin: false,
      nom_complet: 'Owner',
      role: 'DENTISTE',
      employer_id: null,
    };
    renderHeader();
    expect(screen.getByTitle('Réglages')).toBeTruthy();
    await waitFor(() => expect(cabinetApi.getMine).toHaveBeenCalledTimes(1));
  });

  it('keeps global mobile header icon controls named and at least 44px', () => {
    mockUser = { is_superadmin: true, nom_complet: 'Admin', role: 'DENTISTE', employer_id: null };
    const { container } = renderHeader();

    const hub = screen.getByRole('link', { name: "Changer d'espace" });
    const settings = screen.getByRole('link', { name: 'Réglages' });
    const attention = screen.getByRole('button', { name: "Ouvrir le centre d’attention" });
    const logout = screen.getByRole('button', { name: 'Déconnexion' });
    const adminIcon = container.querySelector('a[title="Gestion des Dentistes"][aria-label="Gestion des Dentistes"]');

    for (const control of [hub, settings, attention, logout]) {
      expect(control.className).toContain('min-h-11');
      expect(control.className).toContain('min-w-11');
    }
    expect(adminIcon?.getAttribute('aria-label')).toBe('Gestion des Dentistes');
    expect(adminIcon?.className).toContain('min-h-11');
    expect(adminIcon?.className).toContain('min-w-11');
  });

  it('requires explicit confirmation before logout and Cancel is non-mutating', async () => {
    renderHeader();
    fireEvent.click(screen.getByTitle('Déconnexion'));
    expect(screen.getByText('Êtes-vous sûr de vouloir vous déconnecter de votre session ?')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(authService.logout).not.toHaveBeenCalled();
    expect(screen.queryByText('Êtes-vous sûr de vouloir vous déconnecter de votre session ?')).toBeNull();

    fireEvent.click(screen.getByTitle('Déconnexion'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer' }));
    await waitFor(() => expect(authService.logout).toHaveBeenCalledTimes(1));
  });
});
