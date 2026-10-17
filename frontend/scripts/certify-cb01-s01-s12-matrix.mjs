/**
 * CB-01 isolated GitHub Actions staff evidence ledger, NOT a human T2 certification.
 *
 * Seven scoped HTTP assertions are executed against a disposable synthetic T2.
 * Other canonical S01-S12 journeys remain PARTIAL or NOT_RUN. Never create
 * appointments, mutate clinical records or call /bot/execute.
 */
import fs from 'node:fs';
import path from 'node:path';
import { request } from 'playwright';

if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1') {
  throw new Error('REFUSED: disposable isolated T2 required');
}
const origin = process.env.CB01_T2_API_URL || 'http://127.0.0.1:8005';
const url = new URL(origin);
if (url.protocol !== 'http:' || !['localhost', '127.0.0.1'].includes(url.hostname)
    || url.username || url.password || url.search || url.hash
    || (url.pathname !== '/' && url.pathname !== '')) {
  throw new Error('REFUSED: loopback-only synthetic API');
}
const owner=process.env.T2_USER;
const receptionist=process.env.T2_S05_USER;
const denied=process.env.T2_S06_USER;
const sourceHead=process.env.CB01_SOURCE_HEAD || '';
const patientId=Number(process.env.T2_PATIENT_ID);
const foreignId=Number(process.env.T2_FOREIGN_PATIENT_ID);
const unknownId=Number(process.env.T2_UNKNOWN_PATIENT_ID);
if (![owner,receptionist,denied].every(v=>v?.startsWith('t2-'))
    || new Set([owner,receptionist,denied]).size !== 3
    || ![patientId,foreignId,unknownId].every(v=>Number.isSafeInteger(v)&&v>0)
    || new Set([patientId,foreignId,unknownId]).size !== 3
    || !/^[0-9a-f]{40}$/.test(sourceHead)
    || !process.env.T2_PASSWORD || !process.env.T2_S05_PASSWORD
    || !process.env.T2_S06_PASSWORD) {
  throw new Error('REFUSED: complete distinct synthetic fixtures and exact source SHA required');
}

const statusById=new Map();
for (const [id,title,reason] of [
  ['S01','Dentist agenda tomorrow','PARTIAL: Agenda React layout certified in the preceding browser step, not tomorrow agenda human interaction'],
  ['S07','Adjacent appointment slots','NOT_RUN: booking concurrency belongs to separate integration gates, no clinical booking in CB-01'],
  ['S09','Stale booking ABA conflict','NOT_RUN: PostgreSQL/SQLCipher concurrency checked separately, not an end-to-end UI journey'],
  ['S10','Reception conflict 409 recovery','NOT_RUN: mocked Vitest 409 recovery exists, real concurrent 409 UX not simulated here'],
  ['S12','GhostBrain mark-as-read','NOT_RUN: mock read-ack unit test exists, human alert journey not executed here'],
]) statusById.set(id,{id,title,status:id==='S01'?'PARTIAL_SYNTHETIC':'NOT_RUN',reason,humanE2E:'NOT_RUN'});

const api=await request.newContext({baseURL:origin,ignoreHTTPSErrors:false});
const output=path.resolve('../artifacts/cb01-associate-sidecar/s01-s12-synthetic-matrix.json');
const failures=[];
const noActionIdentifiers=(obj)=>{
  const serialized=JSON.stringify(obj);
  if (/(?:pending_action_id|pendingActionId|action_id|actionId)/.test(serialized)) {
    throw new Error('executable action identifier leaked');
  }
};
const assert=(condition,label)=>{if(!condition)throw new Error(label)};
async function login(email,password) {
  const response=await api.post('/api/auth/login',{form:{username:email,password}});
  assert(response.status()===200,'synthetic login rejected');
  const json=await response.json();
  assert(typeof json.access_token==='string'&&json.access_token.length>10,
    'missing synthetic access token');
  return json.access_token;
}
async function preview(token,messages){
  assert(Array.isArray(messages)&&messages.length>=1&&messages.length<=8,
    'bounded preview transcript violated');
  const response=await api.post('/api/bot/workflows/preview',{
    data:{messages},headers:{Authorization:'Bearer '+token},
    maxRedirects:0,
  });
  const json=await response.json();
  noActionIdentifiers(json);
  return {code:response.status(),body:json};
}
async function check(id,title,fn){
  try {
    await fn();
    statusById.set(id,{id,title,status:'PASS_SYNTHETIC',humanE2E:'NOT_RUN',
      scope:'Synthetic scoped HTTP contract only; no human end-to-end journey'});
  } catch(error) {
    statusById.set(id,{id,title,status:'FAIL',humanE2E:'NOT_RUN',
      scope:'Synthetic scoped HTTP assertion failed (details intentionally withheld)'});
    failures.push(id);
  }
}
try {
  const [dentist,s05,s06]=await Promise.all([
    login(owner,process.env.T2_PASSWORD),
    login(receptionist,process.env.T2_S05_PASSWORD),
    login(denied,process.env.T2_S06_PASSWORD),
  ]);
  await check('S02','Benali homonyms, explicit patient identity',async()=>{
    const r=await preview(dentist,['/patient','BENALI']);
    assert(r.code===200&&r.body.status==='disambiguation'
      && r.body.proposal===null
      && r.body.candidates?.length===2,'homonyms not disambiguated');
    const dossiers=new Set(r.body.candidates.map(p=>p.numero_dossier));
    assert(dossiers.has('CB01-N-101')&&dossiers.has(String(patientId)),
      'expected two synthetic dossiers');
  });
  await check('S03','Dentist lookup of authorized synthetic patient',async()=>{
    const r=await preview(dentist,['/patient','dossier:T2-0001']);
    assert(r.code===200&&r.body.status==='read'
      && r.body.patient?.id===patientId&&r.body.proposal===null,
      'authorized patient read failed');
  });
  await check('S04','Mme Benali surname selection and no auto-choice',async()=>{
    const r=await preview(dentist,['/patient','Mme Benali']);
    assert(r.code===200&&r.body.status==='disambiguation'
      && r.body.candidates?.length===2&&r.body.proposal===null,
      'exact surname homonyms not safely handled');
  });
  const proposal=['/rdv','dossier:CB01-N-101','2099-01-01','10:00',
    '30','consultation','CONFIRMER'];
  await check('S05','Reception prepares non-executable appointment',async()=>{
    const r=await preview(s05,proposal);
    assert(r.code===200&&r.body.status==='proposal_only'
      && r.body.proposal?.type==='CREATE_APPOINTMENT'
      && Number.isInteger(r.body.proposal?.params?.patient_id)
      && r.body.proposal?.params?.datetime_start==='2099-01-01T10:00:00'
      && r.body.proposal?.params?.duration_minutes===30
      && r.body.proposal?.params?.motif==='CONSULTATION',
      'S05 returned no safe appointment proposal');
  });
  await check('S06','Reception without agenda permission fails closed',async()=>{
    const early=await preview(s06,['/rdv']);
    const full=await preview(s06,proposal);
    assert(early.code===403&&full.code===403
      && early.body.detail==='Accès refusé.'
      && JSON.stringify(early.body)===JSON.stringify(full.body),
      'S06 denied permission leaked identity or changed response');
  });
  await check('S08','Dentist crown estimate is only a non-executable draft',async()=>{
    const r=await preview(dentist,[
      '/devis','dossier:CB01-N-101','couronne','CONFIRMER',
    ]);
    assert(r.code===200&&r.body.status==='proposal_only'
      && r.body.proposal?.type==='OPEN_DEVIS_EDITOR'
      && r.body.proposal?.params?.procedure==='COURONNE'
      && r.body.proposal?.params?.draft_only===true,
      'S08 preview unexpectedly actionable or unavailable');
  });
  await check('S11','Foreign patient and unknown ID indistinguishable',async()=>{
    const results=await Promise.all([
      preview(dentist,['/patient','id:'+foreignId]),
      preview(dentist,['/patient','id:'+unknownId]),
      preview(dentist,['/patient','dossier:CB00-FR-0001']),
    ]);
    assert(results.every(x=>x.code===404
      && x.body.detail==='Patient introuvable.'
      && JSON.stringify(x.body)===JSON.stringify(results[0].body)),
      'S11 foreign patient existence leakage');
  });
} finally {
  await api.dispose();
}
const cases=Array.from({length:12},(_,i)=>{
  const key='S'+String(i+1).padStart(2,'0');
  const entry=statusById.get(key);
  if(!entry) throw new Error('FAIL: incomplete evidence manifest '+key);
  return entry;
});
const counters={
  passedSynthetic:cases.filter(c=>c.status==='PASS_SYNTHETIC').length,
  partialSynthetic:cases.filter(c=>c.status==='PARTIAL_SYNTHETIC').length,
  notRun:cases.filter(c=>c.status==='NOT_RUN').length,
  failed:cases.filter(c=>c.status==='FAIL').length,
  humanE2EValidated:0,
};
const report={
  schema:'CB01_S01_S12_MACHINE_MATRIX_V1',
  kind:'DISPOSABLE_GITHUB_ACTIONS_SYNTHETIC_ONLY',
  exactHead:sourceHead,
  humanWorkstation:'NOT_CONNECTED',
  browserNativeZoom200:'NOT_TESTED',
  databaseFullDiff:'NOT_TESTED',
  noClinicalBookingPerformed:true,
  scenarios:cases,counts:counters,
};
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n',{mode:0o600});
if(counters.passedSynthetic!==7||counters.partialSynthetic!==1
    ||counters.notRun!==4||counters.failed>0) {
  throw new Error('FAIL: incomplete or failed S01-S12 synthetic certification matrix ('+
    failures.join(',')+')');
}
console.log('CB01_S01_S12_SYNTHETIC: PASS '+JSON.stringify(counters));
