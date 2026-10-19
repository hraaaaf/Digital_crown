/** Synthetic Command day agenda: presentation only; no Cabinet routes or writes. */
import React from 'react';
import { CalendarDays, ChevronDown, Plus } from 'lucide-react';
import { appointments, quarterHours, type AppointmentStatus } from './command-synthetic-fixtures';
import { AppointmentIdentity } from './command-appointment-presentation';

export type CommandAgendaProps={
 activeLane:number;
 setActiveLane:(lane:number)=>void;
 mockStatuses:Readonly<Record<string,AppointmentStatus>>;
 requestSwitch:(appointmentId:string)=>void;
 announce:(action:string)=>void;
};

export function CommandAgenda({activeLane,setActiveLane,mockStatuses,requestSwitch,announce}:CommandAgendaProps){
 return <section id="cmd-agenda" tabIndex={-1} className="cmd-card cmd-agenda" aria-labelledby="cmd-agenda-title">
  <header className="cmd-cardhead"><h3 id="cmd-agenda-title">Agenda · Vue journalière</h3><small>15 min · 3 praticiens</small></header>
        <div className="cmd-datebar"><button onClick={()=>announce('Calendrier')}><CalendarDays size={15}/> Lundi 19 octobre 2026 <ChevronDown size={13}/></button><button onClick={()=>announce('Aujourd’hui')}>Aujourd’hui</button><button className="cmd-primary" onClick={()=>announce('RDV')}><Plus size={15}/> RDV</button></div>
        <div className="cmd-agenda-modes" role="group" aria-label="Modes de l’agenda fictif"><button type="button" className="active" aria-pressed="true" aria-label="Jour — vue disponible">Jour</button>{['Semaine','Liste'].map(x=><button type="button" key={x} disabled aria-disabled="true" aria-label={x+' — en construction'} aria-pressed="false">{x}<small>En construction</small></button>)}</div>
        <div className="cmd-mobile-lanes" role="group" aria-label="Praticien affiché dans l’agenda mobile">{['Dr A','Dr B','Dr C'].map((name,index)=><button key={name} type="button" aria-label={'Agenda '+name} aria-pressed={activeLane===index} onClick={()=>setActiveLane(index)}>{name}</button>)}</div>
        <div className="cmd-agenda-overflow"><div className="cmd-calendar" data-quarter-hour-grid="true" data-active-lane={activeLane}>
         <div className="cmd-timehead" style={{gridRow:1,gridColumn:1}}>Heure</div>
         {['Dr A · Salle 1','Dr B · Salle 2','Dr C · Salle 3'].map((name,lane)=><div className="cmd-lanehead" key={name} data-lane={lane} data-current-lane={activeLane===lane} style={{gridRow:1,gridColumn:lane+2}}><b>{['DA','DB','DC'][lane]}</b><span>{name}<small>{lane===2?'Chirurgie':'Omnipratique'}</small></span></div>)}
         {quarterHours.map(({label,minute},tick)=><React.Fragment key={label}><div className="cmd-hour" data-minute={minute} style={{gridRow:tick+2,gridColumn:1}}>{label}</div>{[0,1,2].map(lane=><div key={lane} className={'cmd-quarter-cell '+(minute===0?'cmd-quarter-start':'')} data-lane={lane} data-current-lane={activeLane===lane} style={{gridRow:tick+2,gridColumn:lane+2}} aria-hidden="true"/>)}</React.Fragment>)}
         {appointments.map(appt=><button key={appt.id} type="button" data-lane={appt.practitionerId} data-current-lane={activeLane===appt.practitionerId} data-appointment-id={appt.id} data-patient-id={appt.patientId} onClick={()=>requestSwitch(appt.id)} style={{gridRow:`${(appt.startMinutes-480)/15+2} / span ${Math.max(1,appt.duration/15)}`,gridColumn:appt.practitionerId+2}} className={'cmd-appt cmd-appt-'+(mockStatuses[appt.id]??appt.status)} aria-label={'Patient '+appt.patientId+', rendez-vous '+appt.ref+', '+appt.label+', '+appt.duration+' minutes, démonstration'}><AppointmentIdentity appointment={appt}/></button>)}
        </div></div>
        <div className="cmd-legend"><span>● Réalisé</span><span>● En attente</span><span>● À venir</span><span>● Urgence</span></div>
 </section>;
}
