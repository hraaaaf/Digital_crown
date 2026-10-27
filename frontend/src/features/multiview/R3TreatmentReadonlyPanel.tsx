import { useEffect, useState } from 'react';
import { ClipboardList, LockKeyhole } from 'lucide-react';
import { api } from '../../services/api';

/** R3 DEV-only clinical panel: GET the server-authorized, canonical Master Plan.
 * Never mount TreatmentPlanStudio: it is an editor with separate clinical gates.
 * No mutation, cache, local storage, derived diagnosis or fabricated plan.
 */
type TreatmentStep = Readonly<{
  id: number; title: string; assistant: string; status: string; date_str: string | null;
}>;
type Plan = Readonly<{ id: number; patient_id: number; steps: readonly TreatmentStep[] }>;
type State = { patientId: number; status: 'loading' | 'ready' | 'empty' | 'denied'; plan: Plan | null };

export function validateR3MasterPlan(value: unknown, patientId: number): Plan | null | undefined {
  if (value === null) return null; // Genuinely absent, not a synthetic empty plan.
  if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
  const raw = value as Record<string, unknown>;
  if (!Number.isSafeInteger(raw.id) || Number(raw.id) <= 0 ||
      raw.patient_id !== patientId || !Array.isArray(raw.steps)) return undefined;
  const steps: TreatmentStep[] = [];
  for (const candidate of raw.steps) {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return undefined;
    const step = candidate as Record<string, unknown>;
    if (!Number.isSafeInteger(step.id) || Number(step.id) <= 0 ||
        typeof step.title !== 'string' || !step.title.trim() ||
        typeof step.assistant !== 'string' ||
        typeof step.status !== 'string' ||
        !['pending','done','postponed'].includes(step.status) ||
        !(typeof step.date_str === 'string' || step.date_str === null)) return undefined;
    steps.push({id:Number(step.id),title:step.title,assistant:step.assistant,
      status:step.status,date_str:step.date_str});
  }
  return {id:Number(raw.id),patient_id:patientId,steps};
}

const statusLabel: Record<string, string> = {
  pending: 'En attente', done: 'Terminé', postponed: 'Reporté',
};
const statusClass: Record<string, string> = {
  pending: 'bg-warning-surface text-warning',
  done: 'bg-success-surface text-success',
  postponed: 'bg-input-field text-text-muted',
};

export function R3TreatmentReadonlyPanel({patientId}:{patientId:number}) {
  const [state,setState] = useState<State>({patientId,status:'loading',plan:null});
  useEffect(()=>{
    let active=true;
    setState({patientId,status:'loading',plan:null});
    if (!Number.isSafeInteger(patientId) || patientId <= 0) {
      setState({patientId,status:'denied',plan:null});
      return ()=>{active=false;};
    }
    api.get('/patients/' + patientId + '/master-plan')
      .then(response=>{
        if (!active) return;
        const plan=validateR3MasterPlan(response.data,patientId);
        if (plan === undefined) setState({patientId,status:'denied',plan:null});
        else setState({patientId,status:plan===null?'empty':'ready',plan});
      })
      .catch(()=>{if(active)setState({patientId,status:'denied',plan:null});});
    return ()=>{active=false;}; // No late A response after patient / workstation / account switch.
  },[patientId]);
  const current=state.patientId===patientId ? state : {patientId,status:'loading' as const,plan:null};
  return <section data-testid="r3-real-treatment" data-r3-plan-state={current.status}
    className="dc-r3-treatment min-w-0 space-y-3 p-3 text-text-main"
    aria-label="Plan de traitement enregistré, lecture seule">
    <header className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="flex min-w-0 items-center gap-2 text-sm font-bold">
        <ClipboardList size={17} aria-hidden="true"/> Plan de traitement
      </h3>
      <span className="inline-flex items-center gap-1 rounded-full border border-border-main bg-medical-pearl px-2 py-1 text-xs font-semibold">
        <LockKeyhole size={13} aria-hidden="true"/> Lecture seule
      </span>
    </header>
    {current.status==='loading' && <p role="status" className="text-xs text-text-muted">Chargement du plan enregistré…</p>}
    {current.status==='denied' && <p role="alert" className="text-xs text-danger">Plan indisponible : accès refusé ou réponse non vérifiée.</p>}
    {current.status==='empty' && <p className="text-xs text-text-muted">Aucun plan de traitement enregistré.</p>}
    {current.status==='ready' && current.plan && <>
      <div data-testid="r3-treatment-source-summary" className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold text-text-main">{current.plan.steps.length} étape(s) enregistrée(s)</span>
        <span className="text-text-muted">· source Master Plan vérifiée</span>
        {current.plan.steps.length > 0 && <span className="rounded-full border border-border-main bg-medical-pearl px-2 py-1 font-semibold tabular-nums text-primary-ink">
          {current.plan.steps.filter(step=>step.status==='done').length} terminée(s) · {current.plan.steps.filter(step=>step.status==='pending').length} en attente · {current.plan.steps.filter(step=>step.status==='postponed').length} reportée(s)
        </span>}
      </div>
      {current.plan.steps.length === 0
        ? <p className="text-xs text-text-muted">Ce plan ne contient aucune étape enregistrée.</p>
        : <ol className="dc-r3-treatment-steps grid gap-3">
            {current.plan.steps.map((step,index)=><li key={step.id}
              className="min-w-0 rounded-xl border border-border-main bg-card p-4 shadow-sm">
              <div className="flex min-w-0 items-start justify-between gap-2">
                <p className="min-w-0 break-words text-sm font-bold leading-snug text-text-main">{index+1}. {step.title}</p>
                <span className={'shrink-0 rounded-full px-2 py-1 text-[11px] font-semibold ' + statusClass[step.status]}>
                  {statusLabel[step.status]}
                </span>
              </div>
              {(step.assistant || step.date_str) && <p className="mt-1 break-words text-xs text-text-muted">
                {[step.assistant,step.date_str].filter(Boolean).join(' · ')}
              </p>}
            </li>)}
          </ol>}
    </>}
  </section>;
}
