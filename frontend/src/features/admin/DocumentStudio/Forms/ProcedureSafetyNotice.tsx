import React from 'react';
import { AlertCircle } from 'lucide-react';
import { api } from '../../../../services/api';

export type ProcedureSafetyAlertKey =
  | 'CONTEXT_REQUIRED'
  | 'CLINICAL_REVIEW_RECOMMENDED'
  | 'PRESCRIBER_REVIEW_RECOMMENDED'
  | 'SPECIALIST_REVIEW_RECOMMENDED';

export type ProcedureSafetyEvaluationInput = {
  patientId: string | number;
  procedureDate: string;
  procedureBleedingRisk:
    | 'UNKNOWN'
    | 'UNLIKELY_TO_CAUSE_BLEEDING'
    | 'LOW_POSTOP_BLEEDING_RISK'
    | 'HIGHER_POSTOP_BLEEDING_RISK';
  procedureOsseousRisk:
    | 'UNKNOWN'
    | 'NO_OSSEOUS_INJURY'
    | 'DENTOALVEOLAR_OSSEOUS_INJURY';
  procedureIsImplant?: boolean | null;
  ieProcedureQualifies?: boolean | null;
  oralRoutePossible?: boolean | null;
  currentlyTakingPenicillinOrAmoxicillin?: boolean | null;
  presentationId?: string | null;
};

type EvaluationResponse = {
  status?: string;
  alert_key?: ProcedureSafetyAlertKey | null;
  read_only?: boolean;
};

const MESSAGE_BY_KEY: Record<ProcedureSafetyAlertKey, string> = {
  CONTEXT_REQUIRED: 'Contexte patient à compléter.',
  CLINICAL_REVIEW_RECOMMENDED: 'Vérification clinique conseillée avant validation.',
  PRESCRIBER_REVIEW_RECOMMENDED: 'Avis prescripteur recommandé.',
  SPECIALIST_REVIEW_RECOMMENDED: 'Avis spécialisé recommandé.',
};

const EVENT_NAME = 'digitalcrown:procedure-safety-evaluate';

export function dispatchProcedureSafetyEvaluation(input: ProcedureSafetyEvaluationInput) {
  window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: input }));
}

export function ProcedureSafetyNotice({ patientId }: { patientId: string }) {
  const [alertKey, setAlertKey] = React.useState<ProcedureSafetyAlertKey | null>(null);

  React.useEffect(() => {
    setAlertKey(null);
  }, [patientId]);

  React.useEffect(() => {
    let requestRevision = 0;

    const handleEvaluate = (event: Event) => {
      const detail = (event as CustomEvent<ProcedureSafetyEvaluationInput>).detail;
      if (!detail || String(detail.patientId) !== String(patientId)) return;
      if (!detail.procedureDate) return;

      const revision = ++requestRevision;
      void api.post('/prescriptions/clinical-rules/procedure-safety/evaluate', {
        patient_id: Number(detail.patientId),
        procedure_date: detail.procedureDate,
        procedure_bleeding_risk: detail.procedureBleedingRisk,
        procedure_osseous_risk: detail.procedureOsseousRisk,
        procedure_is_implant: detail.procedureIsImplant ?? null,
        ie_procedure_qualifies: detail.ieProcedureQualifies ?? null,
        oral_route_possible: detail.oralRoutePossible ?? null,
        currently_taking_penicillin_or_amoxicillin: detail.currentlyTakingPenicillinOrAmoxicillin ?? null,
        presentation_id: detail.presentationId ?? null,
      }).then(response => {
        if (revision !== requestRevision) return;
        const data = response.data as EvaluationResponse;
        if (data?.read_only !== true) {
          setAlertKey(null);
          return;
        }
        const key = data?.alert_key ?? null;
        setAlertKey(key && key in MESSAGE_BY_KEY ? key : null);
      }).catch(() => {
        if (revision === requestRevision) setAlertKey(null);
      });
    };

    window.addEventListener(EVENT_NAME, handleEvaluate);
    return () => {
      requestRevision += 1;
      window.removeEventListener(EVENT_NAME, handleEvaluate);
    };
  }, [patientId]);

  if (!alertKey) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      data-procedure-safety-notice="subtle"
      data-alert-key={alertKey}
      className="flex min-h-8 items-center gap-1.5 rounded-lg border border-amber-500/15 bg-amber-500/[0.035] px-2.5 py-1.5 text-[10px] font-semibold text-text-muted"
    >
      <AlertCircle size={12} className="shrink-0 opacity-65" aria-hidden="true" />
      <span>{MESSAGE_BY_KEY[alertKey]}</span>
    </div>
  );
}
