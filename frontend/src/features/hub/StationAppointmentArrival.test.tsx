import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StationAppointmentArrival } from './StationAppointmentArrival';
import { stationPatientSessionService } from '../../services/stationPatientSession';

vi.mock('../../services/stationPatientSession', () => ({
  stationPatientSessionService: { todayAppointments: vi.fn(), arrive: vi.fn() },
}));

describe('StationAppointmentArrival V1.5-03.4', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(stationPatientSessionService.arrive).mockResolvedValue({ status: 'ARRIVED', appointmentId: 1 });
  });

  it('does not auto-create when no appointment exists', async () => {
    vi.mocked(stationPatientSessionService.todayAppointments).mockResolvedValue({ status: 'none', appointments: [], staffActionRequired: true });
    render(<StationAppointmentArrival sessionId="s-1" displayName="Aya Audit" onLeave={vi.fn()} backLabel="Retour" />);
    expect(await screen.findByText("Aucun rendez-vous retrouvé aujourd’hui")).toBeInTheDocument();
    expect(screen.getByText(/ne crée pas automatiquement de rendez-vous/i)).toBeInTheDocument();
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
    fireEvent.click(screen.getByRole('button', { name: /11:00 · 45 min/i }));
    fireEvent.click(confirm);
    await waitFor(() => expect(stationPatientSessionService.arrive).toHaveBeenCalledWith('s-2', 2));
  });
});
