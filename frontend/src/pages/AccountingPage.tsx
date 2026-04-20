import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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
  Trash2
} from 'lucide-react';
import { api } from '../services/api';

interface HonoraireItem {
  id: number | string;
  patient_id: number;
  patient_name: string;
  assurance: string;
  date: string;
  title: string;
  amount: number;
  file_url: string;
}

export const AccountingPage = () => {
  const [items, setItems] = useState<HonoraireItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [totalAmount, setTotalAmount] = useState(0);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssurance, setSelectedAssurance] = useState('ALL');
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  const months = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
  ];

  const fetchHonoraires = async () => {
    setLoading(true);
    try {
      let url = `/accounting/honoraires?year=${selectedYear}`;
      if (selectedMonth !== 0) url += `&month=${selectedMonth}`;
      if (selectedAssurance !== 'ALL') url += `&assurance=${selectedAssurance}`;
      
      const res = await api.get(url);
      setItems(res.data.items);
      setTotalAmount(res.data.total_amount);
    } catch (err) {
      console.error("Erreur honoraires:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHonoraires();
  }, [selectedMonth, selectedYear, selectedAssurance]);

  const handleExport = async () => {
    setExporting(true);
    try {
      let url = `/accounting/export-pdf?year=${selectedYear}`;
      if (selectedMonth !== 0) url += `&month=${selectedMonth}`;
      if (selectedAssurance !== 'ALL') url += `&assurance=${selectedAssurance}`;
      
      const res = await api.get(url);
      window.open(`http://localhost:8000/${res.data.pdf_url}`, '_blank');
    } catch (err) {
      console.error("Erreur export:", err);
      alert("Erreur lors de la génération du rapport PDF.");
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async (id: number | string) => {
    if (window.confirm("Êtes-vous sûr de vouloir supprimer cette note d'honoraires ? Elle sera déplacée dans la corbeille.")) {
      try {
        await api.post(`/documents/${id}/trash`);
        // Mise à jour locale de la liste
        setItems(prev => prev.filter(item => item.id !== id));
        // Recalculer le total optionnellement ou re-fetcher
        fetchHonoraires();
      } catch (err) {
        console.error("Erreur suppression honoraire:", err);
        alert("Erreur lors de la suppression.");
      }
    }
  };

  const filteredItems = items.filter(item => 
    item.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getAssuranceBadge = (assurance: string) => {
    switch (assurance) {
      case 'CNOPS': return <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-[10px] font-black">CNOPS</span>;
      case 'CNSS': return <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-lg text-[10px] font-black">CNSS</span>;
      case 'MUTUELLE_FAR': return <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-[10px] font-black">FAR</span>;
      case 'PRIVEE': return <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-lg text-[10px] font-black">PRIVÉE</span>;
      default: return <span className="px-2 py-1 bg-slate-100 text-slate-500 rounded-lg text-[10px] font-black">AUCUNE</span>;
    }
  };

  const getBreakdown = () => {
    const breakdown: Record<string, number> = {};
    items.forEach(item => {
      const ass = item.assurance || 'AUCUNE';
      breakdown[ass] = (breakdown[ass] || 0) + item.amount;
    });
    return breakdown;
  };

  const breakdown = getBreakdown();

  return (
    <div className="max-w-[1600px] mx-auto w-full px-6 py-8 md:px-10 md:py-10 space-y-8 animate-in fade-in duration-700">
      
      {/* HEADER PREMIUM */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white/80 backdrop-blur-xl border border-slate-200/60 p-8 rounded-[2.5rem] shadow-[0_8px_40px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 bg-[#003380] text-white rounded-2xl flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Receipt size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-black text-[#003380] tracking-tight">Comptabilité & Honoraires</h1>
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
                <span className="text-[11px] font-bold text-[#003380]">{amount.toLocaleString('fr-FR')}</span>
              </div>
            ))}
          </div>
          <div className="bg-emerald-50 px-6 py-4 rounded-3xl border border-emerald-100 flex flex-col items-end shadow-sm">
            <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-1">Total Période</span>
            <span className="text-2xl font-black text-[#003380]">{totalAmount.toLocaleString('fr-FR')} MAD</span>
          </div>

          <button 
            onClick={handleExport}
            disabled={exporting || items.length === 0}
            className="flex items-center gap-3 px-6 py-4 bg-[#003380] text-white rounded-[1.5rem] font-black uppercase text-[12px] tracking-widest shadow-xl shadow-blue-900/20 hover:-translate-y-1 transition-all active:scale-95 disabled:opacity-50 disabled:translate-y-0"
          >
            {exporting ? <Loader2 className="animate-spin" size={20} /> : <Download size={20} />}
            {exporting ? "Génération..." : "Exporter Rapport"}
          </button>
        </div>
      </header>

      {/* FILTRES DYNAMIQUES */}
      <section className="bg-white/60 backdrop-blur-md border border-slate-200/60 p-6 rounded-[2rem] shadow-sm flex flex-wrap items-center gap-6">
        
        {/* Recherche */}
        <div className="relative flex-1 min-w-[300px] group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#003380] transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Rechercher un patient..." 
            className="w-full pl-12 pr-4 py-3 bg-white border border-slate-200 rounded-2xl text-sm font-bold focus:ring-4 focus:ring-[#003380]/5 outline-none transition-all"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filtre Assurance */}
        <div className="flex items-center gap-3">
          <ShieldCheck size={18} className="text-[#003380]" />
          <select 
            className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold outline-none focus:ring-4 focus:ring-[#003380]/5"
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
          <Calendar size={18} className="text-[#003380]" />
          <select 
            className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold outline-none focus:ring-4 focus:ring-[#003380]/5"
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
          className="bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-bold outline-none focus:ring-4 focus:ring-[#003380]/5"
          value={selectedYear}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
        >
          {[2024, 2025, 2026].map(y => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </section>

      {/* LISTE DES HONORAIRES */}
      <main className="bg-white/80 backdrop-blur-xl border border-slate-200/60 rounded-[2.5rem] overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-40 flex flex-col items-center gap-4">
            <Loader2 className="animate-spin text-[#003380]" size={48} />
            <p className="text-slate-400 font-black uppercase tracking-widest text-xs">Extraction des encaissements...</p>
          </div>
        ) : filteredItems.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50/50 border-b border-slate-100">
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Patient</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Assurance</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Date</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Libellé</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-right">Montant</th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-blue-50/30 transition-colors group">
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-[#003380] font-black text-xs border border-slate-200 group-hover:bg-[#003380] group-hover:text-white transition-all">
                          {item.patient_name.charAt(0)}
                        </div>
                        <Link 
                          to={`/patients/${item.patient_id}?tab=admin`}
                          className="font-bold text-slate-800 tracking-tight hover:text-[#003380] hover:underline transition-colors"
                        >
                          {item.patient_name}
                        </Link>
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      {getAssuranceBadge(item.assurance)}
                    </td>
                    <td className="px-8 py-5 text-sm text-slate-500 font-medium">
                      {new Date(item.date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-8 py-5">
                      <span className="text-sm font-bold text-slate-600 truncate max-w-[200px] block">{item.title}</span>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <span className="font-black text-[#003380]">{item.amount.toLocaleString('fr-FR')} MAD</span>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center justify-center gap-2">
                        <a 
                          href={`http://localhost:8000/${item.file_url}`} 
                          target="_blank" 
                          rel="noreferrer"
                          className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-[#003380] hover:text-white transition-all border border-blue-100"
                        >
                          <Eye size={16} />
                        </a>
                        <a 
                          href={`/patients/${item.patient_id}/edit`}
                          className="p-2 bg-emerald-50 text-emerald-600 rounded-lg hover:bg-emerald-600 hover:text-white transition-all border border-emerald-100"
                          title="Attribuer Assurance"
                        >
                          <Edit size={16} />
                        </a>
                        <a 
                          href={`http://localhost:8000/${item.file_url}`} 
                          download
                          className="p-2 bg-slate-50 text-slate-600 rounded-lg hover:bg-slate-800 hover:text-white transition-all border border-slate-200"
                        >
                          <Download size={16} />
                        </a>
                        <button 
                          onClick={() => handleDelete(item.id)}
                          className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-600 hover:text-white transition-all border border-red-100"
                          title="Supprimer"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
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
    </div>
  );
};
