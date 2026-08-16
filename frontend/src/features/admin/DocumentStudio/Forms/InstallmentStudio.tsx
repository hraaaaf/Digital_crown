import React, { useEffect, useState } from 'react';
import { Banknote, DollarSign, FileText, MessageCircle, Plus, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { PriceBrain } from '../../../../components/odontogram/PriceBrain';
import { api } from '../../../../services/api';
import { buildExactInstallmentAllocation } from '../InstallmentAllocationPolicy';

interface InstallmentStudioProps {
  patientId: string;
  onPayloadChange?: (payload: { patient_id: number; title: string; total_amount: number; items: Array<{ label: string; amount: number; due_date: string; paid: boolean }> }) => void;
}

type PaymentMethod = 'ESPECES' | 'CARTE' | 'CHEQUE' | 'VIREMENT';

interface InstallmentItem {
  id: string;
  label: string;
  amount: number;
  dueDate: string;
  paid?: boolean;
  sendReminder?: boolean;
  persisted?: boolean;
  paymentMethod?: PaymentMethod;
}

const DEFAULT_TITLE = 'Plan de paiement';

export const InstallmentStudio: React.FC<InstallmentStudioProps> = ({ patientId, onPayloadChange }) => {
  const [title, setTitle] = useState(DEFAULT_TITLE);
  const [totalAmount, setTotalAmount] = useState<number>(0);
  const [advanceAmount, setAdvanceAmount] = useState<number>(0);
  const [advanceDate, setAdvanceDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [monthsCount, setMonthsCount] = useState<number>(1);
  const [monthlyAmount, setMonthlyAmount] = useState<number>(0);
  const [items, setItems] = useState<InstallmentItem[]>([]);
  const [patientPhone, setPatientPhone] = useState<string>('');
  const [loadedPlanId, setLoadedPlanId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [collectingId, setCollectingId] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId || patientId === '0') return;
    api.get(`/patients/${patientId}`).then((res: any) => {
      const p = res.data;
      const phone = p.telephone_mobile || p.telephone || p.telephone_fixe || '';
      setPatientPhone(phone.replace(/\s/g, ''));
    }).catch(() => {});
  }, [patientId]);

  useEffect(() => {
    if (!patientId || patientId === '0') return;
    api.get(`/installments/patient/${patientId}/latest`)
      .then((res: any) => {
        const latestPlan = res.data;
        setLoadedPlanId(latestPlan.id);
        setTitle(latestPlan.title || DEFAULT_TITLE);
        setTotalAmount(latestPlan.total_amount || 0);
        setItems((latestPlan.installments || []).map((inst: any) => ({
          id: String(inst.id),
          label: inst.label || 'Versement',
          amount: Number(inst.amount),
          dueDate: inst.due_date ? inst.due_date.split('T')[0] : '',
          paid: inst.status === 'PAYE',
          sendReminder: false,
          persisted: true,
        })));
      })
      .catch((error: any) => {
        if (error?.response?.status !== 404) console.error(error);
      });
  }, [patientId]);

  const startNewPlan = () => {
    setLoadedPlanId(null);
    setTitle(DEFAULT_TITLE);
    setTotalAmount(0);
    setAdvanceAmount(0);
    setMonthsCount(1);
    setMonthlyAmount(0);
    setItems([]);
  };

  const generateTable = () => {
    if (loadedPlanId) {
      toast.error('Créez un nouveau plan avant de modifier sa structure financière.');
      return;
    }
    if (!Number.isInteger(monthsCount) || monthsCount < 1) {
      toast.error('Le nombre de mensualités doit être un entier positif');
      return;
    }

    try {
      const allocation = buildExactInstallmentAllocation(totalAmount, advanceAmount, monthsCount);
      const newItems: InstallmentItem[] = [];
      if (allocation.advanceAmount > 0) {
        newItems.push({
          id: 'advance',
          label: 'Avance Initiale',
          amount: allocation.advanceAmount,
          dueDate: advanceDate,
          paid: false,
          sendReminder: false,
          persisted: false,
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
          paid: false,
          sendReminder: false,
          persisted: false,
        });
      });
      setItems(newItems);
      PriceBrain.recordInstallmentPlan(title, allocation.advanceAmount, monthsCount, allocation.monthlyAmounts[0] ?? 0);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Échéancier financier invalide.');
    }
  };

  useEffect(() => {
    if (totalAmount <= 0 || monthsCount < 1 || loadedPlanId) return;
    try {
      const allocation = buildExactInstallmentAllocation(totalAmount, advanceAmount, monthsCount);
      setMonthlyAmount(allocation.monthlyAmounts[0] ?? 0);
    } catch {
      setMonthlyAmount(0);
    }
  }, [totalAmount, advanceAmount, monthsCount, loadedPlanId]);

  const updateItem = (id: string, field: keyof InstallmentItem, value: unknown) => {
    setItems(current => current.map(item => item.id === id ? { ...item, [field]: value } : item));
  };

  const addItem = () => {
    if (loadedPlanId) {
      toast.error('La structure d’un plan enregistré est figée. Créez un nouveau plan pour la modifier.');
      return;
    }
    setItems(current => [...current, {
      id: `manual_${Date.now()}`,
      label: 'Nouveau versement',
      amount: 0,
      dueDate: new Date().toISOString().split('T')[0],
      paid: false,
      sendReminder: false,
      persisted: false,
    }]);
  };

  const removeItem = (id: string) => {
    const item = items.find(row => row.id === id);
    if (item?.persisted) {
      toast.error('Une échéance enregistrée ne se supprime pas isolément depuis ce brouillon.');
      return;
    }
    setItems(current => current.filter(row => row.id !== id));
  };

  const persistEditableField = async (item: InstallmentItem, field: 'label' | 'due_date', value: string) => {
    if (!item.persisted || item.paid) return;
    try {
      const persistedValue = field === 'due_date' ? `${value}T00:00:00` : value;
      await api.put(`/installments/${item.id}`, { [field]: persistedValue });
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Modification non enregistrée');
    }
  };

  const collectInstallment = async (item: InstallmentItem) => {
    if (!item.persisted || item.paid) return;
    if (!item.paymentMethod) {
      toast.error('Choisissez un mode de règlement.');
      return;
    }
    setCollectingId(item.id);
    try {
      const res = await api.put(`/installments/${item.id}`, {
        status: 'PAYE',
        payment_method: item.paymentMethod,
      });
      setItems(current => current.map(row => row.id === item.id ? { ...row, paid: res.data.status === 'PAYE', paymentMethod: undefined } : row));
      toast.success('Paiement enregistré');
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Encaissement refusé');
    } finally {
      setCollectingId(null);
    }
  };

  const plannedTotal = items.reduce((acc, item) => acc + (Number(item.amount) || 0), 0);
  const paidTotal = items.filter(item => item.paid).reduce((acc, item) => acc + (Number(item.amount) || 0), 0);
  const remainingTotal = Math.max(totalAmount - paidTotal, 0);
  const isBalanced = totalAmount > 0 && Math.abs(plannedTotal - totalAmount) < 0.005;
  const hasValidDraftRows = items.length > 0 && items.every(item => item.label.trim() && item.amount > 0 && !!item.dueDate);

  const savePlan = async () => {
    if (loadedPlanId) {
      toast.error('Ce plan est déjà enregistré.');
      return;
    }
    if (!isBalanced || !hasValidDraftRows || !title.trim()) {
      toast.error('Le plan doit être complet et exactement équilibré avant enregistrement.');
      return;
    }
    setSaving(true);
    try {
      const res = await api.post('/installments/', {
        patient_id: parseInt(patientId, 10),
        title: title.trim(),
        total_amount: totalAmount,
        installments: items.map(item => ({
          label: item.label.trim(),
          amount: item.amount,
          due_date: `${item.dueDate}T00:00:00`,
          status: 'EN_ATTENTE',
        })),
      });
      setLoadedPlanId(res.data.id);
      setItems((res.data.installments || []).map((inst: any) => ({
        id: String(inst.id),
        label: inst.label,
        amount: Number(inst.amount),
        dueDate: inst.due_date.split('T')[0],
        paid: inst.status === 'PAYE',
        sendReminder: false,
        persisted: true,
      })));
      toast.success('Plan enregistré');
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Plan refusé par le serveur');
    } finally {
      setSaving(false);
    }
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
        paid: item.paid ?? false,
      })),
    });
  }, [items, title, totalAmount, patientId, onPayloadChange]);

  const openWhatsAppReminder = (item: InstallmentItem) => {
    const msg = `Bonjour, ceci est un rappel pour votre échéance: ${item.label} d'un montant de ${item.amount} MAD prévue le ${item.dueDate}. Merci.`;
    let phone = patientPhone.replace(/\s|-/g, '');
    if (phone.startsWith('+')) phone = phone.slice(1);
    else if (phone.startsWith('00')) phone = phone.slice(2);
    else if (phone.startsWith('0')) phone = '212' + phone.slice(1);
    const url = phone ? `https://wa.me/${phone}?text=${encodeURIComponent(msg)}` : `https://wa.me/?text=${encodeURIComponent(msg)}`;
    window.open(url, '_blank');
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col h-full overflow-y-auto" id="installment-studio-container" data-plan-data={JSON.stringify({ title, totalAmount, items })}>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold text-slate-900 mb-1">Suivi Paiement</h3>
          <p className="text-sm text-slate-500">Brouillon équilibré → enregistrement → encaissement explicite.</p>
        </div>
        <button type="button" onClick={startNewPlan} className="px-3 py-2 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-50">
          Nouveau plan
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Titre du plan</label>
          <div className="relative">
            <FileText className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="text" value={title} disabled={!!loadedPlanId} onChange={e => setTitle(e.target.value)} className="w-full pl-10 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm disabled:opacity-60" placeholder="Ex: Plan de paiement" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Montant Total Prévu (MAD)</label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="number" value={totalAmount} disabled={!!loadedPlanId} onChange={e => setTotalAmount(Number(e.target.value))} onFocus={e => e.target.select()} className="w-full pl-10 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm disabled:opacity-60" />
          </div>
        </div>
      </div>

      {!loadedPlanId && (
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 mb-6">
          <h4 className="text-sm font-bold text-slate-800 mb-3">Génération rapide</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 items-end">
            <div><label className="block text-xs font-medium text-slate-600 mb-1">Avance (MAD)</label><input type="number" value={advanceAmount} onChange={e => setAdvanceAmount(Number(e.target.value))} onFocus={e => e.target.select()} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            <div><label className="block text-xs font-medium text-slate-600 mb-1">Date Avance</label><input type="date" value={advanceDate} onChange={e => setAdvanceDate(e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            <div><label className="block text-xs font-medium text-slate-600 mb-1">Nbre Mensualités</label><input type="number" min="1" value={monthsCount} onChange={e => setMonthsCount(Number(e.target.value))} onFocus={e => e.target.select()} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            <div><label className="block text-xs font-medium text-slate-600 mb-1">Montant / Mois (indicatif)</label><input type="number" value={monthlyAmount} readOnly className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-100" /></div>
          </div>
          <button type="button" onClick={generateTable} className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-sm font-medium rounded-lg w-full">Générer le tableau des échéances</button>
        </div>
      )}

      <div className="flex items-center justify-between mb-3 gap-3">
        <h4 className="text-sm font-bold text-slate-800">Échéances</h4>
        {!loadedPlanId && <button type="button" onClick={addItem} className="flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary text-xs font-medium rounded-lg"><Plus className="w-3.5 h-3.5" />Ajouter manuellement</button>}
      </div>

      <div className="flex-1 overflow-x-auto min-h-[200px] border border-slate-200 rounded-xl">
        <table className="w-full min-w-[780px] text-sm text-left">
          <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200 uppercase">
            <tr><th className="px-3 py-3">Statut / Encaissement</th><th className="px-4 py-3">Libellé</th><th className="px-4 py-3">Date</th><th className="px-4 py-3">Montant</th><th className="px-4 py-3 text-center">Rappel WA</th><th className="px-4 py-3 w-16"></th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map(item => (
              <tr key={item.id} className={item.paid ? 'bg-emerald-50/60' : ''}>
                <td className="px-3 py-2 min-w-[230px]">
                  {item.paid ? <span className="font-semibold text-emerald-600">PAYÉ</span> : item.persisted ? (
                    <div className="flex items-center gap-2">
                      <select
                        aria-label={`Mode de règlement ${item.label}`}
                        value={item.paymentMethod || ''}
                        onChange={e => updateItem(item.id, 'paymentMethod', e.target.value as PaymentMethod)}
                        className="border border-slate-200 rounded-lg px-2 py-1 text-xs"
                      >
                        <option value="" disabled>Mode…</option>
                        <option value="ESPECES">Espèces</option>
                        <option value="CARTE">Carte</option>
                        <option value="CHEQUE">Chèque</option>
                        <option value="VIREMENT">Virement</option>
                      </select>
                      <button type="button" onClick={() => collectInstallment(item)} disabled={collectingId === item.id || !item.paymentMethod} className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-emerald-600 text-white text-xs disabled:opacity-50"><Banknote size={14} />Encaisser</button>
                    </div>
                  ) : <span className="text-xs text-slate-500">Brouillon non encaissable</span>}
                </td>
                <td className="px-4 py-2"><input type="text" disabled={item.paid} value={item.label} onChange={e => updateItem(item.id, 'label', e.target.value)} onBlur={e => persistEditableField(item, 'label', e.target.value)} className={`w-full bg-transparent border-none p-0 text-sm font-medium ${item.paid ? 'text-slate-400 line-through' : 'text-slate-700'}`} /></td>
                <td className="px-4 py-2"><input type="date" disabled={item.paid} value={item.dueDate} onChange={e => updateItem(item.id, 'dueDate', e.target.value)} onBlur={e => persistEditableField(item, 'due_date', e.target.value)} className="w-full bg-transparent border-none p-0 text-sm" /></td>
                <td className="px-4 py-2"><div className="flex items-center gap-1"><input type="number" disabled={item.persisted || item.paid} value={item.amount} onChange={e => updateItem(item.id, 'amount', Number(e.target.value))} onFocus={e => e.target.select()} className={`w-full bg-transparent border-none p-0 text-sm font-bold ${item.paid ? 'text-emerald-500' : 'text-slate-900'} disabled:opacity-70`} /><span className="text-xs text-slate-400">MAD</span></div></td>
                <td className="px-4 py-2 text-center"><div className="flex items-center justify-center gap-2"><input type="checkbox" checked={item.sendReminder || false} onChange={e => updateItem(item.id, 'sendReminder', e.target.checked)} className="w-4 h-4 rounded" aria-label={`Activer rappel WhatsApp ${item.label}`} />{item.sendReminder && <button type="button" onClick={() => openWhatsAppReminder(item)} className="text-emerald-500" title="Ouvrir WhatsApp avec le rappel prérempli"><MessageCircle size={16} /></button>}</div></td>
                <td className="px-4 py-2 text-right">{!item.persisted && <button type="button" onClick={() => removeItem(item.id)} className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg" aria-label={`Supprimer ${item.label}`}><Trash2 className="w-4 h-4" /></button>}</td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">Aucune échéance définie.</td></tr>}
          </tbody>
        </table>
      </div>

      <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col gap-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
          <span>Total planifié : <b>{plannedTotal.toFixed(2)} MAD</b></span>
          <span>Payé : <b className="text-emerald-600">{paidTotal.toFixed(2)} MAD</b></span>
          <span>Restant : <b>{remainingTotal.toFixed(2)} MAD</b></span>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          {totalAmount > 0 && <span className={isBalanced ? 'text-emerald-600 text-sm font-medium' : 'text-amber-600 text-sm font-medium'}>{isBalanced ? 'Total équilibré' : 'Le total planifié diffère du total prévu'}</span>}
          {!loadedPlanId && <button type="button" onClick={savePlan} disabled={saving || !isBalanced || !hasValidDraftRows} className="px-4 py-2 bg-primary text-white text-sm font-semibold rounded-lg disabled:opacity-40">{saving ? 'Enregistrement…' : 'Enregistrer le plan'}</button>}
          {loadedPlanId && <span className="text-xs text-slate-500">Plan enregistré #{loadedPlanId}. Les montants sont figés ; toute restructuration passe par un nouveau plan.</span>}
        </div>
      </div>
    </div>
  );
};