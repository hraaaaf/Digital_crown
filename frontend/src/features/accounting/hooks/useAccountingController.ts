import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import type { HonoraireItem } from '../types';

export const useAccountingController = () => {
  const [searchParams] = useSearchParams();
  
  const [items, setItems] = useState<HonoraireItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [sendingEmail, setSendingEmail] = useState<string | null>(null);
  const [overdueData, setOverdueData] = useState<any>(null);
  const [editingCell, setEditingCell] = useState<{ id: string; field: 'title' | 'amount' } | null>(null);
  const [editingValue, setEditingValue] = useState<string>('');
  const [totalAmount, setTotalAmount] = useState(0);
  const [totalCollected, setTotalCollected] = useState(0);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'history' | 'treasury' | 'insights' | 'unpaid'>(
    searchParams.get('tab') === 'insights' ? 'insights' :
    searchParams.get('tab') === 'treasury' ? 'treasury' :
    searchParams.get('tab') === 'unpaid' ? 'unpaid' : 'history'
  );
  const [treasuryData, setTreasuryData] = useState<any>(null);
  const [loadingTreasury, setLoadingTreasury] = useState(false);

  const [debtData, setDebtData] = useState<{
    total_patients: number;
    total_amount: number;
    items: Array<{
      patient_id: number; nom: string; prenom: string;
      telephone: string; assurance: string;
      total_billed: number; total_paid: number; remaining_due: number;
    }>;
  } | null>(null);
  const [loadingDebts, setLoadingDebts] = useState(false);

  // États pour Visual Insights
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [projections, setProjections] = useState<any>(null);
  const [conversions, setConversions] = useState<any>(null);
  const [distributions, setDistributions] = useState<any[]>([]);

  const [financialData, setFinancialData] = useState<any>(null);

  const fetchVisualInsights = useCallback(async () => {
    setLoadingInsights(true);
    try {
      const res = await api.get('/analytics/financial');
      setFinancialData(res.data);
    } catch (err) {
      console.error("Erreur chargement Visual Insights:", err);
    } finally {
      setLoadingInsights(false);
    }
  }, []);

  const toggleGroup = (key: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  // Filters
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssurance, setSelectedAssurance] = useState('ALL');
  const [treasuryStatusFilter, setTreasuryStatusFilter] = useState('ALL');
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [filterType, setFilterType] = useState<'all' | 'insured_notes_only'>('all');
  const [summaryByTitle, setSummaryByTitle] = useState<Record<string, number>>({});

  const months = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
  ];

  const fetchHonoraires = useCallback(async () => {
    setLoading(true);
    try {
      let url = `/accounting/honoraires?year=${selectedYear}`;
      if (selectedMonth !== 0) url += `&month=${selectedMonth}`;
      if (selectedAssurance !== 'ALL') url += `&assurance=${selectedAssurance}`;
      url += `&filter_type=${filterType}`;
      
      const res = await api.get(url);
      setItems(res.data.items || []);
      setTotalAmount(res.data.total_amount || 0);
      setTotalCollected(res.data.total_collected || 0);
      setSummaryByTitle(res.data.summary_by_title || {});
    } catch (err) {
      console.error("Erreur honoraires:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedYear, selectedMonth, selectedAssurance, filterType]);

  const fetchTreasury = useCallback(async () => {
    setLoadingTreasury(true);
    try {
      const [treasuryRes, overdueRes] = await Promise.all([
        api.get('/accounting/treasury-hub'),
        api.get('/accounting/overdue?days=30'),
      ]);
      setTreasuryData(treasuryRes.data);
      setOverdueData(overdueRes.data);
    } catch (err) {
      console.error("Erreur treasury hub:", err);
    } finally {
      setLoadingTreasury(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHonoraires();
    } else if (activeTab === 'treasury') {
      fetchTreasury();
    } else if (activeTab === 'insights') {
      fetchVisualInsights();
    } else if (activeTab === 'unpaid' && !debtData) {
      setLoadingDebts(true);
      api.get('/accounting/patient-debts')
        .then(res => setDebtData(res.data))
        .catch(() => {})
        .finally(() => setLoadingDebts(false));
    }
  }, [activeTab, fetchHonoraires, fetchTreasury, fetchVisualInsights, debtData]);

  const handleExport = async () => {
    setExporting(true);
    try {
      let url = `/accounting/export-pdf?year=${selectedYear}`;
      if (selectedMonth !== 0) url += `&month=${selectedMonth}`;
      if (selectedAssurance !== 'ALL') url += `&assurance=${selectedAssurance}`;
      
      const response = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `Rapport_Honoraires_${selectedYear}_${selectedMonth || 'Global'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Erreur export:", err);
      alert("Erreur lors de la génération du rapport PDF.");
    } finally {
      setExporting(false);
    }
  };

  const handleViewDocument = async (url: string) => {
    try {
      const response = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const docUrl = window.URL.createObjectURL(blob);
      window.open(docUrl, '_blank');
      // Cleanup URL after a while
      setTimeout(() => window.URL.revokeObjectURL(docUrl), 5000);
    } catch (err) {
      console.error("Erreur visualisation document:", err);
      alert("Impossible de visualiser le document (Problème d'accès ou de token).");
    }
  };

  const handleDownloadDocument = async (url: string, filename: string) => {
    try {
      const response = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const docUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = docUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => window.URL.revokeObjectURL(docUrl), 5000);
    } catch (err) {
      console.error("Erreur téléchargement document:", err);
      alert("Erreur lors du téléchargement.");
    }
  };

  const handleDelete = (id: number | string) => {
    setConfirmDeleteId(id);
  };

  const confirmDelete = async () => {
    if (!confirmDeleteId) return;
    try {
      await api.post(`/documents/${confirmDeleteId}/trash`);
      setItems(prev => prev.filter(item => item.id !== confirmDeleteId));
      fetchHonoraires();
      const isActe = String(confirmDeleteId).startsWith('acte_');
      toast.success(isActe ? "Acte déplacé dans la corbeille." : "Note déplacée dans la corbeille.");
    } catch (err) {
      console.error("Erreur suppression honoraire:", err);
      toast.error("Erreur lors de la suppression.");
    } finally {
      setConfirmDeleteId(null);
    }
  };

  const handleEncaisser = async (id: number | string) => {
    try {
      await api.post(`/accounting/encaisser/${id}`);
      toast.success("Règlement encaissé avec succès !");
      fetchTreasury(); // Rafraîchir les données
    } catch (err) {
      console.error("Erreur encaissement:", err);
      toast.error("Échec de l'encaissement.");
    }
  };

  const handleExportCsv = async () => {
    setExportingCsv(true);
    try {
      let url = `/accounting/export-csv?year=${selectedYear}`;
      if (selectedMonth !== 0) url += `&month=${selectedMonth}`;
      if (selectedAssurance !== 'ALL') url += `&assurance=${selectedAssurance}`;
      url += `&filter_type=${filterType}`;
      const response = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8-sig' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `Compta_${selectedYear}_${selectedMonth || 'Annuel'}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      toast.error("Erreur lors de l'export CSV.");
    } finally {
      setExportingCsv(false);
    }
  };

  const handleSendEmail = async (itemId: string | number) => {
    setSendingEmail(String(itemId));
    try {
      await api.post(`/accounting/send-email/${itemId}`);
      toast.success("Note envoyée par email au patient.");
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Erreur d'envoi email.";
      toast.error(detail);
    } finally {
      setSendingEmail(null);
    }
  };

  const handleRelance = async (itemId: string) => {
    setSendingEmail(itemId);
    try {
      await api.post(`/accounting/relance/${itemId}`);
      toast.success("Relance envoyée par email.");
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Erreur d'envoi de relance.";
      toast.error(detail);
    } finally {
      setSendingEmail(null);
    }
  };

  const startEdit = (id: string | number, field: 'title' | 'amount', currentValue: string | number) => {
    setEditingCell({ id: String(id), field });
    setEditingValue(String(currentValue));
  };

  const cancelEdit = () => {
    setEditingCell(null);
    setEditingValue('');
  };

  const commitEdit = async () => {
    if (!editingCell) return;
    const trimmed = editingValue.trim();
    if (!trimmed) { cancelEdit(); return; }

    const body: Record<string, string | number> = {};
    if (editingCell.field === 'title') {
      body.title = trimmed;
    } else {
      const parsed = parseFloat(trimmed.replace(',', '.'));
      if (isNaN(parsed) || parsed < 0) { toast.error("Montant invalide"); return; }
      body.amount = parsed;
    }

    try {
      await api.patch(`/accounting/item/${editingCell.id}`, body);
      setItems(prev => prev.map(item =>
        String(item.id) === editingCell.id
          ? { ...item, [editingCell.field === 'title' ? 'title' : 'amount']: editingCell.field === 'title' ? trimmed : parseFloat(trimmed.replace(',', '.')) }
          : item
      ));
      toast.success("Modifié avec succès.");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erreur de modification.");
    } finally {
      cancelEdit();
    }
  };

  const navigate = useNavigate();

  const handlePatientClick = (patientId: number) => {
    navigate(`/patients/${patientId}`);
  };

  const filteredItems = items.filter(item => 
    item.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.title.toLowerCase().includes(searchTerm.toLowerCase())
  );


  return {
    items,
    loading,
    exporting,
    exportingCsv,
    sendingEmail,
    overdueData,
    editingCell,
    editingValue,
    setEditingValue,
    totalAmount,
    totalCollected,
    expandedGroups,
    activeTab,
    setActiveTab,
    treasuryData,
    loadingTreasury,
    debtData,
    loadingDebts,
    loadingInsights,
    financialData,
    toggleGroup,
    confirmDeleteId,
    setConfirmDeleteId,
    searchTerm,
    setSearchTerm,
    selectedAssurance,
    setSelectedAssurance,
    treasuryStatusFilter,
    setTreasuryStatusFilter,
    selectedMonth,
    setSelectedMonth,
    selectedYear,
    setSelectedYear,
    filterType,
    setFilterType,
    summaryByTitle,
    months,
    handleExport,
    handleViewDocument,
    handleDownloadDocument,
    handleDelete,
    confirmDelete,
    handleEncaisser,
    handleExportCsv,
    handleSendEmail,
    handleRelance,
    startEdit,
    cancelEdit,
    commitEdit,
    handlePatientClick,
    filteredItems,
  };
};
