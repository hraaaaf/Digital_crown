import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import type { AppUser } from '../../types';
import { useAuthStore } from '../../stores/useAuthStore';
import { hasAccess } from '../../utils/accessControl';
import { workstationModeService } from '../../services/workstationMode';
import { api } from '../../services/api';
import { PatientMediaTimeline } from '../patients/components/PatientMediaTimeline';
import { OrthoLongitudinalComparePanel } from '../ortho/OrthoLongitudinalComparePanel';
import { StudioLayoutFrame } from './StudioLayoutFrame';
import { authorizeLayout, PRESETS, type Geometry, type Layout, type ModuleKey, type WorkspaceContext } from './studioLayouts';
import { geometryGridStyle, geometrySlotStyle } from './studioGeometry';
import './CabinetMultiViewLab.css';

export interface MultiViewPatient {
  id: number;
  nom: string;
  prenom: string;
  numero_dossier: string;
}

/** Explicit DEV-only opt-in. Importing this module never enables the lab in production. */
export function isCabinetMultiViewLabEnabled(dev: boolean, flag: string | undefined): boolean {
  return dev === true && flag === '1';
}

function desktopSubscribe(onChange: () => void) {
  const mq = window.matchMedia?.('(min-width: 1280px)');
  mq?.addEventListener('change', onChange);
  return () => mq?.removeEventListener('change', onChange);
}
function desktopSnapshot() { return Boolean(window.matchMedia?.('(min-width: 1280px)').matches); }

const PILOT_LAYOUTS: readonly Layout[] = [
  {id:'dossier-media-2cols',label:'Dossier + Médiathèque — colonnes',geometry:'two-columns',
    slots:[{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'}]},
  {id:'dossier-media-2rows',label:'Dossier + Médiathèque — lignes',geometry:'two-rows',
    slots:[{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'}]},
  {id:'media-focus',label:'Médiathèque — vue unique',geometry:'single',
    slots:[{id:'imagerie',module:'imagerie'}]},
  {id:'dossier-media-suivi-3cols',label:'Dossier + Médias + Suivi — 3 colonnes',geometry:'three-columns',
    slots:[{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'},{id:'suivi',module:'suivi'}]},
  {id:'dossier-media-suivi-hero',label:'Dossier dominant + Médias + Suivi',geometry:'hero-two',
    slots:[{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'},{id:'suivi',module:'suivi'}]},
];

/** Only real existing module adapters appear here; there are NO mocked clinical slots. */
export function selectablePilotLayouts(allowCephalo: boolean): readonly Layout[] {
  return PILOT_LAYOUTS.filter(layout => allowCephalo || layout.slots.every(slot => slot.module !== 'suivi'));
}

function tenantKey(user: AppUser | null): string | null {
  if (!user || !user.id) return null;
  // Mirrors local employer/owner identity purely for in-memory UI partitioning.
  // Actual cross-tenant permission is enforced by each backend route, NOT this string.
  if (typeof user.employer_id === 'number' && user.employer_id > 0) return String(user.employer_id);
  if (user.employer_id === null && (user.role === 'DENTISTE' || user.role === 'ADMIN')) return String(user.id);
  return null;
}

/**
 * Actual patient dossier route adapter, opt-in development only.
 * Reuses ONE authenticated read-only PatientMediaTimeline and optional existing longitudinal
 * comparison; never mounts arbitrary module names or second CephaloWorkspace.
 */
export function CabinetMultiViewLab({patient, routePatientId, user}: {
  patient: MultiViewPatient;
  routePatientId: string | undefined;
  user: AppUser | null;
}) {
  const desktop = useSyncExternalStore(desktopSubscribe, desktopSnapshot, () => false);
  const [workstationProof,setWorkstationProof] = useState<{key:string;id:string}|null>(null);
  const [patientProof,setPatientProof] = useState<{key:string;patient:MultiViewPatient}|null>(null);
  const [workspaceWidth,setWorkspaceWidth] = useState(0);
  const [appliedId,setAppliedId] = useState(PILOT_LAYOUTS[0].id);
  const [draftId,setDraftId] = useState(PILOT_LAYOUTS[0].id);
  const [preview,setPreview] = useState(false);
  const [ratio,setRatio] = useState(50);
  const [exchanged,setExchanged] = useState(false);
  const root = useRef<HTMLDivElement>(null);

  const activeIdentity = useAuthStore(state => state.isAuthenticated);
  const identityKey = JSON.stringify([user?.id ?? null,tenantKey(user),user?.role,
    user?.permissions ?? null,activeIdentity]);
  const workstationId = workstationProof?.key===identityKey ? workstationProof.id : null;
  const proofKey = identityKey + ':' + String(patient.id);
  const trustedPatient = patientProof?.key===proofKey ? patientProof.patient : null;
  const canPatients = Boolean(activeIdentity && hasAccess(user,'patients'));
  const canCephalo = Boolean(activeIdentity && hasAccess(user,'cephalo'));
  const patientMatches = Boolean(patient && Number.isSafeInteger(patient.id) &&
    patient.id > 0 && String(patient.id) === routePatientId);

  useEffect(() => {
    setWorkstationProof(null);
    if (!desktop || !canPatients || !patientMatches) return;
    let active=true;
    const load=async()=>{
      // UI is fail-closed while this authenticated bootstrap is pending or denied.
      setWorkstationProof(null);
      try {
        const state=await workstationModeService.getBootstrapState();
        const current=useAuthStore.getState();
        if (!active || current.user?.id !== user?.id || current.isAuthenticated !== true) return;
        if (state.authenticated === true && state.enrollmentRequired === false &&
            (state.defaultExperience === 'cabinet' || state.defaultExperience === null) &&
            state.stationLocked === false &&
            typeof state.workstationId === 'string' && state.workstationId.trim()) {
          setWorkstationProof({key:identityKey,id:state.workstationId});
        }
      } catch {
        if (active) setWorkstationProof(null);
      }
    };
    void load();
    const unsub=workstationModeService.subscribe(()=>{void load();});
    return ()=>{active=false;unsub();};
  },[desktop,canPatients,patientMatches,identityKey,user?.id]);

  useEffect(() => {
    setPatientProof(null);
    if (!desktop || !canPatients || !patientMatches || !user?.id) return;
    let active=true;
    api.get('/patients/' + patient.id).then(response => {
      const current=useAuthStore.getState();
      if (!active || current.user?.id !== user.id || current.isAuthenticated !== true) return;
      const verified=response.data as Partial<MultiViewPatient> | null;
      if (verified && verified.id===patient.id && typeof verified.nom==='string' &&
          typeof verified.prenom==='string' && typeof verified.numero_dossier==='string') {
        setPatientProof({key:proofKey,patient:verified as MultiViewPatient});
      }
    }).catch(()=>{if(active)setPatientProof(null);});
    return ()=>{active=false;};
  },[desktop,canPatients,patientMatches,proofKey,user?.id,patient.id]);

  useEffect(() => {
    if (!desktop || !canPatients || !patientMatches) {
      setWorkspaceWidth(0);
      return;
    }
    const element=root.current;
    if (!element) return;
    const update=()=>setWorkspaceWidth(Math.floor(Math.min(window.innerWidth,element.getBoundingClientRect().width)));
    update();
    const observer=typeof ResizeObserver!=='undefined' ? new ResizeObserver(update) : null;
    observer?.observe(element);
    window.addEventListener('resize',update);
    return ()=>{observer?.disconnect();window.removeEventListener('resize',update);};
  },[desktop,canPatients,patientMatches]);

  if (!activeIdentity || !canPatients || !patientMatches) {
    return <p role="alert">Vues multiples refusées : patient ou autorisation non vérifiés.</p>;
  }
  // Genuine legacy mobile/tablet content is preserved; no MultiView slot mounted.
  if (!desktop) return <PatientMediaTimeline patientId={patient.id}/>;

  const possible=selectablePilotLayouts(canCephalo);
  const applied=possible.find(item=>item.id===appliedId) || possible[0];
  const draft=possible.find(item=>item.id===draftId) || applied;
  const mounted: Layout = exchanged && applied.slots.length>1
    ? {...applied,slots:[...applied.slots].reverse()} : applied;
  const context: WorkspaceContext = {
    authenticated:activeIdentity && Boolean(user),
    userId:user?.id ? String(user.id) : null,
    workstationId,
    tenantId:tenantKey(user),
    patientId:patientMatches && trustedPatient ? trustedPatient.id : null,
    cssViewportWidth:workspaceWidth,
    allowedModules: [
      ...(canPatients ? ['dossier','imagerie'] as ModuleKey[] : []),
      ...(canCephalo ? ['suivi'] as ModuleKey[] : []),
    ],
  };
  const mountedGate=authorizeLayout(mounted,context,ratio);
  const accepted=mountedGate.ok;
  // At 1280px the desktop viewport can be wide while the actual Cabinet
  // workspace is too narrow for any safe MultiView composition.  Never force
  // undersized clinical slots or leave a blank pane: show the existing genuine
  // single-media experience, but only with a verified patient and workstation.
  const responsiveSingleMediaFallback=!accepted &&
    (mountedGate.reason==='DESKTOP_ONLY' || mountedGate.reason==='UNREADABLE_LAYOUT') &&
    Boolean(workstationId && trustedPatient);
  const canApply=authorizeLayout(draft,context,50).ok;

  const renderSlot=(slot:{module:ModuleKey})=>{
    if (!trustedPatient) return null;
    if (slot.module==='imagerie') return <PatientMediaTimeline patientId={trustedPatient.id} readOnly/>;
    if (slot.module==='dossier') return (
      <div data-testid="multiview-real-dossier" className="space-y-2 p-3 text-sm">
        <p className="font-semibold">Dossier patient</p>
        <dl className="space-y-2">
          <div><dt className="text-text-muted">Patient</dt><dd className="font-medium" >{trustedPatient.prenom} {trustedPatient.nom}</dd></div>
          <div><dt className="text-text-muted">N° de dossier</dt><dd className="font-medium" >{trustedPatient.numero_dossier}</dd></div>
        </dl>
      </div>
    );
    if (slot.module==='suivi' && canCephalo) {
      return <OrthoLongitudinalComparePanel patientId={trustedPatient.id}/>;
    }
    // Never synthesize absent business modules: the resolver must deny them.
    return null;
  };

  return (
    <div ref={root} data-v15-071-real-cabinet-lab className="min-w-0 space-y-3">
      <header className="rounded-xl border border-border-main bg-card-bg p-3 space-y-2">
        <p className="text-sm font-bold text-text-main">Vues multiples · laboratoire Cabinet Desktop</p>
        <p className="text-xs text-text-muted">Une seule identité patient. Dispositions de démonstration non enregistrées.</p>
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="multiview-pilot-select" className="text-sm">Disposition</label>
          <select id="multiview-pilot-select" aria-label="Disposition MultiView"
            value={draft.id} onChange={e=>{setDraftId(e.target.value);setPreview(false);}}
            className="rounded-md border border-border-main bg-card px-2 py-2 text-sm">
            <optgroup label="Connectées aux vrais modules">
              {possible.map(item=><option key={item.id} value={item.id}>{item.label}</option>)}
            </optgroup>
            <optgroup label="Neuf directions produit — non connectées">
              {PRESETS.map(item=><option key={item.id} value={'future-'+item.id} disabled>{item.label} — à intégrer</option>)}
            </optgroup>
          </select>
          <button type="button" onClick={()=>setPreview(true)} className="rounded-md border px-3 py-2 text-xs">Aperçu</button>
          <button type="button" disabled={!preview || !canApply}
            onClick={()=>{setAppliedId(draft.id);setRatio(50);setExchanged(false);setPreview(false);}}
            className="rounded-md border px-3 py-2 text-xs disabled:opacity-40">Appliquer</button>
          <button type="button" onClick={()=>{setDraftId(applied.id);setPreview(false);}}
            className="rounded-md border px-3 py-2 text-xs">Annuler</button>
          <button type="button" onClick={()=>{setAppliedId(PILOT_LAYOUTS[0].id);setDraftId(PILOT_LAYOUTS[0].id);
            setExchanged(false);setRatio(50);setPreview(false);}}
            className="rounded-md border px-3 py-2 text-xs">Réinitialiser</button>
        </div>
        {preview && (
          <div aria-label="Aperçu schématique sans données patient" data-testid="multiview-schematic-preview"
            className="rounded-lg border border-dashed border-border-main p-2">
            <p className="text-xs mb-2">Aperçu de la disposition — sans chargement clinique</p>
            <div style={{...geometryGridStyle(draft.geometry),height:96}}>
              {draft.slots.map((slot,index)=><div key={slot.id} style={geometrySlotStyle(draft.geometry,index)}
                className="flex items-center justify-center min-w-0 rounded border border-border-main bg-medical-pearl text-xs">
                {slot.module}</div>)}
            </div>
          </div>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" disabled={applied.slots.length<2}
            onClick={()=>setExchanged(value=>!value)} className="rounded-md border px-3 py-2 text-xs disabled:opacity-40">
            Échanger les vues
          </button>
          {(applied.geometry==='two-columns' || applied.geometry==='hero-two') &&
            <label className="flex items-center gap-2 text-xs">
              Largeur du panneau principal
              <input type="range" min={37} max={63} step={1} value={ratio}
                aria-label="Redimensionner les panneaux" onChange={e=>setRatio(Number(e.target.value))}/>
              <span>{ratio} %</span>
            </label>}
        </div>
      </header>
      {!accepted && <p role="status" className="text-xs text-text-muted">
        {responsiveSingleMediaFallback
          ? 'Disposition trop large pour cet écran : affichage sécurisé de la médiathèque seule.'
          : 'Disposition protégée : identité du poste, permissions ou largeur des panneaux à vérifier.'}
      </p>}
      {responsiveSingleMediaFallback && trustedPatient
        ? <section data-testid="multiview-responsive-single-media-fallback"
            aria-label="Médiathèque clinique seule — repli de lisibilité"
            className="min-w-0 rounded-xl border border-border-main bg-card-bg p-2">
            <PatientMediaTimeline patientId={trustedPatient.id}/>
          </section>
        : <StudioLayoutFrame layout={mounted} context={context} primaryRatio={ratio}
            renderSlot={renderSlot}/>} 
    </div>
  );
}
