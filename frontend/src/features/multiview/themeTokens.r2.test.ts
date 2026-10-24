/** LOT07 R2: prohibit fixed brand palettes inside UX code we own.
 * The globally maintained theme system is authoritative for all color choices.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const frontendRoot = process.cwd();
const source = (relativePath: string) =>
  readFileSync(resolve(frontendRoot, 'src', relativePath), 'utf8');

const fixedPalette = /\b(?:bg|text|border|ring|outline|from|via|to|hover:bg|hover:text|hover:border)-(?:blue|slate|amber|white|black|gray|red|emerald|rose|indigo|cyan|teal|pink)(?:-\d+)?(?:\/\d+)?\b/g;
const literalColor = /#[0-9a-f]{3,8}\b|\brgba?\s*\(\s*(?:\d|\.\d)/gi;

describe('DEC-R2 UX follows selected theme, never fixed palette', () => {
  it.each([
    'features/multiview/CabinetMultiViewLab.tsx',
    'features/multiview/HistoricBilanReadonlyPanel.tsx',
  ])('%s has only semantic theme classes', file => {
    const content = source(file);
    expect(content.match(fixedPalette) ?? []).toEqual([]);
    expect(content.match(literalColor) ?? []).toEqual([]);
    expect(content).toMatch(/(?:bg-card|bg-primary|bg-medical-pearl|border-border-main)/);
  });

  it.each([
    'features/multiview/CabinetMultiViewLab.css',
    'features/patients/PatientRadiologyPolish.css',
  ])('%s inherits theme CSS variables', file => {
    const content = source(file);
    expect(content.match(literalColor) ?? []).toEqual([]);
    expect(content).toContain('var(--');
    expect(content).not.toMatch(/(?:background|color|border-color):\s*\b(?:blue|white|black|red|gray|grey)\b/i);
  });

  it('new clinical media empty states are theme-derived', () => {
    const content = source('features/patients/components/PatientMediaTimeline.tsx');
    const start = content.indexOf('{!loading && !loadError && items.length === 0 && (');
    const end = content.indexOf('{!loading && !loadError && filteredItems.length > 0 && (', start);
    expect(start).toBeGreaterThan(0);
    expect(end).toBeGreaterThan(start);
    expect(content.slice(start, end).match(fixedPalette) ?? []).toEqual([]);
  });

  it('micropolish preserves semantic dark contrast, mobile discoverability and fail-closed 1280 mode', () => {
    const css = source('features/patients/PatientRadiologyPolish.css');
    const patient = source('features/patients/PatientDetailsInner.tsx');
    const multiview = source('features/multiview/CabinetMultiViewLab.tsx');
    expect(css).toContain(`[data-theme='dark'] [data-dc-patient-radiology="true"]`);
    expect(css).toContain('--primary: var(--status-info)');
    expect(css).toContain('--color-primary: var(--status-info)');
    expect(css).toContain('--color-primary-ink: var(--status-info)');
    expect(css).toContain('--color-on-primary: var(--bg-medical-pearl)');
    expect(css).toContain('--color-text-muted: color-mix(');
    expect(css).toContain('.dc-radiology-tab-scroll-hint');
    expect(patient).toContain('aria-describedby={isRadiology');
    expect(patient).toContain('Faites glisser pour afficher les autres onglets');
    expect(multiview).toContain('multiview-responsive-single-media-fallback');
    expect(multiview).toContain('Disposition trop large pour cet écran');
    expect(multiview).toContain('bg-info-surface');
  });

  it('theme engine exposes all configured semantic color roles', () => {
    const theme = source('index.css');
    for (const name of ['--card-bg', '--bg-medical-pearl', '--text-main',
      '--text-muted', '--border-color', '--border-hover', '--primary',
      '--text-on-primary', '--status-warning', '--status-warning-surface']) {
      expect(theme).toContain(name + ':');
    }
    for (const themeName of ['emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast']) {
      expect(theme).toContain("[data-theme='" + themeName + "']");
    }
  });
});
