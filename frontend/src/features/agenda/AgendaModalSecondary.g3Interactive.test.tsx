import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AgendaModal } from './AgendaModal';
import { api } from '../../services/api';

const elite = vi.hoisted(() => ({
  suggestedAppointment: null as any,
  fetchPatientIntelligence: vi.fn(),
  fetchSuggestedAppointment: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));
vi.mock('../clinical-ref/useClinicalRef', () => ({ useClinicalRef: () => null }));
vi.mock('../clinical-ref/ClinicalRefSidebar', () => ({ ClinicalRefSidebar: () => null }));
vi.mock('../../hooks/useEscapeKey', () => ({ useEscapeKey: () => undefined }));
vi.mock('./AppointmentMobileBridge', () => ({ AppointmentMobileBridge: () => null }));
vi.mock('../../stores/useEliteStore', () => ({
  useEliteStore: () => ({
    fetchPatientIntelligence: elite.fetchPatientIntelligence,
    fetchSuggestedAppointment: elite.fetchSuggestedAppointment,
    suggestedAppointment: elite.suggestedAppointment,
    isLoading: false,
  }),
}));

function renderModal(opts: Record<string, any> = {}) {
  const onClose = vi.fn();
  const onSaved = vi.fn();
  const view = render(
    <MemoryRouter initialEntries={['/agenda']}>
      <Routes>
        <Route path="/agenda" element={
          <AgendaModal
            isOpen
            onClose={onClose}
            onSaved={onSaved}
            selectedDate={new Date('2026-09-21T00:00:00')}
            initialTime="10:00"
            {...opts}
          />
        } />
        <Route path="/patients/:id/edit" element={<div>Edit patient destination</div>} />
        <Route path="/patients/new" element={<div>New patient destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
  return { ...view, onClose, onSaved };
}

beforeEach(() => {
  vi.clearAllMocks();
  elite.suggestedAppointment = null;
  elite.fetchPatientIntelligence.mockResolvedValue(undefined);
  elite.fetchSuggestedAppointment.mockResolvedValue(undefined);
  vi.mocked(api.get).mockImplementation(async (url: string, config?: any) => {
    if (url === '/patients/') {
      return { data: [{ id: 7, nom: 'BENALI', prenom: 'Sara', numero_dossier: 'P-7' }] } as never;
    }
    if (url === '/actes/catalog/search') return { data: [] } as never;
    if (url === '/catalog/specialties') return { data: [{ id: 1, name: 'SOINS' }] } as never;
    if (url === '/actes/duration') return { data: { duration: 30 } } as never;
    if (url === '/appointments/check-conflicts') {
      return {
        data: {
          conflicts: config?.params?.datetime_start
            ? [{ id: 90, patient_name: 'Conflit Test', datetime_start: '2026-09-21T10:15:00Z' }]
            : [],
        },
      } as never;
    }
    if (url === '/patients/7/appointment-intel') {
      return { data: { suggestion: 'Contrôle administratif', duration: 20 } } as never;
    }
    throw new Error('unexpected GET '+url);
  });
  vi.mocked(api.post).mockImplementation(async (url: string, payload?: any) => {
    if (url === '/actes/catalog/quick-add') {
      return { data: { id: 44, name: payload.name, base_price: payload.base_price, category: payload.category } } as never;
    }
    if (url === '/appointments/') return { data: { id: 1 } } as never;
    throw new Error('unexpected POST '+url);
  });
  vi.spyOn(window, 'open').mockImplementation(() => null);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('AgendaModal G3 secondary control matrix', () => {
  it('searches and selects an existing patient, then exposes edit and WhatsApp reminder actions', async () => {
    const view=renderModal();

    fireEvent.change(screen.getByPlaceholderText('Rechercher ou saisir un nom...'), { target: { value: 'Sara' } });
    expect(await screen.findByText('BENALI Sara')).toBeTruthy();
    fireEvent.click(screen.getByText('BENALI Sara'));

    expect(await screen.findByText('BENALI Sara')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Modifier' })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Rappel WhatsApp/i })).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue..."), { target: { value: 'Contrôle' } });
    fireEvent.click(screen.getByRole('button', { name: /Rappel WhatsApp/i }));
    expect(window.open).toHaveBeenCalledWith(expect.stringContaining('https://wa.me/?text='), '_blank');

    fireEvent.click(screen.getByRole('button', { name: 'Modifier' }));
    expect(view.onClose).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('Edit patient destination')).toBeTruthy();
  });

  it('offers patient creation when search has no match', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/') return { data: [] } as never;
      if (url === '/actes/catalog/search') return { data: [] } as never;
      if (url === '/catalog/specialties') return { data: [] } as never;
      if (url === '/appointments/check-conflicts') return { data: { conflicts: [] } } as never;
      return { data: {} } as never;
    });
    const { onClose }=renderModal();

    fireEvent.change(screen.getByPlaceholderText('Rechercher ou saisir un nom...'), { target: { value: 'Inconnu' } });
    expect(await screen.findByText('Aucun patient trouvé')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Créer Patient Externe/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(await screen.findByText('New patient destination')).toBeTruthy();
  });

  it('quick-adds a missing clinical act with price and category and selects it only after ACK', async () => {
    renderModal({ initialPatientId:7, initialPatientNom:'BENALI', initialPatientPrenom:'Sara' });

    const act=screen.getByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue...");
    fireEvent.change(act,{target:{value:'Acte Test'}});
    fireEvent.focus(act);

    fireEvent.click(await screen.findByRole('button',{name:/Ajouter « Acte Test » aux actes/i}));
    fireEvent.change(screen.getByLabelText('Tarif (DHS)'),{target:{value:'450'}});
    fireEvent.change(screen.getByLabelText('Catégorie'),{target:{value:'SOINS'}});
    fireEvent.click(screen.getByRole('button',{name:'Ajouter au catalogue'}));

    await waitFor(()=>expect(api.post).toHaveBeenCalledWith('/actes/catalog/quick-add',{
      name:'Acte Test',base_price:450,category:'SOINS'
    }));
    expect(await screen.findByText('Acte Test')).toBeTruthy();
  });

  it('opens on-demand suggestions and applies administrative suggestion', async () => {
    renderModal({ initialPatientId:7, initialPatientNom:'BENALI', initialPatientPrenom:'Sara' });

    fireEvent.click(screen.getByRole('button',{name:/Suggestions/i}));
    await waitFor(()=>expect(api.get).toHaveBeenCalledWith('/patients/7/appointment-intel'));
    expect(elite.fetchPatientIntelligence).toHaveBeenCalledWith(7);
    expect(elite.fetchSuggestedAppointment).toHaveBeenCalledWith(7);

    const apply=await screen.findByRole('button',{name:/Appliquer/i});
    fireEvent.click(apply);
    expect((screen.getByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue...") as HTMLInputElement).value).toBe('Contrôle administratif');
  });

  it('surfaces conflict details without silently changing the requested slot', async () => {
    renderModal({ initialPatientId:7, initialPatientNom:'BENALI', initialPatientPrenom:'Sara' });

    expect(await screen.findByText(/Chevauchement avec 1 RDV/i,{}, {timeout:2000})).toBeTruthy();
    expect(screen.getByText(/Conflit Test/)).toBeTruthy();
    expect(screen.getByRole('button',{name:'Confirmer le RDV'})).toBeTruthy();
  });
});
