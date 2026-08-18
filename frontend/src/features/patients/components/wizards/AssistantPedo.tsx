import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Baby, CheckCircle2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantPedoProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'denture',
    title: "Stade de Denture",
    subtitle: "Identifiez l'âge dentaire de l'enfant.",
    options: [
      { id: 'd_temp', label: "Denture Temporaire (< 6 ans)", value: 0 },
      { id: 'd_mixte', label: "Denture Mixte (6 à 12 ans)", value: 1 },
      { id: 'd_perm', label: "Denture Permanente Jeune (> 12 ans)", value: 2 }
    ]
  },
  {
    id: 'motif',
    title: "Motif de la Consultation",
    subtitle: "Raison principale de la visite.",
    options: [
      { id: 'm_bilan', label: "Bilan / Prévention / Prophylaxie", value: 0 },
      { id: 'm_carie', label: "Lésion carieuse / Douleur pulpaire", value: 1 },
      { id: 'm_trauma', label: "Traumatisme (Choc / Fracture / Luxation)", value: 2 }
    ]
  },
  {
    id: 'comportement',
    title: "Comportement de l'enfant (Échelle de Frankl)",
    subtitle: "Évaluation de la coopération au fauteuil.",
    options: [
      { id: 'c_positif', label: "Coopératif (Frankl 3 ou 4)", value: 0 },
      { id: 'c_negatif', label: "Non coopératif / Anxieux / Phobique (Frankl 1 ou 2)", value: 1 }
    ]
  }
];

export const AssistantPedo: React.FC<AssistantPedoProps> = ({ onComplete, onCancel }) => {
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
      const denture = QUESTIONS[0].options.find(opt => opt.value === finalAnswers.denture)?.label ?? 'Non renseignée';
      const motif = QUESTIONS[1].options.find(opt => opt.value === finalAnswers.motif)?.label ?? 'Non renseigné';
      const comportement = QUESTIONS[2].options.find(opt => opt.value === finalAnswers.comportement)?.label ?? 'Non renseigné';

      const summary = [
        'Synthèse pédodontique structurée.',
        `Stade de denture renseigné : ${denture}.`,
        `Motif rapporté : ${motif}.`,
        `Coopération / comportement renseigné : ${comportement}.`,
        'Ces éléments doivent être confrontés à l’examen clinique, aux antécédents, à l’âge réel et aux examens complémentaires jugés nécessaires par le praticien.',
        'Aucun diagnostic, examen radiographique, sédation, anesthésie, prescription ou traitement dentaire n’est déterminé automatiquement.',
        'Diagnostic, examens complémentaires et conduite thérapeutique : décision exclusive du praticien après validation clinique.'
      ].join('\n');

      onComplete(summary, []);
    }, 1500);
  };

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <Baby className="w-12 h-12 text-sky-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Synthèse pédodontique structurée...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-sky-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
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
                      ? "bg-sky-500/10 border-sky-500 text-sky-600 dark:text-sky-400 shadow-md shadow-sky-500/10"
                      : "bg-card-bg border-border-main hover:border-sky-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-sky-500 bg-sky-500 text-white" : "border-slate-300 group-hover:border-sky-400"
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
