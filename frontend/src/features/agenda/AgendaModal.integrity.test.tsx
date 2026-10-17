import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AgendaModal } from './AgendaModal';
import { api } from '../../services/api';
import toast from 'react-hot-toast';

vi.mock('../../services/api', () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() } }));
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));
vi.mock('../clinical-ref/useClinicalRef', () => ({ useClinicalRef: () => null }));
vi.mock('../clinical-ref/ClinicalRefSidebar', () => ({ ClinicalRefSidebar: () => null }));
vi.mock('../../hooks/useEscapeKey', () => ({ useEscapeKey: () => {} }));
vi.mock('../../stores/useEliteStore', () => ({
  useEliteStore: () => ({
    fetchPatientIntelligence: vi.fn(), fetchSuggestedAppointment: vi.fn(),
    suggestedAppointment: null, isLoading: false,
  }),
}));
const mount=(editingAppointment?: any, initialPractitionerId=1)=>render(
  <MemoryRouter><AgendaModal isOpen onClose={vi.fn()} onSaved={vi.fn()}
    selectedDate={new Date(2026, 9, 19, 12, 0)} initialPatientId={7}
    initialPatientNom="CERTIFICATION" initialPatientPrenom="T2" editingAppointment={editingAppointment} initialPractitionerId={initialPractitionerId} /></MemoryRouter>
);
const confirm=()=>screen.getByRole('button', { name: 'Confirmer le RDV' }) as HTMLButtonElement;

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/appointments/assignable-practitioners') return { data: [{ id: 1, name: 'Dr Test' }, { id: 2, name: 'Dr Two' }] } as never;
    if (url === '/agenda/resources') return { data: [{ id: 5, name: 'Fauteuil 1' }] } as never;
    if(url==='/appointments/check-conflicts') return { data: { has_conflict:false, conflicts:[] } } as never;
    if(url==='/actes/catalog/search') return {data:[]} as never;
    if(url==='/catalog/specialties') return {data:[]} as never;
    throw Error('Unexpected GET '+url);
  });
  vi.mocked(api.post).mockResolvedValue({data:{id:1}} as never);
  vi.mocked(api.put).mockResolvedValue({data:{id:1}} as never);
});
afterEach(()=>cleanup());

describe('LOT07 07-A — Agenda conflict fail-closed integrated modal', () => {
  it('exposes accessible labels for the editable date, time, duration and clinical act', () => {
    mount();
    expect(screen.getByLabelText('Date')).toBeTruthy();
    expect(screen.getByLabelText('Début')).toBeTruthy();
    expect(screen.getByLabelText('Durée Prévue')).toBeTruthy();
    expect(screen.getByLabelText('Acte / Motif')).toBeTruthy();
  });

  it('blocks exact-time save when the API check fails; never claims no conflicts', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/appointments/assignable-practitioners') return { data: [{ id: 1, name: 'Dr Test' }, { id: 2, name: 'Dr Two' }] } as never;
    if (url === '/agenda/resources') return { data: [{ id: 5, name: 'Fauteuil 1' }] } as never;
      if(url==='/appointments/check-conflicts') throw Error('Network unavailable');
      return {data:[]} as never;
    });
    mount();
    expect(confirm().disabled).toBe(true);
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Vérification des conflits indisponible'), {timeout:4000});
    expect(confirm().disabled).toBe(true);
    fireEvent.submit(confirm().closest('form')!);
    expect(api.post).not.toHaveBeenCalled();
  });

  it('blocks both provider and resource collisions even with empty appointment conflicts', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/appointments/assignable-practitioners') return { data: [{ id: 1, name: 'Dr Test' }, { id: 2, name: 'Dr Two' }] } as never;
    if (url === '/agenda/resources') return { data: [{ id: 5, name: 'Fauteuil 1' }] } as never;
      if(url==='/appointments/check-conflicts')return {data:{has_conflict:true,conflicts:[],resource_conflict_id:42}} as never;
      return {data:[]} as never;
    });
    mount();
    await waitFor(() => expect(screen.getByText(/Créneau occupé : enregistrement bloqué/)).toBeTruthy(), {timeout:4000});
    expect(confirm().disabled).toBe(true);
  });

  it('sends the SAME naive cabinet wall-clock format to conflict GET and POST', async () => {
    mount();
    await waitFor(() => expect(confirm().disabled).toBe(false), {timeout:4000});
    const checks=vi.mocked(api.get).mock.calls.filter(call=>call[0]==='/appointments/check-conflicts');
    expect(checks[checks.length-1][1]).toEqual({params:{
      datetime_start:'2026-10-19T09:00:00',duration_minutes:30,praticien_id:1,
    }});
    fireEvent.change(screen.getByPlaceholderText('Saisir l\'acte ou rechercher dans le catalogue...'), {target:{value:'Consultation T2'}});
    fireEvent.click(confirm());
    await waitFor(()=>expect(api.post).toHaveBeenCalledWith('/appointments/',expect.objectContaining({
      datetime_start:'2026-10-19T09:00:00'
    })), {timeout:4000});
  });

  it('allows an explicit retry after a failed conflict check without changing the date or time', async () => {
    let attempts = 0;
    vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/appointments/assignable-practitioners') return { data: [{ id: 1, name: 'Dr Test' }, { id: 2, name: 'Dr Two' }] } as never;
    if (url === '/agenda/resources') return { data: [{ id: 5, name: 'Fauteuil 1' }] } as never;
      if (url === '/appointments/check-conflicts') {
        attempts += 1;
        if (attempts === 1) throw Error('Network unavailable');
        return { data: { has_conflict: false, conflicts: [] } } as never;
      }
      return { data: [] } as never;
    });
    mount();
    const retry = await screen.findByRole('button', { name: 'Relancer la vérification' });
    expect(confirm().disabled).toBe(true);
    fireEvent.click(retry);
    await waitFor(() => expect(confirm().disabled).toBe(false), { timeout: 4000 });
    expect(attempts).toBe(2);
  });

  it('refuses an inconsistent API response with conflicts but has_conflict=false', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/appointments/assignable-practitioners') return { data: [{ id: 1, name: 'Dr Test' }, { id: 2, name: 'Dr Two' }] } as never;
    if (url === '/agenda/resources') return { data: [{ id: 5, name: 'Fauteuil 1' }] } as never;
      if (url === '/appointments/check-conflicts')
        return { data: { has_conflict: false, conflicts: [{ id: 99, datetime_start: '2026-10-19T09:00:00' }] } } as never;
      return { data: [] } as never;
    });
    mount();
    await screen.findByRole('button', { name: 'Relancer la vérification' });
    expect(confirm().disabled).toBe(true);
    expect(api.post).not.toHaveBeenCalled();
  });

  it('renders a safe human-readable error and refreshes conflicts when POST races to a structured 409', async () => {
    let checks = 0;
    vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/appointments/assignable-practitioners') return { data: [{ id: 1, name: 'Dr Test' }, { id: 2, name: 'Dr Two' }] } as never;
    if (url === '/agenda/resources') return { data: [{ id: 5, name: 'Fauteuil 1' }] } as never;
      if (url === '/appointments/check-conflicts') {
        checks += 1;
        return { data: checks === 1 ? { has_conflict: false, conflicts: [] }
          : { has_conflict: true, conflicts: [{ id: 77, datetime_start: '2026-10-19T09:00:00' }] } } as never;
      }
      return { data: [] } as never;
    });
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { status: 409, data: { detail: {
        message: 'Créneau en conflit avec un autre rendez-vous', conflicts: [{ id: 77 }]
      } } }
    });
    mount();
    await waitFor(() => expect(confirm().disabled).toBe(false), { timeout: 4000 });
    fireEvent.change(screen.getByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue..."),
      { target: { value: 'Consultation T2' } });
    fireEvent.click(confirm());
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Créneau en conflit avec un autre rendez-vous'));
    await waitFor(() => expect(confirm().disabled).toBe(true), { timeout: 4000 });
    await waitFor(() => expect(screen.getByText(/Créneau occupé : enregistrement bloqué/)).toBeTruthy());
    expect(checks).toBeGreaterThanOrEqual(2);
  });

  it('fails closed when backend sends a malformed conflict response', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/appointments/assignable-practitioners') return { data: [{ id: 1, name: 'Dr Test' }, { id: 2, name: 'Dr Two' }] } as never;
    if (url === '/agenda/resources') return { data: [{ id: 5, name: 'Fauteuil 1' }] } as never;
      if(url==='/appointments/check-conflicts')return {data:{conflicts:[]}} as never;
      return {data:[]} as never;
    });
    mount();
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('indisponible'), {timeout:4000});
    expect(confirm().disabled).toBe(true);
  });
  it('preflights and persists exactly the selected practitioner and capacity-one resource', async () => {
    mount();
    await screen.findByLabelText('Ressource clinique');
    fireEvent.change(screen.getByLabelText('Ressource clinique'), { target: { value: '5' } });
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.some(([url, opts]) =>
      url === '/appointments/check-conflicts' && opts?.params?.praticien_id === 1 && opts?.params?.resource_id === 5)), {timeout:4000});
    await waitFor(() => expect(confirm().disabled).toBe(false), {timeout:4000});
    fireEvent.change(screen.getByPlaceholderText("Saisir l'acte ou rechercher dans le catalogue..."), {target:{value:'Contrôle'}});
    fireEvent.click(confirm());
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/appointments/', expect.objectContaining({
      praticien_id:1, resource_id:5, datetime_start:'2026-10-19T09:00:00'
    })), {timeout:4000});
  });

  it.each(['EXACT_TIME','MORNING','AFTERNOON','FULL_DAY'])('edit roundtrip preserves %s and all persisted fields', async (kind) => {
    const existing = { id:74, patient_id:7, patient_name:'CERTIFICATION T2 MULTI WORD', praticien_id:2,
      resource_id:5, datetime_start:'2026-10-19T09:45:00', duration_minutes:45,
      scheduling_type:kind, status:'CONFIRMÉ', motif:'Consultation' };
    mount(existing);
    const save=screen.getByRole('button',{name:'Modifier le RDV'}) as HTMLButtonElement;
    await waitFor(() => expect(save.disabled).toBe(false), {timeout:4000});
    fireEvent.click(save);
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/appointments/74',expect.objectContaining({
      praticien_id:2,resource_id:5,datetime_start:'2026-10-19T09:45:00',duration_minutes:45,
      scheduling_type:kind,status:'CONFIRMÉ',patient_id:7,patient_name:'CERTIFICATION T2 MULTI WORD'
    })), {timeout:4000});
  });

  it('fails closed when no assignable practitioner is available', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if(url==='/appointments/assignable-practitioners')return {data:[]} as never;
      if(url==='/agenda/resources')return {data:[]} as never;
      return {data:{has_conflict:false,conflicts:[]}} as never;
    });
    mount(undefined, 0);
    await waitFor(() => expect(screen.getByText(/Aucun praticien assignable/)).toBeTruthy(),{timeout:4000});
    expect(confirm().disabled).toBe(true);
    expect(api.post).not.toHaveBeenCalled();
  });

  it('refuses late stale conflict results after editing the time', async () => {
    let oldResolve!: (value: unknown) => void;
    vi.mocked(api.get).mockImplementation((url: string,opts?: any) => {
      if(url==='/appointments/assignable-practitioners')return Promise.resolve({data:[{id:1,name:'Dr Test'}]}) as never;
      if(url==='/agenda/resources')return Promise.resolve({data:[]}) as never;
      if(url==='/appointments/check-conflicts' && opts?.params?.datetime_start?.includes('09:00'))
        return new Promise(resolve=>{oldResolve=resolve;}) as never;
      if(url==='/appointments/check-conflicts')return Promise.resolve({data:{has_conflict:true,conflicts:[{id:45}]}}) as never;
      return Promise.resolve({data:[]}) as never;
    });
    mount();
    await waitFor(() => expect(typeof oldResolve).toBe('function'),{timeout:4000});
    fireEvent.change(screen.getByLabelText('Début'),{target:{value:'10:00'}});
    await waitFor(() => expect(screen.getByText(/Créneau occupé : enregistrement bloqué/)).toBeTruthy(),{timeout:4000});
    oldResolve({data:{has_conflict:false,conflicts:[]}});
    await new Promise(resolve=>setTimeout(resolve,20));
    expect(confirm().disabled).toBe(true);
  });

});
