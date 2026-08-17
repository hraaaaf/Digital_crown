import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Activity,
  FileText,
  ArrowLeft,
  User,
  Calendar,
  Phone,
  Loader2,
  Archive,
  FileDigit,
  Target,
  HeartPulse,
  Stethoscope,
  Mail,
  MapPin,
  AlertTriangle,
  RefreshCcw
} from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';
import toast from 'react-hot-toast';
import { parseMotifs, findMotifById } from '../../data/motifsDictionary';

import { CephaloWorkspace } from '../ortho/CephaloWorkspace';
import { PanoramicStudio } from '../panoramic/PanoramicStudio';
import { DocumentHub } from '../admin/DocumentHub';
import { PatientDocuments } from './PatientDocuments';
import { ClinicalHub } from './components/ClinicalHub';
import { PatientJourney } from './components/PatientJourney';
import { PatientFinances } from './components/PatientFinances';
import { FlashSummary } from '../../components/clinical/FlashSummary';
import { QuickPayModal } from './components/QuickPayModal';
import { usePatientStore } from '../../stores/usePatientStore';
import { useAuthStore } from '../../stores/useAuthStore';
import { EliteGhostLoader } from '../../components/EliteGhostLoader';
import { AssuranceBadge } from '../../components/AssuranceBadge';
import { Banknote } from 'lucide-react';

interface Patient {
  id: number;
  numero_dossier: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  telephone: string;
  telephone_2?: string;
  telephone_3?: string;
  email?: string;
  adresse?: string;
  assurance: string;
  assurance_privee_nom?: string;
  assurance_complementaire?: boolean;
  assurance_complementaire_nom?: string;
  antecedents_medicaux?: string;
  motif_consultation?: string;
  dossier?: {
    is_ortho_active: boolean;
  };
}

type TabType = 'tracking' | 'clinical' | 'radiology' | 'admin' | 'archives' | 'finances';

export const PatientDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = (searchParams.get('tab') as TabType) || 'tracking';

  // Permission « clinical » : le propriétaire (sans employer_id) passe toujours,
  // un sous-compte doit l'avoir explicitement (miroir de has_permission backend).
  const user = useAuthStore(state => state.user);
  const canClinical = !user?.employer_id || Boolean(user?.permissions?.clinical);

  const { editingDoc, setEditingDoc, patientsCache } = usePatientStore();
  const cachedPatient = patientsCache.find(p => String(p.id) === id);
  const [patient, setPatient] = useState<Patient | null>(cachedPatient ? { ...cachedPatient, assurance: cachedPatient.assurance } : null);
  const [loading, setLoading] = useState(!cachedPatient);
  const [fetchError, setFetchError] = useState(false);
  const radioTab = (searchParams.get('radioTab') as 'cephalo' | 'panoramic') || 'cephalo';
  const handleRadioTabChange = (v: 'cephalo' | 'panoramic') =>
    setSearchParams(prev => { const p = new URLSearchParams(prev); p.set('radioTab', v); return p; });
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);

  const lastEditingDoc = useRef(null);

  useEffect(() => {
    if (editingDoc && editingDoc !== lastEditingDoc.current) {
      setSearchParams(prev => {
        const p = new URLSearchParams(prev);
        p.set('tab', 'admin');
        return p;
      });
    }
    lastEditingDoc.current = editingDoc;
  }, [editingDoc, setSearchParams]);

  useEffect(() => {
    const handlePrescription = () => setSearchParams({ tab: 'admin' });
    window.addEventListener('perio-create-prescription', handlePrescription);
    return () => window.removeEventListener('perio-create-prescription', handlePrescription);
  }, [setSearchParams]);

  const fetchPatient = useCallback(async () => {
    if (!id) return;
    try {
      setFetchError(false);
      if (!cachedPatient) setLoading(true);
      const response = await api.get(`/patients/${id}`);
      setPatient(response.data);
    } catch (error) {
      console.error("❌ Erreur chargement patient:", error);
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  }, [id, cachedPatient]);

  useEffect(() => {
    fetchPatient();
  }, [fetchPatient]);

  useEffect(() => {
    if (!id) return;
    const timer = setTimeout(() => {
      api.get(`/intelligence/patient/${id}/nba`).then(res => {
        if (res.data.nba) {
          toast(`💡 ${res.data.nba.title} — ${res.data.nba.action}`, { duration: 6000 });
        }
      }).catch(() => {});
    }, 1500); // Délai pour ne pas spammer au chargement immédiat
    
    return () => clearTimeout(timer);
  }, [id]);

  // Garde-fou : l'onglet clinique peut être atteint via l'URL (?tab=clinical).
  // Sans la permission, on bascule sur le suivi pour éviter un onglet vide.
  useEffect(() => {
    if (!canClinical && activeTab === 'clinical') {
      setSearchParams({ tab: 'tracking' }, { replace: true });
    }
  }, [canClinical, activeTab, setSearchParams]);

  const activateOrtho = async () => {
    try {
      setLoading(true);
      await api.patch(`/patients/${id}/ortho`, { is_ortho_active: true });
      setPatient(prev => prev ? { ...prev, dossier: { ...prev.dossier, is_ortho_active: true } } : null);
      toast.success('Suivi orthodontique activé');
    } catch (err) {
      toast.error('Erreur lors de l\'activation');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab: TabType) => {
    setSearchParams({ tab });
  };

  if (loading) {
    return <EliteGhostLoader text="Ouverture du dossier clinique..." size="medium" />;
  }

  if (fetchError) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-[2rem] shadow-xl border border-slate-100 p-8 text-center space-y-6">
          <div className="w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto">
            <AlertTriangle size={40} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-800 mb-2">Impossible de charger le dossier</h1>
            <p className="text-slate-500 font-medium text-sm">Erreur réseau ou patient introuvable. Vérifiez votre connexion et réessayez.</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate('/patients')} className="flex-1 px-4 py-2.5 text-sm font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-all">Retour</button>
            <button onClick={() => fetchPatient()} className="flex-1 px-4 py-2.5 text-sm font-bold text-white bg-primary hover:bg-primary/90 rounded-lg transition-all flex items-center justify-center gap-2">
              <RefreshCcw size={16} /> Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!patient) return null;

  const fullName = `${patient.nom.toUpperCase()} ${patient.prenom}`;
  const isCompact = activeTab === 'admin' || activeTab === 'archives';

  return (
    <div className={cn("flex flex-col bg-transparent", isCompact ? "h-screen overflow-hidden" : "min-h-screen")}>
      
      <header className={cn(
        "sticky top-0 z-[300] bg-card-bg/80 backdrop-blur-xl border-b border-border-main transition-all duration-500",
        isCompact ? "pt-3 pb-0 shadow-elite" : "pt-8 pb-0 shadow-elite"
      )}>
        <div className="max-w-[1600px] mx-auto px-6 md:px-10">
          
          <div className={cn("flex items-center justify-between transition-all duration-500", isCompact ? "mb-2" : "mb-6")}>
            <div className="flex items-center gap-5">
              <button
                onClick={() => navigate('/patients')}
                className={cn("bg-card-bg border border-border-main text-text-muted hover:border-primary flex items-center justify-center rounded-xl transition-all shadow-sm active:scale-95",
                  isCompact ? "w-8 h-8" : "w-12 h-12"
                )}
                style={{ color: 'var(--primary)' }}
                aria-label="Retourner à la liste des patients"
              >
                <ArrowLeft size={isCompact ? 18 : 24} strokeWidth={2.5} />
              </button>
              
              <div>
                <div className="flex items-center gap-3">
                  <h1 className={cn("font-black tracking-tight flex items-center gap-4 transition-all duration-500", isCompact ? "text-xl" : "text-3xl")} style={{ color: 'var(--primary)' }}>
                    {fullName}
                  </h1>
                  <AssuranceBadge assurance={patient.assurance} size="full" hideWhenNone />
                  {!isCompact && (
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 bg-primary/5 text-primary text-[10px] font-black rounded-lg uppercase tracking-widest border border-primary/10 shadow-sm" style={{ color: 'var(--primary)' }}>
                        Dossier Actif
                      </span>
                      <button 
                        onClick={() => navigate(`/patients/${id}/edit`)}
                        className="px-3 py-1 bg-primary text-white text-[10px] font-black rounded-lg uppercase tracking-widest shadow-sm hover:opacity-90 transition-opacity"
                        style={{ backgroundColor: 'var(--primary)' }}
                      >
                        Modifier Dossier
                      </button>
                    </div>
                  )}
                </div>
                
                <div className={cn("flex flex-wrap items-center gap-4 mt-3 text-sm font-bold text-text-muted transition-all duration-300", isCompact ? "hidden" : "opacity-100")}>
                  <div className="flex items-center gap-2 px-2 py-1 bg-card-bg border border-border-main rounded-lg shadow-sm">
                    <FileDigit size={14} style={{ color: 'var(--primary)' }} />
                    <span className="font-mono" style={{ color: 'var(--primary)' }}>{patient.numero_dossier || `ID-${patient.id}`}</span>
                  </div>
                  <div className="flex items-center gap-2"><Calendar size={16} className="text-text-muted" /><span>{new Date(patient.date_naissance).toLocaleDateString('fr-FR')}</span></div>
                  <div className="flex items-center gap-2"><Phone size={16} className="text-text-muted" /><span>{patient.telephone}</span></div>
                  {patient.telephone_2 && <div className="flex items-center gap-2"><Phone size={16} className="text-text-muted" /><span>{patient.telephone_2}</span></div>}
                  {patient.telephone_3 && <div className="flex items-center gap-2"><Phone size={16} className="text-text-muted" /><span>{patient.telephone_3}</span></div>}
                  {patient.email && <div className="flex items-center gap-2"><Mail size={16} className="text-text-muted" /><span>{patient.email}</span></div>}
                  {patient.adresse && <div className="flex items-center gap-2"><MapPin size={16} className="text-text-muted" /><span>{patient.adresse}</span></div>}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/agenda', {
                  state: { prefillPatientId: patient.id, prefillPatientNom: patient.nom, prefillPatientPrenom: patient.prenom }
                })}
                className={cn("bg-card-bg border border-border-main text-text-muted hover:text-primary hover:border-primary/30 hover:bg-primary/5 rounded-[1.2rem] shadow-sm transition-all flex items-center justify-center group", isCompact ? "w-10 h-10" : "h-16 px-6")}
              >
                <Calendar size={isCompact ? 18 : 24} className="group-active:scale-95 transition-transform" />
                {!isCompact && <span className="ml-3 font-black uppercase tracking-widest text-[11px]">Prendre RDV</span>}
              </button>

              <button
                onClick={() => setIsPayModalOpen(true)}
                className={cn("bg-card-bg border border-border-main text-text-muted hover:text-emerald-500 hover:border-emerald-500/30 hover:bg-emerald-500/5 rounded-[1.2rem] shadow-sm transition-all flex items-center justify-center group", isCompact ? "w-10 h-10" : "h-16 px-6")}
              >
                <Banknote size={isCompact ? 18 : 24} className="group-active:scale-95 transition-transform" />
                {!isCompact && <span className="ml-3 font-black uppercase tracking-widest text-[11px]">Encaisser</span>}
              </button>

              <div className={cn("rounded-[1.2rem] text-white shadow-xl transition-all duration-500 flex items-center justify-center", isCompact ? "w-10 h-10" : "w-16 h-16")} style={{ backgroundColor: 'var(--primary)', boxShadow: '0 10px 30px -10px var(--primary)' }}>
                <User size={isCompact ? 20 : 30} strokeWidth={2} />
              </div>
            </div>
          </div>

          <div data-tour="patient-tabs" className="flex gap-10 border-b border-transparent -mb-[1px]">
            <TabButton active={activeTab === 'tracking'} onClick={() => handleTabChange('tracking')} icon={<Calendar size={18} />} label="Séances & Suivi" />
            {canClinical && <TabButton active={activeTab === 'clinical'} onClick={() => handleTabChange('clinical')} icon={<Stethoscope size={18} />} label="Examen Clinique" />}
            <TabButton active={activeTab === 'radiology'} onClick={() => handleTabChange('radiology')} icon={<Activity size={18} />} label="Radiologie (IA)" />
            <TabButton active={activeTab === 'admin'} onClick={() => handleTabChange('admin')} icon={<FileText size={18} />} label="Documents A5" />
            <TabButton active={activeTab === 'archives'} onClick={() => handleTabChange('archives')} icon={<Archive size={18} />} label="Archives & Historique" />
            <TabButton active={activeTab === 'finances'} onClick={() => handleTabChange('finances')} icon={<Banknote size={18} />} label="Finances" />
          </div>
        </div>
      </header>

      <main className={cn(
        "max-w-[1600px] mx-auto w-full transition-all duration-500",
        isCompact ? "flex-1 h-[calc(100vh-90px)] px-4 py-4 md:px-8 md:py-6" : "flex-1 px-10 py-10 space-y-10"
      )}>
        
        
        {!isCompact && (patient.antecedents_medicaux || patient.motif_consultation) && (
          <div className="flex flex-col gap-3 animate-in fade-in slide-in-from-top-4 duration-500">
            {patient.antecedents_medicaux && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-start gap-3 text-red-700 shadow-sm">
                <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-black text-sm uppercase tracking-widest mb-1">Antécédents Médicaux</h4>
                  <p className="text-sm font-medium whitespace-pre-wrap">{patient.antecedents_medicaux}</p>
                </div>
              </div>
            )}
            {patient.motif_consultation && (
              <div className="p-4 bg-blue-50 border border-blue-100 rounded-2xl flex items-start gap-3 text-blue-800 shadow-sm">
                <Activity className="w-5 h-5 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-black text-sm uppercase tracking-widest mb-2">Motif de Consultation Initial</h4>
                  <div className="flex flex-wrap gap-2">
                    {parseMotifs(patient.motif_consultation).map(motifId => {
                      const motif = findMotifById(motifId);
                      if (!motif) return null;
                      const isUrgent = motif.urgency === 'urgence';
                      return (
                        <div
                          key={motifId}
                          className={cn(
                            'inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold tracking-wider',
                            isUrgent
                              ? 'bg-red-100 text-red-700 border border-red-200'
                              : 'bg-blue-100 text-blue-700 border border-blue-200'
                          )}
                        >
                          {motif.label}
                          {isUrgent && <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse" />}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <FlashSummary patientId={Number(id)} patientName={fullName} />

        <div className={cn("animate-in fade-in slide-in-from-bottom-8 duration-700 h-full", !isCompact && "delay-150")}>
          {activeTab === 'radiology' && (
            <div className="space-y-6">
              {/* Ghost Elite Toggle */}
              <div className="flex justify-center">
                <div className="inline-flex bg-card-bg/50 p-1.5 rounded-2xl border border-border-main shadow-inner">
                  <button 
                    onClick={() => handleRadioTabChange('cephalo')}
                    className={cn(
                      "px-8 py-3 text-xs font-black uppercase tracking-[0.15em] rounded-xl transition-all duration-300 flex items-center gap-2", 
                      radioTab === 'cephalo' ? "bg-card-bg text-primary shadow-elite" : "text-text-muted hover:text-main"
                    )}
                  >
                    <Activity size={16} />
                    Céphalométrie COM
                  </button>
                  <button 
                    onClick={() => handleRadioTabChange('panoramic')}
                    className={cn(
                      "px-8 py-3 text-xs font-black uppercase tracking-[0.15em] rounded-xl transition-all duration-300 flex items-center gap-2", 
                      radioTab === 'panoramic' ? "bg-card-bg text-primary shadow-elite" : "text-text-muted hover:text-main"
                    )}
                  >
                    <Target size={16} />
                    Panoramique DENTEX
                  </button>
                </div>
              </div>

              <div className="bg-card-bg rounded-[2.5rem] shadow-elite border border-border-main overflow-hidden min-h-[85vh]">
                {radioTab === 'cephalo' ? (
                  patient?.dossier?.is_ortho_active ? (
                    <CephaloWorkspace patientId={Number(id)} patientName={fullName} />
                  ) : (
                    <div className="flex flex-col items-center justify-center h-[60vh] text-center p-10">
                      <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mb-6">
                        <Activity className="w-12 h-12 text-slate-400" />
                      </div>
                      <h3 className="text-2xl font-black text-slate-800 mb-2">Module Céphalométrique Verrouillé</h3>
                      <p className="text-slate-500 mb-8 max-w-md">Ce module nécessite que le suivi orthodontique soit actif pour ce patient afin de permettre les tracés COM.</p>
                      <button 
                        onClick={activateOrtho}
                        className="px-8 py-4 bg-[#003380] text-white font-bold rounded-2xl hover:bg-[#002266] transition-all shadow-lg flex items-center gap-3"
                      >
                        <Target className="w-5 h-5" />
                        Activer le Suivi Orthodontique
                      </button>
                    </div>
                  )
                ) : (
                  <PanoramicStudio patientId={Number(id)} patientName={fullName} />
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'tracking' && <PatientJourney patientId={Number(id)} />}
          
          {activeTab === 'clinical' && <ClinicalHub patientId={Number(id)} />}

          {activeTab === 'admin' && (
            <DocumentHub patientId={id!} patientName={fullName} editData={editingDoc} />
          )}

          {activeTab === 'archives' && (
            <PatientDocuments />
          )}

          {activeTab === 'finances' && (
            <PatientFinances patientId={Number(id)} />
          )}
        </div>
      </main>

      <QuickPayModal 
        isOpen={isPayModalOpen} 
        onClose={() => setIsPayModalOpen(false)} 
        patientId={Number(id)} 
      />
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label }: any) => (
  <button
    onClick={onClick}
    className={cn(
      "flex items-center gap-2 pb-3 px-2 text-[12px] font-black uppercase tracking-[0.1em] transition-all border-b-4",
      active 
        ? "text-primary" 
        : "border-transparent text-text-muted hover:text-main hover:border-border-main"
    )}
    style={active ? { borderColor: 'var(--primary)', color: 'var(--primary)' } : {}}
  >
    {icon} {label}
  </button>
);
