import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  join(process.cwd(), 'src/features/mobile/Onboarding/OnboardingScanner.tsx'),
  'utf8',
);
const palette = readFileSync(join(process.cwd(), 'src/index.css'), 'utf8');

describe('Pocket onboarding consumes canonical selected/default theme tokens', () => {
  it('does not locally own background, text, border or status colors', () => {
    const unsupportedHex = /#[0-9a-fA-F]{3,8}\b/g;
    const fixedPalette = /\b(?:bg|text|border)-(?:slate|gray|blue|indigo|amber|emerald|rose|red|green|yellow|pink|orange)(?:[-/][\w]+)?\b/g;
    expect(source.match(unsupportedHex) ?? [], 'local hexadecimal colors').toEqual([]);
    expect(source.match(fixedPalette) ?? [], 'hardcoded Tailwind color palettes').toEqual([]);
    expect(source).not.toContain('bg-white');
    expect(source).not.toContain('text-white');
    expect(source).not.toContain('document.documentElement.dataset.theme =');
    expect(source).not.toContain('document.body.dataset.theme =');
  });

  it('uses global tokens on all six page shells including onboarding failures', () => {
    expect(source.match(/data-dc-mobile-shell className="[^"]*bg-background text-text-main"/g)?.length).toBe(6);
    for (const semanticRole of ['bg-card', 'bg-input-field', 'bg-primary', 'text-on-primary',
      'text-text-muted', 'bg-success-surface', 'bg-warning-surface', 'bg-danger-surface',
      'text-success', 'text-warning', 'text-danger']) {
      expect(source).toContain(semanticRole);
    }
  });

  it('keeps both logos visible through a theme-owned contrast filter', () => {
    expect(source.match(/var\(--theme-logo-filter\)/g)?.length).toBe(2);
    expect(palette).toContain('--theme-logo-filter: brightness(1);');
    expect(palette.match(/--theme-logo-filter: brightness\(0\) invert\(1\);/g)?.length).toBe(2);
  });

  it('resolves semantic colors through global CSS declarations including default Elite', () => {
    for (const token of ['--color-background: var(--bg-medical-pearl)',
      '--color-card: var(--card-bg)', '--color-input-field: var(--input-bg)',
      '--color-on-primary: var(--text-on-primary)', '--color-success-surface: var(--status-success-surface)',
      '--color-warning-surface: var(--status-warning-surface)',
      '--color-danger-surface: var(--status-danger-surface)']) {
      expect(palette).toContain(token);
    }
    for (const selected of ['emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast']) {
      expect(palette).toContain(`[data-theme='${selected}']`);
    }
    expect(palette).toContain(':root {');
  });
});
