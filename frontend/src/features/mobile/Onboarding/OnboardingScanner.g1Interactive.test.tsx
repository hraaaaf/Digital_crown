import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { OnboardingScanner, resolveBridgeRoute } from './OnboardingScanner';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { deriveMasterKey, generateClientKeyPair, hasPlaintextMasterKey } from '../../../services/zka/ecdhPairing';

vi.mock('html5-qrcode', () => ({
  Html5QrcodeSupportedFormats: { QR_CODE: 0 },
  Html5QrcodeScanner: vi.fn().mockImplementation(() => ({
    render: vi.fn(),
    clear: vi.fn().mockResolvedValue(undefined),
  })),
}));

vi.mock('../../../hooks/usePWAInstall', () => ({
  usePWAInstall: () => ({ isIOS: false, isInstalled: true }),
}));

vi.mock('../../../services/zka/MobileStorage', () => ({
  MobileStorage: {
    saveCredentials: vi.fn(),
    saveBridgeContext: vi.fn(),
    clearBridgeContext: vi.fn(),
    clearAll: vi.fn(),
  },
}));

vi.mock('../../../services/zka/ecdhPairing', () => ({
  generateClientKeyPair: vi.fn(),
  deriveMasterKey: vi.fn(),
  hasPlaintextMasterKey: vi.fn(),
}));

function renderScanner(entry = '/mobile/onboarding') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/mobile/onboarding" element={<OnboardingScanner />} />
        <Route path="/mobile/dashboard" element={<div>Mobile dashboard destination</div>} />
        <Route path="/mobile/context" element={<div>Mobile context destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function response(ok: boolean, status: number, payload: unknown) {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
  localStorage.clear();

  Object.defineProperty(window, 'isSecureContext', { configurable: true, value: true });
  vi.mocked(generateClientKeyPair).mockResolvedValue({
    privateKey: {} as CryptoKey,
    publicKeyHex: 'client-key',
  });
  vi.mocked(deriveMasterKey).mockResolvedValue('a'.repeat(64));
  vi.mocked(hasPlaintextMasterKey).mockReturnValue(false);
  vi.mocked(MobileStorage.saveCredentials).mockResolvedValue(undefined);
  vi.mocked(MobileStorage.saveBridgeContext).mockResolvedValue(undefined);
  vi.mocked(MobileStorage.clearBridgeContext).mockResolvedValue(undefined);
  vi.mocked(MobileStorage.clearAll).mockResolvedValue(undefined);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('OnboardingScanner G1 interactive matrix', () => {
  it('keeps manual OK disabled until exactly six numeric digits and strips non-digits', () => {
    renderScanner();

    const input = screen.getByLabelText("Code d'appairage à 6 chiffres") as HTMLInputElement;
    const ok = screen.getByRole('button', { name: "Valider le code d'appairage" }) as HTMLButtonElement;
    expect(ok.disabled).toBe(true);

    fireEvent.change(input, { target: { value: '12a34b56x7' } });
    expect(input.value).toBe('123456');
    expect(ok.disabled).toBe(false);
  });

  it('maps only known bridge destinations and fails closed to agenda', () => {
    expect(resolveBridgeRoute('finance')).toBe('/mobile/dashboard?tab=finance');
    expect(resolveBridgeRoute('context')).toBe('/mobile/context');
    expect(resolveBridgeRoute('unknown')).toBe('/mobile/dashboard?tab=agenda');
    expect(resolveBridgeRoute(null)).toBe('/mobile/dashboard?tab=agenda');
  });

  it('claims a manual token, stores derived credentials and shows true pairing success', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(true, 200, {
        publicId: 'a'.repeat(16),
        access_token: 'access',
        refresh_token: 'refresh',
        device_id: 'device',
        server_public_key_hex: 'server-key',
        encrypted_master_key_hex: 'encrypted-key',
      }))
      .mockResolvedValueOnce(response(false, 404, {}))
      .mockResolvedValueOnce(response(true, 200, { destination: 'finance' }));
    vi.stubGlobal('fetch', fetchMock);

    renderScanner();
    fireEvent.change(screen.getByLabelText("Code d'appairage à 6 chiffres"), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: "Valider le code d'appairage" }));

    expect(await screen.findByText('Appairage réussi')).toBeTruthy();
    expect(screen.getByText('Finance')).toBeTruthy();
    expect(MobileStorage.saveCredentials).toHaveBeenCalledWith(expect.objectContaining({
      publicId: 'a'.repeat(16),
      masterKey: 'a'.repeat(64),
      access_token: 'access',
      refresh_token: 'refresh',
      device_id: 'device',
    }));
    expect(MobileStorage.clearBridgeContext).toHaveBeenCalledTimes(1);
  });

  it('surfaces backend claim refusal and Retry restores the welcome state without false success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(
      response(false, 401, { detail: 'Code expiré.' }),
    ));

    renderScanner();
    fireEvent.change(screen.getByLabelText("Code d'appairage à 6 chiffres"), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: "Valider le code d'appairage" }));

    expect(await screen.findByText("Échec de l'appairage")).toBeTruthy();
    expect(screen.getByText('Code expiré.')).toBeTruthy();
    expect(screen.queryByText('Appairage réussi')).toBeNull();
    expect(MobileStorage.saveCredentials).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    expect(await screen.findByText('Compagnon Mobile')).toBeTruthy();
  });

  it('refuses plaintext master-key pairing payloads before persistence', async () => {
    vi.mocked(hasPlaintextMasterKey).mockReturnValue(true);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(true, 200, {
      publicId: 'a'.repeat(16),
      access_token: 'access',
      refresh_token: 'refresh',
      device_id: 'device',
      server_public_key_hex: 'server-key',
      encrypted_master_key_hex: 'encrypted-key',
      masterKey: 'forbidden',
    })));

    renderScanner();
    fireEvent.change(screen.getByLabelText("Code d'appairage à 6 chiffres"), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: "Valider le code d'appairage" }));

    expect(await screen.findByText(/masterKey en clair refusee/i)).toBeTruthy();
    expect(MobileStorage.saveCredentials).not.toHaveBeenCalled();
  });
});
