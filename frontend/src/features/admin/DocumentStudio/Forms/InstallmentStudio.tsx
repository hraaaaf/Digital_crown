import React, { useEffect, useState } from 'react';
import { DollarSign, FileText, Plus, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';

import { PriceBrain } from '../../../../components/odontogram/PriceBrain';
import { api } from '../../../../services/api';
import { buildExactInstallmentAllocation } from '../InstallmentAllocationPolicy';
import { InstallmentTrackingPanel } from './InstallmentTrackingPanel';

interface InstallmentStudioProps {
  patientId: string;
  onPayloadChange?: (payload: {
    patient_id: number;
    title: string;
    total_amount: number;
    items: Array<{ label: string; amount: number; due_date: string; paid: boolean }>;
  }) => void;
}

interface DraftInstallmentItem {
  id: string;
  label: string;
  amount: number;
  dueDate: string;
}

export const InstallmentStudio: React.FC<InstallmentStudioProps> = ({ patientId, onPayloadChange }) => {
  const [title, setTitle] = useState('Traitement Orthodontique');
  const [totalAmount, setTotalAmount] = useState<number>(0);
  const [advanceAmount, setAdvanceAmount] = useState<number>(0);
  const [advanceDate, setAdvanceDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [monthsCount, setMonthsCount] = useState<number>(1);
  const [monthlyAmount, setMonthlyAmount] = useState<number>(0);
  const [items, setItems] = useState<DraftInstallmentItem[]>([]);
  const [patientPhone, setPatientPhone] = useState<string>('');

  useEffect(() => {
    if (!patientId || patientId === '0') {
      setPatientPhone('');
      return;
    }
    api.get(`/patients/${patientId}`)
      .then((res: any) => {
        const patient = res.data;
        const phone = patient.telephone_mobile || patient.telephone || patient.telephone_fixe || '';
        setPatientPhone(String(phone).replace(/\s/g, ''));
      })
      .catch(() => setPatientPhone(''));
  }, [patientId]);

  const generateTable = () => {
    if (!Number.isInteger(monthsCount) || monthsCount < 1 || monthsCount > 24) {
      toast.error('Le nombre de mensualités doit être un entier entre 1 et 24.');
      return;
    }
    if (!Number.isFinite(totalAmount) || totalAmount <= 0) {
      toast.error('Renseignez un total strictement positif.');
      return;
    }

    let allocation;
    try {
      allocation = buildExactInstallmentAllocation(totalAmount, advanceAmount, monthsCount);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Échéancier financier invalide.');
      return;
    }

    const newItems: DraftInstallmentItem[] = [];
    if (allocation.advanceAmount > 0) {
      newItems.push({
        id: 'advance',
        label: 'Avance Initiale',
        amount: allocation.advanceAmount,
        dueDate: advanceDate,
      });
    }

    const currentDate = new Date(advanceDate);
    allocation.monthlyAmounts.forEach((amount, index) => {
      currentDate.setMonth(currentDate.getMonth() + 1);
      newItems.push({
        id: `inst_${index}`,
        label: `Mensualité ${index + 1}`,
        amount,
        dueDate: currentDate.toISOString().split('T')[0],
      });
    });

    setItems(newItems);
    PriceBrain.recordInstallmentPlan(
      title,
      allocation.advanceAmount,
      monthsCount,
      allocation.monthlyAmounts[0] ?? 0,
    );
  };

  useEffect(() => {
    if (totalAmount <= 0 || monthsCount < 1) return;
    try {
      const allocation = buildExactInstallmentAllocation(totalAmount, advanceAmount, monthsCount);
      setMonthlyAmount(allocation.monthlyAmounts[0] ?? 0);
    } catch {
      setMonthlyAmount(0);
    }
  }, [totalAmount, advanceAmount, monthsCount]);

  const addItem = () => {
    setItems(prev => [
      ...prev,
      {
        id: `manual_${Date.now()}`,
        label: 'Nouveau versement',
        amount: 0,
        dueDate: new Date().toISOString().split('T')[0],
      },
    ]);
  };

  const updateItem = (id: string, field: keyof DraftInstallmentItem, value: string | number) => {
    setItems(prev => prev.map(item => item.id === id ? { ...item, [field]: value } : item));
  };

  const removeItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  const resetDraft = () => {
    setTitle('Traitement Orthodontique');
    setTotalAmount(0);
    setAdvanceAmount(0);
    setAdvanceDate(new Date().toISOString().split('T')[0]);
    setMonthsCount(1);
    setMonthlyAmount(0);
    setItems([]);
  };

  useEffect(() => {
    onPayloadChange?.({
      patient_id: parseInt(patientId, 10) || 0,
      title,
      total_amount: totalAmount,
      items: items.map(item => ({
        label: item.label,
        amount: item.amount,
        due_date: item.dueDate,
        paid: false,
      })),
    });
  }, [items, title, totalAmount, patientId, onPayloadChange]);

  const plannedTotal = items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0);
  const isBalanced = totalAmount > 0 && Math.abs(plannedTotal - totalAmount) < 0.005;

  return (
    <div className="h-full overflow-y-auto" id="installment-studio-container">
      <InstallmentTrackingPanel patientId={patientId} patientPhone={patientPhone} />

      <section className="flex flex-col rounded-2xl border border-slate-100 bg-white p-6 shadow-sm" aria-labelledby="new-installment-plan-title">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h3 id="new-installment-plan-title" className="text-lg font-bold text-slate-900">Nouveau plan de paiement</h3>
            <p className="text-sm text-slate-500">Préparez un nouvel échéancier. Toutes les lignes seront créées en attente de règlement.</p>
          </div>
          <button
            type="button"
            onClick={resetDraft}
            className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-500 transition hover:bg-slate-50"
          >
            Réinitialiser le brouillon
          </button>
        </div>

        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="installment-plan-title" className="mb-1 block text-sm font-medium text-slate-700">Titre du traitement</label>
            <div className="relative">
              <FileText className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="installment-plan-title"
                type="text"
                value={title}
                onChange={event => setTitle(event.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-10 pr-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="Ex: Traitement Orthodontique"
              />
            </div>
          </div>
          <div>
            <label htmlFor="installment-total" className="mb-1 block text-sm font-medium text-slate-700">Montant total prévu (MAD)</label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="installment-total"
                type="number"
                min="0"
                value={totalAmount}
                onChange={event => setTotalAmount(Number(event.target.value))}
                onFocus={event => event.target.select()}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-10 pr-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>
        </div>

        <div className="mb-6 rounded-xl border border-slate-100 bg-slate-50 p-4">
          <h4 className="mb-3 text-sm font-bold text-slate-800">Génération rapide</h4>
          <div className="grid grid-cols-2 items-end gap-4 md:grid-cols-4">
            <div>
              <label htmlFor="installment-advance" className="mb-1 block text-xs font-medium text-slate-600">Avance (MAD)</label>
              <input
                id="installment-advance"
                type="number"
                min="0"
                value={advanceAmount}
                onChange={event => setAdvanceAmount(Number(event.target.value))}
                onFocus={event => event.target.select()}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label htmlFor="installment-advance-date" className="mb-1 block text-xs font-medium text-slate-600">Date avance</label>
              <input
                id="installment-advance-date"
                type="date"
                value={advanceDate}
                onChange={event => setAdvanceDate(event.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label htmlFor="installment-month-count" className="mb-1 block text-xs font-medium text-slate-600">Nbre mensualités</label>
              <input
                id="installment-month-count"
                type="number"
                min="1"
                max="24"
                value={monthsCount}
                onChange={event => setMonthsCount(Number(event.target.value))}
                onFocus={event => event.target.select()}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label htmlFor="installment-monthly-preview" className="mb-1 block text-xs font-medium text-slate-600">Montant / mois indicatif</label>
              <input
                id="installment-monthly-preview"
                type="number"
                value={monthlyAmount}
                readOnly
                aria-readonly="true"
                className="w-full rounded-lg border border-slate-200 bg-slate-100 px-3 py-2 text-sm text-slate-500"
              />
            </div>
          </div>
          <button
            type="button"
            onClick={generateTable}
            className="mt-4 w-full rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-900"
          >
            Générer le tableau des échéances
          </button>
        </div>

        <div className="mb-3 flex items-center justify-between gap-3">
          <h4 className="text-sm font-bold text-slate-800">Échéances du nouveau plan</h4>
          <button
            type="button"
            onClick={addItem}
            className="flex items-center gap-1 rounded-lg bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20"
          >
            <Plus className="h-3.5 w-3.5" /> Ajouter manuellement
          </button>
        </div>

        <div className="min-h-[200px] overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Libellé</th>
                <th className="w-40 px-4 py-3 font-semibold">Date</th>
                <th className="w-40 px-4 py-3 font-semibold">Montant</th>
                <th className="w-16 px-4 py-3"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map(item => (
                <tr key={item.id} className="hover:bg-slate-50/50">
                  <td className="px-4 py-2">
                    <input
                      type="text"
                      value={item.label}
                      onChange={event => updateItem(item.id, 'label', event.target.value)}
                      className="w-full border-none bg-transparent p-0 text-sm font-medium text-slate-700 focus:ring-0"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <input
                      type="date"
                      value={item.dueDate}
                      onChange={event => updateItem(item.id, 'dueDate', event.target.value)}
                      className="w-full border-none bg-transparent p-0 text-sm text-slate-600 focus:ring-0"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min="0"
                        value={item.amount}
                        onChange={event => updateItem(item.id, 'amount', Number(event.target.value))}
                        onFocus={event => event.target.select()}
                        className="w-full border-none bg-transparent p-0 text-sm font-bold text-slate-900 focus:ring-0"
                      />
                      <span className="text-xs text-slate-400">MAD</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      type="button"
                      onClick={() => removeItem(item.id)}
                      aria-label={`Supprimer ${item.label}`}
                      className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-sm text-slate-500">
                    Aucun brouillon. Utilisez la génération rapide ou ajoutez une échéance manuellement.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex flex-col gap-2 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
          <span className="text-sm text-slate-500">Total planifié : <b className="text-slate-900">{plannedTotal.toFixed(2)} MAD</b></span>
          {totalAmount > 0 && (
            <span className={isBalanced ? 'font-medium text-emerald-600' : 'font-medium text-amber-600'} role="status">
              {isBalanced ? 'Total équilibré' : 'Le total planifié diffère du total prévu'}
            </span>
          )}
        </div>
      </section>
    </div>
  );
};
