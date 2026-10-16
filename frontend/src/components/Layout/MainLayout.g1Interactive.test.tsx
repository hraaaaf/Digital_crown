import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { MainLayout } from './MainLayout';

const fetchPatientIntelligence = vi.fn();
const fetchProfile = vi.fn();
let mockUser: any = { is_superadmin: false, nom_complet: 'Owner', role: 'DENTISTE', employer_id: null };
let mockProfile: any = { nom: 'Cabinet', font_fr: 'inter' };

vi.mock('../Sidebar', () => ({
  Sidebar: ({ isOpen, onClose }: { isOpen?: boolean; onClose?: () => void }) => (
    <div>
      <span>{isOpen ? 'Sidebar open' : 'Sidebar closed'}</span>
      {isOpen ? <button onClick={onClose}>Close sidebar</button> : null}
    </div>
  ),
}));

vi.mock('../Header', () => ({
  Header: ({ onToggleCrownBot }: { onToggleCrownBot?: () => void }) => (
    <div>{onToggleCrownBot ? <button onClick={onToggleCrownBot}>Header CrownBot</button> : null}</div>
  ),
}));

vi.mock('../LicenseBanner', () => ({ LicenseBanner: () => null }));
vi.mock('../AnimatedBackground', () => ({ AnimatedBackground: () => null }));
vi.mock('../CrownBot/CrownBotChat', () => ({
  CrownBotChat: ({ onClose }: { onClose: () => void }) => <button onClick={onClose}>Close CrownBot</button>,
}));
vi.mock('../../features/tutorial/VoluntaryTutorial', () => ({ VoluntaryTutorialPanel: () => null }));
vi.mock('../../features/clinic/ClinicPractitionerBar', () => ({ ClinicPractitionerBar: () => <div>Practitioner context</div> }));
vi.mock('../../stores/useEliteStore', () => ({ useEliteStore: () => ({ fetchPatientIntelligence }) }));
vi.mock('../../stores/useAuthStore', () => ({ useAuthStore: () => ({ user: mockUser }) }));
vi.mock('../../features/admin/Settings/hooks/useSettingsStore', () => ({
  useSettingsStore: () => ({ profile: mockProfile, fetchProfile }),
}));
vi.mock('../../hooks/useLocalStorage', () => ({ safeStorage: { get: vi.fn(() => 'false') } }));
vi.mock('../../features/admin/constants', () => ({ PREMIUM_FONTS: [{ id: 'inter', class: 'font-sans' }] }));

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="*" element={<MainLayout><div>Page content</div></MainLayout>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockUser = { is_superadmin: false, nom_complet: 'Owner', role: 'DENTISTE', employer_id: null };
  mockProfile = { nom: 'Cabinet', font_fr: 'inter' };
});
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

function simulateViewport(wide: boolean) {
  const matches = wide;
  vi.stubGlobal('matchMedia', vi.fn(() => ({
    matches, media: '(min-width: 1280px)', addEventListener: vi.fn(),
    removeEventListener: vi.fn(), addListener: vi.fn(), removeListener: vi.fn(),
  })));
}

describe('MainLayout G1 shell matrix', () => {
  it('opens and closes the mobile sidebar through the shared Menu control', () => {
    renderAt('/dashboard');
    expect(screen.getByText('Sidebar closed')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Menu' }));
    expect(screen.getByText('Sidebar open')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Close sidebar' }));
    expect(screen.getByText('Sidebar closed')).toBeTruthy();
  });

  it('opens and closes floating CrownBot without leaving current page', async () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir CrownBot' }));
    expect(screen.getByRole('button', { name: 'Close CrownBot' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Close CrownBot' }));
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Close CrownBot' })).toBeNull());
    expect(screen.getByText('Page content')).toBeTruthy();
  });

  it('enables patient-route header CrownBot and loads exact patient intelligence id', async () => {
    renderAt('/patients/42?tab=admin');

    await waitFor(() => expect(fetchPatientIntelligence).toHaveBeenCalledWith(42));
    expect(screen.getByRole('button', { name: 'Header CrownBot' })).toBeTruthy();
  });

  it('does not fetch settings profile for a restricted shell user', async () => {
    mockUser = {
      is_superadmin: false,
      nom_complet: 'Restricted',
      role: 'SECRETAIRE',
      employer_id: 1,
      permissions: { settings: false },
    };
    mockProfile = { nom: '', font_fr: 'inter' };
    renderAt('/dashboard');
    await waitFor(() => expect(fetchProfile).not.toHaveBeenCalled());
  });

  it('fetches settings profile for an owner when profile is missing', async () => {
    mockProfile = { nom: '', font_fr: 'inter' };
    renderAt('/dashboard');
    await waitFor(() => expect(fetchProfile).toHaveBeenCalledTimes(1));
  });

  it('shows practitioner context only on designated shell routes', () => {
    const { unmount } = renderAt('/dashboard');
    expect(screen.getByText('Practitioner context')).toBeTruthy();
    unmount();

    renderAt('/patients');
    expect(screen.queryByText('Practitioner context')).toBeNull();
  });
});


describe('CB-01 Associate Sidecar: double gating and no hidden duplicate', () => {
  it('keeps original floating view when new flag is OFF, even on desktop', () => {
    vi.stubEnv('VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED', 'false');
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    simulateViewport(true);
    const result = renderAt('/dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir CrownBot' }));
    expect(result.container.querySelector('[data-cb01-associate-sidecar]')).toBeNull();
    expect(result.container.querySelector('[data-ux1-c-crownbot-overlay]')).toBeTruthy();
    expect(screen.getAllByRole('button', { name: 'Close CrownBot' })).toHaveLength(1);
  });

  it('keeps floating fallback on narrow web screens; not Pocket', () => {
    vi.stubEnv('VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED', 'true');
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    simulateViewport(false);
    const result = renderAt('/dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir CrownBot' }));
    expect(result.container.querySelector('[data-cb01-associate-sidecar]')).toBeNull();
    expect(result.container.querySelector('[data-ux1-c-crownbot-overlay]')).toBeTruthy();
    expect(screen.getByText('Page content')).toBeTruthy();
  });

  it('renders exactly one accessible reflow sidecar at desktop and can collapse', () => {
    vi.stubEnv('VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED', 'true');
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    simulateViewport(true);
    const result = renderAt('/patients/42');
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir CrownBot' }));
    expect(result.container.querySelector('[data-cb01-associate-sidecar]')).toBeTruthy();
    expect(result.container.querySelector('[data-ux1-c-crownbot-overlay]')).toBeNull();
    expect(screen.getByRole('complementary', {
      name: 'Crown Bot — assistant latéral expérimental',
    })).toBeTruthy();
    expect(screen.getAllByRole('button', { name: 'Close CrownBot' })).toHaveLength(1);
    expect(screen.getByText('Page content')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Réduire le panneau Crown Bot' }));
    expect(result.container.querySelector('[data-cb01-associate-sidecar]')).toBeNull();
    expect(screen.getByText('Page content')).toBeTruthy();
  });

  it('requires the prior safe preview flag even when sidecar is opted in', () => {
    vi.stubEnv('VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED', 'true');
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'false');
    simulateViewport(true);
    const result = renderAt('/dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir CrownBot' }));
    expect(result.container.querySelector('[data-cb01-associate-sidecar]')).toBeNull();
    expect(result.container.querySelector('[data-ux1-c-crownbot-overlay]')).toBeTruthy();
  });
});
