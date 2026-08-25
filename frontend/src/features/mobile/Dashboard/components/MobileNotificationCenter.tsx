import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Bell, BellOff, Check, Clock3, RefreshCw, X } from 'lucide-react';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

interface MobileNotification {
  id: number;
  patient_id?: number | null;
  patient_name?: string | null;
  type: string;
  title: string;
  message: string;
  priority?: number | string | null;
  created_at?: string | null;
}

type LoadStatus = 'idle' | 'loading' | 'success' | 'error';

function resolveApiBaseUrl(stored: string): string {
  const normalized = stored.endsWith('/') ? stored.slice(0, -1) : stored;
  if (typeof window === 'undefined') return normalized;
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return normalized;
  if (normalized.includes('localhost') || normalized.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return normalized;
}

function priorityTone(priority: MobileNotification['priority']) {
  return Number(priority) === 1
    ? 'border-rose-200 bg-rose-500/5'
    : 'border-border-main bg-card';
}

export function MobileNotificationCenter() {
  const [alerts, setAlerts] = useState<MobileNotification[]>([]);
  const [status, setStatus] = useState<LoadStatus>('idle');
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [mutatingId, setMutatingId] = useState<number | null>(null);

  const syncAppBadge = useCallback((count: number) => {
    if (typeof navigator === 'undefined') return;
    const badgeNavigator = navigator as Navigator & {
      setAppBadge?: (contents?: number) => Promise<void>;
      clearAppBadge?: () => Promise<void>;
    };
    const operation = count > 0
      ? badgeNavigator.setAppBadge?.(count)
      : badgeNavigator.clearAppBadge?.();
    void operation?.catch(() => undefined);
  }, []);

  const load = useCallback(async () => {
    try {
      setStatus('loading');
      setError('');
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile expirée ou révoquée.');
      const response = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/notifications`, {
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Notifications indisponibles (${response.status}).`);
      }
      const payload = await response.json();
      const next = Array.isArray(payload.alerts) ? payload.alerts : [];
      setAlerts(next);
      syncAppBadge(next.length);
      setStatus('success');
    } catch (err) {
      setStatus('error');
      setError(err instanceof TypeError
        ? 'Serveur du cabinet inaccessible.'
        : err instanceof Error ? err.message : 'Notifications indisponibles.');
    }
  }, [syncAppBadge]);

  useEffect(() => {
    void load();
    const onOnline = () => { void load(); };
    const onFocus = () => { void load(); };
    window.addEventListener('online', onOnline);
    window.addEventListener('focus', onFocus);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('focus', onFocus);
    };
  }, [load]);

  const mutate = async (id: number, action: 'read' | 'snooze') => {
    setMutatingId(id);
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile expirée ou révoquée.');
      const response = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/notifications/${id}/${action}`, {
        method: 'PATCH',
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Action refusée (${response.status}).`);
      }
      setAlerts(current => {
        const next = current.filter(alert => alert.id !== id);
        syncAppBadge(next.length);
        return next;
      });
      setError('');
      setStatus('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action impossible.');
      setStatus('error');
    } finally {
      setMutatingId(null);
    }
  };

  const unreadLabel = alerts.length > 9 ? '9+' : String(alerts.length);

  return (
    <>
      <button
        type="button"
        onClick={() => { setOpen(true); void load(); }}
        aria-label={alerts.length ? `Notifications, ${alerts.length} non lues` : 'Notifications'}
        aria-haspopup="dialog"
        aria-expanded={open}
        className="relative h-12 w-12 shrink-0 rounded-[16px] border border-glass-border bg-card shadow-elite backdrop-blur-md flex items-center justify-center text-primary active:scale-95 transition-transform"
        style={{ backgroundColor: 'var(--glass-bg)' }}
      >
        <Bell size={18} aria-hidden="true" />
        {alerts.length > 0 && (
          <span className="absolute -right-1 -top-1 min-w-5 h-5 px-1 rounded-full bg-rose-500 text-white text-[9px] font-black flex items-center justify-center border-2 border-white" aria-hidden="true">
            {unreadLabel}
          </span>
        )}
      </button>

      {open && (
        <>
          <button
            type="button"
            tabIndex={-1}
            aria-label="Fermer les notifications"
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-[80] bg-slate-950/25 backdrop-blur-[2px]"
          />
          <section
            role="dialog"
            aria-modal="true"
            aria-label="Notifications"
            className="fixed z-[90] left-3 right-3 bottom-[max(12px,env(safe-area-inset-bottom))] mx-auto max-w-md max-h-[78dvh] overflow-hidden rounded-[30px] border border-glass-border bg-card shadow-2xl backdrop-blur-xl flex flex-col"
            style={{ backgroundColor: 'var(--glass-bg)' }}
          >
            <div className="px-5 pt-5 pb-4 border-b border-border-main/70 flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Notifications</p>
                <h2 className="text-xl font-black text-text-main mt-1">À traiter</h2>
                <p className="text-[11px] font-bold text-text-muted mt-1">
                  {alerts.length ? `${alerts.length} non lue${alerts.length > 1 ? 's' : ''}` : 'Aucune alerte en attente'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Fermer"
                className="h-12 w-12 shrink-0 rounded-2xl border border-border-main bg-white/70 flex items-center justify-center text-text-muted active:scale-95 transition-transform"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>

            <div className="overflow-y-auto px-4 py-4 space-y-3">
              {status === 'loading' && alerts.length === 0 && (
                <div className="min-h-32 rounded-[22px] border border-border-main bg-white/60 flex flex-col items-center justify-center gap-3 text-text-muted">
                  <RefreshCw size={20} className="animate-spin" aria-hidden="true" />
                  <p className="text-xs font-black">Synchronisation des alertes…</p>
                </div>
              )}

              {status === 'error' && (
                <div className="rounded-[22px] border border-amber-200 bg-amber-500/5 p-4 flex gap-3 items-start">
                  <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-black text-amber-700">Notifications indisponibles</p>
                    <p className="text-[11px] font-bold text-amber-700/80 mt-1 break-words">{error}</p>
                    <button type="button" onClick={() => void load()} className="mt-3 min-h-12 px-4 rounded-xl bg-amber-100 text-amber-800 text-xs font-black active:scale-95 transition-transform">Réessayer</button>
                  </div>
                </div>
              )}

              {status !== 'loading' && status !== 'error' && alerts.length === 0 && (
                <div className="min-h-40 rounded-[22px] border border-border-main bg-white/60 flex flex-col items-center justify-center gap-3 text-center px-6">
                  <BellOff size={24} className="text-emerald-500" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-black text-text-main">Rien à traiter</p>
                    <p className="text-[11px] font-bold text-text-muted mt-1">Les nouvelles alertes du cabinet apparaîtront ici.</p>
                  </div>
                </div>
              )}

              {alerts.map(alert => (
                <article key={alert.id} className={`rounded-[22px] border p-4 shadow-sm ${priorityTone(alert.priority)}`}>
                  <div className="flex items-start gap-3">
                    <div className={`h-10 w-10 shrink-0 rounded-2xl flex items-center justify-center ${Number(alert.priority) === 1 ? 'bg-rose-100 text-rose-600' : 'bg-primary/10 text-primary'}`}>
                      {Number(alert.priority) === 1 ? <AlertTriangle size={17} aria-hidden="true" /> : <Bell size={17} aria-hidden="true" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-black text-text-main leading-tight">{alert.title}</h3>
                      {alert.patient_name && <p className="text-[10px] font-black text-primary mt-1">{alert.patient_name}</p>}
                      <p className="text-[11px] font-bold text-text-muted mt-2 leading-relaxed">{alert.message}</p>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      disabled={mutatingId === alert.id}
                      onClick={() => void mutate(alert.id, 'read')}
                      className="min-h-12 rounded-xl bg-primary text-white text-xs font-black flex items-center justify-center gap-2 disabled:opacity-50 active:scale-[0.98] transition-transform"
                    >
                      <Check size={15} aria-hidden="true" /> Lu
                    </button>
                    <button
                      type="button"
                      disabled={mutatingId === alert.id}
                      onClick={() => void mutate(alert.id, 'snooze')}
                      className="min-h-12 rounded-xl border border-border-main bg-white/75 text-text-main text-xs font-black flex items-center justify-center gap-2 disabled:opacity-50 active:scale-[0.98] transition-transform"
                    >
                      <Clock3 size={15} aria-hidden="true" /> + 24 h
                    </button>
                  </div>
                </article>
              ))}
            </div>

            <p className="px-5 pb-5 text-[10px] font-bold text-text-muted text-center">
              Les détails restent dans Digital Crown après authentification.
            </p>
          </section>
        </>
      )}
    </>
  );
}
