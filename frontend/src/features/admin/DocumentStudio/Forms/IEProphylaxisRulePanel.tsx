import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, Loader2, ShieldCheck } from 'lucide-react';

import { api } from '../../../../services/api';
import type { DrugItem } from './prescriptionTypes';


type TriState = boolean | null;

type RuleEvaluation = {
  status: 'BLOCKED' | 'READY';
  rule_id: string;
  rule_version: string;
  blockers: string[];
  active_ingredient_code: string | null;
  total_dose_mg: number | null;
  timing_min_minutes_before: number | null;
  timing_max_minutes_before: number | null;
  single_dose: boolean | null;
  source_ids: string[];
};

const fieldClass = 'min-h-[44px] w-full rounded-xl border border-border-main bg-background px-3 py-2 text-sm font-semibold text-text-main outline-none transition focus:border-accent/60 focus:ring-2 focus:ring-accent/10';
const labelClass = 'mb-1.5 block text-[10px] font-black uppercase tracking-[0.13em] text-text-muted';

const blockerLabels: Record<string, string> = {
  AGE_UNKNOWN: 'Date de naissance du patient indisponible.',
  ADULT_RULE_ONLY: 'Cette aide est limitée aux patients adultes.',
  CARDIAC_RISK_UNKNOWN: 'Situation cardiaque à vérifier dans le contexte patient.',
  CARDIAC_RISK_NOT_QUALIFYING: 'La situation cardiaque renseignée n’entre pas dans le périmètre automatisé de cette aide.',
  DENTAL_PROCEDURE_ELIGIBILITY_UNKNOWN: 'Précisez si le geste concerne la gencive, la région périapicale ou perfore la muqueuse.',
  DENTAL_PROCEDURE_NOT_QUALIFYING: 'Le geste renseigné n’entre pas dans le périmètre de cette prophylaxie.',
  GENERIC_MEDICATION_ALLERGY_REQUIRES_RECONCILIATION: 'Une allergie médicamenteuse est rapportée. Réconciliez les allergies dans le contexte patient avant évaluation.',
  PENICILLIN_ALLERGY_UNKNOWN: 'Allergie pénicilline/amoxicilline à vérifier dans le contexte patient.',
  PENICILLIN_ALLERGY_PRESENT: 'Une allergie pénicilline/amoxicilline est rapportée. Cette suggestion ne s’applique pas.',
  ORAL_ROUTE_UNKNOWN: 'Précisez si la voie orale est possible.',
  ORAL_ROUTE_NOT_POSSIBLE: 'La voie orale n’est pas possible. Cette suggestion ne s’applique pas.',
  CURRENT_ANTIBIOTIC_EXPOSURE_UNKNOWN: 'Précisez si le patient prend actuellement de la pénicilline ou de l’amoxicilline.',
  CURRENT_PENICILLIN_OR_AMOXICILLIN: 'Le patient prend déjà de la pénicilline ou de l’amoxicilline. Cette suggestion ne s’applique pas.',
  PRESENTATION_NOT_VERIFIED: 'La présentation médicamenteuse sélectionnée n’a pas pu être vérifiée.',
  ACTIVE_INGREDIENT_NOT_AMOXICILLIN: 'La présentation sélectionnée n’est pas une amoxicilline mono-composant compatible avec cette aide.',
};

function BoolSelect({
  label,
  ariaLabel,
  value,
  onChange,
}: {
  label: string;
  ariaLabel: string;
  value: TriState;
  onChange: (value: TriState) => void;
}) {
  return (
    <label>
      <span className={labelClass}>{label}</span>
      <select
        aria-label={ariaLabel}
        className={fieldClass}
        value={value === null ? '' : value ? 'yes' : 'no'}
        onChange={event => onChange(event.target.value === '' ? null : event.target.value === 'yes')}
      >
        <option value="">À préciser</option>
        <option value="yes">Oui</option>
        <option value="no">Non</option>
      </select>
    </label>
  );
}

export function IEProphylaxisRulePanel({
  patientId,
  drug,
}: {
  patientId?: number;
  drug?: DrugItem;
}) {
  const [expanded, setExpanded] = useState(false);
  const [procedureDate, setProcedureDate] = useState('');
  const [qualifyingProcedure, setQualifyingProcedure] = useState<TriState>(null);
  const [oralRoutePossible, setOralRoutePossible] = useState<TriState>(null);
  const [currentPenicillinOrAmoxicillin, setCurrentPenicillinOrAmoxicillin] = useState<TriState>(null);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState(false);
  const [evaluation, setEvaluation] = useState<RuleEvaluation | null>(null);

  const presentationId = drug?.catalogPresentationId;
  const exactAmoxicillin = ['AMOXICILLINE', 'AMOXICILLIN'].includes((drug?.catalogDci || '').trim().toUpperCase());

  useEffect(() => {
    setExpanded(false);
    setProcedureDate('');
    setQualifyingProcedure(null);
    setOralRoutePossible(null);
    setCurrentPenicillinOrAmoxicillin(null);
    setEvaluation(null);
    setRequestError(false);
  }, [patientId, presentationId]);

  if (!patientId || !presentationId || !exactAmoxicillin) return null;

  const evaluate = async () => {
    if (!procedureDate || loading) return;
    setLoading(true);
    setRequestError(false);
    setEvaluation(null);
    try {
      const response = await api.post('/prescriptions/clinical-rules/ie-prophylaxis/evaluate', {
        patient_id: patientId,
        procedure_date: procedureDate,
        dental_procedure_qualifies: qualifyingProcedure,
        oral_route_possible: oralRoutePossible,
        currently_taking_penicillin_or_amoxicillin: currentPenicillinOrAmoxicillin,
        presentation_id: presentationId,
      });
      setEvaluation(response.data as RuleEvaluation);
    } catch (error) {
      console.error('IE prophylaxis evaluation failed:', error);
      setRequestError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      data-ie-prophylaxis-rule="c2"
      data-rule-expanded={expanded ? 'true' : 'false'}
      data-rule-result={evaluation?.status || 'idle'}
      className="rounded-2xl border border-border-main bg-glass-bg/70 px-3.5 py-3 shadow-sm backdrop-blur-xl sm:px-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">
            <ShieldCheck size={13} /> Prévention endocardite
          </div>
          <p className="mt-1 text-[11px] font-semibold leading-relaxed text-text-muted">
            Vérifiez l’éligibilité à une prophylaxie avant un geste dentaire invasif.
          </p>
        </div>
        <button
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded(value => !value)}
          className="inline-flex min-h-[44px] shrink-0 items-center gap-1.5 rounded-xl border border-border-main bg-background px-3 text-[10px] font-black uppercase tracking-wide text-text-main transition hover:border-accent/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/20"
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {expanded ? 'Réduire' : 'Évaluer'}
        </button>
      </div>

      {!expanded ? (
        <div className="mt-2 rounded-xl border border-border-main/80 bg-background/55 px-3 py-2 text-[10px] font-bold leading-relaxed text-text-muted">
          Présentation sélectionnée : <span className="text-text-main">{drug?.name}</span>
        </div>
      ) : (
        <>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <label>
              <span className={labelClass}>Date prévue du geste</span>
              <input
                aria-label="Date prévue du geste"
                type="date"
                className={fieldClass}
                value={procedureDate}
                onChange={event => { setProcedureDate(event.target.value); setEvaluation(null); setRequestError(false); }}
              />
            </label>

            <BoolSelect
              label="Geste invasif concerné"
              ariaLabel="Geste avec manipulation gingivale périapicale ou perforation muqueuse"
              value={qualifyingProcedure}
              onChange={value => { setQualifyingProcedure(value); setEvaluation(null); setRequestError(false); }}
            />

            <BoolSelect
              label="Voie orale possible"
              ariaLabel="Voie orale possible"
              value={oralRoutePossible}
              onChange={value => { setOralRoutePossible(value); setEvaluation(null); setRequestError(false); }}
            />

            <BoolSelect
              label="Pénicilline / amoxicilline en cours"
              ariaLabel="Prise actuelle de pénicilline ou amoxicilline"
              value={currentPenicillinOrAmoxicillin}
              onChange={value => { setCurrentPenicillinOrAmoxicillin(value); setEvaluation(null); setRequestError(false); }}
            />
          </div>

          <div className="mt-3 flex justify-end">
            <button
              type="button"
              onClick={evaluate}
              disabled={!procedureDate || loading}
              className="inline-flex min-h-[44px] items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 px-4 text-xs font-black text-primary transition hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-45"
            >
              {loading && <Loader2 size={14} className="animate-spin" />}
              Vérifier la prophylaxie
            </button>
          </div>

          {requestError && (
            <div className="mt-3 flex items-start gap-2 rounded-xl border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-xs font-bold text-amber-700 dark:text-amber-300">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" /> Évaluation indisponible. Aucune suggestion n’est appliquée.
            </div>
          )}

          {evaluation?.status === 'BLOCKED' && (
            <div className="mt-3 rounded-xl border border-amber-500/25 bg-amber-500/5 px-3 py-2.5 text-xs text-amber-800 dark:text-amber-200">
              <div className="font-black">Suggestion non applicable avec les informations actuelles</div>
              <ul className="mt-1.5 list-disc space-y-1 pl-4 font-semibold">
                {evaluation.blockers.map(blocker => (
                  <li key={blocker}>{blockerLabels[blocker] || 'Une information clinique requise reste à vérifier.'}</li>
                ))}
              </ul>
            </div>
          )}

          {evaluation?.status === 'READY' && (
            <div className="mt-3 rounded-xl border border-emerald-500/25 bg-emerald-500/5 px-3 py-3 text-emerald-900 dark:text-emerald-100">
              <div className="flex items-center gap-2 text-xs font-black">
                <CheckCircle2 size={15} /> Suggestion disponible
              </div>
              <div className="mt-1.5 text-sm font-black">
                Amoxicilline 2 g, prise unique, 30–60 min avant le geste
              </div>
              <p className="mt-1 text-[11px] font-semibold leading-relaxed opacity-80">
                Références : American Heart Association (2021) et American Dental Association. Vérification et décision finales par le praticien.
              </p>
              <p className="mt-1 text-[10px] font-semibold opacity-70">
                Cette aide ne modifie pas automatiquement l’ordonnance.
              </p>
            </div>
          )}
        </>
      )}
    </section>
  );
}
