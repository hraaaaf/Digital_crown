import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PatientList } from './PatientList';

vi.mock('../../services/api', () => ({
  API_BASE: 'http://127.0.0.1:8005',
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

  it('keeps a single semantic patient row while stacking cells for narrow viewports', () => {
    renderList();

    const table = screen.getByRole('table');
    const head = table.querySelector('thead');
    const body = table.querySelector('tbody');
    const row = screen.getByText('ALAMI Nour').closest('tr')!;
    const identity = screen.getByText('ALAMI Nour');

    expect(table.classList.contains('block')).toBe(true);
    expect(table.classList.contains('md:table')).toBe(true);
    expect(head?.classList.contains('md:table-header-group')).toBe(true);
    expect(body?.classList.contains('md:table-row-group')).toBe(true);
    expect(row.classList.contains('block')).toBe(true);
    expect(row.classList.contains('md:table-row')).toBe(true);
    expect(row.querySelectorAll('td')).toHaveLength(4);
    expect(row.querySelector('td')?.classList.contains('md:table-cell')).toBe(true);
    expect(identity.classList.contains('break-words')).toBe(true);
    expect(screen.getAllByText('ALAMI Nour')).toHaveLength(1);
  });

  it('opens a patient dossier from the keyboard-accessible row', async () => {
    renderList();
    const row = screen.getByText('ALAMI Nour').closest('tr')!;
    fireEvent.keyDown(row, { key: 'Enter' });
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });
});
