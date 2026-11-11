/** Exact-head synthetic authenticated Cephalo point-drag → FastAPI → SQLite test.
 * No patient photographs, medical model, measured calibration or clinical signoff.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head=process.env.PRODUCT_HEAD;
const password=process.env.T2_PASSWORD;
const seed=JSON.parse(process.env.CEPH_ODF_CASE_JSON||'{}');
const expectedDB='sqlite:///./t2-runtime-cert.db';
if (process.env.ENVIRONMENT!=='test'
  || process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
  || process.env.DATABASE_URL!==expectedDB
  || process.env.CLOUD_AI_ENABLED!=='false'
  || !/^[a-f0-9]{40}$/.test(head||'')
  || !password
  || !Number.isSafeInteger(seed.patient_id)
  || !Number.isSafeInteger(seed.analysis_id)
  || seed.clinical_release!==false
  || seed.fixture_name!=='T2-CEPH-ODF-E2E-01'
  || !Array.isArray(seed.original_landmarks)
  || seed.original_landmarks.length!==38) throw Error('NON_DISPOSABLE_ENVIRONMENT_OR_STUDY_REJECTED');

const dir=path.resolve('../artifacts/ceph-odf-gui-sqlite-e2e');
await fs.mkdir(dir,{recursive:true});
const report={
  schema:'CEPH_ODF_GUI_SQLITE_REAL_E2E_SYNTHETIC_V1', head,
  study_id:seed.analysis_id, patient_synthetic:true,
  real_image_used:false, model_inference_used:false, clinical_release:false,
  mm_scale_validated:false, scientific_norms_validated:false,
  checks:[],errors:[], screenshots:[],changed_id:null,
  original_landmarks:seed.original_landmarks, saved_landmarks:null, after_undo:null, after_redo:null,
  final_status:'NOT_TESTED'
};
const assert=(ok,message)=>{if(!ok)throw Error(message)};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const browser=await chromium.launch({headless:true});
let ctx=null,page=null,token=null;
const putResponses=[];
async function shot(name){
  if(!page)return;
  const file=name+'.png';
  await page.screenshot({path:path.join(dir,file),animations:'disabled',fullPage:false});
  report.screenshots.push(file);
}
async function check(id,fn){
  try{const value=await fn();report.checks.push({id,status:'PASS',value});console.log('CEPH_ODF_E2E_PASS',id);return true;}
  catch(error){report.checks.push({id,status:'FAIL',error:String(error)});report.errors.push(id+': '+String(error));console.error('CEPH_ODF_E2E_FAIL',id,String(error));await shot('fail-'+id).catch(()=>{});return false;}
}
async function read(){
  const response=await api.get('/api/ia/analyses/'+seed.analysis_id,{headers:{Authorization:'Bearer '+token}});
  assert(response.status()===200,'REAL_GET_FAILED '+response.status());
  return response.json();
}
const diffs=(a,b)=>a.filter((p,i)=>{
  const q=b[i];return !q||p.id!==q.id||Math.abs(p.x-q.x)>0.05||Math.abs(p.y-q.y)>0.05;
});
async function until(description,fn,timeout=18000){
  const stop=Date.now()+timeout;
  while(Date.now()<stop){
    const item=await read();
    if(fn(item))return item;
    await sleep(300);
  }
  throw Error(description+' — no committed change on fresh REST GET');
}
async function loadStudy(){
  await page.goto('http://127.0.0.1:5173/patients/'+seed.patient_id+'?tab=radiology&radioTab=cephalo',{waitUntil:'domcontentloaded'});
  await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:30000});
  const active=page.locator('[data-cephalo-selected-analysis-id="'+seed.analysis_id+'"]');
  if(!(await active.isVisible().catch(()=>false))){
    await page.getByRole('button',{name:'Historique',exact:true}).click();
    await page.locator('[data-cephalo-history-analysis-id="'+seed.analysis_id+'"]').click();
  }
  await active.waitFor({state:'visible',timeout:25000});
  await page.locator('svg[data-cephalo-viewport="base"] image').waitFor({state:'attached'});
  const ready=page.locator('[data-cephalo-readiness]');
  await ready.waitFor({state:'visible'});
  const body=await ready.innerText();
  assert(body.includes('Validation du praticien non attestée'),'NO_CLINICAL_VALIDATION_DISCLOSURE');
  assert(body.includes('mesures en mm non attestées'),'FALSE_MM_SCALE_DISCLOSURE');
  assert((await page.getByText('Brouillon uniquement · sans validation clinique').count())>0,'DRAFT_SAVE_DISCLOSURE_MISSING');
}
try{
  const login=await check('REAL_AUTHENTICATED_CABINET_LOGIN',async()=>{
    const auth=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
    assert(auth.status()===200,'LOGIN_REJECTED '+auth.status());
    token=(await auth.json()).access_token;
    const station=await enrollT2Workstation(api,token,password);
    ctx=await browser.newContext({viewport:{width:1280,height:900},
      storageState:{cookies:station.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
    page=await ctx.newPage();page.setDefaultTimeout(25000);
    page.on('response',r=>{
      if(r.request().method()==='PUT'&&r.url().includes('/api/ia/analyses/'+seed.analysis_id)){
        putResponses.push({status:r.status(),urlPath:'/api/ia/analyses/{synthetic-id}'});
      }
    });
    await page.goto('http://127.0.0.1:5173/hub?select=1',{waitUntil:'domcontentloaded'});
    await page.locator('[data-hub-experience="cabinet"]').click();
    await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
    await page.locator('input[type=password]').fill(password);
    await page.getByRole('button',{name:'Se connecter',exact:true}).click();
    await page.waitForURL(url=>new URL(url).pathname==='/dashboard',{timeout:50000});
    await loadStudy();
    const before=await read();
    assert(before.landmarks_data?.length===38,'NOT_38_SYNTHETIC_LANDMARKS');
    assert(same(before.landmarks_data,seed.original_landmarks),'SOURCE_CHANGED_BEFORE_TEST');
    assert(before.is_calibrated===false&&before.mm_per_pixel===null,'FALSE_PHYSICAL_CALIBRATION');
    await shot('01-before-genuine-workspace');
    return {case_id:seed.analysis_id,loaded_from:'FastAPI',source:'synthetic PNG + 38 fixtures'};
  });
  if(login){
    const dragOK=await check('REAL_POINTER_DRAG_COMMITTED_TO_FASTAPI',async()=>{
      await page.getByText('Historique des corrections',{exact:true}).click();
      const undo=page.getByRole('button',{name:'Annuler dernière correction'});
      assert(await undo.isDisabled(),'EDIT_HISTORY_NOT_EMPTY');
      const targets=page.locator('g[data-ortho-layer="landmarks"] circle[r="20"]');
      const count=await targets.count();
      // Scientific source retains 38; the active COM/Steiner view intentionally
      // shows only the applicable subset of its 38 source landmarks.
      assert(count>=3&&count<=38,'INVALID_VISIBLE_RETICLE_COUNT '+count);
      let drag=null;
      for(let i=0;i<count;i++){
        const p=targets.nth(i);
        await p.scrollIntoViewIfNeeded().catch(()=>{});
        const r=await p.boundingBox();
        if(!r||r.width<1||r.height<1)continue;
        const x=r.x+r.width/2,y=r.y+r.height/2;
        const cx=Number(await p.getAttribute('cx')),cy=Number(await p.getAttribute('cy'));
        const source=seed.original_landmarks.find(q=>Math.hypot(q.x-cx,q.y-cy)<.05);
        if(!source||x<120||x>1150||y<165||y>825)continue;
        const hit=await page.evaluate(({x,y})=>{
          const n=document.elementFromPoint(x,y);
          return n?.tagName?.toLowerCase()==='circle'&&n.getAttribute('r')==='20';
        },{x,y});
        if(hit){drag={x,y,id:source.id};break;}
      }
      assert(drag,'NO_UNOBSTRUCTED_LANDMARK_ON_REAL_SVG');
      report.changed_id=drag.id;
      await page.mouse.move(drag.x,drag.y);
      await page.mouse.down();
      await page.mouse.move(drag.x+23,drag.y+17,{steps:14});
      await page.mouse.up();
      await page.waitForTimeout(250);
      assert(!(await undo.isDisabled()),'DRAG_DID_NOT_CREATE_UNDO');
      const after=await until('REAL_POINTER_DRAG_NOT_PERSISTED',d=>
        d.landmarks_data?.length===38&&diffs(seed.original_landmarks,d.landmarks_data).length===1);
      const modified=diffs(seed.original_landmarks,after.landmarks_data);
      assert(modified.length===1&&modified[0].id===report.changed_id,'DRAG_CHANGED_WRONG_POINT');
      assert(after.is_calibrated===false&&after.mm_per_pixel===null,'DRAG_FABRICATED_MM_SCALE');
      report.saved_landmarks=after.landmarks_data;
      await shot('02-after-real-pointer-drag');
      return {drag_id:report.changed_id,saved:true,points:38,no_physical_calibration:true};
    });
    if(dragOK)await check('REAL_GUI_UNDO_REDO_PERSISTED_SQLITE',async()=>{
      const undo=page.getByRole('button',{name:'Annuler dernière correction'});
      const redo=page.getByRole('button',{name:'Rétablir correction'});
      await undo.click();
      assert(!(await redo.isDisabled()),'UNDO_DID_NOT_ENABLE_REDO');
      const first=await until('UNDO_NOT_PERSISTED',d=>same(d.landmarks_data,seed.original_landmarks));
      report.after_undo=first.landmarks_data;
      await shot('03-after-undo');
      await redo.click();
      assert(!(await undo.isDisabled()),'REDO_DID_NOT_RESTORE_HISTORY');
      const second=await until('REDO_NOT_PERSISTED',d=>same(d.landmarks_data,report.saved_landmarks));
      report.after_redo=second.landmarks_data;
      await shot('04-after-redo');
      return {undo_persisted:true,redo_persisted:true};
    });
    if(dragOK)await check('DRAFT_SAVE_AND_FRESH_BROWSER_RELOAD',async()=>{
      const before=await read();
      assert(same(before.landmarks_data,report.saved_landmarks),'INCONSISTENT_REDO_BEFORE_SAVE');
      await page.getByRole('button',{name:'Sauvegarder l’analyse céphalométrique'}).click();
      await until('MANUAL_DRAFT_SAVE_NOT_VISIBLE',d=>same(d.landmarks_data,report.saved_landmarks));
      assert((await page.getByText('Brouillon uniquement · sans validation clinique').count())>0,'DRAFT_LABEL_LOST');
      await page.reload({waitUntil:'domcontentloaded'});
      await loadStudy();
      const reopened=await read();
      assert(same(reopened.landmarks_data,report.saved_landmarks),'DATA_CHANGED_AFTER_BROWSER_RELOAD');
      assert(reopened.is_calibrated===false&&reopened.mm_per_pixel===null,'RELOAD_FABRICATED_SCALE');
      const ui=page.locator('g[data-ortho-layer="landmarks"] circle[r="20"]');
      await ui.first().waitFor({state:'attached'});
      const coords=await ui.evaluateAll(els=>els.map(el=>({
        x:Number(el.getAttribute('cx')),y:Number(el.getAttribute('cy'))
      })));
      assert(coords.length>=3&&coords.length<=38,'RELOADED_UI_MISSING_RETICLES');
      const edited=report.saved_landmarks.find(x=>x.id===report.changed_id);
      assert(edited&&coords.some(p=>Math.abs(p.x-edited.x)<.08&&Math.abs(p.y-edited.y)<.08),
        'RELOADED_UI_EDITED_LANDMARK_COORDS_MISMATCH');
      await shot('05-after-browser-reload');
      await page.setViewportSize({width:390,height:844});
      await shot('06-mobile-final-synthetic');
      return {auth_fresh_REST_GET:true,reloaded_UI:true,not_clinically_validated:true};
    });
  }
  report.put_responses=putResponses;
  assert(putResponses.some(p=>p.status>=200&&p.status<300),'NO_SUCCESSFUL_AUTHENTICATED_PUT');
  assert(putResponses.every(p=>p.status>=200&&p.status<300),'ONE_OR_MORE_PUT_FAILED');
  if(!report.errors.length&&report.saved_landmarks&&report.after_undo&&report.after_redo){
    report.final_status='REAL_GUI_FASTAPI_SQLITE_DRAG_UNDO_REDO_RELOAD_PASS_SYNTHETIC_NONCLINICAL';
  }else{
    report.final_status='NO_GO_REAL_GUI_E2E_UNPROVED';
  }
}catch(error){
  report.errors.push('UNEXPECTED '+String(error));
  report.final_status='NO_GO_REAL_GUI_E2E_UNPROVED';
}finally{
  await fs.writeFile(path.join(dir,'report.json'),JSON.stringify(report,null,2));
  console.log('CEPH_ODF_GUI_SQLITE_RESULT',report.final_status,
    JSON.stringify({head,passes:report.checks.filter(x=>x.status==='PASS').map(x=>x.id),
      failures:report.errors, clinical_release:false}));
  if(ctx)await ctx.close().catch(()=>{});
  await browser.close();
  await api.dispose();
}
if(report.errors.length||report.final_status!=='REAL_GUI_FASTAPI_SQLITE_DRAG_UNDO_REDO_RELOAD_PASS_SYNTHETIC_NONCLINICAL')
  process.exitCode=1;
