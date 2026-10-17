/** Real Cabinet UI login and real JWT FastAPI PDF, test-only disposable T2.
 * Browser is never pre-seeded with JWT. Uses legitimate station enrollment.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
const identities = JSON.parse(process.env.P2TER_STUDIES || '{}');
const isolated = process.env.ENVIRONMENT === 'test' && process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1';
if (!isolated || !/^[a-f0-9]{40}$/.test(head||'') || !password ||
    ![identities.patient_id, identities.older_id, identities.latest_id].every(Number.isSafeInteger) ||
    identities.older_id >= identities.latest_id)
  throw Error('P2ter authentic desktop proof requires isolated T2 and two selected versioned studies');

const output=path.resolve('../artifacts/ceph-p2ter-authenticated-desktop');
await fs.mkdir(output,{recursive:true});
const run={head,mode:'REAL CABINET LOGIN + REAL FASTAPI JWT + SYNTHETIC STUDIES ONLY',
  type:'DESKTOP_E2E_NOT_FACAD_OR_CLINICAL',viewports:[],facad_action_executed:false,
  clinical_release:false,patient_real:false};
const browser=await chromium.launch({headless:true});
const root='http://127.0.0.1:5173', backend='http://127.0.0.1:8005';

async function viewportRun(viewport){
 const record={viewport:viewport.width+'x'+viewport.height,checks:[],shots:[],pageErrors:[],valid:false};
 const api=await request.newContext({baseURL:backend});
 let context;
 try{
  const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
  if(login.status()!==200)throw Error('Bootstrap auth failed '+login.status());
  const token=(await login.json()).access_token;
  const enrolled=await enrollT2Workstation(api,token,password);
  const station=enrolled.cookies.filter(c=>c.name==='dc_workstation');
  if(station.length!==1)throw Error('Workstation enrollment missing');
  context=await browser.newContext({viewport,acceptDownloads:true,reducedMotion:'reduce',
    storageState:{cookies:station,origins:[]}});
  const page=await context.newPage();
  page.on('pageerror',e=>record.pageErrors.push(e.message));
  const shot=async name=>{
   const filename=record.viewport+'-'+name+'.png';
   await page.screenshot({path:path.join(output,filename),fullPage:false,animations:'disabled'});
   record.shots.push(filename);
  };
  await page.goto(root+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
  await page.locator('[data-hub-experience="cabinet"]').click();
  await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
  if(!await page.evaluate(()=>Boolean(localStorage.getItem('token'))))
    throw Error('No actual authenticated cabinet browser session');
  record.checks.push('REAL_UI_LOGIN');
  await page.goto(root+'/patients/'+identities.patient_id+'?tab=radiology&radioTab=cephalo',
    {waitUntil:'domcontentloaded',timeout:45000});
  await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:35000});
  await shot('before-history');
  for(const [label,study] of [['older',identities.older_id],['newer',identities.latest_id]]){
   await page.getByRole('button',{name:'Historique',exact:true}).click();
   const card=page.locator('[data-cephalo-history-analysis-id="'+study+'"]');
   await card.waitFor({state:'visible',timeout:20000});
   await card.click();
   await page.locator('[data-cephalo-selected-analysis-id="'+study+'"]').waitFor({state:'visible',timeout:15000});
   record.checks.push('SELECT_'+label.toUpperCase()+'_STUDY_'+study);
   await shot(label+'-selected');
   await page.getByRole('button',{name:'4. Documents & stratégie',exact:true}).click();
   const draft=page.getByRole('button',{name:'Brouillon PDF'});
   await draft.waitFor({state:'visible',timeout:20000});
   const responsePromise=page.waitForResponse(r=>{
     const u=new URL(r.url());return u.pathname==='/api/patients/'+identities.patient_id+'/pdf'
       && r.request().method()==='POST';
   },{timeout:30000});
   await draft.click();
   const response=await responsePromise;
   const body=response.request().postDataJSON();
   if(body.analysis_id!==study || !Number.isSafeInteger(body.expected_revision) ||
       body.expected_revision<=0 || body.archive!==false)
     throw Error('Wrong analysis request identity from Cabinet UI '+label);
   if(response.status()!==200)throw Error('Cabinet PDF HTTP '+response.status()+': '+(await response.text()).slice(0,300));
   const headers=response.headers();
   if(headers['x-cephalo-analysis-id']!==String(study) ||
       headers['x-cephalo-revision']!==String(body.expected_revision))
     throw Error('Cabinet returned wrong study or revision '+label);
   const pdf=await response.body();
   if(pdf.subarray(0,4).toString('latin1')!=='%PDF')throw Error('Not a PDF binary '+label);
   await fs.writeFile(path.join(output,record.viewport+'-'+label+'-selected-study.pdf'),pdf);
   await shot(label+'-pdf-finished');
   record.checks.push('REAL_JWT_HTTP_PDF_'+label.toUpperCase()+'_STUDY_'+study+'_REV_'+body.expected_revision);
  }
  if(record.pageErrors.length)throw Error('React exceptions '+JSON.stringify(record.pageErrors));
  record.valid=true;
 }catch(error){record.error=String(error);}
 finally{await context?.close().catch(()=>{});await api.dispose();}
 return record;
}
try{
 for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
  run.viewports.push(await viewportRun(viewport));
 }
}finally{
 await browser.close();
 await fs.writeFile(path.join(output,'report.json'),JSON.stringify(run,null,2));
}
if(run.viewports.some(r=>!r.valid)||run.viewports.length!==2)
 throw Error('Authenticated cabinet E2E NOT certified: '+JSON.stringify(run.viewports.map(({viewport,error,checks})=>({viewport,error,checks}))));
console.log('P2TER_AUTHENTICATED_CABINET_E2E_SUCCESS',JSON.stringify(run.viewports.map(({viewport,checks})=>({viewport,checks}))));
