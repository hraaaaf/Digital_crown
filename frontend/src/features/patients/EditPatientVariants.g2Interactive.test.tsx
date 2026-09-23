import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { EditPatientForm } from './EditPatientForm';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock('./components/MotifSelector', () => ({
  MotifSelector: () => <div>Motif selector</div>,
}));

const basePatient = {
  id: 7,
  numero_dossier: 'P-000007',
  nom: 'BENALI',
  prenom: 'Sara',
  date_naissance: '1990-01-01',
  sexe: 'F',
  telephone: '0600000000',
  telephone_2: '',
  telephone_3: '',
  email: 'sara@example.com',
  adresse: '',
  assurance: 'CNSS',
  assurance_privee_nom: '',
  assurance_complementaire: false,
  assurance_complementaire_nom: '',
  antecedents_medicaux: '',
  motif_consultation: [],
};

function renderForm() {
  return render(
    <MemoryRouter initialEntries={['/patients/7/edit']}>
      <Routes>
        <Route path="/patients/:id/edit" element={<EditPatientForm />} />
        <Route path="/patients/:id" element={<div>Patient detail destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/7') return { data: basePatient } as never;
    if (url.startsWith('/patients/check-dossier/')) return { data: { exists: false } } as never;
    throw new Error('unexpected GET ' + url);
  });
  vi.mocked(api.put).mockResolvedValue({ data: basePatient } as never);
});

afterEach(() => cleanup());

describe('EditPatientForm G2 variant controls', () => {
  it('persists extra phones and private/complementary insurance in the edit payload', async () => {
    const { container } = renderForm();
    await screen.findByDisplayValue('BENALI');

    fireEvent.click(screen.getByRole('button', { name: '+ Ajouter un numéro' }));
    fireEvent.change(screen.getByPlaceholderText('Téléphone secondaire'), { target: { value: '0611111111' } });

    fireEvent.click(screen.getByRole('button', { name: '+ Ajouter un numéro' }));
    fireEvent.change(screen.getByPlaceholderText('Autre numéro'), { target: { value: '0622222222' } });

    fireEvent.change(container.querySelector('select[name="assurance"]')!, { target: { value: 'PRIVEE' } });
    fireEvent.change(screen.getByPlaceholderText('Ex: Sanlam, Wafa Assurance...'), { target: { value: 'Sanlam' } });

    fireEvent.click(screen.getByText('Assurance Complémentaire'));
    fireEvent.change(screen.getByPlaceholderText('Ex: Mutuelle interne...'), { target: { value: 'Mutuelle Test' } });

    fireEvent.click(screen.getByRole('button', { name: 'Valider les modifications' }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith(
      '/patients/7',
      expect.objectContaining({
        telephone_2: '0611111111',
        telephone_3: '0622222222',
        assurance: 'PRIVEE',
        assurance_privee_nom: 'Sanlam',
        assurance_complementaire: true,
        assurance_complementaire_nom: 'Mutuelle Test',
      }),
    ));
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });
});
