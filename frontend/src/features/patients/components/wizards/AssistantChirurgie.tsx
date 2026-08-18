import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scissors, CheckCircle2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantChirurgieProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'motif',
    title: "Motif de l'intervention chirurgicale",
    subtitle: "Sélectionnez l'indication principale.",
    options: [
      { id: 'm_carie', label: "Délabrement carieux irrécupérable / Fracture", value: 0 },
      { id: 'm_ortho', label: "Indication Orthodontique (Désencombrement)", value: 1 },
      { id: 'm_sagesse', label: "Dent de sagesse incluse / semi-incluse", value: 2 },
      { id: 'm_paro', label: "Mobilité terminale (Parodontite)", value: 3 }
    ]
  },
  {
    id: 'anatomie',
    title: "Proximité Anatomique (Imagerie)",
    subtitle: "Rapport avec les structures nobles (N.A.I, Sinus Maxillaire).",
    options: [
      { id: 'a_loin', label: "Éloignée des structures nobles", value: 0 },
      { id: 'a_proche', label: "Proximité immédiate (Risque lésionnel)", value: 1 }
    ]
  },
  {
    id: 'risque',
    title: "Terrain et Risque Médical",
    subtitle: "Sélectionnez les facteurs de risque liés au patient.",
    options: [
      { id: 'r_sain', label: "Patient sain (ASA 1 ou 2)", value: 0 },
      { id: 'r_coag', label: "Sous anticoagulants / Antiagrégants (Risque hémorragique)", value: 1 },
      { id: 'r_bis', label: "Traitement par Bisphosphonates (Risque d'ostéonécrose)", value: 2 }
    ]
  }
];

export const AssistantChirurgie: React.FC<AssistantChirurgieProps> = ({ onComplete, onCancel }) => {
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
      const motif = QUESTIONS[0].options.find(opt => opt.value === finalAnswers.motif)?.label ?? 'Non renseigné';
      const anatomie = QUESTIONS[1].options.find(opt => opt.value === finalAnswers.anatomie)?.label ?? 'Non renseignée';
      const risque = QUESTIONS[2].options.find(opt => opt.value === finalAnswers.risque)?.label ?? 'Non renseigné';

      const summary = [
        'Synthèse pré-opératoire structurée.',
        `Motif rapporté : ${motif}.`,
        `Rapport anatomique renseigné : ${anatomie}.`,
        `Terrain / risque médical renseigné : ${risque}.`,
        'Ces réponses constituent des éléments de vigilance à confronter à l’examen clinique, à l’imagerie disponible et au dossier médical.',
        'Aucun diagnostic chirurgical, examen complémentaire, protocole médicamenteux ou geste opératoire n’est déterminé automatiquement.',
        'Indication, examens complémentaires, conduite péri-opératoire et traitement : décision exclusive du praticien après validation clinique.'
      ].join('\n');

      onComplete(summary, []);
    }, 1500);
  };

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <Scissors className="w-12 h-12 text-purple-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Synthèse pré-opératoire structurée...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-purple-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
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
                      ? "bg-purple-500/10 border-purple-500 text-purple-600 dark:text-purple-400 shadow-md shadow-purple-500/10"
                      : "bg-card-bg border-border-main hover:border-purple-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-purple-500 bg-purple-500 text-white" : "border-slate-300 group-hover:border-purple-400"
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
