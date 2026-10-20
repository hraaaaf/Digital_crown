/** LOT07/07-C — patient-bound presentation, synthetic fixture context only. */
import React from 'react';
import { Phone, Mail, MoreHorizontal, Clock3, FileImage, ShieldCheck, ClipboardList, FileText, CreditCard, ChevronDown } from 'lucide-react';
import { PremiumOdontogramSVG } from '../../components/odontogram/PremiumOdontogramSVG';
import { appointments, type SyntheticAppointment, type AppointmentStatus } from './command-synthetic-fixtures';
import type { RoomDisplay } from './command-appointment-presentation';
import { Card, Pill, type Tone } from './command-ui-primitives';

const patientTabs=['Vue d’ensemble','Dossier','Plan de traitement','Odontogramme','Imagerie','Documents','Facturation'] as const;

export type CommandPatientWorkspaceProps={
 activeAppointment:SyntheticAppointment;
 currentStatus:AppointmentStatus;
 roomDisplay:RoomDisplay;
 patientHeadingRef:React.RefObject<HTMLHeadingElement|null>;
 tab:string;
 setTab:React.Dispatch<React.SetStateAction<string>>;
 additionalOpen:boolean;
 setAdditionalOpen:React.Dispatch<React.SetStateAction<boolean>>;
 mockStatuses:Readonly<Record<string,AppointmentStatus>>;
 samePractitionerNext:SyntheticAppointment|undefined;
 canBeginConsultation:boolean;
 requestSwitch:(id:string)=>void;
 updateMockStatus:(next:AppointmentStatus)=>void;
 announce:(message:string)=>void;
 clearNotification:()=>void;
};
export function CommandPatientWorkspace({activeAppointment,currentStatus,roomDisplay,patientHeadingRef,tab,setTab,additionalOpen,setAdditionalOpen,mockStatuses,samePractitionerNext,canBeginConsultation,requestSwitch,updateMockStatus,announce,clearNotification}:CommandPatientWorkspaceProps){
 const patientTag='Patient '+activeAppointment.patientId;
 const containsTab=(...names:string[])=>names.includes(tab);
 return (
<div className="cmd-right" key={activeAppointment.patientId} data-patient-id={activeAppointment.patientId}>
        <div className="cmd-patienthero"><div className="cmd-patientavatar">T</div><div className="cmd-patientintro"><p className="cmd-patienteyebrow" data-room-state={roomDisplay.state}>DOSSIER ACTIF <span aria-hidden="true">·</span> {roomDisplay.eyebrow}</p><h2 tabIndex={-1} ref={patientHeadingRef}>{patientTag} <Pill tone={currentStatus==='current'?'success':currentStatus==='paused'?'warning':'info'}>{currentStatus==='current'?'En cours':currentStatus==='paused'?'En pause':currentStatus==='finished'?'Terminé':currentStatus==='waiting'?'En attente':'RDV fictif'}</Pill></h2><p>Identité fictive · Dr {['A','B','C'][activeAppointment.practitionerId]} · {roomDisplay.description}</p><span><Pill>Accès non testé</Pill> <Pill>Données synthétiques</Pill></span></div><div className="cmd-contact"><button aria-label="Téléphone démonstration" onClick={()=>announce('Téléphone')}><Phone size={15}/></button><button aria-label="Mail démonstration" onClick={()=>announce('E-mail')}><Mail size={15}/></button><button aria-label="Plus démonstration" onClick={()=>announce('Menu')}><MoreHorizontal size={15}/></button></div><div className="cmd-patienttime"><strong>{activeAppointment.startLabel} – {activeAppointment.endLabel}</strong><small>RDV {activeAppointment.ref} · {activeAppointment.label}</small><span><Clock3 size={12}/> {activeAppointment.duration} min fictives</span></div><div className="cmd-patientbuttons"><button className="cmd-primary" disabled={currentStatus!=='current'&&currentStatus!=='paused'} onClick={()=>updateMockStatus(currentStatus==='paused'?'current':'paused')}>{currentStatus==='paused'?'Reprendre (simulation)':'Mettre en pause'}</button><button disabled={currentStatus!=='current'&&currentStatus!=='paused'} onClick={()=>updateMockStatus('finished')}>Terminer le RDV (simulation)</button><button disabled={!samePractitionerNext} onClick={()=>samePractitionerNext&&requestSwitch(samePractitionerNext.id)}>Patient suivant (même praticien)</button>{canBeginConsultation&&<button onClick={()=>updateMockStatus('current')}>Démarrer la consultation (simulation)</button>}</div></div>
        <div className="cmd-tabs" role="tablist" aria-label="Dossier fictif">{patientTabs.map((t,index)=><button role="tab" key={t} id={'cmd-tab-'+index} aria-controls="cmd-cards" aria-selected={tab===t} tabIndex={tab===t?0:-1} className={tab===t?'active':''} onClick={()=>{setTab(t);clearNotification();}} onKeyDown={e=>{if(['ArrowRight','ArrowLeft','Home','End'].includes(e.key)){e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?patientTabs.length-1:(index+(e.key==='ArrowRight'?1:patientTabs.length-1))%patientTabs.length;setTab(patientTabs[next]);const tabs=e.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]');tabs?.[next]?.focus();}}}>{t}</button>)}</div>
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
 );
}
