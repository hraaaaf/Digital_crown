import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import SettingsContainer from './SettingsContainer';
import { api } from '../../../services/api';

const state = vi.hoisted(() => ({
  user: {
    id: 1,
    role: 'ADMIN',
    employer_id: null as number | null,
    is_superadmin: false,
    permissions: {} as Record<string, boolean>,
  } as any,
  settings: {
    loading: false,
    saving: false,
    saveSuccess: false,
    isDirty: false,
    fetchProfile: vi.fn(),
    saveProfile: vi.fn(),
  },
  responseReject: null as null | ((error: any) => Promise<never>),
}));

vi.mock('../../../stores/useAuthStore', () => ({
  useAuthStore: (selector: (s: { user: typeof state.user }) => unknown) => selector({ user: state.user }),
}));

vi.mock('./hooks/useSettingsStore', () => ({
  useSettingsStore: () => state.settings,
}));

vi.mock('../../../services/api', () => ({
  api: {
    interceptors: {
      response: {
        use: vi.fn((_ok: any, reject: any) => {
          state.responseReject = reject;
          return 11;
        }),
        eject: vi.fn(),
      },
    },
  },
}));

vi.mock('./tabs/ProfileTab', () => ({ ProfileTab: () => <div>Profile surface</div> }));
vi.mock('./tabs/BrandingTab', () => ({ BrandingTab: () => <div>Branding surface</div> }));
vi.mock('./tabs/CatalogTab', () => ({ CatalogTab: () => <div>Catalog surface</div> }));
vi.mock('./tabs/AgendaTab', () => ({ AgendaTab: () => <div>Agenda surface</div> }));
vi.mock('./tabs/IATab', () => ({ IATab: () => <div>IA surface</div> }));
vi.mock('./tabs/SecurityTab', () => ({ SecurityTab: () => <div>Security surface</div> }));
vi.mock('./components/TeamReadTruthGate', () => ({ TeamReadTruthGate: () => <div>Team surface</div> }));
vi.mock('../../../components/DigitalCrownLoader', () => ({
  DigitalCrownLoader: ({ text }: { text: string }) => <div>{text}</div>,
}));

beforeEach(() => {
  vi.clearAllMocks();
  state.user.role = 'ADMIN';
  state.user.employer_id = null;
  state.user.is_superadmin = false;
  state.user.permissions = {};
  state.settings.loading = false;
  state.settings.saving = false;
  state.settings.saveSuccess = false;
  state.settings.isDirty = false;
  state.settings.fetchProfile.mockResolvedValue(undefined);
  state.settings.saveProfile.mockResolvedValue(undefined);
  state.responseReject = null;
});

afterEach(() => cleanup());

describe('SettingsContainer G5 shell matrix', () => {
  it('exposes all cabinet settings tabs to an owner/admin and switches real surfaces', async () => {
    render(<SettingsContainer />);
    await waitFor(() => expect(state.settings.fetchProfile).toHaveBeenCalled());

    for (const label of [
      'Profil Cabinet',
      'Design & Ambiance',
      'Catalogue Actes',
      'Horaires & Agenda',
      'Performance & Assistance',
      'Sécurité & Backup',
      'Mon Équipe',
    ]) {
      expect(screen.getByRole('button', { name: label })).toBeTruthy();
    }

    fireEvent.click(screen.getByRole('button', { name: 'Sécurité & Backup' }));
    expect(screen.getByText('Security surface')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Mon Équipe' }));
    expect(screen.getByText('Team surface')).toBeTruthy();
  });

  it('shows only Agenda to a secretary with legacy/default agenda access and no settings/admin access', async () => {
    state.user.role = 'SECRETAIRE';
    state.user.employer_id = 1;
    state.user.permissions = {};
    render(<SettingsContainer />);

    expect(await screen.findByRole('button', { name: 'Horaires & Agenda' })).toBeTruthy();
    expect(screen.getByText('Agenda surface')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Profil Cabinet' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Sécurité & Backup' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Mon Équipe' })).toBeNull();
  });

  it('shows the shared save bar only for dirty profile-backed configuration and saves explicitly', async () => {
    state.settings.isDirty = true;
    render(<SettingsContainer />);

    expect(await screen.findByTestId('settings-save-bar')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer la configuration' }));
    await waitFor(() => expect(state.settings.saveProfile).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole('button', { name: 'Catalogue Actes' }));
    expect(screen.getByText('Catalog surface')).toBeTruthy();
    expect(screen.queryByTestId('settings-save-bar')).toBeNull();
    expect(screen.getByTestId('settings-pending-config-notice')).toBeTruthy();
  });

  it('fails closed on /clinics/me read error and retries before allowing profile-backed editing', async () => {
    render(<SettingsContainer />);
    await waitFor(() => expect(state.responseReject).toBeTypeOf('function'));

    await state.responseReject!({
      config: { url: '/clinics/me', method: 'get' },
      response: { status: 500 },
    }).catch(() => undefined);

    expect(await screen.findByText('Profil indisponible')).toBeTruthy();
    expect(screen.queryByText('Profile surface')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(state.settings.fetchProfile).toHaveBeenCalledTimes(2));
  });

  it('preserves dirty state when shared save fails', async () => {
    state.settings.isDirty = true;
    state.settings.saveProfile.mockRejectedValueOnce(new Error('save refused'));
    render(<SettingsContainer />);

    fireEvent.click(await screen.findByRole('button', { name: 'Enregistrer la configuration' }));
    await waitFor(() => expect(state.settings.saveProfile).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId('settings-save-bar')).toBeTruthy();
  });
});
