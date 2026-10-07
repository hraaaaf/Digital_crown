import { useEffect, useMemo, useState } from 'react';
import { NotificationsView, type MobileAlert } from './views/NotificationsView';
import { WaitingRoomView } from './views/WaitingRoomView';
import { api } from '../../../services/api';
import { useAuthStore } from '../../../stores/useAuthStore';
import { MobileStorage } from '../../../services/zka/MobileStorage';

const DEFAULT_WAITING_FIXTURE = [
  { id: 9101, patient_id: 101, patient_name: 'Sara BENALI', time: '09:00', motif: 'Détartrage', status: 'EN_ATTENTE', ticket_number: 4 },
  { id: 9102, patient_id: 102, patient_name: 'Omar ALAMI', time: '09:30', motif: 'Contrôle', status: 'EN_ATTENTE', ticket_number: 12 },
];

export function MobileG3BrowserCertHarness() {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const tab = params.get('tab') || 'notifications';
  const patientId = Number(params.get('patientId') || '') || 101;
  const patientName = params.get('patientName') || 'Sara BENALI';
  const ticketNumber = Number(params.get('ticket') || '') || 4;
  const initialAppointments = useMemo(
    () => params.get('patientId')
      ? [{ id: 9101, patient_id: patientId, patient_name: patientName, time: '09:00', motif: 'Certification photo', status: 'EN_ATTENTE', ticket_number: ticketNumber }]
      : DEFAULT_WAITING_FIXTURE,
    [params, patientId, patientName, ticketNumber],
  );
  const [appointments, setAppointments] = useState(initialAppointments);
  const [authReady, setAuthReady] = useState(false);
  const authenticatedUser = useAuthStore(state => state.user);

  const certificationToken = localStorage.getItem('token');
  if (certificationToken) MobileStorage.setBiometricAccessToken(certificationToken);

  useEffect(() => {
    let cancelled = false;
    // Preview-cert harness: keep the injected mobile token stable across React
    // StrictMode's development effect replay. The whole harness is isolated
    // behind the preview-only /mobile/g3-cert entrypoint.
    if (certificationToken) MobileStorage.setBiometricAccessToken(certificationToken);
    void useAuthStore.getState().checkAuth().finally(() => {
      if (!cancelled) setAuthReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, [certificationToken]);

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

  if (!authReady) {
    return <main data-g3-browser-cert data-auth-state="loading" className="min-h-screen bg-background p-6 text-text-main">Chargement certification…</main>;
  }

  if (!authenticatedUser) {
    return <main data-g3-browser-cert data-auth-state="error" className="min-h-screen bg-background p-6 text-text-main"><p role="alert">Authentification certification indisponible</p></main>;
  }

  return (
    <main data-g3-browser-cert data-auth-state="ready" className="min-h-screen bg-background p-6 text-text-main">
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
