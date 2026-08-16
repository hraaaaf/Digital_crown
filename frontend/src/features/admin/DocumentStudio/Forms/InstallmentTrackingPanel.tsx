import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Banknote, CheckCircle2, Clock3, MessageCircle, RefreshCw, X } from 'lucide-react';
import { toast } from 'react-hot-toast';

import { api } from '../../../../services/api';
import {
  summarizeInstallmentPlan,
  type TrackedInstallment,
  type TrackedInstallmentPlan,
} from '../InstallmentTrackingPolicy';

interface InstallmentTrackingPanelProps {
  patientId: string;
  patientPhone: string;
}

type PaymentMethod = 'ESPECES' | 'CHEQUE' | 'TPE' | 'VIREMENT';

interface PendingPayment {
  installment: TrackedInstallment;
  planTitle: string;
}

const PAYMENT_METHODS: Array<{ value: PaymentMethod; label: string }> = [
  { value: 'ESPECES', label: 'Espèces' },
  { value: 'TPE', label: 'TPE / Carte' },
  { value: 'CHEQUE', label: 'Chèque' },
  { value: 'VIREMENT', label: 'Virement' },
];

function formatMoney(value: number): string {
  return `${Number(value || 0).toFixed(2)} MAD`;
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value.slice(0, 10) : date.toLocaleDateString('fr-FR');
}

function normalizeWhatsappPhone(phone: string): string {
  let normalized = String(phone || '').replace(/\s|-/g, '');
  if (normalized.startsWith('+')) normalized = normalized.slice(1);
  else if (normalized.startsWith('00')) normalized = normalized.slice(2);
  else if (normalized.startsWith('0')) normalized = `212${normalized.slice(1)}`;
  return normalized;
}

export const InstallmentTrackingPanel: React.FC<InstallmentTrackingPanelProps> = ({ patientId, patientPhone }) => {
  const [plans, setPlans] = useState<TrackedInstallmentPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [pendingPayment, setPendingPayment] = useState<PendingPayment | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('ESPECES');
  const [savingPayment, setSavingPayment] = useState(false);

  const loadPlans = useCallback(async () => {
    if (!patientId || patientId === '0') {
      setPlans([]);
      return;
    }
    setLoading(true);
    try {
      const response = await api.get(`/installments/patient/${patientId}`);
      const nextPlans = Array.isArray(response.data) ? response.data : [];
      setPlans([...nextPlans].sort((left, right) => Number(right.id) - Number(left.id)));
    } catch (error) {
      console.error('P5: failed to load installment plans', error);
      toast.error('Impossible de charger le suivi des paiements.');
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    loadPlans();
  }, [loadPlans]);

  const todayIso = useMemo(() => new Date().toISOString().split('T')[0], []);

  const confirmPayment = async () => {
    if (!pendingPayment || savingPayment) return;
    setSavingPayment(true);
    try {
      await api.put(`/installments/${pendingPayment.installment.id}`, {
        status: 'PAYE',
        payment_method: paymentMethod,
      });
      toast.success('Règlement enregistré.');
      setPendingPayment(null);
      await loadPlans();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : "Le règlement n'a pas été enregistré.");
    } finally {
      setSavingPayment(false);
    }
  };

  const sendReminder = (item: TrackedInstallment) => {
    const message = `Bonjour, ceci est un rappel pour votre échéance « ${item.label} » de ${formatMoney(item.amount)}, prévue le ${formatDate(item.due_date)}. Merci.`;
    const phone = normalizeWhatsappPhone(patientPhone);
    const url = phone
      ? `https://wa.me/${phone}?text=${encodeURIComponent(message)}`
      : `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <section className="mb-8 rounded-2xl border border-slate-200 bg-white shadow-sm" aria-labelledby="installment-tracking-title">
      <div className="flex items-center justify-between gap-4 border-b border-slate-100 px-5 py-4">
        <div>
          <h3 id="installment-tracking-title" className="text-base font-bold text-slate-900">Suivi des paiements</h3>
          <p className="mt-0.5 text-xs text-slate-500">Statuts issus de la comptabilité backend. Aucun règlement n'est déduit localement.</p>
        </div>
        <button
          type="button"
          onClick={loadPlans}
          disabled={loading}
          aria-label="Actualiser le suivi des paiements"
          className="rounded-xl border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="space-y-4 p-5">
        {loading && plans.length === 0 && (
          <p className="text-sm text-slate-500">Chargement des plans…</p>
        )}

        {!loading && plans.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-200 p-5 text-center text-sm text-slate-500">
            Aucun plan de paiement enregistré pour ce patient.
          </div>
        )}

        {plans.map(plan => {
          const summary = summarizeInstallmentPlan(plan, todayIso);
          return (
            <article key={plan.id} className="overflow-hidden rounded-2xl border border-slate-200" aria-labelledby={`plan-${plan.id}-title`}>
              <div className="bg-slate-50 px-4 py-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <h4 id={`plan-${plan.id}-title`} className="font-bold text-slate-900">{plan.title}</h4>
                    <p className="text-xs text-slate-500">Total contractuel : {formatMoney(plan.total_amount)}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <div className="rounded-xl bg-white px-3 py-2 text-xs">
                      <span className="block text-slate-400">Payé</span>
                      <strong className="text-emerald-600">{formatMoney(summary.paidTotal)}</strong>
                    </div>
                    <div className="rounded-xl bg-white px-3 py-2 text-xs">
                      <span className="block text-slate-400">Restant</span>
                      <strong className="text-slate-900">{formatMoney(summary.remainingTotal)}</strong>
                    </div>
                    <div className="rounded-xl bg-white px-3 py-2 text-xs">
                      <span className="block text-slate-400">Prochaine</span>
                      <strong className="text-slate-900">{formatDate(summary.nextPending?.due_date)}</strong>
                    </div>
                    <div className="rounded-xl bg-white px-3 py-2 text-xs">
                      <span className="block text-slate-400">En retard</span>
                      <strong className={summary.overdueCount > 0 ? 'text-amber-600' : 'text-slate-900'}>{summary.overdueCount}</strong>
                    </div>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-sm">
                  <thead className="border-b border-slate-100 bg-white text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Statut</th>
                      <th className="px-4 py-3">Échéance</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3 text-right">Montant</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {plan.installments.map(item => {
                      const paid = String(item.status || '').toUpperCase() === 'PAYE';
                      const overdue = !paid && item.due_date?.slice(0, 10) < todayIso;
                      return (
                        <tr key={item.id} className={paid ? 'bg-emerald-50/40' : ''}>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
                              paid ? 'bg-emerald-100 text-emerald-700' : overdue ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
                            }`}>
                              {paid ? <CheckCircle2 className="h-3.5 w-3.5" /> : overdue ? <AlertTriangle className="h-3.5 w-3.5" /> : <Clock3 className="h-3.5 w-3.5" />}
                              {paid ? 'Réglé' : overdue ? 'En retard' : 'En attente'}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-medium text-slate-700">{item.label}</td>
                          <td className="px-4 py-3 text-slate-600">{formatDate(item.due_date)}</td>
                          <td className="px-4 py-3 text-right font-bold text-slate-900">{formatMoney(item.amount)}</td>
                          <td className="px-4 py-3">
                            <div className="flex justify-end gap-2">
                              {!paid && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => sendReminder(item)}
                                    aria-label={`Envoyer un rappel pour ${item.label}`}
                                    className="rounded-lg border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50"
                                  >
                                    <MessageCircle className="h-4 w-4" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setPaymentMethod('ESPECES');
                                      setPendingPayment({ installment: item, planTitle: plan.title });
                                    }}
                                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white transition hover:bg-emerald-700"
                                  >
                                    <Banknote className="h-4 w-4" /> Enregistrer règlement
                                  </button>
                                </>
                              )}
                              {paid && <span className="text-xs text-slate-400">Payé le {formatDate(item.paid_date)}</span>}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </article>
          );
        })}
      </div>

      {pendingPayment && (
        <div className="fixed inset-0 z-[20000] flex items-center justify-center bg-slate-950/50 p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="installment-payment-title"
            className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h4 id="installment-payment-title" className="font-black text-slate-900">Enregistrer un règlement</h4>
                <p className="mt-1 text-sm text-slate-500">{pendingPayment.planTitle} · {pendingPayment.installment.label}</p>
              </div>
              <button
                type="button"
                onClick={() => setPendingPayment(null)}
                aria-label="Annuler le règlement"
                className="rounded-full p-2 text-slate-400 hover:bg-slate-100"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="my-5 rounded-2xl bg-emerald-50 p-4 text-center">
              <span className="block text-xs uppercase tracking-wider text-emerald-600">Montant à enregistrer</span>
              <strong className="text-2xl text-emerald-700">{formatMoney(pendingPayment.installment.amount)}</strong>
            </div>

            <label htmlFor="installment-payment-method" className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
              Mode de règlement
            </label>
            <select
              id="installment-payment-method"
              value={paymentMethod}
              onChange={event => setPaymentMethod(event.target.value as PaymentMethod)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm font-semibold text-slate-700"
            >
              {PAYMENT_METHODS.map(method => (
                <option key={method.value} value={method.value}>{method.label}</option>
              ))}
            </select>

            <p className="mt-4 text-xs leading-relaxed text-slate-500">
              Cette action crée un paiement comptable réel et marque définitivement l'échéance comme réglée. Une contrepassation dédiée est requise pour l'annuler.
            </p>

            <div className="mt-6 flex gap-3">
              <button
                type="button"
                onClick={() => setPendingPayment(null)}
                disabled={savingPayment}
                className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-600 disabled:opacity-50"
              >Annuler</button>
              <button
                type="button"
                onClick={confirmPayment}
                disabled={savingPayment}
                className="flex-1 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
              >{savingPayment ? 'Enregistrement…' : 'Confirmer le règlement'}</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
