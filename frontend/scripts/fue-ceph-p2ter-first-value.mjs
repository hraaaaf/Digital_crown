/** Experimental P2ter++ FUE-I, fresh Cabinet browser personas on synthetic T2.
 * Runs after the authenticated desktop tests seeded two verified archives.
 * Does not pretend to represent an unsupervised clinician or a blank patient.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
const ids = JSON.parse(process.env.P2TER_STUDIES || '{}');
if (process.env.ENVIRONMENT !== 'test' || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || !/^[a-f0-9]{40}$/.test(head || '') || !password
    || ![ids.patient_id, ids.older_id].every(Number.isSafeInteger)) {
  throw Error('FUE-I requires exact HEAD and disposable T2 patient/study/JWT environment');
}
const root='http://127.0.0.1:5173';
const backend='http://127.0.0.1:8005';
const output=path.resolve('../artifacts/ceph-p2ter-fue-i');
await fs.mkdir(output,{recursive:true});
const report={
  head,classification:'FUE-I',scope:'CEPH-FAC-PARITY/P2ter++',
  persona:'first-time Cabinet dentist with an existing synthetic versioned study',
  fixture:'disposable T2; official archive already created by the desktop certification',
  firstValue:'genuine study/revision-bound PDF draft downloaded, followed by official archive replay',
  exclusions:['real first patient creation','real medical records','clinical signoff','server persistence of patient photos',
    'production or mobile native app','genuine independent clinical/human audit'],
  viewports:[],overall:'NOT_TESTED',
};
const browser=await chromium.launch({headless:true});
const matrixIDs=[
  'CLEAN_BROWSER_LOGIN','OPEN_CEPHALO','SELECT_OLDER_STUDY',
  'RESPONSIVE_STEPPER','NO_HORIZONTAL_VIEWPORT_OVERFLOW',
  'DRAFT_PDF_FIRST_VALUE','OFFICIAL_ARCHIVE_REPLAY',
];
async function viewportRun(viewport) {
  const label=viewport.width+'x'+viewport.height;
  const record={viewport:label,platform:viewport.width<768?'responsive-mobile-web':'desktop-web',
    matrix:[],screenshots:[],errors:[],firstValue:null,score:null,valid:false};
  const api=await request.newContext({baseURL:backend});
  let context,page;
  const shot=async name=>{
    if(!page) return;
    const file=label+'-'+name+'.png';
    await page.screenshot({path:path.join(output,file),fullPage:false,animations:'disabled'});
    record.screenshots.push(file);
  };
  const run=async (id,action)=>{
    const start=Date.now();
    try {
      const evidence=await action();
      record.matrix.push({id,status:'PASS',duration_ms:Date.now()-start,evidence:evidence??null});
      return true;
    } catch(error) {
      const message=String(error);
      record.matrix.push({id,status:'FAIL',duration_ms:Date.now()-start,error:message});
      record.errors.push(id+': '+message);
      try {await shot('failure-'+id.toLowerCase());}catch{}
      return false;
    }
  };
  let ready=true;
  try {
    const auth=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
    if(auth.status()!==200)throw Error('T2 bootstrap login HTTP '+auth.status());
    const token=(await auth.json()).access_token;
    const station=await enrollT2Workstation(api,token,password);
    const cookies=station.cookies.filter(c=>c.name==='dc_workstation');
    if(cookies.length!==1)throw Error('Cabinet workstation cookie absent');
    context=await browser.newContext({viewport,reducedMotion:'reduce',
      acceptDownloads:true,storageState:{cookies,origins:[]}});
    page=await context.newPage();
    page.on('pageerror',err=>record.errors.push('PAGEERROR: '+err.message));
    await page.goto(root+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
    await shot('before-hub');
    ready=await run('CLEAN_BROWSER_LOGIN',async()=>{
      if(await page.evaluate(()=>Boolean(localStorage.getItem('token'))))throw Error('FUE browser is not initially fresh');
      await page.locator('[data-hub-experience="cabinet"]').click();
      await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button',{name:'Se connecter',exact:true}).click();
      await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
      if(!await page.evaluate(()=>Boolean(localStorage.getItem('token'))))throw Error('Cabinet login did not establish session');
      await shot('after-login');
      return 'Real UI login, disposable JWT and enrolled Cabinet workstation';
    });
    if(ready) ready=await run('OPEN_CEPHALO',async()=>{
      await page.goto(root+'/patients/'+ids.patient_id+'?tab=radiology&radioTab=cephalo',
        {waitUntil:'domcontentloaded',timeout:45000});
      await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:35000});
      await shot('before-select-study');
      return 'Cephalometry header visible with patient identifier';
    });
    if(ready) ready=await run('SELECT_OLDER_STUDY',async()=>{
      await page.getByRole('button',{name:'Historique',exact:true}).click();
      await page.locator('[data-cephalo-history-analysis-id="'+ids.older_id+'"]').click();
      await page.locator('[data-cephalo-selected-analysis-id="'+ids.older_id+'"]').waitFor({state:'visible',timeout:30000});
      await shot('after-study-selected');
      return 'Real UI selected study '+ids.older_id;
    });
    if(ready) ready=await run('RESPONSIVE_STEPPER',async()=>{
      if(viewport.width<768){
        const selector=page.locator('[data-cephalo-mobile-step-selector]');
        await selector.waitFor({state:'visible',timeout:10000});
        await selector.selectOption('4');
        await page.getByRole('button',{name:'Brouillon PDF'}).waitFor({state:'visible',timeout:35000});
      }else{
        const step=page.getByRole('button',{name:'4. Documents & stratégie',exact:true});
        await step.click();
        await page.getByRole('button',{name:'Brouillon PDF'}).waitFor({state:'visible',timeout:35000});
      }
      await shot('before-first-value');
      return viewport.width<768?'Native responsive web select -> Step4':'Desktop Step4 button';
    });
    if(ready) await run('NO_HORIZONTAL_VIEWPORT_OVERFLOW',async()=>{
      const dimensions=await page.evaluate(()=>({
        innerWidth:window.innerWidth,
        bodyScroll:document.body.scrollWidth,
        htmlScroll:document.documentElement.scrollWidth,
      }));
      if(Math.max(dimensions.bodyScroll,dimensions.htmlScroll)>dimensions.innerWidth+2)
        throw Error('Horizontal overflow: '+JSON.stringify(dimensions));
      return dimensions;
    });
    if(ready) ready=await run('DRAFT_PDF_FIRST_VALUE',async()=>{
      const responsePromise=page.waitForResponse(res=>
        new URL(res.url()).pathname==='/api/patients/'+ids.patient_id+'/pdf'
        && res.request().method()==='POST' && res.request().postDataJSON()?.archive===false,
      {timeout:45000});
      const downloadPromise=page.waitForEvent('download',{timeout:45000});
      await page.getByRole('button',{name:'Brouillon PDF'}).click();
      const [response,download]=await Promise.all([responsePromise,downloadPromise]);
      const payload=response.request().postDataJSON();
      const bytes=await response.body();
      if(response.status()!==200||!bytes.subarray(0,4).equals(Buffer.from('%PDF'))
        ||payload.analysis_id!==ids.older_id||!(payload.expected_revision>0)
        ||response.headers()['x-cephalo-analysis-id']!==String(ids.older_id)
        ||response.headers()['x-cephalo-revision']!==String(payload.expected_revision))
        throw Error('First PDF is not bound to chosen study/revision, HTTP '+response.status());
      const downloadFailure=await download.failure();
      if(downloadFailure)throw Error('Clinician draft PDF download failed: '+downloadFailure);
      await fs.writeFile(path.join(output,label+'-first-value.pdf'),bytes);
      record.firstValue={analysis_id:ids.older_id,revision:payload.expected_revision,
        bytes:bytes.length,downloadName:download.suggestedFilename()};
      await shot('after-first-value');
      return record.firstValue;
    });
    if(ready) ready=await run('OFFICIAL_ARCHIVE_REPLAY',async()=>{
      const archive=page.getByRole('button',{name:'Archiver le bilan'});
      await archive.waitFor({state:'visible',timeout:15000});
      await page.waitForFunction(()=>{
        const b=[...document.querySelectorAll('button')].find(e=>e.textContent?.includes('Archiver le bilan'));
        return Boolean(b&&!b.disabled);
      },null,{timeout:30000});
      page.once('dialog',dialog=>dialog.dismiss());
      const responsePromise=page.waitForResponse(res=>
        new URL(res.url()).pathname==='/api/patients/'+ids.patient_id+'/pdf'
        && res.request().method()==='POST' && res.request().postDataJSON()?.archive===true,
      {timeout:45000});
      await archive.click();
      const response=await responsePromise;
      const payload=response.request().postDataJSON();
      const bytes=await response.body();
      if(response.status()!==200||!bytes.subarray(0,4).equals(Buffer.from('%PDF'))
        ||payload.analysis_id!==ids.older_id
        ||payload.expected_revision!==record.firstValue.revision
        ||response.headers()['x-cephalo-analysis-id']!==String(ids.older_id)
        ||response.headers()['x-cephalo-revision']!==String(record.firstValue.revision)
        ||response.headers()['x-cephalo-archive-replayed']!=='true')
        throw Error('Official archive replay is not identity/revision-verified, HTTP '+response.status());
      await shot('after-official-archive-replay');
      return {analysis_id:ids.older_id,revision:payload.expected_revision,replayed:true,bytes:bytes.length};
    });
  }catch(error){
    record.errors.push('HARNESS_SETUP: '+String(error));
    try{await shot('failure-harness-setup')}catch{}
  }finally{
    for(const id of matrixIDs){
      if(!record.matrix.some(item=>item.id===id))
        record.matrix.push({id,status:'NOT_TESTED',reason:'upstream user journey or harness error'});
    }
    record.valid=record.matrix.every(item=>item.status==='PASS')&&!record.errors.length;
    // Score is never fabricated from mere technical checks. UX usability,
    // accessibility and clinical interpretation require separate review.
    record.score={technical:record.valid?'ALL_SCOPED_CHECKS_PASS':'NOT_CERTIFIED',
      severe_ux_out_of_10:null,reason:'human UX evaluation and full before/after comparison not yet performed'};
    await context?.close().catch(()=>{});
    await api.dispose();
  }
  return record;
}
try{
  for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
    report.viewports.push(await viewportRun(viewport));
  }
}finally{
  await browser.close();
  report.overall=report.viewports.length===2&&report.viewports.every(item=>item.valid)?'FUE_I_AUTOMATED_SCOPE_PASS':'FUE_I_PARTIAL_OR_FAIL';
  await fs.writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
}
console.log('P2TER_FUE_I_EVIDENCE',JSON.stringify({head,overall:report.overall,
  viewports:report.viewports.map(({viewport,valid,matrix,errors})=>({
    viewport,valid,checks:matrix.map(({id,status})=>({id,status})),errors}))}));
if(report.overall!=='FUE_I_AUTOMATED_SCOPE_PASS')
  throw Error('P2ter FUE-I incomplete: inspect retained matrix/screenshots');
