import type { Tab } from './Dashboard/types';

export const MOBILE_BRIDGE_ROUTES: Record<string, string> = {
  agenda: '/mobile/dashboard?tab=agenda',
  patients: '/mobile/dashboard?tab=patients',
  finance: '/mobile/dashboard?tab=finance',
  lab: '/mobile/dashboard?tab=lab',
  assistant: '/mobile/dashboard?tab=bot',
  security: '/mobile/dashboard?tab=securite',
  dentists: '/mobile/dashboard?tab=dentists',
  superadmin: '/mobile/superadmin',
};

export const MOBILE_BRIDGE_LABELS: Record<string, string> = {
  agenda: 'Agenda',
  patients: 'Patients',
  finance: 'Finance',
  lab: 'Labo',
  assistant: 'Assistant',
  security: 'Sécurité',
  dentists: 'Équipe praticiens',
  superadmin: 'SuperAdmin',
};

const DASHBOARD_TABS = new Set<Tab>(['agenda', 'patients', 'finance', 'lab', 'bot', 'securite', 'dentists']);

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
