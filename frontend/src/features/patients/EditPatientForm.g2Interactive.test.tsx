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

const patient = {
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
  vi.mocked(api.get).mockResolvedValue({ data: patient } as never);
  vi.mocked(api.put).mockResolvedValue({ data: patient } as never);
  vi.spyOn(window, 'alert').mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('EditPatientForm G2 interactive matrix', () => {
  it('hydrates from backend truth and saves the edited identity before navigating back to the dossier', async () => {
    renderForm();

    const nameInput = await screen.findByDisplayValue('BENALI');
    fireEvent.change(nameInput, { target: { value: 'EL AMRANI' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/i }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith(
      '/patients/7',
      expect.objectContaining({ nom: 'EL AMRANI', prenom: 'Sara', sexe: 'F' }),
    ));
    expect(await screen.findByText('Patient detail destination')).toBeTruthy();
  });

  it('shows a truthful load error and retries instead of rendering default patient values', async () => {
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error('load failed'))
      .mockResolvedValueOnce({ data: patient } as never);

    renderForm();

    expect(await screen.findByText('Impossible de charger le patient')).toBeTruthy();
    expect(screen.getByText(/Le formulaire n'est pas affiché avec des valeurs par défaut/i)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Réessayer/i }));
    expect(await screen.findByDisplayValue('BENALI')).toBeTruthy();
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it('surfaces a dossier-number conflict and does not navigate on backend refusal', async () => {
    vi.mocked(api.put).mockRejectedValueOnce({
      response: {
        status: 409,
        data: { detail: { message: 'Ce numéro de dossier est déjà utilisé.' } },
      },
    });

    renderForm();
    await screen.findByDisplayValue('BENALI');
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/i }));

    expect(await screen.findByText(/Ce numéro de dossier est déjà utilisé/i)).toBeTruthy();
    expect(screen.queryByText('Patient detail destination')).toBeNull();
  });

  it('keeps the user on the form and reports a generic save failure without false success', async () => {
    vi.mocked(api.put).mockRejectedValueOnce(new Error('save failed'));

    renderForm();
    await screen.findByDisplayValue('BENALI');
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/i }));

    await waitFor(() => expect(window.alert).toHaveBeenCalledWith('Erreur lors de la sauvegarde.'));
    expect(screen.queryByText('Patient detail destination')).toBeNull();
  });
});
