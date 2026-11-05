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
 case_ids:[],checks:[],errors:[],screenshots:[],svg_screenshots:[],react_steiner:[],fullfilm_review:[],overall:'NOT_TESTED'};
const sourceLockedSnapshots=[];
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
     // Independently persisted, authenticated GET snapshot — never invent landmarks.
     const persistedPoints=stored.landmarks_data.map(p=>({id:p.id,x:p.x,y:p.y}));
     ensure(persistedPoints.length===38&&new Set(persistedPoints.map(p=>p.id)).size===38
       &&persistedPoints.every(p=>typeof p.id==='string'&&Number.isFinite(p.x)&&Number.isFinite(p.y)
         &&p.x>=0&&p.x<spec.width&&p.y>=0&&p.y<spec.height),
       'Cannot audit 38 complete landmarks in native-image coordinates');
     sourceLockedSnapshots.push({
       radio:spec.name,source_image_sha256:spec.hash,source_name:spec.file,
       source_width:spec.width,source_height:spec.height,study_id:payload.analysis_id,
       inference_mode:'SOTA_ONNX_38',is_calibrated:false,mm_per_pixel:null,
       landmarks:persistedPoints,
     });
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
     // Staff uses the CABINET OWNER'S already-enrolled workstation (normal
     // shared office device), but authenticates as an independent secretary.
     // Another cabinet owner enrolls their OWN new test workstation.
     const sameCabinetCookies=(await api.storageState()).cookies
       .filter(c=>c.name==='dc_workstation');
     const opts=label==='restricted'
       ?{baseURL:'http://127.0.0.1:8005',storageState:{cookies:sameCabinetCookies,origins:[]}}
       :{baseURL:'http://127.0.0.1:8005'};
     const outsiderApi=await request.newContext(opts);
     try {
       const r=await outsiderApi.post('/api/auth/login',{form:{username:email,password}});
       ensure(r.status()===200,label+' login failed');
       const outsider=(await r.json()).access_token;
       if(label==='other_cabinet'){
         const outsiderStation=await enrollT2Workstation(outsiderApi,outsider,password);
         ensure(outsiderStation.cookies.some(c=>c.name==='dc_workstation'),
           'second cabinet workstation not enrolled');
       } else {
         ensure(sameCabinetCookies.length===1,'owner workstation provenance missing');
       }
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
   // A fresh browser must authenticate again through the genuine Cabinet UI.
   // The workstation cookie alone is NOT a user login/session token.
   await page.goto('http://127.0.0.1:5173/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
   await page.locator('[data-hub-experience="cabinet"]').waitFor({state:'visible'});
   await page.locator('[data-hub-experience="cabinet"]').click();
   await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
   await page.locator('input[type=password]').fill(password);
   await page.getByRole('button',{name:'Se connecter',exact:true}).click();
   await page.waitForURL(x=>new URL(x).pathname==='/dashboard',{timeout:45000});
   await page.goto('http://127.0.0.1:5173/patients/'+test.patient_id+'?tab=radiology&radioTab=cephalo',{waitUntil:'domcontentloaded'});
   await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:40000});
   for(const i of [1,0]){
     await page.getByRole('button',{name:'Historique',exact:true}).click();
     await page.locator('[data-cephalo-history-analysis-id="'+report.case_ids[i]+'"]').click();
     await page.locator('[data-cephalo-selected-analysis-id="'+report.case_ids[i]+'"]').waitFor({state:'visible'});
     await visibleImage(specs[i]);
     const fresh=await api.get('/api/ia/analyses/'+report.case_ids[i],{headers:{Authorization:'Bearer '+token}});
     ensure(fresh.status()===200,'Reopened study not independently readable by authenticated GET');
     const persisted=await fresh.json();
     const locked=sourceLockedSnapshots.find(p=>p.radio===specs[i].name);
     ensure(locked&&JSON.stringify(persisted.landmarks_data.map(p=>({id:p.id,x:p.x,y:p.y})))
       ===JSON.stringify(locked.landmarks)&&persisted.is_calibrated===false
       &&persisted.mm_per_pixel==null,'Full-film source points changed during reopen');
     await shot('03-reopen-'+specs[i].name);
     // Actual Digital Crown SVG screenshot. Kept separately from the audited
     // pixel-accurate full-film board to prevent conflating UI and audit views.
     const svg=page.locator('svg[data-cephalo-viewport="base"]');
     await svg.waitFor({state:'visible',timeout:20000});
     const uiFile='04-ui-svg-'+specs[i].name+'.png';
     await svg.screenshot({path:path.join(out,uiFile),animations:'disabled',timeout:20000});
     report.svg_screenshots.push(uiFile);
     // This is the REAL native React SVG, using persisted GET landmarks,
     // not the external Python drawing or a synthetic feature-point overlay.
     const selector=page.locator('#cephalo-ready-analysis');
     await selector.waitFor({state:'visible'});
     const selectable=await selector.locator('option').evaluateAll(nodes=>
       nodes.filter(n=>!n.disabled).map(n=>n.value));
     ensure(JSON.stringify(selectable)===JSON.stringify(['com','steiner']),
       'Unexpected V1 selectable modes: '+JSON.stringify(selectable));
     await selector.selectOption('steiner');
     await page.locator('[data-cephalo-analysis="steiner"]').waitFor({state:'visible'});
     for(const id of ['sn','na','nb'])
       await svg.locator('[data-cephalo-line-key="'+id+'"]').first()
         .waitFor({state:'attached',timeout:20000});
     const rendered=await svg.locator('[data-cephalo-line-key]').evaluateAll(nodes=>
       nodes.map(node=>({id:node.getAttribute('data-cephalo-line-key'),
         x1:Number(node.getAttribute('x1')),y1:Number(node.getAttribute('y1')),
         x2:Number(node.getAttribute('x2')),y2:Number(node.getAttribute('y2'))})));
     const originalPoints=new Map(locked.landmarks.map(p=>[p.id.toLowerCase(),p]));
     const near=(line,p,q)=>Math.hypot(line.x1-p.x,line.y1-p.y)<0.05
       &&Math.hypot(line.x2-q.x,line.y2-q.y)<0.05;
     const segments=[];
     for(const [id,from,to] of [['sn','s','n'],['na','n','a'],['nb','n','b']]){
       const p=originalPoints.get(from),q=originalPoints.get(to);
       ensure(p&&q,'Source GET points missing for '+id);
       const line=rendered.find(l=>l.id===id&&near(l,p,q));
       ensure(line,'Native React SVG line differs from source GET for '+id);
       segments.push({...line,from,to});
     }
     const whole='05-real-react-steiner-'+specs[i].name+'.png';
     const native='06-real-react-steiner-svg-'+specs[i].name+'.png';
     await page.screenshot({path:path.join(out,whole),animations:'disabled'});
     await svg.screenshot({path:path.join(out,native),animations:'disabled',timeout:20000});
     report.screenshots.push(whole);
     report.svg_screenshots.push(native);
     report.react_steiner.push({radio:specs[i].name,study_id:report.case_ids[i],
       source_image_sha256:specs[i].hash,renderer:'DIGITAL_CROWN_AUTHENTICATED_REACT_SVG',
       source_lock:'AUTHENTICATED_GET_AFTER_REAL_UI_UPLOAD',model:'SOTA_ONNX_38',
       uncalibrated:true,expert_verified:false,line_segments:segments,
       screenshot:whole,svg_screenshot:native});
     console.log('R23H_NATIVE_REACT_STEINER',specs[i].name,
       'SEGMENTS_SN_NA_NB_SOURCE_LOCKED_NONCLINICAL');
   }
   return {new_browser:true,studies:report.case_ids.slice().reverse(),
     native_react_steiner:report.react_steiner.map(v=>v.radio)};
 });
 ensure(sourceLockedSnapshots.length===2&&report.svg_screenshots.length===4
   &&report.react_steiner.length===2,
   'Missing source-locked real-landmark data or genuine native Steiner screenshots');
 await fs.writeFile(path.join(out,'source-locked-38-points.json'),
   JSON.stringify({
     head,clinical_authority:false,model_sha256:'a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb',
     source:'EXACT_SHA_AUTHENTICATED_GET_AFTER_REAL_UI_IMPORT',cases:sourceLockedSnapshots,
   },null,2));
 report.fullfilm_review=sourceLockedSnapshots.map(p=>({
   radio:p.radio,landmark_count:p.landmarks.length,source_image_sha256:p.source_image_sha256,
   study_id:p.study_id,source:'AUTHENTICATED_GET',clinical_accuracy_evaluated:false,
 }));
 report.overall='FUE_H_REAL_UI_ONNX_PERSISTENCE_SECURITY_PASS_NONCLINICAL';
}catch(e){report.overall='FUE_H_FAILED';if(!report.errors.some(x=>x.includes(String(e))))report.errors.push(String(e))}
finally{
 if(ctx)await ctx.close().catch(()=>{});
 await api.dispose();await browser.close();
 await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
 console.log('R23H_RESULT',report.overall,JSON.stringify({head,passed:report.checks.filter(x=>x.status==='PASS').length,failed:report.checks.filter(x=>x.status==='FAIL').map(x=>x.id),studies:report.case_ids.length,errors:report.errors}));
 if(report.overall==='FUE_H_FAILED')process.exitCode=1;
}
