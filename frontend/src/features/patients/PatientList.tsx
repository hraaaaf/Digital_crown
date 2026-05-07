import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { Patient } from '../../types'; 
import { UserPlus, Search, Loader2, Edit3, Trash2, AlertTriangle, X, UserX, ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';

export const PatientList = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState<'newest'|'oldest'|'az'|'za'|'dossier'|'created'>('newest');

  // NOUVEAU : État de la modale de suppression
  const [deleteModal, setDeleteModal] = useState<{ open: boolean; id: number | null; name: string }>({
    open: false,
    id: null,
    name: ""
  });

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const res = await api.get('/patients/');
      setPatients(res.data);
    } catch (err) {
      console.error("Erreur chargement:", err);
    } finally {
      setLoading(false);
    }
  };

  // Logique de suppression liée à la modale
  const confirmDelete = async () => {
    if (!deleteModal.id) return;
    try {
      await api.delete(`/patients/${deleteModal.id}`);
      setPatients(patients.filter(p => p.id !== deleteModal.id));
      setDeleteModal({ open: false, id: null, name: "" });
    } catch (err) {
      alert("Erreur lors de la suppression.");
    }
  };

  const filtered = patients.filter(p => {
    const term = searchTerm.toLowerCase();
    const matchSearch = p.nom.toLowerCase().includes(term) ||
                        p.prenom.toLowerCase().includes(term) ||
                        (p.numero_dossier && p.numero_dossier.toLowerCase().includes(term));
    if (!matchSearch) return false;
    return true;
  }).sort((a, b) => {
    if (sortOrder === 'newest') return (b.id || 0) - (a.id || 0);
    if (sortOrder === 'oldest') return (a.id || 0) - (b.id || 0);
    if (sortOrder === 'az') return a.nom.localeCompare(b.nom);
    if (sortOrder === 'za') return b.nom.localeCompare(a.nom);
    if (sortOrder === 'dossier') return (a.numero_dossier || '').localeCompare(b.numero_dossier || '');
    if (sortOrder === 'created') {
      const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
      const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
      return dateB - dateA;
    }
    return 0;
  });

  return (
    <div className="space-y-8 p-6 md:p-10 max-w-[1500px] mx-auto animate-in fade-in duration-700">
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-4xl font-black tracking-tight" style={{ color: 'var(--primary)' }}>Dossiers Patients</h2>
          <p className="text-slate-500 mt-2 font-medium">Gestion de la base de données</p>
        </div>
        <Link 
          to="/patients/new" 
          className="text-white px-6 py-4 rounded-2xl font-black flex items-center justify-center gap-3 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
          style={{ backgroundColor: 'var(--primary)', boxShadow: '0 8px 30px -10px var(--primary)' }}
        >
          <UserPlus size={22} strokeWidth={2.5} /> Créer un dossier
        </Link>
      </div>

      <div className="flex flex-col xl:flex-row gap-4 bg-white/60 backdrop-blur-xl border border-white/80 p-4 rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
        <div className="relative group flex-1">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[var(--primary)] transition-colors" size={20} />
          <input 
              type="text" 
              placeholder="Rechercher par nom, prénom ou dossier..." 
              className="w-full pl-12 pr-6 py-3 bg-white/80 border border-slate-200/60 rounded-2xl focus:ring-4 outline-none text-base transition-all font-bold"
              style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)', borderColor: 'var(--primary)', color: 'var(--primary)' } as any}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <select 
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            className="bg-white border border-slate-200 text-slate-600 font-bold px-4 py-3 rounded-2xl outline-none focus:ring-4 focus:ring-blue-100 cursor-pointer min-w-[180px]"
          >
            <option value="newest">Plus Récents</option>
            <option value="oldest">Plus Anciens</option>
            <option value="az">Alphabétique (A-Z)</option>
            <option value="za">Alphabétique (Z-A)</option>
            <option value="dossier">N° Dossier</option>
            <option value="created">Date de création</option>
          </select>
        </div>
      </div>    

      {/* TABLEAU DES DOSSIERS */}
      <div className="bg-card backdrop-blur-2xl rounded-[2.5rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-border-main overflow-hidden">
        {loading ? (
          <div className="p-32 flex flex-col items-center justify-center gap-6">
            <Loader2 className="animate-spin text-primary" size={36} />
            <p className="text-sm font-black text-text-muted uppercase tracking-widest">Chargement...</p>
          </div>
        ) : filtered.length === 0 && searchTerm.trim() ? (
          /* AUCUN RÉSULTAT - PROPOSITION DE CRÉATION */
          <div className="p-16 flex flex-col items-center justify-center gap-6 text-center">
            <div className="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center">
              <UserX className="text-primary" size={36} />
            </div>
            <div>
              <h3 className="text-xl font-black text-slate-800">Aucun patient trouvé</h3>
              <p className="text-text-muted mt-2 font-medium">
                Aucun dossier ne correspond à "<span className="font-bold text-primary">{searchTerm}</span>"
              </p>
            </div>
            <button
              onClick={() => {
                // Parser le nom saisi (nom prénom ou juste nom)
                const parts = searchTerm.trim().split(/\s+/);
                const nom = parts[0]?.toUpperCase() || '';
                const prenom = parts.slice(1).join(' ') || '';
                navigate(`/patients/new?nom=${encodeURIComponent(nom)}&prenom=${encodeURIComponent(prenom)}`);
              }}
              className="mt-4 bg-gradient-to-br from-primary to-secondary text-white px-8 py-4 rounded-2xl font-black flex items-center gap-3 hover:shadow-2xl hover:shadow-primary/30 hover:-translate-y-1 transition-all duration-300"
            >
              <UserPlus size={22} strokeWidth={2.5} />
              Créer "{searchTerm}"
              <ArrowRight size={18} />
            </button>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200/50 font-black text-slate-400 uppercase tracking-widest text-[10px]">
              <tr>
                <th className="px-10 py-8">Patient</th>
                <th className="px-6 py-8">Assurance</th>
                <th className="px-6 py-8 text-center">Contact</th>
                <th className="px-10 py-8 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100/50">
              {filtered.map((p, index) => {
                const rowKey = p.id ?? `patient-${index}`;

                return (
                  <tr 
                    key={rowKey} 
                    onClick={() => p.id && navigate(`/patients/${p.id}`)}
                    className="hover:bg-blue-50/30 transition-all duration-300 cursor-pointer group"
                  >
                    <td className="px-10 py-6">
                      <div className="flex items-center gap-5">
                        <div className="w-14 h-14 rounded-[1.2rem] bg-gradient-to-br from-primary/5 to-white flex items-center justify-center text-primary font-black text-xl border border-primary/20 shadow-sm group-hover:shadow-md transition-all">
                          {(p.prenom?.charAt(0) || '')}{(p.nom?.charAt(0) || '')}
                        </div>
                        <div>
                          <div className="font-black text-primary text-lg tracking-tight">
                            {p.nom.toUpperCase()} {p.prenom}
                          </div>
                          <div className="text-[11px] font-bold text-slate-400 mt-1 uppercase tracking-wider font-mono">
                            {p.numero_dossier || `ID-${p.id}`}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-6">
                      {p.assurance && p.assurance !== 'AUCUNE' ? (
                        <span className={cn(
                          "px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border shadow-sm",
                          p.assurance === 'CNOPS' ? "bg-blue-100 text-blue-700 border-blue-200" :
                          p.assurance === 'CNSS' ? "bg-emerald-100 text-emerald-700 border-emerald-200" :
                          p.assurance === 'MUTUELLE_FAR' ? "bg-purple-100 text-purple-700 border-purple-200" :
                          "bg-amber-100 text-amber-700 border-amber-200"
                        )}>
                          {p.assurance === 'MUTUELLE_FAR' ? 'FAR' : p.assurance}
                        </span>
                      ) : (
                        <span className="text-slate-300 text-[10px] font-bold uppercase">Privé</span>
                      )}
                    </td>
                    <td className="px-6 py-6 font-mono text-slate-500 font-bold text-center">
                      {p.telephone || "—"}
                    </td>
                    <td className="px-10 py-6 text-right">
                      <div className="flex items-center justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        {/* ACTION 1 : MODIFIER */}
                        <button 
                          onClick={(e) => { 
                            e.stopPropagation(); 
                            if(p.id) navigate(`/patients/${p.id}/edit`); 
                          }}
                          className="p-3 text-text-muted hover:text-primary hover:bg-card border border-transparent hover:border-border-main rounded-2xl transition-all shadow-sm"
                          title="Modifier les infos"
                        >
                          <Edit3 size={20} />
                        </button>
                        
                        {/* ACTION 2 : SUPPRIMER (Ouvre la modale) */}
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            if(p.id) setDeleteModal({ open: true, id: p.id, name: `${p.prenom} ${p.nom}` });
                          }}
                          className="p-3 text-slate-300 hover:text-red-500 hover:bg-red-50 border border-transparent hover:border-red-100 rounded-2xl transition-all shadow-sm"
                          title="Supprimer définitivement"
                        >
                          <Trash2 size={20} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* MODALE DE SUPPRESSION PREMIUM */}
      {deleteModal.open && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-medical-dark/40 backdrop-blur-md animate-in fade-in duration-300 h-screen w-screen">
          <div className="bg-card rounded-[2.5rem] p-10 max-w-md w-full shadow-2xl border border-border-main relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6">
               <button onClick={() => setDeleteModal({ ...deleteModal, open: false })} className="text-slate-300 hover:text-slate-500 transition-colors">
                 <X size={24} />
               </button>
            </div>
            <div className="w-20 h-20 bg-red-50 text-red-500 rounded-3xl flex items-center justify-center mb-6">
              <AlertTriangle size={40} />
            </div>
            <h3 className="text-2xl font-black text-text-main leading-tight tracking-tight">Supprimer le dossier ?</h3>
            <p className="text-text-muted mt-3 font-medium leading-relaxed">
              Vous allez supprimer définitivement le dossier de <span className="font-bold text-text-main">{deleteModal.name}</span>. Cette action effacera également ses documents générés.
            </p>
            <div className="flex gap-4 mt-10">
              <button 
                onClick={() => setDeleteModal({ ...deleteModal, open: false })} 
                className="flex-1 py-4 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-2xl font-bold transition-all active:scale-95"
              >
                Annuler
              </button>
              <button 
                onClick={confirmDelete} 
                className="flex-1 py-4 bg-red-500 hover:bg-red-600 text-white rounded-2xl font-bold shadow-lg shadow-red-200 transition-all active:scale-95"
              >
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};