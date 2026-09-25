import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CsvImportModal } from './CsvImportModal';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: { post: vi.fn() },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

beforeEach(() => vi.clearAllMocks());
afterEach(() => cleanup());

describe('CsvImportModal G2 interactive matrix', () => {
  it('keeps Import disabled until a CSV is selected', () => {
    render(<CsvImportModal isOpen onClose={vi.fn()} onSuccess={vi.fn()} />);
    expect((screen.getByRole('button', { name: 'Importer' }) as HTMLButtonElement).disabled).toBe(true);
  });

  it('uploads the selected CSV with multipart form data and refreshes only when rows were created', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { created: 2, skipped_duplicates: 1, errors: [] },
    } as never);
    const onSuccess = vi.fn();

    const { container } = render(<CsvImportModal isOpen onClose={vi.fn()} onSuccess={onSuccess} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['nom;prenom\nBENALI;Sara'], 'patients.csv', { type: 'text/csv' });

    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.getByText('patients.csv')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Importer' }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    const [url, form, config] = vi.mocked(api.post).mock.calls[0];
    expect(url).toBe('/patients/import-csv');
    expect(form).toBeInstanceOf(FormData);
    expect((form as FormData).get('file')).toBe(file);
    expect(config).toEqual({ headers: { 'Content-Type': 'multipart/form-data' } });
    expect(await screen.findByText('2')).toBeTruthy();
    expect(screen.getByText('1')).toBeTruthy();
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('shows row errors truthfully and does not call success when nothing was created', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        created: 0,
        skipped_duplicates: 1,
        errors: [{ row: 3, reason: 'date invalide' }],
      },
    } as never);
    const onSuccess = vi.fn();

    const { container } = render(<CsvImportModal isOpen onClose={vi.fn()} onSuccess={onSuccess} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['bad'], 'bad.csv', { type: 'text/csv' })] } });
    fireEvent.click(screen.getByRole('button', { name: 'Importer' }));

    expect(await screen.findByText(/Ligne 3/)).toBeTruthy();
    expect(screen.getByText(/date invalide/)).toBeTruthy();
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it('keeps the modal usable after backend refusal and does not report false success', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { detail: 'CSV invalide' } },
    });
    const onSuccess = vi.fn();

    const { container } = render(<CsvImportModal isOpen onClose={vi.fn()} onSuccess={onSuccess} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['bad'], 'bad.csv', { type: 'text/csv' })] } });
    fireEvent.click(screen.getByRole('button', { name: 'Importer' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1));
    expect(screen.getByRole('button', { name: 'Importer' })).toBeTruthy();
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it('resets transient state when closing', async () => {
    const onClose = vi.fn();
    const { container, rerender } = render(<CsvImportModal isOpen onClose={onClose} onSuccess={vi.fn()} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['x'], 'x.csv', { type: 'text/csv' })] } });
    expect(screen.getByText('x.csv')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(onClose).toHaveBeenCalledTimes(1);

    rerender(<CsvImportModal isOpen onClose={onClose} onSuccess={vi.fn()} />);
    expect(screen.queryByText('x.csv')).toBeNull();
    expect((screen.getByRole('button', { name: 'Importer' }) as HTMLButtonElement).disabled).toBe(true);
  });
});
