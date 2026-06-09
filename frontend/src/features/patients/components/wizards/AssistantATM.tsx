import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, CheckCircle2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantATMProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'symptome',
    title: "Symptôme Principal",
    subtitle: "Sélectionnez le signe clinique dominant.",
    options: [
      { id: 's_bruit', label: "Bruits articulaires (Claquements / Crissements)", value: 0 },
      { id: 's_douleur', label: "Douleurs musculaires (Cervicales, masséters) au réveil", value: 1 },
      { id: 's_blocage', label: "Limitation d'ouverture buccale / Blocage", value: 2 }
    ]
  },
  {
    id: 'parafonction',
    title: "Parafonctions (Bruxisme)",
    subtitle: "Habitudes nocives identifiées.",
    options: [
      { id: 'p_nocturne', label: "Grincement nocturne (Bruxisme excentré)", value: 0 },
      { id: 'p_diurne', label: "Serrement diurne (Bruxisme centré)", value: 1 },
      { id: 'p_aucune', label: "Aucune parafonction évidente", value: 2 }
    ]
  },
  {
    id: 'facteur',
    title: "Facteurs déclenchants",
    subtitle: "Contexte d'apparition des troubles.",
    options: [
      { id: 'f_stress', label: "Période de stress intense", value: 0 },
      { id: 'f_trauma', label: "Traumatisme maxillo-facial récent", value: 1 },
      { id: 'f_aucun', label: "Aucun (Apparition progressive/spontanée)", value: 2 }
    ]
  }
];

export const AssistantATM: React.FC<AssistantATMProps> = ({ onComplete, onCancel }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [isCalculating, setIsCalculating] = useState(false);

  const handleSelect = (questionId: string, value: number) => {
    const newAnswers = { ...answers, [questionId]: value };
    setAnswers(newAnswers);

    if (currentStep < QUESTIONS.length - 1) {
      setTimeout(() => setCurrentStep(prev => prev + 1), 300);
    } else {
      generateDiagnosis(newAnswers);
    }
  };

  const generateDiagnosis = (finalAnswers: Record<string, number>) => {
    setIsCalculating(true);
    
    setTimeout(() => {
      let diag = "Dysfonctionnement de l'Appareil Manducateur (DAM)";
      const steps = [];

      // Logic ATM
      if (finalAnswers.symptome === 1) {
        diag = "Myalgie masticatoire / DAM musculaire";
      } else if (finalAnswers.symptome === 2) {
        diag = "DAM Articulaire (Déplacement discal irréductible)";
      } else {
        diag = "DAM Articulaire (Déplacement discal réductible)";
      }

      if (finalAnswers.parafonction === 0) {
        diag += " aggravé par Bruxisme Nocturne (Excentré)";
        steps.push({ title: 'Gouttière de libération occlusale (Port nocturne)', assistant: 'atm' });
      } else if (finalAnswers.parafonction === 1) {
        diag += " aggravé par Bruxisme Diurne (Centré)";
        steps.push({ title: 'Prise de conscience / Biofeedback (Éviter le serrement)', assistant: 'atm' });
        steps.push({ title: 'Prescription Myorelaxants (Courte durée)', assistant: 'general' });
      }

      if (finalAnswers.facteur === 0) {
        steps.push({ title: 'Gestion du stress / Relaxation', assistant: 'general' });
      } else if (finalAnswers.facteur === 1) {
        diag = "DAM post-traumatique";
        steps.unshift({ title: 'Prescription CBCT / IRM des ATM', assistant: 'general' });
        steps.push({ title: 'Avis spécialisé (Maxillo-facial)', assistant: 'chirurgie' });
      }

      if (finalAnswers.symptome === 1 || finalAnswers.symptome === 2) {
        steps.push({ title: 'Kinésithérapie Maxillo-Faciale (Séances)', assistant: 'general' });
      }

      // Toujours une surveillance
      if (!steps.find(s => s.assistant === 'chirurgie')) {
         steps.push({ title: 'Réévaluation à 1 mois', assistant: 'atm' });
      }

      onComplete(diag, steps);
    }, 1500);
  };

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <Zap className="w-12 h-12 text-fuchsia-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Analyse Occluso-Articulaire...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-fuchsia-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
          ))}
        </div>
        <span className="text-xs font-black text-slate-400">Étape {currentStep + 1} / {QUESTIONS.length}</span>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="flex-1"
        >
          <h2 className="text-xl font-black text-slate-800 dark:text-slate-100 mb-2">{question.title}</h2>
          <p className="text-sm text-slate-500 font-bold mb-8">{question.subtitle}</p>

          <div className="flex flex-col gap-3">
            {question.options.map((opt) => {
              const isSelected = answers[question.id] === opt.value;
              return (
                <button
                  key={opt.id}
                  onClick={() => handleSelect(question.id, opt.value)}
                  className={cn(
                    "p-4 rounded-2xl border text-left flex items-center justify-between transition-all group",
                    isSelected 
                      ? "bg-fuchsia-500/10 border-fuchsia-500 text-fuchsia-600 dark:text-fuchsia-400 shadow-md shadow-fuchsia-500/10" 
                      : "bg-card-bg border-border-main hover:border-fuchsia-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-fuchsia-500 bg-fuchsia-500 text-white" : "border-slate-300 group-hover:border-fuchsia-400"
                  )}>
                    {isSelected && <CheckCircle2 size={12} />}
                  </div>
                </button>
              );
            })}
          </div>
        </motion.div>
      </AnimatePresence>

      <div className="flex items-center justify-between mt-8 pt-4 border-t border-border-main">
        <button onClick={onCancel} className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest">Annuler</button>
        {currentStep > 0 && (
          <button onClick={() => setCurrentStep(prev => prev - 1)} className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest">Retour</button>
        )}
      </div>
    </div>
  );
};
