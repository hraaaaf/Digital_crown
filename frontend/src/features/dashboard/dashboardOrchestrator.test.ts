import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (relativePath: string) => readFileSync(new URL(relativePath, import.meta.url), 'utf8');

const dashboardSource = read('../../pages/Dashboard.tsx');
const componentSources = [
  './components/DashboardHeader.tsx',
  './components/QuickActions.tsx',
  './components/MarketplaceCard.tsx',
  './components/RecentActivity.tsx',
  './components/WaitingRoom.tsx',
  './components/WeeklyPerformance.tsx',
  './components/FinanceSummary.tsx',
  './components/CabinetHealth.tsx',
  './components/IntelligenceAlerts.tsx',
  './components/BusinessInsights.tsx',
].map(read).join('\n');

describe('Dashboard D4 — contrat orchestrateur', () => {
  it('garde Dashboard.tsx compact et sans transport API direct', () => {
    expect(dashboardSource.split('\n').length).toBeLessThanOrEqual(430);
    expect(dashboardSource).not.toMatch(/\bapi\s*\./);
    expect(dashboardSource).not.toMatch(/from\s+['"]\.\.\/services\/api['"]/);
  });

  it('préserve les ancres data-tour canoniques après extraction', () => {
    for (const tourId of [
      'dashboard-stats',
      'dashboard-recent',
      'dashboard-waiting',
      'dashboard-health',
      'dashboard-finance',
    ]) {
      expect(componentSources).toContain(`data-tour="${tourId}"`);
    }
  });
});
