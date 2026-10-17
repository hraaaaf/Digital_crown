// LOT07 07-A Agenda Integrity — real disposable T2 authenticated POST/PUT/GET.
// No remote services, clinic data, patient identifiers or real patient names.
import { request } from 'playwright';

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
const invalidAuth=await client.get('/api/appointments/',{headers:{Authorization:'Bearer invalid-token'}});
ensure([401,403].includes(invalidAuth.status()),'Expired/invalid session accepted '+invalidAuth.status());
const restricted=await client.post('/api/auth/login',{form:{
 username:'t2-restricted@cabinet.ma',password:process.env.T2_PASSWORD
}});
ensure(restricted.status()===200,'Restricted T2 auth fixture failed');
const rt=(await restricted.json()).access_token;
const restrictedWrite=await client.post('/api/appointments/',{headers:{Authorization:'Bearer '+rt},
 data:{...payload(date+'T11:30:00'),patient_id:999999}});
ensure([403,404].includes(restrictedWrite.status()),
 'Unauthorized patient relation unexpectedly permitted '+restrictedWrite.status());
const other=await client.post('/api/auth/login',{form:{
 username:'t2-setup-390@cabinet.ma',password:process.env.T2_PASSWORD
}});
ensure(other.status()===200,'Other-tenant T2 auth fixture failed');
const otherToken=(await other.json()).access_token;
const otherList=await client.get('/api/appointments/',{headers:{Authorization:'Bearer '+otherToken}});
ensure(otherList.status()===200&&!((await otherList.json()).some(row=>row.id===record.id)),
 'Cross-tenant appointment became readable');
await client.dispose();
console.log('LOT07_AGENDA_INTEGRITY_T2_SUCCESS '+JSON.stringify({
 sourceHead:process.env.SOURCE_HEAD,
 post:200,put:200,get:200,wallStart:hour1,wallEdited:hour2,
 conflictCheck:200,duplicateConflict:409,
 invalidAuth:invalidAuth.status(),restricted:restrictedWrite.status(),
 otherTenantHidden:true,disposable:true
}));
