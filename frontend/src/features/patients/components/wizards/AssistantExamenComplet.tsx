import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Stethoscope, AlertTriangle, CheckCircle2, ChevronRight } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface AssistantExamenCompletProps {
  onComplete: (diagnostic: string, plan: any[], suggestedNextAssistant?: string | null) => void;
  onCancel: () => void;
}

type Branch = 'none' | 'urgence' | 'routine';

// ── Branche Urgence ────────────────────────────────────────────────────────
const URGENCE_STEPS = [
  {
    id: 'type_douleur',
    title: 'Type de douleur / motif urgent',
    subtitle: 'Caractérisez la plainte principale.',
    options: [
      { id: 'u_pulp', label: 'Douleur dentaire intense (pulpaire)', value: 'pulpaire' },
      { id: 'u_trauma', label: 'Traumatisme / fracture dentaire', value: 'trauma' },
      { id: 'u_paro', label: 'Tuméfaction / abcès parodontal', value: 'abces_paro' },
      { id: 'u_atm', label: 'Blocage / douleur articulaire (ATM)', value: 'atm' },
    ],
  },
  {
    id: 'localisation',
    title: 'Localisation de la douleur',
    subtitle: 'Secteur concerné.',
    options: [
      { id: 'l_max_ant', label: 'Maxillaire antérieur (1-3 / 1-3)', value: 'max_ant' },
      { id: 'l_max_post', label: 'Maxillaire postérieur (4-8)', value: 'max_post' },
      { id: 'l_mand_ant', label: 'Mandibulaire antérieur', value: 'mand_ant' },
      { id: 'l_mand_post', label: 'Mandibulaire postérieur', value: 'mand_post' },
      { id: 'l_diff', label: 'Diffuse / impossible à localiser', value: 'diffuse' },
    ],
  },
  {
    id: 'caractere',
    title: 'Caractère de la douleur',
    subtitle: 'Évolution dans le temps.',
    options: [
      { id: 'c_spon', label: 'Spontanée, permanente, lancinante', value: 'spontanee' },
      { id: 'c_prov', label: 'Provoquée (froid/chaud), disparaît vite', value: 'provoquee' },
      { id: 'c_tumor', label: 'Gonflement / tuméfaction visible', value: 'tuméfaction' },
      { id: 'c_pression', label: 'Douleur à la pression / percussion', value: 'percussion' },
    ],
  },
  {
    id: 'signes_gen',
    title: 'Signes généraux associés',
    subtitle: 'Complications systémiques possibles.',
    options: [
      { id: 'sg_ras', label: 'RAS — état général conservé', value: 'ras' },
      { id: 'sg_fievre', label: 'Fièvre (≥ 38°C)', value: 'fievre' },
      { id: 'sg_trismus', label: 'Trismus / difficulté à ouvrir la bouche', value: 'trismus' },
      { id: 'sg_adeno', label: 'Adénopathies / cellulite diffuse', value: 'cellulite' },
    ],
  },
];

// ── Branche Routine ────────────────────────────────────────────────────────
const ROUTINE_STEPS = [
  {
    id: 'antecedents',
    title: 'Antécédents médicaux',
    subtitle: 'Alerte médicale à consigner dans le dossier.',
    options: [
      { id: 'a_ras', label: 'RAS — Patient sain', value: 'ras' },
      { id: 'a_hta', label: 'HTA / Diabète / Anticoagulants', value: 'hta_diabete' },
      { id: 'a_allergie', label: 'Allergie médicamenteuse connue (pénicilline…)', value: 'allergie' },
      { id: 'a_cardio', label: 'Cardiopathie / Prothèse valvulaire (haut risque infectieux)', value: 'cardio' },
    ],
  },
  {
    id: 'hygiene',
    title: 'Hygiène bucco-dentaire',
    subtitle: 'Évaluation clinique de la plaque et du tartre.',
    options: [
      { id: 'h_bonne', label: 'Bonne — brossage régulier, gencive saine', value: 'bonne' },
      { id: 'h_moy', label: 'Moyenne — plaque visible, tartre localisé', value: 'moyenne' },
      { id: 'h_med', label: 'Médiocre — tartre abondant, inflammation généralisée', value: 'mediocre' },
    ],
  },
  {
    id: 'paro',
    title: 'Statut parodontal',
    subtitle: 'Examen des gencives, profondeurs de poche, mobilités.',
    options: [
      { id: 'p_sain', label: 'Parodonte sain — pas de saignement', value: 'sain' },
      { id: 'p_gingi', label: 'Gingivite — saignement au sondage, pas de poches', value: 'gingivite' },
      { id: 'p_paro_mod', label: 'Parodontite modérée — poches 4-5 mm', value: 'paro_moderee' },
      { id: 'p_paro_sev', label: 'Parodontite sévère — poches ≥6 mm, mobilités', value: 'paro_severe' },
    ],
  },
  {
    id: 'dentaire',
    title: 'Statut dentaire',
    subtitle: 'Caries actives et restaurations existantes.',
    options: [
      { id: 'd_intact', label: 'Denture saine — pas de caries, restaurations correctes', value: 'sain' },
      { id: 'd_caries', label: 'Caries actives présentes (1 ou plusieurs)', value: 'caries' },
      { id: 'd_rest', label: 'Restaurations défaillantes / fractures coronaires', value: 'restaurations' },
      { id: 'd_caries_rest', label: 'Caries + restaurations défaillantes', value: 'caries_et_restaurations' },
    ],
  },
  {
    id: 'occlusion',
    title: 'Examen occlusal',
    subtitle: 'Classe, guidances, parafonctions.',
    options: [
      { id: 'o_norm', label: 'Occlusion normale — classe I, pas de parafonction', value: 'normale' },
      { id: 'o_classe', label: 'Malocclusion — classe II ou III', value: 'malocclusion' },
      { id: 'o_brux', label: 'Bruxisme / usure marquée / facettes', value: 'bruxisme' },
      { id: 'o_sup', label: 'Supracontacts / déflexions en fermeture', value: 'supracontacts' },
    ],
  },
  {
    id: 'tissus_mous',
    title: 'Examen des tissus mous',
    subtitle: 'Muqueuses, langue, plancher, lèvres.',
    options: [
      { id: 't_ras', label: 'RAS — muqueuses saines', value: 'ras' },
      { id: 't_lesion', label: 'Lésion suspecte (leucoplasie, érythroplasie, ulcère persistant)', value: 'lesion_suspecte' },
      { id: 't_aphte', label: 'Aphtes / stomatite ulcéreuse récidivante', value: 'aphtes' },
      { id: 't_sec', label: 'Sécheresse buccale / xérostomie', value: 'xerostomie' },
    ],
  },
];

// ── Moteurs de diagnostic ─────────────────────────────────────────────────

function buildUrgenceDiag(ans: Record<string, string>): { diag: string; steps: any[]; next: string | null } {
  const selectedLabel = (questionId: string, value: string | undefined) => {
    const question = URGENCE_STEPS.find((item) => item.id === questionId);
    return question?.options.find((option) => option.value === value)?.label || 'Non renseigné';
  };

  const observations = [
    `Motif urgent rapporté : ${selectedLabel('type_douleur', ans.type_douleur)}`,
    `Localisation rapportée : ${selectedLabel('localisation', ans.localisation)}`,
    `Caractère rapporté : ${selectedLabel('caractere', ans.caractere)}`,
    `Signes généraux rapportés : ${selectedLabel('signes_gen', ans.signes_gen)}`,
  ];

  const vigilance: string[] = [];
  if (ans.signes_gen === 'fievre') {
    vigilance.push('Fièvre ≥ 38°C rapportée : signal de vigilance systémique à évaluer cliniquement sans délai.');
  }
  if (ans.signes_gen === 'trismus') {
    vigilance.push("Trismus rapporté : signal de vigilance nécessitant une évaluation clinique de l'extension et de la gravité.");
  }
  if (ans.signes_gen === 'cellulite') {
    vigilance.push('Adénopathies / cellulite diffuse rapportées : signal de vigilance nécessitant une évaluation clinique immédiate.');
  }

  const summary = [
    `Observations recueillies : ${observations.join(' ; ')}.`,
    vigilance.length ? `Vigilance : ${vigilance.join(' ')}` : 'Vigilance : aucun signe général critique déclaré dans ce questionnaire.',
    "Données à confirmer / compléter : examen extra- et intra-oral, constantes si indiquées, tests cliniques ciblés et examens complémentaires décidés par le praticien.",
    "Ce questionnaire ne pose pas automatiquement de diagnostic et ne détermine pas de traitement.",
    "Diagnostic et conduite thérapeutique : décision du praticien après évaluation clinique complète.",
  ].join(' ');

  return { diag: summary, steps: [], next: null };
}

function buildRoutineDiag(ans: Record<string, string>): { diag: string; steps: any[]; next: string | null } {
  const selectedLabel = (questionId: string, value: string | undefined) => {
    const question = ROUTINE_STEPS.find((item) => item.id === questionId);
    return question?.options.find((option) => option.value === value)?.label || 'Non renseigné';
  };

  const observations = [
    `Antécédents rapportés : ${selectedLabel('antecedents', ans.antecedents)}`,
    `Hygiène renseignée : ${selectedLabel('hygiene', ans.hygiene)}`,
    `Statut parodontal renseigné : ${selectedLabel('paro', ans.paro)}`,
    `Statut dentaire renseigné : ${selectedLabel('dentaire', ans.dentaire)}`,
    `Examen occlusal renseigné : ${selectedLabel('occlusion', ans.occlusion)}`,
    `Tissus mous renseignés : ${selectedLabel('tissus_mous', ans.tissus_mous)}`,
  ];

  const vigilance: string[] = [];
  if (ans.antecedents === 'cardio') {
    vigilance.push('Antécédent cardiovasculaire / prothèse valvulaire déclaré : indication éventuelle de prophylaxie à qualifier précisément selon la cardiopathie, le geste envisagé et les recommandations applicables.');
  }
  if (ans.antecedents === 'allergie') {
    vigilance.push('Allergie médicamenteuse déclarée : substance, réaction, gravité et statut actuel à confirmer avant toute prescription.');
  }
  if (ans.antecedents === 'hta_diabete') {
    vigilance.push('HTA / diabète / anticoagulants déclarés : situation médicale et traitements en cours à préciser avant décision clinique.');
  }
  if (ans.paro === 'paro_severe' || ans.paro === 'paro_moderee') {
    vigilance.push('Signes parodontaux rapportés : diagnostic et stade à confirmer par examen parodontal complet et données nécessaires.');
  }
  if (ans.dentaire === 'caries' || ans.dentaire === 'caries_et_restaurations' || ans.dentaire === 'restaurations') {
    vigilance.push('Anomalies dentaires rapportées : confirmer dent par dent avant diagnostic, imagerie ou plan thérapeutique.');
  }
  if (ans.occlusion !== 'normale') {
    vigilance.push('Anomalie occlusale / parafonction rapportée : examen fonctionnel à compléter avant conclusion ou traitement.');
  }
  if (ans.tissus_mous === 'lesion_suspecte') {
    vigilance.push('Lésion muqueuse rapportée comme suspecte : examen clinique ciblé, documentation et orientation à décider sans délai selon les constatations du praticien.');
  } else if (ans.tissus_mous !== 'ras') {
    vigilance.push('Anomalie des tissus mous rapportée : description clinique, durée, évolution et facteurs associés à documenter.');
  }

  const summary = [
    `Observations recueillies : ${observations.join(' ; ')}.`,
    vigilance.length ? `Vigilance : ${vigilance.join(' ')}` : 'Vigilance : aucun signal particulier déclaré dans ce questionnaire.',
    "Données à confirmer / compléter : examen clinique complet et examens complémentaires décidés par le praticien selon les indications constatées.",
    "Ce questionnaire ne pose pas automatiquement de diagnostic et ne détermine pas de traitement.",
    "Diagnostic, examens complémentaires et conduite thérapeutique : décision du praticien après validation clinique.",
  ].join(' ');

  return { diag: summary, steps: [], next: null };
}

// ── Composant principal ────────────────────────────────────────────────────

export const AssistantExamenComplet: React.FC<AssistantExamenCompletProps> = ({ onComplete, onCancel }) => {
  const [branch, setBranch] = useState<Branch>('none');
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isCalculating, setIsCalculating] = useState(false);

  const steps = branch === 'urgence' ? URGENCE_STEPS : ROUTINE_STEPS;
  const totalSteps = steps.length;
  const progress = totalSteps > 0 ? Math.round(((currentStep + 1) / totalSteps) * 100) : 0;

  const handleSelect = (questionId: string, value: string) => {
    const newAnswers = { ...answers, [questionId]: value };
    setAnswers(newAnswers);

    if (currentStep < totalSteps - 1) {
      setTimeout(() => setCurrentStep(prev => prev + 1), 280);
    } else {
      setIsCalculating(true);
      setTimeout(() => {
        const result = branch === 'urgence'
          ? buildUrgenceDiag(newAnswers)
          : buildRoutineDiag(newAnswers);
        onComplete(result.diag, result.steps, result.next);
      }, 1400);
    }
  };

  // ── Écran de triage initial ──
  if (branch === 'none') {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3 mb-2">
          <Stethoscope className="w-6 h-6 text-primary" style={{ color: 'var(--primary)' }} />
          <div>
            <h2 className="text-xl font-black text-text-main">Examen Clinique Complet</h2>
            <p className="text-sm text-text-muted font-bold">Commencez par le motif principal de la consultation.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          <button
            onClick={() => { setBranch('urgence'); setCurrentStep(0); }}
            className="flex items-center justify-between p-5 rounded-2xl border-2 border-rose-300 bg-rose-50/50 hover:bg-rose-100/60 hover:border-rose-400 transition-all text-left group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-rose-500/10 text-rose-500 rounded-xl flex items-center justify-center border border-rose-300">
                <AlertTriangle size={22} />
              </div>
              <div>
                <h3 className="font-black text-rose-700 text-base">Urgence / Douleur aiguë</h3>
                <p className="text-xs text-rose-500/80 font-bold mt-0.5">Douleur sévère, tuméfaction, traumatisme, blocage ATM</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-rose-400 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => { setBranch('routine'); setCurrentStep(0); }}
            className="flex items-center justify-between p-5 rounded-2xl border-2 border-emerald-300 bg-emerald-50/50 hover:bg-emerald-100/60 hover:border-emerald-400 transition-all text-left group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-500/10 text-emerald-500 rounded-xl flex items-center justify-center border border-emerald-300">
                <CheckCircle2 size={22} />
              </div>
              <div>
                <h3 className="font-black text-emerald-700 text-base">Contrôle de routine / Bilan</h3>
                <p className="text-xs text-emerald-600/80 font-bold mt-0.5">Examen complet, bilan paro, dentaire, occlusal et tissus mous</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-emerald-400 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        <div className="flex justify-start pt-2">
          <button onClick={onCancel} className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest">Annuler</button>
        </div>
      </div>
    );
  }

  // ── Écran calcul ──
  if (isCalculating) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-5">
        <div className={cn(
          'w-16 h-16 rounded-2xl flex items-center justify-center animate-pulse',
          branch === 'urgence' ? 'bg-rose-500/10 text-rose-500' : 'bg-emerald-500/10 text-emerald-500'
        )}>
          <Stethoscope size={32} />
        </div>
        <h3 className="text-sm font-black uppercase tracking-widest text-slate-500">
          {branch === 'urgence' ? 'Protocole d\'urgence en cours…' : 'Synthèse du bilan clinique…'}
        </h3>
        <p className="text-xs text-slate-400 font-bold">
        {branch === 'urgence' ? 'Synthèse des observations et signaux de vigilance' : 'Synthèse clinique structurée'}
      </p>
      </div>
    );
  }

  // ── Questions ──
  const question = steps[currentStep];
  const isUrgence = branch === 'urgence';

  return (
    <div className="flex flex-col h-full">
      {/* Progress */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <motion.div
            className={cn('h-full rounded-full', isUrgence ? 'bg-rose-500' : 'bg-emerald-500')}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
        <span className={cn('text-xs font-black', isUrgence ? 'text-rose-500' : 'text-emerald-500')}>
          {currentStep + 1} / {totalSteps}
        </span>
      </div>

      {/* Badge branche */}
      <div className="mb-5">
        <span className={cn(
          'inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full',
          isUrgence
            ? 'bg-rose-500/10 text-rose-600 border border-rose-300'
            : 'bg-emerald-500/10 text-emerald-600 border border-emerald-300'
        )}>
          {isUrgence ? <AlertTriangle size={10} /> : <CheckCircle2 size={10} />}
          {isUrgence ? 'Protocole Urgence' : 'Examen de Routine'}
        </span>
      </div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${branch}-${currentStep}`}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
          className="flex-1"
        >
          <h2 className="text-xl font-black text-text-main mb-1">{question.title}</h2>
          <p className="text-sm text-text-muted font-bold mb-7">{question.subtitle}</p>

          <div className="flex flex-col gap-3">
            {question.options.map((opt) => {
              const isSelected = answers[question.id] === opt.value;
              return (
                <button
                  key={opt.id}
                  onClick={() => handleSelect(question.id, opt.value)}
                  className={cn(
                    'p-4 rounded-2xl border text-left flex items-center justify-between transition-all group',
                    isSelected
                      ? isUrgence
                        ? 'bg-rose-500/10 border-rose-500 text-rose-700'
                        : 'bg-emerald-500/10 border-emerald-500 text-emerald-700'
                      : 'bg-card-bg border-border-main hover:shadow-sm text-text-main',
                    isUrgence ? 'hover:border-rose-400' : 'hover:border-emerald-400'
                  )}
                >
                  <span className="font-bold text-sm">{opt.label}</span>
                  <div className={cn(
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ml-3 transition-colors',
                    isSelected
                      ? isUrgence ? 'border-rose-500 bg-rose-500' : 'border-emerald-500 bg-emerald-500'
                      : 'border-slate-300'
                  )}>
                    {isSelected && <CheckCircle2 size={11} className="text-white" />}
                  </div>
                </button>
              );
            })}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8 pt-4 border-t border-border-main">
        <button onClick={onCancel} className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest">
          Annuler
        </button>
        <div className="flex items-center gap-4">
          {currentStep > 0 && (
            <button
              onClick={() => setCurrentStep(prev => prev - 1)}
              className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest"
            >
              ← Retour
            </button>
          )}
          {currentStep === 0 && (
            <button
              onClick={() => { setBranch('none'); setAnswers({}); }}
              className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest"
            >
              ← Triage
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
