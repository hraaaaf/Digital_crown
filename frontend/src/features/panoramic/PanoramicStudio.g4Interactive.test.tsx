import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PanoramicStudio } from './PanoramicStudio';
import { usePanoramicStore } from './stores/usePanoramicStore';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  API_BASE: 'http://api.test',
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}));

vi.mock('../../hooks/useAuthenticatedImage', () => ({
  useAuthenticatedImage: (url: string) => url,
}));

vi.mock('./XRayCanvas', () => ({
  XRayCanvas: ({ filterString, onImgLoad }: any) => (
    <div data-testid="xray-canvas" data-filter={filterString}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onImgLoad?.({ currentTarget: { naturalWidth: 1000, naturalHeight: 500 } });
        }}
      >
        Load image dimensions
      </button>
    </div>
  ),
}));

vi.mock('./PanoramicHistory', () => ({
  PanoramicHistory: ({ onSelect }: any) => (
    <div>
      <span>Panoramic history list</span>
      <button
        type="button"
        onClick={() => onSelect({
          id: 41,
          image_path: 'archive.jpg',
          detections_data: { visual_annotations: [] },
          report_narrative: 'Archive report',
          created_at: '2026-01-01T00:00:00Z',
        })}
      >
        Select archived panoramic
      </button>
    </div>
  ),
}));

vi.mock('./ReportViewer', () => ({
  ReportViewer: ({ markdown, onDownload, onPreview, onSaveEdit }: any) => (
    <div>
      <span>Report content: {markdown || 'empty'}</span>
      <button type="button" onClick={onPreview}>Preview report</button>
      <button type="button" onClick={onDownload}>Download report</button>
      <button type="button" onClick={() => onSaveEdit('Edited report')}>Save edited report</button>
    </div>
  ),
}));

vi.mock('../admin/DocumentStudio/LivePreview', () => ({
  LivePreview: ({ title, onClose }: any) => (
    <div>
      <span>{title}</span>
      <button type="button" onClick={onClose}>Close preview</button>
    </div>
  ),
}));

const uploadResult = {
  id: 55,
  image_path: 'current.jpg',
  vision: {
    detections_data: {
      detections: [
        { id: 'd1', rejected: false },
        { id: 'd2', rejected: true },
      ],
    },
  },
  report_narrative: '',
  created_at: '2026-09-19T12:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
  usePanoramicStore.getState().resetAll();
  localStorage.clear();

  vi.mocked(api.get).mockImplementation(async (url: string, config?: any) => {
    if (url === '/ia/patients/7/panoramic-comparison') {
      return { data: { available: false, reason: 'Deux bilans requis' } } as never;
    }
    if (url === '/ia/panoramic/55/pdf' && config?.responseType === 'blob') {
      return { data: new Blob(['pdf'], { type: 'application/pdf' }) } as never;
    }
    throw new Error('unexpected GET ' + url);
  });

  vi.mocked(api.post).mockImplementation(async (url: string) => {
    if (url === '/ia/upload-panoramic?patient_id=7') return { data: uploadResult } as never;
    if (url === '/ia/generate-panoramic-report') {
      return { data: { report_narrative: 'Generated clinical report' } } as never;
    }
    throw new Error('unexpected POST ' + url);
  });

  vi.mocked(api.put).mockResolvedValue({ data: { report_narrative: 'Edited report' } } as never);

  vi.stubGlobal('URL', {
    createObjectURL: vi.fn(() => 'blob:pano-pdf'),
    revokeObjectURL: vi.fn(),
  });
  vi.spyOn(window, 'open').mockImplementation(() => ({}) as Window);
  vi.spyOn(window, 'prompt').mockReturnValue('Détail clinique manuel');
});

afterEach(() => {
  cleanup();
  usePanoramicStore.getState().resetAll();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function uploadPanoramic() {
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(['image'], 'pano.jpg', { type: 'image/jpeg' });
  fireEvent.change(input, { target: { files: [file] } });
  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/ia/upload-panoramic?patient_id=7',
    expect.any(FormData),
    { headers: { 'Content-Type': 'multipart/form-data' } },
  ));
  expect(await screen.findByTestId('xray-canvas')).toBeTruthy();
  await waitFor(() => expect(screen.getByRole('button', { name: /VALIDER ET GÉNÉRER/i })).not.toBeDisabled());
}

describe('PanoramicStudio G4 deep interaction matrix', () => {
  it('uses semantic theme tokens for the clinical-entry helper', async () => {
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    await uploadPanoramic();

    const title = screen.getByText('Mode Saisie Clinique');
    const helper = title.parentElement?.parentElement;
    const icon = helper?.firstElementChild;

    expect(helper?.className).toContain('bg-primary/10');
    expect(helper?.className).toContain('border-primary/20');
    expect(title.className).toContain('text-primary');
    expect(icon?.className).toContain('bg-primary');
    expect(helper?.className).not.toContain('indigo');
  });

  it('uploads a new panoramic exam and keeps the empty state until backend ACK', async () => {
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    expect(screen.getByText('AUCUNE RADIOGRAPHIE CHARGÉE')).toBeTruthy();

    await uploadPanoramic();

    expect(screen.queryByText('AUCUNE RADIOGRAPHIE CHARGÉE')).toBeNull();
    expect(screen.getByRole('button', { name: 'Constatations' })).toBeTruthy();
  });

  it('preserves the empty/no-result state when upload is refused', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'Image refusée' } } });
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['bad'], 'bad.jpg', { type: 'image/jpeg' })] } });

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('AUCUNE RADIOGRAPHIE CHARGÉE')).toBeTruthy();
    expect(screen.queryByTestId('xray-canvas')).toBeNull();
  });

  it('toggles a global finding and finalizes with practitioner findings only after explicit action', async () => {
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    await uploadPanoramic();

    fireEvent.click(screen.getByRole('button', { name: 'Alvéolyse généralisée légère' }));
    expect(usePanoramicStore.getState().globalFindings).toContain('alveolyse_gen_legere');

    fireEvent.click(screen.getByRole('button', { name: /VALIDER ET GÉNÉRER/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/ia/generate-panoramic-report',
      expect.objectContaining({
        analysis_id: 55,
        manual_anomalies: {},
        global_findings: ['alveolyse_gen_legere'],
        rejected_detections: [1],
        visual_annotations: [],
        report_context: expect.any(Object),
      }),
    ));

    expect(await screen.findByText('Report content: Generated clinical report')).toBeTruthy();
    expect(usePanoramicStore.getState().globalFindings).toEqual([]);
  });

  it('does not clear practitioner findings when report generation fails', async () => {
    vi.mocked(api.post).mockImplementation(async (url: string) => {
      if (url === '/ia/upload-panoramic?patient_id=7') return { data: uploadResult } as never;
      if (url === '/ia/generate-panoramic-report') {
        throw { response: { data: { detail: 'Génération refusée' } } };
      }
      throw new Error('unexpected POST ' + url);
    });

    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    await uploadPanoramic();

    fireEvent.click(screen.getByRole('button', { name: 'Alvéolyse généralisée légère' }));
    fireEvent.click(screen.getByRole('button', { name: /VALIDER ET GÉNÉRER/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/ia/generate-panoramic-report',
      expect.any(Object),
    ));
    expect(usePanoramicStore.getState().globalFindings).toContain('alveolyse_gen_legere');
  });

  it('previews, downloads and edits the archived report through separate backend boundaries', async () => {
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    await uploadPanoramic();

    fireEvent.click(screen.getByRole('button', { name: 'Bilan PDF' }));

    fireEvent.click(screen.getByRole('button', { name: 'Preview report' }));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(
      '/ia/panoramic/55/pdf',
      { responseType: 'blob' },
    ));
    expect(await screen.findByText('Aperçu du Bilan Panoramique')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Close preview' }));
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Close preview' })).toBeNull());

    fireEvent.click(screen.getByRole('button', { name: 'Download report' }));
    await waitFor(() => expect(window.open).toHaveBeenCalledWith(
      'blob:pano-pdf',
      '_blank',
      'noopener,noreferrer',
    ));

    fireEvent.click(screen.getByRole('button', { name: 'Save edited report' }));
    await waitFor(() => expect(api.put).toHaveBeenCalledWith(
      '/ia/panoramic/55/report',
      { report_narrative: 'Edited report' },
    ));
    expect(await screen.findByText('Report content: Edited report')).toBeTruthy();
  });

  it('opens history, loads an archived exam, and supports T0/T1 comparison selection', async () => {
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    await uploadPanoramic();

    fireEvent.click(screen.getByRole('button', { name: 'Historique' }));
    expect(screen.getByText('Panoramic history list')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Select archived panoramic' }));
    expect(screen.getByTestId('xray-canvas')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Comparer T0/T1' }));
    expect(screen.getByText('Panoramic history list')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Select archived panoramic' }));

    expect(screen.getByText(/Archive \(T0\)/)).toBeTruthy();
    expect(screen.getByText(/Examen Actuel \(T1\)/)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Quitter Comparaison' }));
    expect(screen.queryByText(/Archive \(T0\)/)).toBeNull();
  });

  it('applies and resets image tools and records/removes a manual annotation locally', async () => {
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    await uploadPanoramic();

    const canvas = screen.getByTestId('xray-canvas');
    expect(canvas.getAttribute('data-filter')).toContain('invert(0%)');

    fireEvent.click(screen.getByTitle('Inverser les couleurs (Négatif)'));
    expect(screen.getByTestId('xray-canvas').getAttribute('data-filter')).toContain('invert(100%)');

    fireEvent.click(screen.getByTitle('Réinitialiser les filtres'));
    expect(screen.getByTestId('xray-canvas').getAttribute('data-filter')).toContain('invert(0%)');

    fireEvent.click(screen.getByTitle('Ajouter un détail clinique'));
    fireEvent.click(screen.getByTestId('xray-canvas'));
    expect(await screen.findByText('Détail clinique manuel')).toBeTruthy();

    const annotationRow = screen.getByText('Détail clinique manuel').closest('div')!;
    const remove = annotationRow.querySelector('button');
    if (!remove) throw new Error('annotation remove control missing');
    fireEvent.click(remove);
    expect(screen.queryByText('Détail clinique manuel')).toBeNull();
  });

  it('shows evolution as unavailable from backend truth instead of fabricating trend data', async () => {
    render(<PanoramicStudio patientId={7} patientName="Sara BENALI" />);
    await uploadPanoramic();

    fireEvent.click(screen.getByRole('button', { name: 'Évolution' }));
    expect(await screen.findByText('Évolution indisponible')).toBeTruthy();
    expect(screen.getByText('Deux bilans requis')).toBeTruthy();
  });
});
