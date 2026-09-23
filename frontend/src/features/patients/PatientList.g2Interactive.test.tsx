import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { PatientList } from './PatientList';
import { api } from '../../services/api';

const setPatientsCache = vi.fn();

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../../stores/usePatientStore', () => ({
  usePatientStore: () => ({
    patientsCache: [
      {
        id: 7,
        nom: 'BENALI',
        prenom: 'Sara',
        numero_dossier: 'P-000007',
        assurance: 'CNSS',
        telephone: '0600000000',
      },
    ],
    patientsCacheLoaded: true,
    patientsCacheUpdatedAt: Date.now(),
    setPatientsCache,
  }),
}));

vi.mock('../admin/Settings/hooks/useSettingsStore', () => ({
  useSettingsStore: (selector: (state: { profile: { show_patient_badges: boolean } }) => unknown) =>
    selector({ profile: { show_patient_badges: false } }),
}));

vi.mock('./components/PatientScoreBadge', () => ({ PatientScoreBadge: () => null }));
vi.mock('./components/PatientSummaryHoverCard', () => ({ PatientSummaryHoverCard: () => null }));
vi.mock('../../components/AssuranceBadge', () => ({ AssuranceBadge: () => <span>Assurance</span> }));
vi.mock('./CsvImportModal', () => ({
  CsvImportModal: ({ isOpen }: { isOpen: boolean }) => (isOpen ? <div>CSV modal open</div> : null),
}));
vi.mock('../../components/CrownDialog', () => ({
  CrownDialog: ({ open, children }: { open: boolean; children: React.ReactNode }) => (open ? <div>{children}</div> : null),
}));

function PatientCreateDestination() {
  const location = useLocation();
  return <div>Patient create destination {location.search}</div>;
}

function renderList() {
  return render(
    <MemoryRouter initialEntries={['/patients']}>
      <Routes>
        <Route path="/patients" element={<PatientList />} />
        <Route path="/patients/:id" element={<div>Patient detail destination</div>} />
        <Route path="/patients/:id/edit" element={<div>Patient edit destination</div>} />
        <Route path="/patients/new" element={<PatientCreateDestination />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  vi.mocked(api.get).mockResolvedValue({ data: [] } as never);
  vi.mocked(api.delete).mockResolvedValue({ data: {} } as never);
  vi.spyOn(window, 'alert').mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('PatientList G2 interactive matrix', () => {
  it('opens the patient dossier from the row and opens edit without falling through to the row action', async () => {
    const view = renderList();
    expect(await screen.findByText('BENALI Sara')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Modifier les infos' }));
    expect(await screen.findByText('Patient edit destination')).toBeTruthy();

    view.unmount();
    renderList();
    fireEvent.click(await screen.findByText('BENALI Sara'));
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });

  it('requires the exact patient name before deleting and removes locally only after backend success', async () => {
    renderList();
    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer définitivement' }));

    const confirm = screen.getByRole('button', { name: 'Supprimer' }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(true);

    const input = screen.getByPlaceholderText('Sara BENALI');
    fireEvent.change(input, { target: { value: 'wrong' } });
    expect(confirm.disabled).toBe(true);
    expect(api.delete).not.toHaveBeenCalled();

    fireEvent.change(input, { target: { value: 'Sara BENALI' } });
    expect(confirm.disabled).toBe(false);
    fireEvent.click(confirm);

    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/patients/7'));
    await waitFor(() => expect(screen.queryByText('BENALI Sara')).toBeNull());
    expect(setPatientsCache).toHaveBeenCalledWith([]);
  });

  it('preserves the patient locally when deletion fails', async () => {
    vi.mocked(api.delete).mockRejectedValueOnce(new Error('delete failed'));
    renderList();

    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer définitivement' }));
    fireEvent.change(screen.getByPlaceholderText('Sara BENALI'), { target: { value: 'Sara BENALI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));

    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/patients/7'));
    expect(await screen.findByText('BENALI Sara')).toBeTruthy();
    expect(setPatientsCache).not.toHaveBeenCalled();
    expect(window.alert).toHaveBeenCalledWith('Erreur lors de la suppression.');
  });

  it('opens CSV import and creates a prefilled patient from an empty search result', async () => {
    renderList();

    fireEvent.click(await screen.findByRole('button', { name: /Import CSV/i }));
    expect(screen.getByText('CSV modal open')).toBeTruthy();

    const search = screen.getByPlaceholderText('Rechercher par nom, prénom ou dossier...');
    fireEvent.change(search, { target: { value: 'alami nour' } });
    fireEvent.click(await screen.findByRole('button', { name: /Créer "alami nour"/i }));

    expect(await screen.findByText('Patient create destination')).toBeTruthy();
  });

  it('persists the table/grid display choice', async () => {
    renderList();
    fireEvent.click(await screen.findByRole('button', { name: 'Vue Grille' }));
    expect(localStorage.getItem('patient_list_view_mode')).toBe('grid');

    fireEvent.click(screen.getByRole('button', { name: 'Vue Table' }));
    expect(localStorage.getItem('patient_list_view_mode')).toBe('table');
  });
});
