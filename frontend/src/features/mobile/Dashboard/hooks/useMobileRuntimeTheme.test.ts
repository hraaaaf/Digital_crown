import { beforeEach, describe, expect, it } from 'vitest';
import { applyMobileRuntimeTheme } from './useMobileRuntimeTheme';

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
    expect(localStorage.getItem('digitalcrown_theme')).toBe('rose');
    expect(localStorage.getItem('digitalcrown_font_fr')).toBe('playfair');
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
    expect(localStorage.getItem('digitalcrown_theme')).toBe('elite');
    expect(localStorage.getItem('digitalcrown_font_fr')).toBe('inter');
  });
});
