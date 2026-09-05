import { useEffect, useMemo, useState } from 'react';
import { Bell, Check, Clock3, RefreshCw } from 'lucide-react';
import { api } from '../../../../services/api';
import type { Tab } from '../types';

type MobileAlert = {
  id: number;
  patient_id?: number | null;
  patient_name?: string | null;
  type: string;
  title: string;
  message: string;
  priority?: string | null;
  created_at?: string | null;
};

type AlertsResponse = { total: number; alerts: MobileAlert[] };
type Filter = 'all' | 'priority';

function priorityMeta(value?: string | null) {
  const normalized = String(value || '').toUpperCase();
  if (['CRITICAL', 'URGENT', 'HIGH'].includes(normalized)) {
    return { label: 'Urgent', className: 'border-rose-500/25 bg-rose-500/5 text-rose-600', important: true };
  }
  if (['MEDIUM', 'IMPORTANT', 'WARNING'].includes(normalized)) {
    return { label: 'Important', className: 'border-amber-500/25 bg-amber-500/5 text-amber-700', important: true };
  }
  return { label: 'Info', className: 'border-primary/20 bg-primary/5 text-primary', important: false };
}

function actionFor(alert: MobileAlert): { label: string; tab: Tab } | null {
  const type = String(alert.type || '').toUpperCase();
  if (type.startsWith('OVERDUE_PAYMENT') || type.startsWith('HIGH_VALUE_RISK') || type.startsWith('ORTHO_SEMESTER_')) {
    return { label: 'Voir finance', tab: 'finance' };
  }
  if (alert.patient_id) return { label: 'Voir patient', tab: 'patients' };
  return null;
}

function relativeTime(value?: string | null) {
  if (!value) return 'Récente';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Récente';
  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
  if (minutes < 1) return 'À l’instant';
  if (minutes < 60) return `Il y a ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Il y a ${hours} h`;
  return `Il y a ${Math.floor(hours / 24)} j`;
}

export function NotificationsView({ onNavigate }: { onNavigate: (tab: Tab) => void }) {
  const [alerts, setAlerts] = useState<MobileAlert[]>([]);
  const [filter, setFilter] = useState<Filter>('all');
  const [loading, setLoading] = useState(true);
  const [mutatingId, setMutatingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<AlertsResponse>('/mobile/notifications');
      setAlerts(Array.isArray(response.data?.alerts) ? response.data.alerts : []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Impossible de charger les notifications.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const visible = useMemo(
    () => filter === 'all' ? alerts : alerts.filter(alert => priorityMeta(alert.priority).important),
    [alerts, filter],
  );

  const mutate = async (alert: MobileAlert, action: 'read' | 'snooze') => {
    setMutatingId(alert.id);
    setError(null);
    try {
      await api.patch(`/mobile/notifications/${alert.id}/${action}`);
      setAlerts(current => current.filter(item => item.id !== alert.id));
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Action impossible.');
    } finally {
      setMutatingId(null);
    }
  };

  return (
    <section className="pb-6" data-mobile-notifications>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">À traiter</p>
          <h1 className="mt-1 text-[24px] font-black text-text-main">Notifications</h1>
          <p className="mt-1 text-[11px] font-bold text-text-muted">{alerts.length} non lue{alerts.length > 1 ? 's' : ''}</p>
        </div>
        <button
          type="button"
          aria-label="Actualiser les notifications"
          onClick={() => void load()}
          disabled={loading}
          className="grid min-h-11 min-w-11 place-items-center rounded-full border border-glass-border bg-card text-text-muted disabled:opacity-50"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 rounded-[18px] border border-glass-border bg-card p-1.5">
        {([['all', 'Toutes'], ['priority', 'Prioritaires']] as const).map(([id, label]) => (
          <button
            key={id}
            type="button"
            aria-pressed={filter === id}
            onClick={() => setFilter(id)}
            className={`min-h-11 rounded-[14px] px-3 text-[11px] font-black ${filter === id ? 'bg-primary text-white' : 'text-text-muted'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-3 rounded-[18px] border border-rose-500/20 bg-rose-500/5 px-4 py-3 text-[11px] font-bold text-rose-600">
          {error}
        </div>
      )}

      {!loading && visible.length === 0 && (
        <div className="rounded-[24px] border border-glass-border bg-card px-5 py-8 text-center shadow-sm">
          <Bell size={28} className="mx-auto text-primary" />
          <h2 className="mt-3 text-[16px] font-black text-text-main">Aucune alerte à traiter</h2>
          <p className="mt-1 text-[11px] font-bold text-text-muted">Rien d’urgent dans ce filtre.</p>
        </div>
      )}

      <div className="grid gap-3">
        {visible.map(alert => {
          const meta = priorityMeta(alert.priority);
          const action = actionFor(alert);
          const busy = mutatingId === alert.id;
          return (
            <article key={alert.id} className="rounded-[24px] border border-glass-border bg-card p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <span className={`inline-flex rounded-full border px-2.5 py-1 text-[9px] font-black ${meta.className}`}>{meta.label}</span>
                  <h2 className="mt-2 text-[15px] font-black text-text-main">{alert.title}</h2>
                  {alert.patient_name && <p className="mt-1 text-[10px] font-black text-primary">{alert.patient_name}</p>}
                  <p className="mt-1 line-clamp-3 text-[11px] font-semibold leading-relaxed text-text-muted">{alert.message}</p>
                </div>
                <span className="shrink-0 text-[9px] font-bold text-text-muted">{relativeTime(alert.created_at)}</span>
              </div>

              <div className="mt-4 grid gap-2 sm:grid-cols-3">
                {action && (
                  <button
                    type="button"
                    onClick={() => onNavigate(action.tab)}
                    className="min-h-11 rounded-[16px] bg-primary px-3 text-[11px] font-black text-white"
                  >
                    {action.label}
                  </button>
                )}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void mutate(alert, 'read')}
                  className="flex min-h-11 items-center justify-center gap-1.5 rounded-[16px] border border-glass-border bg-background px-3 text-[11px] font-black text-text-main disabled:opacity-50"
                >
                  <Check size={14} /> Lu
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void mutate(alert, 'snooze')}
                  className="flex min-h-11 items-center justify-center gap-1.5 rounded-[16px] border border-glass-border bg-background px-3 text-[11px] font-black text-text-main disabled:opacity-50"
                >
                  <Clock3 size={14} /> 24 h
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
