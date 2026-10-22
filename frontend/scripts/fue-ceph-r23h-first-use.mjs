/** Independent FUE-H: authentic first-file-chooser UX with certified ONNX,
 * real JPEG bytes, persistent studies and unauthorized account denials.
 * No mock server, landmark injection, fake calibration or clinical signoff.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {chromium, request} from 'playwright';
import {enrollT2Workstation} from './t2-workstation-session.mjs';

const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const head=process.env.PRODUCT_HEAD,password=process.env.T2_PASSWORD;
const test=JSON.parse(process.env.CEPH_R23H_PATIENT||'{}');
if(process.env.ENVIRONMENT!=='test'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
 ||process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db'
 ||!password||!/^[a-f0-9]{40}$/.test(head||'')||test.initial_studies!==0
 ||!Number.isSafeInteger(test.patient_id)||test.clinical_release!==false)
 throw Error('Refusing non-disposable or pre-filled FUE-H');
const specs=[
 {name:'anug',file:'anug.jpg',width:2272,height:1818,hash:'ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6'},
 {name:'challiyan',file:'challiyan.jpg',width:1000,height:1255,hash:'98c6384dd9cc392ac54bf365173e522a4860ce55a64b8b15e87485dbcc30371b'},
];
const dir=process.env.CEPH_PUBLIC_SOURCE_DIR||'/tmp/ceph-public-originals';
const out=path.resolve('../artifacts/ceph-r23h-first-use');
await fs.mkdir(out,{recursive:true});
const report={head,clinical_release:false,scientific_goldset:false,patient_real:false,
 case_ids:[],checks:[],errors:[],screenshots:[],overall:'NOT_TESTED'};
const browser=await chromium.launch({headless:true});
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
let page,ctx,token;
function ensure(value,error){if(!value)throw Error(error)}
async function shot(name){if(!page)return;const file=name+'.png';await page.screenshot({path:path.join(out,file),animations:'disabled'});report.screenshots.push(file)}
async function check(id,fn){
 try{const evidence=await fn();report.checks.push({id,status:'PASS',evidence:evidence||null});console.log('R23H_PASS',id)}
 catch(e){report.checks.push({id,status:'FAIL',error:String(e)});report.errors.push(id+': '+String(e));console.log('R23H_FAIL',id,String(e));await shot('fail-'+id).catch(()=>{});throw e;}
}
const sourcePath=spec=>path.join(dir,spec.file);
async function visibleImage(spec){
 await page.waitForFunction(()=>Boolean(document.querySelector('svg[data-cephalo-viewport="base"] image')?.getAttribute('href')?.startsWith('blob:')),null,{timeout:60000});
 const image=await page.evaluate(async()=>{
   const url=document.querySelector('svg[data-cephalo-viewport="base"] image').getAttribute('href');
   const img=new Image();img.src=url;await img.decode();
   const bytes=await(await fetch(url)).arrayBuffer();
   const hash=await crypto.subtle.digest('SHA-256',bytes);
   return {width:img.naturalWidth,height:img.naturalHeight,hash:[...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('')};
 });
 ensure(image.hash===spec.hash&&image.width===spec.width&&image.height===spec.height,
  'Displayed image bytes/dimensions differ from original '+JSON.stringify(image));
 return image;
}
try {
 await check('BLANK_FIRST_USE_AND_VERIFIED_ORIGINALS',async()=>{
   for(const spec of specs)ensure(sha(await fs.readFile(sourcePath(spec)))===spec.hash,'Original sha mismatch');
   const r=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
   ensure(r.status()===200,'Dentist login rejected');
   token=(await r.json()).access_token;
   const list=await api.get('/api/ia/patients/'+test.patient_id+'/cephalo-analyses',{headers:{Authorization:'Bearer '+token}});
   ensure(list.status()===200&&(await list.json()).length===0,'Fresh patient already has studies');
   return {initial_studies:0};
 });
 await check('GENUINE_FIRST_BROWSER_CABINET_AND_UPLOAD_WIDGET',async()=>{
   const station=await enrollT2Workstation(api,token,password);
   ctx=await browser.newContext({viewport:{width:1280,height:900},
    storageState:{cookies:station.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
   page=await ctx.newPage();page.setDefaultTimeout(35000);
   await page.goto('http://127.0.0.1:5173/hub?select=1',{waitUntil:'domcontentloaded'});
   await page.locator('[data-hub-experience="cabinet"]').click();
   await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
   await page.locator('input[type=password]').fill(password);
   await page.getByRole('button',{name:'Se connecter',exact:true}).click();
   await page.waitForURL(x=>new URL(x).pathname==='/dashboard',{timeout:45000});
   await page.getByRole('button',{name:'Chercher un patient'}).click();
   await page.getByRole('textbox',{name:'Chercher un patient'}).fill('RADIO-PUBLIQUE');
   await page.locator('#dashboard-patient-search-results button').filter({hasText:'T2-FUEH-0001'}).click();
   await page.waitForURL(x=>new URL(x).pathname==='/patients/'+test.patient_id);
   await page.getByRole('button',{name:'Imagerie',exact:true}).click();
   await page.locator('[aria-label="Modalités d’imagerie"]').getByRole('button',{name:'Céphalométrie',exact:true}).click();
   await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
   await page.locator('input[type=file][accept="image/jpeg,image/png"]').waitFor({state:'attached'});
   await shot('01-before-first-file');
   return {fresh:true,patient_id:test.patient_id};
 });
 for(const spec of specs){
   await check(spec.name.toUpperCase()+'_REAL_UI_UPLOAD_WITH_PINNED_ONNX',async()=>{
     if(spec.name==='challiyan'){
       await page.getByTitle("Changer d'image").click();
       await page.locator('input[type=file][accept="image/jpeg,image/png"]').waitFor({state:'attached'});
     }
     const future=page.waitForResponse(r=>{
       const u=new URL(r.url());
       return u.pathname==='/api/ia/upload-radio'
         &&u.searchParams.get('patient_id')===String(test.patient_id)
         &&r.request().method()==='POST';
     },{timeout:240000});
     await page.locator('input[type=file][accept="image/jpeg,image/png"]').setInputFiles(sourcePath(spec));
     const response=await future;
     const body=await response.text();
     ensure(response.status()===200,'TRUE UI IMPORT BLOCKED HTTP '+response.status()+' '+body.slice(0,220));
     const payload=JSON.parse(body);
     ensure(Number.isSafeInteger(payload.analysis_id),'No persisted study ID');
     ensure(payload.is_calibrated===false&&payload.mm_per_pixel==null,'Invalid automatic calibration claim');
     ensure(payload.landmarks?.length===38&&payload.results?.vision_metadata?.mode_inference==='SOTA_ONNX_38',
       'Actual certified ONNX38 inference not performed');
     ensure(!report.case_ids.includes(payload.analysis_id),'Second upload reused first study');
     report.case_ids.push(payload.analysis_id);
     const imagePath=payload.image_path;
     ensure(/^api\/static\/uploads\/radios\/[a-z0-9-]+\.jpg$/i.test(imagePath),'Unexpected image path');
     const media=await api.get('/'+imagePath,{headers:{Authorization:'Bearer '+token}});
     ensure(media.status()===200&&sha(await media.body())===spec.hash,'Protected original bytes changed');
     const detail=await api.get('/api/ia/analyses/'+payload.analysis_id,{headers:{Authorization:'Bearer '+token}});
     ensure(detail.status()===200,'Persisted study inaccessible');
     const stored=await detail.json();
     ensure(stored.image_original_path===imagePath&&stored.is_calibrated===false
       &&stored.mm_per_pixel==null&&stored.landmarks_data?.length===38
       &&stored.angles_data?.vision_metadata?.mode_inference==='SOTA_ONNX_38',
       'Persistence or actual source/model provenance mismatch');
     const displayed=await visibleImage(spec);
     await shot('02-real-upload-'+spec.name);
     return {study_id:payload.analysis_id,actual_onnx_landmarks:38,displayed_hash:displayed.hash,calibration_verified:false};
   });
 }
 await check('RESTRICTED_AND_OTHER_CABINET_CANNOT_READ',async()=>{
   const study=report.case_ids[0];
   const owner=await api.get('/api/ia/analyses/'+study,{headers:{Authorization:'Bearer '+token}});
   const imagePath=(await owner.json()).image_original_path;
   const result={};
   for(const [label,email] of [['restricted','t2-restricted@cabinet.ma'],['other_cabinet','t2-setup-1280@cabinet.ma']]){
     // SECURITY: each user requires a brand-new HTTP context with an EMPTY
     // cookie jar. Reusing 'api' keeps the dentist cookie despite outsider
     // Authorization, which is an invalid cross-cabinet security assertion.
     const outsiderApi=await request.newContext({baseURL:'http://127.0.0.1:8005'});
     try {
       const r=await outsiderApi.post('/api/auth/login',{form:{username:email,password}});
       ensure(r.status()===200,label+' login failed');
       const outsider=(await r.json()).access_token;
       const a=await outsiderApi.get('/api/ia/analyses/'+study,{headers:{Authorization:'Bearer '+outsider}});
       const m=await outsiderApi.get('/'+imagePath,{headers:{Authorization:'Bearer '+outsider}});
       ensure([401,403,404].includes(a.status())&&[401,403,404].includes(m.status()),
         label+' REALLY LEAKED on cookie-isolated session: study='+a.status()+' media='+m.status());
       result[label]={study:a.status(),image:m.status()};
     }finally{await outsiderApi.dispose();}
   }
   return result;
 });
 await check('FRESH_SECOND_BROWSER_REOPEN_BOTH_SOURCES',async()=>{
   await ctx.close();ctx=null;page=null;
   const station=await enrollT2Workstation(api,token,password);
   ctx=await browser.newContext({viewport:{width:1600,height:1000},
      storageState:{cookies:station.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
   page=await ctx.newPage();
   await page.goto('http://127.0.0.1:5173/patients/'+test.patient_id+'?tab=radiology&radioTab=cephalo',{waitUntil:'domcontentloaded'});
   await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:40000});
   for(const i of [1,0]){
     await page.getByRole('button',{name:'Historique',exact:true}).click();
     await page.locator('[data-cephalo-history-analysis-id="'+report.case_ids[i]+'"]').click();
     await page.locator('[data-cephalo-selected-analysis-id="'+report.case_ids[i]+'"]').waitFor({state:'visible'});
     await visibleImage(specs[i]);
     await shot('03-reopen-'+specs[i].name);
   }
   return {new_browser:true,studies:report.case_ids.slice().reverse()};
 });
 report.overall='FUE_H_REAL_UI_ONNX_PERSISTENCE_SECURITY_PASS_NONCLINICAL';
}catch(e){report.overall='FUE_H_FAILED';if(!report.errors.some(x=>x.includes(String(e))))report.errors.push(String(e))}
finally{
 if(ctx)await ctx.close().catch(()=>{});
 await api.dispose();await browser.close();
 await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
 console.log('R23H_RESULT',report.overall,JSON.stringify({head,passed:report.checks.filter(x=>x.status==='PASS').length,failed:report.checks.filter(x=>x.status==='FAIL').map(x=>x.id),studies:report.case_ids.length,errors:report.errors}));
 if(report.overall==='FUE_H_FAILED')process.exitCode=1;
}
