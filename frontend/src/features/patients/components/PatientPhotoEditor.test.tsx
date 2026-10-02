import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PatientPhotoEditor, computeCropGeometry } from './PatientPhotoEditor';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal('URL', {
    createObjectURL: vi.fn(() => 'blob:photo-preview'),
    revokeObjectURL: vi.fn(),
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('PatientPhotoEditor crop geometry', () => {
  it('matches the preview translation semantics for square sources', () => {
    expect(computeCropGeometry(100, 100, 1, 50, -25, 768)).toEqual({
      drawnWidth: 768,
      drawnHeight: 768,
      x: 384,
      y: -192,
    });
    expect(computeCropGeometry(100, 100, 2, 25, 0, 768)).toEqual({
      drawnWidth: 1536,
      drawnHeight: 1536,
      x: -192,
      y: -384,
    });
  });
});

describe('PatientPhotoEditor', () => {
  it('shows initials fallback and photo actions without loading an unauthenticated image URL', () => {
    render(<PatientPhotoEditor patientId={7} firstName="Sara" lastName="Benali" />);
    expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB');
    expect(screen.getByRole('button', { name: /Importer/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Prendre une photo/i })).toBeTruthy();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('rejects unsupported files before upload', () => {
    render(<PatientPhotoEditor patientId={7} firstName="Sara" lastName="Benali" />);
    const input = screen.getByLabelText('Importer une photo du patient');
    fireEvent.change(input, { target: { files: [new File(['x'], 'bad.gif', { type: 'image/gif' })] } });
    expect(screen.getByRole('alert').textContent).toMatch(/JPEG, PNG ou WebP/i);
    expect(api.post).not.toHaveBeenCalled();
  });

  it('reports camera unavailability truthfully', async () => {
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: undefined });
    render(<PatientPhotoEditor patientId={7} firstName="Sara" lastName="Benali" />);
    fireEvent.click(screen.getByRole('button', { name: /Prendre une photo/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Aucune caméra accessible/i);
  });

  it('loads an existing photo as an authenticated blob and exposes delete', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) } as never);
    render(<PatientPhotoEditor patientId={7} firstName="Sara" lastName="Benali" initialHasPhoto />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/7/photo', { responseType: 'blob' }));
    expect(await screen.findByRole('button', { name: /Supprimer/i })).toBeTruthy();
  });

  it('preserves the existing photo binding when the authenticated blob read fails transiently', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('network'));
    render(<PatientPhotoEditor patientId={7} firstName="Sara" lastName="Benali" initialHasPhoto />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/momentanément indisponible/i);
    expect(screen.getByRole('button', { name: /Supprimer/i })).toBeTruthy();
    expect(api.delete).not.toHaveBeenCalled();
  });

  it('deletes the canonical photo binding without false success', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) } as never);
    vi.mocked(api.delete).mockResolvedValue({ status: 204 } as never);
    render(<PatientPhotoEditor patientId={7} firstName="Sara" lastName="Benali" initialHasPhoto />);
    const remove = await screen.findByRole('button', { name: /Supprimer/i });
    fireEvent.click(remove);
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/patients/7/photo'));
    await waitFor(() => expect(screen.queryByRole('button', { name: /Supprimer/i })).toBeNull());
  });
});
