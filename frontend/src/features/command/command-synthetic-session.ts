/** LOT07/07-C — deterministic fixture-only appointment state transitions.
 * This reducer never calls Cabinet APIs or persists medical data.
 */
import {useReducer} from 'react';
import {appointments,initialRoomAssignments,nextArrivedForPractitioner,occupiedRoomCount,type AppointmentStatus} from './command-synthetic-fixtures';

export type SyntheticSessionState = {
 activeAppointmentId:string;
 pendingAppointmentId:string|null;
 roomAssignments:Record<number,string|null>;
 mockStatuses:Record<string,AppointmentStatus>;
};
export type SyntheticSessionAction =
 |{type:'request-switch';appointmentId:string}
 |{type:'cancel-switch'}
 |{type:'confirm-switch'}
 |{type:'transition';to:'current'|'paused'|'finished'};

export const initialSyntheticSession:Readonly<SyntheticSessionState> = {
 activeAppointmentId:'APT-TEST-001',pendingAppointmentId:null,
 roomAssignments:{...initialRoomAssignments},mockStatuses:{}
};

export function syntheticSessionReducer(state:SyntheticSessionState,action:SyntheticSessionAction):SyntheticSessionState {
 const active=appointments.find(x=>x.id===state.activeAppointmentId);
 if(!active)return state;
 switch(action.type){
  case 'request-switch': {
   const target=appointments.find(x=>x.id===action.appointmentId);
   if(!target||target.id===active.id||state.pendingAppointmentId)return state;
   return {...state,pendingAppointmentId:target.id};
  }
  case 'cancel-switch':return state.pendingAppointmentId?{...state,pendingAppointmentId:null}:state;
  case 'confirm-switch': {
   const target=appointments.find(x=>x.id===state.pendingAppointmentId);
   if(!target||target.id===active.id)return {...state,pendingAppointmentId:null};
   return {...state,activeAppointmentId:target.id,pendingAppointmentId:null};
  }
  case 'transition': {
   if(state.pendingAppointmentId)return state;
   const current=state.mockStatuses[active.id]??active.status;
   const occupant=state.roomAssignments[active.room];
   const permitted =
    (current==='current'&&(action.to==='paused'||action.to==='finished')&&occupant===active.id)||
    (current==='paused'&&(action.to==='current'||action.to==='finished')&&occupant===active.id)||
    (current==='waiting'&&action.to==='current'&&active.arrival==='arrived'&&!occupant);
   if(!permitted)return state;
   const nextRooms=action.to==='finished'
    ?Object.fromEntries(Object.entries(state.roomAssignments).map(([room,id])=>[room,id===active.id?null:id]))
    :current==='waiting'&&action.to==='current'
     ?{...state.roomAssignments,[active.room]:active.id}
     :state.roomAssignments;
   return {...state,roomAssignments:nextRooms,mockStatuses:{...state.mockStatuses,[active.id]:action.to}};
  }
 }
}
export function useSyntheticSession(){
 const [state,dispatch]=useReducer(syntheticSessionReducer,initialSyntheticSession);
 const activeAppointment=appointments.find(a=>a.id===state.activeAppointmentId)??appointments[0];
 const currentStatus=state.mockStatuses[activeAppointment.id]??activeAppointment.status;
 const samePractitionerNext=nextArrivedForPractitioner(activeAppointment,state.mockStatuses);
 const inChair=occupiedRoomCount(state.roomAssignments);
 const inWaiting=appointments.filter(a=>a.arrival==='arrived'&&(state.mockStatuses[a.id]??a.status)==='waiting').length;
 const freeRooms=Object.keys(state.roomAssignments).length-inChair;
 const plannedSwitch=appointments.find(a=>a.id===state.pendingAppointmentId);
 const canBeginConsultation=currentStatus==='waiting'&&activeAppointment.arrival==='arrived'&&!state.roomAssignments[activeAppointment.room];
 return {state,dispatch,activeAppointment,currentStatus,samePractitionerNext,inChair,inWaiting,freeRooms,plannedSwitch,canBeginConsultation};
}
