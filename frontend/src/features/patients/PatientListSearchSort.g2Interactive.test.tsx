import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PatientList } from './PatientList';

vi.mock('../../services/api', () => ({
  api: { get: vi.fn().mockResolvedValue({ data: [] }), delete: vi.fn() },
}));

vi.mock('../../stores/usePatientStore', () => ({
  usePatientStore: () => ({
    patientsCache: [
      { id: 2, nom: 'ZIANI', prenom: 'Omar', numero_dossier: 'P-000002', assurance: 'CNSS', telephone: '' },
      { id: 9, nom: 'ALAMI', prenom: 'Nour', numero_dossier: 'P-000009', assurance: 'CNOPS', telephone: '' },
    ],
    patientsCacheLoaded: true,
    patientsCacheUpdatedAt: Date.now(),
    setPatientsCache: vi.fn(),
  }),
}));

vi.mock('../admin/Settings/hooks/useSettingsStore', () => ({
  useSettingsStore: (selector: (state: { profile: { show_patient_badges: boolean } }) => unknown) =>
    selector({ profile: { show_patient_badges: false } }),
}));
vi.mock('./components/PatientScoreBadge', () => ({ PatientScoreBadge: () => null }));
vi.mock('./components/PatientSummaryHoverCard', () => ({ PatientSummaryHoverCard: () => null }));
vi.mock('../../components/AssuranceBadge', () => ({ AssuranceBadge: () => <span>Assurance</span> }));
vi.mock('./CsvImportModal', () => ({ CsvImportModal: () => null }));
vi.mock('../../components/CrownDialog', () => ({ CrownDialog: () => null }));

function renderList() {
  return render(
    <MemoryRouter initialEntries={['/patients']}>
      <Routes>
        <Route path="/patients" element={<PatientList />} />
        <Route path="/patients/:id" element={<div>Patient detail destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => localStorage.clear());
afterEach(() => cleanup());

describe('PatientList G2 search, sort and keyboard matrix', () => {
  it('filters by patient name and dossier number', () => {
    renderList();
    const search = screen.getByPlaceholderText('Rechercher par nom, prénom ou dossier...');

    fireEvent.change(search, { target: { value: 'ALAMI' } });
    expect(screen.getByText('ALAMI Nour')).toBeTruthy();
    expect(screen.queryByText('ZIANI Omar')).toBeNull();

    fireEvent.change(search, { target: { value: 'P-000002' } });
    expect(screen.getByText('ZIANI Omar')).toBeTruthy();
    expect(screen.queryByText('ALAMI Nour')).toBeNull();
  });

  it('applies alphabetical sort choices to the rendered rows', () => {
    renderList();
    const sort = screen.getByRole('combobox');

    fireEvent.change(sort, { target: { value: 'az' } });
    let rows = screen.getAllByRole('button').filter(el => el.tagName === 'TR');
    expect(rows[0].textContent).toContain('ALAMI Nour');
    expect(rows[1].textContent).toContain('ZIANI Omar');

    fireEvent.change(sort, { target: { value: 'za' } });
    rows = screen.getAllByRole('button').filter(el => el.tagName === 'TR');
    expect(rows[0].textContent).toContain('ZIANI Omar');
    expect(rows[1].textContent).toContain('ALAMI Nour');
  });

  it('opens a patient dossier from the keyboard-accessible row', async () => {
    renderList();
    const row = screen.getByText('ALAMI Nour').closest('tr')!;
    fireEvent.keyDown(row, { key: 'Enter' });
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });
});
