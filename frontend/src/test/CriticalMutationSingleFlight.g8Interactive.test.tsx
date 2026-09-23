import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { QuickPayModal } from '../features/patients/components/QuickPayModal';
import { FrontdeskModal } from '../features/agenda/FrontdeskModal';
import { RvgUploadModal } from '../features/patients/components/RvgUploadModal';
import { paymentApi } from '../services/paymentApi';
import { api } from '../services/api';
import rvgService from '../services/rvgService';

const accounting = vi.hoisted(() => ({
  setGroupSelectedTeeth: vi.fn(),
  setOdontogramMode: vi.fn(),
}));

vi.mock('../services/paymentApi', () => ({
  paymentApi: { recordPayment: vi.fn() },
}));
vi.mock('../services/api', () => ({
  api: { post: vi.fn() },
}));
vi.mock('../services/rvgService', () => ({
  default: { uploadRVG: vi.fn() },
}));
vi.mock('../features/admin/store/useAccountingStore', () => ({
  useAccountingStore: {
    getState: () => ({
      setGroupSelectedTeeth: accounting.setGroupSelectedTeeth,
      setOdontogramMode: accounting.setOdontogramMode,
    }),
  },
}));
vi.mock('../hooks/useEscapeKey', () => ({ useEscapeKey: () => undefined }));
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

beforeEach(() => {
  vi.clearAllMocks();
});
afterEach(() => cleanup());

describe('G8 critical mutation single-flight matrix', () => {
  it('disables QuickPay submit immediately after the first mutation dispatch', async () => {
    const gate = deferred<any>();
    vi.mocked(paymentApi.recordPayment).mockReturnValue(gate.promise);

    render(<QuickPayModal isOpen onClose={vi.fn()} patientId={7} />);
    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '250' } });
    fireEvent.click(screen.getByRole('button', { name: 'Carte' }));

    const submit = screen.getByRole('button', { name: 'Encaisser' }) as HTMLButtonElement;
    fireEvent.click(submit);

    expect(paymentApi.recordPayment).toHaveBeenCalledTimes(1);
    expect(submit.disabled).toBe(true);

    fireEvent.click(submit);
    expect(paymentApi.recordPayment).toHaveBeenCalledTimes(1);

    gate.resolve({});
    await waitFor(() => expect(accounting.setGroupSelectedTeeth).toHaveBeenCalledWith([]));
  });

  it('disables Frontdesk create while the first request is in flight', async () => {
    const gate = deferred<any>();
    vi.mocked(api.post).mockReturnValue(gate.promise);

    render(
      <FrontdeskModal
        open
        onClose={vi.fn()}
        onSuccess={vi.fn()}
        selectedDate={new Date('2026-09-21T00:00:00')}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText('Prénom'), { target: { value: 'Sara' } });
    fireEvent.change(screen.getByPlaceholderText('Nom'), { target: { value: 'BENALI' } });

    const submit = screen.getByRole('button', { name: 'Créer demande' }) as HTMLButtonElement;
    fireEvent.click(submit);

    expect(api.post).toHaveBeenCalledTimes(1);
    expect(submit.disabled).toBe(true);

    fireEvent.click(submit);
    expect(api.post).toHaveBeenCalledTimes(1);

    gate.resolve({ data: { id: 1 } });
    await waitFor(() => expect(submit.disabled).toBe(false));
  });

  it('disables RVG save while upload is in flight and prevents duplicate upload dispatch', async () => {
    const gate = deferred<any>();
    vi.mocked(rvgService.uploadRVG).mockReturnValue(gate.promise);

    const { container } = render(
      <RvgUploadModal open patientId={7} onClose={vi.fn()} onSuccess={vi.fn()} />,
    );

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File(['x'], 'rvg.pdf', { type: 'application/pdf' })] },
    });

    const submit = screen.getByRole('button', { name: 'Enregistrer' }) as HTMLButtonElement;
    fireEvent.click(submit);

    expect(rvgService.uploadRVG).toHaveBeenCalledTimes(1);
    expect(submit.disabled).toBe(true);

    fireEvent.click(submit);
    expect(rvgService.uploadRVG).toHaveBeenCalledTimes(1);

    gate.resolve({
      id: 9,
      original_filename: 'rvg.pdf',
      created_at: '2026-09-19T12:00:00Z',
      clinical_data: { radio_type: 'rvg' },
    } as any);

    await waitFor(() => expect(rvgService.uploadRVG).toHaveBeenCalledTimes(1));
  });
});
