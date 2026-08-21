import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  Baby,
  CheckCircle2,
  ChevronRight,
  Clock,
  Diamond,
  HeartPulse,
  History,
  Microscope,
  RefreshCcw,
  Save,
  Scissors,
  ShieldCheck,
  Smile,
  Sparkles,
  Stethoscope,
  Trash2,
  Zap,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import {
  patientClinicalPersistence,
  type ClinicalConclusion,
  type MasterPlanRevision,
  type PersistedOdontogram,
} from '../../../services/patientClinicalPersistence';
import { cn } from '../../../utils/cn';
import { Odontogram } from '../../../components/odontogram/Odontogram';
import type { OdontogramType, ToothSurfaceState } from '../../../components/odontogram/types';
import { AssistantParo } from './wizards/AssistantParo';
import { AssistantEndo } from './wizards/AssistantEndo';
import { AssistantChirurgie } from './wizards/AssistantChirurgie';
import { AssistantProthese } from './wizards/AssistantProthese';
import { AssistantPedo } from './wizards/AssistantPedo';
import { AssistantOrtho } from './wizards/AssistantOrtho';
import { AssistantExamenComplet } from './wizards/AssistantExamenComplet';
import { AssistantATM } from './wizards/AssistantATM';
import { AssistantPatho } from './wizards/AssistantPatho';

interface ClinicalHubProps {
  patientId: number;
}

type PlanStatus = 'pending' | 'done' | 'postponed';

type TreatmentStep = {
  id: string;
  title: string;
  assistant: string;
  status: PlanStatus;
  date: string;
};

type LastProposal = {
  text: string;
  date: string;
  wizard: string;
};

type PatientMedicalSource = {
  antecedents_medicaux?: string | null;
};

const ASSISTANTS = [
  {
    id: 'general',
    name: 'Examen clinique complet',
    description: 'Collecte structurée générale et synthèse à valider par le praticien.',
    icon: Stethoscope,
    iconClass: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
  },
  {
    id: 'paro',
    name: 'Parodontologie',
    description: 'Bilan parodontal structuré et observations à interpréter par le praticien.',
    icon: HeartPulse,
    iconClass: 'bg-rose-500/10 text-rose-600 border-rose-500/20',
  },
  {
    id: 'endo',
    name: 'Endodontie',
    description: 'Symptômes pulpaires et péri-apicaux, proposition clinique non autoritative.',
    icon: Activity,
    iconClass: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  },
  {
    id: 'prothese',
    name: 'Prothèse & esthétique',
    description: 'Constats prothétiques et esthétiques structurés, sans plan automatique.',
    icon: Diamond,
    iconClass: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  },
  {
    id: 'chirurgie',
    name: 'Chirurgie orale',
    description: 'Collecte pré-opératoire et constatations de chirurgie orale.',
    icon: Scissors,
    iconClass: 'bg-purple-500/10 text-purple-600 border-purple-500/20',
  },
  {
    id: 'pedo',
    name: 'Pédodontie',
    description: 'Denture temporaire ou mixte, traumatismes et prévention.',
    icon: Baby,
    iconClass: 'bg-sky-500/10 text-sky-600 border-sky-500/20',
  },
  {
    id: 'ortho',
    name: 'Orthodontie (ODF)',
    description: 'Observations orthodontiques structurées à valider par le praticien.',
    icon: Smile,
    iconClass: 'bg-indigo-500/10 text-indigo-600 border-indigo-500/20',
  },
  {
    id: 'atm',
    name: 'Occlusodontie & ATM',
    description: 'Bruxisme, DTM et observations articulaires structurées.',
    icon: Zap,
    iconClass: 'bg-fuchsia-500/10 text-fuchsia-600 border-fuchsia-500/20',
  },
  {
    id: 'patho',
    name: 'Médecine buccale',
    description: 'Description des lésions et éléments de dépistage à interpréter.',
    icon: Microscope,
    iconClass: 'bg-teal-500/10 text-teal-600 border-teal-500/20',
  },
] as const;

const mapPersistedPlan = (data: any): TreatmentStep[] => {
  const rawSteps = Array.isArray(data?.steps) ? data.steps : [];
  return rawSteps.map((step: any) => ({
    id: step.id ? String(step.id) : crypto.randomUUID(),
    title: step.title,
    assistant: step.assistant,
    status: step.status,
    date: step.date_str,
  }));
};

const inferDentitionType = (state: Record<number, ToothSurfaceState>): OdontogramType => {
  const toothNumbers = Object.keys(state).map(Number);
  return toothNumbers.some((tooth) => tooth >= 50) ? 'PEDIATRIC' : 'ADULT';
};

const formatClinicalDate = (value?: string | null) => {
  if (!value) return 'Date indisponible';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('fr-FR');
};

export const ClinicalHub: React.FC<ClinicalHubProps> = ({ patientId }) => {
  const [activeAssistant, setActiveAssistant] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'EXAMS' | 'ODONTOGRAM'>('ODONTOGRAM');
  const wizardRef = useRef<HTMLDivElement>(null);

  const [medicalSource, setMedicalSource] = useState<PatientMedicalSource | null>(null);
  const [medicalLoading, setMedicalLoading] = useState(true);
  const [medicalError, setMedicalError] = useState(false);

  const [odontogram, setOdontogram] = useState<PersistedOdontogram | null>(null);
  const [odontogramDraft, setOdontogramDraft] = useState<Record<number, ToothSurfaceState> | undefined>(undefined);
  const [odontogramType, setOdontogramType] = useState<OdontogramType>('ADULT');
  const [odontogramLoading, setOdontogramLoading] = useState(true);
  const [odontogramError, setOdontogramError] = useState<string | null>(null);
  const [odontogramDirty, setOdontogramDirty] = useState(false);
  const [odontogramSaving, setOdontogramSaving] = useState(false);
  const suppressNextOdontogramChange = useRef(true);

  const [lastProposal, setLastProposal] = useState<LastProposal | null>(null);
  const [conclusionDraft, setConclusionDraft] = useState('');
  const [conclusions, setConclusions] = useState<ClinicalConclusion[]>([]);
  const [conclusionsLoading, setConclusionsLoading] = useState(true);
  const [conclusionSaving, setConclusionSaving] = useState(false);
  const [conclusionError, setConclusionError] = useState<string | null>(null);

  const [treatmentPlan, setTreatmentPlan] = useState<TreatmentStep[]>([]);
  const [planLoading, setPlanLoading] = useState(true);
  const [planError, setPlanError] = useState<string | null>(null);
  const [planRevisions, setPlanRevisions] = useState<MasterPlanRevision[]>([]);

  const loadMedicalSource = async () => {
    setMedicalLoading(true);
    setMedicalError(false);
    try {
      const response = await api.get(`/patients/${patientId}`);
      setMedicalSource(response.data);
    } catch (error) {
      console.error('Erreur chargement source médicale:', error);
      setMedicalSource(null);
      setMedicalError(true);
    } finally {
      setMedicalLoading(false);
    }
  };

  const loadOdontogram = async () => {
    setOdontogramLoading(true);
    setOdontogramError(null);
    try {
      const persisted = await patientClinicalPersistence.getOdontogram(patientId);
      setOdontogram(persisted);
      setOdontogramDraft(persisted?.state ?? undefined);
      setOdontogramType(persisted?.dentition_type ?? 'ADULT');
      setOdontogramDirty(false);
      suppressNextOdontogramChange.current = true;
    } catch (error) {
      console.error('Erreur chargement odontogramme:', error);
      setOdontogram(null);
      setOdontogramDraft(undefined);
      setOdontogramError("Impossible de charger l'odontogramme enregistré.");
    } finally {
      setOdontogramLoading(false);
    }
  };

  const loadConclusions = async () => {
    setConclusionsLoading(true);
    setConclusionError(null);
    try {
      setConclusions(await patientClinicalPersistence.listConclusions(patientId));
    } catch (error) {
      console.error('Erreur chargement conclusions:', error);
      setConclusions([]);
      setConclusionError('Historique des conclusions indisponible.');
    } finally {
      setConclusionsLoading(false);
    }
  };

  const loadPlan = async () => {
    setPlanLoading(true);
    setPlanError(null);
    try {
      const [planResponse, revisions] = await Promise.all([
        api.get(`/patients/${patientId}/master-plan`),
        patientClinicalPersistence.listMasterPlanRevisions(patientId),
      ]);
      setTreatmentPlan(mapPersistedPlan(planResponse.data));
      setPlanRevisions(revisions);
    } catch (error) {
      console.error('Erreur chargement master plan:', error);
      setTreatmentPlan([]);
      setPlanRevisions([]);
      setPlanError("Plan de traitement indisponible. Aucune donnée locale n'est utilisée comme remplacement.");
    } finally {
      setPlanLoading(false);
    }
  };

  useEffect(() => {
    void loadMedicalSource();
    void loadOdontogram();
    void loadConclusions();
    void loadPlan();
  }, [patientId]);

  useEffect(() => {
    if (activeAssistant && wizardRef.current) {
      setTimeout(() => wizardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    }
  }, [activeAssistant]);

  const saveOdontogram = async () => {
    if (!odontogramDraft) return;
    setOdontogramSaving(true);
    setOdontogramError(null);
    try {
      const saved = await patientClinicalPersistence.saveOdontogram(patientId, {
        dentition_type: odontogramType,
        state: odontogramDraft,
        expected_revision: odontogram?.revision ?? 0,
      });
      setOdontogram(saved);
      setOdontogramDraft(saved.state);
      setOdontogramType(saved.dentition_type);
      setOdontogramDirty(false);
      suppressNextOdontogramChange.current = true;
      toast.success(`Odontogramme enregistré · révision ${saved.revision}.`);
    } catch (error: any) {
      if (error?.response?.status === 409) {
        setOdontogramError("L'odontogramme a été modifié ailleurs. Rechargez avant d'enregistrer.");
      } else {
        setOdontogramError("L'odontogramme n'a pas été enregistré.");
      }
    } finally {
      setOdontogramSaving(false);
    }
  };

  const saveConclusion = async () => {
    const conclusionText = conclusionDraft.trim();
    if (!conclusionText) return;
    setConclusionSaving(true);
    setConclusionError(null);
    try {
      await patientClinicalPersistence.createConclusion(patientId, {
        conclusion_text: conclusionText,
        proposal_text: lastProposal?.text ?? null,
        proposal_source: lastProposal?.wizard ?? null,
      });
      setConclusionDraft('');
      await loadConclusions();
      toast.success('Conclusion praticien enregistrée au dossier.');
    } catch (error: any) {
      const status = error?.response?.status;
      setConclusionError(status === 403
        ? "Vous n'êtes pas autorisé à retenir une conclusion clinique."
        : "La conclusion n'a pas été enregistrée.");
    } finally {
      setConclusionSaving(false);
    }
  };

  const savePlan = async (plan: TreatmentStep[]): Promise<boolean> => {
    const payload = plan.map((step) => ({
      title: step.title,
      assistant: step.assistant,
      status: step.status,
      date_str: step.date,
    }));
    try {
      const response = await api.put(`/patients/${patientId}/master-plan`, payload);
      setTreatmentPlan(mapPersistedPlan(response.data));
      setPlanRevisions(await patientClinicalPersistence.listMasterPlanRevisions(patientId));
      setPlanError(null);
      return true;
    } catch (error) {
      console.error('Erreur sauvegarde master plan:', error);
      setPlanError("La modification n'a pas été enregistrée. Le plan affiché reste inchangé.");
      toast.error('Échec de sauvegarde du plan de traitement.');
      return false;
    }
  };

  const deleteStep = async (id: string) => {
    const updated = treatmentPlan.filter((step) => step.id !== id);
    if (await savePlan(updated)) toast.success('Étape supprimée du plan enregistré.');
  };

  const updateStatus = async (id: string, newStatus: PlanStatus) => {
    const updated = treatmentPlan.map((step) => step.id === id
      ? { ...step, status: newStatus, date: newStatus === 'done' ? `Fait le ${new Date().toLocaleDateString('fr-FR')}` : 'Reporté' }
      : step);
    if (await savePlan(updated) && newStatus === 'done') toast.success('Étape validée dans le plan enregistré.');
  };

  const handleWizardComplete = (wizardId: string, proposalText: string) => {
    const wizard = ASSISTANTS.find((assistant) => assistant.id === wizardId)?.name ?? wizardId;
    setLastProposal({ text: proposalText, date: new Date().toLocaleString('fr-FR'), wizard });
    setActiveAssistant(null);
    toast.success('Proposition clinique générée. Validation du praticien requise.');
  };

  const completedSteps = treatmentPlan.filter((step) => step.status === 'done').length;
  const progressPercent = treatmentPlan.length > 0 ? Math.round((completedSteps / treatmentPlan.length) * 100) : 0;
  const latestRevision = planRevisions[0];

  return (
    <div className="w-full min-w-0 space-y-5 rounded-[1.75rem] border border-white/60 bg-white/40 p-3 shadow-elite backdrop-blur-xl dark:border-slate-800/50 dark:bg-slate-900/40 sm:p-6">
      <header className="flex min-w-0 flex-col gap-3 border-b border-border-main/50 pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary sm:h-12 sm:w-12">
            <Stethoscope size={23} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-black tracking-tight text-text-main sm:text-2xl">Espace Clinique</h2>
              <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.12em] text-primary">Données structurées</span>
            </div>
            <p className="mt-1 text-xs font-bold text-text-muted sm:text-sm">Sources enregistrées, propositions séparées et décisions praticien traçables.</p>
          </div>
        </div>
      </header>

      <section aria-label="Sécurité médicale" className="rounded-2xl border border-red-200 bg-red-50/80 p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-100 text-red-700"><ShieldCheck size={20} /></div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-black uppercase tracking-[0.1em] text-red-800">Sécurité médicale</h3>
                <p className="mt-0.5 text-[10px] font-bold uppercase tracking-wider text-red-600/80">Source : dossier Patient</p>
              </div>
              {medicalError && <button onClick={() => void loadMedicalSource()} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-red-200 bg-white px-3 text-xs font-black text-red-700"><RefreshCcw size={14} /> Réessayer</button>}
            </div>
            <div className="mt-3 text-sm font-semibold leading-relaxed text-red-900">
              {medicalLoading
                ? 'Chargement des antécédents…'
                : medicalError
                  ? 'Impossible de charger la source médicale.'
                  : medicalSource?.antecedents_medicaux?.trim()
                    ? medicalSource.antecedents_medicaux
                    : 'Aucun antécédent médical renseigné.'}
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <div className="min-w-0 space-y-5 xl:col-span-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="text-xs font-black uppercase tracking-[0.18em] text-text-muted">Dossier clinique</h3>
            <div className="flex max-w-full overflow-x-auto rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
              <button onClick={() => setViewMode('ODONTOGRAM')} className={cn('min-h-10 shrink-0 rounded-lg px-3 text-[10px] font-black uppercase tracking-wider', viewMode === 'ODONTOGRAM' ? 'bg-white text-primary shadow-sm dark:bg-slate-700' : 'text-text-muted')}>Odontogramme</button>
              <button onClick={() => setViewMode('EXAMS')} className={cn('min-h-10 shrink-0 rounded-lg px-3 text-[10px] font-black uppercase tracking-wider', viewMode === 'EXAMS' ? 'bg-white text-primary shadow-sm dark:bg-slate-700' : 'text-text-muted')}>Examens</button>
            </div>
          </div>

          {viewMode === 'ODONTOGRAM' ? (
            <section className="min-w-0 rounded-3xl border border-border-main bg-card-bg/80 p-3 shadow-sm sm:p-5">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h4 className="font-black text-text-main">Odontogramme enregistré</h4>
                  <p className="mt-1 text-xs font-bold text-text-muted">
                    {odontogram
                      ? `Source backend · révision ${odontogram.revision} · ${formatClinicalDate(odontogram.updated_at)}`
                      : 'Aucun odontogramme enregistré. Le schéma affiché devient autoritatif uniquement après Enregistrer.'}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {odontogramError && <button onClick={() => void loadOdontogram()} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-border-main bg-white px-3 text-xs font-black text-text-main"><RefreshCcw size={14} /> Recharger</button>}
                  <button
                    onClick={() => void saveOdontogram()}
                    disabled={odontogramLoading || odontogramSaving || !odontogramDraft || !odontogramDirty}
                    className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-primary px-4 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <Save size={14} /> {odontogramSaving ? 'Enregistrement…' : 'Enregistrer'}
                  </button>
                </div>
              </div>
              {odontogramError && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-bold text-red-700">{odontogramError}</div>}
              {odontogramDirty && <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs font-bold text-amber-800">Modifications non enregistrées.</div>}
              {odontogramLoading ? (
                <div className="flex min-h-48 items-center justify-center text-sm font-bold text-text-muted">Chargement de l’odontogramme…</div>
              ) : (
                <Odontogram
                  key={`${patientId}-${odontogram?.revision ?? 0}-${odontogramType}`}
                  patientId={patientId}
                  mode="EDIT_STATUS"
                  defaultType={odontogramType}
                  initialData={odontogramDraft}
                  onStatusChange={(state) => {
                    setOdontogramDraft(state);
                    setOdontogramType(inferDentitionType(state));
                    if (suppressNextOdontogramChange.current) {
                      suppressNextOdontogramChange.current = false;
                      return;
                    }
                    setOdontogramDirty(true);
                  }}
                />
              )}
            </section>
          ) : (
            <div className="space-y-5">
              {lastProposal && (
                <section className="rounded-2xl border border-indigo-200 bg-indigo-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2"><Sparkles size={16} className="text-indigo-600" /><h4 className="text-sm font-black text-indigo-900">Proposition à valider · {lastProposal.wizard}</h4></div>
                      <p className="mt-2 whitespace-pre-wrap text-xs font-semibold leading-relaxed text-indigo-800">{lastProposal.text}</p>
                      <p className="mt-2 text-[10px] font-bold text-indigo-600/70">Session · {lastProposal.date}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button onClick={() => setConclusionDraft(lastProposal.text)} className="min-h-10 rounded-xl border border-indigo-200 bg-white px-3 text-xs font-black text-indigo-700">Utiliser comme brouillon</button>
                      </div>
                    </div>
                    <button aria-label="Supprimer la proposition" onClick={() => setLastProposal(null)} className="shrink-0 rounded-lg p-2 text-indigo-400 hover:bg-indigo-100 hover:text-indigo-700"><Trash2 size={16} /></button>
                  </div>
                </section>
              )}

              <section className="rounded-3xl border border-border-main bg-card-bg/80 p-4 shadow-sm sm:p-5">
                <div className="mb-4">
                  <h4 className="font-black text-text-main">Conclusion retenue par le praticien</h4>
                  <p className="mt-1 text-xs font-bold text-text-muted">Une proposition d’assistant ne devient jamais une conclusion sans cette action explicite.</p>
                </div>
                <textarea
                  value={conclusionDraft}
                  onChange={(event) => setConclusionDraft(event.target.value)}
                  placeholder="Saisir la conclusion que vous retenez après examen…"
                  className="min-h-28 w-full resize-y rounded-2xl border border-border-main bg-white p-3 text-sm font-semibold text-text-main outline-none focus:border-primary dark:bg-slate-900"
                />
                <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                  {conclusionError ? <p className="text-xs font-bold text-red-600">{conclusionError}</p> : <span />}
                  <button onClick={() => void saveConclusion()} disabled={conclusionSaving || !conclusionDraft.trim()} className="min-h-10 rounded-xl bg-primary px-4 text-xs font-black text-white disabled:opacity-40">{conclusionSaving ? 'Enregistrement…' : 'Enregistrer la conclusion'}</button>
                </div>
              </section>

              <section className="rounded-3xl border border-border-main bg-card-bg/80 p-4 shadow-sm sm:p-5">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div><h4 className="font-black text-text-main">Conclusions enregistrées</h4><p className="mt-1 text-xs font-bold text-text-muted">Historique append-only du dossier clinique.</p></div>
                  <button onClick={() => void loadConclusions()} className="rounded-lg p-2 text-text-muted hover:bg-slate-100" aria-label="Recharger les conclusions"><RefreshCcw size={16} /></button>
                </div>
                {conclusionsLoading ? <p className="text-xs font-bold text-text-muted">Chargement…</p> : conclusions.length === 0 ? <p className="rounded-xl border border-dashed border-border-main p-4 text-xs font-bold text-text-muted">Aucune conclusion retenue enregistrée.</p> : (
                  <div className="space-y-3">
                    {conclusions.slice(0, 5).map((conclusion) => (
                      <article key={conclusion.id} className="rounded-2xl border border-border-main bg-white/70 p-3 dark:bg-slate-900/70">
                        <p className="whitespace-pre-wrap text-sm font-semibold text-text-main">{conclusion.conclusion_text}</p>
                        <p className="mt-2 text-[10px] font-bold text-text-muted">Validée par utilisateur #{conclusion.validated_by} · {formatClinicalDate(conclusion.created_at)}</p>
                        {conclusion.proposal_source && <p className="mt-1 text-[10px] font-bold text-indigo-600">Provenance de brouillon : {conclusion.proposal_source}</p>}
                      </article>
                    ))}
                  </div>
                )}
              </section>

              <div>
                <h4 className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-text-muted">Examens structurés</h4>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {ASSISTANTS.map((assistant) => {
                    const Icon = assistant.icon;
                    return (
                      <motion.button key={assistant.id} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} onClick={() => setActiveAssistant(assistant.id)} className="group min-w-0 rounded-2xl border border-border-main bg-card-bg/80 p-4 text-left shadow-sm transition-colors hover:border-primary/30">
                        <div className="flex items-start justify-between gap-3">
                          <div className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border', assistant.iconClass)}><Icon size={19} /></div>
                          <ChevronRight size={16} className="mt-2 shrink-0 text-text-muted group-hover:text-primary" />
                        </div>
                        <h5 className="mt-3 text-sm font-black text-text-main">{assistant.name}</h5>
                        <p className="mt-1 text-[11px] font-semibold leading-relaxed text-text-muted">{assistant.description}</p>
                      </motion.button>
                    );
                  })}
                </div>
              </div>

              <AnimatePresence mode="wait">
                {activeAssistant && (
                  <motion.div ref={wizardRef} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }} className="scroll-mt-40 rounded-3xl border border-primary/25 bg-card-bg p-4 shadow-xl sm:p-6">
                    <div className="mb-5 flex items-center justify-between gap-3"><h4 className="text-lg font-black text-text-main">Examen · {ASSISTANTS.find((assistant) => assistant.id === activeAssistant)?.name}</h4></div>
                    {activeAssistant === 'paro' ? <AssistantParo onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('paro', proposal)} />
                      : activeAssistant === 'endo' ? <AssistantEndo onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('endo', proposal)} />
                        : activeAssistant === 'chirurgie' ? <AssistantChirurgie onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('chirurgie', proposal)} />
                          : activeAssistant === 'prothese' ? <AssistantProthese onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('prothese', proposal)} />
                            : activeAssistant === 'pedo' ? <AssistantPedo onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('pedo', proposal)} />
                              : activeAssistant === 'ortho' ? <AssistantOrtho onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('ortho', proposal)} />
                                : activeAssistant === 'general' ? <AssistantExamenComplet onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('general', proposal)} />
                                  : activeAssistant === 'atm' ? <AssistantATM onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('atm', proposal)} />
                                    : activeAssistant === 'patho' ? <AssistantPatho onCancel={() => setActiveAssistant(null)} onComplete={(proposal) => handleWizardComplete('patho', proposal)} />
                                      : null}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>

        <aside className="min-w-0 space-y-4 xl:col-span-4">
          <div className="flex items-center justify-between gap-3">
            <div><h3 className="text-xs font-black uppercase tracking-[0.18em] text-text-muted">Master Plan</h3><p className="mt-1 text-[10px] font-bold text-text-muted">Source backend enregistrée</p></div>
            <button
              onClick={async () => {
                if (window.confirm('Remplacer le plan enregistré par un plan vide ?') && await savePlan([])) toast.success('Plan de traitement réinitialisé.');
              }}
              disabled={planLoading || treatmentPlan.length === 0}
              className="min-h-9 rounded-lg border border-rose-200 px-2.5 text-[9px] font-black uppercase tracking-wider text-rose-600 disabled:opacity-40"
            >Réinitialiser</button>
          </div>

          <section className="rounded-3xl border border-border-main bg-card-bg/80 p-4 shadow-sm sm:p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs font-black text-text-main"><Clock size={15} className="text-primary" /> Progression</div>
              <span className="text-xl font-black text-primary">{progressPercent}%</span>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-primary transition-all" style={{ width: `${progressPercent}%` }} /></div>

            {planError && <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-bold text-red-700">{planError}</div>}
            {planLoading ? <p className="mt-5 text-xs font-bold text-text-muted">Chargement du plan…</p> : treatmentPlan.length === 0 ? <div className="mt-5 rounded-2xl border border-dashed border-border-main p-5 text-center text-xs font-bold text-text-muted">Aucune étape de traitement enregistrée.</div> : (
              <div className="mt-5 space-y-3">
                {treatmentPlan.map((step) => (
                  <article key={step.id} className="rounded-2xl border border-border-main bg-white/70 p-3 dark:bg-slate-900/70">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0"><p className="text-sm font-black text-text-main">{step.title}</p><p className="mt-1 text-[10px] font-bold text-text-muted">{step.assistant} · {step.date || 'Date non renseignée'}</p></div>
                      <button aria-label="Supprimer l’étape" onClick={() => void deleteStep(step.id)} className="shrink-0 rounded-lg p-2 text-rose-400 hover:bg-rose-50 hover:text-rose-600"><Trash2 size={14} /></button>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button onClick={() => void updateStatus(step.id, 'pending')} className={cn('rounded-lg px-2.5 py-1.5 text-[9px] font-black uppercase', step.status === 'pending' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-text-muted')}>À faire</button>
                      <button onClick={() => void updateStatus(step.id, 'done')} className={cn('rounded-lg px-2.5 py-1.5 text-[9px] font-black uppercase', step.status === 'done' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-text-muted')}>Fait</button>
                      <button onClick={() => void updateStatus(step.id, 'postponed')} className={cn('rounded-lg px-2.5 py-1.5 text-[9px] font-black uppercase', step.status === 'postponed' ? 'bg-slate-300 text-slate-800' : 'bg-slate-100 text-text-muted')}>Reporté</button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-3xl border border-border-main bg-card-bg/80 p-4 shadow-sm sm:p-5">
            <div className="mb-3 flex items-center gap-2"><History size={16} className="text-primary" /><h4 className="text-xs font-black uppercase tracking-[0.12em] text-text-main">Traçabilité du plan</h4></div>
            {latestRevision ? (
              <div className="space-y-2">
                <p className="text-sm font-black text-text-main">Révision {latestRevision.revision}</p>
                <p className="text-xs font-bold text-text-muted">{latestRevision.steps_snapshot.length} étape(s) · utilisateur #{latestRevision.updated_by ?? '—'}</p>
                <p className="text-[10px] font-bold text-text-muted">{formatClinicalDate(latestRevision.created_at)}</p>
                {planRevisions.length > 1 && <p className="pt-1 text-[10px] font-bold text-primary">{planRevisions.length} révisions disponibles dans l’historique.</p>}
              </div>
            ) : <p className="text-xs font-bold text-text-muted">Aucune révision enregistrée.</p>}
          </section>
        </aside>
      </div>
    </div>
  );
};
