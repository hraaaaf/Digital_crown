import { useEffect, useState } from 'react';
import { ShieldCheck, Waypoints } from 'lucide-react';
import {
  fetchOrthoCase, fetchOrthoTimepoints, fetchOrthoLongitudinalCompare,
  type OrthoCompareTimepoint, type OrthoMeasurementDelta,
} from '../ortho/orthoLongitudinalCompare';

/** Distinct T0/T1 read-only evidence instance. NEVER mounts a second
 * CephaloWorkspace/editor, guesses a timepoint, or manufactures measurements.
 * Server rechecks patient+tenant for each source GET. No writes/persistence.
 */
type Evidence = Readonly<{
  timepoint:OrthoCompareTimepoint; analysisId:number; measures:readonly OrthoMeasurementDelta[];
}>;
type Loaded = {patientId:number;state:'loading'|'unavailable'|'denied'|'ready';evidence:Evidence|null};

export function R3CephaloTimepointReadonlyPanel({patientId,ordinal}:{
  patientId:number;ordinal:0|1;
}) {
  const [loaded,setLoaded] = useState<Loaded>({patientId,state:'loading',evidence:null});
  useEffect(()=>{
    let active=true;
    setLoaded({patientId,state:'loading',evidence:null});
    if (!Number.isSafeInteger(patientId)||patientId<1) {
      setLoaded({patientId,state:'denied',evidence:null});
      return ()=>{active=false;};
    }
    void (async()=>{
      try {
        const orthoCase=await fetchOrthoCase(patientId);
        if (!active) return;
        if (!orthoCase) {setLoaded({patientId,state:'unavailable',evidence:null});return;}
        if (orthoCase.patient_id!==patientId || !Number.isSafeInteger(orthoCase.id)) throw Error('case mismatch');
        const timepoints=await fetchOrthoTimepoints(patientId,orthoCase.id);
        if (!active) return;
        const t0=timepoints.filter(t=>t.ordinal===0&&t.patient_id===patientId&&t.ortho_case_id===orthoCase.id);
        const t1=timepoints.filter(t=>t.ordinal===1&&t.patient_id===patientId&&t.ortho_case_id===orthoCase.id);
        if (t0.length!==1||t1.length!==1||t0[0].id===t1[0].id) {
          setLoaded({patientId,state:'unavailable',evidence:null});return;
        }
        const cmp=await fetchOrthoLongitudinalCompare(patientId,orthoCase.id,0,1);
        if (!active) return;
        if (cmp.patient_id!==patientId||cmp.ortho_case_id!==orthoCase.id||
            cmp.from_timepoint.id!==t0[0].id||cmp.to_timepoint.id!==t1[0].id||
            cmp.from_timepoint.ordinal!==0||cmp.to_timepoint.ordinal!==1||
            cmp.interpretation_policy!=='NUMERIC_ONLY_CLINICIAN_INTERPRETATION') throw Error('comparison mismatch');
        const tp=ordinal===0?cmp.from_timepoint:cmp.to_timepoint;
        const analyses=tp.evidences.filter(e=>e.kind==='CEPHALO'&&Number.isSafeInteger(e.ref_id)&&e.ref_id>0);
        // No cephalometry = no claim of a clinical Cephalo panel.
        const peer=(ordinal===0?cmp.to_timepoint:cmp.from_timepoint).evidences.filter(e=>e.kind==='CEPHALO');
        if (analyses.length!==1||peer.length!==1||peer[0].ref_id===analyses[0].ref_id) {
          setLoaded({patientId,state:'unavailable',evidence:null});return;
        }
        setLoaded({patientId,state:'ready',evidence:{
          timepoint:tp,analysisId:analyses[0].ref_id,measures:cmp.measurements,
        }});
      } catch {
        if(active)setLoaded({patientId,state:'denied',evidence:null});
      }
    })();
    return ()=>{active=false;};
  },[patientId,ordinal]);
  const current=loaded.patientId===patientId?loaded:{patientId,state:'loading',evidence:null};
  return <section data-testid={'r3-cephalo-t'+ordinal} data-r3-cephalo-state={current.state}
    aria-label={'Analyse céphalométrique T'+ordinal+' · lecture seule'}
    className="min-w-0 space-y-3 p-3 text-text-main">
    <header className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="flex items-center gap-2 text-sm font-semibold"><Waypoints size={18}/> Céphalo T{ordinal}</h3>
      <span className="rounded-full border border-border-main px-2 py-1 text-xs">R · lecture seule</span>
    </header>
    {current.state==='loading' && <p role="status" className="text-xs text-text-muted">Lecture des repères T0/T1…</p>}
    {current.state==='denied' && <p role="alert" className="text-xs text-danger">Données indisponibles : accès ou source non vérifiés.</p>}
    {current.state==='unavailable' && <p data-testid={'r3-cephalo-missing-t'+ordinal}
      className="text-xs text-text-muted">Aucune paire T0/T1 avec une céphalométrie canonique unique par repère. Aucune analyse inventée.</p>}
    {current.state==='ready' && current.evidence && <>
      <div className="rounded-xl border border-border-main bg-medical-pearl p-3.5">
        <p className="flex items-center gap-2 text-xs font-medium text-text-main">
          <ShieldCheck size={15}/> Analyse source #{current.evidence.analysisId}
        </p>
        <p className="mt-1 text-xs text-text-muted">T{ordinal} · {current.evidence.timepoint.occurred_at.slice(0,10)}</p>
      </div>
      <div className="grid gap-2" aria-label={'Mesures céphalométriques vérifiées T'+ordinal}>
        {current.evidence.measures.length===0
          ? <p className="text-xs text-text-muted">Aucune mesure commune certifiée entre T0 et T1.</p>
          : current.evidence.measures.map(m=><div key={m.key}
              data-testid={'r3-cephalo-measure-t'+ordinal}
              className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-xl border border-border-main bg-card px-4 py-3">
              <span className="text-xs font-bold uppercase tracking-wide text-text-muted">{m.label}</span>
              <span className="tabular-nums text-2xl font-extrabold tracking-tight text-primary-ink">{(ordinal===0?m.from_value:m.to_value).toLocaleString('fr-FR',{maximumFractionDigits:2})} <small className="text-xs font-semibold">{m.unit}</small></span>
            </div>)}
      </div>
      <p className="text-[11px] text-text-muted">Comparaison numérique factuelle · interprétation réservée au praticien.</p>
    </>}
  </section>;
}
