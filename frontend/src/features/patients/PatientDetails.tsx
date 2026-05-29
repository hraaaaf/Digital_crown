import { useState, useEffect } from 'react';
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
  Stethoscope
} from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';
import toast from 'react-hot-toast';

import { CephaloWorkspace } from '../ortho/CephaloWorkspace';
import { PanoramicStudio } from '../panoramic/PanoramicStudio';
import { DocumentHub } from '../admin/DocumentHub';
import { PatientDocuments } from './PatientDocuments';
import { ClinicalHub } from './components/ClinicalHub';
import { FlashSummary } from '../../components/clinical/FlashSummary';
import { QuickPayModal } from './components/QuickPayModal';
import { PatientScoreBadge } from './components/PatientScoreBadge';
import { useSettingsStore } from '../admin/Settings/hooks/useSettingsStore';
import { usePatientStore } from '../../stores/usePatientStore';
import { Banknote } from 'lucide-react';

interface Patient {
  id: number;
  numero_dossier: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  telephone: string;
  assurance: string;
  adresse?: string;
  dossier?: {
    is_ortho_active: boolean;
  };
}

type TabType = 'clinical' | 'radiology' | 'admin' | 'archives';

export const PatientDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = (searchParams.get('tab') as TabType) || 'admin';
  const show_patient_badges = useSettingsStore(state => state.profile.show_patient_badges);

  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const { editingDoc, setEditingDoc } = usePatientStore();
  const radioTab = (searchParams.get('radioTab') as 'cephalo' | 'panoramic') || 'cephalo';
  const handleRadioTabChange = (v: 'cephalo' | 'panoramic') =>
    setSearchParams(prev => { const p = new URLSearchParams(prev); p.set('radioTab', v); return p; });
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);

  useEffect(() => {
    if (editingDoc) {
      setSearchParams({ tab: 'admin' });
    }
  }, [editingDoc, setSearchParams]);

  useEffect(() => {
    const handlePrescription = () => setSearchParams({ tab: 'admin' });
    window.addEventListener('perio-create-prescription', handlePrescription);
    return () => window.removeEventListener('perio-create-prescription', handlePrescription);
  }, [setSearchParams]);

  useEffect(() => {
    const fetchPatient = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const response = await api.get(`/patients/${id}`);
        setPatient(response.data);
      } catch (error) {
        console.error("❌ Erreur chargement patient:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPatient();
  }, [id]);

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
    return (
      <div className="flex h-screen items-center justify-center flex-col gap-6 bg-transparent">
        <Loader2 className="w-14 h-14 animate-spin" style={{ color: 'var(--primary)' }} />
        <p className="text-text-muted font-black uppercase tracking-[0.2em] text-[10px]">
          Ouverture du dossier clinique...
        </p>
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
              >
                <ArrowLeft size={isCompact ? 18 : 24} strokeWidth={2.5} />
              </button>
              
              <div>
                <div className="flex items-center gap-3">
                  <h1 className={cn("font-black tracking-tight flex items-center gap-4 transition-all duration-500", isCompact ? "text-xl" : "text-3xl")} style={{ color: 'var(--primary)' }}>
                    {fullName}
                  </h1>
                  {show_patient_badges && <PatientScoreBadge patientId={Number(id)} />}
                  {patient.assurance && patient.assurance !== 'AUCUNE' && (
                    <span className={cn(
                      "px-2.5 py-1 text-[10px] font-black rounded-lg uppercase tracking-widest border shadow-sm",
                      patient.assurance === 'CNOPS' ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                      patient.assurance === 'CNSS' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                      patient.assurance === 'MUTUELLE_FAR' ? "bg-purple-500/10 text-purple-400 border-purple-500/20" :
                      "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    )}>
                      {patient.assurance === 'MUTUELLE_FAR' ? 'FAR' : patient.assurance}
                    </span>
                  )}
                  {!isCompact && (
                    <span className="px-2.5 py-1 bg-primary/5 text-primary text-[10px] font-black rounded-lg uppercase tracking-widest border border-primary/10 shadow-sm" style={{ color: 'var(--primary)' }}>
                      Dossier Actif
                    </span>
                  )}
                </div>
                
                <div className={cn("flex items-center gap-6 mt-2 text-sm font-bold text-text-muted transition-all duration-300", isCompact ? "hidden" : "opacity-100")}>
                  <div className="flex items-center gap-2 px-2 py-1 bg-card-bg border border-border-main rounded-lg shadow-sm">
                    <FileDigit size={14} style={{ color: 'var(--primary)' }} />
                    <span className="font-mono" style={{ color: 'var(--primary)' }}>{patient.numero_dossier || `ID-${patient.id}`}</span>
                  </div>
                  <div className="flex items-center gap-2"><Calendar size={16} className="text-text-muted" /><span>{new Date(patient.date_naissance).toLocaleDateString('fr-FR')}</span></div>
                  <div className="flex items-center gap-2"><Phone size={16} className="text-text-muted" /><span>{patient.telephone}</span></div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
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
            <TabButton active={activeTab === 'clinical'} onClick={() => handleTabChange('clinical')} icon={<Stethoscope size={18} />} label="Examen Clinique" />
            <TabButton active={activeTab === 'radiology'} onClick={() => handleTabChange('radiology')} icon={<Activity size={18} />} label="Radiologie (IA)" />
            <TabButton active={activeTab === 'admin'} onClick={() => handleTabChange('admin')} icon={<FileText size={18} />} label="Documents A5" />
            <TabButton active={activeTab === 'archives'} onClick={() => handleTabChange('archives')} icon={<Archive size={18} />} label="Archives & Historique" />
          </div>
        </div>
      </header>

      <main className={cn(
        "max-w-[1600px] mx-auto w-full transition-all duration-500",
        isCompact ? "flex-1 h-[calc(100vh-90px)] px-4 py-4 md:px-8 md:py-6" : "flex-1 px-10 py-10 space-y-10"
      )}>
        
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
          
          {activeTab === 'clinical' && <ClinicalHub patientId={Number(id)} />}

          {activeTab === 'admin' && (
            <DocumentHub patientId={id!} patientName={fullName} editData={editingDoc} />
          )}

          {activeTab === 'archives' && (
            <PatientDocuments />
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
