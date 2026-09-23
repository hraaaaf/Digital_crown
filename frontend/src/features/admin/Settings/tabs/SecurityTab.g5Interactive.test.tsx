import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SecurityTab } from './SecurityTab';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../../Security/MobileSecurity', () => ({ MobileSecurity: () => <div>Mobile security surface</div> }));
vi.mock('../../Security/AuditLogViewer', () => ({ AuditLogViewer: () => <div>Audit log surface</div> }));
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

const preflightReady = {
  restore_id: 'restore-1',
  status: 'preflight_ready',
  original_name: 'backup.enc',
  size_bytes: 2048,
  archive_type: 'ENC',
  backup_created_at: '2026-09-19',
  compatible: true,
  restore_database: true,
  restore_media: false,
  media_file_count: 0,
  preserved: ['media'],
  warnings: [],
  errors: [],
};

const prepared = {
  ...preflightReady,
  status: 'prepared',
  prepared_at: '2026-09-19T12:00:00Z',
};

const success = {
  ...prepared,
  status: 'success',
  message: 'Restauration terminée',
  smoke_check: 'ok',
  rollback: 'not_needed',
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/admin/export-db') {
      return {
        data: new Blob(['backup']),
        headers: { 'content-disposition': 'attachment; filename="clinic.dcbackup"' },
      } as never;
    }
    if (url === '/admin/restore/restore-1/status') return { data: success } as never;
    throw new Error('unexpected GET ' + url);
  });
  vi.mocked(api.post).mockImplementation(async (url: string) => {
    if (url === '/admin/restore/preflight') return { data: preflightReady } as never;
    if (url === '/admin/restore/restore-1/prepare') return { data: prepared } as never;
    if (url === '/admin/restore/restore-1/apply') return { data: { ...prepared, status: 'scheduled' } } as never;
    throw new Error('unexpected POST ' + url);
  });
  vi.mocked(api.delete).mockResolvedValue({ data: {} } as never);

  vi.stubGlobal('URL', {
    createObjectURL: vi.fn(() => 'blob:backup'),
    revokeObjectURL: vi.fn(),
  });
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function fileInput(container: HTMLElement) {
  return container.querySelector('input[type="file"]') as HTMLInputElement;
}

describe('SecurityTab G5 backup/restore matrix', () => {
  it('exports a verified backup blob using the backend filename', async () => {
    render(<SecurityTab />);

    fireEvent.click(screen.getByRole('button', { name: /Créer et télécharger la sauvegarde/i }));

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/admin/export-db', { responseType: 'blob' }));
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:backup');
  });

  it('runs restore preflight as multipart without any apply/prepare mutation', async () => {
    const { container } = render(<SecurityTab />);
    const file = new File(['backup'], 'backup.enc', { type: 'application/octet-stream' });

    fireEvent.change(fileInput(container), { target: { files: [file] } });

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const [url, body, config] = vi.mocked(api.post).mock.calls[0];
    expect(url).toBe('/admin/restore/preflight');
    expect(body).toBeInstanceOf(FormData);
    expect((body as FormData).get('backup')).toBe(file);
    expect(config).toEqual({ timeout: 120_000 });
    expect(screen.getByText('Préflight validé')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalledWith('/admin/restore/restore-1/prepare', expect.anything(), expect.anything());
    expect(api.post).not.toHaveBeenCalledWith('/admin/restore/restore-1/apply', expect.anything());
  });

  it('blocks preparation for an incompatible backup', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { ...preflightReady, compatible: false, status: 'blocked', errors: ['Version incompatible'] },
    } as never);
    const { container } = render(<SecurityTab />);

    fireEvent.change(fileInput(container), { target: { files: [new File(['bad'], 'bad.enc')] } });

    expect(await screen.findByText('Préflight bloqué')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Préparer la restauration/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Redémarrer et restaurer/i })).toBeNull();
  });

  it('prepares only after a compatible preflight and still performs no destructive apply', async () => {
    const { container } = render(<SecurityTab />);
    fireEvent.change(fileInput(container), { target: { files: [new File(['backup'], 'backup.enc')] } });

    fireEvent.click(await screen.findByRole('button', { name: /Préparer la restauration/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/admin/restore/restore-1/prepare',
      {},
      { timeout: 600_000 },
    ));
    expect(await screen.findByText(/Préparation sécurisée validée/i)).toBeTruthy();
    expect(api.post).not.toHaveBeenCalledWith('/admin/restore/restore-1/apply', expect.anything());
  });

  it('requires the exact RESTAURER confirmation before apply, then verifies terminal success', async () => {
    const { container } = render(<SecurityTab />);
    fireEvent.change(fileInput(container), { target: { files: [new File(['backup'], 'backup.enc')] } });
    fireEvent.click(await screen.findByRole('button', { name: /Préparer la restauration/i }));

    const confirm = await screen.findByPlaceholderText('RESTAURER');
    const apply = screen.getByRole('button', { name: /Redémarrer et restaurer/i }) as HTMLButtonElement;

    fireEvent.change(confirm, { target: { value: 'restaurer' } });
    expect(apply.disabled).toBe(true);
    expect(api.post).not.toHaveBeenCalledWith('/admin/restore/restore-1/apply', expect.anything());

    fireEvent.change(confirm, { target: { value: 'RESTAURER' } });
    expect(apply.disabled).toBe(false);
    fireEvent.click(apply);

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/admin/restore/restore-1/apply',
      { confirmation: 'RESTAURER' },
    ));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/admin/restore/restore-1/status'));
    expect(await screen.findByText('Restauration terminée')).toBeTruthy();
  });

  it('cancels a non-running preflight through DELETE and clears restore state', async () => {
    const { container } = render(<SecurityTab />);
    fireEvent.change(fileInput(container), { target: { files: [new File(['backup'], 'backup.enc')] } });

    fireEvent.click(await screen.findByRole('button', { name: /Fermer ce préflight/i }));

    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/admin/restore/restore-1'));
    expect(screen.queryByText('Préflight validé')).toBeNull();
  });

  it('surfaces preflight refusal without exposing prepare/apply controls', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { detail: 'Backup corrompu' } },
    });
    const { container } = render(<SecurityTab />);

    fireEvent.change(fileInput(container), { target: { files: [new File(['bad'], 'bad.enc')] } });

    expect(await screen.findByText('Backup corrompu')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Préparer la restauration/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Redémarrer et restaurer/i })).toBeNull();
  });
});
