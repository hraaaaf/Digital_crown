import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const hookSource = readSource('src/features/mobile/Dashboard/hooks/useMobileDashboard.ts');
const dashboardSource = readSource('src/features/mobile/Dashboard/MobileDashboard.tsx');
const storageSource = readSource('src/services/zka/MobileStorage.ts');
const addApptSource = readSource('src/features/mobile/Dashboard/components/AddApptModal.tsx');
const patientsSource = readSource('src/features/mobile/Dashboard/views/MobilePatientsView.tsx');

describe('Digital Crown Pocket production runtime scope', () => {
  it('does not preload retired Lab or Finance workflows', () => {
    expect(hookSource).not.toContain('fetchLabJobs');
    expect(hookSource).not.toContain('labJobService');
    expect(hookSource).not.toContain('LabJobStatus');
    expect(hookSource).not.toContain('/api/mobile/accounting/export-pdf');
    expect(hookSource).not.toContain('handleExportPDF');
    expect(hookSource).not.toContain('handleWhatsAppSend');
  });

  it('does not promote Pocket credentials into desktop auth or generic write APIs', () => {
    expect(storageSource).not.toContain("localStorage.setItem('token'");
    expect(hookSource).not.toContain("localStorage.setItem('token'");
    expect(addApptSource).not.toContain('/api/patients/');
    expect(addApptSource).not.toContain('/api/appointments/');
    expect(addApptSource).toContain('/api/mobile/patients');
    expect(addApptSource).toContain('/api/mobile/appointments');
    expect(patientsSource).not.toContain('MobileQuickDocumentSheet');
    expect(patientsSource).not.toContain('Créer un document');
  });

  it('keeps the production shell on the bounded Pocket surfaces', () => {
    for (const retired of ['FinanceView', 'LabView', 'BotView', 'DentistsView', 'StockView', 'LibraryView', 'MarketplaceView']) {
      expect(dashboardSource).not.toContain(retired);
    }
    expect(dashboardSource).toContain('PocketTodayOverview');
    expect(dashboardSource).toContain("actions.setActiveTab('patients')");
    expect(dashboardSource).toContain('initialSelectedId={initialPatientId}');
  });
});
