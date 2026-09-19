import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { RvgUploadModal } from './RvgUploadModal';
import { RvgCard } from './RvgCard';
import rvgService from '../../../services/rvgService';

vi.mock('../../../services/rvgService', () => ({
  default: {
    uploadRVG: vi.fn(),
    fetchRVGBlob: vi.fn(),
    deleteRVG: vi.fn(),
  },
}));

vi.mock('../../../hooks/useAuthenticatedImage', () => ({
  useAuthenticatedImage: () => 'blob:thumb',
}));

const doc = {
  id: 44,
  original_filename: 'rvg_16.pdf',
  created_at: '2026-09-19T10:00:00Z',
  clinical_data: {
    radio_type: 'periapical',
    tooth_number: '16',
    sector: 'UR',
    acquisition_date: '2026-09-18',
    note: 'Contrôle endo',
  },
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(rvgService.uploadRVG).mockResolvedValue(doc as never);
  vi.mocked(rvgService.fetchRVGBlob).mockResolvedValue(new Blob(['rvg'], { type: 'application/pdf' }));
  vi.mocked(rvgService.deleteRVG).mockResolvedValue(undefined as never);

  vi.stubGlobal('URL', {
    createObjectURL: vi.fn(() => 'blob:rvg-file'),
    revokeObjectURL: vi.fn(),
  });
  vi.spyOn(window, 'open').mockImplementation(() => ({}) as Window);
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('RVG G4 deep interaction matrix', () => {
  it('keeps save disabled until a file exists and uploads exact metadata only after explicit save', async () => {
    const onSuccess = vi.fn();
    const { container } = render(
      <RvgUploadModal open patientId={7} onClose={vi.fn()} onSuccess={onSuccess} />,
    );

    const save = screen.getByRole('button', { name: 'Enregistrer' }) as HTMLButtonElement;
    expect(save.disabled).toBe(true);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['pdf'], 'rvg_16.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [file] } });

    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'periapical' } });
    fireEvent.change(screen.getByPlaceholderText('ex: 16, 27, 38'), { target: { value: '16' } });
    fireEvent.change(screen.getByPlaceholderText('ex: UR, LL'), { target: { value: 'UR' } });
    fireEvent.change(container.querySelector('input[type="date"]')!, { target: { value: '2026-09-18' } });
    fireEvent.change(screen.getByPlaceholderText('Observations cliniques...'), { target: { value: 'Contrôle endo' } });

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(rvgService.uploadRVG).toHaveBeenCalledWith(
      7,
      expect.objectContaining({
        file,
        radio_type: 'periapical',
        tooth_number: '16',
        sector: 'UR',
        acquisition_date: '2026-09-18',
        note: 'Contrôle endo',
      }),
    ));
    expect(onSuccess).toHaveBeenCalledWith(doc);
  });

  it('surfaces upload refusal and never calls success', async () => {
    vi.mocked(rvgService.uploadRVG).mockRejectedValueOnce({
      response: { data: { detail: 'Fichier RVG refusé' } },
    });
    const onSuccess = vi.fn();
    const onError = vi.fn();
    const { container } = render(
      <RvgUploadModal open patientId={7} onClose={vi.fn()} onSuccess={onSuccess} onError={onError} />,
    );

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['bad'], 'bad.pdf', { type: 'application/pdf' })] } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    expect(await screen.findByText('Fichier RVG refusé')).toBeTruthy();
    expect(onSuccess).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledTimes(1);
  });

  it('opens the file from an authenticated blob boundary', async () => {
    render(<RvgCard doc={doc as never} canDelete canDownload onDelete={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir' }));

    await waitFor(() => expect(rvgService.fetchRVGBlob).toHaveBeenCalledWith(44));
    expect(window.open).toHaveBeenCalledWith('blob:rvg-file', '_blank', 'noopener,noreferrer');
  });

  it('downloads through a fetched blob and revokes the object URL', async () => {
    render(<RvgCard doc={doc as never} canDelete canDownload onDelete={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Télécharger' }));

    await waitFor(() => expect(rvgService.fetchRVGBlob).toHaveBeenCalledWith(44));
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:rvg-file');
  });

  it('deletes only after explicit dialog confirmation and notifies parent only after backend ACK', async () => {
    const onDelete = vi.fn();
    render(<RvgCard doc={doc as never} canDelete canDownload onDelete={onDelete} />);

    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
    expect(screen.getByText('Confirmer la suppression')).toBeTruthy();
    expect(rvgService.deleteRVG).not.toHaveBeenCalled();

    const buttons = screen.getAllByRole('button', { name: 'Supprimer' });
    fireEvent.click(buttons[buttons.length - 1]);

    await waitFor(() => expect(rvgService.deleteRVG).toHaveBeenCalledWith(44));
    expect(onDelete).toHaveBeenCalledWith(44);
  });

  it('preserves the card when deletion is refused', async () => {
    vi.mocked(rvgService.deleteRVG).mockRejectedValueOnce(new Error('delete refused'));
    const onDelete = vi.fn();
    render(<RvgCard doc={doc as never} canDelete canDownload onDelete={onDelete} />);

    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
    const buttons = screen.getAllByRole('button', { name: 'Supprimer' });
    fireEvent.click(buttons[buttons.length - 1]);

    await waitFor(() => expect(rvgService.deleteRVG).toHaveBeenCalledWith(44));
    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByText('Contrôle endo')).toBeTruthy();
  });
});
