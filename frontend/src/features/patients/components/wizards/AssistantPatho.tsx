import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Microscope, CheckCircle2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantPathoProps {
  onComplete: (diagnostic: string, plan: any[]) => void;
  onCancel: () => void;
}

const QUESTIONS = [
  {
    id: 'type',
    title: "Aspect Clinique de la Lésion",
    subtitle: "Sélectionnez le type de manifestation muqueuse.",
    options: [
      { id: 't_ulcere', label: "Ulcération (Aphte, lésion traumatique)", value: 0 },
      { id: 't_blanche', label: "Lésion Blanche (Lichen, Leucoplasie, Candidose)", value: 1 },
      { id: 't_rouge', label: "Lésion Rouge / Vésiculeuse (Herpès, Érythème)", value: 2 },
      { id: 't_tumeur', label: "Tuméfaction / Excroissance (Diapneusie, Papillome)", value: 3 }
    ]
  },
  {
    id: 'duree',
    title: "Durée d'évolution",
    subtitle: "Depuis quand la lésion est-elle présente ?",
    options: [
      { id: 'd_aigue', label: "Aiguë (< 2 semaines)", value: 0 },
      { id: 'd_chronique', label: "Chronique (Persistante, > 2 semaines)", value: 1 }
    ]
  },
  {
    id: 'symptome',
    title: "Symptomatologie Associée",
    subtitle: "Signes fonctionnels ressentis par le patient.",
    options: [
      { id: 's_rien', label: "Asymptomatique", value: 0 },
      { id: 's_douleur', label: "Douloureux / Brûlure", value: 1 },
      { id: 's_suspect', label: "Induration / Saignement / Adénopathie", value: 2 }
    ]
  }
];

export const AssistantPatho: React.FC<AssistantPathoProps> = ({ onComplete, onCancel }) => {
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
      let diag = "Lésion Muqueuse Buccale";
      const steps = [];

      // Logic Patho
      if (finalAnswers.type === 0) {
        if (finalAnswers.duree === 0) {
          diag = "Ulcération Aiguë (Aphtose ou Traumatique)";
          steps.push({ title: 'Élimination du facteur traumatique (si existant)', assistant: 'general' });
          steps.push({ title: 'Prescription gel cicatrisant/anesthésique', assistant: 'general' });
        } else {
          diag = "Ulcération Chronique Persistante";
        }
      } else if (finalAnswers.type === 1) {
        diag = "Lésion Blanche (Suspicion Lichen / Candidose / Leucoplasie)";
        if (finalAnswers.symptome === 1) {
          steps.push({ title: 'Prescription Antifongique (Épreuve thérapeutique)', assistant: 'general' });
        }
      } else if (finalAnswers.type === 2) {
        diag = "Lésion Érythémateuse ou Vésiculeuse";
        if (finalAnswers.duree === 0) {
          steps.push({ title: 'Traitement Antiviral (si primo-infection herpétique)', assistant: 'general' });
        }
      } else if (finalAnswers.type === 3) {
        diag = "Tuméfaction / Excroissance bénigne probable";
        steps.push({ title: 'Exérèse chirurgicale (Biopsie exérèse)', assistant: 'chirurgie' });
        steps.push({ title: 'Analyse Anatomo-Pathologique (Anapath)', assistant: 'patho' });
      }

      // RED FLAGS (Lésion suspecte)
      if (finalAnswers.duree === 1 && (finalAnswers.type === 0 || finalAnswers.type === 1) || finalAnswers.symptome === 2) {
        diag = "Lésion Suspecte (À investiguer urgemment)";
        steps.unshift({ title: 'Prise de photos intra-orales détaillées', assistant: 'general' });
        steps.push({ title: 'Biopsie incisionnelle pour analyse', assistant: 'chirurgie' });
        steps.push({ title: 'Adressage en service de Pathologie Buccale / Maxillo-facial', assistant: 'general' });
      } else if (finalAnswers.type !== 3) {
        steps.push({ title: 'Surveillance à 7-14 jours', assistant: 'patho' });
      }

      onComplete(diag, steps);
    }, 1500);
  };

  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-4">
        <Microscope className="w-12 h-12 text-teal-500 animate-pulse" />
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">Analyse de la Lésion Muqueuse...</h3>
      </div>
    );
  }

  const question = QUESTIONS[currentStep];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1">
          {QUESTIONS.map((_, idx) => (
            <div key={idx} className={cn("h-1.5 rounded-full transition-all duration-300", idx <= currentStep ? "w-8 bg-teal-500" : "w-4 bg-slate-200 dark:bg-slate-700")} />
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
                      ? "bg-teal-500/10 border-teal-500 text-teal-600 dark:text-teal-400 shadow-md shadow-teal-500/10" 
                      : "bg-card-bg border-border-main hover:border-teal-400 hover:shadow-sm text-text-main"
                  )}
                >
                  <span className="font-bold">{opt.label}</span>
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected ? "border-teal-500 bg-teal-500 text-white" : "border-slate-300 group-hover:border-teal-400"
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
