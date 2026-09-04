import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const FORBIDDEN_FONT_CLASS = /\bfont-(?:outfit|sans|serif|mono)\b/;
const CRITICAL_MOB2_SURFACES = [
  'src/features/mobile/Dashboard/MobileDashboard.tsx',
  'src/features/mobile/Dashboard/components/MobileHeader.tsx',
  'src/features/mobile/Dashboard/views/MobilePatientsView.tsx',
  'src/features/mobile/Dashboard/views/MobilePatientsGate.tsx',
  'src/features/mobile/Dashboard/MobilePreviewDashboard.tsx',
];

describe('mobile theme hardcoding guard', () => {
  it('keeps new MOB-2 surfaces free of component-owned font utilities', () => {
    const offenders = CRITICAL_MOB2_SURFACES.filter((path) =>
      FORBIDDEN_FONT_CLASS.test(readFileSync(join(process.cwd(), path), 'utf8')),
    );
    expect(offenders, `Hardcoded MOB-2 font utilities: ${offenders.join(', ')}`).toEqual([]);
  });

  it('routes legacy mobile font utilities through the cabinet runtime font', () => {
    const css = readFileSync(
      join(process.cwd(), 'src/features/mobile/mobileRuntimeTheme.css'),
      'utf8',
    );
    expect(css).toContain("html[data-mobile-theme-runtime='true']");
    expect(css).toContain('.font-outfit');
    expect(css).toContain('.font-sans');
    expect(css).toContain('.font-serif');
    expect(css).toContain('.font-mono');
    expect(css).toContain('var(--app-font-family');
  });
});
