import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PatientAvatar } from './PatientAvatar';
import { api } from '../../../services/api';
import { usePatientStore } from '../../../stores/usePatientStore';
import { useAuthStore } from '../../../stores/useAuthStore';

vi.mock('../../../services/api', () => ({
  API_BASE: 'http://127.0.0.1:8005',
  api: { get: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
  usePatientStore.setState({
    patientsCache: [],
    patientsCacheLoaded: false,
    patientsCacheUpdatedAt: 0,
  });
  useAuthStore.setState({
    user: { role: 'ADMIN', is_superadmin: false } as any,
    isAuthenticated: true,
    isLoading: false,
    error: null,
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

  it.each([404, 503])('falls back to initials on a %s read failure', async status => {
    vi.mocked(api.get).mockRejectedValue({ response: { status } });
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB');
  });

  it('never fetches a direct canonical photo without patients permission', async () => {
    useAuthStore.setState({
      user: { role: 'SECRETAIRE', permissions: { agenda: true, patients: false } } as any,
      isAuthenticated: true,
    });
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    await waitFor(() => expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB'));
    expect(api.get).not.toHaveBeenCalled();
  });

  it('never resolves the patient directory without patients permission', async () => {
    useAuthStore.setState({
      user: { role: 'SECRETAIRE', permissions: { agenda: true, patients: false } } as any,
      isAuthenticated: true,
    });
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" resolveFromDirectory />);
    await waitFor(() => expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB'));
    expect(api.get).not.toHaveBeenCalled();
  });

  it('revokes ObjectURLs when the patient changes', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) } as never);
    const view = render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalledTimes(1));
    view.rerender(<PatientAvatar patientId={8} firstName="Nora" lastName="Amrani" photoUrl={null} />);
    await waitFor(() => expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:patient-avatar'));
    expect(screen.getByLabelText('Initiales du patient').textContent).toBe('NA');
  });

  it('ignores and revokes a stale blob response after rapid patient navigation', async () => {
    let resolveFirst!: (value: unknown) => void;
    vi.mocked(api.get)
      .mockImplementationOnce(() => new Promise(resolve => { resolveFirst = resolve; }) as never)
      .mockResolvedValueOnce({ data: new Blob(['jpeg-2'], { type: 'image/jpeg' }) } as never);

    const view = render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    view.rerender(<PatientAvatar patientId={8} firstName="Nora" lastName="Amrani" photoUrl="/api/patients/8/photo" />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/8/photo', expect.objectContaining({ responseType: 'blob' })));
    resolveFirst({ data: new Blob(['jpeg-1'], { type: 'image/jpeg' }) });
    await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByLabelText(/Photo de Nora Amrani/)).toBeTruthy());
    expect(screen.queryByLabelText(/Photo de Sara Benali/)).toBeNull();
  });

  it('revokes a late ObjectURL when unmounted before the photo response resolves', async () => {
    let resolvePhoto!: (value: unknown) => void;
    vi.mocked(api.get).mockImplementationOnce(() => new Promise(resolve => { resolvePhoto = resolve; }) as never);
    const view = render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" photoUrl="/api/patients/7/photo" />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/7/photo', expect.objectContaining({ responseType: 'blob' })));
    view.unmount();
    resolvePhoto({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) });
    await waitFor(() => expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:patient-avatar'));
  });

  it('rejects a stale directory response after the authenticated identity changes', async () => {
    let resolveFirstDirectory!: (value: unknown) => void;
    vi.mocked(api.get)
      .mockImplementationOnce(() => new Promise(resolve => { resolveFirstDirectory = resolve; }) as never)
      .mockResolvedValueOnce({ data: [{ id: 7, nom: 'NEW', prenom: 'Tenant', photo_url: null }] } as never);

    useAuthStore.setState({
      user: { id: 1, email: 'first@cabinet.ma', role: 'ADMIN' } as any,
      isAuthenticated: true,
    });
    const view = render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" resolveFromDirectory />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/'));

    act(() => {
      useAuthStore.setState({
        user: { id: 2, email: 'second@cabinet.ma', role: 'ADMIN' } as any,
        isAuthenticated: true,
      });
    });
    view.rerender(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" resolveFromDirectory />);
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.filter(call => call[0] === '/patients/')).toHaveLength(2));

    resolveFirstDirectory({
      data: [{ id: 7, nom: 'OLD', prenom: 'Tenant', photo_url: '/api/patients/7/photo' }],
    });
    await waitFor(() => expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB'));
    expect(api.get).not.toHaveBeenCalledWith('/patients/7/photo', expect.anything());
    expect(usePatientStore.getState().patientsCache[0]?.nom).toBe('NEW');
  });

  it('refreshes the directory after patients permission is revoked then restored', async () => {
    vi.mocked(api.get).mockImplementation(((url: string) => {
      if (url === '/patients/') {
        return Promise.resolve({ data: [{ id: 7, nom: 'BENALI', prenom: 'Sara', photo_url: '/api/patients/7/photo' }] });
      }
      return Promise.resolve({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) });
    }) as never);

    useAuthStore.setState({
      user: { id: 1, email: 'same@cabinet.ma', role: 'ADMIN' } as any,
      isAuthenticated: true,
    });
    render(<PatientAvatar patientId={7} firstName="Sara" lastName="Benali" resolveFromDirectory />);
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.filter(call => call[0] === '/patients/')).toHaveLength(1));
    await waitFor(() => expect(screen.getByLabelText(/Photo de Sara Benali/)).toBeTruthy());

    act(() => {
      useAuthStore.setState({
        user: { id: 1, email: 'same@cabinet.ma', role: 'SECRETAIRE', permissions: { agenda: true, patients: false } } as any,
        isAuthenticated: true,
      });
    });
    await waitFor(() => expect(screen.getByLabelText('Initiales du patient').textContent).toBe('SB'));
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:patient-avatar');

    act(() => {
      useAuthStore.setState({
        user: { id: 1, email: 'same@cabinet.ma', role: 'ADMIN' } as any,
        isAuthenticated: true,
      });
    });
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.filter(call => call[0] === '/patients/')).toHaveLength(2));
  });

  it('deduplicates the patient directory request across agenda-like avatars', async () => {
    vi.mocked(api.get).mockImplementation(((url: string) => {
      if (url === '/patients/') {
        return Promise.resolve({ data: [
          { id: 7, nom: 'BENALI', prenom: 'Sara', photo_url: '/api/patients/7/photo' },
          { id: 8, nom: 'AMRANI', prenom: 'Nora', photo_url: '/api/patients/8/photo' },
        ] });
      }
      return Promise.resolve({ data: new Blob(['jpeg'], { type: 'image/jpeg' }) });
    }) as never);
    render(<>
      <PatientAvatar patientId={7} firstName="Sara" lastName="Benali" resolveFromDirectory />
      <PatientAvatar patientId={8} firstName="Nora" lastName="Amrani" resolveFromDirectory />
    </>);
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.filter(call => call[0] === '/patients/')).toHaveLength(1));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/7/photo', expect.objectContaining({ responseType: 'blob' })));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/8/photo', expect.objectContaining({ responseType: 'blob' })));
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
