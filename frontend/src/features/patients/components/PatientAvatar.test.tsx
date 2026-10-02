import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PatientAvatar } from './PatientAvatar';
import { api } from '../../../services/api';
import { usePatientStore } from '../../../stores/usePatientStore';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
  usePatientStore.setState({
    patientsCache: [],
    patientsCacheLoaded: false,
    patientsCacheUpdatedAt: 0,
  });
  vi.stubGlobal('URL', {
    createObjectURL: vi.fn(() => 'blob:patient-avatar'),
    revokeObjectURL: vi.fn(),
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('PatientAvatar', () => {
  it('does not explore the photo route when photo_url is absent', () => {
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl={null} />);
    expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB');
    expect(api.get).not.toHaveBeenCalled();
  });

  it('refuses an external/public photo_url without fetching it', () => {
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="https://example.com/photo.jpg" />);
    expect(screen.getByLabelText('Initiales du patient')).toBeTruthy();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('loads the canonical photo through the authenticated blob route', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) } as never);
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/7/photo', expect.objectContaining({ responseType: 'blob' })));
    await waitFor(() => expect(screen.getByLabelText(/Photo de Sara Benali/)).toBeTruthy());
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
  });

  it('falls back to initials on a 404 or 503 read failure', async () => {
    vi.mocked(api.get).mockRejectedValue({ response: { status: 503 } });
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB');
  });

  it('revokes ObjectURLs when the patient changes', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) } as never);
    const view = render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalledTimes(1));
    view.rerender(<PatientAvatar patientId={8} firstName="Nora" lastName="Amrani" photoUrl={null} />);
    await waitFor(() => expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:patient-avatar'));
    expect(screen.getByLabelText('Initiales du patient').textContent).toBe('NA');
  });

  it('resolves photo presence from the patient contract for agenda-like surfaces', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: [{ id: 7, nom: 'BENALI', prenom: 'Sara', photo_url: '/api/patients/7/photo' }] } as never)
      .mockResolvedValueOnce({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) } as never);
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" resolveFromDirectory />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/'));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/7/photo', expect.objectContaining({ responseType: 'blob' })));
  });
});
