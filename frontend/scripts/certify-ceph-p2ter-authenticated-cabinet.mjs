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
  const clinicalSentinel='P2TER_SENTINEL_A_ONLY';
  const draftRevisions={};
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
   const therapyNote=page.locator('textarea[placeholder^="Saisie libre"]');
   await therapyNote.waitFor({state:'visible',timeout:15000});
   if(label==='older'){
     await therapyNote.fill(clinicalSentinel);
     if((await therapyNote.inputValue())!==clinicalSentinel)
       throw Error('A-only clinical sentinel not retained by A text input');
   } else if((await therapyNote.inputValue()).includes(clinicalSentinel)){
     throw Error('CLINICAL_CROSS_STUDY_LEAK: A therapy note appears in B form');
   }
   const responsePromise=page.waitForResponse(r=>{
     const u=new URL(r.url());return u.pathname==='/api/patients/'+identities.patient_id+'/pdf'
       && r.request().method()==='POST';
   },{timeout:30000});
   await draft.click();
   const response=await responsePromise;
   const body=response.request().postDataJSON();
   const sentInPDF=JSON.stringify(body).includes(clinicalSentinel);
   if((label==='older' && !sentInPDF) || (label==='newer' && sentInPDF))
     throw Error('CLINICAL_CROSS_STUDY_LEAK: wrong clinical sentinel in '+label+' PDF POST');
   if(label==='newer') record.checks.push('CABINET_A_TO_B_CLINICAL_SENTINEL_ISOLATED_IN_FORM_AND_PDF_POST');
   draftRevisions[label]=body.expected_revision;
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
  // The four-part A4 renderer produces an UNSIGNED draft even when science is
  // valid. The Cabinet must never offer an official archive creation button.
  await page.getByRole('button',{name:'Historique',exact:true}).click();
  await page.locator('[data-cephalo-history-analysis-id="'+identities.older_id+'"]').click();
  await page.locator('[data-cephalo-selected-analysis-id="'+identities.older_id+'"]').waitFor({state:'visible'});
  await page.getByRole('button',{name:'4. Documents & stratégie',exact:true}).click();
  const suspended=page.getByRole('button',{name:'Archivage suspendu'});
  await suspended.waitFor({state:'visible'});
  if(!await suspended.isDisabled()) throw Error('Unsigned official archive is clickable');
  if(!await page.getByRole('button',{name:'Brouillon PDF'}).isEnabled())
    throw Error('Draft should remain available with official archive suspended');
  const reason=await page.getByTestId('unsigned-cephalo-archive-hold').innerText();
  if(!/brouillon non signé/i.test(reason) || !/signature vérifiable/i.test(reason))
    throw Error('Unsigned archive suspension is not explained to clinician');
  await suspended.scrollIntoViewIfNeeded();
  await shot('archive-suspended-explained');
  record.checks.push('REAL_CABINET_UNSIGNED_ARCHIVE_DISABLED_AND_DRAFT_AVAILABLE');

  // Direct authenticated POST (outside disabled UI) must fail closed, too:
  // a forged client cannot convert an unsigned A4 draft into official evidence.
  const denied=await api.post('/api/patients/'+identities.patient_id+'/pdf',{
    headers:{Authorization:'Bearer '+token},
    data:{analysis_id:identities.older_id,expected_revision:draftRevisions.older,archive:true},
  });
  const detail=(await denied.json().catch(()=>({}))).detail||'';
  if(denied.status()!==409 || !String(detail).includes('BROUILLON NON SIGNÉ'))
    throw Error('Unsigned archive HTTP must be 409, got '+denied.status()+': '+String(detail));
  record.checks.push('REAL_JWT_UNSIGNED_NEW_OFFICIAL_ARCHIVE_HTTP_409');

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

  // Concurrency: two independent authenticated tabs must not race into
  // creating an official unsigned archive, even on the same exact revision.
  const concurrentPayload={
    analysis_id:identities.latest_id,
    expected_revision:draftRevisions.newer,
    archive:true,
  };
  const archiveURL=backend+'/api/patients/'+identities.patient_id+'/pdf';
  const archiveFromTab=tab=>tab.evaluate(async ({url,payload})=>{
    const token=localStorage.getItem('token');
    if(!token)throw Error('Authenticated tab missing Cabinet token');
    const response=await fetch(url,{method:'POST',credentials:'include',
      headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},
      body:JSON.stringify(payload)});
    const result=await response.json().catch(()=>({}));
    return {status:response.status,detail:result.detail||'',body:result};
  },{url:archiveURL,payload:concurrentPayload});
  const [sameA,sameB]=await Promise.all([archiveFromTab(page),archiveFromTab(tabB)]);
  for(const response of [sameA,sameB]){
    if(response.status!==409 || !String(response.detail).includes('BROUILLON NON SIGNÉ'))
      throw Error('Concurrent unsigned archive must be 409: '+JSON.stringify(response));
  }
  record.checks.push('TWO_AUTHENTICATED_TABS_SAME_STUDY_UNSIGNED_ARCHIVE_BOTH_409');
  record.sameRevisionArchive={analysis_id:identities.latest_id,
    revision:draftRevisions.newer,creation_refused:true,responses:[sameA.status,sameB.status]};
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
  // Revision safety stays enforced independently of the unsigned-draft guard.
  // A stale expected_revision must not be accepted by any authenticated client.
  if(viewport.width===1600){
    await page.getByRole('button',{name:'4. Documents & stratégie',exact:true}).click();
    if(!await page.getByRole('button',{name:'Archivage suspendu'}).isDisabled())
      throw Error('Unsigned archive UI became enabled after study switching');
    const stale=await api.post('/api/patients/'+identities.patient_id+'/pdf',{
      headers:{Authorization:'Bearer '+token},
      data:{analysis_id:identities.latest_id,expected_revision:1,archive:true},
    });
    if(stale.status()!==409)
      throw Error('Stale / unsigned archive must fail closed: '+stale.status());
    record.checks.push('STALE_REVISION_OR_UNSIGNED_ARCHIVE_FAIL_CLOSED_409');
    await shot('stale-unsigned-archive-suspended');
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
