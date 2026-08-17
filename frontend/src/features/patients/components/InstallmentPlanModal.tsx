import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, Trash2, Loader2, CalendarDays } from 'lucide-react';
import axios from 'axios';
import { api } from '../../../services/api';
import toast from 'react-hot-toast';
import type { ActeBillingItem } from './PayActeModal';

interface InstallmentRow {
  label: string;
  amount: string;
  due_date: string;
}

interface InstallmentPlanModalProps {
  acte: ActeBillingItem;
  patientId: number;
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const defaultRow = (index: number, due_date: string): InstallmentRow => ({
  label: `Versement ${index + 1}`,
  amount: '',
  due_date,
});

const nextMonth = (fromDate: string, addMonths: number): string => {
  const d = new Date(fromDate);
  d.setMonth(d.getMonth() + addMonths);
  return d.toISOString().slice(0, 10);
};

const money = (value: number): number => Math.round((value + Number.EPSILON) * 100) / 100;

export const InstallmentPlanModal = ({ acte, patientId, isOpen, onClose, onCreated }: InstallmentPlanModalProps) => {
  const today = new Date().toISOString().slice(0, 10);
  const [title, setTitle] = useState(`Plan de paiement — ${acte.libelle}`);
  const [rows, setRows] = useState<InstallmentRow[]>([
    defaultRow(0, today),
    defaultRow(1, nextMonth(today, 1)),
  ]);
  const [submitting, setSubmitting] = useState(false);

  const normalizedAmounts = rows.map((row) => money(parseFloat(row.amount) || 0));
  const totalEntered = money(normalizedAmounts.reduce((sum, amount) => sum + amount, 0));
  const remainingDue = money(acte.remaining_due);
  const gap = money(remainingDue - totalEntered);
  const coverageExact = gap === 0;
  const rowsValid = rows.every((row) => (
    row.label.trim().length > 0
    && row.amount !== ''
    && money(parseFloat(row.amount)) > 0
    && Boolean(row.due_date)
  ));

  const addRow = () => {
    const lastDate = rows[rows.length - 1]?.due_date || today;
    setRows(prev => [...prev, defaultRow(prev.length, nextMonth(lastDate, 1))]);
  };

  const removeRow = (idx: number) => {
    if (rows.length <= 1) return;
    setRows(prev => prev.filter((_, i) => i !== idx));
  };

  const updateRow = (idx: number, field: keyof InstallmentRow, value: string) => {
    setRows(prev => prev.map((r, i) => i === idx ? { ...r, [field]: value } : r));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!rowsValid) {
      toast.error('Renseignez chaque versement, son montant et sa date');
      return;
    }
    if (!coverageExact) {
      toast.error('Le plan doit couvrir exactement le reste dû de l’acte');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/installments/', {
        patient_id: patientId,
        acte_id: acte.id,
        title: title.trim(),
        total_amount: remainingDue,
        installments: rows.map((row, index) => ({
          label: row.label.trim(),
          amount: normalizedAmounts[index],
          due_date: row.due_date,
        })),
      });
      toast.success('Plan d’échéances créé');
      onCreated();
    } catch (error: unknown) {
      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null;
      toast.error(typeof detail === 'string' ? detail : 'Erreur lors de la création du plan');
    } finally {
      setSubmitting(false);
    }
  };

  const modal = (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm"
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="installment-plan-title"
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="bg-white rounded-3xl shadow-2xl w-full max-w-lg relative z-10 overflow-hidden max-h-[calc(100dvh-2rem)] flex flex-col my-auto"
          >
            <div className="p-5 sm:p-6 border-b border-slate-100 flex justify-between items-start bg-slate-50/50 shrink-0">
              <div className="min-w-0 pr-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Plan d'échéances</p>
                <h2 id="installment-plan-title" className="text-base font-black text-slate-800 tracking-tight truncate">{acte.libelle}</h2>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Reste dû : <span className="font-black text-red-600">{remainingDue.toLocaleString('fr-MA')} MAD</span>
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Fermer le plan d’échéances"
                className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors mt-0.5 shrink-0"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
              <div className="p-5 sm:p-6 space-y-5 overflow-y-auto overscroll-contain flex-1 min-h-0">
                <div>
                  <label className="block text-[11px] font-black uppercase tracking-widest text-slate-500 mb-2">Titre du plan</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-primary"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3 gap-3">
                    <label className="text-[11px] font-black uppercase tracking-widest text-slate-500">Versements</label>
                    <button
                      type="button"
                      onClick={addRow}
                      className="flex items-center gap-1.5 text-xs font-black text-primary hover:text-primary/80 transition-colors shrink-0"
                    >
                      <Plus size={14} /> Ajouter
                    </button>
                  </div>

                  <div className="space-y-3">
                    {rows.map((row, idx) => (
                      <div key={idx} className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_7rem_10rem_auto] gap-2 sm:items-center rounded-2xl sm:rounded-none border border-slate-100 sm:border-0 p-3 sm:p-0 bg-slate-50/40 sm:bg-transparent">
                        <input
                          type="text"
                          required
                          value={row.label}
                          onChange={e => updateRow(idx, 'label', e.target.value)}
                          placeholder={`Versement ${idx + 1}`}
                          aria-label={`Libellé du versement ${idx + 1}`}
                          className="w-full min-w-0 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-primary"
                        />
                        <div className="relative min-w-0">
                          <input
                            type="number"
                            step="0.01"
                            min="0.01"
                            required
                            value={row.amount}
                            onChange={e => updateRow(idx, 'amount', e.target.value)}
                            placeholder="Montant"
                            aria-label={`Montant du versement ${idx + 1}`}
                            className="w-full min-w-0 px-3 py-2 pr-8 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-primary"
                          />
                          <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 font-bold">MAD</span>
                        </div>
                        <div className="relative min-w-0">
                          <CalendarDays size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                          <input
                            type="date"
                            required
                            value={row.due_date}
                            onChange={e => updateRow(idx, 'due_date', e.target.value)}
                            aria-label={`Date du versement ${idx + 1}`}
                            className="w-full min-w-0 pl-7 pr-2 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-primary"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => removeRow(idx)}
                          disabled={rows.length <= 1}
                          aria-label={`Supprimer le versement ${idx + 1}`}
                          className="justify-self-end sm:justify-self-auto p-2 text-slate-300 hover:text-red-400 transition-colors disabled:opacity-30 rounded-lg"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-50 rounded-2xl p-4 space-y-2">
                  <div className="flex justify-between gap-4 text-xs font-bold text-slate-600">
                    <span>Total des versements</span>
                    <span className="whitespace-nowrap">{totalEntered.toLocaleString('fr-MA')} MAD</span>
                  </div>
                  <div className="flex justify-between gap-4 text-xs font-bold text-slate-600">
                    <span>Reste dû sur l'acte</span>
                    <span className="whitespace-nowrap">{remainingDue.toLocaleString('fr-MA')} MAD</span>
                  </div>
                  <div className={`flex justify-between gap-4 text-xs font-black pt-1 border-t border-slate-200 ${gap > 0 ? 'text-amber-600' : gap < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                    <span>{gap > 0 ? 'Non couvert' : gap < 0 ? 'Dépassement' : 'Couverture exacte'}</span>
                    <span className="text-right">{gap > 0 ? `${gap.toLocaleString('fr-MA')} MAD restant` : gap < 0 ? `+${Math.abs(gap).toLocaleString('fr-MA')} MAD` : '✓'}</span>
                  </div>
                </div>
              </div>

              <div className="p-5 sm:p-6 border-t border-slate-100 shrink-0 bg-white">
                <button
                  type="submit"
                  disabled={submitting || !rowsValid || !coverageExact || title.trim().length === 0}
                  className="w-full flex items-center justify-center gap-2 py-3.5 sm:py-4 rounded-2xl text-white font-black uppercase tracking-widest text-sm transition-all disabled:opacity-50 shadow-lg"
                  style={{ backgroundColor: 'var(--primary)' }}
                >
                  {submitting ? <Loader2 size={18} className="animate-spin" /> : 'Créer le plan'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );

  return typeof document === 'undefined' ? null : createPortal(modal, document.body);
};
