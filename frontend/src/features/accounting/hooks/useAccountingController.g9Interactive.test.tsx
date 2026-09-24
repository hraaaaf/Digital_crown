import type { ReactNode } from 'react';
import { act, renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import { useAccountingController } from './useAccountingController';

const getMock = vi.mocked(api.get);
const postMock = vi.mocked(api.post);
const patchMock = vi.mocked(api.patch);
const toastSuccess = vi.mocked(toast.success);
const toastError = vi.mocked(toast.error);

const baseItem = {
  id: 12,
  document_archive_id: 77,
  patient_id: 4,
  patient_name: 'Patient G9',
  assurance: 'AUCUNE',
  date: '2026-09-24T10:00:00Z',
  title: 'Consultation',
  amount: 300,
  file_url: '/documents/77.pdf',
  payment_status: 'A_ENCAISSER',
  is_collected: false,
};

const wrapper = ({ children }: { children: ReactNode }) => (
  <MemoryRouter initialEntries={['/accounting']}>{children}</MemoryRouter>
);

async function renderController() {
  const rendered = renderHook(() => useAccountingController(), { wrapper });
  await waitFor(() => expect(rendered.result.current.loading).toBe(false));
  return rendered.result;
}

describe('Accounting global page G9 interaction truth', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    getMock.mockImplementation(async (url: string) => {
      if (url.startsWith('/accounting/honoraires')) {
        return {
          data: {
            items: [{ ...baseItem }],
            total_amount: 300,
            total_collected: 0,
            summary_by_title: { Consultation: 300 },
          },
        } as any;
      }
      if (url === '/accounting/treasury-hub') {
        return { data: { pending_count: 1, items: [] } } as any;
      }
      if (url === '/accounting/overdue?days=30') {
        return { data: { items: [] } } as any;
      }
      if (url === '/analytics/financial') {
        return { data: { revenue: 300 } } as any;
      }
      if (url === '/accounting/patient-debts') {
        return { data: { total_patients: 0, total_amount: 0, items: [] } } as any;
      }
      return { data: {} } as any;
    });

    postMock.mockResolvedValue({ data: {} } as any);
    patchMock.mockResolvedValue({ data: {} } as any);
  });

  it('never reports an encaissement success when the backend refuses, then reports success only after ACK', async () => {
    const result = await renderController();

    postMock.mockRejectedValueOnce(new Error('encaissement refused'));
    await act(async () => {
      await result.current.handleEncaisser(12);
    });

    expect(postMock).toHaveBeenCalledWith('/accounting/encaisser/12');
    expect(toastError).toHaveBeenCalledWith("Échec de l'encaissement.");
    expect(toastSuccess).not.toHaveBeenCalledWith('Règlement encaissé avec succès !');

    await act(async () => {
      await result.current.handleEncaisser(12);
    });

    expect(toastSuccess).toHaveBeenCalledWith('Règlement encaissé avec succès !');
  });

  it('keeps the accounting row when trashing is refused and exposes the refusal instead of false deletion', async () => {
    const result = await renderController();

    act(() => result.current.handleDelete(77));
    expect(result.current.confirmDeleteId).toBe(77);

    postMock.mockRejectedValueOnce(new Error('trash refused'));
    await act(async () => {
      await result.current.confirmDelete();
    });

    expect(postMock).toHaveBeenCalledWith('/documents/77/trash');
    expect(result.current.filteredItems).toHaveLength(1);
    expect(result.current.filteredItems[0].id).toBe(12);
    expect(toastError).toHaveBeenCalledWith('Erreur lors de la suppression.');
  });

  it('commits edited amounts only after backend ACK and preserves the previous amount on refusal', async () => {
    const result = await renderController();

    act(() => {
      result.current.startEdit(12, 'amount', 300);
      result.current.setEditingValue('450');
    });
    await waitFor(() => expect(result.current.editingValue).toBe('450'));

    patchMock.mockRejectedValueOnce(new Error('edit refused'));
    await act(async () => {
      await result.current.commitEdit();
    });

    expect(patchMock).toHaveBeenCalledWith('/accounting/item/12', { amount: 450 });
    expect(result.current.filteredItems[0].amount).toBe(300);
    expect(toastError).toHaveBeenCalledWith('Erreur de modification.');

    act(() => {
      result.current.startEdit(12, 'amount', 300);
      result.current.setEditingValue('450');
    });
    await waitFor(() => expect(result.current.editingValue).toBe('450'));

    await act(async () => {
      await result.current.commitEdit();
    });

    expect(result.current.filteredItems[0].amount).toBe(450);
    expect(toastSuccess).toHaveBeenCalledWith('Modifié avec succès.');
  });

  it('keeps email feedback ACK-bound and loads each global accounting tab from its canonical source', async () => {
    const result = await renderController();

    postMock.mockRejectedValueOnce({ response: { data: { detail: 'Email refusé' } } });
    await act(async () => {
      await result.current.handleSendEmail(12);
    });
    expect(postMock).toHaveBeenCalledWith('/accounting/send-email/12');
    expect(toastError).toHaveBeenCalledWith('Email refusé');
    expect(toastSuccess).not.toHaveBeenCalledWith('Note envoyée par email au patient.');

    await act(async () => {
      await result.current.handleSendEmail(12);
    });
    expect(toastSuccess).toHaveBeenCalledWith('Note envoyée par email au patient.');

    act(() => result.current.setActiveTab('treasury'));
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/accounting/treasury-hub'));

    act(() => result.current.setActiveTab('insights'));
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/analytics/financial'));

    act(() => result.current.setActiveTab('unpaid'));
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/accounting/patient-debts'));
  });
});
