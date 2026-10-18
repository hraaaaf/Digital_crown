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

type Tone = 'success'|'warning'|'danger'|'info';
const menu: {name: string; icon: LucideIcon}[] = [
  {name:'Command',icon:LayoutDashboard},{name:'Agenda',icon:CalendarDays},
  {name:'Patients',icon:Users},{name:'Dossier clinique',icon:FolderOpen},
  {name:'Imagerie',icon:ImageIcon},{name:'Cabinet',icon:Activity},
  {name:'Facturation',icon:Receipt},{name:'Documents',icon:FileText},
  {name:'Rapports',icon:ClipboardList}
];
const slots = [
  [['TEST-002','Contrôle','done'],['TEST-003','Détartrage','done'],['TEST-004','Bilan','planned']],
  [['TEST-001','Soins conservateurs','current'],['TEST-005','Consultation','waiting'],['TEST-006','Chirurgie','planned']],
  [['TEST-007','Suivi','waiting'],['TEST-008','Prothèse','planned'],['TEST-009','Contrôle','done']],
  [['TEST-URG','Créneau réservé','urgent'],['TEST-010','Contrôle','waiting'],['TEST-011','Parodontologie','planned']],
  [null,null,null],
  [['TEST-012','Consultation','planned'],['TEST-013','Soins','planned'],['TEST-014','Consultation','planned']],
  [['TEST-015','Couronne','planned'],['TEST-016','Implantologie','planned'],['TEST-017','Contrôle','planned']],
  [null,null,null],
  [['TEST-018','Consultation','planned'],['TEST-019','Chirurgie','planned'],['TEST-020','Suivi','planned']],
] as const;
/** All schedule data remain synthetic and read-only. Slots are quarter-hour cells. */
const slotMinutes: (readonly number[])[] = [
 [30,30,45],[45,30,60],[30,60,30],[60,30,45],
 [0,0,0],[30,45,30],[60,60,30],[0,0,0],[30,60,30]
];
const quarterHours = Array.from({length:36},(_,index)=>{
 const hour=8+Math.floor(index/4), minute=(index%4)*15;
 return {label:`${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}`,minute};
});
function Pill({children,tone='info'}:{children:React.ReactNode;tone?:Tone}) {
 return <span className={'cmd-pill cmd-pill-'+tone}>{children}</span>;
}
function Card({title,action,children,className=''}:{title:string;action?:React.ReactNode;children:React.ReactNode;className?:string}) {
 return <section className={'cmd-card '+className}><header className="cmd-cardhead"><h3>{title}</h3>{action}</header>{children}</section>;
}
export function CommandWorkbenchReactTarget(){
 const [view,setView]=useState('Command');
 const [tab,setTab]=useState('Vue d’ensemble');
 const [notification,setNotification]=useState('');
 const [mode,setMode]=useState('Jour');
 const [activeLane,setActiveLane]=useState(0);
 const announce=(what:string)=>setNotification(what+' : simulation uniquement, aucune opération clinique.');
 return <div className="cmd-shell" data-command-target="07-C-react-isolated" data-synthetic-fixtures="true">
  <aside className="cmd-sidebar">
    <div className="cmd-brand"><img className="cmd-logo-full" src={OfficialLogo} alt="Digital Crown"/><img className="cmd-logo-mini" src={CompactLogo} alt="Digital Crown — logo compact" /><small>COMMAND · 07-C</small></div>
    <div className="cmd-navtitle">ESPACE CABINET</div>
    <nav aria-label="Navigation de démonstration" className="cmd-navigation">{menu.map(({name,icon:Icon})=><button type="button" key={name} aria-current={view===name?'page':undefined} aria-label={name} className={view===name?'cmd-selected':''} onClick={()=>{setView(name);setNotification('');}}><Icon size={17} aria-hidden="true"/><span>{name}</span></button>)}</nav>
    <div className="cmd-sidebarfooter"><Settings size={16}/> Maquette sans backend<br/><small>Données TEST uniquement</small></div>
  </aside>
  <main className="cmd-main">
   <header className="cmd-toolbar">
    <span className="cmd-search"><Search size={16}/> Rechercher un patient, un rendez-vous, un document...</span>
    <span className="cmd-topright"><small>Thème hérité du Cabinet</small><Bell size={16}/><span className="cmd-avatar">DC</span></span>
   </header>
   <div className="cmd-content">
    <div className="cmd-heading"><div><h1>{view} <Pill>CIBLE 07-C</Pill></h1><p>Vue multi-praticien · Patient TEST-001 · Données 100 % synthétiques</p></div><div className="cmd-chips"><Pill tone="success">3 en salle</Pill><Pill tone="warning">2 en attente</Pill><Pill>2 salles libres</Pill></div></div>
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
         {slots.flatMap((row,hourIndex)=>row.map((entry,lane)=>entry ? <button key={entry[0]} type="button" data-lane={lane} data-current-lane={activeLane===lane} onClick={()=>announce(entry[0])} style={{gridRow:`${hourIndex*4+2} / span ${Math.max(1,slotMinutes[hourIndex][lane]/15)}`,gridColumn:lane+2}} className={'cmd-appt cmd-appt-'+entry[2]} aria-label={entry[0]+' '+entry[1]+' '+slotMinutes[hourIndex][lane]+' minutes, démonstration'}><strong>{entry[0]}</strong><span>{entry[1]} · {slotMinutes[hourIndex][lane]} min</span></button> : null))}
        </div></div>
        <div className="cmd-legend"><span>● Réalisé</span><span>● En attente</span><span>● À venir</span><span>● Urgence</span></div>
       </Card>
       <div className="cmd-right">
        <div className="cmd-patienthero"><div className="cmd-patientavatar">T1</div><div className="cmd-patientintro"><h2>Patient TEST-001 <Pill tone="success">En cours</Pill></h2><p>Identité fictive · 36 ans · Praticien A · Salle 1</p><span><Pill>Accès non testé</Pill> <Pill>Données synthétiques</Pill></span></div><div className="cmd-contact"><button aria-label="Téléphone démonstration" onClick={()=>announce('Téléphone')}><Phone size={15}/></button><button aria-label="Mail démonstration" onClick={()=>announce('E-mail')}><Mail size={15}/></button><button aria-label="Plus démonstration" onClick={()=>announce('Menu')}><MoreHorizontal size={15}/></button></div><div className="cmd-patienttime"><strong>09:00 – 09:45</strong><small>Soins conservateurs</small><span><Clock3 size={12}/> Consultation fictive</span></div><div className="cmd-patientbuttons"><button className="cmd-primary" onClick={()=>announce('Pause')}>Mettre en pause</button><button onClick={()=>announce('Terminer RDV')}>Terminer le RDV</button></div></div>
        <div className="cmd-tabs" role="tablist" aria-label="Dossier fictif">{['Vue d’ensemble','Dossier','Plan de traitement','Odontogramme','Imagerie','Documents','Facturation'].map(t=><button role="tab" aria-selected={tab===t} className={tab===t?'active':''} key={t} onClick={()=>{setTab(t);if(t!=='Vue d’ensemble')announce('Onglet '+t)}}>{t}</button>)}</div>
        <div className="cmd-cards">
         <Card title="Informations patient"><dl className="cmd-patientfields">{[['Référence','TEST-001'],['Âge','36 ans'],['Téléphone','00 00 00 00'],['Email','test001@example.invalid'],['Praticien','Dr A (fictif)'],['Couverture','Fictive'],['Antécédents','Non renseignés']].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl></Card>
         <Card title="Odontogramme officiel" action={<small>Référence adulte v3</small>}><div className="cmd-odonto"><PremiumOdontogramSVG type="ADULT" readOnly selectedTooth={null} multiSelectedTeeth={[]} showNumbers/></div><p className="cmd-small">Schéma source, aucune dent pathologique simulée.</p></Card>
         <Card title="Imagerie" action={<button className="cmd-link" onClick={()=>announce('Galerie')}>Galerie</button>}><div className="cmd-image-tabs">RVG　 ·　 Panoramique　 ·　 Céphalométrie</div><div className="cmd-imagegrid">{['RVG 14','RVG 16','Panoramique','Céphalométrie'].map(x=><button onClick={()=>announce(x)} key={x}><FileImage size={25}/><strong>{x}</strong><small>Aucun média patient</small></button>)}</div></Card>
         <Card title="Plan de traitement"><div className="cmd-treatments">{[['Soins conservateurs 14','À réaliser','warning'],['Couronne céramo-céramique 16','Validé','success'],['Détartrage / surfaçage','À planifier','info'],['Suivi parodontal','Proposé','warning']].map(([label,state,tone],i)=><div key={i}><b className="cmd-numeric">{i+1}</b><strong>{label}</strong><Pill tone={tone as Tone}>{state}</Pill></div>)}</div></Card>
         <Card title="Notes cliniques"><div className="cmd-editorbar">Paragraphe　　<strong>B</strong>　　<i>I</i>　 ☰</div><p className="cmd-notes">Aucune note réelle. Aucune écriture ni diagnostic.</p></Card>
         <Card title="Alertes & informations"><div className="cmd-alerts"><p><ShieldCheck size={15}/> Identité fictive – prototype</p><p><ClipboardList size={15}/> Consentement : non démontré</p><p><Clock3 size={15}/> Prochain contrôle : exemple</p></div></Card>
         <Card title="File d’attente"><div className="cmd-bottomrows"><p>09:45　 <strong>TEST-005</strong>　 Contrôle　15 min</p><p>10:00　 <strong>TEST-007</strong>　 Suivi　30 min</p></div></Card>
         <Card title="Documents & consentements"><div className="cmd-bottomrows"><p><FileText size={14}/> Consentement TEST</p><p><FileText size={14}/> Devis fictif</p></div></Card>
         <Card title="Paiement & facturation"><div className="cmd-bottomrows"><p><CreditCard size={14}/> Devis fictif　850 DH</p><p>Aucune opération de paiement</p></div></Card>
        </div>
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
