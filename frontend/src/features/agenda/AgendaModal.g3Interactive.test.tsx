import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AgendaModal } from './AgendaModal';
import { api } from '../../services/api';

const elite = vi.hoisted(() => ({
  suggestedAppointment: null as any,
  fetchPatientIntelligence: vi.fn(),
  fetchSuggestedAppointment: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

vi.mock('../clinical-ref/useClinicalRef', () => ({ useClinicalRef: () => null }));
vi.mock('../clinical-ref/ClinicalRefSidebar', () => ({ ClinicalRefSidebar: () => null }));
vi.mock('../../stores/useEliteStore', () => ({
  useEliteStore: () => ({
    fetchPatientIntelligence: elite.fetchPatientIntelligence,
    fetchSuggestedAppointment: elite.fetchSuggestedAppointment,
    suggestedAppointment: elite.suggestedAppointment,
    isLoading: false,
  }),
}));
vi.mock('../../hooks/useEscapeKey', () => ({ useEscapeKey: () => undefined }));
vi.mock('./AppointmentMobileBridge', () => ({ AppointmentMobileBridge: () => <div>Appointment mobile bridge</div> }));

function renderCreate(overrides: Record<string, unknown> = {}) {
  const onClose = vi.fn();
  const onSaved = vi.fn();
  render(
    <MemoryRouter>
      <AgendaModal
        isOpen
        onClose={onClose}
        onSaved={onSaved}
        selectedDate={new Date('2026-09-21T00:00:00')}
        initialTime="10:00"
        initialPatientId={7}
        initialPatientNom="BENALI"
        initialPatientPrenom="Sara"
        {...overrides}
      />
    </MemoryRouter>,
  );
  return { onClose, onSaved };
}

beforeEach(() => {
  vi.clearAllMocks();
  elite.suggestedAppointment = null;
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/actes/catalog/search') return { data: [] } as never;
    if (url === '/catalog/specialties') return { data: [{ id: 1, name: 'SOINS' }] } as never;
    if (url === '/actes/duration') return { data: { duration: 30 } } as never;
    if (url === '/appointments/check-conflicts') return { data: { conflicts: [] } } as never;
    if (url.includes('/appointment-intel')) return { data: null } as never;
    throw new Error('unexpected GET ' + url);
  });
  vi.mocked(api.post).mockResolvedValue({ data: { id: 99 } } as never);
  vi.mocked(api.put).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.delete).mockResolvedValue({ data: {} } as never);
  vi.spyOn(window, 'confirm').mockReturnValue(true);
  vi.spyOn(window, 'alert').mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('AgendaModal G3 appointment mutation matrix', () => {
  it('creates a patient appointment and closes only after backend ACK', async () => {
    const { onClose, onSaved } = renderCreate();

    const act = await screen.findByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue...");
    fireEvent.change(act, { target: { value: 'Détartrage' } });
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le RDV' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/appointments/',
      expect.objectContaining({
        patient_id: 7,
        patient_name: 'BENALI Sara',
        motif: 'Détartrage',
        duration_minutes: 30,
        status: 'PRÉVU',
        scheduling_type: 'EXACT_TIME',
        datetime_start: expect.any(String),
      }),
    ));
    expect(onSaved).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('propagates planning type and status choices into the appointment payload', async () => {
    const { onSaved } = renderCreate();

    fireEvent.change(await screen.findByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue..."), { target: { value: 'Consultation' } });
    fireEvent.click(screen.getByRole('button', { name: /Matin/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmé' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le RDV' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/appointments/',
      expect.objectContaining({ scheduling_type: 'MORNING', status: 'CONFIRMÉ' }),
    ));
    expect(onSaved).toHaveBeenCalledTimes(1);
  });

  it('keeps the modal open and reports no false success when create is refused', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'Créneau refusé' } } });
    const { onClose, onSaved } = renderCreate();

    fireEvent.change(await screen.findByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue..."), { target: { value: 'Détartrage' } });
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le RDV' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1));
    expect(onSaved).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog', { name: 'Nouveau Rendez-vous' })).toBeTruthy();
  });

  it('edits the historical appointment through PUT and preserves the edit boundary', async () => {
    const editingAppointment = {
      id: 55,
      patient_id: 7,
      patient_name: 'BENALI Sara',
      motif: 'Contrôle',
      datetime_start: '2026-09-21T10:00:00',
      duration_minutes: 30,
      status: 'PRÉVU',
    };
    const { onSaved, onClose } = renderCreate({ editingAppointment });

    fireEvent.click(await screen.findByRole('button', { name: 'Modifier le RDV' }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith(
      '/appointments/55',
      expect.objectContaining({ patient_id: 7, motif: 'Contrôle', status: 'PRÉVU' }),
    ));
    expect(onSaved).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('deletes only after explicit confirmation and does not report success on refusal', async () => {
    const editingAppointment = {
      id: 55,
      patient_id: 7,
      patient_name: 'BENALI Sara',
      motif: 'Contrôle',
      datetime_start: '2026-09-21T10:00:00',
      duration_minutes: 30,
      status: 'PRÉVU',
    };
    const first = renderCreate({ editingAppointment });

    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer' }));
    expect(window.confirm).toHaveBeenCalledWith('Supprimer ce rendez-vous ?');
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/appointments/55'));
    expect(first.onSaved).toHaveBeenCalledTimes(1);
    expect(first.onClose).toHaveBeenCalledTimes(1);

    cleanup();
    vi.clearAllMocks();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.spyOn(window, 'alert').mockImplementation(() => undefined);
    vi.mocked(api.delete).mockRejectedValueOnce(new Error('delete refused'));
    vi.mocked(api.get).mockResolvedValue({ data: [] } as never);

    const second = renderCreate({ editingAppointment });
    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer' }));
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/appointments/55'));
    expect(second.onSaved).not.toHaveBeenCalled();
    expect(second.onClose).not.toHaveBeenCalled();
    expect(window.alert).toHaveBeenCalledWith('Erreur lors de la suppression.');
  });
});
