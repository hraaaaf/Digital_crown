/** LOT07/07-C: purely presentational helpers for synthetic Command fixtures. */
import React from 'react';
import type { SyntheticAppointment } from './command-synthetic-fixtures';

export function AppointmentIdentity({appointment}: {appointment:SyntheticAppointment}) {
 return <><strong>Patient {appointment.patientId}</strong><span><small>RDV {appointment.ref}</small> · {appointment.label} · {appointment.duration} min</span></>;
}
export type RoomDisplay = {state:'seated'|'planned-occupied'|'planned-free'; eyebrow:string; description:string};
export function getRoomDisplay(appointment:SyntheticAppointment,roomAssignments:Record<number,string|null>):RoomDisplay {
 const occupant=roomAssignments[appointment.room];
 if(occupant===appointment.id) return {state:'seated',eyebrow:'AU FAUTEUIL · SALLE '+appointment.room,description:'Installé en salle '+appointment.room};
 if(occupant) return {state:'planned-occupied',eyebrow:'SALLE '+appointment.room+' PRÉVUE · OCCUPÉE',description:'Salle '+appointment.room+' prévue, occupée par un autre rendez-vous fictif'};
 return {state:'planned-free',eyebrow:'SALLE '+appointment.room+' PRÉVUE · LIBRE',description:'Salle '+appointment.room+' prévue, patient non installé'};
}
