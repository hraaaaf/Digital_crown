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
    availableDocuments: vi.fn(),
    downloadCareSheet: vi.fn(),
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
    vi.mocked(stationPatientSessionService.availableDocuments).mockResolvedValue({ documents: [] });
    vi.mocked(stationPatientSessionService.downloadCareSheet).mockResolvedValue(new Blob(['%PDF-1.4'], { type: 'application/pdf' }));
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

  it('resolves the appointment bridge after QR identity then returns and starts purge', async () => {
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
  it('returns immediately even when server purge remains unavailable', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'identified',
      sessionId: 'session-1',
      displayName: 'Aya Audit',
      claimedAt: new Date().toISOString(),
    });
    vi.mocked(stationPatientSessionService.purge).mockReturnValue(new Promise<void>(() => undefined));
    const onBack = vi.fn();

    render(<StationPatientIdentity onBack={onBack} backLabel='Retour' />);
    expect(await screen.findByText('Identité confirmée')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));

    expect(onBack).toHaveBeenCalledTimes(1);
    expect(stationPatientSessionService.purge).toHaveBeenCalledWith('session-1');
  });

  it('retries session purge up to three times before leaving the patient flow', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'identified',
      sessionId: 'session-1',
      displayName: 'Aya Audit',
      claimedAt: new Date().toISOString(),
    });
    vi.mocked(stationPatientSessionService.purge)
      .mockRejectedValueOnce(new Error('offline-1'))
      .mockRejectedValueOnce(new Error('offline-2'))
      .mockResolvedValueOnce(undefined);
    const onBack = vi.fn();

    render(<StationPatientIdentity onBack={onBack} backLabel='Retour' />);
    expect(await screen.findByText('Identité confirmée')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));

    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledTimes(3));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('still leaves locally after three failed purge attempts so patient data is not left on screen', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'identified',
      sessionId: 'session-1',
      displayName: 'Aya Audit',
      claimedAt: new Date().toISOString(),
    });
    vi.mocked(stationPatientSessionService.purge).mockRejectedValue(new Error('offline'));
    const onBack = vi.fn();

    render(<StationPatientIdentity onBack={onBack} backLabel='Retour' />);
    expect(await screen.findByText('Identité confirmée')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));

    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledTimes(3));
    expect(onBack).toHaveBeenCalledTimes(1);
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


  it('04.4 documents: identifies via QR without invoking appointment arrival or staff signal, and purges on exit', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'identified',
      sessionId: 'session-1',
      displayName: 'Aya Audit',
      claimedAt: new Date().toISOString(),
    });
    const onBack = vi.fn();
    render(<StationPatientIdentity purpose="documents" onBack={onBack} backLabel="Retour" />);

    expect(await screen.findByText('Identité confirmée')).toBeInTheDocument();
    expect(screen.getByText('Aya Audit')).toBeInTheDocument();
    await waitFor(() => expect(stationPatientSessionService.availableDocuments).toHaveBeenCalledWith('session-1'));
    expect(screen.getByText(/personnel du cabinet/i)).toBeInTheDocument();
    expect(screen.queryByText('Confirmer mon arrivée')).toBeNull();
    expect(stationPatientSessionService.todayAppointments).not.toHaveBeenCalled();
    expect(stationPatientSessionService.arrive).not.toHaveBeenCalled();
    expect(stationPatientSessionService.requestStaffAssistance).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(onBack).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledWith('session-1'));
  });

  it('04.5 documents: FR/EN/AR empty eligible list does not advertise printing or Pocket', async () => {
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'identified',
      sessionId: 'session-1',
      displayName: 'Aya Audit',
      claimedAt: new Date().toISOString(),
    });
    for (const [lang, phrase] of [
      ['fr', 'Pour obtenir vos documents, adressez-vous au personnel du cabinet.'],
      ['en', 'Please ask the practice staff for your documents.'],
      ['ar', 'يرجى طلب الوثائق من فريق العيادة.'],
    ] as const) {
      const rendered = render(<StationPatientIdentity purpose="documents" language={lang} onBack={vi.fn()} backLabel="Retour" />);
      expect(await screen.findByText(phrase)).toBeInTheDocument();
      expect(stationPatientSessionService.todayAppointments).not.toHaveBeenCalled();
      rendered.unmount();
    }
  });

  it('revokes a QR created after navigating away before create resolves', async () => {
    let resolveCreate!: (value: Awaited<ReturnType<typeof stationPatientSessionService.create>>) => void;
    vi.mocked(stationPatientSessionService.create).mockReturnValue(
      new Promise(resolve => { resolveCreate = resolve; }),
    );
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'pending', sessionId: 'late-session', expiresAt: new Date(Date.now() + 120_000).toISOString(),
    });
    const onBack = vi.fn();
    const rendered = render(<StationPatientIdentity purpose="documents" onBack={onBack} backLabel="Retour" />);
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    rendered.unmount();
    resolveCreate({
      sessionId: 'late-session',
      handoffUrl: 'https://cabinet.local/companion?stationSession=late',
      nfcPayload: 'https://cabinet.local/companion?stationSession=late',
      qrDataUrl: 'data:image/png;base64,AAAA',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
      fallbackMode: 'disabled',
    });
    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledWith('late-session'));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('revokes a QR created by Retry after leaving, without rendering stale patient identity', async () => {
    vi.mocked(stationPatientSessionService.create).mockRejectedValueOnce(new Error('offline'));
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'pending', sessionId: 'retry-late', expiresAt: new Date(Date.now() + 120_000).toISOString(),
    });
    let resolveRetry!: (value: Awaited<ReturnType<typeof stationPatientSessionService.create>>) => void;
    vi.mocked(stationPatientSessionService.create).mockImplementationOnce(
      () => new Promise(resolve => { resolveRetry = resolve; }),
    );
    const rendered = render(<StationPatientIdentity purpose="documents" onBack={vi.fn()} backLabel="Retour" />);
    fireEvent.click(await screen.findByRole('button', { name: 'Réessayer' }));
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    rendered.unmount();
    resolveRetry({
      sessionId: 'retry-late',
      handoffUrl: 'https://cabinet.local/companion?stationSession=late-retry',
      nfcPayload: 'https://cabinet.local/companion?stationSession=late-retry',
      qrDataUrl: 'data:image/png;base64,AAAA',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
      fallbackMode: 'disabled',
    });
    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledWith('retry-late'));
  });

  it('revokes an older QR response when a newer retry generation wins', async () => {
    let resolveFirst!: (value: Awaited<ReturnType<typeof stationPatientSessionService.create>>) => void;
    vi.mocked(stationPatientSessionService.create).mockImplementationOnce(
      () => new Promise(resolve => { resolveFirst = resolve; }),
    );
    const onBack = vi.fn();
    const rendered = render(<StationPatientIdentity purpose="documents" onBack={onBack} backLabel="Retour" />);
    // The loading state cannot initiate a second creation; navigate away instead.
    rendered.unmount();
    resolveFirst({
      sessionId: 'obsolete-generation',
      handoffUrl: 'https://cabinet.local/companion?stationSession=obsolete',
      nfcPayload: 'https://cabinet.local/companion?stationSession=obsolete',
      qrDataUrl: 'data:image/png;base64,AAAA',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
      fallbackMode: 'disabled',
    });
    await waitFor(() => expect(stationPatientSessionService.purge).toHaveBeenCalledWith('obsolete-generation'));
  });

});
