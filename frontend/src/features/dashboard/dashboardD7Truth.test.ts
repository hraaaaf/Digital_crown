import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const readSource = (relativePath: string) => readFileSync(
  fileURLToPath(new URL(relativePath, import.meta.url)),
  'utf-8',
);

describe('Dashboard D7 — vérité des états dégradés', () => {
  it('n’utilise plus UTC pour déterminer les rendez-vous du jour', () => {
    const source = readSource('./hooks/useTodayAppointments.ts');
    expect(source.includes('toISOString()')).toBe(false);
    expect(source.includes('getLocalDayBounds')).toBe(true);
  });

  it('n’injecte plus de statistiques synthétiques en cas d’erreur', () => {
    const source = readSource('./hooks/useDashboardStats.ts');
    expect(source.includes('EMPTY_STATS')).toBe(false);
    expect(source.includes("setStats(null)")).toBe(true);
    expect(source.includes("setStatsState('error')")).toBe(true);
  });

  it('affiche des états indisponibles au lieu de faux états vides', () => {
    const waitingRoom = readSource('./components/WaitingRoom.tsx');
    const recentActivity = readSource('./components/RecentActivity.tsx');
    const weeklyPerformance = readSource('./components/WeeklyPerformance.tsx');

    expect(waitingRoom.includes('Rendez-vous indisponibles')).toBe(true);
    expect(recentActivity.includes('Activité indisponible')).toBe(true);
    expect(weeklyPerformance.includes('Performance indisponible')).toBe(true);
  });
});
