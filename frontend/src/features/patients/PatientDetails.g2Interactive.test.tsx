import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PatientDetails } from './PatientDetailsInner';
import { api } from '../../services/api';

const state = vi.hoisted(() => ({
  user: {
    role: 'ADMIN',
    employer_id: null as number | null,
    permissions: {} as Record<string, boolean>,
  },
  patient: {
    id: 7,
    numero_dossier: 'P-000007',
    nom: 'BENALI',
    prenom: 'Sara',
    date_naissance: '1990-01-01',
    telephone: '0600000000',
    email: 'sara@example.com',
    assurance: 'CNSS',
    antecedents_medicaux: '',
    motif_consultation: '',
    dossier: { is_ortho_active: false },
  },
}));

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: (selector: (s: { user: typeof state.user }) => unknown) => selector({ user: state.user }),
}));

vi.mock('../../stores/usePatientStore', () => ({
  usePatientStore: () => ({
    editingDoc: null,
    patientsCache: [state.patient],
    setEditingDoc: vi.fn(),
  }),
}));

vi.mock('../../hooks/useFlowHandoff', () => ({ useFlowHandoff: () => vi.fn() }));
vi.mock('../../components/AssuranceBadge', () => ({ AssuranceBadge: () => <span>Assurance</span> }));
vi.mock('../ortho/OrthoCockpitPanel', () => ({ OrthoCockpitPanel: () => <div>Tracking cockpit</div> }));
vi.mock('../ortho/OrthoLongitudinalComparePanel', () => ({ OrthoLongitudinalComparePanel: () => <div>Ortho compare</div> }));
vi.mock('./components/PatientJourney', () => ({ PatientJourney: () => <div>Patient journey</div> }));
vi.mock('./components/ClinicalHub', () => ({ ClinicalHub: () => <div>Clinical hub</div> }));
vi.mock('./components/PatientFinances', () => ({ PatientFinances: () => <div>Patient finances</div> }));
vi.mock('./components/PatientRvgPanel', () => ({ PatientRvgPanel: () => <div>RVG panel</div> }));
vi.mock('./components/PatientMediaTimeline', () => ({ PatientMediaTimeline: () => <div>Media timeline</div> }));
vi.mock('../panoramic/PanoramicStudio', () => ({ PanoramicStudio: () => <div>Panoramic studio</div> }));
vi.mock('../ortho/CephaloWorkspace', () => ({ CephaloWorkspace: () => <div>Cephalo workspace</div> }));
vi.mock('../admin/DocumentHub', () => ({ DocumentHub: () => <div>Document hub</div> }));
vi.mock('./PatientDocuments', () => ({ PatientDocuments: () => <div>Patient documents history</div> }));
vi.mock('./components/PatientMobileBridge', () => ({ PatientMobileBridge: () => <div>Mobile bridge</div> }));
vi.mock('./components/PatientCompanionPanel', () => ({ PatientCompanionPanel: () => <div>Companion panel</div> }));
vi.mock('./components/QuickPayModal', () => ({
  QuickPayModal: ({ isOpen }: { isOpen: boolean }) => (isOpen ? <div>Quick pay modal</div> : null),
}));

function renderDetails(entry = '/patients/7') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/patients/:id" element={<PatientDetails />} />
        <Route path="/patients/:id/edit" element={<div>Edit destination</div>} />
        <Route path="/patients" element={<div>Patient list destination</div>} />
        <Route path="/agenda" element={<div>Agenda destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  state.user.role = 'ADMIN';
  state.user.employer_id = null;
  state.user.permissions = {};
  state.patient.dossier = { is_ortho_active: false };

  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/7') return { data: state.patient } as never;
    if (url === '/intelligence/patient/7/nba') return { data: { nba: null } } as never;
    if (url === '/motifs') return { data: [] } as never;
    throw new Error(`unexpected GET ${url}`);
  });
  vi.mocked(api.patch).mockResolvedValue({ data: {} } as never);
});

afterEach(() => cleanup());

describe('PatientDetails G2 interactive permission matrix', () => {
  it('lets an owner/admin navigate the dossier tabs and open quick payment', async () => {
    renderDetails();

    expect(await screen.findByText('Tracking cockpit')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Clinique' }));
    expect(await screen.findByText('Clinical hub')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Finances' }));
    expect(await screen.findByText('Patient finances')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Encaisser' }));
    expect(screen.getByText('Quick pay modal')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Companion' }));
    expect(await screen.findByText('Companion panel')).toBeTruthy();
  });

  it('normalizes a forbidden clinical deep-link back to tracking', async () => {
    state.user.role = 'SECRETAIRE';
    state.user.employer_id = 99;
    state.user.permissions = { clinical: false };

    renderDetails('/patients/7?tab=clinical');

    expect(await screen.findByText('Tracking cockpit')).toBeTruthy();
    expect(screen.queryByText('Clinical hub')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Clinique' })).toBeNull();
  });

  it('normalizes a forbidden finance deep-link and exposes no payment action', async () => {
    state.user.role = 'SECRETAIRE';
    state.user.employer_id = 99;
    state.user.permissions = { accounting: false, payments: false };

    renderDetails('/patients/7?tab=finances');

    expect(await screen.findByText('Tracking cockpit')).toBeTruthy();
    expect(screen.queryByText('Patient finances')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Finances' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Encaisser' })).toBeNull();
  });

  it('normalizes a forbidden Companion deep-link for non owner/admin roles', async () => {
    state.user.role = 'DENTISTE';
    state.user.employer_id = 99;
    state.user.permissions = { clinical: true };

    renderDetails('/patients/7?tab=companion');

    expect(await screen.findByText('Tracking cockpit')).toBeTruthy();
    expect(screen.queryByText('Companion panel')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Companion' })).toBeNull();
  });

  it('fails closed from a forbidden cephalo deep-link to RVG', async () => {
    state.user.role = 'SECRETAIRE';
    state.user.employer_id = 99;
    state.user.permissions = { panoramic: false, cephalo: false };

    renderDetails('/patients/7?tab=radiology&radioTab=cephalo');

    expect(await screen.findByText('RVG panel')).toBeTruthy();
    expect(screen.queryByText('Cephalo workspace')).toBeNull();
    expect(screen.queryByRole('button', { name: /Céphalométrie/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Panoramique/i })).toBeNull();
  });

  it('activates orthodontic follow-up only after backend ACK before unlocking cephalo', async () => {
    renderDetails('/patients/7?tab=radiology&radioTab=cephalo');

    expect(await screen.findByText('Module Céphalométrique Verrouillé')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Activer le Suivi Orthodontique/i }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/patients/7/ortho', { is_ortho_active: true }));
    expect(await screen.findByText('Cephalo workspace')).toBeTruthy();
  });

  it('keeps cephalo locked and shows no false unlock on activation failure', async () => {
    vi.mocked(api.patch).mockRejectedValueOnce(new Error('activation failed'));
    renderDetails('/patients/7?tab=radiology&radioTab=cephalo');

    fireEvent.click(await screen.findByRole('button', { name: /Activer le Suivi Orthodontique/i }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/patients/7/ortho', { is_ortho_active: true }));
    expect(await screen.findByText('Module Céphalométrique Verrouillé')).toBeTruthy();
    expect(screen.queryByText('Cephalo workspace')).toBeNull();
  });

  it('routes quick actions to edit, agenda and documents without mutating patient data', async () => {
    renderDetails();

    fireEvent.click(await screen.findByRole('button', { name: 'Modifier' }));
    expect(await screen.findByText('Edit destination')).toBeTruthy();

    cleanup();
    renderDetails();
    fireEvent.click(await screen.findByRole('button', { name: 'RDV' }));
    expect(await screen.findByText('Agenda destination')).toBeTruthy();

    cleanup();
    renderDetails();
    fireEvent.click((await screen.findAllByRole('button', { name: 'Document' }))[0]);
    expect(await screen.findByText('Document hub')).toBeTruthy();
    expect(api.patch).not.toHaveBeenCalled();
  });
  it('renders a persisted custom cabinet motif after patient reload', async () => {
    state.patient.motif_consultation = JSON.stringify(['cm_e2e_implant_followup']);

    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/7') return { data: state.patient } as never;
      if (url === '/motifs') {
        return {
          data: [{
            id: 'cm_e2e_implant_followup',
            label: 'Contrôle implant personnalisé',
            category_id: 'IMPLANTOLOGIE',
            urgency: 'normal',
            is_active: true,
            source: 'cabinet',
          }],
        } as never;
      }
      if (url === '/intelligence/patient/7/nba') return { data: { nba: null } } as never;
      throw new Error(`unexpected GET ${url}`);
    });

    renderDetails();

    expect(await screen.findByText('Contrôle implant personnalisé')).toBeTruthy();
    expect(screen.getByText('Cabinet')).toBeTruthy();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/motifs', { params: { include_inactive: true } }));

    state.patient.motif_consultation = '';
  });

  it('shows a truthful patient-load error and retries successfully', async () => {
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error('patient load failed'))
      .mockImplementation(async (url: string) => {
        if (url === '/patients/7') return { data: state.patient } as never;
        if (url === '/intelligence/patient/7/nba') return { data: { nba: null } } as never;
        throw new Error('unexpected GET ' + url);
      });

    renderDetails();

    expect(await screen.findByText('Impossible de charger le dossier')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Réessayer/i }));
    expect(await screen.findByText('Tracking cockpit')).toBeTruthy();
  });

  it('switches Documents between create and history without entering deep document actions', async () => {
    renderDetails();

    fireEvent.click((await screen.findAllByRole('button', { name: 'Document' }))[0]);
    expect(await screen.findByText('Document hub')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Historique' }));
    expect(await screen.findByText('Patient documents history')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));
    expect(await screen.findByText('Document hub')).toBeTruthy();
  });
});
