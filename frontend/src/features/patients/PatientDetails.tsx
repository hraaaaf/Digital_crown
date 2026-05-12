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
  Target
} from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

import { CephaloWorkspace } from '../ortho/CephaloWorkspace';
import { PanoramicStudio } from '../panoramic/PanoramicStudio';
import { DocumentHub } from '../admin/DocumentHub';
import { PatientDocuments } from './PatientDocuments';
import { FlashSummary } from '../../components/clinical/FlashSummary';
import { QuickPayModal } from './components/QuickPayModal';
import { PatientScoreBadge } from './components/PatientScoreBadge';
import { Banknote } from 'lucide-react';

interface Patient {
  id: number;
  numero_dossier: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  telephone: string;
  assurance: string;
}

type TabType = 'radiology' | 'admin' | 'archives';

export const PatientDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = (searchParams.get('tab') as TabType) || 'admin';

  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingDoc, setEditingDoc] = useState<any>(null);
  const [radioTab, setRadioTab] = useState<'cephalo' | 'panoramic'>('cephalo');
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);

  useEffect(() => {
    const handleEditDoc = (e: any) => {
      setEditingDoc(e.detail);
      setSearchParams({ tab: 'admin' });
    };
    window.addEventListener('edit_document', handleEditDoc);
    return () => window.removeEventListener('edit_document', handleEditDoc);
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

  const handleTabChange = (tab: TabType) => {
    setSearchParams({ tab });
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center flex-col gap-6 bg-slate-50/50">
        <Loader2 className="w-14 h-14 animate-spin" style={{ color: 'var(--primary)' }} />
        <p className="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">
          Ouverture du dossier clinique...
        </p>
      </div>
    );
  }

  if (!patient) return null;

  const fullName = `${patient.nom.toUpperCase()} ${patient.prenom}`;
  const isCompact = activeTab === 'admin' || activeTab === 'archives';

  return (
    <div className={cn("flex flex-col bg-slate-50/30", isCompact ? "h-screen overflow-hidden" : "min-h-screen")}>
      
      <header className={cn(
        "sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-slate-200/60 transition-all duration-500",
        isCompact ? "pt-3 pb-0 shadow-sm" : "pt-8 pb-0 shadow-[0_4px_30px_rgba(0,0,0,0.03)]"
      )}>
        <div className="max-w-[1600px] mx-auto px-6 md:px-10">
          
          <div className={cn("flex items-center justify-between transition-all duration-500", isCompact ? "mb-2" : "mb-6")}>
            <div className="flex items-center gap-5">
              <button 
                onClick={() => navigate('/patients')}
                className={cn("bg-white border border-slate-200 text-slate-400 hover:border-primary flex items-center justify-center rounded-xl transition-all shadow-sm active:scale-95",
                  isCompact ? "w-8 h-8" : "w-12 h-12"
                )}
                style={{ color: 'var(--primary)' }}
              >
                <ArrowLeft size={isCompact ? 18 : 24} strokeWidth={2.5} />
              </button>
              
              <div>
                <h1 className={cn("font-black tracking-tight flex items-center gap-4 transition-all duration-500", isCompact ? "text-xl" : "text-3xl")} style={{ color: 'var(--primary)' }}>
                  {fullName}
                  <PatientScoreBadge patientId={Number(id)} />
                  {patient.assurance && patient.assurance !== 'AUCUNE' && (
                    <span className={cn(
                      "px-2.5 py-1 text-[10px] font-black rounded-lg uppercase tracking-widest border shadow-sm",
                      patient.assurance === 'CNOPS' ? "bg-blue-100 text-blue-700 border-blue-200" :
                      patient.assurance === 'CNSS' ? "bg-emerald-100 text-emerald-700 border-emerald-200" :
                      patient.assurance === 'MUTUELLE_FAR' ? "bg-purple-100 text-purple-700 border-purple-200" :
                      "bg-amber-100 text-amber-700 border-amber-200"
                    )}>
                      {patient.assurance === 'MUTUELLE_FAR' ? 'FAR' : patient.assurance}
                    </span>
                  )}
                  {!isCompact && (
                    <span className="px-2.5 py-1 bg-primary/5 text-primary text-[10px] font-black rounded-lg uppercase tracking-widest border border-primary/10 shadow-sm" style={{ color: 'var(--primary)' }}>
                      Dossier Actif
                    </span>
                  )}
                </h1>
                
                <div className={cn("flex items-center gap-6 mt-2 text-sm font-bold text-slate-500 transition-all duration-300", isCompact ? "hidden" : "opacity-100")}>
                  <div className="flex items-center gap-2 px-2 py-1 bg-white border border-slate-200/60 rounded-lg shadow-sm">
                    <FileDigit size={14} style={{ color: 'var(--primary)' }} />
                    <span className="font-mono" style={{ color: 'var(--primary)' }}>{patient.numero_dossier || `ID-${patient.id}`}</span>
                  </div>
                  <div className="flex items-center gap-2"><Calendar size={16} className="text-slate-400" /><span>{new Date(patient.date_naissance).toLocaleDateString('fr-FR')}</span></div>
                  <div className="flex items-center gap-2"><Phone size={16} className="text-slate-400" /><span>{patient.telephone}</span></div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Quick Pay Button */}
              <button
                onClick={() => setIsPayModalOpen(true)}
                className={cn("bg-white border border-slate-200 text-slate-700 hover:text-emerald-600 hover:border-emerald-200 hover:bg-emerald-50 rounded-[1.2rem] shadow-sm transition-all flex items-center justify-center group", isCompact ? "w-10 h-10" : "h-16 px-6")}
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
        
        {!isCompact && (
          <FlashSummary patientId={Number(id)} patientName={fullName} />
        )}

        <div className={cn("animate-in fade-in slide-in-from-bottom-8 duration-700 h-full", !isCompact && "delay-150")}>
          {activeTab === 'radiology' && (
            <div className="space-y-6">
              {/* Ghost Elite Toggle */}
              <div className="flex justify-center">
                <div className="inline-flex bg-slate-100/50 p-1.5 rounded-2xl border border-slate-200/60 shadow-inner">
                  <button 
                    onClick={() => setRadioTab('cephalo')}
                    className={cn(
                      "px-8 py-3 text-xs font-black uppercase tracking-[0.15em] rounded-xl transition-all duration-300 flex items-center gap-2", 
                      radioTab === 'cephalo' ? "bg-white text-indigo-600 shadow-md" : "text-slate-400 hover:text-slate-600"
                    )}
                  >
                    <Activity size={16} />
                    Céphalométrie COM
                  </button>
                  <button 
                    onClick={() => setRadioTab('panoramic')}
                    className={cn(
                      "px-8 py-3 text-xs font-black uppercase tracking-[0.15em] rounded-xl transition-all duration-300 flex items-center gap-2", 
                      radioTab === 'panoramic' ? "bg-white text-indigo-600 shadow-md" : "text-slate-400 hover:text-slate-600"
                    )}
                  >
                    <Target size={16} />
                    Panoramique DENTEX
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-[2.5rem] shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden min-h-[85vh]">
                {radioTab === 'cephalo' ? (
                  <CephaloWorkspace patientId={Number(id)} patientName={fullName} />
                ) : (
                  <PanoramicStudio patientId={Number(id)} patientName={fullName} />
                )}
              </div>
            </div>
          )}
          
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
        : "border-transparent text-slate-400 hover:text-slate-600 hover:border-slate-200"
    )}
    style={active ? { borderColor: 'var(--primary)', color: 'var(--primary)' } : {}}
  >
    {icon} {label}
  </button>
);
