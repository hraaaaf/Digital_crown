/**
 * LOT07 R6 / 07.1.C FUE-I: real React patient route + genuine FastAPI.
 * Synthetic-only disposable T2 SQLite database; no API route interception.
 * Does not certify physical 2nd screen, native Windows 200% or cephalo zoom/pan.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';

const sha = process.env.SOURCE_HEAD;
const password = process.env.T2_PASSWORD;
assert.match(sha ?? '', /^[a-f0-9]{40}$/);
assert.ok(password && process.env.ENVIRONMENT === 'test' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1' &&
  process.env.DATABASE_URL === 'sqlite:///./t2-runtime-cert.db' &&
  process.env.VITE_LOT07_R6_071C_LAB === 'true', 'Unsafe R6 FUE-I environment');
const apiBase = 'http://127.0.0.1:8005';
const webBase = 'http://127.0.0.1:5173';
const directory = path.resolve('../artifacts/lot07-r6-071c-fue-i');
await fs.mkdir(directory,{recursive:true});
const report = {
  head:sha, syntheticOnly:true, actualFastAPI:true, actualReactBrowser:true,
  routeIntercepted:false, database:'DISPOSABLE_T2_SQLITE', production:false,
  physicalSecondScreen:false, zoomPanCertified:false, humanApproved:false,
  pass:false, checks:[],screenshots:[],denials:[],error:null,
};
const check = (name, condition, details={}) => {
  report.checks.push({name,pass:Boolean(condition),...details});
  assert.ok(condition, 'R6 FUE-I FAILURE: '+name+' '+JSON.stringify(details));
};
const capture = async (page,name) => {
  await page.screenshot({path:path.join(directory,name+'.png'),fullPage:false,animations:'disabled'});
  report.screenshots.push(name+'.png');
};
let browser;
let page;
const contexts=[];
const api=await request.newContext({baseURL:apiBase});
const fakePng=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEANmpCD8ongcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfUJxAYTIfIvQAAAAAElFTkSuQmCC','base64');
try {
  const login=await api.post('/api/auth/login',{
    form:{username:'t2-browser@cabinet.ma',password},
  });
  check('actual-owner-JWT-login',login.status()===200,{status:login.status()});
  const auth=await login.json();
  const head={Authorization:'Bearer '+auth.access_token};
  const patientsResponse=await api.get('/api/patients/',{headers:head});
  check('actual-authenticated-patient-index',patientsResponse.status()===200);
  const patient=(await patientsResponse.json()).find(p=>p.numero_dossier==='T2-0001');
  check('synthetic-owner-patient-found',Number.isSafeInteger(patient?.id));

  // Real uploads persist THREE distinct independent source records.
  const clinicalAssets={};
  for (const label of ['T0','T1','T2']) {
    const response=await api.post('/api/patients/'+patient.id+'/assets/import',{
      headers:head,
      multipart:{file:{name:'r6-synthetic-'+label+'.png',mimeType:'image/png',buffer:fakePng},
        asset_type:'PHOTO',source_kind:'UPLOAD',timepoint:label},
    });
    check('real-import-'+label,response.status()===201 || response.status()===200,{status:response.status()});
  }
  const assetsResponse=await api.get('/api/patients/'+patient.id+'/assets',{headers:head});
  check('real-authenticated-assets-index',assetsResponse.status()===200);
  const assets=(await assetsResponse.json()).items;
  for(const label of ['T0','T1','T2']) {
    clinicalAssets[label]=assets.find(a=>a.timepoint===label && a.original_filename==='r6-synthetic-'+label+'.png')?.id;
    // Original filename is not always exposed in list payload; the T2 runtime
    // begins with no other T0/T1/T2 assets, so the timepoint is sufficient.
    if(!clinicalAssets[label])clinicalAssets[label]=assets.find(a=>a.timepoint===label)?.id;
    check('persisted-canonical-source-'+label,Number.isSafeInteger(clinicalAssets[label]));
  }
  check('three-canonical-assets-distinct',new Set(Object.values(clinicalAssets)).size===3);

  const caseResponse=await api.post('/api/patients/'+patient.id+'/ortho-case',{
    headers:head,data:{started_at:'2026-01-02T09:00:00'},
  });
  check('real-ortho-case-created',caseResponse.status()===201,{status:caseResponse.status()});
  const caseId=(await caseResponse.json()).id;
  const createdPoints=[];
  for(const [ordinal,label,date] of [
    [0,'T0','2026-01-02T09:00:00'],[1,'T1','2026-04-02T09:00:00'],[2,'T2','2026-07-02T09:00:00'],
  ]) {
    const tp=await api.post('/api/patients/'+patient.id+'/ortho-case/'+caseId+'/timepoints',{
      headers:head,data:{ordinal,occurred_at:date,note:'R6_PRIVATE_SYNTHETIC_NOTE_DO_NOT_RENDER'},
    });
    check('real-timepoint-'+label,tp.status()===201,{status:tp.status()});
    const tpId=(await tp.json()).id;
    createdPoints.push({id:tpId,label,ordinal});
    const link=await api.post('/api/patients/'+patient.id+'/ortho-case/'+caseId+
      '/timepoints/'+tpId+'/evidences',{
      headers:head,data:{clinical_asset_id:clinicalAssets[label]},
    });
    check('real-source-binding-'+label,link.status()===201,{status:link.status()});
  }
  const reused=await api.post('/api/patients/'+patient.id+'/ortho-case/'+caseId+
    '/timepoints/'+createdPoints[2].id+'/evidences',{
    headers:head,data:{clinical_asset_id:clinicalAssets.T0},
  });
  check('backend-refuses-reused-canonical-source',reused.status()===409,{status:reused.status()});
  report.denials.push({reason:'SOURCE_REUSE',status:reused.status()});

  const realCase=await api.get('/api/patients/'+patient.id+'/ortho-case',{headers:head});
  const realPoints=await api.get('/api/patients/'+patient.id+'/ortho-case/'+caseId+'/timepoints',{headers:head});
  check('backend-stored-case-and-three-points',realCase.status()===200 &&
    realPoints.status()===200 && (await realPoints.json()).length===3);
  for(const [from,to] of [[0,1],[1,2],[0,2]]) {
    const response=await api.get('/api/patients/'+patient.id+'/ortho-case/'+caseId+'/compare',{
      headers:head,params:{from_ordinal:from,to_ordinal:to},
    });
    const body=response.status()===200?await response.json():null;
    check('genuine-comparison-'+from+'-'+to,response.status()===200 &&
      body?.patient_id===patient.id && body?.ortho_case_id===caseId &&
      body?.from_timepoint?.ordinal===from && body?.to_timepoint?.ordinal===to &&
      body?.interpretation_policy==='NUMERIC_ONLY_CLINICIAN_INTERPRETATION',
      {status:response.status()});
  }

  const responseB=await api.post('/api/patients/',{
    headers:head,
    data:{numero_dossier:'R6-T2-0002',nom:'SYNTHETIC_B',prenom:'BETA',
      date_naissance:'1992-05-04',sexe:'F'},
  });
  check('second-patient-same-cabinet',responseB.status()===201 ||
    responseB.status()===200,{status:responseB.status()});
  const patientB=await responseB.json();
  check('synthetic-patient-identities-distinct',patientB.id!==patient.id);

  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({
    viewport:{width:1440,height:900},locale:'fr-FR',reducedMotion:'reduce',
    serviceWorkers:'block',
  });
  await context.addInitScript(({access,refresh})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('refresh_token',refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:auth.access_token,refresh:auth.refresh_token});
  page=await context.newPage();
  const errors=[],network=[];
  page.on('pageerror',error=>errors.push(String(error).slice(0,240)));
  page.on('response',response=>{
    const url=new URL(response.url());
    if(url.pathname.includes('/ortho-case')) {
      network.push({path:url.pathname,status:response.status()});
    }
  });
  await page.goto(webBase+'/patients/'+patient.id+'?tab=tracking',{
    waitUntil:'domcontentloaded',timeout:90000,
  });
  const triple=page.locator('[data-testid="r6-longitudinal-three-points"]');
  await triple.waitFor({state:'visible',timeout:90000});
  check('actual-React-patient-page-shows-triple',await triple.count()===1);
  const sourceText=await triple.innerText();
  check('three-actual-ordinals-and-source-ids',
    ['T0','T1','T2'].every(label=>sourceText.includes(label)) &&
    Object.values(clinicalAssets).every(id=>sourceText.includes('#'+id)));
  check('clinical-notes-and-author-not-displayed',
    !sourceText.includes('R6_PRIVATE_SYNTHETIC_NOTE_DO_NOT_RENDER') &&
    !sourceText.includes('created_by'));
  check('real-ortho-API-observed-from-browser',
    network.some(r=>r.path==='/api/patients/'+patient.id+'/ortho-case' && r.status===200) &&
    network.some(r=>r.path.endsWith('/timepoints') && r.status===200));
  await triple.scrollIntoViewIfNeeded();
  await capture(page,'01-A-before-triple-1440');

  for(const [from,to] of [[0,1],[1,2],[0,2]]) {
    const watch=page.waitForResponse(r=>{
      const u=new URL(r.url());
      return u.pathname==='/api/patients/'+patient.id+'/ortho-case/'+caseId+'/compare' &&
        u.searchParams.get('from_ordinal')===String(from) &&
        u.searchParams.get('to_ordinal')===String(to);
    },{timeout:40000});
    await triple.getByRole('button',{name:'T'+from+' → T'+to,exact:true}).click();
    check('real-click-selected-pair-'+from+'-'+to,
      await triple.getByRole('button',{name:'T'+from+' → T'+to,exact:true})
        .getAttribute('aria-pressed')==='true');
    const response=await watch;
    check('real-browser-response-pair-'+from+'-'+to,response.status()===200,
      {status:response.status()});
    await page.locator('[data-ortho-f3-compare]').getByText('Mesures communes',{exact:true})
      .waitFor({state:'visible',timeout:25000});
    await triple.scrollIntoViewIfNeeded();
    await capture(page,'02-pair-'+from+'-'+to+'-1440');
  }

  const goPatient=async(id)=>{
    await page.evaluate(url=>{
      window.history.pushState({},'',url);
      window.dispatchEvent(new PopStateEvent('popstate'));
    },'/patients/'+id+'?tab=tracking');
  };
  await goPatient(patientB.id);
  await page.locator('[data-testid="r6-longitudinal-three-points"]').waitFor({
    state:'detached',timeout:30000,
  });
  await page.getByText(patientB.numero_dossier,{exact:true}).first()
    .waitFor({state:'visible',timeout:30000});
  check('A-to-B-hides-canonical-triple',await triple.count()===0 &&
    !(await page.locator('body').innerText()).includes('R6_PRIVATE_SYNTHETIC_NOTE_DO_NOT_RENDER'));
  await capture(page,'03-B-without-A-evidence-1440');

  await goPatient(patient.id);
  await triple.waitFor({state:'visible',timeout:45000});
  const backText=await triple.innerText();
  check('B-to-A-source-identity-verified',
    Object.values(clinicalAssets).every(id=>backText.includes('#'+id)) &&
    !backText.includes('R6_PRIVATE_SYNTHETIC_NOTE_DO_NOT_RENDER'));
  await capture(page,'04-A-return-1440');

  // Real network delay via CDP. No route.fulfill/route.intercept/mock responses.
  const cdp=await context.newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions',{
    offline:false,latency:700,downloadThroughput:-1,uploadThroughput:-1,
  });
  await goPatient(patientB.id);
  await goPatient(patient.id);
  await goPatient(patientB.id);
  await page.getByText(patientB.numero_dossier,{exact:true}).first()
    .waitFor({state:'visible',timeout:45000});
  await page.waitForTimeout(2100);
  check('delayed-A-responses-do-not-expose-source-on-B',
    await triple.count()===0 &&
    !(await page.locator('body').innerText()).includes('Céphalo #'+clinicalAssets.T0));
  await cdp.send('Network.emulateNetworkConditions',{
    offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1,
  });
  await cdp.detach();
  await capture(page,'05-B-delayed-network-1440');

  // Real product workstation enrollment; denial must not be a missing-station 423.
  const enrolled=await api.post('/api/workstation/enroll',{
    headers:head,data:{accountPassword:password},
  });
  check('owner-workstation-enrollment',enrolled.status()===200,{status:enrolled.status()});
  const cookies=(await api.storageState()).cookies.filter(c=>c.name==='dc_workstation');
  check('genuine-HttpOnly-workstation-cookie',cookies.length===1);
  const restricted=await request.newContext({
    baseURL:apiBase,storageState:{cookies,origins:[]},
  });
  contexts.push(restricted);
  const restrictedLogin=await restricted.post('/api/auth/login',{
    form:{username:'t2-restricted@cabinet.ma',password},
  });
  check('restricted-actor-real-login',restrictedLogin.status()===200);
  const restrictedToken=(await restrictedLogin.json()).access_token;
  const restrictedHeader={Authorization:'Bearer '+restrictedToken};
  const staffBootstrap=await restricted.get('/api/workstation/bootstrap',{headers:restrictedHeader});
  check('restricted-actor-verified-workstation',staffBootstrap.status()===200);
  const denied=await restricted.get('/api/patients/'+patient.id+'/ortho-case',{headers:restrictedHeader});
  check('RBAC-ortho-case-refused-not-workstation',denied.status()===403,
    {status:denied.status()});
  report.denials.push({reason:'STAFF_RBAC',status:denied.status()});

  const foreign=await request.newContext({baseURL:apiBase});
  contexts.push(foreign);
  const foreignLogin=await foreign.post('/api/auth/login',{
    form:{username:'t2-setup-1280@cabinet.ma',password},
  });
  check('independent-foreign-tenant-login',foreignLogin.status()===200);
  const foreignHead={Authorization:'Bearer '+(await foreignLogin.json()).access_token};
  const foreignEnroll=await foreign.post('/api/workstation/enroll',{
    headers:foreignHead,data:{accountPassword:password},
  });
  check('foreign-workstation-enrollment',foreignEnroll.status()===200);
  const forbidden=await foreign.get('/api/patients/'+patient.id+'/ortho-case',{
    headers:foreignHead,
  });
  check('cross-tenant-ortho-case-refused',forbidden.status()===403 ||
    forbidden.status()===404,{status:forbidden.status()});
  report.denials.push({reason:'CROSS_TENANT',status:forbidden.status()});

  check('no-unhandled-browser-errors',errors.length===0,{errors:errors.slice(0,2)});
  report.pass=report.checks.every(c=>c.pass) && report.screenshots.length>=6;
  console.log('LOT07_R6_FUE_I_PASS',report.checks.length,sha);
} catch(error) {
  report.error=String(error?.stack||error).slice(0,1400);
  if(page)try {await capture(page,'failure-snapshot');}catch{/* page may have closed */}
  throw error;
} finally {
  await fs.writeFile(path.join(directory,'report.json'),JSON.stringify(report,null,2));
  await browser?.close();
  for(const context of contexts)await context.dispose();
  await api.dispose();
  console.log('LOT07_R6_FUE_I_RESULT',JSON.stringify({
    sha,pass:report.pass,checks:report.checks.length,screenshots:report.screenshots.length,
    error:report.error,
  }));
}
