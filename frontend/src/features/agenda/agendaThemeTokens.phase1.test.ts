/** Agenda phase 1: semantic themes on clinical-UI surfaces, no behavioral changes.
 * QR raster backdrop is a single documented neutral white exception for scanners.
 * Overlay backdrops may use translucent black independent of theme.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) =>
  readFileSync(resolve(process.cwd(), 'src/features/agenda', file), 'utf8');
const files = [
  'PendingRequestCard.tsx',
  'FrontdeskModal.tsx',
  'AppointmentMobileBridge.tsx',
  'GoogleImportModal.tsx',
] as const;
const fixedUi = /(?:[a-z-]+:)*(?:bg|text|border|ring|fill|stroke|outline|from|to|hover:bg|hover:text)-(?:slate|gray|blue|red|green|orange|yellow|amber|indigo|emerald|rose|purple|pink|cyan|teal|zinc|stone|neutral|sky)-\d{2,3}(?:\/\d+)?\b/g;

describe('Agenda phase 1 semantic theme compliance', () => {
  it.each(files)('%s has no hardcoded UI palette classes', name => {
    expect(source(name).match(fixedUi) ?? []).toEqual([]);
  });

  it('all form actions and fields inherit the selected theme', () => {
    const frontdesk = source('FrontdeskModal.tsx');
    expect(frontdesk).toContain('bg-card text-text-main');
    expect(frontdesk).toContain('bg-input-field text-text-main');
    expect(frontdesk).toContain('bg-primary text-on-primary');
    expect(frontdesk).toContain('bg-danger-surface');
    expect(frontdesk).toContain('border-danger-border');
    expect(frontdesk).toContain('focus-visible:outline-primary');
  });

  it('approval, rejection, warnings and info use semantic statuses', () => {
    const request = source('PendingRequestCard.tsx');
    for (const role of ['warning', 'danger', 'info']) {
      expect(request).toContain('bg-' + role + '-surface');
      expect(request).toContain('border-' + role + '-border');
      expect(request).toContain('text-' + role);
    }
    expect(request).toContain('bg-primary text-on-primary');
  });

  it('preserves the scan-safe QR backdrop as the only fixed white surface', () => {
    const bridge = source('AppointmentMobileBridge.tsx');
    expect(bridge.match(/\bbg-white\b/g) ?? []).toHaveLength(1);
    expect(bridge).toMatch(/<img src=\{bridge\.qr_code\}[^>]+bg-white[^>]+alt=/);
  });

  it('retains readonly/sensitive QR and server-derived invitation contracts', () => {
    const bridge = source('AppointmentMobileBridge.tsx');
    expect(bridge).toContain("data.contains_patient_data !== false");
    expect(bridge).toContain("data.contains_resource_data !== false");
    expect(bridge).toContain("api.post('/mobile/resource-bridge-pairing'");
    expect(bridge).toContain('bg-success-surface');
    expect(bridge).toContain('bg-danger-surface');
  });

  it('ICS import remains an explicit action with thematic error feedback', () => {
    const ics = source('GoogleImportModal.tsx');
    expect(ics).toContain('bg-primary text-on-primary');
    expect(ics).toContain('bg-danger-surface text-danger');
    expect(ics).toContain('border-border-main');
    expect(ics).toContain('bg-background');
  });

  it('the source of theme roles and eight themes is the central stylesheet', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
    for (const token of ['--color-primary:', '--color-on-primary:', '--color-warning-surface:',
                         '--color-danger-surface:', '--color-success-surface:', '--color-info-surface:']) {
      expect(css).toContain(token);
    }
    for (const theme of ['emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast']) {
      expect(css).toContain("[data-theme='" + theme + "']");
    }
  });
});
