import type { Tab } from './Dashboard/types';

export const MOBILE_BRIDGE_ROUTES: Record<string, string> = {
  agenda: '/mobile/dashboard?tab=agenda',
};

export const MOBILE_BRIDGE_LABELS: Record<string, string> = {
  agenda: 'Digital Crown Pocket',
};

const DASHBOARD_TABS = new Set<Tab>([
  'agenda',
  'patients',
  'waiting-room',
  'frontdesk',
  'notifications',
  'securite',
]);

export function resolveBridgeRoute(destination: unknown): string {
  return typeof destination === 'string' && MOBILE_BRIDGE_ROUTES[destination]
    ? MOBILE_BRIDGE_ROUTES[destination]
    : MOBILE_BRIDGE_ROUTES.agenda;
}

export function resolveBridgeLabel(destination: unknown): string {
  return typeof destination === 'string' && MOBILE_BRIDGE_LABELS[destination]
    ? MOBILE_BRIDGE_LABELS[destination]
    : MOBILE_BRIDGE_LABELS.agenda;
}

export function resolveDashboardTab(search: string): Tab {
  const requested = new URLSearchParams(search).get('tab') as Tab | null;
  return requested && DASHBOARD_TABS.has(requested) ? requested : 'agenda';
}
