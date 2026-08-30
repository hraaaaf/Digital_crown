import { beforeEach, describe, expect, it } from 'vitest';
import {
  STORAGE_CART_KEY,
  getMarketplaceCartStorageKey,
  readStoredCart,
  writeStoredCart,
} from './data';

const owner = { id: 10, employer_id: null };
const teammate = { id: 11, employer_id: 10 };
const otherTeammate = { id: 12, employer_id: 10 };

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
