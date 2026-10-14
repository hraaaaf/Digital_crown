import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { beforeEach, describe, expect, it } from 'vitest';
import { accessiblePrimaryInk, applyMobileRuntimeTheme, textColorForHex } from './hooks/useMobileRuntimeTheme';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const POCKET = 'src/features/mobile/Dashboard/';
const polishedSurfaces = [
  'components/MobileHeader.tsx',
  'components/MobileBottomNav.tsx',
  'components/PocketTodayOverview.tsx',
  'components/MobileQuickActionHub.tsx',
  'views/PocketAgendaDay.tsx',
  'views/FrontdeskView.tsx',
  'views/FinanceView.tsx',
  'views/StockView.tsx',
  'views/LabView.tsx',
  'views/WaitingRoomView.tsx',
  'views/NotificationsView.tsx',
  'views/LibraryView.tsx',
  'views/DentistsView.tsx',
  'views/SecuriteView.tsx',
  'components/MobileNotificationCenter.tsx',
  'MobileDashboard.tsx',
  'MobilePreviewDashboard.tsx',
  'types.tsx',
];

function luminance(hex: string): number {
  const rgb = [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16) / 255);
  return rgb.map(c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
    .reduce((sum, c, index) => sum + c * [0.2126, 0.7152, 0.0722][index], 0);
}
function contrast(a: string, b: string): number {
  const [upper, lower] = [luminance(a), luminance(b)].sort((a, b) => b - a);
  return (upper + 0.05) / (lower + 0.05);
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute('style');
  document.body.removeAttribute('style');
  document.documentElement.dataset.theme = '';
  document.body.dataset.theme = '';
});

describe('P1/P2 iOS micro-polish color inheritance', () => {
  it('does not bake fixed palette colors into the polished Pocket surfaces', () => {
    const hardcoded = /#[a-f0-9]{3,8}\b|\b(?:bg|text|border|ring|hover:border)-(?:slate|white|black|rose|amber|emerald|blue|indigo|gray|sky|cyan|teal|green|red|orange)(?:-\d{2,3})?(?:\/\d{1,3})?\b/i;
    for (const relative of polishedSurfaces) {
      const source = readSource(POCKET + relative);
      expect(source, relative).not.toMatch(hardcoded);
    }
    const palette = readSource('src/index.css');
    expect(palette).toContain('--color-on-primary: var(--text-on-primary)');
    expect(palette).toContain('--color-primary-ink: var(--primary-ink)');
    expect(palette).toContain('--color-warning-surface: var(--status-warning-surface)');
    expect(palette).toContain("[data-theme='dark'], [data-theme='prestige']");
    const reducedMotion = readSource('src/features/mobile/mobileRuntimeTheme.css');
    expect(reducedMotion).toContain('prefers-reduced-motion: reduce');
    expect(reducedMotion).toContain("[data-theme='emerald']");
    expect(reducedMotion).toContain("[data-theme='dark']");
    expect(reducedMotion).toContain('[data-dc-mobile-shell]');
  });

  it.each([
    ['#003380', '#ffffff'],
    ['#059669', '#020617'],
    ['#3b82f6', '#020617'],
    ['#db2777', '#ffffff'],
    ['#000000', '#ffffff'],
    ['#ffffff', '#020617'],
    ['#475569', '#ffffff'],
    ['#0284c7', '#020617'],
  ])('chooses WCAG contrast against primary %s, not YIQ guesses', (primary, foreground) => {
    expect(textColorForHex(primary)).toBe(foreground);
    expect(contrast(primary, foreground)).toBeGreaterThanOrEqual(4.5);
  });

  it.each([
    ['#003380', '#ffffff', '#f8fafc'],
    ['#059669', '#fcfdfd', '#f0fdf4'],
    ['#db2777', '#fffbfb', '#fff1f2'],
    ['#3b82f6', '#1e293b', '#0f172a'],
    ['#0284c7', '#ffffff', '#f0f9ff'],
    ['#475569', '#ffffff', '#f1f5f9'],
    ['#4f46e5', '#0f172a', '#020617'],
    ['#000000', '#ffffff', '#ffffff'],
  ])('derives a 4.5:1 small-label primary ink while retaining the brand fill %s', (primary, card, canvas) => {
    const ink = accessiblePrimaryInk(primary, card, canvas);
    expect(ink).toMatch(/^#[a-f0-9]{6}$/);
    expect(contrast(ink as string, card)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(ink as string, canvas)).toBeGreaterThanOrEqual(4.5);
  });

  it.each([
    ['ocean', '#0284c7', '#fff', '#ffffff', '#f0f9ff'],
    ['graphite', '#475569', '#fff', '#ffffff', '#f1f5f9'],
    ['high-contrast', '#000', '#fff', '#ffffff', '#fff'],
  ])('accepts production-minified CSS hex shorthand for %s without a false safe fallback', (
    _theme, primary, shortCard, fullCard, canvas,
  ) => {
    const ink = accessiblePrimaryInk(primary, shortCard, canvas);
    expect(ink).toMatch(/^#[a-f0-9]{6}$/);
    expect(ink).toBe(accessiblePrimaryInk(primary, fullCard, canvas));
    const canonical = (value: string) => /^#[0-9a-f]{3}$/i.test(value)
      ? '#' + [...value.slice(1)].map(channel => channel + channel).join('')
      : value;
    expect(contrast(ink as string, canonical(shortCard))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(ink as string, canonical(canvas))).toBeGreaterThanOrEqual(4.5);
  });

  it('inherits selected dark, rose and high-contrast themes without a component-owned preset', () => {
    for (const selected_theme of ['prestige', 'dark', 'rose', 'emerald', 'ocean', 'graphite', 'high-contrast']) {
      applyMobileRuntimeTheme({ selected_theme });
      expect(document.documentElement.dataset.theme).toBe(selected_theme);
      expect(document.body.dataset.theme).toBe(selected_theme);
      expect(document.documentElement.style.getPropertyValue('--primary')).toBe('');
    }
    applyMobileRuntimeTheme({ selected_theme: 'emerald', primary_color: '#059669' });
    expect(document.documentElement.style.getPropertyValue('--text-on-primary')).toBe('#020617');
    applyMobileRuntimeTheme({ selected_theme: 'elite', primary_color: '#003380' });
    expect(document.documentElement.style.getPropertyValue('--text-on-primary')).toBe('#ffffff');
  });

  it('keeps theme switching in the demo harness rather than hardcoding Elite', () => {
    const demo = readSource(POCKET + 'MobilePreviewDashboard.tsx');
    expect(demo).toContain("new URLSearchParams(window.location.search).get('theme')");
    expect(demo).toContain("'high-contrast'");
    expect(demo).not.toContain("primary_color: '#003380'");
  });
});
