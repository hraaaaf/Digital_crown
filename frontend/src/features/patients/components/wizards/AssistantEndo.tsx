import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, CheckCircle2, HeartPulse } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantEndoProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'douleur',
    title: "Symptomatologie et Douleur",
    subtitle: "Décrivez la plainte principale du patient.",
    options: [
      { id: 'd_none', label: "Aucune douleur (Découverte fortuite ou radio)", value: 0 },
      { id: 'd_prov', label: "Douleur provoquée courte (froid/sucre)", value: 1 },
      { id: 'd_spont', label: "Douleur spontanée, nocturne, irradiante", value: 2 },
      { id: 'd_mast', label: "Douleur à la pression / mastication", value: 3 }
    ]
  },
  {
    id: 'vitalite',
    title: "Test de Vitalité Pulpaire (Froid/Électrique)",
    subtitle: "Résultat du test de sensibilité.",
    options: [
      { id: 'v_norm', label: "Positif (Normale, réponse brève)", value: 0 },
      { id: 'v_exag', label: "Positif (Exagérée, persistante)", value: 1 },
      { id: 'v_neg', label: "Négatif (Aucune réponse)", value: 2 }
    ]
  },
  {
    id: 'radio',
    title: "Signes Radiographiques",
    subtitle: "Observation à la radiographie rétro-alvéolaire.",
    options: [
      { id: 'r_norm', label: "Espace desmodontal normal", value: 0 },
      { id: 'r_elarg', label: "Élargissement desmodontal apical", value: 1 },
      { id: 'r_lesion', label: "Lésion radio-claire (Granulome/Kyste)", value: 2 }
    ]
  }
];

export const AssistantEndo: React.FC<AssistantEndoProps> = ({ onComplete, onCancel }) => {
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
    const selectedLabel = (questionId: string, value: number | undefined) => {
      const question = QUESTIONS.find((item) => item.id === questionId);
      return question?.options.find((option) => option.value === value)?.label || 'Non renseigné';
    };

    const observations = [
      `Douleur rapportée : ${selectedLabel('douleur', finalAnswers.douleur)}`,
      `Test de sensibilité rapporté : ${selectedLabel('vitalite', finalAnswers.vitalite)}`,
      `Observation radiographique rapportée : ${selectedLabel('radio', finalAnswers.radio)}`,
    ];

    const summary = [
      `Observations recueillies : ${observations.join(' ; ')}.`,
      "Données à confirmer / compléter : anamnèse, examen clinique, tests de sensibilité comparatifs et interprétation de l'imagerie par le praticien.",
      "Ces éléments ne suffisent pas à établir automatiquement un diagnostic pulpaire ou péri-apical.",
      "Diagnostic et conduite thérapeutique : décision du praticien après synthèse des données cliniques.",
    ].join(' ');

    onComplete(summary, []);
  }, 1500);
};

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <Activity className="w-12 h-12 text-amber-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Synthèse des observations endodontiques...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-amber-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
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
                      ? "bg-amber-500/10 border-amber-500 text-amber-600 dark:text-amber-400 shadow-md shadow-amber-500/10" 
                      : "bg-card-bg border-border-main hover:border-amber-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-amber-500 bg-amber-500 text-white" : "border-slate-300 group-hover:border-amber-400"
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
