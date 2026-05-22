import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Diamond, CheckCircle2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantProtheseProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'perte',
    title: "Type de perte de substance / État coronaire",
    subtitle: "Sélectionnez l'étendue de la destruction tissulaire.",
    options: [
      { id: 'p_min', label: "Lésion coronaire mineure à moyenne (< 2 parois)", value: 0 },
      { id: 'p_depulp', label: "Dent dépulpée avec perte modérée", value: 1 },
      { id: 'p_maj', label: "Perte coronaire majeure (≥ 2 parois)", value: 2 },
      { id: 'p_edent', label: "Édentement (Dent manquante)", value: 3 }
    ]
  },
  {
    id: 'esthetique',
    title: "Exigence Esthétique",
    subtitle: "Localisation de la dent concernée.",
    options: [
      { id: 'e_faible', label: "Faible / Modérée (Secteur Postérieur)", value: 0 },
      { id: 'e_haute', label: "Haute (Secteur Antérieur, Sourire)", value: 1 }
    ]
  },
  {
    id: 'occlusion',
    title: "Contexte Occlusal",
    subtitle: "Évaluation des contraintes mécaniques.",
    options: [
      { id: 'o_norm', label: "Occlusion fonctionnelle normale", value: 0 },
      { id: 'o_brux', label: "Bruxisme / Parafonctions / Usure sévère", value: 1 }
    ]
  }
];

export const AssistantProthese: React.FC<AssistantProtheseProps> = ({ onComplete, onCancel }) => {
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
      let diag = "Reconstruction coronaire";
      const steps = [];

      // Logic Prothese
      if (finalAnswers.perte === 3) {
        diag = "Édentement";
        if (finalAnswers.esthetique === 1) {
          diag += " avec fort préjudice esthétique";
          steps.push({ title: 'Empreinte pour prothèse provisoire immédiate', assistant: 'prothese' });
        }
        steps.push({ title: 'Étude implantaire (CBCT + Guide)', assistant: 'chirurgie' });
        steps.push({ title: 'Pose d\'Implant / Prothèse sur Implant', assistant: 'prothese' });
      } else if (finalAnswers.perte === 2 || finalAnswers.perte === 1) {
        diag = "Délabrement coronaire majeur";
        if (finalAnswers.occlusion === 1) {
          diag += " (Contexte de Bruxisme)";
          steps.push({ title: 'Couronne monolithique ultra-résistante (Zircone ou Emax)', assistant: 'prothese' });
          steps.push({ title: 'Gouttière de libération occlusale post-traitement', assistant: 'atm' });
        } else {
          if (finalAnswers.esthetique === 1) {
            steps.push({ title: 'Couronne Céramo-Céramique Stratifiée Haute Esthétique', assistant: 'prothese' });
          } else {
            steps.push({ title: 'Couronne Céramo-Métallique ou Zircone', assistant: 'prothese' });
          }
        }
        
        if (finalAnswers.perte === 2) {
          steps.unshift({ title: 'Reconstitution Corono-Radiculaire (Inlay-core / RCR)', assistant: 'prothese' });
        }
      } else {
        if (finalAnswers.esthetique === 1) {
          diag = "Lésion coronaire du secteur esthétique";
          steps.push({ title: 'Restauration Composite Stratifié / Facette', assistant: 'prothese' });
        } else {
          diag = "Lésion coronaire du secteur postérieur";
          steps.push({ title: 'Inlay / Onlay Composite ou Céramique', assistant: 'prothese' });
        }
      }

      onComplete(diag, steps);
    }, 1500);
  };

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <Diamond className="w-12 h-12 text-blue-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Génération du Plan Prothétique...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-blue-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
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
                      ? "bg-blue-500/10 border-blue-500 text-blue-600 dark:text-blue-400 shadow-md shadow-blue-500/10" 
                      : "bg-card-bg border-border-main hover:border-blue-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-blue-500 bg-blue-500 text-white" : "border-slate-300 group-hover:border-blue-400"
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
