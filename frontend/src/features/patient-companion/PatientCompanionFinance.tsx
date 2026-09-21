import { useEffect, useState } from 'react';
import { Banknote, Download, FileText, RefreshCw, WalletCards } from 'lucide-react';

import { API_BASE } from '../../services/api';
import type { PatientPairing } from './PatientCompanionStorage';

type FinancePayload = {
  summary: {
    billed: number;
    collected: number;
    remaining_due: number;
  };
  payments: Array<{
    id: number;
    amount: number;
    method: string;
    paid_at: string;
    source: string;
  }>;
  schedules: Array<{
    id: number;
    title: string;
    total_amount: number;
    items: Array<{
      id: number;
      label: string;
      amount: number;
      due_date: string;
      paid_date: string | null;
      status: string;
    }>;
  }>;
  invoices: Array<{
    share_id: string;
    document_id: number;
    title: string;
    amount: number;
    issued_at: string | null;
    download_path: string;
  }>;
  online_payment: {
    available: boolean;
  };
};

const money = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'MAD',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const dateLabel = (raw?: string | null) => {
  if (!raw) return 'Date non renseignée';
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return 'Date non renseignée';
  return parsed.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

const methodLabel = (method: string) => {
  const labels: Record<string, string> = {
    ESPECES: 'Espèces',
    CARTE: 'Carte',
    VIREMENT: 'Virement',
    CHEQUE: 'Chèque',
  };
  return labels[method] || method;
};

const statusLabel = (status: string) => {
  const labels: Record<string, string> = {
    EN_ATTENTE: 'À venir',
    PAYE: 'Payée',
    PARTIEL: 'Partielle',
  };
  return labels[status] || status;
};

export const PatientCompanionFinance = ({
  pairing,
  enabled,
}: {
  pairing: PatientPairing;
  enabled: boolean;
}) => {
  const [data, setData] = useState<FinancePayload | null>(null);
  const [state, setState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [downloadId, setDownloadId] = useState<string | null>(null);

  const load = async () => {
    if (!enabled) {
      setData(null);
      setState('idle');
      return;
    }
    setState('loading');
    setData(null);
    try {
      const accessId = encodeURIComponent(pairing.context.access_id);
      const response = await fetch(
        `${API_BASE}/api/patient-companion/contexts/${accessId}/finance`,
        {
          headers: { Authorization: `Bearer ${pairing.accessToken}` },
          cache: 'no-store',
        },
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || 'Données financières indisponibles.');
      }
      setData(payload as FinancePayload);
      setState('ready');
    } catch {
      setData(null);
      setState('error');
    }
  };

  useEffect(() => {
    void load();
    // Finance is intentionally live-only: never reuse a stale cached amount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pairing.context.access_id, pairing.accessToken, enabled]);

  const downloadInvoice = async (invoice: FinancePayload['invoices'][number]) => {
    if (!enabled || downloadId) return;
    setDownloadId(invoice.share_id);
    try {
      const response = await fetch(`${API_BASE}${invoice.download_path}`, {
        headers: { Authorization: `Bearer ${pairing.accessToken}` },
        cache: 'no-store',
      });
      if (!response.ok) throw new Error('download failed');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${invoice.title || 'note-honoraires'}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } finally {
      setDownloadId(null);
    }
  };

  return (
    <section
      data-pc06-finance
      className="rounded-[28px] border border-border-main bg-card-bg p-5 shadow-sm"
      aria-labelledby="pc06-finance-title"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <WalletCards size={20} aria-hidden="true" />
            <h2 id="pc06-finance-title" className="text-lg font-black">Mes finances</h2>
          </div>
          <p className="mt-1 text-xs font-bold text-text-muted">Données du cabinet · actualisées à la demande</p>
        </div>
        <span className="shrink-0 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-black text-emerald-800">
          Source cabinet
        </span>
      </div>

      {!enabled && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs font-bold text-amber-900">
          Reconnexion au cabinet requise pour actualiser les données financières.
        </div>
      )}

      {enabled && state === 'loading' && (
        <div role="status" aria-live="polite" className="mt-4 rounded-2xl bg-background p-4 text-sm font-bold text-text-muted">
          Actualisation des données financières…
        </div>
      )}

      {enabled && state === 'error' && (
        <div role="alert" className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-3">
          <p className="text-xs font-bold text-rose-800">Impossible d’actualiser les données financières.</p>
          <button
            type="button"
            onClick={() => void load()}
            className="mt-3 min-h-[44px] w-full rounded-xl border border-rose-200 bg-white px-3 text-xs font-black text-rose-800"
          >
            <RefreshCw size={15} className="mr-2 inline" aria-hidden="true" />
            Réessayer
          </button>
        </div>
      )}

      {enabled && state === 'ready' && data && (
        <>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="min-w-0 rounded-2xl bg-background p-3">
              <p className="text-[9px] font-black uppercase tracking-wide text-text-muted">Facturé</p>
              <p className="mt-1 whitespace-nowrap text-[clamp(10px,3.2vw,14px)] font-black tracking-tight tabular-nums">{money.format(data.summary.billed)}</p>
            </div>
            <div className="min-w-0 rounded-2xl bg-background p-3">
              <p className="text-[9px] font-black uppercase tracking-wide text-text-muted">Encaissé</p>
              <p className="mt-1 whitespace-nowrap text-[clamp(10px,3.2vw,14px)] font-black tracking-tight tabular-nums">{money.format(data.summary.collected)}</p>
            </div>
            <div className="min-w-0 rounded-2xl bg-primary/5 p-3">
              <p className="text-[9px] font-black uppercase tracking-wide text-primary">Reste dû</p>
              <p className="mt-1 whitespace-nowrap text-[clamp(10px,3.2vw,14px)] font-black tracking-tight tabular-nums text-primary">{money.format(data.summary.remaining_due)}</p>
            </div>
          </div>

          {!data.online_payment.available && (
            <div className="mt-3 rounded-2xl border border-border-main bg-background px-3 py-2.5 text-[11px] font-bold text-text-muted">
              Paiement en ligne non activé par le cabinet.
            </div>
          )}

          <div className="mt-5">
            <div className="flex items-center gap-2">
              <Banknote size={17} aria-hidden="true" />
              <h3 className="text-sm font-black">Échéanciers</h3>
            </div>
            {data.schedules.length === 0 ? (
              <p className="mt-2 text-xs font-bold text-text-muted">Aucun échéancier actif.</p>
            ) : (
              <div className="mt-2 grid gap-2">
                {data.schedules.map(plan => (
                  <div key={plan.id} className="rounded-2xl border border-border-main p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-xs font-black">{plan.title}</p>
                      <p className="text-xs font-black">{money.format(plan.total_amount)}</p>
                    </div>
                    <div className="mt-2 grid gap-1.5">
                      {plan.items.map(item => (
                        <div key={item.id} className="flex items-start justify-between gap-3 rounded-xl bg-background px-2.5 py-2">
                          <div className="min-w-0">
                            <p className="truncate text-[11px] font-black">{item.label}</p>
                            <p className="text-[10px] font-bold text-text-muted">{dateLabel(item.due_date)} · {statusLabel(item.status)}</p>
                          </div>
                          <p className="shrink-0 text-[11px] font-black">{money.format(item.amount)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-5">
            <div className="flex items-center gap-2">
              <Banknote size={17} aria-hidden="true" />
              <h3 className="text-sm font-black">Paiements récents</h3>
            </div>
            {data.payments.length === 0 ? (
              <p className="mt-2 text-xs font-bold text-text-muted">Aucun paiement enregistré.</p>
            ) : (
              <div className="mt-2 grid gap-2">
                {data.payments.slice(0, 6).map(payment => (
                  <div key={payment.id} className="flex items-center justify-between gap-3 rounded-2xl bg-background px-3 py-2.5">
                    <div>
                      <p className="text-[11px] font-black">{methodLabel(payment.method)}</p>
                      <p className="text-[10px] font-bold text-text-muted">{dateLabel(payment.paid_at)}</p>
                    </div>
                    <p className="text-xs font-black">{money.format(payment.amount)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-5">
            <div className="flex items-center gap-2">
              <FileText size={17} aria-hidden="true" />
              <h3 className="text-sm font-black">Notes d’honoraires</h3>
            </div>
            {data.invoices.length === 0 ? (
              <p className="mt-2 text-xs font-bold text-text-muted">Aucune note d’honoraires partagée.</p>
            ) : (
              <div className="mt-2 grid gap-2">
                {data.invoices.map(invoice => (
                  <div key={invoice.share_id} className="rounded-2xl border border-border-main p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-xs font-black">{invoice.title}</p>
                        <p className="mt-1 text-[10px] font-bold text-text-muted">{dateLabel(invoice.issued_at)}</p>
                      </div>
                      <p className="shrink-0 text-xs font-black">{money.format(invoice.amount)}</p>
                    </div>
                    <button
                      type="button"
                      disabled={downloadId !== null}
                      onClick={() => void downloadInvoice(invoice)}
                      className="mt-3 min-h-[44px] w-full rounded-xl border border-border-main bg-background px-3 text-xs font-black disabled:opacity-60"
                    >
                      <Download size={15} className="mr-2 inline" aria-hidden="true" />
                      {downloadId === invoice.share_id ? 'Préparation…' : 'Télécharger'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
};
