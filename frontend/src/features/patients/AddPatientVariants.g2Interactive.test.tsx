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

function renderForm() {
  return render(
    <MemoryRouter initialEntries={['/patients/new?nom=BENALI&prenom=Sara']}>
      <Routes>
        <Route path="/patients/new" element={<AddPatientForm />} />
        <Route path="/patients/:id" element={<div>Patient detail destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/next-dossier-number') return { data: { next_number: 'P-000008' } } as never;
    if (url.startsWith('/patients/check-dossier/')) return { data: { exists: false } } as never;
    throw new Error('unexpected GET ' + url);
  });
  vi.mocked(api.post).mockImplementation(async (url: string) => {
    if (url === '/patients/check-duplicate') return { data: { has_duplicate: false } } as never;
    if (url === '/patients/') return { data: { id: 8 } } as never;
    throw new Error('unexpected POST ' + url);
  });
});

afterEach(() => cleanup());

describe('AddPatientForm G2 variant controls', () => {
  it('persists extra phones, private/complementary insurance and ortho activation in the create payload', async () => {
    const { container } = renderForm();

    fireEvent.change(container.querySelector('input[name="date_naissance"]')!, { target: { value: '1990-01-01' } });
    fireEvent.change(container.querySelector('select[name="sexe"]')!, { target: { value: 'F' } });

    fireEvent.click(screen.getByRole('button', { name: '+ Ajouter un numéro' }));
    fireEvent.change(screen.getByPlaceholderText('Téléphone secondaire'), { target: { value: '0611111111' } });

    fireEvent.click(screen.getByRole('button', { name: '+ Ajouter un numéro' }));
    fireEvent.change(screen.getByPlaceholderText('Autre numéro'), { target: { value: '0622222222' } });

    fireEvent.change(container.querySelector('select[name="assurance"]')!, { target: { value: 'PRIVEE' } });
    fireEvent.change(screen.getByPlaceholderText('Ex: Sanlam, Wafa Assurance...'), { target: { value: 'Sanlam' } });

    fireEvent.click(screen.getByText('Assurance Complémentaire'));
    fireEvent.change(screen.getByPlaceholderText('Ex: Mutuelle interne...'), { target: { value: 'Mutuelle Test' } });

    fireEvent.click(screen.getByText('Suivi Orthodontique'));

    fireEvent.click(screen.getByRole('button', { name: 'Créer le dossier' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/patients/',
      expect.objectContaining({
        nom: 'BENALI',
        prenom: 'Sara',
        sexe: 'F',
        telephone_2: '0611111111',
        telephone_3: '0622222222',
        assurance: 'PRIVEE',
        assurance_privee_nom: 'Sanlam',
        assurance_complementaire: true,
        assurance_complementaire_nom: 'Mutuelle Test',
        is_ortho_active: true,
      }),
    ));
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });
});
