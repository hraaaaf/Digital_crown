import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CreditCard, Banknote, Landmark, FileSignature, Loader2 } from 'lucide-react';
import { paymentApi } from '../../../services/paymentApi';
import toast from 'react-hot-toast';
import { cn } from '../../../utils/cn';
import { useAccountingStore } from '../../admin/store/useAccountingStore';
import { useEscapeKey } from '../../../hooks/useEscapeKey';

interface QuickPayModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: number;
}

export const QuickPayModal = ({ isOpen, onClose, patientId }: QuickPayModalProps) => {
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState<'ESPECES' | 'CARTE' | 'VIREMENT' | 'CHEQUE'>('ESPECES');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEscapeKey(isOpen, onClose);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) return;

    try {
      setIsSubmitting(true);
      await paymentApi.recordPayment({
        patient_id: patientId,
        amount: parseFloat(amount),
        payment_method: method,
        notes: notes || undefined
      });
      toast.success('Paiement enregistré avec succès');
      setAmount('');
      setNotes('');
      useAccountingStore.getState().setGroupSelectedTeeth([]);
      useAccountingStore.getState().setOdontogramMode('individual');
      onClose();
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement du paiement');
    } finally {
      setIsSubmitting(false);
    }
  };

  const methods = [
    { id: 'ESPECES', label: 'Espèces', icon: <Banknote size={20} /> },
    { id: 'CARTE', label: 'Carte', icon: <CreditCard size={20} /> },
    { id: 'VIREMENT', label: 'Virement', icon: <Landmark size={20} /> },
    { id: 'CHEQUE', label: 'Chèque', icon: <FileSignature size={20} /> }
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div role="dialog" aria-modal="true" aria-label="Saisir un Paiement" className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
          />

          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="bg-white rounded-3xl shadow-2xl w-full max-w-md relative z-10 overflow-hidden"
          >
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-xl font-black text-slate-800 tracking-tight uppercase">Saisir un Paiement</h2>
              <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors" aria-label="Fermer">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-slate-500 mb-2">Montant (MAD)</label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full text-3xl font-black text-slate-800 pl-4 pr-16 py-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all"
                    placeholder="0.00"
                    style={{ '--tw-ring-color': 'rgba(0,51,128,0.1)' } as React.CSSProperties}
                  />
                  <span className="absolute right-6 top-1/2 -translate-y-1/2 text-slate-400 font-bold">MAD</span>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-slate-500 mb-2">Méthode</label>
                <div className="grid grid-cols-2 gap-3">
                  {methods.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => setMethod(m.id as any)}
                      className={cn(
                        "flex items-center gap-3 p-4 rounded-2xl border transition-all",
                        method === m.id 
                          ? "bg-primary/5 border-primary text-primary shadow-sm" 
                          : "bg-white border-slate-200 text-slate-500 hover:border-slate-300 hover:bg-slate-50"
                      )}
                    >
                      {m.icon}
                      <span className="font-bold text-sm">{m.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-black uppercase tracking-widest text-slate-500 mb-2">Notes (Optionnel)</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Ex: Acompte traitement ortho..."
                  className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 outline-none focus:border-primary"
                />
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isSubmitting || !amount}
                  className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl text-white font-black uppercase tracking-widest text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-slate-900 hover:bg-primary shadow-lg"
                  style={!isSubmitting && amount ? { backgroundColor: 'var(--primary)' } : {}}
                >
                  {isSubmitting ? <Loader2 size={20} className="animate-spin" /> : 'Encaisser'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
