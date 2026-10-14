import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MobileBiometricGate } from './MobileBiometricGate';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { getMobilePasskeyStatus, isStablePasskeyOrigin, unlockMobilePasskey } from '../../../services/zka/mobilePasskey';

vi.mock('../../../services/zka/MobileStorage', () => ({
  MobileStorage: {
    getBiometricVaultEnvelope: vi.fn(),
    isBiometricVaultUnlocked: vi.fn(),
    getBiometricAccessToken: vi.fn(),
    lockBiometricVault: vi.fn(),
  },
}));

vi.mock('../../../services/zka/mobilePasskey', () => ({
  getMobilePasskeyStatus: vi.fn(),
  isStablePasskeyOrigin: vi.fn(),
  unlockMobilePasskey: vi.fn(),
}));

const disabledStatus = {
  state: 'disabled' as const,
  credential_id: null, rp_id: 'digitalcrown.local',
  expected_origin: 'https://digitalcrown.local:8005',
  origin_ready: true, user_verification: 'required' as const, server_gate: false,
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getMobilePasskeyStatus).mockResolvedValue(disabledStatus);
  vi.mocked(MobileStorage.getBiometricVaultEnvelope).mockResolvedValue(null);
  vi.mocked(MobileStorage.isBiometricVaultUnlocked).mockResolvedValue(false);
  vi.mocked(MobileStorage.getBiometricAccessToken).mockReturnValue(null);
  vi.mocked(isStablePasskeyOrigin).mockReturnValue(true);
});

afterEach(() => cleanup());

describe('mobile biometric gate at first paired Safari navigation', () => {
  it('allows a properly paired device when no passkey is enrolled', async () => {
    render(<MobileBiometricGate><div>Agenda vraiment chargé</div></MobileBiometricGate>);
    expect(await screen.findByText('Agenda vraiment chargé')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Déverrouiller' })).toBeNull();
  });

  it('does not advertise Face ID when a real server passkey requires a missing local vault', async () => {
    vi.mocked(getMobilePasskeyStatus).mockResolvedValue({
      ...disabledStatus, state: 'enabled', credential_id: 'server-passkey', server_gate: true,
    });
    render(<MobileBiometricGate><div>PRIVATE AGENDA</div></MobileBiometricGate>);
    expect(await screen.findByText('Accès mobile protégé')).toBeTruthy();
    expect(screen.queryByText('PRIVATE AGENDA')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Déverrouiller' })).toBeNull();
    expect(screen.getByRole('alert').textContent).toContain('Coffre biométrique absent');
    expect(unlockMobilePasskey).not.toHaveBeenCalled();
  });

  it('fails closed when a canonical lock event arrives without a local vault', async () => {
    render(<MobileBiometricGate><div>PRIVATE AGENDA</div></MobileBiometricGate>);
    await screen.findByText('PRIVATE AGENDA');
    window.dispatchEvent(new CustomEvent('digitalcrown:mobile-biometric-locked'));
    await waitFor(() => expect(screen.getByText('Accès mobile protégé')).toBeTruthy());
    expect(screen.queryByText('PRIVATE AGENDA')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Déverrouiller' })).toBeNull();
    expect(MobileStorage.lockBiometricVault).toHaveBeenCalledOnce();
  });

  it('keeps the working Face ID unlock path for an existing sealed passkey vault', async () => {
    vi.mocked(getMobilePasskeyStatus).mockResolvedValue({
      ...disabledStatus, state: 'enabled', credential_id: 'server-passkey', server_gate: true,
    });
    vi.mocked(MobileStorage.getBiometricVaultEnvelope).mockResolvedValue({ credential_id: 'server-passkey' } as any);
    render(<MobileBiometricGate><div>PRIVATE AGENDA</div></MobileBiometricGate>);
    expect(await screen.findByRole('button', { name: 'Déverrouiller' })).toBeTruthy();
    expect(screen.queryByText('PRIVATE AGENDA')).toBeNull();
  });

  it('preserves Security recovery for an unfinished passkey enrollment', async () => {
    vi.mocked(getMobilePasskeyStatus).mockResolvedValue({
      ...disabledStatus, state: 'pending', credential_id: 'pending-passkey',
    });
    render(<MobileBiometricGate><div>Sécurité en attente</div></MobileBiometricGate>);
    expect(await screen.findByText('Sécurité en attente')).toBeTruthy();
  });
});
