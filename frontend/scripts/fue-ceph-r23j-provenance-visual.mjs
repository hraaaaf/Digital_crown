/** R23-J — verify source-specific neutral authority labels on ACTUAL H radios.
 * Runs after full independent H, never replaces real model with mocked output.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {chromium, request} from 'playwright';
import {enrollT2Workstation} from './t2-workstation-session.mjs';

if(process.env.ENVIRONMENT!=='test'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
 ||process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db'
 ||!/^[a-f0-9]{40}$/.test(process.env.PRODUCT_HEAD||'')
 ||!process.env.T2_PASSWORD||!process.env.CEPH_R23H_PATIENT)
  throw Error('R23-J refuses anything except isolated exact-HEAD T2');
const fixture=JSON.parse(process.env.CEPH_R23H_PATIENT);
const h=JSON.parse(await fs.readFile('../artifacts/ceph-r23h-first-use/report.json','utf8'));
if(h.overall!=='FUE_H_REAL_UI_ONNX_PERSISTENCE_SECURITY_PASS_NONCLINICAL'
  ||h.head!==process.env.PRODUCT_HEAD||h.case_ids?.length!==2)
  throw Error('No exact-HEAD real first-use runtime FUE-H to compare');
const out=path.resolve('../artifacts/ceph-r23j-visual');
await fs.mkdir(out,{recursive:true});
const report={head:process.env.PRODUCT_HEAD,source_h:h.overall,
 clinical_release:false,checks:[],screenshots:[],errors:[],overall:'NOT_TESTED'};
const req=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const browser=await chromium.launch({headless:true});
let page,ctx;
const ensure=(c,m)=>{if(!c)throw Error(m)};
const shot=async name=>{
 const file=name+'.png';await page.screenshot({path:path.join(out,file),animations:'disabled'});report.screenshots.push(file);
};
async function check(id,fn){
 try{const ev=await fn();report.checks.push({id,status:'PASS',evidence:ev});console.log('R23J_VISUAL_PASS',id);}
 catch(e){report.checks.push({id,status:'FAIL',reason:String(e)});report.errors.push(id+': '+String(e));console.log('R23J_VISUAL_FAIL',id,String(e));if(page)await shot('FAIL-'+id).catch(()=>{});throw e;}
}
try{
 const login=await req.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password:process.env.T2_PASSWORD}});
 ensure(login.status()===200,'T2 real dentist auth fail');
 const jwt=(await login.json()).access_token;
 const station=await enrollT2Workstation(req,jwt,process.env.T2_PASSWORD);
 const workstationCookies=station.cookies.filter(x=>x.name==='dc_workstation');
 ensure(workstationCookies.length===1,'workstation missing');
 for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
   const vp=viewport.width+'x'+viewport.height;
   ctx=await browser.newContext({viewport,
      storageState:{cookies:workstationCookies,origins:[]}});
   page=await ctx.newPage();page.setDefaultTimeout(35000);
   await check(vp+'_FULL_LOGIN',async()=>{
     await page.goto('http://127.0.0.1:5173/hub?select=1',{waitUntil:'domcontentloaded'});
     await page.locator('[data-hub-experience="cabinet"]').click();
     await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
     await page.locator('input[type=password]').fill(process.env.T2_PASSWORD);
     await page.getByRole('button',{name:'Se connecter',exact:true}).click();
     await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
     await page.getByRole('button',{name:'Chercher un patient'}).click();
     await page.getByRole('textbox',{name:'Chercher un patient'}).fill('RADIO-PUBLIQUE');
     await page.locator('#dashboard-patient-search-results button').filter({hasText:'T2-FUEH-0001'}).click();
     await page.getByRole('button',{name:'Imagerie',exact:true}).click();
     await page.locator('[aria-label="Modalités d’imagerie"]')
       .getByRole('button',{name:'Céphalométrie',exact:true}).click();
     await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
     return {patient_id:fixture.patient_id,real_browser:true};
   });
   for(const [i,caseName] of ['anug','challiyan'].entries()){
     await check(vp+'_'+caseName.toUpperCase()+'_RAW_NOT_CLINICALLY_APPROVED',async()=>{
       const studyId=h.case_ids[i];
       await page.getByRole('button',{name:'Historique',exact:true}).click();
       await page.locator('[data-cephalo-history-analysis-id="'+studyId+'"]').click();
       await page.locator('[data-cephalo-selected-analysis-id="'+studyId+'"]').waitFor({state:'visible'});
       const select=page.locator('#cephalo-ready-analysis');
       await select.selectOption('all');
       const banner=page.locator('[data-r23j-provenance="AUTOMATIC_SRPOSE38_UNREVIEWED"]');
       await banner.waitFor({state:'visible'});
       const body=await banner.innerText();
       ensure(body.includes('SRPose38')&&body.includes('Étude #'+studyId)
         &&body.includes('non attestée')&&body.includes('non validées cliniquement'),
         'Source or human-review state not visibly explicit: '+body);
       const count=page.locator('[data-r23j-raw-metric-count]');
       await count.waitFor({state:'visible'});
       const countText=await count.innerText();
       const found=countText.match(/^(\d+)\/15 mesures brutes calculées$/);
       ensure(found&&Number(found[1])>0,'Raw numerical angular observations disappeared: '+countText);
       const metric=page.locator('[data-r23j-metric-authority="UNREVIEWED"]');
       await metric.waitFor({state:'visible'});
       ensure((await metric.innerText()).includes('non validée cliniquement'),
         'Numeric detail falsely approved');
       ensure(await metric.locator('svg.lucide-check-circle-2,svg.lucide-circle-check-big').count()===0,
         'Unreviewed numeric displayed with an apparent green check');
       await shot('R23J-'+vp+'-'+caseName+'-raw-source');
       return {study_id:studyId,source:'SOTA_ONNX_38',automatic:true,
         raw_count:Number(found[1]),clinician_validated:false,photo:caseName};
     });
   }
   await ctx.close();ctx=null;page=null;
 }
 report.overall='R23J_REAL_PUBLIC_VISUAL_PROVENANCE_PASS_NONCLINICAL';
}catch(e){
 report.overall='R23J_FAIL';if(!report.errors.some(x=>x.includes(String(e))))report.errors.push(String(e));
}finally{
 if(ctx)await ctx.close().catch(()=>{});
 await browser.close();await req.dispose();
 await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
 console.log('R23J_REAL_BROWSER_RESULT',JSON.stringify({
    result:report.overall,checks:report.checks.length,errors:report.errors,
    head:report.head,clinical_release:false}));
 if(report.overall!=='R23J_REAL_PUBLIC_VISUAL_PROVENANCE_PASS_NONCLINICAL')process.exitCode=1;
}
