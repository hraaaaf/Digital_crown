/** DC-DOS-01 authenticated multi-tenant patient-switch FUE. Synthetic isolated T2 only. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';
const checkTrue = (x,msg)=>{if(!x)throw Error(msg)};
const head=process.env.PRODUCT_HEAD,password=process.env.T2_PASSWORD;
const f=JSON.parse(process.env.DC_DOS01_FIXTURE||'{}');
checkTrue(process.env.ENVIRONMENT==='test' && process.env.DIGITALCROWN_ISOLATED_RUNTIME==='1'
  && /^[a-f0-9]{40}$/.test(head||'') && password && f.synthetic_only===true
  && ['patient_a','patient_b','patient_x','study_a','study_b','tenant_x_user'].every(x=>Number.isSafeInteger(f[x]))
  && new Set([f.patient_a,f.patient_b,f.patient_x]).size===3,
  'Refusing unverified T2-only synthetic multitenant fixture');
const root='http://127.0.0.1:5173', backend='http://127.0.0.1:8005';
const output=path.resolve('../artifacts/ceph-v1-dos01-multitenant');
await fs.mkdir(output,{recursive:true});
const proof={head,case_id:'DC-DOS-01',synthetic_only:true,official_fue_complete:false,
  clinical_release:false,checks:[],shots:[],errors:[],status:'NOT_RUN'};
let browser,page,foreignPage,ownerApi,foreignApi,ownerContext,foreignContext;
async function shot(name,p=page) {
  if (!p) return;
  await p.screenshot({path:path.join(output,name+'.png'),animations:'disabled'});
  proof.shots.push(name+'.png');
}
async function verify(id,fn) {
  try {
    const result=await fn();
    proof.checks.push({id,status:'PASS',evidence:result||{}});
    console.log('DC_DOS01_PASS',id);
    return result;
  }catch(e) {
    proof.checks.push({id,status:'FAIL',error:String(e)});
    proof.errors.push(id+': '+String(e));
    await shot('failure-'+id.toLowerCase()).catch(()=>{});
    console.log('DC_DOS01_FAIL',id,String(e));
    throw e;
  }
}
async function login(api,email) {
  const res=await api.post('/api/auth/login',{form:{username:email,password}});
  checkTrue(res.status()===200,'JWT login failed '+res.status());
  return (await res.json()).access_token;
}
async function importPhoto(api,token,pid,file) {
  const res=await api.post('/api/patients/'+pid+'/ortho-media-record/photos/EXTRA_PROFILE',{
    headers:{Authorization:'Bearer '+token},
    multipart:{file:{name:'synthetic.png',mimeType:'image/png',buffer:await fs.readFile(file)},
      timepoint:'T0',acquired_at:'2026-11-08T09:00:00+00:00'},
  });
  checkTrue(res.status()===201,'Media import patient '+pid+' HTTP '+res.status()+' '+(await res.text()).slice(0,400));
  const data=await res.json();
  checkTrue(data.schema_version==='ORTHO_MEDIA_RECORD_V1' &&
    data.slot_id==='EXTRA_PROFILE' && data.asset?.patient_id===pid &&
    Number.isSafeInteger(data.asset?.id),'Media asset identity mismatch');
  return data.asset.id;
}
const get=(api,token,url)=>api.get(url,{headers:{Authorization:'Bearer '+token}});
async function deny(api,token,url) {
  const res=await get(api,token,url);
  checkTrue([403,404].includes(res.status()),'Cross-tenant HTTP '+res.status()+' at '+url);
  return res.status();
}
async function own(api,token,url) {
  const res=await get(api,token,url);
  checkTrue(res.status()===200,'Own-patient HTTP '+res.status()+' at '+url);
  return res.json();
}
async function browserLogin(context,email) {
  const p=await context.newPage();
  await p.goto(root+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
  await p.locator('[data-hub-experience="cabinet"]').click();
  await p.locator('input[type=email]').fill(email);
  await p.locator('input[type=password]').fill(password);
  await p.getByRole('button',{name:'Se connecter',exact:true}).click();
  await p.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
  checkTrue(await p.evaluate(()=>Boolean(localStorage.getItem('token'))),'Real UI JWT missing');
  return p;
}
async function openPatient(p,id,fresh=false) {
  const url=root+'/patients/'+id+'?tab=radiology&radioTab=cephalo';
  if(fresh)await p.goto(url,{waitUntil:'domcontentloaded',timeout:45000});
  else await p.evaluate(dest=>{
    history.pushState({},'',dest);
    dispatchEvent(new PopStateEvent('popstate',{state:{}}));
  },url);
}
async function selectStudy(p,id) {
  await p.getByRole('button',{name:'Historique',exact:true}).click();
  const choice=p.locator('[data-cephalo-history-analysis-id="'+id+'"]');
  await choice.waitFor({state:'visible',timeout:30000});
  await choice.click();
  await p.locator('[data-cephalo-selected-analysis-id="'+id+'"]')
    .waitFor({state:'visible',timeout:30000});
}
async function showProfile(p) {
  await p.getByRole('button',{name:'Passer aux moulages',exact:true}).click();
  const image=p.locator('[data-ortho-photo-slot="EXTRA_PROFILE"] img[alt="Vue orthodontique"]');
  await image.waitFor({state:'visible',timeout:30000});
  const src=await image.getAttribute('src');
  checkTrue(src?.startsWith('blob:'),'Protected Media Core preview did not render a blob');
  return src;
}
try {
  ownerApi=await request.newContext({baseURL:backend});
  foreignApi=await request.newContext({baseURL:backend});
  browser=await chromium.launch({headless:true});
  const ownerJwt=await login(ownerApi,'t2-browser@cabinet.ma');
  const foreignJwt=await login(foreignApi,'t2-dos01-foreign@cabinet.ma');
  const ownerEnrolled=await enrollT2Workstation(ownerApi,ownerJwt,password);
  const foreignEnrolled=await enrollT2Workstation(foreignApi,foreignJwt,password);
  checkTrue(ownerEnrolled.cookies.some(x=>x.name==='dc_workstation') &&
    foreignEnrolled.cookies.some(x=>x.name==='dc_workstation'),'Isolated cabinet enrollment missing');
  const assets=await verify('REAL_JWT_UPLOADS_TO_THREE_SYNTHETIC_PATIENTS',async()=>{
    const a=await importPhoto(ownerApi,ownerJwt,f.patient_a,f.images.a);
    const b=await importPhoto(ownerApi,ownerJwt,f.patient_b,f.images.b);
    const x=await importPhoto(foreignApi,foreignJwt,f.patient_x,f.images.x);
    checkTrue(new Set([a,b,x]).size===3,'Asset IDs collided across patients');
    return {a,b,x};
  });
  await verify('PATIENT_SCOPED_MEDIA_TIMELINE_AND_ORTHO_SLOTS',async()=>{
    const triple=[[ownerApi,ownerJwt,f.patient_a,assets.a],[ownerApi,ownerJwt,f.patient_b,assets.b],
                  [foreignApi,foreignJwt,f.patient_x,assets.x]];
    for(const [api,jwt,pid,aid] of triple) {
      const media=await own(api,jwt,'/api/patients/'+pid+'/ortho-media-record?timepoint=T0');
      checkTrue(media.patient_id===pid && media.timepoint==='T0','Wrong patient media record');
      const profile=media.photo_slots.find(x=>x.slot_id==='EXTRA_PROFILE');
      checkTrue(profile?.state==='FILLED'&&profile.asset.asset_id===aid,'Wrong source asset');
      const timeline=await own(api,jwt,'/api/patients/'+pid+'/assets');
      checkTrue(timeline.items.length===1 && timeline.items[0].id===aid &&
        timeline.items[0].patient_id===pid,'Duplicate/cross-patient timeline');
      checkTrue(!('storage_key' in timeline.items[0]) && !('sha256' in timeline.items[0]),
        'Asset storage metadata leaked');
      const blob=await get(api,jwt,'/api/patients/'+pid+'/assets/'+aid+'/content');
      checkTrue(blob.status()===200 && (await blob.body()).length>100,'Own blob not available');
    }
    return {real_http:true,patient_records:3,one_asset_per_timeline:true};
  });
  await verify('SAME_TENANT_PATIENT_ASSET_REBIND_DENIED',async()=>{
    const a=await deny(ownerApi,ownerJwt,'/api/patients/'+f.patient_b+'/assets/'+assets.a+'/content');
    const b=await deny(ownerApi,ownerJwt,'/api/patients/'+f.patient_a+'/assets/'+assets.b+'/content');
    return {a_to_b:a,b_to_a:b};
  });
  await verify('FOREIGN_TENANT_ASSETS_PATIENTS_STUDY_DENIED',async()=>{
    let denied=0;
    const subjects=[[foreignApi,foreignJwt,f.patient_a,assets.a],
      [foreignApi,foreignJwt,f.patient_b,assets.b],[ownerApi,ownerJwt,f.patient_x,assets.x]];
    for(const [api,jwt,pid,aid] of subjects) {
      for(const suffix of ['', '/assets','/ortho-media-record?timepoint=T0',
          '/assets/'+aid+'/content']) {
        await deny(api,jwt,'/api/patients/'+pid+suffix);
        denied++;
      }
    }
    const study=await get(foreignApi,foreignJwt,'/api/ia/analyses/'+f.study_a);
    checkTrue([403,404].includes(study.status()),'Cross-tenant science GET returned '+study.status());
    return {refused_http:denied+1,foreign_study_http:study.status()};
  });
  ownerContext=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce',
    storageState:{cookies:ownerEnrolled.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
  page=await browserLogin(ownerContext,'t2-browser@cabinet.ma');
  const aBlob=await verify('REAL_REACT_PATIENT_A_PROFILE',async()=>{
    await openPatient(page,f.patient_a,true);
    await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:40000});
    await selectStudy(page,f.study_a);
    const src=await showProfile(page);
    await shot('01-patient-a-media');
    return {blob_visible:true,source:'A_MEDIA_CORE'};
  });
  await verify('REAL_REACT_SPA_PATIENT_A_TO_B_NO_STALE_PHOTO',async()=>{
    const oldSrc=await page.locator('[data-ortho-photo-slot="EXTRA_PROFILE"] img').getAttribute('src');
    await openPatient(page,f.patient_b);
    await page.waitForURL(u=>new URL(u).pathname==='/patients/'+f.patient_b,{timeout:30000});
    await page.waitForFunction(name=>
      document.querySelector('[data-ortho-workspace-patient]')?.textContent?.includes(name),
      'SYNTHETIC_B',{timeout:35000});
    checkTrue(await page.locator('img[src="'+oldSrc+'"]').count()===0,
      'Patient A blob remained visible after patient B route transition');
    await shot('02-patient-b-before-study');
    await selectStudy(page,f.study_b);
    const newSrc=await showProfile(page);
    checkTrue(newSrc!==oldSrc,'Old A blob was repainted as B');
    checkTrue(await page.locator('img[src="'+oldSrc+'"]').count()===0,'A blob visible in B UI');
    await shot('03-patient-b-own-media');
    return {old_blob_hidden:true,new_blob_authenticated:true};
  });
  foreignContext=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce',
    storageState:{cookies:foreignEnrolled.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
  foreignPage=await browserLogin(foreignContext,'t2-dos01-foreign@cabinet.ma');
  await verify('REAL_REACT_FOREIGN_CABINET_OWN_AND_DENIED',async()=>{
    await openPatient(foreignPage,f.patient_x,true);
    await foreignPage.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:40000});
    const label=await foreignPage.locator('[data-ortho-workspace-patient]').innerText();
    checkTrue(label.includes('SYNTHETIC_X'),'Foreign dentist cannot view own X synthetic patient');
    await shot('04-foreign-own-patient',foreignPage);
    await openPatient(foreignPage,f.patient_a);
    await foreignPage.waitForURL(u=>new URL(u).pathname==='/patients/'+f.patient_a,{timeout:30000});
    await foreignPage.waitForTimeout(500);
    checkTrue(await foreignPage.locator('[data-ortho-photo-slot] img[alt="Vue orthodontique"]').count()===0,
      'Foreign Cabinet displayed A media');
    await shot('05-foreign-cannot-open-a',foreignPage);
    return {foreign_own_visible:true,foreign_A_photo_hidden:true};
  });
  proof.status='SUBLOT_AUTOMATED_PASS';
}catch(e) {
  proof.status='SUBLOT_FAILED';
  proof.errors.push('RUN_STOPPED: '+String(e));
}finally{
  await ownerContext?.close().catch(()=>{});
  await foreignContext?.close().catch(()=>{});
  await ownerApi?.dispose().catch(()=>{});
  await foreignApi?.dispose().catch(()=>{});
  await browser?.close().catch(()=>{});
  await fs.writeFile(path.join(output,'report.json'),JSON.stringify(proof,null,2));
}
console.log('DC_DOS01_SYNTHETIC_REAL_CABINET_RESULT',JSON.stringify({
  head,status:proof.status,checks:proof.checks.map(x=>({id:x.id,status:x.status})),
  screenshots:proof.shots.length,
}));
checkTrue(proof.status==='SUBLOT_AUTOMATED_PASS' &&
  proof.checks.length===7 && proof.checks.every(x=>x.status==='PASS'),
  'DC-DOS-01 sublot not proven: read report.json, never claim official FUE PASS');
