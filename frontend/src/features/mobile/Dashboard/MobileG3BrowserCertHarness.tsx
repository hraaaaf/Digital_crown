import { useMemo, useState } from 'react';
import { NotificationsView, type MobileAlert } from './views/NotificationsView';
import { WaitingRoomView } from './views/WaitingRoomView';
import { api } from '../../../services/api';

const WAITING_FIXTURE = [
  { id: 9101, patient_id: 101, patient_name: 'Sara BENALI', time: '09:00', motif: 'Détartrage', status: 'EN_ATTENTE', ticket_number: 4 },
  { id: 9102, patient_id: 102, patient_name: 'Omar ALAMI', time: '09:30', motif: 'Contrôle', status: 'EN_ATTENTE', ticket_number: 12 },
];

export function MobileG3BrowserCertHarness() {
  const tab = new URLSearchParams(window.location.search).get('tab') || 'notifications';
  const [appointments, setAppointments] = useState(WAITING_FIXTURE);
  const [error, setError] = useState<string | null>(null);
  const [lastNavigation, setLastNavigation] = useState<string | null>(null);
  const snapshot = useMemo(() => ({
    generated_at: new Date().toISOString(),
    role: 'DENTISTE',
    is_superadmin: false,
    appointments,
    finance: { today_revenue: 0, month_revenue: 0, month_variation: 0, appointments_count: 0, weekly_revenue: [], total_patients: 0, total_debt: 0 },
    debtors: [],
  }), [appointments]);

  const onStatusChange = async (id: number, status: string) => {
    setError(null);
    try {
      await api.patch(`/mobile/appointments/${id}/status`, { status });
      setAppointments(current => current.map(item => item.id === id ? { ...item, status } : item));
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Transition refusée');
    }
  };

  return (
    <main data-g3-browser-cert className="min-h-screen bg-background p-6 text-text-main">
      <p className="mb-4 text-xs font-black uppercase tracking-widest text-primary">G3 browser certification harness</p>
      {error && <p role="alert" className="mb-4 text-sm font-bold text-rose-600">{error}</p>}
      {lastNavigation && <p data-testid="g3-mobile-navigation">navigate:{lastNavigation}</p>}
      {tab === 'waiting-room'
        ? <WaitingRoomView snapshot={snapshot as any} onStatusChange={onStatusChange as any} />
        : <NotificationsView onNavigate={(nextTab) => setLastNavigation(nextTab)} />}
    </main>
  );
}

export type { MobileAlert };
