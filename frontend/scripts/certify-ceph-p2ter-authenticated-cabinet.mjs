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
 const record={viewport:viewport.width+'x'+viewport.height,checks:[],shots:[],pageErrors:[],failedRequests:[],httpErrors:[],observedToasts:[],consoleErrors:[],archiveGateDiagnostics:[],valid:false};
 const api=await request.newContext({baseURL:backend});
 let context;
 let page;
 try{
  const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
  if(login.status()!==200)throw Error('Bootstrap auth failed '+login.status());
  const token=(await login.json()).access_token;
  // Direct authenticated media probe to distinguish a real server 500 from a
  // browser CORS symptom, without exposing tokens or weakening network alerts.
  const mediaProbe=await api.get('/api/static/uploads/radios/t2-cephalo-seeded.png',{
    headers:{Authorization:'Bearer '+token,Origin:root},
  });
  record.mediaProbe={
    status:mediaProbe.status(),
    cors:mediaProbe.headers()['access-control-allow-origin']||null,
    type:mediaProbe.headers()['content-type']||null,
    error:mediaProbe.status()===200?null:(await mediaProbe.text()).slice(0,300),
  };
  console.log('P2TER_PROTECTED_MEDIA_DIAGNOSTIC',JSON.stringify({
    viewport:record.viewport,mediaProbe:record.mediaProbe,
  }));
  const enrolled=await enrollT2Workstation(api,token,password);
  const station=enrolled.cookies.filter(c=>c.name==='dc_workstation');
  if(station.length!==1)throw Error('Workstation enrollment missing');
  context=await browser.newContext({viewport,acceptDownloads:true,reducedMotion:'reduce',
    storageState:{cookies:station,origins:[]}});
  page=await context.newPage();
  page.on('pageerror',e=>record.pageErrors.push(e.message));
  page.on('console',message=>{ if(message.type()==='error')record.consoleErrors.push(message.text().slice(0,450)); });
  page.on('requestfailed',req=>record.failedRequests.push({
    method:req.method(), url:req.url(), failure:req.failure()?.errorText||'unknown',
  }));
  page.on('response',res=>{
    if(res.status()>=400)record.httpErrors.push({status:res.status(),url:res.url()});
  });
  await page.addInitScript(()=>{
    window.__p2terSeenToasts=[];
    const inspect=()=>{
      if(document.body?.innerText?.includes('Serveur injoignable') &&
          window.__p2terSeenToasts.length<10)
        window.__p2terSeenToasts.push({time:Date.now(),page:location.pathname});
    };
    document.addEventListener('DOMContentLoaded',()=>{
      new MutationObserver(inspect).observe(document.body,{childList:true,subtree:true,characterData:true});
    });
  });
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
  // Probe exactly the same media URL after real Cabinet login + workstation
  // enrollment. APIRequestContext bypasses browser CORS, while fetch does not.
  const imageURL=backend+'/api/static/uploads/radios/t2-cephalo-seeded.png';
  const sessionMedia=await context.request.get(imageURL,{headers:{Authorization:'Bearer '+token,Origin:root}});
  record.sessionMediaProbe={status:sessionMedia.status(),
    cors:sessionMedia.headers()['access-control-allow-origin']||null,
    type:sessionMedia.headers()['content-type']||null,
    error:sessionMedia.status()===200?null:(await sessionMedia.text()).slice(0,250)};
  record.browserMediaProbe=await page.evaluate(async imageURL=>{
    try {
      const token=localStorage.getItem('token');
      const r=await fetch(imageURL,{credentials:'include',
        headers:token?{Authorization:'Bearer '+token}:{}});
      return {status:r.status,type:r.headers.get('content-type'),
        cors:r.headers.get('access-control-allow-origin')};
    } catch(e) {return {error:String(e)};}
  },imageURL);
  console.log('P2TER_ENROLLED_MEDIA_DIAGNOSTIC',JSON.stringify({
    viewport:record.viewport,sessionMediaProbe:record.sessionMediaProbe,
    browserMediaProbe:record.browserMediaProbe,
  }));

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
  // The archive is exercised through the actual rendered Cabinet button and JWT,
  // not a direct API substitute. All data and the database are disposable T2.
  await page.getByRole('button',{name:'Historique',exact:true}).click();
  await page.locator('[data-cephalo-history-analysis-id="'+identities.older_id+'"]').click();
  await page.locator('[data-cephalo-selected-analysis-id="'+identities.older_id+'"]').waitFor({state:'visible'});
  await page.getByRole('button',{name:'4. Documents & stratégie',exact:true}).click();
  const archiveButton=page.getByRole('button',{name:'Archiver le bilan'});
  await archiveButton.waitFor({state:'visible'});
  try {
    await page.waitForFunction(()=>{
      const b=[...document.querySelectorAll('button')].find(b=>b.textContent?.includes('Archiver le bilan'));
      return Boolean(b && !b.disabled);
    },null,{timeout:20000});
  } catch(e) {
    const diagnosis=await page.evaluate(()=>{
      const btn=[...document.querySelectorAll('button')].find(b=>b.textContent?.includes('Archiver le bilan'));
      return {disabled:btn?.disabled, title:btn?.outerHTML.slice(0,700),
        checklist:document.body.innerText.match(/Landmarks complets[^\\n]*/)?.[0]||null,
        validation:document.body.innerText.match(/Cohérence des mesures[^\\n]*/)?.[0]||null,
        image:document.body.innerText.match(/Image céphalométrique chargée[^\\n]*/)?.[0]||null};
    });
    record.archiveGateDiagnostics.push(diagnosis);
    throw Error('Archive gate disabled '+JSON.stringify(diagnosis)+' / '+String(e));
  }
  const archiveResponsePromise=page.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/patients/'+identities.patient_id+'/pdf' &&
    r.request().method()==='POST' && r.request().postDataJSON()?.archive===true,
    {timeout:45000});
  page.once('dialog',dialog=>dialog.dismiss());
  const archivePosts=[];
  const auditArchiveRequest=req=>{
    if(req.method()==='POST' && new URL(req.url()).pathname==='/api/patients/'+identities.patient_id+'/pdf' &&
        req.postDataJSON()?.archive===true) archivePosts.push(req.postDataJSON());
  };
  page.on('request',auditArchiveRequest);
  await shot('archive-before');
  await archiveButton.dblclick(); // actual Chromium pointer double click: one logical archive request
  const archivedResponse=await archiveResponsePromise;
  await page.waitForTimeout(250);
  page.off('request',auditArchiveRequest);
  if(archivePosts.length!==1)throw Error('Double click created '+archivePosts.length+' archive requests instead of one');
  const archivedPayload=archivedResponse.request().postDataJSON();
  if(archivedResponse.status()!==200 ||
      archivedPayload.analysis_id!==identities.older_id ||
      archivedResponse.headers()['x-cephalo-analysis-id']!==String(identities.older_id) ||
      archivedResponse.headers()['x-cephalo-revision']!==String(archivedPayload.expected_revision))
    throw Error('Authenticated archive did not retain selected OLDER study identity, revision and HTTP 200: '+archivedResponse.status());
  await fs.writeFile(path.join(output,record.viewport+'-older-click-archived.pdf'),await archivedResponse.body());
  await shot('archive-after');
  record.checks.push('REAL_CABINET_ARCHIVE_BUTTON_OLDER_STUDY_'+identities.older_id+'_REV_'+archivedPayload.expected_revision);
  record.checks.push('POINTER_DOUBLE_CLICK_SINGLE_ARCHIVE_POST');
  // UI transport regression only: mock a synthetic 422 response on the real
  // authenticated button. Backend 422 and zero archive are asserted in pytest.
  const clinicalRefusal='Discordance structurelle synthétique';
  const deny422=async route=>{
    const payload=route.request().postDataJSON();
    if(payload?.archive!==true || payload.analysis_id!==identities.older_id)
      throw Error('Unexpected intercepted clinical refusal request');
    await route.fulfill({status:422,contentType:'application/json',
      body:JSON.stringify({detail:{message:'Archivage refusé',fatals:[clinicalRefusal],warnings:[]}})});
  };
  await page.route('**/api/patients/*/pdf',deny422);
  try {
    const refusalResponse=page.waitForResponse(r=>
      new URL(r.url()).pathname==='/api/patients/'+identities.patient_id+'/pdf' &&
      r.request().postDataJSON()?.archive===true,{timeout:30000});
    await archiveButton.click();
    const refusal=await refusalResponse;
    if(refusal.status()!==422)throw Error('Clinical refusal response expected 422');
    await page.getByText(new RegExp(clinicalRefusal)).first().waitFor({state:'visible',timeout:10000});
    await shot('synthetic-clinical-422-refusal-visible');
    record.checks.push('SIMULATED_422_BLOB_REFUSAL_VISIBLE_NO_SERVER_ARCHIVE');
  } finally {
    await page.unroute('**/api/patients/*/pdf',deny422);
  }
  // Concurrent authenticated tabs must retain different selected study identities.
  const tabB=await context.newPage();
  await tabB.goto(root+'/patients/'+identities.patient_id+'?tab=radiology&radioTab=cephalo',
    {waitUntil:'domcontentloaded',timeout:45000});
  await tabB.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
  await tabB.getByRole('button',{name:'Historique',exact:true}).click();
  await tabB.locator('[data-cephalo-history-analysis-id="'+identities.latest_id+'"]').click();
  await tabB.locator('[data-cephalo-selected-analysis-id="'+identities.latest_id+'"]').waitFor({state:'visible'});
  await tabB.getByRole('button',{name:'4. Documents & stratégie',exact:true}).click();
  const tabAResponse=page.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/patients/'+identities.patient_id+'/pdf' &&
    r.request().method()==='POST' && r.request().postDataJSON()?.archive===false,{timeout:45000});
  const tabBResponse=tabB.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/patients/'+identities.patient_id+'/pdf' &&
    r.request().method()==='POST' && r.request().postDataJSON()?.archive===false,{timeout:45000});
  await Promise.all([
    page.getByRole('button',{name:'Brouillon PDF'}).click(),
    tabB.getByRole('button',{name:'Brouillon PDF'}).click(),
  ]);
  const [aPdf,bPdf]=await Promise.all([tabAResponse,tabBResponse]);
  if(aPdf.status()!==200 || bPdf.status()!==200 ||
      aPdf.request().postDataJSON().analysis_id!==identities.older_id ||
      bPdf.request().postDataJSON().analysis_id!==identities.latest_id ||
      aPdf.headers()['x-cephalo-analysis-id']!==String(identities.older_id) ||
      bPdf.headers()['x-cephalo-analysis-id']!==String(identities.latest_id))
    throw Error('Two authenticated tabs crossed study identity on concurrent drafts');
  record.checks.push('TWO_AUTHENTICATED_TABS_DIFFERENT_STUDY_CONCURRENT_PDFS');
  await tabB.screenshot({path:path.join(output,record.viewport+'-two-tabs-B-after.png'),animations:'disabled'});
  record.shots.push(record.viewport+'-two-tabs-B-after.png');
  await tabB.close();
  // Hold an actual PDF request while switching old A -> newer B in the same tab.
  // A late A response must never be downloaded or re-select the wrong study.
  let releaseLatePDF;
  let signalHeldPDF;
  const heldPDF=new Promise(resolve=>{signalHeldPDF=resolve});
  const lateGate=new Promise(resolve=>{releaseLatePDF=resolve});
  let lateDownloadCount=0;
  const lateDownloadListener=()=>{lateDownloadCount++};
  page.on('download',lateDownloadListener);
  const lateRoute=async route=>{
    const payload=route.request().postDataJSON();
    if(payload?.archive===false && payload?.analysis_id===identities.older_id) {
      signalHeldPDF();
      await lateGate;
    }
    await route.continue();
  };
  await page.route('**/api/patients/*/pdf',lateRoute);
  const lateAResponse=page.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/patients/'+identities.patient_id+'/pdf' &&
    r.request().method()==='POST' && r.request().postDataJSON()?.archive===false &&
    r.request().postDataJSON()?.analysis_id===identities.older_id,{timeout:45000});
  try {
    await page.getByRole('button',{name:'Brouillon PDF'}).click();
    await heldPDF;
    await page.getByRole('button',{name:'Historique',exact:true}).click();
    await page.locator('[data-cephalo-history-analysis-id="'+identities.latest_id+'"]').click();
    await page.locator('[data-cephalo-selected-analysis-id="'+identities.latest_id+'"]').waitFor({state:'visible'});
  } finally {
    releaseLatePDF();
  }
  const completedLateA=await lateAResponse;
  await page.unroute('**/api/patients/*/pdf',lateRoute);
  await page.waitForTimeout(200);
  page.off('download',lateDownloadListener);
  if(completedLateA.status()!==200 || lateDownloadCount!==0 ||
      !await page.locator('[data-cephalo-selected-analysis-id="'+identities.latest_id+'"]').isVisible())
    throw Error('Late old-A PDF overwrote B selection or triggered stale download');
  record.checks.push('SWITCH_A_TO_B_WHILE_OLDER_PDF_IN_FLIGHT_REFUSES_STALE_DOWNLOAD');
  await shot('late-old-A-response-B-still-selected');
  // Revalidation TOCTOU: pause archive POST after its real successful prevalidation,
  // edit synthetic study B through authenticated FastAPI, then demand HTTP 409
  // and a comprehensible refusal toast; no archive may be persisted.
  if(viewport.width===1600){
    await page.getByRole('button',{name:'4. Documents & stratégie',exact:true}).click();
    const staleArchiveButton=page.getByRole('button',{name:'Archiver le bilan'});
    await page.waitForFunction(()=>{
      const b=[...document.querySelectorAll('button')].find(b=>b.textContent?.includes('Archiver le bilan'));
      return Boolean(b && !b.disabled);
    },null,{timeout:25000});
    let releaseStale;
    let heldStale;
    let requestRevision;
    const staleHeld=new Promise(resolve=>{heldStale=resolve});
    const staleGate=new Promise(resolve=>{releaseStale=resolve});
    const staleRoute=async route=>{
      const payload=route.request().postDataJSON();
      if(payload?.archive===true && payload?.analysis_id===identities.latest_id){
        requestRevision=payload.expected_revision;
        heldStale();
        await staleGate;
      }
      await route.continue();
    };
    await page.route('**/api/patients/*/pdf',staleRoute);
    const staleValidation=page.waitForResponse(r=>
      new URL(r.url()).pathname==='/api/patients/'+identities.patient_id+'/cephalo-validation'
      && r.request().method()==='GET' && r.status()===200,{timeout:45000});
    const staleResponse=page.waitForResponse(r=>
      new URL(r.url()).pathname==='/api/patients/'+identities.patient_id+'/pdf'
      && r.request().method()==='POST' && r.request().postDataJSON()?.archive===true,
      {timeout:45000});
    try {
      await staleArchiveButton.click();
      await staleHeld;
      const prevalidated=await staleValidation;
      const params=new URL(prevalidated.url()).searchParams;
      if(Number(params.get('analysis_id'))!==identities.latest_id ||
        Number(params.get('expected_revision'))!==requestRevision)
        throw Error('Prevalidation identity mismatch for TOCTOU test');
      const update=await page.evaluate(async ({apiRoot,study})=>{
        const token=localStorage.getItem('token');
        if(!token)throw Error('No Cabinet auth in revision-race test');
        const headers={Authorization:'Bearer '+token,'Content-Type':'application/json'};
        const get=await fetch(apiRoot+'/api/ia/analyses/'+study,{headers,credentials:'include'});
        if(!get.ok)throw Error('Revision setup GET HTTP '+get.status);
        const record=await get.json();
        const points=record.landmarks_data||record.landmarks;
        if(!Array.isArray(points)||points.length===0)throw Error('No editable synthetic landmarks');
        const edited=points.map((p,i)=>i===0?{...p,x:p.x+1}:p);
        const put=await fetch(apiRoot+'/api/ia/analyses/'+study,
          {method:'PUT',headers,credentials:'include',body:JSON.stringify({landmarks:edited})});
        if(!put.ok)throw Error('Revision mutation HTTP '+put.status+' '+(await put.text()).slice(0,300));
        const newer=await fetch(apiRoot+'/api/ia/analyses/'+study,{headers,credentials:'include'});
        return {status:put.status,revision:(await newer.json()).angles_data?.scientific_read_path?.revision};
      },{apiRoot:backend,study:identities.latest_id});
      if(!(Number.isSafeInteger(update.revision) && update.revision>requestRevision))
        throw Error('Revision did not increment before delayed archive '+JSON.stringify(update));
    } finally {
      releaseStale();
    }
    const stale=await staleResponse;
    await page.unroute('**/api/patients/*/pdf',staleRoute);
    if(stale.status()!==409)throw Error('Stale post-prevalidation archive did not fail-closed: '+stale.status());
    await page.getByText(/modifiée|changé|périmée/i).first().waitFor({state:'visible',timeout:10000});
    await shot('stale-revision-archive-refusal-visible');
    record.checks.push('REVISION_CHANGED_AFTER_PREVALIDATION_ARCHIVE_409_TOAST_VISIBLE');
  }
  // The normal end-to-end flow must not report unreachable backend on a
  // canceled obsolete study-image request.
  const falseToasts=await page.evaluate(()=>window.__p2terSeenToasts||[]);
  if(falseToasts.length)throw Error('False server-unreachable toast during successful Cabinet flow: '+JSON.stringify(falseToasts));
  record.checks.push('NO_FALSE_SERVER_UNREACHABLE_TOAST_DURING_SUCCESSFUL_FLOW');

  // A genuinely failed active clinical request MUST still surface the network
  // error. This fault is intentionally injected only AFTER all successful checks.
  const activeFailureRoute=route=>route.abort('failed');
  await page.route('**/api/ia/analyses/*',activeFailureRoute);
  try {
    await page.getByRole('button',{name:'Historique',exact:true}).click();
    const oldStudy=page.locator('[data-cephalo-history-analysis-id="'+identities.older_id+'"]');
    await oldStudy.waitFor({state:'visible'});
    await oldStudy.click();
    await page.waitForFunction(()=>Boolean(window.__p2terSeenToasts?.length),null,{timeout:10000});
    record.checks.push('GENUINE_ACTIVE_REQUEST_NETWORK_ERROR_STILL_DISPLAYS_TOAST');
    await shot('injected-active-network-failure-toast');
  } finally {
    await page.unroute('**/api/ia/analyses/*',activeFailureRoute);
  }
  record.observedToasts=await page.evaluate(()=>window.__p2terSeenToasts||[]);
  console.log('P2TER_NETWORK_DIAGNOSTIC',JSON.stringify({viewport:record.viewport,failedRequests:record.failedRequests,httpErrors:record.httpErrors,observedToasts:record.observedToasts}));
  if(record.pageErrors.length)throw Error('React exceptions '+JSON.stringify(record.pageErrors));
  record.valid=true;
 }catch(error){record.error=String(error);}
 finally{
  if(page && !page.isClosed())record.observedToasts=await page.evaluate(()=>window.__p2terSeenToasts||[]).catch(()=>[]);
  await context?.close().catch(()=>{});await api.dispose();
 }
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
