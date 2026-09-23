import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from '../services/api';
import {
  createLab,
  createLabJob,
  deleteLab,
  fetchLabJobs,
  fetchLabs,
  patchLabJobStatus,
} from '../services/labJobService';
import { LabJobsBoard } from './LabJobsBoard';

vi.mock('../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

vi.mock('../services/labJobService', () => ({
  fetchLabJobs: vi.fn(),
  patchLabJobStatus: vi.fn(),
  createLabJob: vi.fn(),
  fetchLabs: vi.fn(),
  createLab: vi.fn(),
  deleteLab: vi.fn(),
}));

describe('CUST-05 laboratory customization', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchLabJobs).mockResolvedValue([]);
    vi.mocked(fetchLabs).mockResolvedValue([
      { id: 12, name: 'Atlas Dental', phone: '0600000000' },
    ]);
    vi.mocked(api.get).mockResolvedValue({
      data: [
        { id: 1, nom: 'Zircone', categorie: 'MATERIAU' },
        { id: 2, nom: 'Gants', categorie: 'CONSOMMABLE' },
      ],
    } as never);
    vi.mocked(createLabJob).mockResolvedValue({} as never);
    vi.mocked(createLab).mockResolvedValue({ id: 13, name: 'Nouveau labo' });
    vi.mocked(deleteLab).mockResolvedValue();
    vi.mocked(patchLabJobStatus).mockResolvedValue({} as never);
  });

  it('loads cabinet laboratories and stock-backed material suggestions', async () => {
    render(<LabJobsBoard />);

    fireEvent.click(await screen.findByRole('button', { name: /Nouvelle demande/i }));

    expect(await screen.findByRole('option', { name: 'Atlas Dental' })).toBeTruthy();
    expect(screen.getByText(/Suggestions issues des matériaux enregistrés dans Stock/i)).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/stock/items');
  });

  it('creates a lab job with the explicitly selected cabinet laboratory', async () => {
    render(<LabJobsBoard />);

    fireEvent.click(await screen.findByRole('button', { name: /Nouvelle demande/i }));

    fireEvent.change(screen.getByLabelText(/N° patient/i), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText(/N° acte/i), { target: { value: '20' } });
    fireEvent.change(screen.getByLabelText(/^Laboratoire$/i), { target: { value: '12' } });
    fireEvent.change(screen.getByLabelText(/^Matériau$/i), { target: { value: 'Zircone' } });

    fireEvent.click(screen.getByRole('button', { name: /Créer la demande/i }));

    await waitFor(() => {
      expect(createLabJob).toHaveBeenCalledWith(expect.objectContaining({
        patient_id: 10,
        act_id: 20,
        lab_id: 12,
        material: 'Zircone',
      }));
    });
  });

  it('creates a new cabinet laboratory from the manager', async () => {
    render(<LabJobsBoard />);

    fireEvent.click(await screen.findByRole('button', { name: /Gérer les laboratoires/i }));
    fireEvent.change(screen.getByPlaceholderText('Nom du laboratoire'), {
      target: { value: 'Nouveau labo' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Ajouter le laboratoire/i }));

    await waitFor(() => {
      expect(createLab).toHaveBeenCalledWith({
        name: 'Nouveau labo',
        phone: undefined,
      });
    });
  });
});
