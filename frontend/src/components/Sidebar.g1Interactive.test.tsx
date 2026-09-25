import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { api } from '../services/api';

const switchCabinet = vi.fn();
let mockUser: any = { is_superadmin: false, permissions: { agenda: true, accounting: true, patients: true, cephalo: true } };

vi.mock('../features/admin/Settings/hooks/useSettingsStore', () => ({
  useSettingsStore: () => ({
    activeCabinetId: '1',
    cabinets: [{ id: '1', nom: 'Cabinet A' }, { id: '2', nom: 'Cabinet B' }],
    switchCabinet,
  }),
}));

vi.mock('../stores/useAuthStore', () => ({
  useAuthStore: () => ({ user: mockUser }),
}));

vi.mock('../utils/accessControl', () => ({
  hasAccess: (user: any, permission: string) => Boolean(user?.permissions?.[permission]),
}));

vi.mock('../services/api', () => ({
  api: { get: vi.fn() },
}));

vi.mock('../services/auth', () => ({
  authService: {},
}));

function renderSidebar(entry = '/dashboard', props: { isOpen?: boolean; onClose?: () => void } = {}) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Sidebar {...props} />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockUser = { is_superadmin: false, permissions: { agenda: true, accounting: true, patients: true, cephalo: true } };
  vi.mocked(api.get).mockResolvedValue({ data: { total: 3 } } as never);
  localStorage.setItem('clinical_tips_enabled', 'true');
});

afterEach(() => cleanup());

describe('Sidebar G1 navigation matrix', () => {
  it('switches active cabinet from the shared shell control', async () => {
    renderSidebar();
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '2' } });
    expect(switchCabinet).toHaveBeenCalledWith('2');
  });

  it('renders authorized cabinet navigation and alert badge from backend truth', async () => {
    renderSidebar();

    expect(screen.getByRole('link', { name: /Tableau de bord/i }).getAttribute('href')).toBe('/dashboard');
    expect(screen.getByRole('link', { name: 'Agenda' }).getAttribute('href')).toBe('/agenda');
    expect(screen.getByRole('link', { name: 'Comptabilité' }).getAttribute('href')).toBe('/accounting');
    expect(screen.getByRole('link', { name: 'Patients' }).getAttribute('href')).toBe('/patients');
    await waitFor(() => expect(screen.getByText('3')).toBeTruthy());
  });

  it('hides permission-gated navigation when access is absent', () => {
    mockUser = { is_superadmin: false, permissions: { agenda: false, accounting: false, patients: false, cephalo: false } };
    renderSidebar();

    expect(screen.queryByRole('link', { name: 'Agenda' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Comptabilité' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Patients' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Approvisionnement' })).toBeNull();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('shows super-admin destinations only to super-admin identity', () => {
    mockUser = { is_superadmin: true, permissions: { agenda: true, accounting: true, patients: true, cephalo: true } };
    renderSidebar();
    expect(screen.getByRole('link', { name: 'Gestion des Dentistes' }).getAttribute('href')).toBe('/super-admin');
    expect(screen.getByRole('link', { name: 'Fournisseurs' }).getAttribute('href')).toBe('/approvisionnement/admin');

    cleanup();
    mockUser = { is_superadmin: false, permissions: { agenda: true, accounting: true, patients: true, cephalo: true } };
    renderSidebar();
    expect(screen.queryByRole('link', { name: 'Gestion des Dentistes' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Fournisseurs' })).toBeNull();
  });

  it('exposes patient dossier sub-navigation with exact patient id and cephalo permission', () => {
    renderSidebar('/patients/42?tab=analysis');
    expect(screen.getByRole('link', { name: 'Céphalométrie' }).getAttribute('href')).toBe('/patients/42?tab=analysis');
    expect(screen.getByRole('link', { name: 'Documents' }).getAttribute('href')).toBe('/patients/42?tab=admin');
    expect(screen.getByRole('link', { name: 'Archives' }).getAttribute('href')).toBe('/patients/42?tab=archives');
  });

  it('closes the mobile drawer through the backdrop', () => {
    const onClose = vi.fn();
    const { container } = renderSidebar('/dashboard', { isOpen: true, onClose });
    const backdrop = container.querySelector('.fixed.inset-0');
    expect(backdrop).toBeTruthy();
    fireEvent.click(backdrop!);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
  it('gates the AI activity logo pulse by the persisted animation preference', async () => {
    localStorage.setItem('clinical_tips_enabled', 'true');
    renderSidebar();
    const logo = screen.getByAltText('Digital Crown');

    window.dispatchEvent(new Event('ai-generation-start'));
    await waitFor(() => expect(logo.className).toContain('animate-logo-pulse-light'));

    window.dispatchEvent(new Event('ai-generation-end'));
    await waitFor(() => expect(logo.className).not.toContain('animate-logo-pulse-light'));

    cleanup();
    localStorage.setItem('clinical_tips_enabled', 'false');
    renderSidebar();
    const disabledLogo = screen.getByAltText('Digital Crown');
    window.dispatchEvent(new Event('ai-generation-start'));
    await waitFor(() => expect(disabledLogo.className).not.toContain('animate-logo-pulse-light'));
  });

});
