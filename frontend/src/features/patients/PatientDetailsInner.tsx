import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Activity,
  FileText,
  ArrowLeft,
  Calendar,
  Phone,
  FileDigit,
  Target,
  Stethoscope,
  Mail,
  AlertTriangle,
  RefreshCcw,
  Plus,
  History,
  Banknote,
  Image,
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
import { PatientRvgPanel } from './components/PatientRvgPanel';
import { FlashSummary } from '../../components/clinical/FlashSummary';
import { QuickPayModal } from './components/QuickPayModal';
import { usePatientStore } from '../../stores/usePatientStore';
import { useAuthStore } from '../../stores/useAuthStore';
import { EliteGhostLoader } from '../../components/EliteGhostLoader';
import { AssuranceBadge } from '../../components/AssuranceBadge';

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
type RadioTab = 'rvg' | 'panoramic' | 'cephalo';

const userRoleValue = (role: unknown): string => {
  if (!role) return '';
  if (typeof role === 'string') return role;
  if (typeof role === 'object' && role !== null && 'value' in role) {
    return String((role as { value?: unknown }).value || '');
  }
  return '';
};

export const PatientDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = (searchParams.get('tab') as TabType) || 'tracking';

  const user = useAuthStore(state => state.user);
  const role = userRoleValue(user?.role);
  const userPermissions = user?.permissions || {};
  const hasExplicitPermissions = Object.keys(userPermissions).length > 0;
  const ownerOrAdmin = Boolean(user && (role === 'ADMIN' || (role === 'DENTISTE' && !user.employer_id)));
  const canClinical = ownerOrAdmin || Boolean(userPermissions.clinical === true);
  const legacyDentistEmployee = Boolean(user?.employer_id && role === 'DENTISTE' && !hasExplicitPermissions);
  const canPanoramic = ownerOrAdmin || legacyDentistEmployee || Boolean(hasExplicitPermissions && userPermissions.panoramic === true);
  const canCephalo = ownerOrAdmin || legacyDentistEmployee || Boolean(hasExplicitPermissions && userPermissions.cephalo === true);
  const availableRadioTabs: RadioTab[] = [
    'rvg',
    ...(canPanoramic ? ['panoramic' as const] : []),
    ...(canCephalo ? ['cephalo' as const] : []),
  ];

  const requestedRadioTab = (searchParams.get('radioTab') as RadioTab | null) || 'rvg';
  const radioTab: RadioTab = availableRadioTabs.includes(requestedRadioTab) ? requestedRadioTab : availableRadioTabs[0];
  const handleRadioTabChange = (value: RadioTab) => {
    if (!availableRadioTabs.includes(value)) return;
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set('radioTab', value);
      return next;
    });
  };

  const { editingDoc, patientsCache } = usePatientStore();
  const cachedPatient = patientsCache.find(p => String(p.id) === id);
  const [patient, setPatient] = useState<Patient | null>(cachedPatient ? { ...cachedPatient, assurance: cachedPatient.assurance } : null);
  const [loading, setLoading] = useState(!cachedPatient);
  const [fetchError, setFetchError] = useState(false);
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);
  const lastEditingDoc = useRef(null);

  useEffect(() => {
    if (requestedRadioTab !== radioTab && activeTab === 'radiology') {
      setSearchParams(prev => {
        const next = new URLSearchParams(prev);
        next.set('radioTab', radioTab);
        return next;
      }, { replace: true });
    }
  }, [requestedRadioTab, radioTab, activeTab, setSearchParams]);

  useEffect(() => {
    if (editingDoc && editingDoc !== lastEditingDoc.current) {
      setSearchParams(prev => {
        const next = new URLSearchParams(prev);
        next.set('tab', 'admin');
        return next;
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
      console.error('❌ Erreur chargement patient:', error);
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
        if (res.data.nba) toast(`💡 ${res.data.nba.title} — ${res.data.nba.action}`, { duration: 6000 });
      }).catch(() => {});
    }, 1500);
    return () => clearTimeout(timer);
  }, [id]);

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
    } catch {
      toast.error("Erreur lors de l'activation");
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab: TabType) => setSearchParams({ tab });

  if (loading) return <EliteGhostLoader text="Ouverture du dossier clinique..." size="medium" />;

  if (fetchError) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-[2rem] shadow-xl border border-slate-100 p-8 text-center space-y-6">
          <div className="w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto"><AlertTriangle size={40} /></div>
          <div>
            <h1 className="text-2xl font-black text-slate-800 mb-2">Impossible de charger le dossier</h1>
            <p className="text-slate-500 font-medium text-sm">Erreur réseau ou patient introuvable. Vérifiez votre connexion et réessayez.</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate('/patients')} className="flex-1 px-4 py-2.5 text-sm font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-all">Retour</button>
            <button onClick={() => fetchPatient()} className="flex-1 px-4 py-2.5 text-sm font-bold text-white bg-primary hover:bg-primary/90 rounded-lg transition-all flex items-center justify-center gap-2"><RefreshCcw size={16} /> Réessayer</button>
          </div>
        </div>
      </div>
    );
  }

  if (!patient) return null;

  const fullName = `${patient.nom.toUpperCase()} ${patient.prenom}`;
  const isDocuments = activeTab === 'admin' || activeTab === 'archives';
  const documentView = activeTab === 'archives' ? 'history' : 'create';
  const birthDate = new Date(patient.date_naissance);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const birthdayPending = today.getMonth() < birthDate.getMonth() || (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate());
  if (birthdayPending) age -= 1;
  const birthLabel = Number.isNaN(birthDate.getTime()) ? patient.date_naissance : birthDate.toLocaleDateString('fr-FR');

  return (
    <div className={cn('flex flex-col bg-transparent', isDocuments ? 'h-screen overflow-hidden' : 'min-h-screen')}>
      <header className="sticky top-0 z-[300] bg-card-bg/90 backdrop-blur-xl border-b border-border-main shadow-elite">
        <div className="max-w-[1600px] mx-auto px-4 md:px-8 pt-3">
          <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-3 mb-3">
            <div className="flex items-start sm:items-center gap-3 min-w-0">
              <button onClick={() => navigate('/patients')} className="w-10 h-10 shrink-0 bg-card-bg border border-border-main flex items-center justify-center rounded-xl shadow-sm active:scale-95 transition-all" style={{ color: 'var(--primary)' }} aria-label="Retourner à la liste des patients"><ArrowLeft size={20} strokeWidth={2.5} /></button>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="font-black tracking-tight text-xl md:text-2xl truncate" style={{ color: 'var(--primary)' }}>{fullName}</h1>
                  <AssuranceBadge assurance={patient.assurance} size="full" hideWhenNone />
                  {patient.antecedents_medicaux && <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-red-50 border border-red-200 text-red-700 text-[10px] font-black uppercase tracking-wide"><AlertTriangle size={12} /> Alerte médicale</span>}
                  <button onClick={() => navigate(`/patients/${id}/edit`)} className="px-2.5 py-1 text-[10px] font-black uppercase tracking-widest rounded-lg border border-primary/15 bg-primary/5 hover:bg-primary/10 transition-colors" style={{ color: 'var(--primary)' }}>Modifier</button>
                </div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-xs font-bold text-text-muted">
                  <span className="inline-flex items-center gap-1.5"><FileDigit size={13} style={{ color: 'var(--primary)' }} /><span className="font-mono" style={{ color: 'var(--primary)' }}>{patient.numero_dossier || `ID-${patient.id}`}</span></span>
                  <span>{age >= 0 && age < 130 ? `${age} ans · ` : ''}{birthLabel}</span>
                  <span className="inline-flex items-center gap-1.5"><Phone size={13} />{patient.telephone}</span>
                  {patient.email && <span className="hidden md:inline-flex items-center gap-1.5"><Mail size={13} />{patient.email}</span>}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 w-full xl:w-auto" aria-label="Actions rapides patient">
              <QuickAction icon={<Calendar size={18} />} label="RDV" onClick={() => navigate('/agenda', { state: { prefillPatientId: patient.id, prefillPatientNom: patient.nom, prefillPatientPrenom: patient.prenom } })} />
              <QuickAction icon={<Stethoscope size={18} />} label={canClinical ? 'Examen' : 'Suivi'} onClick={() => handleTabChange(canClinical ? 'clinical' : 'tracking')} />
              <QuickAction icon={<FileText size={18} />} label="Document" onClick={() => handleTabChange('admin')} />
              <QuickAction icon={<Banknote size={18} />} label="Encaisser" onClick={() => setIsPayModalOpen(true)} accent="emerald" />
            </div>
          </div>

          <div data-tour="patient-tabs" className="flex gap-1 sm:gap-3 overflow-x-auto border-b border-transparent -mb-[1px] scrollbar-none">
            <TabButton active={activeTab === 'tracking'} onClick={() => handleTabChange('tracking')} icon={<Calendar size={17} />} label="Vue d’ensemble" />
            {canClinical && <TabButton active={activeTab === 'clinical'} onClick={() => handleTabChange('clinical')} icon={<Stethoscope size={17} />} label="Clinique" />}
            <TabButton active={activeTab === 'radiology'} onClick={() => handleTabChange('radiology')} icon={<Activity size={17} />} label="Imagerie" />
            <TabButton active={isDocuments} onClick={() => handleTabChange('admin')} icon={<FileText size={17} />} label="Documents" />
            <TabButton active={activeTab === 'finances'} onClick={() => handleTabChange('finances')} icon={<Banknote size={17} />} label="Finances" />
          </div>
        </div>
      </header>

      <main className={cn('max-w-[1600px] mx-auto w-full transition-all duration-500', isDocuments ? 'flex-1 min-h-0 px-3 py-3 md:px-6 md:py-4' : 'flex-1 px-4 py-6 md:px-8 md:py-8 space-y-6')}>
        {!isDocuments && (patient.antecedents_medicaux || patient.motif_consultation) && (
          <div className="flex flex-col gap-3 animate-in fade-in slide-in-from-top-4 duration-500">
            {patient.antecedents_medicaux && <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-start gap-3 text-red-700 shadow-sm"><AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" /><div><h4 className="font-black text-sm uppercase tracking-widest mb-1">Antécédents Médicaux</h4><p className="text-sm font-medium whitespace-pre-wrap">{patient.antecedents_medicaux}</p></div></div>}
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
                      return <div key={motifId} className={cn('inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold tracking-wider', isUrgent ? 'bg-red-100 text-red-700 border border-red-200' : 'bg-blue-100 text-blue-700 border border-blue-200')}>{motif.label}{isUrgent && <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse" />}</div>;
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'tracking' && <FlashSummary patientId={Number(id)} patientName={fullName} />}

        <div className={cn('animate-in fade-in slide-in-from-bottom-8 duration-700 h-full', !isDocuments && 'delay-150')}>
          {activeTab === 'radiology' && (
            <div className="space-y-6">
              <div className="flex justify-center">
                <div className="inline-flex max-w-full overflow-x-auto bg-card-bg/50 p-1.5 rounded-2xl border border-border-main shadow-inner" aria-label="Modalités d’imagerie">
                  <ImagingButton active={radioTab === 'rvg'} onClick={() => handleRadioTabChange('rvg')} icon={<Image size={16} />} label="RVG" />
                  {canPanoramic && <ImagingButton active={radioTab === 'panoramic'} onClick={() => handleRadioTabChange('panoramic')} icon={<Target size={16} />} label="Panoramique" />}
                  {canCephalo && <ImagingButton active={radioTab === 'cephalo'} onClick={() => handleRadioTabChange('cephalo')} icon={<Activity size={16} />} label="Céphalométrie" />}
                </div>
              </div>

              <div className="bg-card-bg rounded-[2.5rem] shadow-elite border border-border-main overflow-hidden min-h-[70vh] p-3 sm:p-5 min-w-0">
                {radioTab === 'rvg' && <PatientRvgPanel patientId={Number(id)} />}
                {radioTab === 'panoramic' && canPanoramic && <PanoramicStudio patientId={Number(id)} patientName={fullName} />}
                {radioTab === 'cephalo' && canCephalo && (
                  patient?.dossier?.is_ortho_active ? (
                    <CephaloWorkspace patientId={Number(id)} patientName={fullName} />
                  ) : (
                    <div className="flex flex-col items-center justify-center h-[60vh] text-center p-6 sm:p-10">
                      <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mb-6"><Activity className="w-12 h-12 text-slate-400" /></div>
                      <h3 className="text-2xl font-black text-slate-800 mb-2">Module Céphalométrique Verrouillé</h3>
                      <p className="text-slate-500 mb-8 max-w-md">Ce module nécessite que le suivi orthodontique soit actif pour ce patient afin de permettre les tracés céphalométriques.</p>
                      <button onClick={activateOrtho} className="px-8 py-4 bg-[#003380] text-white font-bold rounded-2xl hover:bg-[#002266] transition-all shadow-lg flex items-center gap-3"><Target className="w-5 h-5" /> Activer le Suivi Orthodontique</button>
                    </div>
                  )
                )}
              </div>
            </div>
          )}

          {activeTab === 'tracking' && <PatientJourney patientId={Number(id)} />}
          {activeTab === 'clinical' && <ClinicalHub patientId={Number(id)} />}

          {isDocuments && (
            <div className="h-full min-h-0 flex flex-col gap-3">
              <div className="shrink-0 flex items-center justify-center">
                <div className="inline-flex p-1 rounded-xl bg-card-bg border border-border-main shadow-sm">
                  <button onClick={() => handleTabChange('admin')} className={cn('px-4 py-2 rounded-lg text-xs font-black flex items-center gap-2 transition-all', documentView === 'create' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-main')}><Plus size={15} /> Créer</button>
                  <button onClick={() => handleTabChange('archives')} className={cn('px-4 py-2 rounded-lg text-xs font-black flex items-center gap-2 transition-all', documentView === 'history' ? 'bg-primary text-white shadow-sm' : 'text-text-muted hover:text-main')}><History size={15} /> Historique</button>
                </div>
              </div>
              <div className="flex-1 min-h-0">
                {documentView === 'create' ? <DocumentHub patientId={id!} patientName={fullName} editData={editingDoc} /> : <PatientDocuments />}
              </div>
            </div>
          )}

          {activeTab === 'finances' && <PatientFinances patientId={Number(id)} />}
        </div>
      </main>

      <QuickPayModal isOpen={isPayModalOpen} onClose={() => setIsPayModalOpen(false)} patientId={Number(id)} />
    </div>
  );
};

const QuickAction = ({ icon, label, onClick, accent = 'primary' }: any) => (
  <button onClick={onClick} aria-label={label} className={cn('h-11 sm:h-10 min-w-0 px-1 sm:px-3 rounded-xl border border-border-main bg-card-bg shadow-sm transition-all flex flex-col sm:flex-row items-center justify-center gap-0.5 sm:gap-2 active:scale-95', accent === 'emerald' ? 'text-text-muted hover:text-emerald-600 hover:border-emerald-500/30 hover:bg-emerald-500/5' : 'text-text-muted hover:text-primary hover:border-primary/30 hover:bg-primary/5')}>
    {icon}<span className="inline text-[8px] sm:text-[10px] leading-none font-black uppercase tracking-[0.04em] sm:tracking-widest whitespace-nowrap">{label}</span>
  </button>
);

const TabButton = ({ active, onClick, icon, label }: any) => (
  <button onClick={onClick} className={cn('shrink-0 flex items-center gap-2 pb-2.5 px-2 md:px-3 text-[11px] md:text-[12px] font-black uppercase tracking-[0.08em] transition-all border-b-[3px] whitespace-nowrap', active ? 'text-primary' : 'border-transparent text-text-muted hover:text-main hover:border-border-main')} style={active ? { borderColor: 'var(--primary)', color: 'var(--primary)' } : {}}>
    {icon} {label}
  </button>
);

const ImagingButton = ({ active, onClick, icon, label }: any) => (
  <button onClick={onClick} className={cn('px-4 md:px-7 py-3 text-xs font-black uppercase tracking-[0.12em] rounded-xl transition-all duration-300 flex items-center gap-2 whitespace-nowrap', active ? 'bg-card-bg text-primary shadow-elite' : 'text-text-muted hover:text-main')}>
    {icon} {label}
  </button>
);
