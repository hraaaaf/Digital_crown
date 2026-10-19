import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity, Bell, CalendarDays, ClipboardList, Clock3,
  CreditCard, FileImage, FileText, FolderOpen, Image as ImageIcon,
  LayoutDashboard, Mail, MoreHorizontal, Phone, Receipt,
  Search, Settings, ShieldCheck, Users, type LucideIcon
} from 'lucide-react';
import OfficialLogo from '../../assets/logo.png';
import CompactLogo from '../../assets/logo-compact.png';
import './command-react-target.css';
import { appointments, type AppointmentStatus } from './command-synthetic-fixtures';
import { useSyntheticSession } from './command-synthetic-session';
import { getRoomDisplay } from './command-appointment-presentation';
import { Card, Pill } from './command-ui-primitives';
import { CommandPatientWorkspace } from './command-patient-workspace';
import { CommandAgenda } from './command-agenda';

const menu: {name: string; icon: LucideIcon}[] = [
  {name:'Command',icon:LayoutDashboard},{name:'Agenda',icon:CalendarDays},
  {name:'Patients',icon:Users},{name:'Dossier clinique',icon:FolderOpen},
  {name:'Imagerie',icon:ImageIcon},{name:'Cabinet',icon:Activity},
  {name:'Facturation',icon:Receipt},{name:'Documents',icon:FileText},
  {name:'Rapports',icon:ClipboardList}
];
export function CommandWorkbenchReactTarget(){
 const [view,setView]=useState('Command');
 const [tab,setTab]=useState('Vue d’ensemble');
 const [notification,setNotification]=useState('');
 const [agendaFocusRequest,setAgendaFocusRequest]=useState(0);
 const [activeNavigation,setActiveNavigation]=useState('Command');
 const [activeLane,setActiveLane]=useState(0);
 const [additionalOpen,setAdditionalOpen]=useState(false);
 const {state:session,dispatch,activeAppointment,currentStatus,samePractitionerNext,inChair,inWaiting,freeRooms,plannedSwitch,canBeginConsultation}=useSyntheticSession();
 const {activeAppointmentId,pendingAppointmentId,roomAssignments,mockStatuses}=session;
 const confirmButtonRef=React.useRef<HTMLButtonElement>(null);
 const cancelButtonRef=React.useRef<HTMLButtonElement>(null);
 const dialogRef=React.useRef<HTMLDivElement>(null);
 const patientHeadingRef=React.useRef<HTMLHeadingElement>(null);
 const previousPatientRef=React.useRef(activeAppointmentId);
 const invokedByRef=React.useRef<HTMLElement|null>(null);
 React.useEffect(()=>{
  if(!pendingAppointmentId)return;
  const siblings=Array.from(document.querySelectorAll<HTMLElement>('.cmd-sidebar,.cmd-toolbar,.cmd-heading,.cmd-workbench,.cmd-disclaimer,.cmd-mobile-context'));
  siblings.forEach(e=>{e.inert=true;});
  confirmButtonRef.current?.focus();
  return ()=>siblings.forEach(e=>{e.inert=false;});
 },[pendingAppointmentId]);
 React.useEffect(()=>{if(previousPatientRef.current!==activeAppointmentId){previousPatientRef.current=activeAppointmentId;patientHeadingRef.current?.focus();}},[activeAppointmentId]);
 React.useEffect(()=>{if(agendaFocusRequest>0&&view==='Command')document.getElementById('cmd-agenda')?.focus();},[agendaFocusRequest,view]);
 const announce=(what:string)=>setNotification(what+' : simulation uniquement, aucune opération clinique.');
 const requestSwitch=(refOrId:string)=>{
  const target=appointments.find(a=>a.id===refOrId||a.ref===refOrId);
  if(!target||target.id===activeAppointment.id)return;
  invokedByRef.current=document.activeElement instanceof HTMLElement?document.activeElement:null;
  dispatch({type:'request-switch',appointmentId:target.id});setNotification('');
 };
 const cancelSwitch=()=>{dispatch({type:'cancel-switch'});requestAnimationFrame(()=>invokedByRef.current?.focus());};
 const confirmSwitch=()=>{if(!plannedSwitch)return;dispatch({type:'confirm-switch'});setTab('Vue d’ensemble');setAdditionalOpen(false);setNotification('Patient fictif sélectionné. Aucune opération clinique.');};
 const updateMockStatus=(next:AppointmentStatus)=>{
  dispatch({type:'transition',to:next as 'current'|'paused'|'finished'});
  setNotification('État du RDV fictif : '+next+'. Aucune écriture dans le Cabinet.');
 };
 const roomDisplay=getRoomDisplay(activeAppointment,roomAssignments);
 const trapDialogFocus=(e:React.KeyboardEvent<HTMLDivElement>)=>{
  if(e.key==='Escape'){e.preventDefault();cancelSwitch();return;}
  if(e.key!=='Tab')return;
  const first=confirmButtonRef.current,last=cancelButtonRef.current;
  if(!first||!last)return;
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
 };
 return <div className="cmd-shell" data-command-target="07-C-react-isolated" data-synthetic-fixtures="true" data-active-patient-id={activeAppointment.patientId} data-active-appointment-id={activeAppointment.id} data-occupied-rooms={inChair} data-free-rooms={freeRooms}>
  <aside className="cmd-sidebar">
    <div className="cmd-brand"><img className="cmd-logo-full" src={OfficialLogo} alt="Digital Crown"/><img className="cmd-logo-mini" src={CompactLogo} alt="Digital Crown — logo compact" /><small>COMMAND · 07-C</small></div>
    <div className="cmd-navtitle">ESPACE CABINET</div>
    <nav aria-label="Navigation de démonstration" className="cmd-navigation">{menu.map(({name,icon:Icon})=><button type="button" key={name} aria-current={activeNavigation===name?'page':undefined} aria-label={name} className={activeNavigation===name?'cmd-selected':''} onClick={()=>{setActiveNavigation(name);if(name==='Agenda'){setView('Command');setAgendaFocusRequest(v=>v+1);}else if(name==='Dossier clinique'||name==='Imagerie'){setView('Command');setTab(name==='Imagerie'?'Imagerie':'Dossier');}else{setView(name);if(name==='Command')setTab('Vue d’ensemble');}setNotification('');}}><Icon size={17} aria-hidden="true"/><span>{name}</span></button>)}</nav>
    <div className="cmd-sidebarfooter"><Settings size={16}/> Maquette sans backend<br/><small>Données TEST uniquement</small></div>
  </aside>
  <main className="cmd-main">
   <header className="cmd-toolbar">
    <span className="cmd-search" aria-label="Recherche non disponible dans le prototype"><Search size={16}/> Recherche — en construction dans le prototype</span>
    <span className="cmd-topright"><small>Thème hérité du Cabinet</small><Bell size={16}/><span className="cmd-avatar">DC</span></span>
   </header>
   <div className="cmd-content">
    <div className="cmd-heading"><div className="cmd-headingcopy"><p className="cmd-kicker">ESPACE DE TRAVAIL <span aria-hidden="true">/</span> DIGITAL CROWN</p><h1>{view} <Pill>CIBLE 07-C</Pill></h1><p>Vue multi-praticien · Dossier {activeAppointment.patientId} · Données 100 % synthétiques</p></div><div className="cmd-chips"><Pill tone="success"><Users size={13} aria-hidden="true"/> {inChair} au fauteuil</Pill><Pill tone="warning"><Clock3 size={13} aria-hidden="true"/> {inWaiting} en attente</Pill><Pill><CalendarDays size={13} aria-hidden="true"/> {freeRooms} salles libres</Pill></div></div>
    <div className="cmd-mobile-context" aria-label="Contexte clinique fictif toujours visible" data-patient-id={activeAppointment.patientId} data-appointment-id={activeAppointment.id}>
     <div><strong>Patient {activeAppointment.patientId}</strong><small>RDV {activeAppointment.ref} · Dr {['A','B','C'][activeAppointment.practitionerId]} · {activeAppointment.startLabel}</small></div>
     <button type="button" onClick={()=>patientHeadingRef.current?.focus()} aria-label={'Revenir au dossier de Patient '+activeAppointment.patientId}>Voir dossier</button>
    </div>
    {plannedSwitch&&<div ref={dialogRef} className="cmd-switch-confirm" role="alertdialog" aria-modal="true" aria-labelledby="cmd-switch-title" aria-describedby="cmd-switch-description" onKeyDown={trapDialogFocus}><strong id="cmd-switch-title">{plannedSwitch.patientId===activeAppointment.patientId?'Changement de rendez-vous fictif':'Changement de dossier fictif'} : Patient {activeAppointment.patientId} → Patient {plannedSwitch.patientId}</strong><span id="cmd-switch-description">RDV {plannedSwitch.ref} · Dr {['A','B','C'][plannedSwitch.practitionerId]} · {plannedSwitch.startLabel}–{plannedSwitch.endLabel}. Aucun enregistrement clinique.</span><button type="button" ref={confirmButtonRef} className="cmd-primary" onClick={confirmSwitch}>Confirmer le changement de patient</button><button type="button" ref={cancelButtonRef} onClick={cancelSwitch}>Annuler le changement</button></div>}
    {notification&&<div className="cmd-notice" role="status"><ShieldCheck size={15}/>{notification}<button onClick={()=>setNotification('')} aria-label="Fermer">×</button></div>}
    {view!=='Command'?
     <Card title={view}><div className="cmd-placeholder">Prévisualisation en construction — aucune opération clinique. <button onClick={()=>{setView('Command');setActiveNavigation('Command');}}>Retour au cockpit</button></div></Card>
     :<div className="cmd-workbench">
       <CommandAgenda activeLane={activeLane} setActiveLane={setActiveLane} mockStatuses={mockStatuses} requestSwitch={requestSwitch} announce={announce}/>
       <CommandPatientWorkspace key={activeAppointment.patientId} activeAppointment={activeAppointment} currentStatus={currentStatus} roomDisplay={roomDisplay} patientHeadingRef={patientHeadingRef} tab={tab} setTab={setTab} additionalOpen={additionalOpen} setAdditionalOpen={setAdditionalOpen} mockStatuses={mockStatuses} samePractitionerNext={samePractitionerNext} canBeginConsultation={canBeginConsultation} requestSwitch={requestSwitch} updateMockStatus={updateMockStatus} announce={announce} clearNotification={()=>setNotification('')}/>
     </div>}
    <footer className="cmd-disclaimer">LOT07 / 07-C · TARGET REACT ISOLÉ · Actifs Digital Crown d’origine · Tokens existants · Aucune connexion Cabinet</footer>
   </div>
  </main>
 </div>;
}
const mount=document.getElementById('root');
if (!mount) throw new Error('Missing isolated React target mount');
createRoot(mount).render(<CommandWorkbenchReactTarget/>);
