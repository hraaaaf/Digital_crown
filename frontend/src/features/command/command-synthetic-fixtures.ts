/** LOT07 / 07-C — synthetic-only scheduling model. No Cabinet API or patient data. */
export type AppointmentStatus = 'done' | 'planned' | 'waiting' | 'current' | 'urgent' | 'paused' | 'finished';
export type ArrivalStatus = 'arrived' | 'not-arrived' | 'unknown';
export type SyntheticAppointment = {
 id:string; ref:string; patientId:string; label:string; status:AppointmentStatus; arrival:ArrivalStatus;
 practitionerId:number; room:number; startMinutes:number; startLabel:string; endLabel:string; duration:number;
};
export const slots = [
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
export const slotMinutes:readonly (readonly number[])[] = [
 [30,30,45],[45,30,60],[30,60,30],[60,30,45],
 [0,0,0],[30,45,30],[60,60,30],[0,0,0],[30,60,30]
];
export const quarterHours=Array.from({length:36},(_,index)=>{
 const hour=8+Math.floor(index/4),minute=(index%4)*15;
 return {label:`${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}`,minute};
});
const asClock=(minutes:number)=>String(Math.floor(minutes/60)).padStart(2,'0')+':'+String(minutes%60).padStart(2,'0');
// TEST-001 intentionally has two distinct appointments (APT-TEST-001 and APT-TEST-018).
const patientsByAppointment:Record<string,string>={'TEST-018':'TEST-001'};
export const appointments:SyntheticAppointment[]=slots.flatMap((row,hourIndex)=>row.flatMap((entry,practitionerId)=>{
 if(!entry)return [];
 const ref=entry[0],startMinutes=(hourIndex+8)*60,duration=slotMinutes[hourIndex][practitionerId];
 const status=entry[2] as AppointmentStatus;
 return [{
  id:'APT-'+ref,ref,patientId:patientsByAppointment[ref]||ref,label:entry[1],
  status,arrival:status==='waiting'||status==='current'||status==='done'?'arrived':status==='planned'?'not-arrived':'unknown',
  practitionerId,room:practitionerId+1,startMinutes,startLabel:asClock(startMinutes),endLabel:asClock(startMinutes+duration),duration,
 }];
}));
export const initialRoomAssignments:Record<number,string|null>={1:'APT-TEST-001',2:null,3:null};
export function isEligibleNext(a:SyntheticAppointment,current:SyntheticAppointment,status:AppointmentStatus){
 return a.id!==current.id&&a.practitionerId===current.practitionerId&&a.startMinutes>current.startMinutes
 &&a.arrival==='arrived'&&status==='waiting';
}
export function nextArrivedForPractitioner(current:SyntheticAppointment,statuses:Record<string,AppointmentStatus>){
 return appointments.filter(a=>isEligibleNext(a,current,statuses[a.id]??a.status)).sort((a,b)=>a.startMinutes-b.startMinutes)[0];
}
export function occupiedRoomCount(rooms:Record<number,string|null>){
 return Object.values(rooms).filter(Boolean).length;
}
