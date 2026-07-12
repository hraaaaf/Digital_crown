import { useCallback, useEffect, useState, useRef } from 'react';
import { api } from '../../services/api';
import type { Patient } from '../../types';
import { UserPlus, Search, Loader2, Edit3, Trash2, AlertTriangle, X, UserX, ArrowRight, LayoutGrid, List, UploadCloud } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';
import { PatientScoreBadge } from './components/PatientScoreBadge';
import { useSettingsStore } from '../admin/Settings/hooks/useSettingsStore';
import { PatientSummaryHoverCard } from './components/PatientSummaryHoverCard';
import { EliteGhostLoader } from '../../components/EliteGhostLoader';
import { usePatientStore } from '../../stores/usePatientStore';
import { CsvImportModal } from './CsvImportModal';
import { AssuranceBadge } from '../../components/AssuranceBadge';
import { useEscapeKey } from '../../hooks/useEscapeKey';

export const PatientList = () => {
  const navigate = useNavigate();
  const { patientsCache, patientsCacheLoaded, patientsCacheUpdatedAt, setPatientsCache } = usePatientStore();
  const [patients, setPatients] = useState<Patient[]>(patientsCache);
  const [loading, setLoading] = useState(!patientsCacheLoaded);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState<'newest'|'oldest'|'az'|'za'|'dossier'|'created'>('newest');
  const show_patient_badges = useSettingsStore(state => state.profile.show_patient_badges);
  const [fantomeIds, setFantomeIds] = useState<Set<number>>(new Set());

  // État pour la carte de survol intelligente
  const [hoveredPatient, setHoveredPatient] = useState<{
    id: number;
    name: string;
    dossier: string;
    rect: DOMRect;
  } | null>(null);

  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = (
    e: React.MouseEvent<HTMLElement>,
    id: number,
    nom: string,
    prenom: string,
    dossier: string
  ) => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    const rect = e.currentTarget.getBoundingClientRect();
    hoverTimeoutRef.current = setTimeout(() => {
      setHoveredPatient({
        id,
        name: `${prenom} ${nom.toUpperCase()}`,
        dossier: dossier || `ID-${id}`,
        rect
      });
    }, 250);
  };

  const handleMouseLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
    setHoveredPatient(null);
  };

  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);

  // État du mode d'affichage (Table ou Grille) avec persistance localStorage
  const [viewMode, setViewMode] = useState<'table' | 'grid'>(() => {
    return (localStorage.getItem('patient_list_view_mode') as 'table' | 'grid') || 'table';
  });

  // NOUVEAU : État de la modale de suppression
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deleteModal, setDeleteModal] = useState<{ open: boolean; id: number | null; name: string }>({
    open: false,
    id: null,
    name: ""
  });

  const fetchPatients = useCallback(async (force = false) => {
    const cacheAgeMs = Date.now() - patientsCacheUpdatedAt;
    if (!force && patientsCacheLoaded && cacheAgeMs < 120000) {
      setLoading(false);
      return;
    }

    try {
      const res = await api.get('/patients/');
      setPatients(res.data);
      setPatientsCache(res.data);
    } catch (err) {
      console.error("Erreur chargement:", err);
    } finally {
      setLoading(false);
    }
  }, [patientsCacheLoaded, patientsCacheUpdatedAt, setPatientsCache]);

  useEffect(() => {
    fetchPatients();
    api.get('/patients/fantomes').then(res => {
      setFantomeIds(new Set((res.data as { patient_id: number }[]).map(f => f.patient_id)));
    }).catch(() => {});
  }, [fetchPatients]);

  useEffect(() => {
    localStorage.setItem('patient_list_view_mode', viewMode);
  }, [viewMode]);

  // Logique de suppression liée à la modale — confirmation forte : le nom exact
  // du patient doit être saisi (garde en profondeur, en plus du bouton disabled).
  const confirmDelete = async () => {
    if (!deleteModal.id) return;
    if (deleteConfirmText.trim() !== deleteModal.name.trim()) return;
    try {
      await api.delete(`/patients/${deleteModal.id}`);
      const nextPatients = patients.filter(p => p.id !== deleteModal.id);
      setPatients(nextPatients);
      setPatientsCache(nextPatients);
      setDeleteModal({ open: false, id: null, name: "" });
      setDeleteConfirmText('');
    } catch (err) {
      alert("Erreur lors de la suppression.");
    }
  };

  useEscapeKey(deleteModal.open, () => { setDeleteModal({ ...deleteModal, open: false }); setDeleteConfirmText(''); });

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
          <p className="text-text-muted mt-2 font-medium">Gestion de la base de données</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setIsCsvModalOpen(true)}
            className="px-5 py-4 rounded-2xl font-black flex items-center gap-2 border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:-translate-y-0.5 transition-all duration-300 shadow-sm"
          >
            <UploadCloud size={20} strokeWidth={2.5} /> Import CSV
          </button>
          <Link
            to="/patients/new"
            className="text-white px-6 py-4 rounded-2xl font-black flex items-center justify-center gap-3 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
            style={{ backgroundColor: 'var(--primary)', boxShadow: '0 8px 30px -10px var(--primary)' }}
          >
            <UserPlus size={22} strokeWidth={2.5} /> Créer un dossier
          </Link>
        </div>
      </div>

      <div className="flex flex-col xl:flex-row gap-4 bg-card-bg/60 backdrop-blur-xl border border-border-main p-4 rounded-[2rem] shadow-elite">
        <div className="relative group flex-1">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-[var(--primary)] transition-colors" size={20} />
          <input 
              type="text" 
              placeholder="Rechercher par nom, prénom ou dossier..." 
              className="w-full pl-12 pr-6 py-3 bg-card-bg/80 border border-border-main rounded-2xl focus:ring-4 outline-none text-base transition-all font-bold"
              style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)', color: 'var(--text-main)' } as any}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <select 
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            className="bg-card-bg border border-border-main text-text-muted font-bold px-4 py-3 rounded-2xl outline-none focus:ring-4 focus:ring-primary/10 cursor-pointer min-w-[180px] h-[52px]"
          >
            <option value="newest">Plus Récents</option>
            <option value="oldest">Plus Anciens</option>
            <option value="az">Alphabétique (A-Z)</option>
            <option value="za">Alphabétique (Z-A)</option>
            <option value="dossier">N° Dossier</option>
            <option value="created">Date de création</option>
          </select>

          {/* Commutateur de vue Table / Grille */}
          <div className="flex items-center bg-card-bg/80 border border-border-main p-1 rounded-2xl gap-1 h-[52px]">
            <button
              onClick={() => setViewMode('table')}
              className={cn(
                "p-2.5 rounded-xl transition-all h-full flex items-center justify-center aspect-square",
                viewMode === 'table' 
                  ? "bg-primary text-white shadow-md shadow-primary/20" 
                  : "text-text-muted hover:text-text-main hover:bg-primary/5"
              )}
              style={viewMode === 'table' ? { backgroundColor: 'var(--primary)' } : {}}
              title="Vue Table"
              aria-label="Vue Table"
            >
              <List size={20} />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                "p-2.5 rounded-xl transition-all h-full flex items-center justify-center aspect-square",
                viewMode === 'grid' 
                  ? "bg-primary text-white shadow-md shadow-primary/20" 
                  : "text-text-muted hover:text-text-main hover:bg-primary/5"
              )}
              style={viewMode === 'grid' ? { backgroundColor: 'var(--primary)' } : {}}
              title="Vue Grille"
              aria-label="Vue Grille"
            >
              <LayoutGrid size={20} />
            </button>
          </div>
        </div>
      </div>    

      {/* TABLEAU OU GRILLE DES DOSSIERS */}
      <div className="bg-card-bg backdrop-blur-2xl rounded-[2.5rem] shadow-elite border border-border-main overflow-hidden">
        {loading ? (
          <div className="h-[500px] relative">
            <EliteGhostLoader text="Chargement des dossiers..." fullScreen={false} size="medium" />
          </div>
        ) : patients.length === 0 ? (
          /* AUCUN PATIENT EN BASE (JOUR 1) */
          <div className="p-20 flex flex-col items-center justify-center gap-6 text-center">
            <div className="w-24 h-24 bg-primary/5 rounded-[2rem] flex items-center justify-center">
              <UserPlus className="text-primary w-12 h-12" />
            </div>
            <div>
              <h3 className="text-2xl font-black text-main font-outfit" style={{ color: 'var(--text-main)' }}>Votre base de données est vierge</h3>
              <p className="text-text-muted mt-3 font-medium text-sm max-w-[320px] mx-auto leading-relaxed">
                Il est temps de donner vie à votre clinique. Ajoutez votre premier patient pour accéder à son dossier clinique, ses ordonnances et son historique.
              </p>
            </div>
            <Link
              to="/patients/new"
              className="mt-6 bg-primary text-white px-8 py-4 rounded-2xl font-black flex items-center gap-3 shadow-lg shadow-primary/20 hover:shadow-2xl hover:shadow-primary/30 hover:-translate-y-1 transition-all duration-300"
            >
              <UserPlus size={22} strokeWidth={2.5} />
              Créer mon premier dossier
              <ArrowRight size={18} />
            </Link>
          </div>
        ) : filtered.length === 0 && searchTerm.trim() ? (
          /* AUCUN RÉSULTAT - PROPOSITION DE CRÉATION */
          <div className="p-16 flex flex-col items-center justify-center gap-6 text-center">
            <div className="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center">
              <UserX className="text-primary" size={36} />
            </div>
            <div>
              <h3 className="text-xl font-black text-main" style={{ color: 'var(--text-main)' }}>Aucun patient trouvé</h3>
              <p className="text-text-muted mt-2 font-medium">
                Aucun dossier ne correspond à "<span className="font-bold text-primary">{searchTerm}</span>"
              </p>
            </div>
            <button
              onClick={() => {
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
        ) : viewMode === 'table' ? (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border-main font-black text-text-muted uppercase tracking-widest text-[10px]">
              <tr>
                <th className="px-10 py-8">Patient</th>
                <th className="px-6 py-8">Assurance</th>
                <th className="px-6 py-8 text-center">Contact</th>
                <th className="px-10 py-8 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-main/50">
              {filtered.map((p, index) => {
                const rowKey = p.id ?? `patient-${index}`;

                return (
                  <tr
                    key={rowKey}
                    onClick={() => p.id && navigate(`/patients/${p.id}`)}
                    onMouseEnter={(e) => p.id && handleMouseEnter(e, p.id, p.nom, p.prenom, p.numero_dossier)}
                    onMouseLeave={handleMouseLeave}
                    tabIndex={0}
                    role="button"
                    onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && p.id) { e.preventDefault(); navigate(`/patients/${p.id}`); } }}
                    className="hover:bg-primary/5 transition-all duration-300 cursor-pointer group border-l-4 border-l-transparent hover:border-l-primary hover:scale-[1.002] focus:outline-2 focus:outline-primary focus:outline-offset-2"
                  >
                    <td className="px-10 py-6">
                      <div className="flex items-center gap-5">
                        <div className="w-14 h-14 rounded-[1.2rem] bg-gradient-to-br from-primary/10 to-card-bg flex items-center justify-center text-primary font-black text-xl border border-primary/20 shadow-sm group-hover:shadow-md transition-all">
                          {(p.prenom?.charAt(0) || '')}{(p.nom?.charAt(0) || '')}
                        </div>
                        <div>
                          <div className="flex items-center gap-3">
                            <div className="font-black text-primary text-lg tracking-tight">
                              {p.nom.toUpperCase()} {p.prenom}
                            </div>
                            {show_patient_badges && <PatientScoreBadge patientId={p.id!} className="scale-75 origin-left" onUpdate={() => fetchPatients(true)} />}
                            {p.id && fantomeIds.has(p.id) && (
                              <span className="flex items-center gap-1 px-2 py-0.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-[9px] font-black uppercase tracking-widest">
                                <AlertTriangle size={10} /> Fantôme
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] font-bold text-text-muted mt-1 uppercase tracking-wider font-mono">
                            {p.numero_dossier || `ID-${p.id}`}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-6">
                      <AssuranceBadge assurance={p.assurance} size="full" />
                    </td>
                    <td className="px-6 py-6 font-mono text-text-muted font-bold text-center">
                      {p.telephone || "—"}
                    </td>
                    <td className="px-10 py-6 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if(p.id) navigate(`/patients/${p.id}/edit`);
                          }}
                          className="p-3 text-text-muted hover:text-primary hover:bg-card-bg border border-transparent hover:border-border-main rounded-2xl transition-all shadow-sm"
                          title="Modifier les infos"
                          aria-label="Modifier les infos"
                        >
                          <Edit3 size={20} />
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if(p.id) setDeleteModal({ open: true, id: p.id, name: `${p.prenom} ${p.nom}` });
                          }}
                          className="p-3 text-text-muted hover:text-red-500 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 rounded-2xl transition-all shadow-sm"
                          title="Supprimer définitivement"
                          aria-label="Supprimer définitivement"
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
        ) : (
          /* GRILLE DE DOSSIERS PATIENTS GHOST ELITE */
          <div className="p-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 bg-card-bg/10">
            {filtered.map((p, index) => {
              const cardKey = p.id ?? `patient-card-${index}`;
              return (
                <div
                  key={cardKey}
                  onClick={() => p.id && navigate(`/patients/${p.id}`)}
                  onMouseEnter={(e) => p.id && handleMouseEnter(e, p.id, p.nom, p.prenom, p.numero_dossier)}
                  onMouseLeave={handleMouseLeave}
                  tabIndex={0}
                  role="button"
                  onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && p.id) { e.preventDefault(); navigate(`/patients/${p.id}`); } }}
                  className="bg-card-bg/60 backdrop-blur-xl border border-border-main/60 rounded-[2rem] p-6 hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-2 hover:border-primary/30 hover:bg-card-bg/90 transition-all duration-300 cursor-pointer group relative flex flex-col justify-between min-h-[220px] focus:outline-2 focus:outline-primary focus:outline-offset-2"
                >
                  <div>
                    {/* Ligne du haut: Bulle Patient et Actions rapides */}
                    <div className="flex items-start justify-between gap-3 mb-5">
                      <div className="w-14 h-14 rounded-[1.2rem] bg-gradient-to-br from-primary/10 to-card-bg flex items-center justify-center text-primary font-black text-xl border border-primary/20 shadow-sm group-hover:shadow-md transition-all">
                        {(p.prenom?.charAt(0) || '')}{(p.nom?.charAt(0) || '')}
                      </div>

                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if(p.id) navigate(`/patients/${p.id}/edit`);
                          }}
                          className="p-2.5 text-text-muted hover:text-primary hover:bg-card-bg border border-border-main/50 rounded-xl transition-all shadow-sm"
                          title="Modifier"
                          aria-label="Modifier"
                        >
                          <Edit3 size={16} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if(p.id) setDeleteModal({ open: true, id: p.id, name: `${p.prenom} ${p.nom}` });
                          }}
                          className="p-2.5 text-text-muted hover:text-red-500 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 rounded-xl transition-all shadow-sm"
                          title="Supprimer"
                          aria-label="Supprimer"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    {/* Informations textuelles */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-black text-primary text-lg tracking-tight leading-tight group-hover:text-primary-dark transition-colors">
                          {p.nom.toUpperCase()} {p.prenom}
                        </h4>
                        {p.id && fantomeIds.has(p.id) && (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-[9px] font-black uppercase tracking-widest">
                            <AlertTriangle size={10} /> Fantôme
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider font-mono">
                        {p.numero_dossier || `ID-${p.id}`}
                      </div>
                    </div>
                  </div>

                  {/* Ligne du bas : Badges CRM, Assurances et téléphone */}
                  <div className="mt-6 pt-4 border-t border-border-main/40 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <AssuranceBadge assurance={p.assurance} size="compact" />

                      {show_patient_badges && p.id && (
                        <div onClick={(e) => e.stopPropagation()} className="scale-90 origin-left">
                          <PatientScoreBadge patientId={p.id} onUpdate={() => fetchPatients(true)} />
                        </div>
                      )}
                    </div>

                    <div className="text-[11px] font-mono text-text-muted font-bold tracking-tight">
                      {p.telephone || "—"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* MODALE DE SUPPRESSION PREMIUM */}
      {deleteModal.open && (
        <div role="dialog" aria-modal="true" aria-label="Supprimer le dossier" className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/60 backdrop-blur-md animate-in fade-in duration-300 h-screen w-screen">
          <div className="bg-card-bg rounded-[2.5rem] p-10 max-w-md w-full shadow-2xl border border-border-main relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6">
               <button onClick={() => { setDeleteModal({ ...deleteModal, open: false }); setDeleteConfirmText(''); }} className="text-text-muted hover:text-main transition-colors" aria-label="Fermer">
                 <X size={24} />
               </button>
            </div>
            <div className="w-20 h-20 bg-red-500/10 text-red-500 rounded-3xl flex items-center justify-center mb-6">
              <AlertTriangle size={40} />
            </div>
            <h3 className="text-2xl font-black text-main leading-tight tracking-tight" style={{ color: 'var(--text-main)' }}>Supprimer le dossier ?</h3>
            <p className="text-text-muted mt-3 font-medium leading-relaxed">
              Cette action masque le dossier de <span className="font-bold text-main" style={{ color: 'var(--text-main)' }}>{deleteModal.name}</span> de la liste. Les données restent conservées.
            </p>
            <p className="text-text-muted mt-4 text-xs font-bold uppercase tracking-widest">
              Tapez "{deleteModal.name}" pour confirmer
            </p>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder={deleteModal.name}
              className="w-full mt-2 border border-border-main rounded-xl p-3 text-sm bg-white/50 focus:outline-none focus:ring-2 focus:ring-red-500/30"
            />
            <div className="flex gap-4 mt-10">
              <button
                onClick={() => { setDeleteModal({ ...deleteModal, open: false }); setDeleteConfirmText(''); }}
                className="flex-1 py-4 bg-primary/5 hover:bg-primary/10 text-text-muted rounded-2xl font-bold transition-all active:scale-95"
              >
                Annuler
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteConfirmText.trim() !== deleteModal.name.trim()}
                className="flex-1 py-4 bg-red-500 hover:bg-red-600 disabled:bg-red-500/30 disabled:cursor-not-allowed text-white rounded-2xl font-bold shadow-lg shadow-red-500/20 transition-all active:scale-95"
              >
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pop-over d'intelligence au survol (Lazy loaded) */}
      {hoveredPatient && (
        <PatientSummaryHoverCard
          patientId={hoveredPatient.id}
          patientName={hoveredPatient.name}
          patientDossier={hoveredPatient.dossier}
          triggerRect={hoveredPatient.rect}
        />
      )}

      <CsvImportModal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        onSuccess={() => fetchPatients(true)}
      />
    </div>
  );
};
