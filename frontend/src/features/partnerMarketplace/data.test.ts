import { beforeEach, describe, expect, it } from 'vitest';
import {
  MARKETPLACE_CACHE_TTL_MS,
  STORAGE_CART_KEY,
  getMarketplaceCacheStorageKey,
  getMarketplaceCartStorageKey,
  normalizePartnerProduct,
  readMarketplaceCache,
  readStoredCart,
  writeMarketplaceCache,
  writeStoredCart,
} from './data';

const owner = { id: '10', employer_id: null };
const teammate = { id: '11', employer_id: 10 };
const otherTeammate = { id: '12', employer_id: 10 };

const cachePayload = {
  strategyPresets: [],
  catalogMeta: { categories: ['Consommables'], specialties: ['Omnipratique'], availability: ['AVAILABLE'] },
  suppliers: [],
  products: [],
};

describe('partner marketplace cart storage isolation', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('uses a distinct cart key for each authenticated user, including teammates', () => {
    expect(getMarketplaceCartStorageKey(owner)).toBe(`${STORAGE_CART_KEY}:user:10`);
    expect(getMarketplaceCartStorageKey(teammate)).toBe(`${STORAGE_CART_KEY}:employer:10:user:11`);
    expect(getMarketplaceCartStorageKey(otherTeammate)).toBe(`${STORAGE_CART_KEY}:employer:10:user:12`);
  });

  it('does not expose one user cart to another user', () => {
    writeStoredCart({ '42': 3 }, teammate);

    expect(readStoredCart(teammate)).toEqual({ '42': 3 });
    expect(readStoredCart(otherTeammate)).toEqual({});
    expect(readStoredCart(owner)).toEqual({});
  });

  it('ignores the legacy global cart key instead of migrating it into an authenticated scope', () => {
    window.localStorage.setItem(STORAGE_CART_KEY, JSON.stringify({ '99': 7 }));

    expect(readStoredCart(owner)).toEqual({});
    expect(readStoredCart(teammate)).toEqual({});
  });

  it('derives the current authenticated scope from persisted Zustand auth state', () => {
    window.localStorage.setItem('auth-storage', JSON.stringify({
      state: { user: teammate, isAuthenticated: true },
      version: 0,
    }));

    writeStoredCart({ '7': 2 });
    expect(readStoredCart()).toEqual({ '7': 2 });
    expect(window.localStorage.getItem(`${STORAGE_CART_KEY}:employer:10:user:11`)).toBe(JSON.stringify({ '7': 2 }));
  });
});

describe('partner marketplace catalog cache freshness', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('reads a fresh cache for the exact cabinet scope', () => {
    writeMarketplaceCache(teammate, cachePayload);

    const cached = readMarketplaceCache(teammate);
    expect(cached?.scopeKey).toBe('employer:10');
    expect(cached?.catalogMeta?.categories).toEqual(['Consommables']);
  });

  it('rejects and removes a cache older than the TTL', () => {
    const key = getMarketplaceCacheStorageKey(teammate);
    window.localStorage.setItem(key, JSON.stringify({
      version: 1,
      scopeKey: 'employer:10',
      syncedAt: new Date(Date.now() - MARKETPLACE_CACHE_TTL_MS - 1).toISOString(),
      ...cachePayload,
    }));

    expect(readMarketplaceCache(teammate)).toBeNull();
    expect(window.localStorage.getItem(key)).toBeNull();
  });

  it('rejects a cache whose embedded scope does not match the requested cabinet', () => {
    const key = getMarketplaceCacheStorageKey(teammate);
    window.localStorage.setItem(key, JSON.stringify({
      version: 1,
      scopeKey: 'employer:999',
      syncedAt: new Date().toISOString(),
      ...cachePayload,
    }));

    expect(readMarketplaceCache(teammate)).toBeNull();
    expect(window.localStorage.getItem(key)).toBeNull();
  });

  it('preserves merchandising metadata without changing presentation order here', () => {
    const normalized = normalizePartnerProduct({
      id: 42,
      supplierId: 7,
      supplierName: 'Supplier',
      externalProductId: null,
      name: 'Produit vedette',
      sku: 'SKU-42',
      dentalCategory: 'Consommables',
      dentalSpecialty: 'Omnipratique',
      unit: 'boite',
      price: 125,
      availability: 'AVAILABLE',
      shortDescription: 'Court',
      longDescription: 'Long',
      benefits: ['Bénéfice'],
      isFeatured: true,
      sortOrder: 3,
    });

    expect(normalized.isFeatured).toBe(true);
    expect(normalized.sortOrder).toBe(3);
  });
});
