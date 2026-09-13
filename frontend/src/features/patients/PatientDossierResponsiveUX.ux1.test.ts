import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');

const patient = read('src/features/patients/PatientDetailsInner.tsx');
const bridge = read('src/features/patients/components/PatientMobileBridge.tsx');
const tabs = read('src/features/admin/DocumentStudio/StudioTabs.tsx');
const layout = read('src/components/Layout/MainLayout.tsx');
const css = read('src/components/Layout/patientDossierResponsive.css');

describe('UX1 patient dossier responsive contract', () => {
  it('keeps patient navigation discoverable on compact viewports', () => {
    expect(patient).toContain('data-tour="patient-tabs"');
    expect(css).toContain('[data-tour="patient-tabs"]');
    expect(css).toContain('scroll-snap-type: x mandatory');
    expect(css).toContain('mask-image: linear-gradient');
  });

  it('shows all imaging modalities in a compact three-column layout', () => {
    expect(patient).toContain('aria-label="Modalités d’imagerie"');
    expect(css).toContain('grid-template-columns: repeat(3, minmax(0, 1fr))');
    expect(css).toContain('white-space: normal !important');
  });

  it('exposes all six document types without hidden horizontal scrolling', () => {
    expect(tabs).toContain('grid-cols-2 sm:grid-cols-3 lg:flex');
    expect(tabs).not.toContain('overflow-x-auto');
    expect(tabs).toContain('w-full lg:w-auto');
  });

  it('keeps CrownBot inside mobile safe areas and uses a viewport overlay when open', () => {
    expect(layout).toContain("./patientDossierResponsive.css");
    expect(layout).toContain('bottom-[max(1rem,env(safe-area-inset-bottom))]');
    expect(layout).toContain('fixed inset-3 z-[1000]');
    expect(layout).toContain('sm:w-[400px] sm:h-[600px]');
    expect(layout).toContain("aria-expanded={isBotOpen}");
  });

  it('keeps the mobile bridge available without spending a full text row', () => {
    expect(bridge).toContain('min-h-9 sm:min-h-11');
    expect(bridge).toContain('hidden sm:inline');
    expect(bridge).toContain('aria-label="Ouvrir ce patient sur mobile"');
  });
});
