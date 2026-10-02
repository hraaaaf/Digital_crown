import React from 'react';
import { AlertCircle } from 'lucide-react';
import { api } from '../../../../services/api';

export type ProcedureSafetyAlertKey =
  | 'CONTEXT_REQUIRED'
  | 'CLINICAL_REVIEW_RECOMMENDED'
  | 'PRESCRIBER_REVIEW_RECOMMENDED'
  | 'SPECIALIST_REVIEW_RECOMMENDED'
  | 'SAFETY_CHECK_UNAVAILABLE';

type EvaluationResponse = {
  status?: string;
  alert_key?: ProcedureSafetyAlertKey | null;
  read_only?: boolean;
};

const MESSAGE_BY_KEY: Record<ProcedureSafetyAlertKey, string> = {
  CONTEXT_REQUIRED: 'Contexte clinique à compléter.',
  CLINICAL_REVIEW_RECOMMENDED: 'Vérification clinique conseillée avant validation.',
  PRESCRIBER_REVIEW_RECOMMENDED: 'Avis prescripteur recommandé.',
  SPECIALIST_REVIEW_RECOMMENDED: 'Avis spécialisé recommandé.',
  SAFETY_CHECK_UNAVAILABLE: 'Vérification clinique momentanément indisponible.',
};

export function ProcedureSafetyNotice({
  patientId,
  presentationId,
}: {
  patientId: string;
  presentationId?: string | null;
}) {
  const [alertKey, setAlertKey] = React.useState<ProcedureSafetyAlertKey | null>(null);
  const [revision, setRevision] = React.useState(0);

  React.useEffect(() => {
    setAlertKey(null);
  }, [patientId]);

  React.useEffect(() => {
    const refresh = (event: Event) => {
      const detail = (event as CustomEvent<{ patientId?: number | string }>).detail;
      if (String(detail?.patientId ?? '') === String(patientId)) {
        setRevision(value => value + 1);
      }
    };
    window.addEventListener('digitalcrown:patient-clinical-context-updated', refresh);
    window.addEventListener('digitalcrown:procedure-safety-context-updated', refresh);
    return () => {
      window.removeEventListener('digitalcrown:patient-clinical-context-updated', refresh);
      window.removeEventListener('digitalcrown:procedure-safety-context-updated', refresh);
    };
  }, [patientId]);

  React.useEffect(() => {
    if (!patientId || patientId === '0') {
      setAlertKey(null);
      return;
    }

    let cancelled = false;
    setAlertKey(null);

    void api.get('/prescriptions/clinical-rules/procedure-safety/alert/' + patientId, {
      params: presentationId ? { presentation_id: presentationId } : {},
    }).then(response => {
      if (cancelled) return;
      const data = response.data as EvaluationResponse;
      if (data?.read_only !== true) {
        setAlertKey('SAFETY_CHECK_UNAVAILABLE');
        return;
      }
      const key = data?.alert_key ?? null;
      setAlertKey(key && key in MESSAGE_BY_KEY ? key : null);
    }).catch(() => {
      if (!cancelled) setAlertKey('SAFETY_CHECK_UNAVAILABLE');
    });

    return () => {
      cancelled = true;
    };
  }, [patientId, presentationId, revision]);

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
