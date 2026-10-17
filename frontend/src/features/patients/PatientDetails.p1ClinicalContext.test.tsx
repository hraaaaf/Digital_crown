import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom';
import { PatientDetails } from './PatientDetailsInner';
import { api } from '../../services/api';
import toast from 'react-hot-toast';

vi.mock('react-hot-toast', () => ({
  default: Object.assign(vi.fn(), { success: vi.fn(), error: vi.fn() }),
}));

const fixtures = vi.hoisted(() => ({
  user: { role: 'ADMIN', employer_id: null as number | null, permissions: {} as Record<string, boolean> },
  medicalHistory: '' as string,
  advice: null as null | { title: string; message: string; action?: string },
}));

vi.mock('../../services/api', () => ({
  api: { get: vi.fn(), patch: vi.fn() },
}));
vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: (selector: (state: { user: typeof fixtures.user }) => unknown) => selector({ user: fixtures.user }),
}));
vi.mock('../../stores/usePatientStore', () => ({
  usePatientStore: () => ({ editingDoc: null, patientsCache: [], setEditingDoc: vi.fn() }),
}));
vi.mock('../../hooks/useFlowHandoff', () => ({ useFlowHandoff: () => vi.fn() }));
vi.mock('../../components/AssuranceBadge', () => ({ AssuranceBadge: () => <span>Assurance</span> }));
vi.mock('../ortho/OrthoCockpitPanel', () => ({ OrthoCockpitPanel: () => <div>Ortho cockpit</div> }));
vi.mock('../ortho/OrthoLongitudinalComparePanel', () => ({ OrthoLongitudinalComparePanel: () => <div>Ortho compare</div> }));
vi.mock('./components/PatientJourney', () => ({ PatientJourney: () => <div>Patient journey</div> }));
vi.mock('./components/ClinicalHub', () => ({ ClinicalHub: () => <div>Clinical hub</div> }));
vi.mock('./components/PatientFinances', () => ({ PatientFinances: () => <div>Patient finances</div> }));
vi.mock('./components/PatientRvgPanel', () => ({ PatientRvgPanel: () => <div>RVG panel</div> }));
vi.mock('../panoramic/PanoramicStudio', () => ({ PanoramicStudio: () => <div>Panoramic studio</div> }));
vi.mock('../ortho/CephaloWorkspace', () => ({ CephaloWorkspace: () => <div>Cephalo workspace</div> }));
vi.mock('../admin/DocumentHub', () => ({ DocumentHub: () => <div>Document hub</div> }));
vi.mock('./PatientDocuments', () => ({ PatientDocuments: () => <div>Patient documents</div> }));
vi.mock('./components/PatientCompanionPanel', () => ({ PatientCompanionPanel: () => <div>Companion panel</div> }));
vi.mock('./components/QuickPayModal', () => ({ QuickPayModal: () => null }));
vi.mock('../multiview/CabinetTwoViewsPilot', () => ({
  CabinetTwoViewsPilot: ({ patient }: { patient: { id: number } }) => <div data-testid="g1-active">Real G1 route patient {patient.id}</div>,
}));

function renderDetails(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/patients/:id" element={<PatientDetails />} />
        <Route path="/patients/:id/edit" element={<div>Existing patient edit route</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubEnv('VITE_V15_07_G1_TWO_VIEWS_PILOT', '1');
  fixtures.user.role = 'ADMIN';
  fixtures.user.permissions = {};
  fixtures.medicalHistory = '';
  fixtures.advice = null;
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/7') {
      return { data: {
        id: 7, numero_dossier: 'T2-0001', nom: 'CERTIFICATION', prenom: 'T2',
        date_naissance: '1990-01-01', telephone: '0000', assurance: '',
        antecedents_medicaux: fixtures.medicalHistory, motif_consultation: '',
        dossier: { is_ortho_active: false },
      } } as never;
    }
    if (url === '/intelligence/patient/7/nba') return { data: { nba: fixtures.advice } } as never;
    throw Error('Unexpected GET ' + url);
  });
  vi.mocked(api.patch).mockResolvedValue({ data: {} } as never);
});

afterEach(() => { cleanup(); vi.unstubAllEnvs(); vi.useRealTimers(); });

describe('LOT07 P1 — actual PatientDetails route and G1 MultiView', () => {
  it('shows missing medical history in patient overview with a real edit-route action', async () => {
    renderDetails('/patients/7?tab=tracking');
    expect(await screen.findByRole('status', { name: 'Antécédents médicaux non renseignés' })).toBeTruthy();
    expect(screen.queryByText('Real G1 route patient 7')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Compléter les antécédents dans la fiche patient' }));
    expect(await screen.findByText('Existing patient edit route')).toBeTruthy();
    expect(api.patch).not.toHaveBeenCalled();
  });

  it('keeps the missing-history status above the G1 imaging pilot without duplicating fake content', async () => {
    renderDetails('/patients/7?tab=radiology&radioTab=media');
    expect(await screen.findByTestId('g1-active')).toBeTruthy();
    expect(screen.getByRole('status', { name: 'Antécédents médicaux non renseignés' })).toBeTruthy();
    expect(screen.getAllByText('Antécédents médicaux non renseignés')).toHaveLength(1);
  });

  it('retains clinical access guards for an unauthorized deep-link', async () => {
    fixtures.user.role = 'SECRETAIRE';
    fixtures.user.employer_id = 13;
    fixtures.user.permissions = { clinical: false, cephalo: false, panoramic: false };
    renderDetails('/patients/7?tab=clinical');
    expect(await screen.findByText('Patient journey')).toBeTruthy();
    expect(screen.queryByText('Clinical hub')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Clinique' })).toBeNull();
    expect(screen.getByRole('status', { name: 'Antécédents médicaux non renseignés' })).toBeTruthy();
  });

  it('does not invent missing history when backend reports medical information', async () => {
    fixtures.medicalHistory = 'Antécédents consignés dans le dossier';
    renderDetails('/patients/7?tab=tracking');
    expect(await screen.findByText('Patient journey')).toBeTruthy();
    expect(screen.queryByRole('status', { name: 'Antécédents médicaux non renseignés' })).toBeNull();
    expect(screen.queryByRole('button', { name: /Compléter les antécédents/ })).toBeNull();
  });

  it('never renders stale clinical details from patient 7 when URL switches to patient 8', async () => {
    let resolvePatient8: ((value: { data: unknown }) => void) | undefined;
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/7') return { data: {
        id: 7, numero_dossier: 'T2-0001', nom: 'CERTIFICATION', prenom: 'T2',
        date_naissance: '1990-01-01', telephone: '0000', assurance: '',
        antecedents_medicaux: '', motif_consultation: '', dossier: { is_ortho_active: false },
      } } as never;
      if (url === '/patients/8') return new Promise(resolve => {
        resolvePatient8 = resolve;
      }) as never;
      if (url.endsWith('/nba')) return { data: { nba: null } } as never;
      throw Error('Unexpected GET '+url);
    });
    render(
      <MemoryRouter initialEntries={['/patients/7?tab=tracking']}>
        <Link to="/patients/8?tab=tracking">Changer de patient</Link>
        <Routes><Route path="/patients/:id" element={<PatientDetails />} /></Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByText('CERTIFICATION T2')).toBeTruthy();
    fireEvent.click(screen.getByRole('link', { name: 'Changer de patient' }));
    expect(screen.queryByText('CERTIFICATION T2')).toBeNull();
    expect(screen.queryByRole('status', { name: 'Antécédents médicaux non renseignés' })).toBeNull();
    await act(async () => {
      resolvePatient8?.({ data: {
        id: 8, numero_dossier: 'T2-0002', nom: 'AUTRE', prenom: 'B',
        date_naissance: '1992-01-01', telephone: '0001', assurance: '',
        antecedents_medicaux: 'Donnée réelle', motif_consultation: '',
        dossier: { is_ortho_active: false },
      } });
    });
    expect(await screen.findByText('AUTRE B')).toBeTruthy();
    expect(screen.queryByText('CERTIFICATION T2')).toBeNull();
    expect(screen.queryByRole('status', { name: 'Antécédents médicaux non renseignés' })).toBeNull();
  });

  it('shows the sourced NBA in G1 as a non-executable suggestion, not a clinical action button', async () => {
    fixtures.advice = {
      title: 'Information à compléter', message: 'Antécédents médicaux non renseignés',
      action: 'Vérifier avec le patient',
    };
    vi.useFakeTimers();
    renderDetails('/patients/7?tab=radiology&radioTab=media');
    await act(async () => { await vi.advanceTimersByTimeAsync(1600); });
    const advice = screen.getByRole('note', { name: 'Conseil clinique du dossier' });
    expect(advice.textContent).toContain('Vérifier avec le patient');
    expect(advice.textContent).toContain('non exécutée');
    expect(screen.queryByRole('button', { name: 'Vérifier avec le patient' })).toBeNull();
  });
  it('shows a sourced NBA inline in ordinary imaging, never as an obstructing toast', async () => {
    vi.stubEnv('VITE_V15_07_G1_TWO_VIEWS_PILOT', '0');
    fixtures.advice = {
      title: 'Vérification nécessaire',
      message: 'Information médicale à confirmer',
      action: 'Interroger le patient',
    };
    vi.useFakeTimers();
    renderDetails('/patients/7?tab=radiology&radioTab=rvg');
    await act(async () => { await vi.advanceTimersByTimeAsync(1600); });
    const note = screen.getByRole('note', { name: 'Conseil clinique du dossier' });
    expect(note.textContent).toContain('Information médicale à confirmer');
    expect(note.textContent).toContain('Interroger le patient');
    expect(toast).not.toHaveBeenCalled();
  });

  it('keeps sourced advice accessible on documents without adding a missing-history banner', async () => {
    fixtures.advice = {
      title: 'Dossier à compléter', message: 'Consulter le patient',
    };
    vi.useFakeTimers();
    renderDetails('/patients/7?tab=admin');
    await act(async () => { await vi.advanceTimersByTimeAsync(1600); });
    expect(screen.getByRole('note', { name: 'Conseil clinique du dossier' }).textContent)
      .toContain('Dossier à compléter');
    expect(screen.queryByRole('status', { name: 'Antécédents médicaux non renseignés' })).toBeNull();
    expect(toast).not.toHaveBeenCalled();
  });

  it.each(['late-success', 'late-failure'])('never replaces patient B when patient A finishes after navigation (%s)', async ending => {
    let settleA: ((value: { data: unknown }) => void) | undefined;
    let failA: ((reason: Error) => void) | undefined;
    const pendingA = new Promise<{ data: unknown }>((resolve, reject) => {
      settleA = resolve;
      failA = reject;
    });
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/7') return pendingA as never;
      if (url === '/patients/8') return { data: {
        id: 8, numero_dossier: 'T2-0002', nom: 'PATIENT', prenom: 'B',
        date_naissance: '1990-01-01', telephone: '0008', assurance: '',
        antecedents_medicaux: 'Historique réel patient B', motif_consultation: '',
        dossier: { is_ortho_active: false },
      } } as never;
      if (url.endsWith('/nba')) return { data: { nba: null } } as never;
      throw Error('Unexpected GET '+url);
    });

    render(
      <MemoryRouter initialEntries={['/patients/7?tab=tracking']}>
        <Link to="/patients/8?tab=tracking">Ouvrir patient B</Link>
        <Routes><Route path="/patients/:id" element={<PatientDetails />} /></Routes>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('link', { name: 'Ouvrir patient B' }));
    expect(await screen.findByText('PATIENT B')).toBeTruthy();
    expect(screen.getByText('Historique réel patient B')).toBeTruthy();
    await act(async () => {
      if (ending === 'late-failure') failA?.(new Error('Old patient request failed'));
      else settleA?.({ data: {
        id: 7, numero_dossier: 'T2-0001', nom: 'STALE', prenom: 'A',
        date_naissance: '1990-01-01', telephone: '0007', assurance: '',
        antecedents_medicaux: 'Never render A', motif_consultation: '',
      } });
      await Promise.resolve();
    });
    expect(screen.getByText('PATIENT B')).toBeTruthy();
    expect(screen.getByText('Historique réel patient B')).toBeTruthy();
    expect(screen.queryByText('Never render A')).toBeNull();
    expect(screen.queryByText('STALE A')).toBeNull();
  });

});
