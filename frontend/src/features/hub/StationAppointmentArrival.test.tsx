import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

});
