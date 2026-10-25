import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StationAppointmentArrival } from './StationAppointmentArrival';
import { stationPatientSessionService } from '../../services/stationPatientSession';

vi.mock('../../services/stationPatientSession', () => ({
  stationPatientSessionService: { todayAppointments: vi.fn(), requestStaffAssistance: vi.fn(), arrive: vi.fn() },
}));

describe('StationAppointmentArrival V1.5-03.4', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(stationPatientSessionService.arrive).mockResolvedValue({ status: 'ARRIVED', appointmentId: 1 });
    vi.mocked(stationPatientSessionService.requestStaffAssistance).mockResolvedValue({ status: 'STAFF_NOTIFIED', alertId: 7 });
  });

  it('does not auto-create when no appointment exists', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({ status: 'none', appointments: [], staffActionRequired: true });
    render(<StationAppointmentArrival sessionId="s-1" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    expect(await screen.findByText("Aucun rendez-vous retrouvé aujourd’hui")).toBeInTheDocument();
    expect(await screen.findByText(/L’équipe d’accueil a été prévenue/i)).toBeInTheDocument();
    expect(screen.getByText(/ne crée pas automatiquement de rendez-vous/i)).toBeInTheDocument();
    expect(stationPatientSessionService.requestStaffAssistance).toHaveBeenCalledWith('s-1');
    expect(stationPatientSessionService.arrive).not.toHaveBeenCalled();
  });

  it('fails visibly and tells the visitor to contact reception when staff signaling fails', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({ status: 'none', appointments: [], staffActionRequired: true });
    vi.mocked(stationPatientSessionService.requestStaffAssistance).mockRejectedValue(new Error('offline'));
    render(<StationAppointmentArrival sessionId="s-fail" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/signal n’a pas pu être transmis/i);
    expect(screen.getByRole('alert')).toHaveTextContent(/prévenir directement l’équipe d’accueil/i);
    expect(stationPatientSessionService.arrive).not.toHaveBeenCalled();
  });

  it('preselects a single appointment and confirms explicitly', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'single', staffActionRequired: false,
      appointments: [{ appointmentId: 1, datetimeStart: '2026-10-04T09:30:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' }],
    });
    render(<StationAppointmentArrival sessionId="s-1" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    fireEvent.click(await screen.findByRole('button', { name: 'Confirmer mon arrivée' }));
    await waitFor(() => expect(stationPatientSessionService.arrive).toHaveBeenCalledWith('s-1', 1));
    expect(await screen.findByText('Arrivée confirmée')).toBeInTheDocument();
    expect(screen.getByText(/Aucun numéro de file ni ordre de passage/i)).toBeInTheDocument();
  });

  it('fails closed when arrival write is unavailable', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'single', staffActionRequired: false,
      appointments: [{ appointmentId: 21, datetimeStart: '2026-10-04T09:30:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' }],
    });
    vi.mocked(stationPatientSessionService.arrive).mockRejectedValue(new Error('offline'));

    render(<StationAppointmentArrival sessionId="s-offline" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    fireEvent.click(await screen.findByRole('button', { name: 'Confirmer mon arrivée' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/Arrivée non confirmée/i);
    expect(screen.queryByText('Arrivée confirmée')).toBeNull();
    expect(stationPatientSessionService.arrive).toHaveBeenCalledWith('s-offline', 21);
  });

  it('requires selection when multiple appointments exist', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'multiple', staffActionRequired: false,
      appointments: [
        { appointmentId: 1, datetimeStart: '2026-10-04T09:00:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'PRÉVU' },
        { appointmentId: 2, datetimeStart: '2026-10-04T11:00:00', durationMinutes: 45, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' },
      ],
    });
    vi.mocked(stationPatientSessionService.arrive).mockResolvedValue({ status: 'ARRIVED', appointmentId: 2 });
    render(<StationAppointmentArrival sessionId="s-2" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    const confirm = await screen.findByRole('button', { name: 'Confirmer mon arrivée' });
    expect(confirm).toBeDisabled();
    fireEvent.click(screen.getAllByRole('button').find((button) => button.getAttribute('data-station-appointment-id') === '2')!);
    fireEvent.click(confirm);
    await waitFor(() => expect(stationPatientSessionService.arrive).toHaveBeenCalledWith('s-2', 2));
  });
  it('keeps primary arrival action text high contrast on the station', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'single', staffActionRequired: false,
      appointments: [{ appointmentId: 32, datetimeStart: '2026-10-04T09:30:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' }],
    });
    render(<StationAppointmentArrival sessionId="s-contrast" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    const confirm = await screen.findByRole('button', { name: 'Confirmer mon arrivée' });
    expect(confirm.className).toContain('bg-primary');
    expect(confirm.className).toContain('text-on-primary');
  });

  it('exposes reduced-motion guard on appointment choices', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'single', staffActionRequired: false,
      appointments: [{ appointmentId: 31, datetimeStart: '2026-10-04T09:30:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' }],
    });
    render(<StationAppointmentArrival sessionId="s-motion" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    const choice = await screen.findByRole('button', { name: /09:30.*30 min/i });
    expect(choice.className).toContain('motion-reduce:transition-none');
  });

  it('renders English and Arabic terminal staff-notification copy without falling back to French', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({ status: 'none', appointments: [], staffActionRequired: true });

    const english = render(<StationAppointmentArrival sessionId="s-en" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Back" language="en" />);
    expect(await screen.findByText('Identity confirmed')).toBeInTheDocument();
    expect(await screen.findByText('No appointment found today')).toBeInTheDocument();
    expect(await screen.findByText(/reception team has been notified/i)).toBeInTheDocument();
    expect(screen.queryByText('Identité confirmée')).not.toBeInTheDocument();
    english.unmount();

    render(<StationAppointmentArrival sessionId="s-ar" displayName="Aya Audit" onLeave={vi.fn()} backLabel="العودة" language="ar" />);
    expect(await screen.findByText('تم تأكيد الهوية')).toBeInTheDocument();
    expect(await screen.findByText('لم يتم العثور على موعد اليوم')).toBeInTheDocument();
    expect(await screen.findByText(/تم إبلاغ فريق الاستقبال/)).toBeInTheDocument();
    expect(screen.queryByText('Identité confirmée')).not.toBeInTheDocument();
  });

  it('localizes known appointment statuses and never leaks an unknown raw status', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'multiple', staffActionRequired: false,
      appointments: [
        { appointmentId: 11, datetimeStart: '2026-10-04T09:00:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'PRÉVU' },
        { appointmentId: 12, datetimeStart: '2026-10-04T11:00:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'INTERNAL_FUTURE_STATUS' },
      ],
    });
    const english = render(<StationAppointmentArrival sessionId="s-status-en" displayName="Aya" onLeave={vi.fn()} backLabel="Back" language="en" />);
    expect(await screen.findByText(/Status : Scheduled/)).toBeInTheDocument();
    expect(screen.queryByText(/PRÉVU/)).not.toBeInTheDocument();
    expect(screen.queryByText(/INTERNAL_FUTURE_STATUS/)).not.toBeInTheDocument();
    english.unmount();

    render(<StationAppointmentArrival sessionId="s-status-ar" displayName="Aya" onLeave={vi.fn()} backLabel="العودة" language="ar" />);
    expect(await screen.findByText(/الحالة : مجدول/)).toBeInTheDocument();
    expect(screen.queryByText(/PRÉVU/)).not.toBeInTheDocument();
    expect(screen.queryByText(/INTERNAL_FUTURE_STATUS/)).not.toBeInTheDocument();
  });

  it('A3-03 prevents a second arrival confirmation while the first HTTP write is pending', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'single', staffActionRequired: false,
      appointments: [{ appointmentId: 51, datetimeStart: '2026-10-25T09:30:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' }],
    });
    let resolveArrival!: (value: { status: 'ARRIVED'; appointmentId: number }) => void;
    vi.mocked(stationPatientSessionService.arrive).mockReturnValue(
      new Promise(resolve => { resolveArrival = resolve; }),
    );
    render(<StationAppointmentArrival sessionId="a3-synthetic" displayName="Patient fictif" onLeave={vi.fn()} backLabel="Retour" />);
    const confirm = await screen.findByRole('button', { name: 'Confirmer mon arrivée' });
    fireEvent.click(confirm);
    expect(await screen.findByRole('button', { name: 'Confirmation…' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmation…' }));
    expect(stationPatientSessionService.arrive).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('Arrivée confirmée')).toBeNull();
    resolveArrival({ status: 'ARRIVED', appointmentId: 51 });
    expect(await screen.findByText('Arrivée confirmée')).toBeInTheDocument();
    expect(stationPatientSessionService.arrive).toHaveBeenCalledTimes(1);
  });

  it('A3-04 never claims arrival after a rejected write and permits explicit retry', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({
      status: 'single', staffActionRequired: false,
      appointments: [{ appointmentId: 52, datetimeStart: '2026-10-25T10:30:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' }],
    });
    vi.mocked(stationPatientSessionService.arrive)
      .mockRejectedValueOnce(new Error('network offline'))
      .mockResolvedValueOnce({ status: 'ARRIVED', appointmentId: 52 });
    render(<StationAppointmentArrival sessionId="a3-retry-synthetic" displayName="Patient fictif" onLeave={vi.fn()} backLabel="Retour" />);
    fireEvent.click(await screen.findByRole('button', { name: 'Confirmer mon arrivée' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Arrivée non confirmée');
    expect(screen.queryByText('Arrivée confirmée')).toBeNull();
    expect(stationPatientSessionService.arrive).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer mon arrivée' }));
    expect(await screen.findByText('Arrivée confirmée')).toBeInTheDocument();
    expect(stationPatientSessionService.arrive).toHaveBeenCalledTimes(2);
  });

  it('A3-11 does not let a late previous-session appointment response replace the new patient session', async () => {
    let resolveOld!: (value: Awaited<ReturnType<typeof stationPatientSessionService.todayAppointments>>) => void;
    const old = new Promise<Awaited<ReturnType<typeof stationPatientSessionService.todayAppointments>>>(resolve => { resolveOld = resolve; });
    vi.mocked(stationPatientSessionService.todayAppointments).mockImplementation(session =>
      session === 'session-old'
        ? old
        : Promise.resolve({
            status: 'single', staffActionRequired: false,
            appointments: [{ appointmentId: 74, datetimeStart: '2026-10-25T09:40:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ' }],
          }),
    );
    const show = (sessionId: string) => <StationAppointmentArrival sessionId={sessionId} displayName="Patient fictif" onLeave={vi.fn()} backLabel="Retour" />;
    const view = render(show('session-old'));
    view.rerender(show('session-new'));
    expect(await screen.findByRole('button', { name: 'Confirmer mon arrivée' })).toBeEnabled();
    await act(async () => {
      resolveOld({ status: 'none', staffActionRequired: false, appointments: [] });
      await Promise.resolve();
    });
    expect(screen.getByRole('button', { name: 'Confirmer mon arrivée' })).toBeEnabled();
    expect(screen.queryByText('Aucun rendez-vous retrouvé aujourd’hui')).toBeNull();
    expect(stationPatientSessionService.requestStaffAssistance).not.toHaveBeenCalled();
  });

  it('A3-11 ignores a late arrival acknowledgement after changing the patient session', async () => {
    let releaseArrival!: (value: { status: 'ARRIVED'; appointmentId: number }) => void;
    vi.mocked(stationPatientSessionService.arrive).mockReturnValue(
      new Promise(resolve => { releaseArrival = resolve; }),
    );
    vi.mocked(stationPatientSessionService.todayAppointments).mockImplementation(session => Promise.resolve({
      status: 'single', staffActionRequired: false,
      appointments: [{
        appointmentId: session === 'session-1' ? 71 : 72,
        datetimeStart: '2026-10-25T09:40:00', durationMinutes: 30, schedulingType: 'EXACT_TIME', status: 'CONFIRMÉ',
      }],
    }));
    const show = (sessionId: string) => <StationAppointmentArrival sessionId={sessionId} displayName="Patient fictif" onLeave={vi.fn()} backLabel="Retour" />;
    const view = render(show('session-1'));
    fireEvent.click(await screen.findByRole('button', { name: 'Confirmer mon arrivée' }));
    await waitFor(() => expect(stationPatientSessionService.arrive).toHaveBeenCalledWith('session-1', 71));
    view.rerender(show('session-2'));
    expect(await screen.findByRole('button', { name: 'Confirmer mon arrivée' })).toBeEnabled();
    await act(async () => {
      releaseArrival({ status: 'ARRIVED', appointmentId: 71 });
      await Promise.resolve();
    });
    expect(screen.queryByText('Arrivée confirmée')).toBeNull();
    expect(screen.getByRole('button', { name: 'Confirmer mon arrivée' })).toBeEnabled();
  });

});
