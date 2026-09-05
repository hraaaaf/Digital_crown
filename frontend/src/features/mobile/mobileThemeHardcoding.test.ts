import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const FORBIDDEN_FONT_CLASS = /\bfont-(?:outfit|sans|serif|mono)\b/;
const FORBIDDEN_LOCAL_BRAND_COLOR = /#[0-9a-fA-F]{3,8}\b/;
const CRITICAL_MOBILE_SURFACES = [
  'src/features/mobile/Dashboard/MobileDashboard.tsx',
  'src/features/mobile/Dashboard/components/MobileHeader.tsx',
  'src/features/mobile/Dashboard/views/MobilePatientsView.tsx',
  'src/features/mobile/Dashboard/views/MobilePatientsGate.tsx',
  'src/features/mobile/Dashboard/MobilePreviewDashboard.tsx',
  'src/features/mobile/Dashboard/components/MobileQuickActionHub.tsx',
  'src/features/mobile/Dashboard/components/MobileQuickPatientFlow.tsx',
  'src/features/mobile/Dashboard/components/MobileQuickNewPatientModal.tsx',
];
const MOB3_SURFACES = [
  'src/features/mobile/Dashboard/components/MobileQuickActionHub.tsx',
  'src/features/mobile/Dashboard/components/MobileQuickPatientFlow.tsx',
  'src/features/mobile/Dashboard/components/MobileQuickNewPatientModal.tsx',
];

describe('mobile theme hardcoding guard', () => {
  it('keeps new mobile surfaces free of component-owned font utilities', () => {
    const offenders = CRITICAL_MOBILE_SURFACES.filter((path) =>
      FORBIDDEN_FONT_CLASS.test(readFileSync(join(process.cwd(), path), 'utf8')),
    );
    expect(offenders, `Hardcoded mobile font utilities: ${offenders.join(', ')}`).toEqual([]);
  });

  it('keeps MOB-3 brand colors token-driven', () => {
    const offenders = MOB3_SURFACES.filter((path) =>
      FORBIDDEN_LOCAL_BRAND_COLOR.test(readFileSync(join(process.cwd(), path), 'utf8')),
    );
    expect(offenders, `Hardcoded MOB-3 brand colors: ${offenders.join(', ')}`).toEqual([]);
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
