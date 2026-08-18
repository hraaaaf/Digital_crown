import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HeartPulse, CheckCircle2, AlertTriangle, ArrowRight, Save } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantParoProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'cal',
    title: "Perte d'Attache Clinique (CAL) interdentaire maximale",
    subtitle: "Sélectionnez la perte d'attache la plus sévère observée.",
    options: [
      { id: 'cal_0', label: "Aucune / Saine", value: 0 },
      { id: 'cal_1_2', label: "1 à 2 mm", value: 1 },
      { id: 'cal_3_4', label: "3 à 4 mm", value: 2 },
      { id: 'cal_5', label: "≥ 5 mm", value: 3 }
    ]
  },
  {
    id: 'complexity',
    title: "Facteurs de complexité locaux",
    subtitle: "Sélectionnez s'il y a des facteurs aggravants.",
    options: [
      { id: 'comp_none', label: "Aucun", value: 0 },
      { id: 'comp_furc', label: "Atteinte furcations (Cl II/III) ou défauts angulaires ≥3mm", value: 1 },
      { id: 'comp_loss', label: "Perte de ≥5 dents pour raisons parodontales", value: 2 }
    ]
  },
  {
    id: 'bop',
    title: "Indice de Saignement (BOP)",
    subtitle: "Évaluation de l'inflammation gingivale.",
    options: [
      { id: 'bop_low', label: "< 10%", value: 0 },
      { id: 'bop_med', label: "10% à 30% (Localisé)", value: 1 },
      { id: 'bop_high', label: "> 30% (Généralisé)", value: 2 }
    ]
  },
  {
    id: 'risk',
    title: "Terrain et Facteurs de risque (Grading)",
    subtitle: "Évaluation du risque de progression rapide.",
    options: [
      { id: 'risk_none', label: "Non-fumeur, Normoglycémique", value: 0 },
      { id: 'risk_smoke', label: "Fumeur (< 10 cig/j)", value: 1 },
      { id: 'risk_high', label: "Fumeur (≥ 10 cig/j) ou Diabète (HbA1c ≥ 7%)", value: 2 }
    ]
  }
];

export const AssistantParo: React.FC<AssistantParoProps> = ({ onComplete, onCancel }) => {
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
      const selected = QUESTIONS.map((question) => {
        const value = finalAnswers[question.id];
        const option = question.options.find((item) => item.value === value);
        return `${question.title} : ${option?.label ?? 'Non renseigné'}`;
      });

      const summary = [
        'Synthèse parodontale structurée.',
        `Observations recueillies : ${selected.join(' ; ')}.`,
        'Ces réponses décrivent uniquement les informations saisies dans le questionnaire.',
        'Aucun diagnostic, examen complémentaire, médicament, dispositif, orientation ou traitement n’est déterminé automatiquement.',
        'Diagnostic, examens complémentaires et conduite thérapeutique : décision exclusive du praticien après validation clinique.'
      ].join(' ');

      onComplete(summary, []);
    }, 1500);
  };

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <HeartPulse className="w-12 h-12 text-rose-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Génération du Diagnostic AAP/EFP 2017...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-rose-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
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
                      ? "bg-rose-500/10 border-rose-500 text-rose-600 dark:text-rose-400 shadow-md shadow-rose-500/10" 
                      : "bg-card-bg border-border-main hover:border-rose-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-rose-500 bg-rose-500 text-white" : "border-slate-300 group-hover:border-rose-400"
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
        <button 
          onClick={onCancel}
          className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest"
        >
          Annuler
        </button>
        {currentStep > 0 && (
          <button 
            onClick={() => setCurrentStep(prev => prev - 1)}
            className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest"
          >
            Retour
          </button>
        )}
      </div>
    </div>
  );
};
