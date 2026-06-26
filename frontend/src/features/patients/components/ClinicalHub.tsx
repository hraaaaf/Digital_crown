import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Stethoscope, 
  HeartPulse, 
  Activity, 
  Diamond, 
  Scissors,
  Baby,
  Smile,
  Zap,
  Microscope,
  CheckCircle2,
  Clock,
  ChevronRight,
  Sparkles,
  Plus,
  Trash2
} from 'lucide-react';
import { cn } from '../../../utils/cn';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import { AssistantParo } from './wizards/AssistantParo';
import { AssistantEndo } from './wizards/AssistantEndo';
import { AssistantChirurgie } from './wizards/AssistantChirurgie';
import { AssistantProthese } from './wizards/AssistantProthese';
import { AssistantPedo } from './wizards/AssistantPedo';
import { AssistantOrtho } from './wizards/AssistantOrtho';
import { AssistantGeneral } from './wizards/AssistantGeneral';
import { AssistantExamenComplet } from './wizards/AssistantExamenComplet';
import { AssistantATM } from './wizards/AssistantATM';
import { AssistantPatho } from './wizards/AssistantPatho';
import { VigilanceRadar } from '../../admin/DocumentStudio/VigilanceRadar';
import { Odontogram } from '../../../components/odontogram/Odontogram';

interface ClinicalHubProps {
  patientId: number;
}

const ASSISTANTS = [
  {
    id: 'general',
    name: 'Examen Clinique Complet',
    description: 'Triage → bilan complet → diagnostic + plan de traitement',
    icon: Stethoscope,
    color: 'emerald',
    gradient: 'from-emerald-500/20 to-emerald-500/5'
  },
  {
    id: 'paro',
    name: 'Parodontologie',
    description: 'Diagnostic AAP/EFP 2017 et assainissement',
    icon: HeartPulse,
    color: 'rose',
    gradient: 'from-rose-500/20 to-rose-500/5'
  },
  {
    id: 'endo',
    name: 'Endodontie',
    description: 'Pathologies pulpaires, péri-apicales et urgences',
    icon: Activity,
    color: 'amber',
    gradient: 'from-amber-500/20 to-amber-500/5'
  },
  {
    id: 'prothese',
    name: 'Prothèse & Esthétique',
    description: 'Réhabilitation, usure, facettes et couronnes',
    icon: Diamond,
    color: 'blue',
    gradient: 'from-blue-500/20 to-blue-500/5'
  },
  {
    id: 'chirurgie',
    name: 'Chirurgie Orale',
    description: 'Dents incluses, avulsions et implantologie',
    icon: Scissors,
    color: 'purple',
    gradient: 'from-purple-500/20 to-purple-500/5'
  },
  {
    id: 'pedo',
    name: 'Pédodontie',
    description: 'Denture mixte, traumatismes et prévention',
    icon: Baby,
    color: 'sky',
    gradient: 'from-sky-500/20 to-sky-500/5'
  },
  {
    id: 'ortho',
    name: 'Orthodontie (ODF)',
    description: 'Malocclusions, dysmorphoses et alignement',
    icon: Smile,
    color: 'indigo',
    gradient: 'from-indigo-500/20 to-indigo-500/5'
  },
  {
    id: 'atm',
    name: 'Occlusodontie & ATM',
    description: 'Bruxisme, DTM et troubles articulaires',
    icon: Zap,
    color: 'fuchsia',
    gradient: 'from-fuchsia-500/20 to-fuchsia-500/5'
  },
  {
    id: 'patho',
    name: 'Médecine Buccale',
    description: 'Lésions muqueuses, dépistage et kystes',
    icon: Microscope,
    color: 'teal',
    gradient: 'from-teal-500/20 to-teal-500/5'
  }
];

type PlanStatus = 'pending' | 'done' | 'postponed';

interface TreatmentStep {
  id: string;
  title: string;
  assistant: string;
  status: PlanStatus;
  date: string;
}

export const ClinicalHub: React.FC<ClinicalHubProps> = ({ patientId }) => {
  const [activeAssistant, setActiveAssistant] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'ASSISTANTS' | 'ODONTOGRAM'>('ASSISTANTS');
  const [savedOdontogram, setSavedOdontogram] = useState<any>(() => {
    const s = localStorage.getItem(`odontogram_state_${patientId}`);
    return s ? JSON.parse(s) : null;
  });
  
  const [treatmentPlan, setTreatmentPlan] = useState<TreatmentStep[]>(() => {
    const saved = localStorage.getItem(`master_plan_${patientId}`);
    if (saved) {
      return JSON.parse(saved);
    }
    return [
      { id: 'step-1', title: 'Consultation & Bilan complet', assistant: 'general', status: 'done', date: 'Aujourd\'hui' },
      { id: 'step-2', title: 'Détartrage & Surfaçage', assistant: 'paro', status: 'pending', date: 'À planifier' }
    ];
  });

  useEffect(() => {
    api.get(`/patients/${patientId}/master-plan`)
      .then((res: any) => {
        if (res.data && res.data.steps && res.data.steps.length > 0) {
          const steps = res.data.steps.map((s: any) => ({
            id: s.id ? s.id.toString() : Math.random().toString(36).substring(7),
            title: s.title,
            assistant: s.assistant,
            status: s.status,
            date: s.date_str
          }));
          setTreatmentPlan(steps);
          localStorage.setItem(`master_plan_${patientId}`, JSON.stringify(steps));
        }
      })
      .catch((err: any) => console.error("Erreur sync master plan:", err));
  }, [patientId]);

  const deleteStep = (id: string) => {
    const updated = treatmentPlan.filter(step => step.id !== id);
    savePlan(updated);
    toast.success('Étape supprimée du plan.');
  };

  const savePlan = (plan: TreatmentStep[]) => {
    setTreatmentPlan(plan);
    localStorage.setItem(`master_plan_${patientId}`, JSON.stringify(plan));
    
    const payload = plan.map((s, index) => ({
       title: s.title,
       assistant: s.assistant,
       status: s.status,
       date_str: s.date,
       order_index: index
    }));
    api.put(`/patients/${patientId}/master-plan`, payload).catch((err: any) => console.error("Erreur sauvegarde master plan:", err));
  };

  const updateStatus = (id: string, newStatus: PlanStatus) => {
    const updated = treatmentPlan.map(step => 
      step.id === id ? { ...step, status: newStatus, date: newStatus === 'done' ? 'Fait le ' + new Date().toLocaleDateString() : 'Reporté' } : step
    );
    savePlan(updated);
    if (newStatus === 'done') {
      toast.success('Étape validée et synchronisée avec l\'historique.');
    }
  };

  const completedSteps = treatmentPlan.filter(s => s.status === 'done').length;
  const progressPercent = treatmentPlan.length > 0 ? Math.round((completedSteps / treatmentPlan.length) * 100) : 0;

  const handleWizardComplete = (wizardId: string, diag: string, steps: any[], suggestedNextAssistant?: string | null) => {
    const newSteps = steps.map(s => ({
      id: crypto.randomUUID(),
      title: s.title,
      assistant: s.assistant,
      status: 'pending' as PlanStatus,
      date: 'Nouveau'
    }));
    
    const diagStep = {
      id: crypto.randomUUID(),
      title: `Diagnostic : ${diag}`,
      assistant: wizardId,
      status: 'done' as PlanStatus,
      date: new Date().toLocaleDateString()
    };
    
    // Ordre scientifique des spécialités : Paro/Urgence -> Endo -> Chirurgie -> ODF -> Prothèse
    const scientificOrder: Record<string, number> = {
      'urgences': 1, 'paro': 2, 'endo': 3, 'patho': 4,
      'chirurgie': 5, 'ortho': 6, 'pedo': 7, 'prothese': 8,
      'atm': 9, 'general': 10
    };

    const combined = [...treatmentPlan, diagStep, ...newSteps].sort((a, b) => {
      // Les étapes terminées restent en haut
      if (a.status === 'done' && b.status !== 'done') return -1;
      if (a.status !== 'done' && b.status === 'done') return 1;
      if (a.status === 'done' && b.status === 'done') return 0;
      
      const oa = scientificOrder[a.assistant] || 99;
      const ob = scientificOrder[b.assistant] || 99;
      return oa - ob;
    });
    
    savePlan(combined);
    
    if (suggestedNextAssistant) {
      setActiveAssistant(suggestedNextAssistant);
      toast.success(`Diagnostic généré. Relais passé à l'Assistant ${suggestedNextAssistant.toUpperCase()}`);
    } else {
      setActiveAssistant(null);
      toast.success(`Diagnostic généré avec succès !`);
    }
  };

  return (
    <div className="w-full flex flex-col gap-6 p-6 bg-white/40 dark:bg-slate-900/40 rounded-[2.5rem] border border-white/60 dark:border-slate-800/50 backdrop-blur-xl shadow-elite min-h-[80vh] relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 blur-[100px] -mr-48 -mt-48 rounded-full pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-primary/5 blur-[100px] -ml-48 -mb-48 rounded-full pointer-events-none" />

      {/* HEADER SECTION */}
      <div className="flex items-center justify-between pb-6 border-b border-border-main/50 relative z-10">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center text-primary shadow-sm" style={{ color: 'var(--primary)', backgroundColor: 'rgba(var(--primary-rgb), 0.1)' }}>
            <Sparkles size={28} />
          </div>
          <div>
            <h2 className="text-2xl font-black text-text-main flex items-center gap-3 tracking-tight">
              Cerveau Clinique Central
              <span className="text-[10px] uppercase tracking-widest bg-primary/10 text-primary px-3 py-1 rounded-full border border-primary/20 font-black shadow-sm" style={{ color: 'var(--primary)' }}>
                Ghost Orchestrator
              </span>
            </h2>
            <p className="text-sm text-text-muted font-bold mt-1">Diagnostic intelligent, plan de traitement global et suivi automatisé.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 h-full relative z-10">
        
        {/* COLONNE GAUCHE : LES ASSISTANTS & VIGILANCE */}
        <div className="xl:col-span-8 flex flex-col gap-6">
          <VigilanceRadar />
          
          <div className="flex items-center justify-between mt-2">
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-text-muted">Dossier Clinique</h3>
            <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
              <button
                onClick={() => setViewMode('ASSISTANTS')}
                className={cn(
                  "px-4 py-2 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all",
                  viewMode === 'ASSISTANTS' ? "bg-white dark:bg-slate-700 text-primary shadow-sm" : "text-text-muted hover:text-text-main"
                )}
              >
                Assistants IA
              </button>
              <button
                onClick={() => setViewMode('ODONTOGRAM')}
                className={cn(
                  "px-4 py-2 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all",
                  viewMode === 'ODONTOGRAM' ? "bg-white dark:bg-slate-700 text-primary shadow-sm" : "text-text-muted hover:text-text-main"
                )}
              >
                Statut Dentaire
              </button>
            </div>
          </div>
          
          {viewMode === 'ODONTOGRAM' ? (
            <div className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-xl rounded-[2rem] border border-white/60 dark:border-slate-700 p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-6">
                 <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                    <Stethoscope size={20} />
                 </div>
                 <div>
                    <h4 className="font-black text-lg">Schéma Dentaire Initial</h4>
                    <p className="text-xs text-text-muted font-bold">Renseignez les caries, restaurations, et dents absentes</p>
                 </div>
              </div>
              <Odontogram 
                patientId={patientId}
                mode="EDIT_STATUS"
                initialData={savedOdontogram}
                onStatusChange={(data) => {
                  setSavedOdontogram(data);
                  localStorage.setItem(`odontogram_state_${patientId}`, JSON.stringify(data));
                }}
              />
            </div>
          ) : (
            <>
              {progressPercent === 100 && treatmentPlan.length > 0 && (
                <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-500/20 text-emerald-600 rounded-full flex items-center justify-center">
                      <CheckCircle2 size={20} />
                    </div>
                    <div>
                      <h4 className="text-sm font-black text-emerald-700">Plan de Traitement Terminé</h4>
                      <p className="text-xs text-emerald-600/70 font-bold">Ce plan est verrouillé en lecture seule. Vous ne pouvez plus ajouter d'étapes.</p>
                    </div>
                  </div>
                </div>
              )}
              
              <div className={cn("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4", progressPercent === 100 && treatmentPlan.length > 0 && "opacity-50 pointer-events-none")}>
                {ASSISTANTS.map((assistant) => {
              const Icon = assistant.icon;
              return (
                <motion.button
                  key={assistant.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveAssistant(assistant.id)}
                  className={cn(
                    "flex flex-col items-start gap-4 p-5 rounded-3xl border transition-all text-left group relative overflow-hidden",
                    activeAssistant === assistant.id 
                      ? "bg-card-bg border-primary/50 shadow-lg" 
                      : "bg-white/50 dark:bg-slate-800/50 border-white/60 dark:border-slate-700/50 hover:bg-white dark:hover:bg-slate-800 shadow-sm backdrop-blur-md"
                  )}
                  style={activeAssistant === assistant.id ? { borderColor: 'var(--primary)', boxShadow: '0 10px 40px -10px rgba(var(--primary-rgb), 0.3)' } : {}}
                >
                  <div className={cn(`absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-500`, assistant.gradient)} />
                  
                  <div className="flex items-center justify-between w-full">
                    <div className={cn(`w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 z-10 bg-${assistant.color}-500/10 text-${assistant.color}-500 border border-${assistant.color}-500/20 shadow-sm`)}>
                      <Icon size={24} />
                    </div>
                    <div className="z-10 w-8 h-8 rounded-full bg-card-bg border border-border-main flex items-center justify-center text-text-muted group-hover:text-primary group-hover:bg-primary/10 transition-colors shadow-sm">
                      <ChevronRight size={16} />
                    </div>
                  </div>
                  <div className="z-10 flex-1 mt-2">
                    <h4 className="text-sm font-black text-text-main mb-1">{assistant.name}</h4>
                    <p className="text-[10px] text-text-muted font-bold leading-relaxed">{assistant.description}</p>
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* ZONE DU WIZARD ACTIF */}
          <AnimatePresence mode="wait">
            {activeAssistant && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-2 p-8 bg-card-bg border border-primary/30 rounded-[2.5rem] shadow-2xl relative overflow-hidden"
                style={{ boxShadow: '0 20px 60px -15px rgba(var(--primary-rgb), 0.15)' }}
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary to-transparent opacity-50" style={{ backgroundImage: 'linear-gradient(to right, transparent, var(--primary), transparent)' }} />
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-black">Agent {ASSISTANTS.find(a => a.id === activeAssistant)?.name}</h3>
                  {activeAssistant !== 'paro' && activeAssistant !== 'endo' && activeAssistant !== 'chirurgie' && activeAssistant !== 'prothese' && activeAssistant !== 'pedo' && activeAssistant !== 'ortho' && activeAssistant !== 'general' && activeAssistant !== 'atm' && activeAssistant !== 'patho' && (
                    <div className="px-3 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded-lg text-[9px] uppercase tracking-widest font-black flex items-center gap-1">
                      <Sparkles size={12} /> Construction (Phase 3)
                    </div>
                  )}
                </div>
                
                {activeAssistant === 'paro' ? (
                  <AssistantParo 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('paro', diag, steps)}
                  />
                ) : activeAssistant === 'endo' ? (
                  <AssistantEndo 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('endo', diag, steps)}
                  />
                ) : activeAssistant === 'chirurgie' ? (
                  <AssistantChirurgie 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('chirurgie', diag, steps)}
                  />
                ) : activeAssistant === 'prothese' ? (
                  <AssistantProthese 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('prothese', diag, steps)}
                  />
                ) : activeAssistant === 'pedo' ? (
                  <AssistantPedo 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('pedo', diag, steps)}
                  />
                ) : activeAssistant === 'ortho' ? (
                  <AssistantOrtho 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('ortho', diag, steps)}
                  />
                ) : activeAssistant === 'general' ? (
                  <AssistantExamenComplet
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps, next) => handleWizardComplete('general', diag, steps, next)}
                  />
                ) : activeAssistant === 'atm' ? (
                  <AssistantATM 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('atm', diag, steps)}
                  />
                ) : activeAssistant === 'patho' ? (
                  <AssistantPatho 
                    onCancel={() => setActiveAssistant(null)}
                    onComplete={(diag, steps) => handleWizardComplete('patho', diag, steps)}
                  />
                ) : (
                  <>
                    <p className="text-text-muted font-bold mb-6 text-sm">
                      Le système est prêt à héberger les algorithmes d'arbre décisionnel (QCM interactif) pour cette spécialité. Le diagnostic généré viendra s'insérer automatiquement dans le Master Plan à droite.
                    </p>
                    <div className="flex gap-4">
                      <button 
                        onClick={() => setActiveAssistant(null)}
                        className="px-6 py-3 bg-card-bg border border-border-main text-text-muted font-black uppercase text-xs tracking-wider rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors shadow-sm"
                      >
                        Fermer l'assistant
                      </button>
                      <button 
                        onClick={() => {
                          const id = crypto.randomUUID();
                          const assistantName = ASSISTANTS.find(a => a.id === activeAssistant)?.id || 'general';
                          savePlan([...treatmentPlan, { id, title: 'Nouvel Acte ' + assistantName.toUpperCase(), assistant: assistantName, status: 'pending', date: 'Nouveau' }]);
                          toast.success('Simulation : Acte ajouté au Master Plan.');
                        }}
                        className="px-6 py-3 bg-primary/10 text-primary font-black uppercase text-xs tracking-wider rounded-xl hover:bg-primary/20 transition-colors flex items-center gap-2"
                        style={{ color: 'var(--primary)' }}
                      >
                        <Plus size={16} /> Simuler Ajout au Plan
                      </button>
                    </div>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
            </>
          )}
        </div>
        
        {/* COLONNE DROITE : PLAN DE TRAITEMENT GLOBAL */}
        <div className="xl:col-span-4 flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-text-muted">Master Plan de Traitement</h3>
            {progressPercent === 100 && treatmentPlan.length > 0 ? (
              <button 
                onClick={() => {
                  if (window.confirm('Voulez-vous archiver ce plan terminé et en démarrer un nouveau ?')) {
                    // Dans un vrai backend, on appellerait une route /archive
                    savePlan([]);
                    setActiveAssistant('general');
                    toast.success('Ancien plan archivé. Nouveau plan initié.');
                  }
                }}
                className="text-[10px] uppercase font-black tracking-widest text-emerald-500 hover:text-white hover:bg-emerald-500 transition-colors px-3 py-1.5 rounded-lg border border-emerald-500/30"
              >
                Archiver & Nouveau
              </button>
            ) : (
              <button 
                onClick={() => {
                  if (window.confirm('Voulez-vous vraiment réinitialiser le plan de traitement complet ?')) {
                    savePlan([]);
                    setActiveAssistant('general');
                    toast.success('Plan réinitialisé. L\'Assistant Général prend le relais.');
                  }
                }}
                className="text-[10px] uppercase font-black tracking-widest text-rose-500 hover:text-white hover:bg-rose-500 transition-colors px-3 py-1.5 rounded-lg border border-rose-500/30"
              >
                Réinitialiser
              </button>
            )}
          </div>
          
          <div className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl border border-white/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-elite flex flex-col h-full relative overflow-hidden">
            <div className="flex items-center justify-between mb-6 relative z-10">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                <span className="text-xs font-bold text-text-muted uppercase tracking-widest">Tracking Actif</span>
              </div>
              {progressPercent === 100 && treatmentPlan.length > 0 ? (
                <div className="flex flex-col items-end">
                  <span className="text-xl font-black text-emerald-500 drop-shadow-sm">COMPLÉTÉ</span>
                  <span className="text-[9px] uppercase tracking-widest text-emerald-500/70 font-black">Plan Verrouillé (Read-Only)</span>
                </div>
              ) : (
                <span className="text-xl font-black text-primary drop-shadow-sm" style={{ color: 'var(--primary)' }}>{progressPercent}%</span>
              )}
            </div>

            {/* PROGRESS BAR */}
            <div className="w-full h-2 bg-slate-200/50 dark:bg-slate-800/50 rounded-full mb-8 overflow-hidden flex relative z-10 shadow-inner">
              <motion.div 
                className="h-full bg-emerald-500 transition-all duration-1000 ease-out shadow-[0_0_15px_rgba(16,185,129,0.8)]" 
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            {/* TIMELINE */}
            <div className="flex flex-col gap-5 flex-1 relative z-10">
              <AnimatePresence>
                {treatmentPlan.map((step, index) => {
                  const ast = ASSISTANTS.find(a => a.id === step.assistant);
                  const color = ast ? ast.color : 'slate';
                  
                  return (
                    <motion.div 
                      key={step.id} 
                      layout
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex gap-4 relative"
                    >
                      {/* Ligne connectrice */}
                      {index < treatmentPlan.length - 1 && (
                        <div className="absolute left-4 top-10 bottom-[-20px] w-[2px] bg-slate-200/50 dark:bg-slate-800/50" />
                      )}
                      
                      <div className={cn(
                        "w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 z-10 bg-card-bg transition-colors shadow-sm",
                        step.status === 'done' 
                          ? "border-emerald-500 text-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.2)]" 
                          : step.status === 'postponed'
                          ? "border-amber-500 text-amber-500"
                          : "border-slate-300 dark:border-slate-700 text-slate-400"
                      )}>
                        {step.status === 'done' ? <CheckCircle2 size={16} /> : <span className="text-xs font-black">{index + 1}</span>}
                      </div>
                      
                      <div className={cn(
                        "flex-1 p-4 rounded-2xl border transition-all",
                        step.status === 'done' 
                          ? "bg-emerald-500/5 border-emerald-500/20 opacity-75" 
                          : step.status === 'postponed'
                          ? "bg-amber-500/5 border-amber-500/20"
                          : "bg-white/50 dark:bg-slate-800/50 shadow-sm border-white/60 dark:border-slate-700/50 backdrop-blur-md"
                      )}>
                        <div className="flex items-center justify-between mb-1">
                          <span className={cn(
                            "text-[9px] uppercase font-black tracking-widest px-2 py-0.5 rounded text-white shadow-sm",
                            `bg-${color}-500`
                          )}>
                            {ast ? ast.name : step.assistant}
                          </span>
                          <span className="text-[10px] text-text-muted font-bold flex items-center gap-1">
                            <Clock size={10} /> {step.date}
                          </span>
                        </div>
                        <h5 className={cn("text-sm font-black mt-2", step.status === 'done' ? "text-emerald-700 dark:text-emerald-400 line-through" : "text-text-main")}>
                          {step.title}
                        </h5>
                        
                        {step.status === 'pending' && (
                          <div className="mt-4 pt-3 border-t border-border-main/50 flex gap-2">
                            <button 
                              onClick={() => updateStatus(step.id, 'done')}
                              className="flex-1 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 text-[10px] font-black uppercase tracking-widest rounded-lg transition-colors shadow-sm" 
                              style={{ color: 'var(--primary)' }}
                            >
                              Fait ✅
                            </button>
                            <button 
                              onClick={() => updateStatus(step.id, 'postponed')}
                              className="flex-1 py-1.5 bg-card-bg hover:bg-slate-100 border border-border-main text-text-muted text-[10px] font-black uppercase tracking-widest rounded-lg transition-colors shadow-sm"
                            >
                              Reporter
                            </button>
                            <button
                              onClick={() => deleteStep(step.id)}
                              className="px-2 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 rounded-lg transition-colors shadow-sm flex items-center justify-center"
                              title="Supprimer l'étape"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        )}
                        {step.status === 'postponed' && (
                          <div className="mt-4 pt-3 border-t border-border-main/50 flex gap-2">
                            <button 
                              onClick={() => updateStatus(step.id, 'pending')}
                              className="flex-1 py-1.5 bg-card-bg hover:bg-slate-100 border border-border-main text-text-muted text-[10px] font-black uppercase tracking-widest rounded-lg transition-colors shadow-sm"
                            >
                              Re-planifier
                            </button>
                            <button
                              onClick={() => deleteStep(step.id)}
                              className="px-2 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 rounded-lg transition-colors shadow-sm flex items-center justify-center"
                              title="Supprimer l'étape"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
            
            <div className="pt-6 mt-6 border-t border-border-main/50 relative z-10">
              <button 
                onClick={() => {
                  localStorage.setItem('pending_devis_plan', JSON.stringify(treatmentPlan));
                  toast.loading('Préparation du devis...', { duration: 1000 });
                  setTimeout(() => {
                    toast.success('Le Master Plan est pré-chargé pour la comptabilité.');
                  }, 1200);
                }}
                disabled={treatmentPlan.length === 0}
                className={cn(
                  "w-full py-4 rounded-2xl text-xs font-black uppercase tracking-[0.15em] shadow-xl transition-all flex items-center justify-center gap-2 border",
                  treatmentPlan.length === 0 
                    ? "bg-slate-200 dark:bg-slate-800 text-slate-400 border-transparent cursor-not-allowed" 
                    : "bg-slate-900 dark:bg-slate-800 text-white hover:bg-black active:scale-95 border-slate-700"
                )}
              >
                <Sparkles size={16} />
                Générer Devis Global
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
