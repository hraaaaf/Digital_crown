import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PatientPhotoEditor } from './PatientPhotoEditor';
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
