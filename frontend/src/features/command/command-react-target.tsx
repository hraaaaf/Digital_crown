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
 const announce=(what:string)=>setNotification(what+' : simulation uniquement, aucune opération clinique.');
 return <div className="cmd-shell" data-command-target="07-C-react-isolated" data-synthetic-fixtures="true">
  <aside className="cmd-sidebar">
    <div className="cmd-brand"><img className="cmd-logo-full" src={OfficialLogo} alt="Digital Crown"/><img className="cmd-logo-mini" src={CompactLogo} alt="" /><small>COMMAND · 07-C</small></div>
    <div className="cmd-navtitle">ESPACE CABINET</div>
    <nav aria-label="Navigation de démonstration" className="cmd-navigation">{menu.map(({name,icon:Icon})=><button type="button" key={name} aria-current={view===name?'page':undefined} className={view===name?'cmd-selected':''} onClick={()=>{setView(name);setNotification('');}}><Icon size={17} aria-hidden="true"/><span>{name}</span></button>)}</nav>
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
        <div className="cmd-agenda-overflow"><div className="cmd-calendar">
         <div className="cmd-timehead">Heure</div>{['Dr A · Salle 1','Dr B · Salle 2','Dr C · Salle 3'].map((s,i)=><div className="cmd-lanehead" key={s}><b>{['DA','DB','DC'][i]}</b><span>{s}<small>{i===2?'Chirurgie':'Omnipratique'}</small></span></div>)}
         {slots.map((row,index)=><React.Fragment key={index}><div className="cmd-hour">{String(index+8).padStart(2,'0')}:00</div>{row.map((entry,j)=><div className="cmd-cell" key={j}>{entry&&<button type="button" onClick={()=>announce(entry[0])} className={'cmd-appt cmd-appt-'+entry[2]}><strong>{entry[0]}</strong><span>{entry[1]}</span></button>}</div>)}</React.Fragment>)}
        </div></div>
        <div className="cmd-legend">● Réalisé　● En attente　● À venir　● Urgence</div>
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
