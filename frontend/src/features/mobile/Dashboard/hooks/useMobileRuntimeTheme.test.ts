import { beforeEach, describe, expect, it } from 'vitest';
import { applyMobileRuntimeTheme, bootstrapMobileRuntimeTheme, mobileThemeCacheKey } from './useMobileRuntimeTheme';

describe('mobile runtime theme contract', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('style');
    document.body.removeAttribute('style');
    document.documentElement.dataset.theme = '';
    document.body.dataset.theme = '';
  });

  it('applies the cabinet-selected theme, palette and font without a component-owned brand choice', () => {
    applyMobileRuntimeTheme({
      selected_theme: 'rose',
      primary_color: '#db2777',
      secondary_color: '#9d174d',
      accent_color: '#f472b6',
      app_accent_color: '#be185d',
      font_fr: 'playfair',
    });

    expect(document.documentElement.dataset.theme).toBe('rose');
    expect(document.body.dataset.theme).toBe('rose');
    expect(document.documentElement.style.getPropertyValue('--primary')).toBe('#db2777');
    expect(document.documentElement.style.getPropertyValue('--secondary')).toBe('#9d174d');
    expect(document.documentElement.style.getPropertyValue('--accent')).toBe('#f472b6');
    expect(document.documentElement.style.getPropertyValue('--app-accent')).toBe('#be185d');
    expect(document.documentElement.style.getPropertyValue('--app-font-family')).toContain('Playfair Display');
    expect(localStorage.getItem('digitalcrown_theme')).toBeNull();
    expect(localStorage.getItem('digitalcrown_font_fr')).toBeNull();
  });

  it('replaces stale theme overrides when the saved cabinet configuration changes', () => {
    applyMobileRuntimeTheme({
      selected_theme: 'prestige',
      primary_color: '#3b82f6',
      app_accent_color: '#60a5fa',
      font_fr: 'outfit',
    });

    applyMobileRuntimeTheme({
      selected_theme: 'elite',
      primary_color: '#003380',
      secondary_color: '#1e40af',
      accent_color: '#60a5fa',
      app_accent_color: null,
      font_fr: 'inter',
    });

    expect(document.documentElement.dataset.theme).toBe('');
    expect(document.documentElement.style.getPropertyValue('--primary')).toBe('#003380');
    expect(document.documentElement.style.getPropertyValue('--app-accent')).toBe('');
    expect(document.documentElement.style.getPropertyValue('--app-font-family')).toContain('Inter');
    expect(localStorage.getItem('digitalcrown_theme')).toBeNull();
    expect(localStorage.getItem('digitalcrown_font_fr')).toBeNull();
  });
  it('partitions cached themes by cabinet, device and API origin', () => {
    const a = mobileThemeCacheKey({ publicId: 'cabinet-A', device_id: 'phone-1', api_base_url: 'https://a.example' });
    const b = mobileThemeCacheKey({ publicId: 'cabinet-B', device_id: 'phone-1', api_base_url: 'https://a.example' });
    const otherDevice = mobileThemeCacheKey({ publicId: 'cabinet-A', device_id: 'phone-2', api_base_url: 'https://a.example' });
    const otherServer = mobileThemeCacheKey({ publicId: 'cabinet-A', device_id: 'phone-1', api_base_url: 'https://b.example' });
    expect(new Set([a, b, otherDevice, otherServer]).size).toBe(4);
    applyMobileRuntimeTheme({ selected_theme: 'rose', primary_color: '#db2777' }, a);
    expect(localStorage.getItem(a)).toContain('rose');
    expect(localStorage.getItem(b)).toBeNull();
  });

  it('resets cabinet A overrides before cabinet B is loaded', () => {
    applyMobileRuntimeTheme({ selected_theme: 'prestige', primary_color: '#123456', app_accent_color: '#654321', font_fr: 'playfair' });
    bootstrapMobileRuntimeTheme();
    expect(document.documentElement.dataset.theme).toBe('');
    expect(document.body.dataset.theme).toBe('');
    expect(document.documentElement.style.getPropertyValue('--primary')).toBe('');
    expect(document.documentElement.style.getPropertyValue('--app-accent')).toBe('');
    expect(document.documentElement.style.getPropertyValue('--app-font-family')).toContain('Inter');
  });
});
