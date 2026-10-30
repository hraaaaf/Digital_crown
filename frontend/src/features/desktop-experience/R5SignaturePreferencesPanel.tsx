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
export function R5SignaturePreferencesPanel({user,mode,onChange}:{
  user:AppUser|null;mode:R5Signature;onChange:(value:R5Signature)=>void;
}) {
  const principal=user?String(user.id)+':'+tenantId(user)+':'+user.role:'anonymous';
  const [scope,setScope]=useState<R5VerifiedScope|null>(null);
  const [saved,setSaved]=useState<R5PersistedState|null>(null);
  const [draft,setDraft]=useState<R5Signature>('core');
  const [pending,setPending]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [ready,setReady]=useState(false);

  useEffect(()=>{
    let active=true;
    setScope(null);setSaved(null);setDraft('core');setReady(false);setError(null);
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
      setSaved(response);onChange(draft);
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
    className="mb-2 rounded-xl border border-border-main bg-card px-3 py-2 text-text-main">
    <div className="flex flex-wrap items-center gap-2">
      <SignatureIconicCabinetControls mode={draft} onChange={setDraft}/>
      <button type="button" disabled={pending||draft===mode} onClick={()=>onChange(draft)}
        className="rounded-lg border border-border-main px-3 py-1.5 text-xs font-semibold">Aperçu</button>
      <button type="button" disabled={pending||draft===saved.record?.signature} onClick={()=>void apply()}
        className="rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-on-primary">Appliquer et enregistrer</button>
      <button type="button" disabled={pending} onClick={()=>{const original=saved.record?.signature||'core';setDraft(original);onChange(original);}}
        className="rounded-lg border border-border-main px-3 py-1.5 text-xs">Annuler</button>
      <button type="button" disabled={pending||!saved.canRollback} onClick={()=>void rollback()}
        className="rounded-lg border border-border-main px-3 py-1.5 text-xs">Rollback</button>
      <span className="text-xs text-text-muted">Utilisateur et poste vérifiés · révision {saved.revision}</span>
    </div>
    {error&&<p role="alert" className="mt-1 text-xs text-danger">{error}</p>}
  </section>;
}
