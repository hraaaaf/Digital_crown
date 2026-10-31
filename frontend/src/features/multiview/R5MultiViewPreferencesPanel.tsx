import {useEffect,useState} from 'react';
import {authorizeLayout,type Layout} from './studioLayouts';
import type {R5VerifiedScope} from './R5PreferencesPolicy';
// R5 API and strict preference policy remain completely separate from clinical views.
import {createR5Preference as projectR5,readR5Preference as readR5,
  type R5PreferenceRecord} from './R5PreferencesPolicy';
import {r5PreferencesService,type R5PersistedState} from './R5PreferencesService';
import {geometryGridStyle,geometrySlotStyle} from './studioGeometry';

export function R5MultiViewPreferencesPanel({context,layouts,onApply,ratio}:{
  context:R5VerifiedScope;layouts:readonly Layout[];
  ratio:number;onApply:(layout:Layout,ratio:number)=>void;
}) {
  const [state,setState]=useState<R5PersistedState|null>(null);
  const [choice,setChoice]=useState(layouts[0]?.id||'');
  const [preview,setPreview]=useState(false);
  const [expanded,setExpanded]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const scopeKey=[context.tenantId,context.userId,context.workstationId,
    context.authenticated,context.workstationVerified,context.patientId,
    context.allowedModules.join(','),context.cssViewportWidth].join(':');

  function matching(record:R5PreferenceRecord|null):Layout|null{
    if(!record?.layout)return null;
    for(const layout of layouts){
      const projected=projectR5(context,record.signature,layout,record.layout.ratio);
      if(projected?.layout?.id===record.layout.id&&
        JSON.stringify(projected.layout.slots)===JSON.stringify(record.layout.slots))return layout;
    }
    return null;
  }
  useEffect(()=>{
    let active=true;
    setState(null);setPreview(false);setExpanded(false);setError(null);
    const load=async()=>{
      try{
        const persisted=await r5PreferencesService.load();
        if(!active)return;
        if(persisted.record&&!readR5(persisted.record,context))return;
        setState(persisted);
        const selected=matching(persisted.record);
        if(selected){setChoice(selected.id);onApply(selected,persisted.record!.layout!.ratio);}
      }catch{if(active)setError('Préférences indisponibles.');}
    };
    void load();
    return ()=>{active=false;};
  },[scopeKey]);

  const selected=layouts.find(l=>l.id===choice);
  const allowed=selected?authorizeLayout(selected,context,ratio).ok:false;
  async function validate():Promise<boolean>{
    // Force the parent to drop saved views as soon as its trusted scope fails.
    return context.authenticated===true&&context.workstationVerified===true&&
      Boolean(context.tenantId&&context.userId&&context.workstationId)&&
      Boolean(selected&&authorizeLayout(selected,context,ratio).ok);
  }
  async function save(){
    if(!state||!selected||busy||!await validate())return;
    setBusy(true);setError(null);
    try{
      const pref=projectR5(context,state.record?.signature||'core',selected,ratio);
      if(!pref)throw new Error('invalid');
      const result=await r5PreferencesService.save(pref,state.revision);
      const validated=readR5(result.record,context);
      if(!validated)throw new Error('scope');
      setState(result);onApply(selected,ratio);setPreview(false);setExpanded(false);
    }catch{setPreview(false);setError('Enregistrement refusé : utilisateur, poste ou révision à vérifier.');}
    finally{setBusy(false);}
  }
  async function rollback(){
    if(!state?.canRollback||busy)return;
    setBusy(true);setError(null);
    try{
      const result=await r5PreferencesService.rollback(state.revision);
      if(result.record&&!readR5(result.record,context))throw new Error('scope');
      setState(result);const previous=matching(result.record);
      if(previous){setChoice(previous.id);onApply(previous,result.record!.layout!.ratio);}
      setPreview(false);setExpanded(false);
    }catch{setError('Rollback refusé.');}finally{setBusy(false);}
  }
  if(!context.authenticated||!context.workstationVerified||!context.workstationId||
      !context.userId||!context.tenantId||!state)return null;
  return <section data-testid="r5-multiview-prefs" aria-label="R5 dispositions persistantes"
    className="mb-2 rounded-xl border border-border-main bg-card px-3 py-3 text-text-main lg:mb-1 lg:py-1.5 lg:border-transparent lg:bg-medical-pearl/40">
    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
        <strong className="text-sm">Disposition du cabinet · R5</strong>
        <span className="text-text-muted">{matching(state.record)?.label||'Disposition standard'} · poste vérifié · révision {state.revision}</span>
      </div>
      <button type="button" data-testid="r5-multiview-toggle"
        aria-expanded={expanded} aria-controls="r5-multiview-settings"
        onClick={()=>{setExpanded(value=>!value);setPreview(false);}}
        className="min-h-9 rounded-lg border border-border-main px-3 py-1.5 font-semibold text-text-main focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
        {expanded?'Replier':'Configurer'}
      </button>
    </div>
    {expanded && <div id="r5-multiview-settings" className="mt-3 flex flex-col gap-3 text-xs">
      <p className="text-text-muted">Une disposition par compte et poste, sans données patient.</p>
      <label className="flex flex-wrap items-center gap-2 font-semibold">Disposition
        <select value={choice} aria-label="Disposition R5" onChange={e=>{setChoice(e.target.value);setPreview(false);}}
          className="min-h-10 max-w-full rounded-lg border border-border-main bg-card px-3 py-2 font-normal">
          {layouts.map(l=><option key={l.id} value={l.id}
             disabled={!authorizeLayout(l,context,ratio).ok}>{l.label}</option>)}
        </select>
      </label>
      <div className="flex flex-wrap items-center gap-2 border-t border-border-main pt-3">
      <button type="button" disabled={busy||!allowed} onClick={()=>setPreview(true)}
        className="min-h-10 rounded-lg border border-border-main px-3 py-2 font-semibold disabled:opacity-50">Aperçu</button>
      <button type="button" disabled={busy||!allowed} onClick={()=>void save()}
        className="min-h-10 rounded-lg bg-primary px-4 py-2 font-bold text-on-primary disabled:opacity-50">Appliquer</button>
      <button type="button" disabled={busy} onClick={()=>setPreview(false)}
        className="min-h-10 rounded-lg border border-border-main px-3 py-2 disabled:opacity-50">Annuler</button>
      <button type="button" disabled={busy||!state.canRollback} onClick={()=>void rollback()}
        className="min-h-10 rounded-lg px-3 py-2 text-text-muted hover:underline disabled:opacity-50">Rollback</button>
      </div>
    </div>}
    {expanded&&preview&&selected&&<div data-testid="r5-multiview-preview" role="status"
       aria-label="Aperçu schématique sans données patient" className="mt-3">
       <p className="mb-2 text-xs">Aperçu : {selected.label}. Appliquer pour enregistrer.</p>
       <div style={{...geometryGridStyle(selected.geometry,ratio),height:152}}>
         {selected.slots.map((slot,index)=><div key={slot.id}
           style={geometrySlotStyle(selected.geometry,index)}
           className="flex items-center justify-center rounded-lg border border-border-main bg-medical-pearl p-2 text-center text-xs">
           {slot.module}
         </div>)}
       </div>
    </div>}
    {error&&<p role="alert" className="mt-2 text-xs text-danger">{error}</p>}
  </section>;
}
