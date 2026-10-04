import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StationPatientIdentity } from './StationPatientIdentity';
import { stationPatientSessionService } from '../../services/stationPatientSession';

vi.mock('../../services/stationPatientSession', () => ({
  stationPatientSessionService: {
    create: vi.fn(),
    status: vi.fn(),
    fallback: vi.fn(),
    purge: vi.fn(),
  },
}));

describe('StationPatientIdentity V1.5-03.3', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(stationPatientSessionService.create).mockResolvedValue({
      sessionId: 'session-1',
      handoffUrl: 'https://cabinet.local/companion?stationSession=opaque-token',
      nfcPayload: 'https://cabinet.local/companion?stationSession=opaque-token',
      qrDataUrl: 'data:image/png;base64,AAAA',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
      fallbackMode: 'phone_dob',
    });
    vi.mocked(stationPatientSessionService.purge).mockResolvedValue(undefined);
  });

  it('shows one-shot QR/NFC handoff and never claims arrival', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'pending',
      sessionId: 'session-1',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
    });

    render(<StationPatientIdentity onBack={vi.fn()} backLabel='Retour' />);

    expect(await screen.findByAltText('QR d’identification Patient Companion')).toHaveAttribute(
      'src',
      'data:image/png;base64,AAAA',
    );
    expect(screen.getByText(/NFC utilise le même lien sécurisé/i)).toBeInTheDocument();
    expect(screen.queryByText(/ARRIVED/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/file d’attente/i)).not.toBeInTheDocument();
  });

  it('uses configured phone + birth date fallback with a generic failure surface', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'pending',
      sessionId: 'session-1',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
    });
    vi.mocked(stationPatientSessionService.fallback).mockResolvedValue({
      status: 'identified',
      sessionId: 'session-1',
      displayName: 'Aya Audit',
    });

    render(<StationPatientIdentity onBack={vi.fn()} backLabel='Retour' />);
    await screen.findByAltText('QR d’identification Patient Companion');

    fireEvent.click(screen.getByRole('button', { name: 'Je n’ai pas mon téléphone' }));
    fireEvent.change(screen.getByLabelText('Téléphone'), { target: { value: '+212612345678' } });
    fireEvent.change(screen.getByLabelText('Date de naissance'), { target: { value: '1992-05-04' } });
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer mon identité' }));

    await waitFor(() => expect(stationPatientSessionService.fallback).toHaveBeenCalledWith(
      'session-1',
      { birthDate: '1992-05-04', phone: '+212612345678' },
    ));
    expect(await screen.findByText('Aya Audit')).toBeInTheDocument();
    expect(screen.getByText('Aucune arrivée n’a encore été enregistrée.')).toBeInTheDocument();
  });

  it('renders identified proof then purges before returning', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'identified',
      sessionId: 'session-1',
      displayName: 'Aya Audit',
      claimedAt: new Date().toISOString(),
    });
    const onBack = vi.fn();

    render(<StationPatientIdentity onBack={onBack} backLabel='Retour' />);

    expect(await screen.findByText('Identité confirmée')).toBeInTheDocument();
    expect(screen.getByText('Aya Audit')).toBeInTheDocument();
    expect(screen.getByText('Aucune arrivée n’a encore été enregistrée.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledWith('session-1'));
    expect(onBack).toHaveBeenCalled();
  });
});
