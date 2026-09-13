import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');

const route = read('src/features/patients/PatientDetails.tsx');
const patient = read('src/features/patients/PatientDetailsInner.tsx');
const bridge = read('src/features/patients/components/PatientMobileBridge.tsx');
const tabs = read('src/features/admin/DocumentStudio/StudioTabs.tsx');
const layout = read('src/components/Layout/MainLayout.tsx');
const header = read('src/components/Header.tsx');
const app = read('src/App.tsx');
const css = read('src/components/Layout/patientDossierResponsive.css');

describe('UX1 patient dossier responsive contract', () => {
  it('loads the responsive contract at the patient route boundary', () => {
    expect(route).toContain("../../components/Layout/patientDossierResponsive.css");
  });

  it('keeps every patient navigation destination visible on compact viewports', () => {
    expect(patient).toContain('data-tour="patient-tabs"');
    expect(css).toContain('[data-tour="patient-tabs"]');
    expect(css).toContain('grid-template-columns: repeat(auto-fit, minmax(3.75rem, 1fr))');
    expect(css).toContain('overflow: visible !important');
    expect(css).toContain('mask-image: none !important');
    expect(css).not.toContain('scroll-snap-type: x mandatory');
  });

  it('shows all imaging modalities in a compact three-column layout', () => {
    expect(patient).toContain('aria-label="Modalités d’imagerie"');
    expect(css).toContain('grid-template-columns: repeat(3, minmax(0, 1fr))');
    expect(css).toContain('white-space: normal !important');
    expect(css).toContain('min-height: 2.75rem !important');
  });

  it('exposes all six document types without hidden horizontal scrolling', () => {
    expect(tabs).toContain('grid-cols-2 sm:grid-cols-3 lg:flex');
    expect(tabs).not.toContain('overflow-x-auto');
    expect(tabs).toContain('w-full lg:w-auto');
  });

  it('moves the patient CrownBot launcher into the compact header and keeps it reachable', () => {
    expect(header).toContain('data-ux1-c-crownbot-header');
    expect(header).toContain('min-w-11 min-h-11');
    expect(header).toContain('pl-16 pr-3 sm:pl-20 sm:pr-6');
    expect(header).toContain('hidden lg:flex items-center gap-4');
    expect(layout).toContain("onToggleCrownBot={isPatientRoute ? () => setIsBotOpen(value => !value) : undefined}");
    expect(layout).toContain("isPatientRoute ? 'hidden lg:block' : ''");
    expect(layout).toContain('lg:w-[400px] lg:h-[600px]');
  });

  it('keeps compact patient toasts non-blocking and below CrownBot', () => {
    expect(app).toContain('const ContextualToaster');
    expect(app).toContain('window.innerWidth < 1024');
    expect(app).toContain("position={patientCompact ? 'top-center' : 'bottom-right'}");
    expect(app).toContain("maxWidth: patientCompact ? 'calc(100vw - 24px)' : '420px'");
    expect(app).toContain('<ContextualToaster />');
    expect(css).toContain('[data-rht-toaster]');
    expect(css).toContain('top: 5.5rem !important');
    expect(css).toContain('z-index: 900 !important');
    expect(css).toContain('pointer-events: none !important');
  });

  it('keeps the mobile bridge compact without shrinking the touch target below 44px', () => {
    expect(bridge).toContain('min-h-11 min-w-11');
    expect(bridge).toContain('hidden sm:inline');
    expect(bridge).toContain('aria-label="Ouvrir ce patient sur mobile"');
  });
});
