import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AppUser } from '../../types';
import { api } from '../../services/api';
import { buildMarketplaceCustomer, usePartnerMarketplace } from './usePartnerMarketplace';

const USER = {
  id: '77',
  employer_id: 10,
  email: 'dentist@example.test',
  full_name: 'Dr Test',
  cabinet_name: 'Cabinet Test',
  role: 'DENTISTE',
} as AppUser;

vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: (selector: (state: { user: AppUser }) => unknown) => selector({ user: USER }),
}));

vi.mock('../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

const product = {
  id: 101,
  supplierId: 11,
  supplierName: 'Atlas Dental',
  externalProductId: 'P-101',
  name: 'Composite universel',
  sku: 'CMP-101',
  dentalCategory: 'Restauration',
  dentalSpecialty: 'Omnipratique',
  unit: 'seringue',
  price: 390,
  availability: 'AVAILABLE',
  shortDescription: 'Composite test',
  longDescription: 'Composite test',
  benefits: [],
  isFeatured: true,
  sortOrder: 1,
};

const strategy = {
  key: 'sent_commission_10',
  label: 'Commission sur commande envoyée',
  settlementBasis: 'SENT_TO_PARTNER',
  revenueModel: 'COMMISSION_PERCENT',
  commissionRate: 10,
  discountRate: 0,
  fixedFeeAmount: 0,
  description: 'Test',
};

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
  vi.mocked(api.get).mockImplementation(async (path: string) => {
    if (path === '/partner-orders/meta') return { data: { strategyPresets: [strategy] } } as never;
    if (path === '/partner-catalog/meta') return { data: { categories: ['Restauration'], specialties: ['Omnipratique'], availability: ['AVAILABLE'] } } as never;
    if (path === '/partner-catalog/suppliers') return { data: [{ id: 11, supplierKey: 'atlas', name: 'Atlas Dental', isActive: true, productCount: 1 }] } as never;
    if (path === '/partner-catalog/products') return { data: [product] } as never;
    throw new Error(`Unexpected GET ${path}`);
  });
  vi.mocked(api.post).mockResolvedValue({ data: { orderNumber: 'CMD-TEST' } } as never);
});

describe('shared Marketplace controller', () => {
  it('prefills known practitioner fields without inventing phone or city', () => {
    expect(buildMarketplaceCustomer(USER)).toEqual({
      fullName: 'Dr Test',
      clinic: 'Cabinet Test',
      email: 'dentist@example.test',
      phone: '',
      city: '',
      note: '',
    });
  });

  it('keeps preview deterministic and fully isolated from Marketplace APIs', async () => {
    const previewData = {
      strategyPresets: [strategy],
      catalogMeta: { categories: ['Restauration'], specialties: ['Omnipratique'], availability: ['AVAILABLE'] },
      suppliers: [{ id: 11, supplierKey: 'preview', name: 'Preview Dental', isActive: true, productCount: 1 }],
      products: [{
        id: '101', supplierId: '11', supplierName: 'Preview Dental', name: 'Composite universel',
        category: 'Restauration', specialty: 'Omnipratique', sku: 'CMP-101', unit: 'seringue', price: 390,
        availability: 'Disponible', description: 'Preview', longDescription: 'Preview', benefits: [], isFeatured: true, sortOrder: 1,
      }],
      customer: {
        fullName: 'Dr Preview', clinic: 'Cabinet Preview', email: 'preview@example.test', phone: '0600000000', city: 'Rabat',
      },
    } as const;

    const { result } = renderHook(() => usePartnerMarketplace({ previewData: previewData as never }));
    await waitFor(() => expect(result.current.catalogLoading).toBe(false));

    expect(result.current.customer).toMatchObject({
      fullName: 'Dr Preview', clinic: 'Cabinet Preview', email: 'preview@example.test', phone: '0600000000', city: 'Rabat',
    });
    expect(api.get).not.toHaveBeenCalled();

    act(() => result.current.adjustQty(result.current.filteredProducts[0], 1));
    let submitted = false;
    await act(async () => { submitted = await result.current.submitDraft(); });

    expect(submitted).toBe(true);
    expect(api.post).not.toHaveBeenCalled();
    expect(result.current.successMessage).toContain('Aucune donnée réelle');
  });

  it('loads the canonical catalog, searches by SKU and prepares one server DRAFT POST', async () => {
    const { result } = renderHook(() => usePartnerMarketplace());

    await waitFor(() => expect(result.current.catalogLoading).toBe(false));
    expect(api.get).toHaveBeenCalledWith('/partner-catalog/products');
    expect(result.current.filteredProducts).toHaveLength(1);

    act(() => result.current.setSearch('CMP-101'));
    expect(result.current.filteredProducts[0]?.name).toBe('Composite universel');

    act(() => result.current.adjustQty(result.current.filteredProducts[0], 1));
    expect(result.current.totalUnits).toBe(1);
    expect(result.current.estimatedTotal).toBe(390);

    act(() => {
      result.current.updateCustomer('phone', '0600000000');
      result.current.updateCustomer('city', 'Rabat');
    });

    let submitted = false;
    await act(async () => { submitted = await result.current.submitDraft(); });
    expect(submitted).toBe(true);
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(api.post).toHaveBeenCalledWith('/partner-orders', expect.objectContaining({
      customer: expect.objectContaining({ fullName: 'Dr Test', clinic: 'Cabinet Test', email: 'dentist@example.test', phone: '0600000000', city: 'Rabat' }),
      lines: [expect.objectContaining({ productId: '101', quantity: 1, unitPrice: 390, lineTotal: 390 })],
      estimatedTotal: 390,
    }));
    expect(result.current.successMessage).toContain('CMD-TEST');
    expect(result.current.totalUnits).toBe(0);
  });
});