// LOT07 07-A Agenda Integrity — real disposable T2 authenticated POST/PUT/GET.
// No remote services, clinic data, patient identifiers or real patient names.
import { request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

if(process.env.ENVIRONMENT!=='test' || process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1' ||
   process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db' ||
   !/^[0-9a-f]{40}$/.test(process.env.SOURCE_HEAD||''))
  throw Error('Refusing non-disposable Agenda Integrity validation');

const client = await request.newContext({baseURL:'http://127.0.0.1:8005'});
const authResponse=await client.post('/api/auth/login',{form:{username:process.env.T2_USER,password:process.env.T2_PASSWORD}});
if(!authResponse.ok())throw Error('T2 authentication failed '+authResponse.status());
const tokens=await authResponse.json();
const headers={Authorization:'Bearer '+tokens.access_token};
const date='2026-10-19';
const hour1=date+'T09:30:00',hour2=date+'T10:30:00';
const payload=(dt)=>({
  patient_id:null,patient_name:'T2 FICTITIOUS AGENDA',motif:'T2 integrity audit',
  datetime_start:dt,duration_minutes:30,status:'PRÉVU',scheduling_type:'EXACT_TIME'
});
const ensure=(condition,message)=>{if(!condition)throw Error(message);};
async function getConflict(datetime_start,extra={}){
 const r=await client.get('/api/appointments/check-conflicts',{headers,params:{datetime_start,duration_minutes:30,...extra}});
 return r;
}
const check=await getConflict(hour1);
ensure(check.status()===200,'Preflight wall clock check failed '+check.status());
ensure((await check.json()).has_conflict===false,'Unexpected T2 preflight conflict');
const create=await client.post('/api/appointments/',{headers,data:payload(hour1)});
ensure(create.status()===200,'Real T2 appointment POST failed '+create.status());
const record=await create.json();
ensure(Number.isSafeInteger(record.id)&&record.datetime_start===hour1,
 'POST roundtrip changed cabinet wall clock '+record.datetime_start);
const occupied=await getConflict(hour1);
ensure(occupied.status()===200 && (await occupied.json()).has_conflict===true,
 'Actual T2 conflict not detected');
const duplicate=await client.post('/api/appointments/',{headers,data:payload(hour1)});
ensure(duplicate.status()===409,'Duplicate T2 appointment was not rejected '+duplicate.status());
const move=await client.put('/api/appointments/'+record.id,{headers,data:{
  datetime_start:hour2, duration_minutes:30
}});
ensure(move.status()===200,'Real T2 appointment PUT failed '+move.status());
ensure((await move.json()).datetime_start===hour2,'PUT changed cabinet wall clock');
const list=await client.get('/api/appointments/',{headers});
ensure(list.status()===200,'Authenticated roundtrip GET failed '+list.status());
const rows=await list.json();
const current=rows.find(row=>row.id===record.id);
ensure(current?.datetime_start===hour2,'Persisted T2 wall clock not preserved');
const previous=await getConflict(hour1);
ensure(previous.status()===200&&(await previous.json()).has_conflict===false,
 'Old slot remained occupied after update');
const movedConflict=await getConflict(hour2,{exclude_id:record.id});
ensure(movedConflict.status()===200&&(await movedConflict.json()).has_conflict===false,
 'Self-exclusion incorrectly marked edited slot as conflicting');
// The T2 workstation bootstrap injects authenticated storageState into client.
// Negative auth must run in a distinct cookie-free context; otherwise the valid
// session cookie can legitimately authenticate despite an invalid Bearer value.
const clean=await request.newContext({baseURL:'http://127.0.0.1:8005',storageState:{cookies:[],origins:[]}});
const invalidAuth=await clean.get('/api/appointments/',{headers:{Authorization:'Bearer invalid-token'}});
ensure([401,403].includes(invalidAuth.status()),'Expired/invalid session accepted '+invalidAuth.status());
const forbiddenPatient=await client.post('/api/appointments/',{headers,data:{
  ...payload(date+'T12:00:00'),patient_id:999999
}});
ensure([403,404].includes(forbiddenPatient.status()),
 'Missing/unrelated patient relation unexpectedly permitted '+forbiddenPatient.status());
const restricted=await clean.post('/api/auth/login',{form:{
 username:'t2-restricted@cabinet.ma',password:process.env.T2_PASSWORD
}});
ensure(restricted.status()===200,'Restricted T2 auth fixture failed');
const rt=(await restricted.json()).access_token;
const restrictedWrite=await clean.post('/api/appointments/',{headers:{Authorization:'Bearer '+rt},
 data:{...payload(date+'T11:30:00'),patient_id:999999}});
// Some restricted staff sessions are denied earlier by workstation/clinic
// policy (423). That is a genuine rejection, NOT proof of patient RBAC alone.
ensure([401,403,404,423].includes(restrictedWrite.status()),
 'Restricted staff request unexpectedly permitted '+restrictedWrite.status());
const other=await clean.post('/api/auth/login',{form:{
 username:'t2-setup-390@cabinet.ma',password:process.env.T2_PASSWORD
}});
ensure(other.status()===200,'Other-tenant T2 auth fixture failed');
const otherToken=(await other.json()).access_token;
const otherStorage=await enrollT2Workstation(clean,otherToken,process.env.T2_PASSWORD);
const otherClient=await request.newContext({baseURL:'http://127.0.0.1:8005',storageState:otherStorage});
const otherList=await otherClient.get('/api/appointments/',{headers:{Authorization:'Bearer '+otherToken}});
ensure(otherList.status()===200&&!((await otherList.json()).some(row=>row.id===record.id)),
 'Cross-tenant appointment became readable or other-tenant session invalid '+otherList.status());
// F03: backend directory/resource contract is authoritative and tenant-scoped.
const directory=await client.get('/api/appointments/assignable-practitioners',{headers});
ensure(directory.status()===200,'Assignable practitioner directory failed '+directory.status());
const practitioners=await directory.json();
ensure(Array.isArray(practitioners)&&practitioners.some(p=>p.id===record.praticien_id),
 'Authenticated practitioner missing from assignable directory');
const resources=await client.get('/api/agenda/resources',{headers});
ensure(resources.status()===200&&Array.isArray(await resources.json()),
 'Tenant-scoped resource directory unavailable');
const resourceCreated=await client.post('/api/agenda/resources',{headers,data:{name:'T2 SYNTHETIC ROOM',resource_type:'ROOM'}});
ensure([201,409].includes(resourceCreated.status()),'T2 synthetic resource creation failed '+resourceCreated.status());
let resourceId;
if(resourceCreated.status()===201)resourceId=(await resourceCreated.json()).id;
else resourceId=(await resources.json()).find(r=>r.name==='T2 SYNTHETIC ROOM')?.id;
ensure(Number.isSafeInteger(resourceId),'Synthetic resource identity unavailable');
const sharedStart=date+'T15:30:00',sameResource=date+'T15:45:00';
const withResource=await client.post('/api/appointments/',{headers,data:{...payload(sharedStart),resource_id:resourceId}});
ensure(withResource.status()===200,'Real resource-specific POST failed '+withResource.status());
const resourceRow=await withResource.json();
ensure(resourceRow.resource_id===resourceId,'Resource silently changed at persistence');
const resourceCheck=await client.get('/api/appointments/check-conflicts',{headers,params:{
 datetime_start:sameResource,duration_minutes:30,praticien_id:record.praticien_id,resource_id:resourceId,
}});
ensure(resourceCheck.status()===200&&(await resourceCheck.json()).has_conflict===true,
 'Capacity-one resource overlap missing in check-conflicts');
const resourceCollision=await client.post('/api/appointments/',{headers,data:{...payload(sameResource),resource_id:resourceId}});
ensure(resourceCollision.status()===409,'Shared capacity-one resource collision not refused');

// F02: real bulk insertion must reject overlaps and remain atomic.
const bulkBase=date+'T16:45:00',bulkOverlap=date+'T16:50:00';
const bulkInvalid=await client.post('/api/appointments/bulk',{headers,data:{appointments:[
 {patient_name:'SYNTHETIC BULK INVALID',datetime_start:bulkBase,duration_minutes:0}
]}});
ensure(bulkInvalid.status()===422,'Bulk accepted nonpositive duration '+bulkInvalid.status());
const bulkInternal=await client.post('/api/appointments/bulk',{headers,data:{appointments:[
 {patient_name:'SYNTHETIC BULK ONE',datetime_start:bulkBase,duration_minutes:30},
 {patient_name:'SYNTHETIC BULK TWO',datetime_start:bulkOverlap,duration_minutes:30}
]}});
ensure(bulkInternal.status()===409,'Bulk accepted overlapping internal appointments '+bulkInternal.status());
const listAfterBulkRejection=await client.get('/api/appointments/',{headers});
ensure((await listAfterBulkRejection.json()).every(x=>x.datetime_start!==bulkBase),
 'Bulk overlap rejection persisted partial data');
const bulkAllowed=await client.post('/api/appointments/bulk',{headers,data:{appointments:[
 {patient_name:'SYNTHETIC BULK ALLOWED',datetime_start:bulkBase,duration_minutes:30}
]}});
ensure(bulkAllowed.status()===200,'Valid bulk appointment failed '+bulkAllowed.status());
const bulkExisting=await client.post('/api/appointments/bulk',{headers,data:{appointments:[
 {patient_name:'SYNTHETIC BULK COLLISION',datetime_start:bulkOverlap,duration_minutes:30}
]}});
ensure(bulkExisting.status()===409,'Bulk ignored persisted overlapping appointment '+bulkExisting.status());
// F03: an explicit resource reassignment must persist on edit.
const clearingResource=await client.put('/api/appointments/'+resourceRow.id,{headers,data:{resource_id:null}});
ensure(clearingResource.status()===200&&(await clearingResource.json()).resource_id===null,
 'Explicit resource unassignment was not persisted safely');

// F05: genuine simultaneous REST requests through the running disposable FastAPI.
// This is a race observation, not proof that all schedules/engines are serializable.
const concurrencyStart='2026-10-22T15:00:00';
const concurrentPosts=await Promise.all([0,1].map(i=>client.post('/api/appointments/',{
  headers,data:{...payload(concurrencyStart),patient_name:'SYNTHETIC CONCURRENT '+i},
})));
const postStatuses=concurrentPosts.map(x=>x.status()).sort((a,b)=>a-b);
const concurrencyList=await client.get('/api/appointments/',{headers});
const storedConcurrent=(await concurrencyList.json()).filter(x=>x.datetime_start===concurrencyStart);
const noDouble=storedConcurrent.length===1 && postStatuses.join(',')==='200,409';
console.log('LOT07_F05_CONCURRENCY_POST_POST '+JSON.stringify({postStatuses,stored:storedConcurrent.length,noDouble}));
ensure(noDouble,'F05 unsafe concurrent POST/POST or unexpected transaction error '+JSON.stringify({postStatuses,stored:storedConcurrent.length}));
const updateRaceTime='2026-10-22T16:00:00';
const updateRace=await Promise.all([
 client.put('/api/appointments/'+record.id,{headers,data:{datetime_start:updateRaceTime,duration_minutes:30}}),
 client.post('/api/appointments/',{headers,data:{...payload(updateRaceTime),patient_name:'SYNTHETIC POST PUT'}})
]);
const updateRaceStatuses=updateRace.map(x=>x.status()).sort((a,b)=>a-b);
const afterRace=await client.get('/api/appointments/',{headers});
const sameSlot=(await afterRace.json()).filter(x=>x.datetime_start===updateRaceTime);
const noDoublePut=sameSlot.length===1 && updateRaceStatuses.join(',')==='200,409';
console.log('LOT07_F05_CONCURRENCY_PUT_POST '+JSON.stringify({statuses:updateRaceStatuses,stored:sameSlot.length,noDouble:noDoublePut}));
ensure(noDoublePut,'F05 unsafe concurrent PUT/POST '+JSON.stringify({statuses:updateRaceStatuses,stored:sameSlot.length}));

const otherDirectory=await otherClient.get('/api/appointments/assignable-practitioners',{headers:{Authorization:'Bearer '+otherToken}});
ensure(otherDirectory.status()===200&&!(await otherDirectory.json()).some(p=>p.id===record.praticien_id),
 'Another tenant can enumerate current practitioner');
await otherClient.dispose();
await clean.dispose();
await client.dispose();
console.log('LOT07_AGENDA_INTEGRITY_T2_SUCCESS '+JSON.stringify({
 sourceHead:process.env.SOURCE_HEAD,
 post:200,put:200,get:200,wallStart:hour1,wallEdited:hour2,
 conflictCheck:200,duplicateConflict:409,
 invalidAuth:invalidAuth.status(),forbiddenPatient:forbiddenPatient.status(),restricted:restrictedWrite.status(),
 otherTenantHidden:true,disposable:true
}));
