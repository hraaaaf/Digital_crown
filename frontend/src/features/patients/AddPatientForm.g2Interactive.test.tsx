import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AddPatientForm } from './AddPatientForm';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('./components/MotifSelector', () => ({
  MotifSelector: () => <div>Motif selector</div>,
}));

function renderForm(entry = '/patients/new?nom=BENALI&prenom=Sara') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/patients/new" element={<AddPatientForm />} />
        <Route path="/patients" element={<div>Patient list destination</div>} />
        <Route path="/patients/:id" element={<div>Patient detail destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function fillRequired(container: HTMLElement) {
  const birth = container.querySelector('input[name="date_naissance"]') as HTMLInputElement;
  const sex = container.querySelector('select[name="sexe"]') as HTMLSelectElement;
  fireEvent.change(birth, { target: { value: '1990-01-01' } });
  fireEvent.change(sex, { target: { value: 'F' } });
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/next-dossier-number') return { data: { next_number: 'P-000008' } } as never;
    if (url.startsWith('/patients/check-dossier/')) return { data: { exists: false } } as never;
    throw new Error(`unexpected GET ${url}`);
  });
});

afterEach(() => cleanup());

describe('AddPatientForm G2 interactive matrix', () => {
  it('creates only after identity validation and a successful anti-duplicate check', async () => {
    vi.mocked(api.post).mockImplementation(async (url: string) => {
      if (url === '/patients/check-duplicate') return { data: { has_duplicate: false } } as never;
      if (url === '/patients/') return { data: { id: 8 } } as never;
      throw new Error(`unexpected POST ${url}`);
    });

    const { container } = renderForm();
    fillRequired(container);
    fireEvent.click(screen.getByRole('button', { name: 'Créer le dossier' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/patients/check-duplicate',
      expect.objectContaining({ nom: 'BENALI', prenom: 'Sara', date_naissance: '1990-01-01', sexe: 'F' }),
    ));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/patients/',
      expect.objectContaining({ nom: 'BENALI', prenom: 'Sara', date_naissance: '1990-01-01', sexe: 'F' }),
    ));
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });

  it('fails closed when anti-duplicate verification is unavailable', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('duplicate service unavailable'));

    const { container } = renderForm();
    fillRequired(container);
    fireEvent.click(screen.getByRole('button', { name: 'Créer le dossier' }));

    expect(await screen.findByText(/Vérification anti-doublon indisponible/i)).toBeTruthy();
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('Patient detail destination')).toBeNull();
  });

  it('does not create a detected duplicate until the user explicitly chooses force-create', async () => {
    vi.mocked(api.post).mockImplementation(async (url: string) => {
      if (url === '/patients/check-duplicate') {
        return {
          data: {
            has_duplicate: true,
            existing_patient: {
              id: 4,
              nom: 'BENALI',
              prenom: 'Sara',
              date_naissance: '1990-01-01',
              created_at: '2025-01-01T00:00:00Z',
            },
          },
        } as never;
      }
      if (url === '/patients/?force_create=true') return { data: { id: 9 } } as never;
      throw new Error(`unexpected POST ${url}`);
    });

    const { container } = renderForm();
    fillRequired(container);
    fireEvent.click(screen.getByRole('button', { name: 'Créer le dossier' }));

    expect(await screen.findByText('Patient similaire trouvé')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalledWith('/patients/?force_create=true', expect.anything());

    fireEvent.click(screen.getByRole('button', { name: /Créer quand même/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/patients/?force_create=true',
      expect.objectContaining({ nom: 'BENALI', prenom: 'Sara' }),
    ));
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });

  it('can open the detected existing dossier without creating another patient', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        has_duplicate: true,
        existing_patient: {
          id: 4,
          nom: 'BENALI',
          prenom: 'Sara',
          date_naissance: '1990-01-01',
          created_at: '2025-01-01T00:00:00Z',
        },
      },
    } as never);

    const { container } = renderForm();
    fillRequired(container);
    fireEvent.click(screen.getByRole('button', { name: 'Créer le dossier' }));

    fireEvent.click(await screen.findByRole('button', { name: /Ouvrir le dossier existant/i }));
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
    expect(api.post).toHaveBeenCalledTimes(1);
  });

  it('cancels to the patient list without creating', async () => {
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(await screen.findByText('Patient list destination')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalled();
  });
});
