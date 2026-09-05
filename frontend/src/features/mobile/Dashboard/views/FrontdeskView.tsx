import { useEffect, useMemo, useState } from 'react';
import { CalendarClock, Check, Clock3, MessageCircle, Phone, RefreshCw, X } from 'lucide-react';
import { api } from '../../../../services/api';

export interface PendingRequest {
  id: number;
  patient_name: string;
  phone?: string | null;
  datetime_start: string;
  duration_minutes: number;
  motif?: string | null;
  status: 'EN_ATTENTE_DEMANDE' | 'EN_ATTENTE_CONFIRM' | string;
  source?: string | null;
  expires_at?: string | null;
  created_at: string;
}

const formatDateTime = (value: string) => {
  const date = new Date(value);
  return {
    date: date.toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short' }),
    time: date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
  };
};

export function FrontdeskView({ previewData }: { previewData?: PendingRequest[] }) {
  const [requests, setRequests] = useState<PendingRequest[]>(previewData ?? []);
  const [loading, setLoading] = useState(!previewData);
  const [mutatingId, setMutatingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<PendingRequest | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const previewMode = Boolean(previewData);

  const load = async () => {
    if (previewData) {
      setRequests(previewData);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<PendingRequest[]>('/appointments/pending');
      setRequests(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Impossible de charger les demandes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [previewData]);

  const mutate = async (request: PendingRequest, action: 'confirm' | 'reject' | 'request-confirmation') => {
    if (previewMode) return;
    setMutatingId(request.id);
    setError(null);
    setMessage(null);
    try {
      const response = await api.post(`/appointments/${request.id}/${action}`);
      if (action === 'request-confirmation') {
        const template = response.data?.message_template;
        setMessage(template ? 'Message de confirmation préparé. Aucun envoi automatique n’a été effectué.' : 'Confirmation demandée.');
      } else if (action === 'confirm') {
        setMessage('Rendez-vous confirmé.');
      } else {
        setMessage('Demande refusée.');
      }
      setRejecting(null);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Action impossible.');
    } finally {
      setMutatingId(null);
    }
  };

  const sorted = useMemo(
    () => [...requests].sort((a, b) => new Date(a.datetime_start).getTime() - new Date(b.datetime_start).getTime()),
    [requests],
  );

  return (
    <section className="pb-6" data-mobile-frontdesk>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Demandes RDV</p>
          <h1 className="mt-1 text-[24px] font-black text-text-main">Frontdesk</h1>
          <p className="mt-1 text-[11px] font-bold text-text-muted">{sorted.length} demande{sorted.length > 1 ? 's' : ''} en attente</p>
        </div>
        <button
          type="button"
          aria-label="Actualiser Frontdesk"
          onClick={() => void load()}
          disabled={loading || previewMode}
          className="grid min-h-11 min-w-11 place-items-center rounded-full border border-glass-border bg-card text-text-muted disabled:opacity-50"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {message && <div className="mb-3 rounded-[18px] border border-primary/20 bg-primary/5 px-4 py-3 text-[11px] font-bold text-text-main">{message}</div>}
      {error && <div className="mb-3 rounded-[18px] border border-rose-500/20 bg-rose-500/5 px-4 py-3 text-[11px] font-bold text-rose-600">{error}</div>}

      {!loading && sorted.length === 0 && (
        <div className="rounded-[24px] border border-glass-border bg-card px-5 py-8 text-center shadow-sm">
          <CalendarClock size={28} className="mx-auto text-primary" />
          <h2 className="mt-3 text-[16px] font-black text-text-main">Aucune demande en attente</h2>
          <p className="mt-1 text-[11px] font-bold text-text-muted">Le Frontdesk est à jour.</p>
        </div>
      )}

      <div className="grid gap-3">
        {sorted.map(request => {
          const { date, time } = formatDateTime(request.datetime_start);
          const busy = mutatingId === request.id;
          const phone = request.phone?.trim();
          const whatsapp = phone ? `https://wa.me/${phone.replace(/\D/g, '')}` : null;
          return (
            <article key={request.id} className="rounded-[24px] border border-glass-border bg-card p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="truncate text-[16px] font-black text-text-main">{request.patient_name}</h2>
                  <p className="mt-1 text-[11px] font-bold text-text-muted">{date} · {time} · {request.duration_minutes} min</p>
                  {request.motif && <p className="mt-1 line-clamp-2 text-[11px] font-semibold text-text-muted">{request.motif}</p>}
                </div>
                <span className="shrink-0 rounded-full border border-primary/20 bg-primary/5 px-2.5 py-1 text-[9px] font-black text-primary">
                  {request.status === 'EN_ATTENTE_CONFIRM' ? 'À confirmer' : 'Nouvelle'}
                </span>
              </div>

              {request.expires_at && <div className="mt-3 flex items-center gap-1.5 text-[10px] font-bold text-text-muted"><Clock3 size={13} />Expire à {new Date(request.expires_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</div>}

              <div className="mt-4 grid grid-cols-2 gap-2">
                <button type="button" onClick={() => void mutate(request, 'confirm')} disabled={busy || previewMode} className="flex min-h-11 items-center justify-center gap-2 rounded-[16px] bg-primary px-3 text-[11px] font-black text-white disabled:opacity-50"><Check size={16} /> Confirmer</button>
                <button type="button" onClick={() => setRejecting(request)} disabled={busy || previewMode} className="flex min-h-11 items-center justify-center gap-2 rounded-[16px] border border-rose-500/20 bg-rose-500/5 px-3 text-[11px] font-black text-rose-600 disabled:opacity-50"><X size={16} /> Refuser</button>
              </div>

              {request.status === 'EN_ATTENTE_DEMANDE' && <button type="button" onClick={() => void mutate(request, 'request-confirmation')} disabled={busy || previewMode} className="mt-2 flex min-h-11 w-full items-center justify-center rounded-[16px] border border-glass-border bg-background px-3 text-[11px] font-black text-text-main disabled:opacity-50">Demander confirmation</button>}

              <div className="mt-2 grid grid-cols-2 gap-2">
                <a href={phone && !previewMode ? `tel:${phone}` : undefined} aria-disabled={!phone || previewMode} className={`flex min-h-11 items-center justify-center gap-2 rounded-[16px] border border-glass-border px-3 text-[11px] font-black ${phone && !previewMode ? 'bg-background text-text-main' : 'pointer-events-none opacity-40'}`}><Phone size={15} /> Appeler</a>
                <a href={whatsapp && !previewMode ? whatsapp : undefined} target={whatsapp && !previewMode ? '_blank' : undefined} rel={whatsapp && !previewMode ? 'noreferrer' : undefined} aria-disabled={!whatsapp || previewMode} className={`flex min-h-11 items-center justify-center gap-2 rounded-[16px] border border-glass-border px-3 text-[11px] font-black ${whatsapp && !previewMode ? 'bg-background text-text-main' : 'pointer-events-none opacity-40'}`}><MessageCircle size={15} /> WhatsApp</a>
              </div>
            </article>
          );
        })}
      </div>

      {rejecting && !previewMode && (
        <div className="fixed inset-0 z-[80] flex items-end justify-center bg-slate-950/25 p-3 backdrop-blur-[1px]">
          <section role="dialog" aria-modal="true" aria-label="Confirmer le refus" className="w-full max-w-[720px] rounded-[28px] border border-glass-border bg-card p-5 shadow-elite-hover">
            <h2 className="text-[17px] font-black text-text-main">Refuser cette demande ?</h2>
            <p className="mt-2 text-[11px] font-bold text-text-muted">{rejecting.patient_name} · cette action mettra la demande au statut refusé.</p>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button type="button" onClick={() => setRejecting(null)} className="min-h-11 rounded-[16px] border border-glass-border bg-background text-[11px] font-black text-text-main">Annuler</button>
              <button type="button" onClick={() => void mutate(rejecting, 'reject')} className="min-h-11 rounded-[16px] bg-rose-600 text-[11px] font-black text-white">Refuser</button>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
