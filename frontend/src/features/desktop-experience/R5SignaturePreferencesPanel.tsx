import {useEffect,useState} from 'react';
import type { AppUser } from '../../types';
import {useAuthStore} from '../../stores/useAuthStore';
import {workstationModeService} from '../../services/workstationMode';
import {createR5Preference,type R5Signature,type R5VerifiedScope} from '../multiview/R5PreferencesPolicy';
import {r5PreferencesService,type R5PersistedState} from '../multiview/R5PreferencesService';
import {SignatureIconicCabinetControls} from './SignatureIconicCabinetControls';

function tenantId(user: AppUser): string | null {
  if(typeof user.employer_id==='number' && user.employer_id>0) return String(user.employer_id);
  if(user.employer_id===null && (user.role==='DENTISTE'||user.role==='ADMIN')) return String(user.id);
  return null;
}

/** DEV-only signature experience: persists no clinical data. Permission checks
 * and workstation enrollment are server-owned and repeated for each mutation.
 */
export function R5SignaturePreferencesPanel({user,mode,onChange,compactOnPatientRoute=false}:{
  user:AppUser|null;mode:R5Signature;onChange:(value:R5Signature)=>void;
  compactOnPatientRoute?:boolean;
}) {
  const principal=user?String(user.id)+':'+tenantId(user)+':'+user.role:'anonymous';
  const [scope,setScope]=useState<R5VerifiedScope|null>(null);
  const [saved,setSaved]=useState<R5PersistedState|null>(null);
  const [draft,setDraft]=useState<R5Signature>('core');
  const [pending,setPending]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [ready,setReady]=useState(false);
  const [detailsOpen,setDetailsOpen]=useState(false);
  const showDetails=!compactOnPatientRoute||detailsOpen;

  useEffect(()=>{
    let active=true;
    setScope(null);setSaved(null);setDraft('core');setReady(false);setError(null);setDetailsOpen(false);
    onChange('core');
    const load=async()=>{
      if(!user||!tenantId(user)||!useAuthStore.getState().isAuthenticated) return;
      try {
        const station=await workstationModeService.getBootstrapState();
        if(!active||!station.authenticated||station.enrollmentRequired!==false||
          station.stationLocked||station.defaultExperience==='control_center'||
          typeof station.workstationId!=='string'||!station.workstationId.trim()) return;
        const verified:R5VerifiedScope={authenticated:true,workstationVerified:true,
          userId:String(user.id),tenantId:tenantId(user),workstationId:station.workstationId,
          patientId:null,cssViewportWidth:window.innerWidth,allowedModules:[]};
        const data=await r5PreferencesService.load();
        if(!active||!useAuthStore.getState().isAuthenticated||
          String(useAuthStore.getState().user?.id)!==String(user.id)) return;
        // The server has already validated the saved JSON and workstation cookie.
        if(data.record && (data.record.userId!==verified.userId||
            data.record.tenantId!==verified.tenantId||
            data.record.workstationId!==verified.workstationId||
            !['core','iconic'].includes(data.record.signature))) return;
        const next=data.record?.signature||'core';
        setScope(verified);setSaved(data);setDraft(next);onChange(next);setReady(true);
      }catch{
        if(active)setError('Préférences indisponibles : aucun changement enregistré.');
      }
    };
    void load();
    const unsubscribe=workstationModeService.subscribe(()=>{setReady(false);setScope(null);setSaved(null);onChange('core');});
    return ()=>{active=false;unsubscribe();};
  },[principal]); // Reinitialize on user/tenant change, not on each rerender.

  useEffect(()=>{setDetailsOpen(false);},[compactOnPatientRoute]);

  async function verifyScope():Promise<boolean> {
    if(!scope||!user||!useAuthStore.getState().isAuthenticated||
      String(useAuthStore.getState().user?.id)!==scope.userId) return false;
    const state=await workstationModeService.getBootstrapState();
    return state.authenticated===true && state.enrollmentRequired===false &&
      state.stationLocked===false && state.defaultExperience!=='control_center' &&
      state.workstationId===scope.workstationId;
  }
  async function apply(){
    if(!scope||!saved||!ready||pending) return;
    setPending(true);setError(null);
    try{
      if(!await verifyScope()) throw new Error('session');
      // Preserve already saved layout metadata; MainLayout does not override a
      // MultiView layout for a patient it cannot independently authorize.
      const record=saved.record?
        {...saved.record,signature:draft}:
        createR5Preference(scope,draft,null);
      if(!record) throw new Error('invalid');
      const response=await r5PreferencesService.save(record,saved.revision);
      setSaved(response);onChange(draft);setDetailsOpen(false);
    }catch{
      setDraft(saved.record?.signature||'core');
      onChange(saved.record?.signature||'core');
      setError('Enregistrement refusé ou modifié dans un autre onglet. Rechargez la page.');
    }finally{setPending(false);}
  }
  async function rollback(){
    if(!saved?.canRollback||!scope||pending) return;
    setPending(true);setError(null);
    try{
      if(!await verifyScope()) throw new Error('session');
      const result=await r5PreferencesService.rollback(saved.revision);
      if(result.record?.userId!==scope.userId||result.record.workstationId!==scope.workstationId)throw new Error('scope');
      setSaved(result);setDraft(result.record.signature);onChange(result.record.signature);
    }catch{setError('Rollback refusé : contexte ou révision à revérifier.');}
    finally{setPending(false);}
  }
  if(!ready||!scope||!saved)return <p data-testid="r5-signature-locked" className="text-xs text-text-muted" role="status">
    R5 · Préférences verrouillées tant que le compte et le poste ne sont pas vérifiés.
  </p>;
  return <section data-testid="r5-signature-prefs" aria-label="R5 préférences Signature"
    className={`mb-2 rounded-xl border border-border-main bg-card px-3 py-2 text-text-main lg:mb-1 lg:py-1.5 ${compactOnPatientRoute ? 'lg:border-transparent lg:bg-medical-pearl/40' : ''}`}>
    {compactOnPatientRoute && <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex min-w-0 items-center gap-2 text-xs">
        <strong className="text-text-main">Signature du cabinet</strong>
        <span className="text-text-muted">{saved.record?.signature==='iconic'?'Iconic':'Core'} · poste vérifié · révision {saved.revision}</span>
      </div>
      <button type="button" data-testid="r5-signature-toggle"
        aria-expanded={showDetails} aria-controls="r5-signature-settings"
        onClick={()=>setDetailsOpen(value=>!value)}
        className="min-h-9 rounded-lg border border-border-main px-3 py-1.5 text-xs font-semibold text-text-main focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-text-main">
        {showDetails?'Replier':'Personnaliser'}
      </button>
    </div>}
    {showDetails && <div id="r5-signature-settings" className="flex flex-col gap-3 pt-1">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-bold text-text-main">Signature du cabinet</h2>
          <p className="text-xs text-text-muted">Prévisualiser sans enregistrer, puis confirmer pour conserver.</p>
        </div>
        <span className="rounded-full border border-border-main bg-medical-pearl px-3 py-1 text-xs text-text-muted">
          Compte et poste vérifiés · révision {saved.revision}
        </span>
      </div>
      <SignatureIconicCabinetControls mode={draft} onChange={setDraft} persisted/>
      <div className="flex flex-wrap items-center gap-2 border-t border-border-main pt-3">
      <button type="button" disabled={pending||draft===mode} onClick={()=>onChange(draft)}
        className="min-h-10 rounded-lg border border-border-main px-3 py-2 text-xs font-semibold disabled:opacity-50">Aperçu</button>
      <button type="button" disabled={pending||draft===saved.record?.signature} onClick={()=>void apply()}
        className="min-h-10 rounded-lg bg-primary px-4 py-2 text-xs font-bold text-on-primary shadow-sm disabled:opacity-50">Appliquer et enregistrer</button>
      <button type="button" disabled={pending} onClick={()=>{const original=saved.record?.signature||'core';setDraft(original);onChange(original);}}
        className="min-h-10 rounded-lg border border-border-main px-3 py-2 text-xs disabled:opacity-50">Annuler</button>
      <button type="button" disabled={pending||!saved.canRollback} onClick={()=>void rollback()}
        className="min-h-10 rounded-lg px-3 py-2 text-xs text-text-muted hover:underline disabled:opacity-50">Rollback</button>
      </div>
      <p role="status" className="text-xs text-text-muted">
        {draft!==saved.record?.signature
          ? 'Sélection non enregistrée : utilisez « Appliquer et enregistrer » pour la conserver.'
          : 'Préférence actuelle enregistrée pour ce compte et ce poste.'}
      </p>
    </div>}
    {error&&<p role="alert" className="mt-1 text-xs text-danger">{error}</p>}
  </section>;
}
