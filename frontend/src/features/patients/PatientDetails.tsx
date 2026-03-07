import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Activity, 
  FileText, 
  ArrowLeft, 
  User, 
  Calendar, 
  Phone, 
  Hash,
  Loader2,
  Info,
  ClipboardList,
  History,
  Archive
} from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

import { CephaloWorkspace } from '../ortho/CephaloWorkspace';
import { DocumentHub } from '../admin/DocumentHub';
import { PatientDocuments } from './PatientDocuments';

interface Patient {
  id: number;
  nom: string;
  prenom: string;
  date_naissance: string;
  telephone: string;
}

type TabType = 'analysis' | 'admin' | 'archives';

export const PatientDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  // Rigueur CTO : L'URL est la SEULE source de vérité. Suppression du useState local redondant.
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = (searchParams.get('tab') as TabType) || 'admin';

  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

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

  // Synchronisation montante directe : Clic -> URL -> Re-render naturel
  const handleTabChange = (tab: TabType) => {
    setSearchParams({ tab });
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center flex-col gap-6 bg-slate-50/50">
        <Loader2 className="w-14 h-14 text-[#003380] animate-spin" />
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
                className={cn("bg-white border border-slate-200 text-slate-400 hover:text-[#003380] hover:border-[#003380] flex items-center justify-center rounded-xl transition-all shadow-sm active:scale-95",
                  isCompact ? "w-8 h-8" : "w-12 h-12"
                )}
              >
                <ArrowLeft size={isCompact ? 18 : 24} strokeWidth={2.5} />
              </button>
              
              <div>
                <h1 className={cn("font-black text-[#003380] tracking-tight flex items-center gap-4 transition-all duration-500", isCompact ? "text-xl" : "text-3xl")}>
                  {fullName}
                  {!isCompact && (
                    <span className="px-2.5 py-1 bg-blue-50 text-[#003380] text-[10px] font-black rounded-lg uppercase tracking-widest border border-blue-100 shadow-sm">
                      Dossier Actif
                    </span>
                  )}
                </h1>
                
                <div className={cn("flex items-center gap-6 mt-2 text-sm font-bold text-slate-500 transition-all duration-300", isCompact ? "hidden" : "opacity-100")}>
                  <div className="flex items-center gap-2 px-2 py-1 bg-white border border-slate-200/60 rounded-lg shadow-sm">
                    <Hash size={14} className="text-[#003380]" />
                    <span className="font-mono text-[#003380]">ID-{patient.id}</span>
                  </div>
                  <div className="flex items-center gap-2"><Calendar size={16} className="text-slate-400" /><span>{new Date(patient.date_naissance).toLocaleDateString('fr-FR')}</span></div>
                  <div className="flex items-center gap-2"><Phone size={16} className="text-slate-400" /><span>{patient.telephone}</span></div>
                </div>
              </div>
            </div>
            
            <div className={cn("rounded-[1.2rem] bg-gradient-to-br from-[#003380] to-blue-900 border border-blue-800 flex items-center justify-center text-white shadow-xl shadow-[#003380]/20 transition-all duration-500", isCompact ? "w-10 h-10" : "w-16 h-16")}>
              <User size={isCompact ? 20 : 30} strokeWidth={2} />
            </div>
          </div>

          <div className="flex gap-10 border-b border-transparent -mb-[1px]">
            <TabButton active={activeTab === 'analysis'} onClick={() => handleTabChange('analysis')} icon={<Activity size={18} />} label="Céphalométrie" />
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <InfoCard icon={<Info size={22} />} title="État Administratif" content="Dossier validé pour la facturation." color="bg-blue-50 text-[#003380]" />
            <InfoCard icon={<ClipboardList size={22} />} title="Antécédents Ortho" content="Module Céphalométrique activé." color="bg-rose-50 text-rose-600" />
            <InfoCard icon={<History size={22} />} title="Historique" content="Suivi des consultations archivé." color="bg-emerald-50 text-emerald-600" />
          </div>
        )}

        <div className={cn("animate-in fade-in slide-in-from-bottom-8 duration-700 h-full", !isCompact && "delay-150")}>
          {activeTab === 'analysis' && (
            <div className="bg-white rounded-[2.5rem] shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden min-h-[85vh]">
              <CephaloWorkspace 
                patientId={Number(id)} 
                patientName={fullName}
              />
            </div>
          )}
          
          {activeTab === 'admin' && (
            <DocumentHub patientId={id} patientName={fullName} />
          )}

          {activeTab === 'archives' && (
            <PatientDocuments />
          )}
        </div>
      </main>
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label }: any) => (
  <button
    onClick={onClick}
    className={cn(
      "flex items-center gap-2 pb-3 px-2 text-[12px] font-black uppercase tracking-[0.1em] transition-all border-b-4",
      active 
        ? "border-[#003380] text-[#003380]" 
        : "border-transparent text-slate-400 hover:text-slate-600 hover:border-slate-200"
    )}
  >
    {icon} {label}
  </button>
);

const InfoCard = ({ icon, title, content, color }: any) => (
  <div className="bg-white/80 backdrop-blur-md border border-slate-200/60 p-6 rounded-[2rem] shadow-sm flex items-center gap-4 hover:shadow-md transition-all">
    <div className={cn("p-4 rounded-2xl", color)}>{icon}</div>
    <div>
      <h3 className="font-black text-slate-800 text-lg tracking-tight">{title}</h3>
      <p className="text-slate-500 text-xs font-medium mt-1 leading-snug">{content}</p>
    </div>
  </div>
);