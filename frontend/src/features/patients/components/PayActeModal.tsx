import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CreditCard, Banknote, Landmark, FileSignature, Loader2, CheckCircle2 } from 'lucide-react';
import { paymentApi } from '../../../services/paymentApi';
import toast from 'react-hot-toast';
import { cn } from '../../../utils/cn';

export interface ActeBillingItem {
  id: number;
  libelle: string;
  montant: number;
  total_paid: number;
  remaining_due: number;
  statut_paiement: string;
  date_debut: string | null;
  type_acte: string | null;
}

interface PayActeModalProps {
  acte: ActeBillingItem;
  patientId: number;
  isOpen: boolean;
  onClose: () => void;
  onPaid: () => void;
}

const METHODS = [
  { id: 'ESPECES',  label: 'Espèces',  icon: <Banknote size={18} /> },
  { id: 'CARTE',    label: 'Carte',    icon: <CreditCard size={18} /> },
  { id: 'VIREMENT', label: 'Virement', icon: <Landmark size={18} /> },
  { id: 'CHEQUE',   label: 'Chèque',  icon: <FileSignature size={18} /> },
] as const;

export const PayActeModal = ({ acte, patientId, isOpen, onClose, onPaid }: PayActeModalProps) => {
  const [amount, setAmount] = useState(String(acte.remaining_due));
  const [method, setMethod] = useState<'ESPECES' | 'CARTE' | 'VIREMENT' | 'CHEQUE'>('ESPECES');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseFloat(amount);
    if (!parsed || parsed <= 0) return;
    setSubmitting(true);
    try {
      await paymentApi.recordPayment({
        patient_id: patientId,
        amount: parsed,
        payment_method: method,
        acte_id: acte.id,
        notes: notes || undefined,
      });
      toast.success('Paiement enregistré');
      onPaid();
    } catch {
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
          />
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="bg-white rounded-3xl shadow-2xl w-full max-w-md relative z-10 overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-start bg-slate-50/50">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Paiement acte</p>
                <h2 className="text-base font-black text-slate-800 tracking-tight">{acte.libelle}</h2>
              </div>
              <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors mt-0.5">
                <X size={18} />
              </button>
            </div>

            {/* Résumé financier de l'acte */}
            <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
              <div className="p-4 text-center">
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Total acte</p>
                <p className="text-lg font-black text-slate-700">{acte.montant.toLocaleString('fr-MA')}</p>
                <p className="text-[9px] text-slate-400 font-bold">MAD</p>
              </div>
              <div className="p-4 text-center">
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Déjà encaissé</p>
                <p className="text-lg font-black text-emerald-600">{acte.total_paid.toLocaleString('fr-MA')}</p>
                <p className="text-[9px] text-slate-400 font-bold">MAD</p>
              </div>
              <div className="p-4 text-center">
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Reste dû</p>
                <p className="text-lg font-black text-red-600">{acte.remaining_due.toLocaleString('fr-MA')}</p>
                <p className="text-[9px] text-slate-400 font-bold">MAD</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Montant */}
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-slate-500 mb-2">
                  Montant à encaisser (MAD)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max={acte.remaining_due}
                    required
                    value={amount}
                    onChange={e => setAmount(e.target.value)}
                    className="w-full text-3xl font-black text-slate-800 pl-4 pr-16 py-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                  />
                  <span className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm">MAD</span>
                </div>
                {parseFloat(amount) < acte.remaining_due && parseFloat(amount) > 0 && (
                  <p className="text-[10px] text-amber-500 font-bold mt-1.5">
                    Paiement partiel — reste {(acte.remaining_due - parseFloat(amount)).toLocaleString('fr-MA')} MAD
                  </p>
                )}
                {parseFloat(amount) >= acte.remaining_due && (
                  <p className="flex items-center gap-1 text-[10px] text-emerald-600 font-bold mt-1.5">
                    <CheckCircle2 size={12} /> Solde intégralement réglé
                  </p>
                )}
              </div>

              {/* Méthode */}
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-slate-500 mb-2">Méthode</label>
                <div className="grid grid-cols-2 gap-2">
                  {METHODS.map(m => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMethod(m.id)}
                      className={cn(
                        "flex items-center gap-2.5 p-3 rounded-xl border transition-all text-sm font-bold",
                        method === m.id
                          ? "bg-primary/5 border-primary text-primary shadow-sm"
                          : "bg-white border-slate-200 text-slate-500 hover:border-slate-300 hover:bg-slate-50"
                      )}
                    >
                      {m.icon} {m.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-slate-500 mb-2">Notes (optionnel)</label>
                <input
                  type="text"
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  placeholder="Ex: Acompte traitement…"
                  className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-medium outline-none focus:border-primary"
                />
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={submitting || !amount || parseFloat(amount) <= 0}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl text-white font-black uppercase tracking-widest text-sm transition-all disabled:opacity-50 shadow-lg"
                style={{ backgroundColor: 'var(--primary)' }}
              >
                {submitting ? <Loader2 size={18} className="animate-spin" /> : 'Encaisser'}
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
