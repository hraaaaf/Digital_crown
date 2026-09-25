import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AppUser } from '../../types';
import { api } from '../../services/api';
import { usePartnerMarketplace } from './usePartnerMarketplace';

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

const discontinued = { ...product, id: 102, sku: 'OLD-102', name: 'Produit arrêté', availability: 'DISCONTINUED' };

function installCatalog(products = [product, discontinued]) {
  vi.mocked(api.get).mockImplementation(async (path: string) => {
    if (path === '/partner-orders/meta') return { data: { strategyPresets: [strategy] } } as never;
    if (path === '/partner-catalog/meta') return { data: { categories: ['Restauration'], specialties: ['Omnipratique'], availability: ['AVAILABLE','DISCONTINUED'] } } as never;
    if (path === '/partner-catalog/suppliers') return { data: [{ id: 11, supplierKey: 'atlas', name: 'Atlas Dental', isActive: true, productCount: products.length }] } as never;
    if (path === '/partner-catalog/products') return { data: products } as never;
    throw new Error('Unexpected GET '+path);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  installCatalog();
  vi.mocked(api.post).mockResolvedValue({ data: { orderNumber: 'CMD-TEST' } } as never);
});

describe('Partner Marketplace G7 adverse matrix', () => {
  it('blocks checkout with an empty cart before any API mutation', async () => {
    const { result } = renderHook(() => usePartnerMarketplace());
    await waitFor(() => expect(result.current.catalogLoading).toBe(false));

    let ok = true;
    await act(async () => { ok = await result.current.submitDraft(); });

    expect(ok).toBe(false);
    expect(result.current.errorMessage).toBe('Ajoutez au moins un produit au panier.');
    expect(api.post).not.toHaveBeenCalled();
  });

  it('blocks checkout when required customer fields are incomplete', async () => {
    const { result } = renderHook(() => usePartnerMarketplace());
    await waitFor(() => expect(result.current.catalogLoading).toBe(false));
    act(() => result.current.adjustQty(result.current.filteredProducts.find(p => p.sku === 'CMP-101')!, 1));

    let ok = true;
    await act(async () => { ok = await result.current.submitDraft(); });

    expect(ok).toBe(false);
    expect(result.current.errorMessage).toBe('Complétez les informations de commande requises.');
    expect(api.post).not.toHaveBeenCalled();
  });

  it('never adds a discontinued product to the cart', async () => {
    const { result } = renderHook(() => usePartnerMarketplace());
    await waitFor(() => expect(result.current.catalogLoading).toBe(false));
    const stopped = result.current.products.find(p => p.sku === 'OLD-102')!;

    act(() => result.current.adjustQty(stopped, 1));

    expect(result.current.totalUnits).toBe(0);
    expect(result.current.cart[stopped.id]).toBeUndefined();
  });

  it('preserves cart and exposes backend detail when order creation is refused', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'Commande partenaire refusée' } } });
    const { result } = renderHook(() => usePartnerMarketplace());
    await waitFor(() => expect(result.current.catalogLoading).toBe(false));

    const current = result.current.filteredProducts.find(p => p.sku === 'CMP-101')!;
    act(() => {
      result.current.adjustQty(current, 2);
      result.current.updateCustomer('phone', '0600000000');
      result.current.updateCustomer('city', 'Rabat');
    });

    let ok = true;
    await act(async () => { ok = await result.current.submitDraft(); });

    expect(ok).toBe(false);
    expect(result.current.errorMessage).toBe('Commande partenaire refusée');
    expect(result.current.totalUnits).toBe(2);
  });

  it('marks catalog unverified instead of presenting a truthful empty catalog when all reads fail without cache', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('catalog unavailable'));
    const { result } = renderHook(() => usePartnerMarketplace());

    await waitFor(() => expect(result.current.catalogLoading).toBe(false));
    expect(result.current.catalogError).toBe(true);
    expect(result.current.products).toEqual([]);
  });

  it('filters availability and category/search without mutating cart', async () => {
    const { result } = renderHook(() => usePartnerMarketplace());
    await waitFor(() => expect(result.current.catalogLoading).toBe(false));

    act(() => result.current.setAvailableOnly(true));
    expect(result.current.filteredProducts.map(p => p.sku)).toEqual(['CMP-101']);

    act(() => result.current.setSearch('absent'));
    expect(result.current.filteredProducts).toEqual([]);
    expect(result.current.totalUnits).toBe(0);
    expect(api.post).not.toHaveBeenCalled();
  });
});
