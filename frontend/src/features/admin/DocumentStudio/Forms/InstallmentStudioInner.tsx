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
      if (res.data.status !== 'PAYE') {
        throw new Error('Encaissement non confirmé par le serveur');
      }

      const latestResponse = await api.get(`/installments/patient/${patientId}/latest`);
      const latestPlan = latestResponse.data;
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
      toast.success('Paiement enregistré');
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || error?.message || 'Encaissement refusé');
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