import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  Receipt, 
  Search, 
  Filter, 
  Calendar, 
  Download, 
  Eye, 
  Loader2,
  TrendingUp,
  ShieldCheck,
  Edit,
  Trash2,
  ChevronDown,
  ChevronRight,
  BarChart2,
  Calculator,
  Check
} from 'lucide-react';
import { cn } from '../utils/cn';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { api } from '../services/api';

// --- COMPOSANTS INTERNES ---

interface HonoraireItem {
  id: number | string;
  patient_id: number;
  patient_name: string;
  assurance: string;
  date: string;
  title: string;
  amount: number;
  file_url: string;
  payment_status?: string;
  is_collected?: boolean;
}

// --- Groupe les notes par patient_id + date (clé composite) ---
interface GroupedItem {
  key: string;
  patient_id: number;
  patient_name: string;
  assurance: string;
  date: string;
  total: number;
  notes: HonoraireItem[];
}

const groupByPatientDate = (items: HonoraireItem[]): GroupedItem[] => {
  const map = new Map<string, GroupedItem>();
  items.forEach(item => {
    const dateKey = new Date(item.date).toLocaleDateString('fr-FR');
    const key = `${item.patient_id}_${dateKey}`;
    if (!map.has(key)) {
      map.set(key, {
        key,
        patient_id: item.patient_id,
        patient_name: item.patient_name,
        assurance: item.assurance,
        date: item.date,
        total: 0,
        notes: [],
      });
    }
    const group = map.get(key)!;
    group.total += item.amount;
    group.notes.push(item);
  });
  return Array.from(map.values());
};

export const AccountingPage = () => {
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'treasury' ? 'treasury' : 'history';
  
  const [items, setItems] = useState<HonoraireItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [totalAmount, setTotalAmount] = useState(0);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'history' | 'treasury'>(initialTab);
  const [treasuryData, setTreasuryData] = useState<any>(null);
  const [loadingTreasury, setLoadingTreasury] = useState(false);

  const toggleGroup = (key: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
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

  const months = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
  ];

  const fetchHonoraires = async () => {
    setLoading(true);
    try {
      let url = `/documents/accounting/honoraires?year=${selectedYear}`;
      if (selectedMonth !== 0) url += `&month=${selectedMonth}`;
      if (selectedAssurance !== 'ALL') url += `&assurance=${selectedAssurance}`;
      
      const res = await api.get(url);
      setItems(res.data.items || []);
      setTotalAmount(res.data.total_amount || 0);
    } catch (err) {
      console.error("Erreur honoraires:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTreasury = async () => {
    setLoadingTreasury(true);
    try {
      const res = await api.get('/documents/accounting/treasury-hub');
      setTreasuryData(res.data);
    } catch (err) {
      console.error("Erreur treasury hub:", err);
    } finally {
      setLoadingTreasury(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHonoraires();
    } else {
      fetchTreasury();
    }
  }, [selectedMonth, selectedYear, selectedAssurance, activeTab]);

  const handleExport = async () => {
    setExporting(true);
    try {
      let url = `/documents/accounting/export-pdf?year=${selectedYear}`;
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
      toast.success("Note déplacée dans la corbeille.");
    } catch (err) {
      console.error("Erreur suppression honoraire:", err);
      toast.error("Erreur lors de la suppression.");
    } finally {
      setConfirmDeleteId(null);
    }
  };

  const handleEncaisser = async (id: number | string) => {
    try {
      await api.post(`/documents/accounting/encaisser/${id}`);
      toast.success("Règlement encaissé avec succès !");
      fetchTreasury(); // Rafraîchir les données
    } catch (err) {
      console.error("Erreur encaissement:", err);
      toast.error("Échec de l'encaissement.");
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

  const getStatusBadge = (item: HonoraireItem) => {
    if (item.payment_status === 'PAYE') {
      if (item.is_collected) {
        return (
          <span className="px-2 py-1 text-[10px] font-black rounded-full bg-emerald-100 text-emerald-700 uppercase tracking-tighter">
            Encaissé
          </span>
        );
      }
      return (
        <span className="px-2 py-1 text-[10px] font-black rounded-full bg-green-100 text-green-700 uppercase tracking-tighter">
          Réglé
        </span>
      );
    }
    
    if (item.payment_status === 'A_ENCAISSER') {
      return (
        <span className="px-2 py-1 text-[10px] font-black rounded-full bg-blue-100 text-blue-700 uppercase tracking-tighter">
          À Encaisser
        </span>
      );
    }

    if (item.payment_status === 'PARTIEL') {
      return (
        <span className="px-2 py-1 text-[10px] font-black rounded-full bg-purple-100 text-purple-700 uppercase tracking-tighter">
          Partiel
        </span>
      );
    }

    return (
      <span className="px-2 py-1 text-[10px] font-black rounded-full bg-amber-100 text-amber-700 uppercase tracking-tighter">
        En attente
      </span>
    );
  };

  const getAssuranceBadge = (assurance: string) => {
    switch (assurance) {
      case 'CNOPS': return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-[10px] font-black">CNOPS</span>;
      case 'CNSS': return <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-lg text-[10px] font-black">CNSS</span>;
      case 'MUTUELLE_FAR': return <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-[10px] font-black">FAR</span>;
      case 'PRIVEE': return <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-lg text-[10px] font-black">PRIVÉE</span>;
      default: return <span className="px-2 py-1 bg-primary/10 text-primary rounded-lg text-[10px] font-black">AUCUNE</span>;
    }
  };

  const getBreakdown = () => {
    const breakdown: Record<string, number> = {};
    items.forEach(item => {
      breakdown[item.assurance] = (breakdown[item.assurance] || 0) + item.amount;
    });
    return breakdown;
  };

  // Préparation des données pour le graphique (par jour)
  const getChartData = () => {
    const dataMap: Record<string, number> = {};
    items.forEach(item => {
      const dateKey = new Date(item.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
      dataMap[dateKey] = (dataMap[dateKey] || 0) + item.amount;
    });
    
    return Object.entries(dataMap)
      .map(([date, amount]) => ({ date, amount }))
      .reverse(); // Ordre chronologique
  };

  const chartData = getChartData();
  const breakdown = getBreakdown();

  const getTrend = (): { pct: number; up: boolean } | null => {
    if (chartData.length < 2) return null;
    const mid = Math.floor(chartData.length / 2);
    const first = chartData.slice(0, mid).reduce((s, d) => s + d.amount, 0);
    const second = chartData.slice(mid).reduce((s, d) => s + d.amount, 0);
    if (first === 0) return null;
    const pct = Math.round(((second - first) / first) * 100);
    return { pct: Math.abs(pct), up: pct >= 0 };
  };
  const trend = getTrend();

  return (
    <div className="max-w-[1600px] mx-auto w-full px-6 py-8 md:px-10 md:py-10 space-y-8 animate-in fade-in duration-700">
      
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-card/80 backdrop-blur-xl border border-border-main p-8 rounded-[2.5rem] shadow-[0_8px_40px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 bg-primary text-white rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20" style={{ backgroundColor: 'var(--primary)' }}>
            <Receipt size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight" style={{ color: 'var(--primary)' }}>Comptabilité & Honoraires</h1>
            <p className="text-slate-500 font-medium mt-1 uppercase text-[10px] tracking-widest flex items-center gap-2">
              <TrendingUp size={14} className="text-emerald-500" />
              Suivi des encaissements par assurance
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex gap-2 mr-4">
            {Object.entries(breakdown).map(([ass, amount]) => amount > 0 && (
              <div key={ass} className="px-3 py-2 bg-slate-50 border border-slate-100 rounded-xl flex flex-col items-center min-w-[80px]">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-tighter">{ass === 'MUTUELLE_FAR' ? 'FAR' : ass}</span>
                <span className="text-[11px] font-bold" style={{ color: 'var(--primary)' }}>{amount.toLocaleString('fr-FR')}</span>
              </div>
            ))}
          </div>
          <div className="bg-emerald-50 px-6 py-4 rounded-3xl border border-emerald-100 flex flex-col items-end shadow-sm">
            <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-1">Total Période</span>
            <span className="text-2xl font-black" style={{ color: 'var(--primary)' }}>{totalAmount.toLocaleString('fr-FR')} MAD</span>
          </div>

          <button 
            onClick={handleExport}
            disabled={exporting || items.length === 0}
            className="flex items-center gap-3 px-6 py-4 text-white rounded-[1.5rem] font-black uppercase text-[12px] tracking-widest shadow-xl shadow-primary/20 hover:-translate-y-1 transition-all active:scale-95 disabled:opacity-50 disabled:translate-y-0"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            {exporting ? <Loader2 className="animate-spin" size={20} /> : <Download size={20} />}
            {exporting ? "Génération..." : "Exporter Rapport"}
          </button>
        </div>
      </header>

      {/* SECTION INSIGHTS FINANCIERS */}
      {activeTab === 'history' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Graphique d'évolution avec empty state conditionnel */}
          <div className="lg:col-span-2 bg-white/80 backdrop-blur-xl border border-slate-200/60 p-8 rounded-[2.5rem] shadow-sm flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-black tracking-tight" style={{ color: 'var(--primary)' }}>Évolution des Recettes</h2>
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Variation sur la période sélectionnée</p>
              </div>
            </div>

            {chartData.length >= 2 ? (
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} dy={10} />
                    <YAxis hide />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-white/95 backdrop-blur-md p-4 rounded-2xl border border-slate-200 shadow-2xl">
                              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{payload[0].payload.date}</p>
                              <p className="text-sm font-black text-primary">{(payload[0].value as number).toLocaleString('fr-FR')} MAD</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Area type="monotone" dataKey="amount" stroke="var(--primary)" strokeWidth={4} fillOpacity={1} fill="url(#colorAmount)" animationDuration={1500} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-40 bg-slate-50 border border-dashed border-slate-200 rounded-2xl gap-3">
                <BarChart2 size={28} className="text-slate-300" />
                <span className="text-slate-500 font-medium text-sm text-center max-w-xs">
                  {chartData.length === 0
                    ? 'Aucun encaissement sur la période sélectionnée.'
                    : 'Données insuffisantes pour tracer l\'évolution (min. 2 dates distinctes).'}
                </span>
              </div>
            )}
          </div>

          {/* Mini Stats Grid */}
          <div className="grid grid-cols-1 gap-4 h-full">
            <div className="bg-white/80 border border-slate-200/60 p-6 rounded-[2rem] flex flex-col justify-between shadow-sm group hover:border-primary/30 transition-all">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Moyenne / Note</span>
              <div className="mt-2">
                <span className="text-3xl font-black text-slate-800">
                  {items.length > 0 ? (totalAmount / items.length).toLocaleString('fr-FR', { maximumFractionDigits: 0 }) : 0}
                </span>
                <span className="text-xs font-bold text-slate-400 ml-2">MAD</span>
              </div>
              {trend && (
                <div className={`mt-4 flex items-center gap-2 ${trend.up ? 'text-emerald-500' : 'text-rose-500'}`}>
                  <TrendingUp size={14} className={trend.up ? '' : 'rotate-180'} />
                  <span className="text-[10px] font-bold">{trend.up ? '+' : '-'}{trend.pct}% sur la période</span>
                </div>
              )}
            </div>

            <div className="bg-white/80 border border-slate-200/60 p-6 rounded-[2rem] flex flex-col justify-between shadow-sm group hover:border-primary/30 transition-all">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Volume d'Activité</span>
              <div className="mt-2">
                <span className="text-3xl font-black text-slate-800">{items.length}</span>
                <span className="text-xs font-bold text-slate-400 ml-2">Notes émises</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TABS NAVIGATION */}
      <div className="flex gap-2 p-1.5 bg-slate-100 rounded-2xl w-fit">
        <button 
          onClick={() => setActiveTab('history')}
          className={cn(
            "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all",
            activeTab === 'history' ? "bg-white shadow-lg text-primary" : "text-slate-500 hover:text-slate-800"
          )}
          style={activeTab === 'history' ? { color: 'var(--primary)' } : {}}
        >
          Historique des Encaissements
        </button>
        <button 
          onClick={() => setActiveTab('treasury')}
          className={cn(
            "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-2 relative",
            activeTab === 'treasury' ? "bg-white shadow-lg text-indigo-600" : "text-slate-500 hover:text-slate-800"
          )}
        >
          <Calculator size={14} /> Ghost Treasury Hub
          {treasuryData?.pending_count > 0 && (
            <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-600 text-[9px] rounded-full font-black animate-pulse">
              {treasuryData.pending_count}
            </span>
          )}
        </button>
      </div>

      {activeTab === 'history' ? (
        <>

      {/* FILTRES DYNAMIQUES */}
      <section className="bg-white/60 backdrop-blur-md border border-slate-200/60 p-6 rounded-[2rem] shadow-sm flex flex-wrap items-center gap-6">
        
        {/* Recherche */}
        <div className="relative flex-1 min-w-[300px] group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Rechercher un patient..." 
            className="w-full pl-12 pr-4 py-3 bg-white border border-slate-200 rounded-2xl text-sm font-bold focus:ring-4 focus:ring-primary/5 outline-none transition-all"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filtre Assurance */}
        <div className="flex items-center gap-3">
          <ShieldCheck size={18} style={{ color: 'var(--primary)' }} />
          <select 
            className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold outline-none focus:ring-4 focus:ring-primary/5"
            value={selectedAssurance}
            onChange={(e) => setSelectedAssurance(e.target.value)}
          >
            <option value="ALL">Toutes Assurances</option>
            <option value="CNOPS">CNOPS</option>
            <option value="CNSS">CNSS</option>
            <option value="MUTUELLE_FAR">FAR</option>
            <option value="PRIVEE">Privée</option>
            <option value="AUCUNE">Sans Assurance</option>
          </select>
        </div>

        {/* Filtre Mois */}
        <div className="flex items-center gap-3">
          <Calendar size={18} style={{ color: 'var(--primary)' }} />
          <select 
            className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold outline-none focus:ring-4 focus:ring-primary/5"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(Number(e.target.value))}
          >
            <option value={0}>Année complète</option>
            {months.map((m, i) => (
              <option key={i} value={i + 1}>{m}</option>
            ))}
          </select>
        </div>

        {/* Filtre Année */}
        <select 
          className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold outline-none focus:ring-4 focus:ring-primary/5"
          value={selectedYear}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
        >
          {[2024, 2025, 2026].map(y => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </section>

      {/* CONFIRMATION SUPPRESSION */}
      {confirmDeleteId && (
        <div className="flex items-center gap-4 px-5 py-3 bg-rose-50 border border-rose-200 rounded-2xl text-sm font-bold text-rose-700">
          <span className="flex-1">Supprimer cette note définitivement ?</span>
          <button onClick={confirmDelete} className="px-4 py-1.5 bg-rose-500 text-white rounded-xl hover:bg-rose-600 transition-all">Confirmer</button>
          <button onClick={() => setConfirmDeleteId(null)} className="px-4 py-1.5 bg-white border border-rose-200 text-rose-500 rounded-xl hover:bg-rose-50 transition-all">Annuler</button>
        </div>
      )}

      {/* LISTE DES HONORAIRES */}
      <main className="bg-white/80 backdrop-blur-xl border border-slate-200/60 rounded-[2.5rem] overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-40 flex flex-col items-center gap-4">
            <Loader2 className="animate-spin" style={{ color: 'var(--primary)' }} size={48} />
            <p className="text-slate-400 font-black uppercase tracking-widest text-xs">Extraction des encaissements...</p>
          </div>
        ) : filteredItems.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50/50 border-b border-slate-100">
                  <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Patient</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Assurance</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Date</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Notes</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] text-right">Total</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] text-center">Statut</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] text-center">Actions</th>
                </tr>
              </thead>
              <tbody>
                {groupByPatientDate(filteredItems).map((group) => {
                  const isExpanded = expandedGroups.has(group.key);
                  const hasMultiple = group.notes.length > 1;
                  return (
                    <React.Fragment key={group.key}>
                      {/* Ligne principale (groupe) */}
                      <tr
                        className={`border-b border-slate-100 transition-colors group ${
                          hasMultiple ? 'cursor-pointer hover:bg-primary/5' : 'hover:bg-primary/5'
                        }`}
                        onClick={() => hasMultiple && toggleGroup(group.key)}
                      >
                        <td className="px-8 py-5">
                          <div className="flex items-center gap-3">
                            {hasMultiple && (
                              <span className="text-slate-400 group-hover:text-primary transition-colors">
                                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                              </span>
                            )}
                            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center font-black text-xs border border-primary/20 group-hover:bg-primary group-hover:text-white transition-all" style={{ color: 'var(--primary)' }}>
                              {group.patient_name.charAt(0)}
                            </div>
                            <Link
                              to={`/patients/${group.patient_id}?tab=admin`}
                              className="font-bold text-slate-800 tracking-tight hover:text-primary hover:underline transition-colors"
                              onClick={e => e.stopPropagation()}
                            >
                              {group.patient_name}
                            </Link>
                          </div>
                        </td>
                        <td className="px-8 py-5">{getAssuranceBadge(group.assurance)}</td>
                        <td className="px-8 py-5 text-sm text-slate-500 font-medium">
                          {new Date(group.date).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="px-8 py-5">
                          {hasMultiple ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-primary/10 rounded-lg text-[10px] font-black" style={{ color: 'var(--primary)' }}>
                              {group.notes.length} notes
                            </span>
                          ) : (
                            <span className="text-sm font-bold text-slate-600 truncate max-w-[200px] block">{group.notes[0].title}</span>
                          )}
                        </td>
                        <td className="px-8 py-5 text-right">
                          <span className="font-black" style={{ color: 'var(--primary)' }}>{group.total.toLocaleString('fr-FR')} MAD</span>
                        </td>
                        <td className="px-8 py-5 text-center">
                          {hasMultiple ? (
                             // Si c'est un groupe, on affiche "Encaissé" uniquement si TOUS sont encaissés
                             group.notes.every(n => n.payment_status === 'PAYE' && n.is_collected) ? (
                               <span className="px-2 py-1 text-[10px] font-black rounded-full bg-emerald-100 text-emerald-700 uppercase tracking-tighter">Encaissé</span>
                             ) : group.notes.every(n => n.payment_status === 'PAYE') ? (
                               <span className="px-2 py-1 text-[10px] font-black rounded-full bg-green-100 text-green-700 uppercase tracking-tighter">Réglé</span>
                             ) : (
                               <span className="px-2 py-1 text-[10px] font-black rounded-full bg-amber-100 text-amber-700 uppercase tracking-tighter">En attente</span>
                             )
                          ) : (
                            getStatusBadge(group.notes[0])
                          )}
                        </td>
                        <td className="px-8 py-5">
                          {!hasMultiple && (
                            <div className="flex items-center justify-center gap-2">
                              {(!group.notes[0].is_collected) && (
                                <button onClick={e => { e.stopPropagation(); handleEncaisser(group.notes[0].id); }} className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-600 hover:text-white transition-all border border-green-100" title="Encaisser">
                                  <Check size={16} />
                                </button>
                              )}
                              <button onClick={() => handleViewDocument(group.notes[0].file_url)} className="p-2 bg-primary/10 text-primary rounded-lg hover:bg-primary hover:text-white transition-all border border-primary/20" title="Voir la Note">
                                <Eye size={16} />
                              </button>
                              <Link to={`/patients/${group.patient_id}?tab=admin`} className="p-2 bg-emerald-50 text-emerald-600 rounded-lg hover:bg-emerald-600 hover:text-white transition-all border border-emerald-100" title="Gérer Patient / Assurance" onClick={e => e.stopPropagation()}>
                                <Edit size={16} />
                              </Link>
                              <button onClick={() => handleDownloadDocument(group.notes[0].file_url, `Note_${group.patient_name}_${group.notes[0].id}.pdf`)} className="p-2 bg-slate-50 text-slate-600 rounded-lg hover:bg-slate-800 hover:text-white transition-all border border-slate-200" title="Télécharger">
                                <Download size={16} />
                              </button>
                              <button onClick={e => { e.stopPropagation(); handleDelete(group.notes[0].id); }} className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-600 hover:text-white transition-all border border-red-100" title="Supprimer">
                                <Trash2 size={16} />
                              </button>
                            </div>
                          )}
                        </td>

                      </tr>

                      {/* Lignes de détail accordéon (multi-notes) */}
                      {hasMultiple && isExpanded && group.notes.map(note => (
                        <tr key={note.id} className="bg-slate-50/60 border-b border-slate-100/60 hover:bg-primary/5 transition-colors">
                          <td className="pl-20 pr-8 py-3" colSpan={3}>
                            <span className="text-sm font-bold text-slate-600 truncate max-w-[240px] block">{note.title}</span>
                          </td>
                          <td className="px-8 py-3 text-right" colSpan={2}>
                            <span className="text-sm font-black text-slate-700">{note.amount.toLocaleString('fr-FR')} MAD</span>
                          </td>
                          <td className="px-8 py-3 text-center">
                             {getStatusBadge(note)}
                          </td>
                          <td className="px-8 py-3">
                            <div className="flex items-center justify-center gap-2">
                              {note.payment_status !== 'PAYE' && (
                                <button onClick={() => handleEncaisser(note.id)} className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-600 hover:text-white transition-all border border-green-100" title="Encaisser">
                                  <Check size={14} />
                                </button>
                              )}
                              <button onClick={() => handleViewDocument(note.file_url)} className="p-2 bg-primary/10 text-primary rounded-lg hover:bg-primary hover:text-white transition-all border border-primary/20" title="Voir la Note">
                                <Eye size={14} />
                              </button>
                              <button onClick={() => handleDownloadDocument(note.file_url, `Note_${group.patient_name}_${note.id}.pdf`)} className="p-2 bg-slate-50 text-slate-600 rounded-lg hover:bg-slate-800 hover:text-white transition-all border border-slate-200" title="Télécharger">
                                <Download size={14} />
                              </button>
                              <button onClick={() => handleDelete(note.id)} className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-600 hover:text-white transition-all border border-red-100" title="Supprimer">
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </td>

                        </tr>
                      ))}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-32 text-center flex flex-col items-center">
            <div className="w-20 h-20 bg-slate-50 rounded-3xl flex items-center justify-center text-slate-200 mb-6 shadow-inner">
              <Filter size={40} />
            </div>
            <h3 className="text-xl font-black text-slate-800 mb-2">Aucun encaissement trouvé</h3>
            <p className="text-slate-400 font-medium max-w-sm">Ajustez vos filtres ou effectuez une nouvelle recherche pour trouver des notes d'honoraires.</p>
          </div>
        )}
      </main>
        </>
      ) : (
        <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
           {/* Treasury Overview Cards */}
           <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col gap-2">
                 <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">En Attente</span>
                 <span className="text-3xl font-black text-slate-800">{treasuryData?.pending_total?.toLocaleString('fr-FR')} MAD</span>
                 <div className="flex items-center gap-2 text-amber-500 mt-2">
                    <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <span className="text-[10px] font-bold uppercase">{treasuryData?.pending_count} dossiers à régulariser</span>
                 </div>
              </div>
              <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col gap-2">
                 <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Règlements Partiels</span>
                 <span className="text-3xl font-black text-slate-800">{treasuryData?.partial_total?.toLocaleString('fr-FR')} MAD</span>
                 <span className="text-[10px] font-bold text-blue-500 uppercase mt-2 italic">Solde restant à percevoir</span>
              </div>
              <div className="bg-indigo-600 p-8 rounded-[2rem] shadow-xl shadow-indigo-200 flex flex-col gap-2 text-white">
                 <span className="text-[10px] font-black text-indigo-200 uppercase tracking-widest">Alerte Chèques</span>
                 <span className="text-3xl font-black">{treasuryData?.cheques_count || 0}</span>
                 <p className="text-[10px] font-medium text-indigo-100 mt-2 leading-relaxed">
                    Chèques en attente de dépôt bancaire ou d'encaissement définitif.
                 </p>
              </div>
              <div className="bg-emerald-600 p-8 rounded-[2rem] shadow-xl shadow-emerald-200 flex flex-col gap-2 text-white">
                 <span className="text-[10px] font-black text-emerald-200 uppercase tracking-widest">Potentiel Immédiat</span>
                 <span className="text-3xl font-black">{( (treasuryData?.pending_total || 0) + (treasuryData?.partial_total || 0) ).toLocaleString('fr-FR')} MAD</span>
                 <p className="text-[10px] font-medium text-emerald-100 mt-2 leading-relaxed">
                    Trésorerie latente à recouvrir activement ce mois.
                 </p>
              </div>
           </div>

           <div className="bg-white rounded-[2.5rem] border border-slate-200 overflow-hidden shadow-sm">
              <div className="px-8 py-6 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                 <div>
                   <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest">Dossiers en souffrance</h3>
                   <p className="text-[10px] text-slate-400 font-medium">Liste des notes non réglées ou partiellement réglées</p>
                 </div>
                 
                 <div className="flex flex-wrap items-center gap-3">
                    <div className="relative group">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-600 transition-colors" size={14} />
                      <input 
                        type="text" 
                        placeholder="Rechercher..." 
                        className="pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-[10px] font-bold focus:ring-4 focus:ring-indigo-500/5 outline-none transition-all w-48"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                      />
                    </div>
                    <select
                      className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-[10px] font-bold outline-none focus:ring-4 focus:ring-indigo-500/5"
                      value={treasuryStatusFilter}
                      onChange={(e) => setTreasuryStatusFilter(e.target.value)}
                    >
                      <option value="ALL">Tous Statuts</option>
                      <option value="EN_ATTENTE">En Attente</option>
                      <option value="PARTIEL">Partiel</option>
                    </select>
                    <button
                      disabled
                      title="Fonctionnalité disponible prochainement"
                      className="px-4 py-2 bg-slate-100 text-slate-400 rounded-xl text-[10px] font-black uppercase tracking-widest cursor-not-allowed border border-slate-200"
                    >
                      Rappels Auto
                    </button>
                 </div>
              </div>
             
             {loadingTreasury ? (
               <div className="py-20 flex flex-col items-center gap-4">
                 <Loader2 className="animate-spin text-indigo-600" size={32} />
               </div>
             ) : (
               <table className="w-full text-left">
                  <thead>
                    <tr className="bg-slate-50/50 border-b border-slate-100">
                      <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Patient</th>
                      <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Date Émission</th>
                      <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Montant</th>
                      <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Statut</th>
                      <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(treasuryData?.items || [])
                      .filter((item: any) =>
                        (item.patient_name.toLowerCase().includes(searchTerm.toLowerCase())) &&
                        (treasuryStatusFilter === 'ALL' || item.status === treasuryStatusFilter)
                      )
                      .map((item: any) => (
                      <tr key={item.id} className="border-b border-slate-100 hover:bg-slate-50 transition-all group">
                        <td className="px-8 py-5">
                          <button 
                            onClick={() => handlePatientClick(item.patient_id)}
                            className="font-bold text-slate-700 hover:text-indigo-600 transition-colors text-left"
                          >
                            {item.patient_name}
                          </button>
                        </td>
                        <td className="px-8 py-5 text-sm text-slate-500">
                          {new Date(item.date).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="px-8 py-5">
                          <span className="font-black text-indigo-600">{item.amount.toLocaleString('fr-FR')} MAD</span>
                        </td>
                        <td className="px-8 py-5">
                          <span className={cn(
                            "px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest",
                            item.status === 'EN_ATTENTE' ? "bg-amber-100 text-amber-700" : 
                            item.status === 'A_ENCAISSER' ? "bg-blue-100 text-blue-700" :
                            "bg-purple-100 text-purple-700"
                          )}>
                            {item.status === 'EN_ATTENTE' ? 'En Attente' : 
                             item.status === 'A_ENCAISSER' ? 'À Encaisser' : 'Partiel'}
                          </span>
                        </td>
                        <td className="px-8 py-5">
                          <div className="flex justify-center gap-2">
                             <button 
                                onClick={() => handleViewDocument(`documents/${item.id}/download`)}
                                className="p-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-600 hover:text-white transition-all border border-indigo-100"
                                title="Voir la note"
                             >
                                <Receipt size={14} />
                             </button>
                             <button 
                                onClick={() => handleEncaisser(item.id)}
                                className="px-4 py-2 bg-emerald-50 text-emerald-600 rounded-xl text-[9px] font-black uppercase tracking-widest border border-emerald-100 hover:bg-emerald-600 hover:text-white transition-all"
                             >
                                Encaisser
                             </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
               </table>
             )}
           </div>
        </div>
      )}
    </div>
  );
};
