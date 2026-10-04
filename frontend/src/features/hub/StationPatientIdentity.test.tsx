import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StationPatientIdentity } from './StationPatientIdentity';
import { stationPatientSessionService } from '../../services/stationPatientSession';

vi.mock('../../services/stationPatientSession', () => ({
  stationPatientSessionService: {
    create: vi.fn(),
    status: vi.fn(),
    fallback: vi.fn(),
    todayAppointments: vi.fn(),
    arrive: vi.fn(),
    purge: vi.fn(),
    requestStaffAssistance: vi.fn(),
  },
}));

describe('StationPatientIdentity V1.5-03.3/03.4', () => {
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
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'none',
      appointments: [],
      staffActionRequired: true,
    });
    vi.mocked(stationPatientSessionService.purge).mockResolvedValue(undefined);
    vi.mocked(stationPatientSessionService.requestStaffAssistance).mockResolvedValue({ status: 'STAFF_NOTIFIED', alertId: 7 });
  });

  it('shows one-shot QR/NFC handoff and never claims arrival before identification', async () => {
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
  });

  it('uses configured phone + birth date fallback then resolves today only after identity', async () => {
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
    await waitFor(() => expect(stationPatientSessionService.todayAppointments).toHaveBeenCalledWith('session-1'));
    expect(await screen.findByText("Aucun rendez-vous retrouvé aujourd’hui")).toBeInTheDocument();
  });

  it('resolves the appointment bridge after QR identity then purges before returning', async () => {
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
    expect(await screen.findByText("Aucun rendez-vous retrouvé aujourd’hui")).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledWith('session-1'));
    expect(onBack).toHaveBeenCalled();
  });
  it('localizes pending identity UI in English and Arabic', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'pending',
      sessionId: 'session-1',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
    });

    const english = render(<StationPatientIdentity onBack={vi.fn()} backLabel='Back' language='en' />);
    expect(await screen.findByAltText('Patient Companion identification QR code')).toBeInTheDocument();
    expect(screen.getByText('Scan with your phone')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'I do not have my phone' })).toBeInTheDocument();
    english.unmount();

    render(<StationPatientIdentity onBack={vi.fn()} backLabel='العودة' language='ar' />);
    expect(await screen.findByAltText('رمز QR للتعرّف عبر Patient Companion')).toBeInTheDocument();
    expect(screen.getByText('امسحوا الرمز بهاتفكم')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'ليس لدي هاتفي' })).toBeInTheDocument();
  });

});
