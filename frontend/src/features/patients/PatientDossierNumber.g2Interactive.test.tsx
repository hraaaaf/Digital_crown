import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AddPatientForm } from './AddPatientForm';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));
vi.mock('./components/MotifSelector', () => ({ MotifSelector: () => null }));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/next-dossier-number') return { data: { next_number: 'P-000008' } } as never;
    if (url === '/patients/check-dossier/P-TAKEN') return { data: { exists: true, patient_name: 'Patient Existant' } } as never;
    if (url === '/patients/check-dossier/P-FREE') return { data: { exists: false } } as never;
    if (url.startsWith('/patients/check-dossier/')) return { data: { exists: false } } as never;
    throw new Error('unexpected GET ' + url);
  });
});
afterEach(() => cleanup());

describe('AddPatientForm G2 dossier-number availability', () => {
  it('shows backend truth for taken and available dossier numbers', async () => {
    render(<MemoryRouter><AddPatientForm /></MemoryRouter>);
    const input = await screen.findByPlaceholderText('P-XXXXXX');

    fireEvent.change(input, { target: { value: 'P-TAKEN' } });
    expect(await screen.findByText(/Ce numéro appartient déjà à/i, {}, { timeout: 2000 })).toBeTruthy();
    expect(screen.getByText(/Patient Existant/)).toBeTruthy();

    fireEvent.change(input, { target: { value: 'P-FREE' } });
    expect(await screen.findByText(/Numéro disponible/i, {}, { timeout: 2000 })).toBeTruthy();
  });

  it('shows an unverified state when dossier-number verification fails', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/next-dossier-number') return { data: { next_number: '' } } as never;
      if (url === '/patients/check-dossier/P-ERR') throw new Error('availability failed');
      return { data: { exists: false } } as never;
    });

    render(<MemoryRouter><AddPatientForm /></MemoryRouter>);
    fireEvent.change(await screen.findByPlaceholderText('P-XXXXXX'), { target: { value: 'P-ERR' } });

    expect(await screen.findByText(/Impossible de vérifier la disponibilité/i, {}, { timeout: 2000 })).toBeTruthy();
  });
});
