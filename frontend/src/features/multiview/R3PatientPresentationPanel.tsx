import { useEffect, useState } from 'react';
import { Eye, EyeOff, LockKeyhole } from 'lucide-react';
import { api } from '../../services/api';
import { validateR3MasterPlan } from './R3TreatmentReadonlyPanel';

interface VerifiedPatient {id:number;prenom:string;nom:string;numero_dossier:string}
type Plan = NonNullable<ReturnType<typeof validateR3MasterPlan>>;
type Stage = 'private' | 'loading' | 'ready' | 'empty' | 'denied';

/** R3 preset: on-this-screen, clinician-triggered R-only preview.
 * NOT a detached 07.1.D second-screen broadcast. No sharing/token transfer.
 * Confidential identity & plan stay absent until explicit "Présenter" action.
 */
export function R3PatientPresentationPanel({patient}:{patient:VerifiedPatient}) {
  const [view,setView]=useState<{id:number;stage:Stage;plan:Plan|null}>({
    id:patient.id,stage:'private',plan:null,
  });
  useEffect(()=>{
    setView({id:patient.id,stage:'private',plan:null});
  },[patient.id]);
  const present=()=>{
    if (!Number.isSafeInteger(patient.id)||patient.id<1||view.stage!=='private') return;
    const id=patient.id;
    setView({id,stage:'loading',plan:null});
    void api.get('/patients/'+id+'/master-plan').then(response=>{
      const plan=validateR3MasterPlan(response.data,id);
      setView(current=>current.id!==id||current.stage!=='loading'?current:
        {id,stage:plan===undefined?'denied':plan===null?'empty':'ready',plan:plan??null});
    }).catch(()=>setView(current=>current.id!==id||current.stage!=='loading'?current:
      {id,stage:'denied',plan:null}));
  };
  const hide=()=>setView({id:patient.id,stage:'private',plan:null});
  const stage=view.id===patient.id?view.stage:'private';
  const plan=view.id===patient.id?view.plan:null;
  return <section data-testid="r3-patient-presentation" aria-label="Présentation locale au patient"
    className="min-w-0 space-y-4 p-5 text-text-main">
    <header className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="text-lg font-bold">Présentation au patient</h3>
      <span className="flex items-center gap-1.5 rounded-full border border-border-main px-3 py-1 text-xs">
        <LockKeyhole size={14}/> Aperçu local · lecture seule
      </span>
    </header>
    {stage==='private'
      ? <div className="rounded-xl border border-dashed border-border-main bg-medical-pearl p-5">
          <p className="text-sm font-semibold">Présentation masquée</p>
          <p className="mt-2 text-xs text-text-muted">Vérifiez que seul le bon patient regarde cet écran. Ce mode ne partage rien sur un autre écran.</p>
          <button type="button" onClick={present} className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-on-primary">
            <Eye size={17}/> Présenter sur cet écran
          </button>
        </div>
      : <button type="button" onClick={hide}
          className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-border-main bg-card px-4 text-sm font-semibold">
          <EyeOff size={17}/> Masquer immédiatement
        </button>}
    {stage==='loading' && <p role="status">Vérification des données autorisées…</p>}
    {stage==='denied' && <p role="alert" className="text-danger">Présentation refusée : source ou autorisation non vérifiée.</p>}
    {(stage==='ready'||stage==='empty') && <div data-testid="r3-presentation-visible"
      className="space-y-4 rounded-xl border border-border-main bg-card p-6">
      <p className="text-2xl font-bold break-words">{patient.prenom} {patient.nom}</p>
      <p className="text-xs text-text-muted">Plan de traitement enregistré · aucune proposition automatique</p>
      {stage==='empty'&&<p>Aucun plan de traitement enregistré.</p>}
      {stage==='ready'&&plan&&<ol className="space-y-3">
        {plan.steps.map((step,index)=><li key={step.id} className="rounded-lg border border-border-main p-3">
          <p className="font-semibold">{index+1}. {step.title}</p>
          <p className="text-xs text-text-muted">{step.status==='done'?'Terminé':step.status==='pending'?'À venir':'Reporté'}</p>
        </li>)}
      </ol>}
    </div>}
  </section>;
}
