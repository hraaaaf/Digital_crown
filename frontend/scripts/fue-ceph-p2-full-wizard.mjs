/** FUE-P2: real authenticated T2 + real ONNX + synthetic ruler + wizard/PDF.
 * Design units apply ONLY to manufactured geometry, never patient imaging.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {chromium,request} from 'playwright';
import {enrollT2Workstation} from './t2-workstation-session.mjs';

const head=process.env.PRODUCT_HEAD,pw=process.env.T2_PASSWORD;
const patient=JSON.parse(process.env.CEPH_R23H_PATIENT||'{}');
const dir=process.env.CEPH_FUE_P2_PHANTOM_DIR||'/tmp/ceph-fue-p2-phantom';
if(process.env.ENVIRONMENT!=='test'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
 ||process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db'||!pw
 ||!/^[a-f0-9]{40}$/.test(head||'')||!Number.isSafeInteger(patient.patient_id))
 throw Error('P2 requires disposable synthetic T2');
const prev=JSON.parse(await fs.readFile('../artifacts/ceph-fue-p1-authenticated/report.json','utf8'));
if(prev.head!==head||prev.checks.length!==6||prev.errors.length
 ||prev.overall!=='FUE_P1_REAL_UI_SAFE_PARTIAL__DOCUMENT_BLOCKED_CALIBRATION')
 throw Error('Exact-head P1 prerequisite missing');
const fixture=JSON.parse(await fs.readFile(path.join(dir,'manifest.json'),'utf8'));
const image=path.join(dir,'ceph_fue_p2_phantom.png');
if(fixture.schema!=='CEPH_FUE_P2_DESIGN_PHANTOM_V1'
 ||fixture.synthetic_no_human_source!==true||fixture.true_physical_patient_scale!==false
 ||fixture.design_mm_per_pixel!==0.1||fixture.design_distance_mm!==20
 ||crypto.createHash('sha256').update(await fs.readFile(image)).digest('hex')!==fixture.sha256)
 throw Error('Unsupported source calibration fixture');
const out=path.resolve('../artifacts/ceph-fue-p2-real');await fs.mkdir(out,{recursive:true});
const report={head,schema:'CEPH_FUE_P2_DESIGN_ONLY_FULL_WIZARD_V1',
  study_id:null,source_sha256:fixture.sha256,design_mm_per_pixel:0.1,
  physical_patient_scale:false,scientific_goldset:false,clinical_release:false,
  facad_parity_verified:false,archived:false,checks:[],errors:[],screenshots:[],overall:'NOT_TESTED'};
const browser=await chromium.launch({headless:true}),api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
let ctx,page,token,study;
const ok=(condition,reason)=>{if(!condition)throw Error(reason)};
const headers=()=>({Authorization:'Bearer '+token});
const detail=async()=>{const r=await api.get('/api/ia/analyses/'+study,{headers:headers()});ok(r.status()===200,'GET selected study '+r.status());return r.json()};
async function shot(id){if(page){const fn=id+'.png';await page.screenshot({path:path.join(out,fn),animations:'disabled'});report.screenshots.push(fn)}}
async function check(id,fn){try{const evidence=await fn();report.checks.push({id,status:'PASS',evidence});console.log('FUE_P2_PASS',id);return evidence}
 catch(e){report.checks.push({id,status:'FAIL',error:String(e)});report.errors.push(id+': '+e);await shot('fail-'+id).catch(()=>{});console.log('FUE_P2_FAIL',id,String(e));throw e}}
async function point(p){
 const {x,y}=await page.locator('svg[data-cephalo-viewport="base"]').evaluate((svg,p)=>{
  const pt=svg.createSVGPoint();pt.x=p.x;pt.y=p.y;
  const screen=pt.matrixTransform(svg.getScreenCTM());return {x:screen.x,y:screen.y};
 },p);
 ok(x>0&&x<1600&&y>0&&y<1000,'Phantom ruler offscreen '+JSON.stringify({x,y,px:p}));
 await page.mouse.click(x,y);
}
try{
 await check('AUTHENTICATED_CABINET_DESIGN_ONLY_PHANTOM',async()=>{
  const a=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password:pw}});
  ok(a.status()===200,'T2 login failed');token=(await a.json()).access_token;
  const st=await enrollT2Workstation(api,token,pw);
  ctx=await browser.newContext({viewport:{width:1600,height:1000},acceptDownloads:true,
   storageState:{cookies:st.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
  page=await ctx.newPage();page.setDefaultTimeout(30000);
  await page.goto('http://127.0.0.1:5173/hub?select=1');
  await page.locator('[data-hub-experience="cabinet"]').click();
  await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
  await page.locator('input[type=password]').fill(pw);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL(x=>new URL(x).pathname==='/dashboard',{timeout:45000});
  await page.goto('http://127.0.0.1:5173/patients/'+patient.patient_id+'?tab=radiology&radioTab=cephalo');
  await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
  await shot('01-cabinet-before-phantom');
  return {real_cabinet:true,digital_source_only:true};
 });
 await check('REAL_UI_IMPORT_AND_REAL_38_OUTPUTS',async()=>{
  if(await page.locator('[data-cephalo-selected-analysis-id]').count())await page.getByTitle("Changer d'image").click();
  const future=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/ia/upload-radio'
     &&r.request().method()==='POST',{timeout:240000});
  await page.locator('input[type=file][accept="image/jpeg,image/png"]').setInputFiles(image);
  const r=await future;
  ok(r.status()===200,'ONNX phantom upload '+r.status()+' '+(await r.text()).slice(0,350));
  const p=await r.json();study=p.analysis_id;report.study_id=study;
  ok(Number.isSafeInteger(study)&&study!==prev.case_id,'Synthetic study ID invalid');
  ok(p.landmarks?.length===38&&p.results?.vision_metadata?.mode_inference==='SOTA_ONNX_38','Real ONNX model was not run');
  const saved=await detail();
  ok(saved.is_calibrated===false&&saved.mm_per_pixel==null,'Unjustified calibration');
  await page.locator('[data-cephalo-selected-analysis-id="'+study+'"]').waitFor({state:'visible'});
  await shot('02-real-onnx-unverified');
  return {study,channels:38,source:'NON-HUMAN',calibrated:false};
 });
 await check('TWO_REAL_UI_CLICKS_AND_BACKEND_MANUAL_PROVENANCE',async()=>{
  await page.locator('[data-r20-radiograph-stage]').getByRole('button',{name:/Calibration :/}).click();
  await page.locator('[data-cephalo-calibration-assistant]')
    .getByRole('button',{name:/Calibrer manuellement|Modifier manuellement|Recalibrer manuellement/}).click();
  await page.getByText('Calibration manuelle',{exact:true}).waitFor({state:'visible'});
  await point(fixture.point_1);await point(fixture.point_2);
  await page.getByPlaceholder('Ex: 10').fill('20');
  await page.getByRole('button',{name:'Valider la distance'}).click();
  const future=page.waitForResponse(r=>r.request().method()==='POST'
      &&new URL(r.url()).pathname==='/api/ia/analyses/'+study+'/calibrate',{timeout:70000});
  await page.getByRole('button',{name:'Appliquer',exact:true}).click();
  const response=await future;
  ok(response.status()===200,'Calibration backend '+response.status()+' '+(await response.text()).slice(0,400));
  const saved=await detail(),p=response.request().postDataJSON();
  ok(saved.is_calibrated&&Math.abs(saved.mm_per_pixel-0.1)<0.002,
    'Constructed ruler ratio drift '+saved.mm_per_pixel);
  ok(p?.distance_mm===20&&Number.isFinite(p.p1?.x)&&Number.isFinite(p.p1?.y)
    &&Number.isFinite(p.p2?.x)&&Number.isFinite(p.p2?.y)
    &&Math.abs(Math.hypot(p.p2.x-p.p1.x,p.p2.y-p.p1.y)-200)<4,
    'UI calibration POST not bound to constructed 200px line: '+JSON.stringify(p));
  ok(saved.angles_data?.calibration_status==='verified',
    'Server projection did not expose verified synthetic scale');
  await shot('03-synthetic-calibration');
  return {design_ratio:saved.mm_per_pixel,submitted_distance_mm:p.distance_mm,
   ui_calibration_post_verified:true,db_calibration_provenance_checked_in_separate_ci:true,
   physical_patient_scale:false,clinical_claim:false};
 });
 await check('REAL_USER_WIZARD_STEPS_2_3_4',async()=>{
  for(let idx=1;idx<4;idx++){
   const tab=page.locator('[data-tour="cephalo-stepper"] > button').nth(idx);
   await tab.click();
   await page.waitForFunction(
     i=>document.querySelectorAll('[data-tour="cephalo-stepper"] > button')[i]?.getAttribute('aria-current')==='step',
     idx,{timeout:20000});
   ok((await tab.getAttribute('aria-current'))==='step','Failed transition to step '+(idx+1));
   await shot('04-step-'+(idx+1));
  }
  const draft=page.getByRole('button',{name:'Brouillon PDF'});
  await draft.waitFor({state:'visible'});
  ok(await draft.isEnabled(),'Document drafting not accessible');
  return {reached:[2,3,4],patient_approved:false};
 });
 await check('AUTHENTICATED_UNARCHIVED_DRAFT_PDF_STUDY_REVISION',async()=>{
  const future=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/patients/'+patient.patient_id+'/pdf'
   &&r.request().method()==='POST'&&r.request().postDataJSON()?.archive===false,{timeout:70000});
  const download=page.waitForEvent('download',{timeout:70000});
  await page.getByRole('button',{name:'Brouillon PDF'}).click();
  const r=await future,b=await r.body(),p=r.request().postDataJSON();
  ok(r.status()===200,'PDF HTTP '+r.status()+' '+b.toString().slice(0,220));
  ok(b.subarray(0,4).toString()==='%PDF'&&b.length>1500,'Invalid PDF bytes');
  ok(p.analysis_id===study&&Number.isSafeInteger(p.expected_revision)&&p.expected_revision>0&&p.archive===false,
    'PDF request not revision/study bound');
  ok(r.headers()['x-cephalo-analysis-id']===String(study)
    &&r.headers()['x-cephalo-revision']===String(p.expected_revision),'PDF response identity mismatch');
  const dl=await download;
  ok(dl.suggestedFilename().endsWith('.pdf'),'Draft download absent');
  report.pdf={study,revision:p.expected_revision,bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex'),
    archive:false,physical_scale:false};
  await fs.writeFile(path.join(out,'synthetic-unarchived-draft.pdf'),b);
  await shot('05-draft-pdf');
  return {revision:p.expected_revision,download:true,archive:false,bytes:b.length};
 });
 await check('REAL_PREVIEW_PDF_SAME_STUDY_NO_ARCHIVE',async()=>{
  const future=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/patients/'+patient.patient_id+'/pdf'
   &&r.request().method()==='POST'&&r.request().postDataJSON()?.archive===false,{timeout:70000});
  await page.getByRole('button',{name:'Prévisualiser'}).click();
  const r=await future,b=await r.body(),p=r.request().postDataJSON();
  ok(r.status()===200&&b.subarray(0,4).toString()==='%PDF','Preview PDF invalid');
  ok(p.analysis_id===study&&r.headers()['x-cephalo-analysis-id']===String(study)
   &&r.headers()['x-cephalo-revision']===String(p.expected_revision),'Preview identity incorrect');
  await shot('06-preview-pdf');
  return {same_study:true,unarchived:true,bytes:b.length};
 });
 report.overall='FUE_P2_FULL_WIZARD_PDF_SYNTHETIC_DESIGN_ONLY_NONCLINICAL_PASS';
}catch(e){report.errors.push('FATAL '+String(e));report.overall='FUE_P2_FAILED'}
finally{
 if(ctx)await ctx.close().catch(()=>{});
 await api.dispose();await browser.close();
 await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
 console.log('FUE_P2_RESULT',report.overall,JSON.stringify({head,study,passed:report.checks.filter(v=>v.status==='PASS').length,
   errors:report.errors,clinical_release:false,archived:false}));
 if(report.errors.length)process.exitCode=1;
}
