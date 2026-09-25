import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PatientRvgPanel } from './components/PatientRvgPanel';
import { RvgCard } from './components/RvgCard';
import { RvgUploadModal } from './components/RvgUploadModal';
import rvgService from '../../services/rvgService';

vi.mock('../../services/rvgService', () => ({
  default: {
    listRVG: vi.fn(),
    uploadRVG: vi.fn(),
    fetchRVGBlob: vi.fn(),
    deleteRVG: vi.fn(),
  },
}));

vi.mock('../../hooks/useAuthenticatedImage', () => ({
  useAuthenticatedImage: () => 'blob:thumbnail',
}));

const doc:any = {
  id: 7,
  original_filename: 'rvg-16.png',
  created_at: '2026-09-19T10:00:00Z',
  clinical_data: {
    radio_type: 'rvg',
    tooth_number: '16',
    sector: 'UR',
    acquisition_date: '2026-09-18',
    note: 'Contrôle endo',
  },
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(rvgService.listRVG).mockResolvedValue([doc]);
  vi.mocked(rvgService.uploadRVG).mockResolvedValue(doc);
  vi.mocked(rvgService.fetchRVGBlob).mockResolvedValue(new Blob(['x'], { type: 'image/png' }));
  vi.mocked(rvgService.deleteRVG).mockResolvedValue(undefined);
  vi.stubGlobal('URL', {
    createObjectURL: vi.fn(() => 'blob:rvg-file'),
    revokeObjectURL: vi.fn(),
  });
  vi.spyOn(window, 'open').mockImplementation(() => ({}) as Window);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('RVG G4 interactive matrix', () => {
  it('distinguishes backend load failure from a truthful empty state and retries', async () => {
    vi.mocked(rvgService.listRVG)
      .mockRejectedValueOnce(new Error('load failed'))
      .mockResolvedValueOnce([]);

    render(<PatientRvgPanel patientId={7} />);

    expect(await screen.findByText('Impossible de charger les RVG')).toBeTruthy();
    expect(screen.queryByText('Aucune radio intra-orale enregistrée')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /Réessayer/i }));
    expect(await screen.findByText('Aucune radio intra-orale enregistrée')).toBeTruthy();
    expect(rvgService.listRVG).toHaveBeenCalledTimes(2);
  });

  it('opens the upload flow and prepends the uploaded RVG only after service success', async () => {
    vi.mocked(rvgService.listRVG).mockResolvedValueOnce([]);

    render(<PatientRvgPanel patientId={7} />);
    await screen.findByText('Aucune radio intra-orale enregistrée');

    fireEvent.click(screen.getByRole('button', { name: /Ajouter une RVG/i }));
    expect(screen.getByText('Ajouter une radio RVG')).toBeTruthy();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['rvg'], 'rvg-16.png', { type: 'image/png' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'periapical' } });
    fireEvent.change(screen.getByPlaceholderText('ex: 16, 27, 38'), { target: { value: '16' } });
    fireEvent.change(screen.getByPlaceholderText('ex: UR, LL'), { target: { value: 'UR' } });
    fireEvent.change(screen.getByRole('textbox', { name: /Note/i }), { target: { value: 'Contrôle endo' } });

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(rvgService.uploadRVG).toHaveBeenCalledWith(
      7,
      expect.objectContaining({
        file,
        radio_type: 'periapical',
        tooth_number: '16',
        sector: 'UR',
        note: 'Contrôle endo',
      }),
    ));
    expect(await screen.findByText('Dent 16')).toBeTruthy();
  });

  it('keeps upload modal open and surfaces backend detail on upload refusal', async () => {
    vi.mocked(rvgService.uploadRVG).mockRejectedValueOnce({
      response: { data: { detail: 'Fichier refusé' } },
    });
    const onClose = vi.fn();
    const onSuccess = vi.fn();

    render(<RvgUploadModal open patientId={7} onClose={onClose} onSuccess={onSuccess} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [new File(['x'], 'bad.png', { type: 'image/png' })] } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    expect(await screen.findByText('Fichier refusé')).toBeTruthy();
    expect(onSuccess).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('opens and downloads the exact RVG blob', async () => {
    const click = vi.fn();
    const append = vi.spyOn(document.body, 'appendChild');
    const originalCreate = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation(((tagName: string) => {
      const element = originalCreate(tagName);
      if (tagName === 'a') Object.defineProperty(element, 'click', { value: click });
      return element;
    }) as typeof document.createElement);

    render(<RvgCard doc={doc} canDelete canDownload />);

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir' }));
    await waitFor(() => expect(rvgService.fetchRVGBlob).toHaveBeenCalledWith(7));
    expect(window.open).toHaveBeenCalledWith('blob:rvg-file', '_blank', 'noopener,noreferrer');

    fireEvent.click(screen.getByRole('button', { name: 'Télécharger' }));
    await waitFor(() => expect(rvgService.fetchRVGBlob).toHaveBeenCalledTimes(2));
    expect(append).toHaveBeenCalled();
    expect(click).toHaveBeenCalledTimes(1);
  });

  it('deletes only after explicit confirmation and calls onDelete only after ACK', async () => {
    const onDelete = vi.fn();
    render(<RvgCard doc={doc} canDelete canDownload onDelete={onDelete} />);

    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
    expect(screen.getByText('Confirmer la suppression')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(rvgService.deleteRVG).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
    const deleteButtons = screen.getAllByRole('button', { name: 'Supprimer' });
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);

    await waitFor(() => expect(rvgService.deleteRVG).toHaveBeenCalledWith(7));
    expect(onDelete).toHaveBeenCalledWith(7);
  });

  it('preserves the RVG when deletion is refused', async () => {
    vi.mocked(rvgService.deleteRVG).mockRejectedValueOnce(new Error('delete refused'));
    const onDelete = vi.fn();

    render(<RvgCard doc={doc} canDelete onDelete={onDelete} />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
    const deleteButtons = screen.getAllByRole('button', { name: 'Supprimer' });
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);

    await waitFor(() => expect(rvgService.deleteRVG).toHaveBeenCalledWith(7));
    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByText('Dent 16')).toBeTruthy();
  });
});
