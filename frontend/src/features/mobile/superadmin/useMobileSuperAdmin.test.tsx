import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../services/zka/mobileFetch';
import { unlockMobilePasskey } from '../../../services/zka/mobilePasskey';
import { useMobileSuperAdmin } from './useMobileSuperAdmin';

vi.mock('../../../services/zka/MobileStorage', () => ({
  MobileStorage: {
    getCredentials: vi.fn(),
    getBiometricAccessToken: vi.fn(),
    clearBiometricAccessToken: vi.fn(),
  },
}));

vi.mock('../../../services/zka/mobileFetch', () => ({
  mobileFetch: vi.fn(),
}));

vi.mock('../../../services/zka/mobilePasskey', () => ({
  unlockMobilePasskey: vi.fn(),
}));

const jsonResponse = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json' },
});

function pathOf(input: RequestInfo | URL) {
  return new URL(String(input)).pathname + new URL(String(input)).search;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(MobileStorage.getCredentials).mockResolvedValue({
    publicId: '0123456789abcdef',
    masterKey: '',
    access_token: 'durable-mobile-token',
    refresh_token: 'refresh-token',
    device_id: 'device-test',
    api_base_url: 'http://127.0.0.1:8005',
  });
  vi.mocked(MobileStorage.getBiometricAccessToken).mockReturnValue(null);
  vi.mocked(unlockMobilePasskey).mockResolvedValue(undefined as never);
  vi.mocked(mobileFetch).mockImplementation(async (input, init) => {
    const path = pathOf(input);
    if (path === '/api/superadmin/clients') return jsonResponse([]);
    if (path === '/api/superadmin/trial-codes') return jsonResponse([]);
    if (path === '/api/partner-orders' && (!init?.method || init.method === 'GET')) return jsonResponse([]);
    if (path === '/api/partner-orders/finance/summary') return jsonResponse({
      ordersCount: 0,
      matchedCount: 0,
      mismatchCount: 0,
      waitingInvoiceCount: 0,
      waitingReceiptCount: 0,
      cancelledCount: 0,
      currentOrderAmount: 0,
      recognizedRevenueAmount: 0,
      expectedSupplierPayable: 0,
      invoicedAmount: 0,
      invoiceVariance: 0,
      orders: [],
    });
    if (path === '/api/partner-orders/42/dispatch' && (!init?.method || init.method === 'GET')) {
      return jsonResponse({ order: { id: 42 }, dispatch: { outcome: 'SUCCEEDED', responseStatus: 201 } });
    }
    if (path === '/api/partner-orders/42/procurement') {
      return jsonResponse({ order: { id: 42 }, procurement: { supplierReference: 'SUP-42' } });
    }
    if (path === '/api/partner-orders/42/receipts') {
      return jsonResponse({
        order: { id: 42 },
        receipts: [{ id: 700, lines: [{ productId: '9', quantityReceived: 2 }] }],
        progress: { receiptCount: 1, isComplete: false },
      });
    }
    if (path === '/api/partner-orders/finance/orders/42/reconciliation') {
      return jsonResponse({ reconciliationStatus: 'WAITING_RECEIPT', invoiceVariance: 0 });
    }
    if (path === '/api/partner-orders/42/dispatch' && init?.method === 'POST') {
      return jsonResponse({ order: { id: 42, status: 'SENT_TO_PARTNER' }, dispatch: { outcome: 'SUCCEEDED' } });
    }
    throw new Error(`Unexpected mobileFetch ${init?.method || 'GET'} ${path}`);
  });
});

describe('useMobileSuperAdmin operational contracts', () => {
  it('normalizes the receipts envelope instead of treating it as a raw array', async () => {
    const { result } = renderHook(() => useMobileSuperAdmin());
    await waitFor(() => expect(result.current.loadingCore).toBe(false));

    let detail: Awaited<ReturnType<typeof result.current.operationActions.loadDetail>> | undefined;
    await act(async () => {
      detail = await result.current.operationActions.loadDetail(42);
    });

    expect(detail?.dispatch).toMatchObject({ outcome: 'SUCCEEDED', responseStatus: 201 });
    expect(detail?.procurement).toMatchObject({ supplierReference: 'SUP-42' });
    expect(detail?.receipts).toEqual([{ id: 700, lines: [{ productId: '9', quantityReceived: 2 }] }]);
    expect(detail?.receiptProgress).toEqual({ receiptCount: 1, isComplete: false });
    expect(detail?.reconciliation).toMatchObject({ reconciliationStatus: 'WAITING_RECEIPT' });
  });

  it('does not invent a WebAuthn prerequisite for tenant-scoped dispatch', async () => {
    const { result } = renderHook(() => useMobileSuperAdmin());
    await waitFor(() => expect(result.current.loadingCore).toBe(false));

    let success = false;
    await act(async () => {
      success = await result.current.operationActions.dispatch(42);
    });

    expect(success).toBe(true);
    expect(unlockMobilePasskey).not.toHaveBeenCalled();
    expect(mobileFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/partner-orders/42/dispatch'),
      expect.objectContaining({ method: 'POST' }),
    );
  });
});
