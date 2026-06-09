import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Smile, CheckCircle2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantOrthoProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'motif',
    title: "Problème Principal (Motif)",
    subtitle: "Sélectionnez l'anomalie dominante.",
    options: [
      { id: 'm_encomb', label: "Encombrement / Chevauchement", value: 0 },
      { id: 'm_espace', label: "Espaces / Diastèmes", value: 1 },
      { id: 'm_sagittal', label: "Décalage osseux (Classe II, Classe III)", value: 2 },
      { id: 'm_habitude', label: "Habitude déformante (Pouce, Déglutition atypique)", value: 3 }
    ]
  },
  {
    id: 'croissance',
    title: "Stade de Croissance",
    subtitle: "Potentiel de croissance osseuse.",
    options: [
      { id: 'c_active', label: "Croissance active (Enfant / Pré-pubertaire)", value: 0 },
      { id: 'c_adulte', label: "Fin de croissance / Adulte", value: 1 }
    ]
  },
  {
    id: 'preference',
    title: "Préférence Thérapeutique du Patient",
    subtitle: "Choix de l'appareillage (si applicable).",
    options: [
      { id: 'p_align', label: "Aligneurs invisibles (Gouttières)", value: 0 },
      { id: 'p_multi', label: "Multi-attaches classique (Bagues)", value: 1 },
      { id: 'p_inter', label: "Traitement fonctionnel (Éducateur / Amovible)", value: 2 }
    ]
  }
];

export const AssistantOrtho: React.FC<AssistantOrthoProps> = ({ onComplete, onCancel }) => {
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
      let diag = "Anomalie Orthodontique";
      const steps = [];

      // Logic Ortho
      steps.push({ title: 'Bilan Orthodontique Complet (Téléradiographie + Empreintes + Photos)', assistant: 'general' });
      steps.push({ title: 'Présentation du Plan de Traitement ODF', assistant: 'ortho' });

      if (finalAnswers.croissance === 0 && (finalAnswers.motif === 2 || finalAnswers.motif === 3 || finalAnswers.preference === 2)) {
        diag = "Dysmorphose interceptable (Croissance active)";
        if (finalAnswers.motif === 3) {
          diag += " avec parafonction";
          steps.push({ title: 'Rééducation myofonctionnelle (Orthophonie)', assistant: 'general' });
        }
        steps.push({ title: 'Appareillage Orthopédique / Interceptif (Plaque, Éducateur)', assistant: 'ortho' });
        steps.push({ title: 'Surveillance de l\'évolution', assistant: 'ortho' });
      } else {
        if (finalAnswers.motif === 0) diag = "Encombrement Dentaire";
        else if (finalAnswers.motif === 1) diag = "Diastèmes / Espacement Dentaire";
        else if (finalAnswers.motif === 2) diag = "Dysmorphose Squelettique (Classe II/III)";
        else diag = "Malocclusion";

        if (finalAnswers.croissance === 1 && finalAnswers.motif === 2) {
          diag += " (Adulte - Décalage Squelettique)";
          steps.push({ title: 'Avis Chirurgie Maxillo-Faciale (Orthognathique)', assistant: 'chirurgie' });
        }

        if (finalAnswers.preference === 0) {
          steps.push({ title: 'Traitement global par Aligneurs Transparents', assistant: 'ortho' });
        } else {
          steps.push({ title: 'Pose Appareillage Multi-attaches (Bagues)', assistant: 'ortho' });
        }
        
        steps.push({ title: 'Contention en fin de traitement (Fil + Gouttière)', assistant: 'ortho' });
      }

      onComplete(diag, steps);
    }, 1500);
  };

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <Smile className="w-12 h-12 text-indigo-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Génération du Plan Orthodontique...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-indigo-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
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
                      ? "bg-indigo-500/10 border-indigo-500 text-indigo-600 dark:text-indigo-400 shadow-md shadow-indigo-500/10" 
                      : "bg-card-bg border-border-main hover:border-indigo-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-indigo-500 bg-indigo-500 text-white" : "border-slate-300 group-hover:border-indigo-400"
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
