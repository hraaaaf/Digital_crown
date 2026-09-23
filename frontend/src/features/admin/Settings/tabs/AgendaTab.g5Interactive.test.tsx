import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AgendaTab } from './AgendaTab';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

vi.mock('react-hot-toast', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock('./PractitionerAvailabilityPanel', () => ({
  PractitionerAvailabilityPanel: () => <div>Practitioner availability</div>,
}));

const weekly = Object.fromEntries(
  ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'].map(day => [day, {
    is_open: true,
    is_continuous: false,
    morning_start: '09:00',
    morning_end: '13:00',
    afternoon_start: '14:00',
    afternoon_end: '18:00',
  }]),
);

const settings = {
  opening_time_morning: '09:00',
  closing_time_morning: '13:00',
  opening_time_afternoon: '14:00',
  closing_time_afternoon: '18:00',
  is_continuous: false,
  agenda_mode: 'EXACT',
  use_tickets: false,
  weekly_schedule: weekly,
};

const exception = {
  id: 5,
  start_date: '2026-09-25T00:00:00',
  end_date: '2026-09-25T23:59:59',
  reason: 'Congés',
  is_holiday: false,
  created_at: '2026-09-19T00:00:00',
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/agenda/settings') return { data: settings } as never;
    if (url === '/agenda/exceptions') return { data: [exception] } as never;
    throw new Error('unexpected GET '+url);
  });
  vi.mocked(api.put).mockImplementation(async (url: string, body: any) => {
    if (url === '/agenda/settings') return { data: body } as never;
    throw new Error('unexpected PUT '+url);
  });
  vi.mocked(api.post).mockResolvedValue({ data: { ...exception, id: 6, reason: 'Formation' } } as never);
  vi.mocked(api.delete).mockResolvedValue({ data: {} } as never);
});

afterEach(() => cleanup());

describe('AgendaTab G5 settings matrix', () => {
  it('loads backend schedule truth before enabling modifications', async () => {
    render(<AgendaTab />);
    expect(await screen.findByText('Horaires & Agenda')).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/agenda/settings');
    expect(api.get).toHaveBeenCalledWith('/agenda/exceptions');
    expect((screen.getByRole('button', { name: 'Enregistrer les horaires' }) as HTMLButtonElement).disabled).toBe(true);
  });

  it('stages day changes then persists exact weekly settings only after explicit save', async () => {
    render(<AgendaTab />);
    await screen.findByText('Horaires & Agenda');

    fireEvent.click(screen.getByLabelText('Lundi ouvert'));
    expect(screen.getByText('Modifications non enregistrées')).toBeTruthy();
    expect(api.put).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer les horaires' }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith(
      '/agenda/settings',
      expect.objectContaining({
        weekly_schedule: expect.objectContaining({
          monday: expect.objectContaining({ is_open: false }),
        }),
      }),
    ));
  });

  it('blocks invalid overlapping hours before backend mutation', async () => {
    render(<AgendaTab />);
    await screen.findByText('Horaires & Agenda');

    fireEvent.change(screen.getByLabelText('Lundi fermeture matin'), { target: { value: '15:00' } });
    fireEvent.change(screen.getByLabelText('Lundi ouverture après-midi'), { target: { value: '14:00' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer les horaires' }));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(/plages matin et après-midi se chevauchent/i)).toBeTruthy();
    expect(api.put).not.toHaveBeenCalled();
  });

  it('keeps dirty state and surfaces refusal when schedule save fails', async () => {
    vi.mocked(api.put).mockRejectedValueOnce(new Error('save refused'));
    render(<AgendaTab />);
    await screen.findByText('Horaires & Agenda');

    fireEvent.click(screen.getByLabelText('Mardi ouvert'));
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer les horaires' }));

    expect(await screen.findByText(/Impossible d'enregistrer ces horaires/i)).toBeTruthy();
    expect(screen.getByText('Modifications non enregistrées')).toBeTruthy();
  });

  it('adds an exception only after valid dates and backend ACK', async () => {
    render(<AgendaTab />);
    await screen.findByText('Horaires & Agenda');

    fireEvent.click(screen.getByRole('button', { name: /Ajouter une fermeture/i }));
    const dates = screen.getAllByDisplayValue('');
    const dateInputs = dates.filter(el => (el as HTMLInputElement).type === 'date');
    fireEvent.change(dateInputs[0], { target: { value: '2026-10-01' } });
    fireEvent.change(dateInputs[1], { target: { value: '2026-10-02' } });
    fireEvent.change(screen.getByPlaceholderText('Ex. Congés annuels'), { target: { value: 'Formation' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/agenda/exceptions', {
      start_date: '2026-10-01T00:00:00',
      end_date: '2026-10-02T23:59:59',
      reason: 'Formation',
      is_holiday: false,
    }));
    expect(await screen.findByText('Formation')).toBeTruthy();
  });

  it('deletes an exception only after the explicit two-step confirmation', async () => {
    render(<AgendaTab />);
    await screen.findByText('Congés');

    fireEvent.click(screen.getByRole('button', { name: 'Retirer' }));
    expect(api.delete).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer' }));

    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/agenda/exceptions/5'));
    expect(screen.queryByText('Congés')).toBeNull();
  });

  it('fails closed when settings truth cannot be loaded and retries', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('read failed'));
    render(<AgendaTab />);

    expect(await screen.findByText('Horaires indisponibles')).toBeTruthy();
    expect(screen.queryByLabelText('Lundi ouvert')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/agenda/settings'));
  });
});
