import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity, Bell, CalendarDays, ChevronDown, ClipboardList, Clock3,
  CreditCard, FileImage, FileText, FolderOpen, Image as ImageIcon,
  LayoutDashboard, Mail, MoreHorizontal, Phone, Plus, Receipt,
  Search, Settings, ShieldCheck, Users, type LucideIcon
} from 'lucide-react';
import OfficialLogo from '../../assets/logo.png';
import CompactLogo from '../../assets/logo-compact.png';
import { PremiumOdontogramSVG } from '../../components/odontogram/PremiumOdontogramSVG';
import './command-react-target.css';
import { appointments, quarterHours, initialRoomAssignments, nextArrivedForPractitioner, occupiedRoomCount, type AppointmentStatus } from './command-synthetic-fixtures';
import { AppointmentIdentity, getRoomDisplay } from './command-appointment-presentation';

type Tone = 'success'|'warning'|'danger'|'info';
const menu: {name: string; icon: LucideIcon}[] = [
  {name:'Command',icon:LayoutDashboard},{name:'Agenda',icon:CalendarDays},
  {name:'Patients',icon:Users},{name:'Dossier clinique',icon:FolderOpen},
  {name:'Imagerie',icon:ImageIcon},{name:'Cabinet',icon:Activity},
  {name:'Facturation',icon:Receipt},{name:'Documents',icon:FileText},
  {name:'Rapports',icon:ClipboardList}
];
const patientTabs = ['Vue d’ensemble','Dossier','Plan de traitement','Odontogramme','Imagerie','Documents','Facturation'] as const;
function Pill({children,tone='info'}:{children:React.ReactNode;tone?:Tone}) {
 return <span className={'cmd-pill cmd-pill-'+tone}>{children}</span>;
}
function Card({title,action,children,className='',hidden=false}:{title:string;action?:React.ReactNode;children:React.ReactNode;className?:string;hidden?:boolean}) {
 return <section hidden={hidden} className={'cmd-card '+className}><header className="cmd-cardhead"><h3>{title}</h3>{action}</header>{children}</section>;
}
export function CommandWorkbenchReactTarget(){
 const [view,setView]=useState('Command');
 const [tab,setTab]=useState('Vue d’ensemble');
 const [notification,setNotification]=useState('');
 const [mode,setMode]=useState('Jour');
 const [activeLane,setActiveLane]=useState(0);
 const [additionalOpen,setAdditionalOpen]=useState(false);
 const [activeAppointmentId,setActiveAppointmentId]=useState('APT-TEST-001');
 const [roomAssignments,setRoomAssignments]=useState<Record<number,string|null>>({...initialRoomAssignments});
 const [pendingAppointmentId,setPendingAppointmentId]=useState<string|null>(null);
 const [mockStatuses,setMockStatuses]=useState<Record<string,AppointmentStatus>>({});
 const activeAppointment=appointments.find(a=>a.id===activeAppointmentId) ?? appointments[0];
 const currentStatus=mockStatuses[activeAppointment.id] ?? activeAppointment.status;
 const inChair=occupiedRoomCount(roomAssignments);
 const inWaiting=appointments.filter(a=>a.arrival==='arrived'&&(mockStatuses[a.id]??a.status)==='waiting').length;
 const freeRooms=Object.keys(roomAssignments).length-inChair;
 const confirmButtonRef=React.useRef<HTMLButtonElement>(null);
 const cancelButtonRef=React.useRef<HTMLButtonElement>(null);
 const dialogRef=React.useRef<HTMLDivElement>(null);
 const patientHeadingRef=React.useRef<HTMLHeadingElement>(null);
 const previousPatientRef=React.useRef(activeAppointmentId);
 const invokedByRef=React.useRef<HTMLElement|null>(null);
 React.useEffect(()=>{
  if(!pendingAppointmentId)return;
  const siblings=Array.from(document.querySelectorAll<HTMLElement>('.cmd-sidebar,.cmd-toolbar,.cmd-heading,.cmd-workbench,.cmd-disclaimer'));
  siblings.forEach(e=>{e.inert=true;});
  confirmButtonRef.current?.focus();
  return ()=>siblings.forEach(e=>{e.inert=false;});
 },[pendingAppointmentId]);
 React.useEffect(()=>{if(previousPatientRef.current!==activeAppointmentId){previousPatientRef.current=activeAppointmentId;patientHeadingRef.current?.focus();}},[activeAppointmentId]);
 const samePractitionerNext=nextArrivedForPractitioner(activeAppointment,mockStatuses);
 const plannedSwitch=appointments.find(a=>a.id===pendingAppointmentId);
 const patientTag='Patient '+activeAppointment.patientId;
 const announce=(what:string)=>setNotification(what+' : simulation uniquement, aucune opération clinique.');
 const requestSwitch=(refOrId:string)=>{
  const target=appointments.find(a=>a.id===refOrId||a.ref===refOrId);
  if(!target||target.id===activeAppointment.id)return;
  invokedByRef.current=document.activeElement instanceof HTMLElement?document.activeElement:null;
  setPendingAppointmentId(target.id);setNotification('');
 };
 const cancelSwitch=()=>{setPendingAppointmentId(null);requestAnimationFrame(()=>invokedByRef.current?.focus());};
 const confirmSwitch=()=>{if(!plannedSwitch)return;setActiveAppointmentId(plannedSwitch.id);setTab('Vue d’ensemble');setAdditionalOpen(false);setPendingAppointmentId(null);setNotification('Patient fictif sélectionné. Aucune opération clinique.');};
 const updateMockStatus=(next:AppointmentStatus)=>{
  setMockStatuses(previous=>({...previous,[activeAppointment.id]:next}));
  if(next==='finished')setRoomAssignments(previous=>Object.fromEntries(Object.entries(previous).map(([room,id])=>[room,id===activeAppointment.id?null:id])));
  if(next==='current'&&currentStatus==='waiting')setRoomAssignments(previous=>({...previous,[activeAppointment.room]:activeAppointment.id}));
  setNotification('État du RDV fictif : '+next+'. Aucune écriture dans le Cabinet.');
 };
 const activeRoomOccupant=roomAssignments[activeAppointment.room];
 const roomDisplay=getRoomDisplay(activeAppointment,roomAssignments);
 const canBeginConsultation=currentStatus==='waiting'&&activeAppointment.arrival==='arrived'&&!activeRoomOccupant;
 const trapDialogFocus=(e:React.KeyboardEvent<HTMLDivElement>)=>{
  if(e.key==='Escape'){e.preventDefault();cancelSwitch();return;}
  if(e.key!=='Tab')return;
  const first=confirmButtonRef.current,last=cancelButtonRef.current;
  if(!first||!last)return;
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
 };
 const containsTab=(...names:string[])=>names.includes(tab);
 return <div className="cmd-shell" data-command-target="07-C-react-isolated" data-synthetic-fixtures="true" data-active-patient-id={activeAppointment.patientId} data-active-appointment-id={activeAppointment.id} data-occupied-rooms={inChair} data-free-rooms={freeRooms}>
  <aside className="cmd-sidebar">
    <div className="cmd-brand"><img className="cmd-logo-full" src={OfficialLogo} alt="Digital Crown"/><img className="cmd-logo-mini" src={CompactLogo} alt="Digital Crown — logo compact" /><small>COMMAND · 07-C</small></div>
    <div className="cmd-navtitle">ESPACE CABINET</div>
    <nav aria-label="Navigation de démonstration" className="cmd-navigation">{menu.map(({name,icon:Icon})=><button type="button" key={name} aria-current={view===name?'page':undefined} aria-label={name} className={view===name?'cmd-selected':''} onClick={()=>{if(name==='Dossier clinique'||name==='Imagerie'){setView('Command');setTab(name==='Imagerie'?'Imagerie':'Dossier');}else{setView(name);if(name==='Command')setTab('Vue d’ensemble');}setNotification('');}}><Icon size={17} aria-hidden="true"/><span>{name}</span></button>)}</nav>
    <div className="cmd-sidebarfooter"><Settings size={16}/> Maquette sans backend<br/><small>Données TEST uniquement</small></div>
  </aside>
  <main className="cmd-main">
   <header className="cmd-toolbar">
    <span className="cmd-search" aria-label="Recherche non disponible dans le prototype"><Search size={16}/> Recherche — en construction dans le prototype</span>
    <span className="cmd-topright"><small>Thème hérité du Cabinet</small><Bell size={16}/><span className="cmd-avatar">DC</span></span>
   </header>
   <div className="cmd-content">
    <div className="cmd-heading"><div className="cmd-headingcopy"><p className="cmd-kicker">ESPACE DE TRAVAIL <span aria-hidden="true">/</span> DIGITAL CROWN</p><h1>{view} <Pill>CIBLE 07-C</Pill></h1><p>Vue multi-praticien · Dossier {activeAppointment.patientId} · Données 100 % synthétiques</p></div><div className="cmd-chips"><Pill tone="success"><Users size={13} aria-hidden="true"/> {inChair} au fauteuil</Pill><Pill tone="warning"><Clock3 size={13} aria-hidden="true"/> {inWaiting} en attente</Pill><Pill><CalendarDays size={13} aria-hidden="true"/> {freeRooms} salles libres</Pill></div></div>
    {plannedSwitch&&<div ref={dialogRef} className="cmd-switch-confirm" role="alertdialog" aria-modal="true" aria-labelledby="cmd-switch-title" aria-describedby="cmd-switch-description" onKeyDown={trapDialogFocus}><strong id="cmd-switch-title">{plannedSwitch.patientId===activeAppointment.patientId?'Changement de rendez-vous fictif':'Changement de dossier fictif'} : Patient {activeAppointment.patientId} → Patient {plannedSwitch.patientId}</strong><span id="cmd-switch-description">RDV {plannedSwitch.ref} · Dr {['A','B','C'][plannedSwitch.practitionerId]} · {plannedSwitch.startLabel}–{plannedSwitch.endLabel}. Aucun enregistrement clinique.</span><button type="button" ref={confirmButtonRef} className="cmd-primary" onClick={confirmSwitch}>Confirmer le changement de patient</button><button type="button" ref={cancelButtonRef} onClick={cancelSwitch}>Annuler le changement</button></div>}
    {notification&&<div className="cmd-notice" role="status"><ShieldCheck size={15}/>{notification}<button onClick={()=>setNotification('')} aria-label="Fermer">×</button></div>}
    {view!=='Command'?
     <Card title={view}><div className="cmd-placeholder">Prévisualisation hors module clinique. <button onClick={()=>setView('Command')}>Retour au cockpit</button></div></Card>
     :<div className="cmd-workbench">
       <Card title="Agenda · Vue journalière" className="cmd-agenda" action={<small>15 min · 3 praticiens</small>}>
        <div className="cmd-datebar"><button onClick={()=>announce('Calendrier')}><CalendarDays size={15}/> Lundi 19 octobre 2026 <ChevronDown size={13}/></button><button onClick={()=>announce('Aujourd’hui')}>Aujourd’hui</button><button className="cmd-primary" onClick={()=>announce('RDV')}><Plus size={15}/> RDV</button></div>
        <div className="cmd-agenda-modes">{['Jour','Semaine','Liste'].map(x=><button aria-pressed={mode===x} className={mode===x?'active':''} key={x} onClick={()=>{setMode(x);if(x!=='Jour')announce(x)}}>{x}</button>)}</div>
        <div className="cmd-mobile-lanes" role="group" aria-label="Praticien affiché dans l’agenda mobile">{['Dr A','Dr B','Dr C'].map((name,index)=><button key={name} type="button" aria-label={'Agenda '+name} aria-pressed={activeLane===index} onClick={()=>setActiveLane(index)}>{name}</button>)}</div>
        <div className="cmd-agenda-overflow"><div className="cmd-calendar" data-quarter-hour-grid="true" data-active-lane={activeLane}>
         <div className="cmd-timehead" style={{gridRow:1,gridColumn:1}}>Heure</div>
         {['Dr A · Salle 1','Dr B · Salle 2','Dr C · Salle 3'].map((name,lane)=><div className="cmd-lanehead" key={name} data-lane={lane} data-current-lane={activeLane===lane} style={{gridRow:1,gridColumn:lane+2}}><b>{['DA','DB','DC'][lane]}</b><span>{name}<small>{lane===2?'Chirurgie':'Omnipratique'}</small></span></div>)}
         {quarterHours.map(({label,minute},tick)=><React.Fragment key={label}><div className="cmd-hour" data-minute={minute} style={{gridRow:tick+2,gridColumn:1}}>{label}</div>{[0,1,2].map(lane=><div key={lane} className={'cmd-quarter-cell '+(minute===0?'cmd-quarter-start':'')} data-lane={lane} data-current-lane={activeLane===lane} style={{gridRow:tick+2,gridColumn:lane+2}} aria-hidden="true"/>)}</React.Fragment>)}
         {appointments.map(appt=><button key={appt.id} type="button" data-lane={appt.practitionerId} data-current-lane={activeLane===appt.practitionerId} data-appointment-id={appt.id} data-patient-id={appt.patientId} onClick={()=>requestSwitch(appt.id)} style={{gridRow:`${(appt.startMinutes-480)/15+2} / span ${Math.max(1,appt.duration/15)}`,gridColumn:appt.practitionerId+2}} className={'cmd-appt cmd-appt-'+(mockStatuses[appt.id]??appt.status)} aria-label={'Patient '+appt.patientId+', rendez-vous '+appt.ref+', '+appt.label+', '+appt.duration+' minutes, démonstration'}><AppointmentIdentity appointment={appt}/></button>)}
        </div></div>
        <div className="cmd-legend"><span>● Réalisé</span><span>● En attente</span><span>● À venir</span><span>● Urgence</span></div>
       </Card>
       <div className="cmd-right" key={activeAppointment.patientId} data-patient-id={activeAppointment.patientId}>
        <div className="cmd-patienthero"><div className="cmd-patientavatar">T</div><div className="cmd-patientintro"><p className="cmd-patienteyebrow" data-room-state={roomDisplay.state}>DOSSIER ACTIF <span aria-hidden="true">·</span> {roomDisplay.eyebrow}</p><h2 tabIndex={-1} ref={patientHeadingRef}>{patientTag} <Pill tone={currentStatus==='current'?'success':currentStatus==='paused'?'warning':'info'}>{currentStatus==='current'?'En cours':currentStatus==='paused'?'En pause':currentStatus==='finished'?'Terminé':currentStatus==='waiting'?'En attente':'RDV fictif'}</Pill></h2><p>Identité fictive · Dr {['A','B','C'][activeAppointment.practitionerId]} · {roomDisplay.description}</p><span><Pill>Accès non testé</Pill> <Pill>Données synthétiques</Pill></span></div><div className="cmd-contact"><button aria-label="Téléphone démonstration" onClick={()=>announce('Téléphone')}><Phone size={15}/></button><button aria-label="Mail démonstration" onClick={()=>announce('E-mail')}><Mail size={15}/></button><button aria-label="Plus démonstration" onClick={()=>announce('Menu')}><MoreHorizontal size={15}/></button></div><div className="cmd-patienttime"><strong>{activeAppointment.startLabel} – {activeAppointment.endLabel}</strong><small>RDV {activeAppointment.ref} · {activeAppointment.label}</small><span><Clock3 size={12}/> {activeAppointment.duration} min fictives</span></div><div className="cmd-patientbuttons"><button className="cmd-primary" disabled={currentStatus!=='current'&&currentStatus!=='paused'} onClick={()=>updateMockStatus(currentStatus==='paused'?'current':'paused')}>{currentStatus==='paused'?'Reprendre (simulation)':'Mettre en pause'}</button><button disabled={currentStatus!=='current'&&currentStatus!=='paused'} onClick={()=>updateMockStatus('finished')}>Terminer le RDV (simulation)</button><button disabled={!samePractitionerNext} onClick={()=>samePractitionerNext&&requestSwitch(samePractitionerNext.id)}>Patient suivant (même praticien)</button>{canBeginConsultation&&<button onClick={()=>updateMockStatus('current')}>Démarrer la consultation (simulation)</button>}</div></div>
        <div className="cmd-tabs" role="tablist" aria-label="Dossier fictif">{patientTabs.map((t,index)=><button role="tab" key={t} id={'cmd-tab-'+index} aria-controls="cmd-cards" aria-selected={tab===t} tabIndex={tab===t?0:-1} className={tab===t?'active':''} onClick={()=>{setTab(t);setNotification('');}} onKeyDown={e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const next=(index+(e.key==='ArrowRight'?1:patientTabs.length-1))%patientTabs.length;setTab(patientTabs[next]);const tabs=e.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]');tabs?.[next]?.focus();}}}>{t}</button>)}</div>
        <div className="cmd-cards" key={activeAppointment.patientId+'-'+tab} id="cmd-cards" data-tab={tab} role="tabpanel" aria-labelledby={'cmd-tab-'+patientTabs.indexOf(tab as typeof patientTabs[number])} aria-label={'Panneau '+tab+' de '+patientTag} data-patient-id={activeAppointment.patientId} data-secondary-expanded={additionalOpen}>
         <Card title="Informations patient" hidden={!containsTab('Vue d’ensemble','Dossier')}><dl className="cmd-patientfields">{[['Référence',activeAppointment.patientId],['Âge','Fictif'],['Téléphone','Aucun numéro réel'],['Email',activeAppointment.patientId.toLowerCase()+'@example.invalid'],['Praticien','Dr '+['A','B','C'][activeAppointment.practitionerId]+' (fictif)'],['Couverture','Fictive'],['Antécédents','Non renseignés']].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl></Card>
         <Card title="Odontogramme officiel" hidden={!containsTab('Vue d’ensemble','Odontogramme')} action={<small>Référence adulte v3</small>}><div className="cmd-odonto"><PremiumOdontogramSVG type="ADULT" readOnly selectedTooth={null} multiSelectedTeeth={[]} showNumbers/></div><p className="cmd-small">Schéma officiel, affiché pour {patientTag} : aucune donnée dentaire clinique.</p></Card>
         <Card title="Imagerie" hidden={!containsTab('Vue d’ensemble','Imagerie')} action={<button className="cmd-link" onClick={()=>announce('Galerie')}>Galerie</button>}><div className="cmd-image-tabs">{patientTag} · RVG　 ·　 Panoramique　 ·　 Céphalométrie</div><div className="cmd-imagegrid">{['RVG 14','RVG 16','Panoramique','Céphalométrie'].map(x=><button onClick={()=>announce(x)} key={x}><FileImage size={25}/><strong>{x}</strong><small>Aucun média pour {activeAppointment.patientId}</small></button>)}</div></Card>
         <Card title="Plan de traitement" hidden={!containsTab('Vue d’ensemble','Plan de traitement')}>{activeAppointment.patientId==='TEST-001'?<div className="cmd-treatments">{[['Soins conservateurs 14','À réaliser','warning'],['Couronne céramo-céramique 16','Validé','success'],['Détartrage / surfaçage','À planifier','info'],['Suivi parodontal','Proposé','warning']].map(([label,state,tone],i)=><div key={i}><b className="cmd-numeric">{i+1}</b><strong>{label}</strong><Pill tone={tone as Tone}>{state}</Pill></div>)}</div>:<p className="cmd-empty-state">Aucun plan de traitement fictif pour {patientTag}. Aucune donnée clinique.</p>}</Card>
         <Card title="Notes cliniques" hidden={!containsTab('Vue d’ensemble','Dossier')}><div className="cmd-editorbar">Paragraphe　　<strong>B</strong>　　<i>I</i>　 ☰</div><p className="cmd-notes">Aucune note pour {activeAppointment.patientId}. Aucune écriture ni diagnostic.</p></Card>
         <Card title="Alertes & informations" hidden={!containsTab('Vue d’ensemble','Dossier')}><div className="cmd-alerts"><p><ShieldCheck size={15}/> Identité fictive – prototype</p><p><ClipboardList size={15}/> Consentement : non démontré</p><p><Clock3 size={15}/> Prochain contrôle : exemple</p></div></Card>
         <Card title="File d’attente" hidden={!containsTab('Vue d’ensemble')}><div className="cmd-bottomrows">{appointments.filter(a=>a.practitionerId===activeAppointment.practitionerId&&a.startMinutes>activeAppointment.startMinutes&&a.arrival==='arrived'&&(mockStatuses[a.id]??a.status)==='waiting').sort((a,b)=>a.startMinutes-b.startMinutes).slice(0,2).map(a=><button className="cmd-queue-button" key={a.id} onClick={()=>requestSwitch(a.id)}>{a.startLabel} · <strong>Patient {a.patientId}</strong> · RDV {a.ref} · {a.label} · {a.duration} min</button>)}</div></Card>
         <Card title="Documents & consentements" hidden={!containsTab('Vue d’ensemble','Documents')}><div className="cmd-bottomrows"><p><FileText size={14}/> Aucun document pour {patientTag} (prototype)</p></div></Card>
         <Card title="Paiement & facturation" hidden={!containsTab('Vue d’ensemble','Facturation')}><div className="cmd-bottomrows"><p><CreditCard size={14}/> Aucune transaction pour {patientTag}</p><p>Simulation sans paiement ni facturation</p></div></Card>
        </div>
        {tab==='Vue d’ensemble'&&<button type="button" className="cmd-secondary-toggle" aria-expanded={additionalOpen} aria-controls="cmd-cards" onClick={()=>setAdditionalOpen(v=>!v)}>{additionalOpen?'Masquer les 4 panneaux complémentaires':'Afficher les 4 panneaux complémentaires'} <ChevronDown size={16} aria-hidden="true" className={additionalOpen?'cmd-rotate':''}/></button>}
       </div>
     </div>}
    <footer className="cmd-disclaimer">LOT07 / 07-C · TARGET REACT ISOLÉ · Actifs Digital Crown d’origine · Tokens existants · Aucune connexion Cabinet</footer>
   </div>
  </main>
 </div>;
}
const mount=document.getElementById('root');
if (!mount) throw new Error('Missing isolated React target mount');
createRoot(mount).render(<CommandWorkbenchReactTarget/>);
