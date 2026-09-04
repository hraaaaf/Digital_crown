import { afterEach, describe, expect, it, vi } from 'vitest';
import { bootstrapMobileQuickIntent } from './mobileQuickIntent';

afterEach(() => {
  document.body.innerHTML = '';
  delete document.documentElement.dataset.mobileQuickIntent;
  sessionStorage.clear();
  window.history.replaceState({}, '', '/');
  vi.restoreAllMocks();
});

describe('bootstrapMobileQuickIntent', () => {
  it('consumes a photo intent and marks the canonical photo action', () => {
    window.history.replaceState({}, '', '/mobile/context');
    sessionStorage.setItem('dc-mobile-quick-intent', 'photo');
    vi.spyOn(window, 'setTimeout').mockImplementation(() => 1 as unknown as number);
    const button = document.createElement('button');
    button.dataset.m6aPhotoAction = '';
    button.scrollIntoView = vi.fn();
    document.body.appendChild(button);

    bootstrapMobileQuickIntent();

    expect(document.documentElement.dataset.mobileQuickIntent).toBe('photo');
    expect(sessionStorage.getItem('dc-mobile-quick-intent')).toBeNull();
  });

  it('ignores quick intents outside the secure context route', () => {
    window.history.replaceState({}, '', '/mobile/dashboard');
    sessionStorage.setItem('dc-mobile-quick-intent', 'scan');

    bootstrapMobileQuickIntent();

    expect(document.documentElement.dataset.mobileQuickIntent).toBeUndefined();
    expect(sessionStorage.getItem('dc-mobile-quick-intent')).toBe('scan');
  });
});
