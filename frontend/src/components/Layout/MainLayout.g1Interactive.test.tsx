import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { MainLayout } from './MainLayout';

const fetchPatientIntelligence = vi.fn();
const fetchProfile = vi.fn();

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
vi.mock('../../features/admin/Settings/hooks/useSettingsStore', () => ({
  useSettingsStore: () => ({ profile: { nom: 'Cabinet', font_fr: 'inter' }, fetchProfile }),
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

beforeEach(() => vi.clearAllMocks());
afterEach(() => cleanup());

describe('MainLayout G1 shell matrix', () => {
  it('opens and closes the mobile sidebar through the shared Menu control', () => {
    renderAt('/dashboard');
    expect(screen.getByText('Sidebar closed')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Menu' }));
    expect(screen.getByText('Sidebar open')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Close sidebar' }));
    expect(screen.getByText('Sidebar closed')).toBeTruthy();
  });

  it('opens and closes floating CrownBot without leaving current page', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir CrownBot' }));
    expect(screen.getByRole('button', { name: 'Close CrownBot' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Close CrownBot' }));
    expect(screen.queryByRole('button', { name: 'Close CrownBot' })).toBeNull();
    expect(screen.getByText('Page content')).toBeTruthy();
  });

  it('enables patient-route header CrownBot and loads exact patient intelligence id', async () => {
    renderAt('/patients/42?tab=admin');

    await waitFor(() => expect(fetchPatientIntelligence).toHaveBeenCalledWith(42));
    expect(screen.getByRole('button', { name: 'Header CrownBot' })).toBeTruthy();
  });

  it('shows practitioner context only on designated shell routes', () => {
    const { unmount } = renderAt('/dashboard');
    expect(screen.getByText('Practitioner context')).toBeTruthy();
    unmount();

    renderAt('/patients');
    expect(screen.queryByText('Practitioner context')).toBeNull();
  });
});
