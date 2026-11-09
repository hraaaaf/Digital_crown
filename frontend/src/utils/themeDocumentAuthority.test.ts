import { beforeEach, describe, expect, it } from 'vitest';
import { syncDesktopBodyThemeFromRoot } from './themeDocumentAuthority';

describe('global CSS theme authority: selected theme or Elite default', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.dataset.theme = '';
    document.body.dataset.theme = '';
  });

  it.each(['emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast'])(
    'mirrors the selected %s root theme to the desktop body',
    (selected) => {
      document.documentElement.dataset.theme = selected;
      document.body.dataset.theme = 'different-theme';
      syncDesktopBodyThemeFromRoot('/station');
      expect(document.body.dataset.theme).toBe(selected);
      expect(document.documentElement.dataset.theme).toBe(selected);
    },
  );

  it('uses the canonical :root Elite fallback when no theme is selected', () => {
    document.body.dataset.theme = 'rose';
    syncDesktopBodyThemeFromRoot('/hub');
    expect(document.documentElement.dataset.theme).toBe('');
    expect(document.body.dataset.theme).toBe('');
  });

  it.each(['/mobile', '/mobile/onboarding', '/mobile/dashboard', '/mobile/context'])(
    'never lets desktop storage overwrite the identity-scoped Pocket theme at %s',
    (path) => {
      localStorage.setItem('digitalcrown_theme', 'prestige'); // stale desktop selection
      document.documentElement.dataset.theme = 'ocean'; // Pocket owner
      document.body.dataset.theme = 'ocean';
      syncDesktopBodyThemeFromRoot(path);
      expect(document.documentElement.dataset.theme).toBe('ocean');
      expect(document.body.dataset.theme).toBe('ocean');
      expect(localStorage.getItem('digitalcrown_theme')).toBe('prestige');
    },
  );

  it('never forces Elite when a selected theme already exists on a desktop root', () => {
    document.documentElement.dataset.theme = 'emerald';
    syncDesktopBodyThemeFromRoot('/dashboard');
    expect(document.body.dataset.theme).toBe('emerald');
  });
});
