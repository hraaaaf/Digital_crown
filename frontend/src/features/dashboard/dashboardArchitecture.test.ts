import { describe, expect, it } from 'vitest';
import { BusinessInsights } from './components/BusinessInsights';
import { CabinetHealth } from './components/CabinetHealth';
import { DashboardHeader } from './components/DashboardHeader';
import { FinanceSummary } from './components/FinanceSummary';
import { IntelligenceAlerts } from './components/IntelligenceAlerts';
import { MarketplaceCard } from './components/MarketplaceCard';
import { QuickActions } from './components/QuickActions';
import { RecentActivity } from './components/RecentActivity';
import { WaitingRoom } from './components/WaitingRoom';
import { WeeklyPerformance } from './components/WeeklyPerformance';
import { useDashboardFinance } from './hooks/useDashboardFinance';
import { useDashboardStats } from './hooks/useDashboardStats';
import { usePatientSearch } from './hooks/usePatientSearch';
import { useProactiveAlerts } from './hooks/useProactiveAlerts';
import { useTodayAppointments } from './hooks/useTodayAppointments';

describe('Dashboard D4 — surface modulaire', () => {
  it('expose les dix composants canoniques', () => {
    const components = [
      DashboardHeader,
      QuickActions,
      MarketplaceCard,
      RecentActivity,
      WaitingRoom,
      WeeklyPerformance,
      FinanceSummary,
      CabinetHealth,
      IntelligenceAlerts,
      BusinessInsights,
    ];

    expect(components).toHaveLength(10);
    components.forEach(component => expect(typeof component).toBe('function'));
  });

  it('expose les loaders par domaine', () => {
    const loaders = [
      useDashboardStats,
      useTodayAppointments,
      useDashboardFinance,
      useProactiveAlerts,
      usePatientSearch,
    ];

    expect(loaders).toHaveLength(5);
    loaders.forEach(loader => expect(typeof loader).toBe('function'));
  });
});
