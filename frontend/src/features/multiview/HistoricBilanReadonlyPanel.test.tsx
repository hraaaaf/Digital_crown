import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../services/api';
import { HistoricBilanReadonlyPanel } from './HistoricBilanReadonlyPanel';

vi.mock('../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:r2-bilan-synthetic') });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
});
afterEach(() => cleanup());

describe('DEC-R2-02 MultiView BILAN R-only adapter', () => {
  it('shows only typed BILAN and opens exclusively authenticated GET bytes', async () => {
    vi.mocked(api.get).mockImplementation((url) => {
      if (url === '/patients/17/documents') return Promise.resolve({ data: [
        { id: '41', type: 'BILAN', name: 'Bilan synthétique', url: '/api/documents/bilan/41/view' },
        { id: '42', type: 'DEVIS', name: 'Facture secrète' },
        { id: 'legacy:17:file.pdf', type: 'BILAN', name: 'Non classé' },
      ] } as never);
      if (url === '/documents/bilan/41/view') return Promise.resolve({
        data: new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
      } as never);
      return Promise.reject(new Error('Unexpected route'));
    });
    render(<HistoricBilanReadonlyPanel patientId={17}/>);
    const button = await screen.findByRole('button', { name: 'Consulter : Bilan synthétique' });
    expect(screen.queryByText('Facture secrète')).toBeNull();
    expect(screen.queryByText('Non classé')).toBeNull();
    fireEvent.click(button);
    await waitFor(() => expect(document.querySelector('iframe[src="blob:r2-bilan-synthetic"]')).not.toBeNull());
    expect(vi.mocked(api.get)).toHaveBeenCalledWith('/documents/bilan/41/view', { responseType: 'blob' });
    for (const mutation of [api.post, api.put, api.patch, api.delete]) expect(vi.mocked(mutation)).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: "Fermer l'aperçu" }));
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:r2-bilan-synthetic');
    expect(document.querySelector('iframe')).toBeNull();
  });

  it('does not infer BILAN or reveal a list when the server denies access', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('403'));
    render(<HistoricBilanReadonlyPanel patientId={17}/>);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent',
      'Consultation BILAN indisponible ou refusée.');
    expect(screen.queryByRole('button', { name: /Consulter/ })).toBeNull();
  });

  it('discards late patient-A list responses after switching to B', async () => {
    let resolveA: ((value: unknown) => void) | undefined;
    vi.mocked(api.get).mockImplementation((url) => (
      url === '/patients/17/documents'
        ? new Promise(resolve => { resolveA = resolve; }) as never
        : Promise.resolve({ data: [] }) as never
    ));
    const { rerender } = render(<HistoricBilanReadonlyPanel patientId={17}/>);
    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalledWith('/patients/17/documents'));
    rerender(<HistoricBilanReadonlyPanel patientId={18}/>);
    await waitFor(() => expect(screen.getByText('Aucun bilan consultable.')).toBeTruthy());
    await act(async () => { resolveA?.({ data: [{ id: '41', type: 'BILAN', name: 'Patient A confidentiel' }] }); });
    expect(screen.queryByText(/Patient A confidentiel/)).toBeNull();
  });

  it('preserves R mode with empty authorized collection and never submits', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] } as never);
    render(<HistoricBilanReadonlyPanel patientId={18}/>);
    expect(await screen.findByText('Aucun bilan consultable.')).toBeTruthy();
    expect(document.querySelector('form')).toBeNull();
    expect(document.querySelector('input[type=file]')).toBeNull();
    expect(vi.mocked(api.post)).not.toHaveBeenCalled();
  });
  it('offers a larger BILAN view without exporting, signing or modifying clinical data', async () => {
    vi.mocked(api.get).mockImplementation((url) =>
      url === '/patients/17/documents'
        ? Promise.resolve({ data: [{ id: '41', type: 'BILAN', name: 'Bilan visuel synthétique' }] } as never)
        : Promise.resolve({ data: new Blob(['%PDF-1.4'], { type: 'application/pdf' }) } as never));
    render(<HistoricBilanReadonlyPanel patientId={17}/>);
    fireEvent.click(await screen.findByRole('button', { name: 'Consulter : Bilan visuel synthétique' }));
    await waitFor(() => expect(screen.getByRole('button', { name: /Agrandir/ })).toBeTruthy());
    fireEvent.click(screen.getByRole('button', { name: /Agrandir/ }));
    expect(screen.getByRole('dialog', { name: /Bilan historique agrandi/ })).toBeTruthy();
    expect(document.querySelectorAll('iframe')).toHaveLength(2);
    fireEvent.click(screen.getByRole('button', { name: /^Fermer$/ }));
    expect(screen.queryByRole('dialog')).toBeNull();
    for (const mutate of [api.post, api.put, api.patch, api.delete]) {
      expect(vi.mocked(mutate)).not.toHaveBeenCalled();
    }
  });

  it('renders guarded PNG pages with pure GET navigation and revokes old image URLs', async () => {
    vi.mocked(api.get).mockImplementation((url) => {
      if (url === '/patients/17/documents') return Promise.resolve({
        data: [{ id: '41', type: 'BILAN', name: 'Bilan à deux pages' }],
      } as never);
      if (url === '/documents/bilan/41/view') return Promise.resolve({
        data: new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
      } as never);
      if (url === '/documents/bilan/41/page') return Promise.resolve({
        data: new Blob(['synthetic-png-bytes'], { type: 'image/png' }),
        headers: { 'x-bilan-page-count': '2' },
      } as never);
      return Promise.reject(new Error('unexpected route'));
    });
    render(<HistoricBilanReadonlyPanel patientId={17}/>);
    fireEvent.click(await screen.findByRole('button', { name: 'Consulter : Bilan à deux pages' }));
    expect(await screen.findByTestId('bilan-page-image')).toBeTruthy();
    expect(screen.getByText('Page 1 / 2')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Page suivante' }));
    await waitFor(() => expect(screen.getByText('Page 2 / 2')).toBeTruthy());
    expect(vi.mocked(api.get)).toHaveBeenCalledWith('/documents/bilan/41/page', {
      responseType: 'blob', params: { page: 2 },
    });
    expect(URL.revokeObjectURL).toHaveBeenCalled();
    for (const mutation of [api.post, api.put, api.patch, api.delete])
      expect(vi.mocked(mutation)).not.toHaveBeenCalled();
  });

});
