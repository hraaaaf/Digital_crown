/**
 * LOT07 R6 / 07.1.D FUE-I: real React patient route + genuine FastAPI.
 * Synthetic-only disposable T2 SQLite database; no API route interception.
 * Does not certify physical 2nd screen, native Windows 200% or cephalo zoom/pan.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { chromium, request } from 'playwright';
import { verifyR7DesktopMatrix } from './certify-lot07-r7-desktop-matrix.mjs';

const sha = process.env.SOURCE_HEAD;
const password = process.env.T2_PASSWORD;
assert.match(sha ?? '', /^[a-f0-9]{40}$/);
assert.ok(password && process.env.ENVIRONMENT === 'test' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1' &&
  process.env.DATABASE_URL === 'sqlite:///./t2-runtime-cert.db' &&
  process.env.VITE_LOT07_R6_071C_LAB === 'true' && process.env.VITE_LOT07_R6_071D_LAB === 'true', 'Unsafe R6 FUE-I environment');
const apiBase = 'http://127.0.0.1:8005';
const webBase = 'http://127.0.0.1:5173';
const directory = path.resolve('../artifacts/lot07-r6-071d-fue-i');
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
let zoomWorker=null;
let isolatedWindowsProfile=null;
let isolatedWindowsExtension=null;
let page;
const contexts=[];
const api=await request.newContext({baseURL:apiBase});
// Three distinct Pillow-verified PNGs with schematic color/grid only.
// The old 150-byte inherited fixture was a truncated image (HTTP 422).
const syntheticPngBase64={
  T0:'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAABTklEQVR42u2aSxHCMBCGW4Y7DqqEGAEF1AEKcFAUoKROcIADDlwyTUNJso9/md0bt3yzH80+0h9PU2c5dp3xcAAHaIz94vf8uICfOJzvrhCyQrlMqUfObVfIARzgjwHm6WkY4HN6fIYMwOsakyBjZAAONys6ZRUK4xDGAZ9h4yuUMqBhbH9GFwxoqfjpHkDWqeAiw9Sp7CYG1Km4lEDTqbIWwtGpvpgD0ampGkXQiaCc1tWJph9Q1ImsodHSibgjk9eJvqUU1omlJ17ViQmDsamXSQXvVELgny0xVmHVSWguxKeT3GCLSSfpyRy5TgqjRVqddGajhDppDndJdFKeTrfrpD9eb9QJZT9QrRPQgqNOJ6wNTYVOiCumIp1Ad2SpTvHOxQDAik7JzgUdIE7FSkKsAHw/feeLbgdojux7Ify3Z64QRvT+9NgBHMB2vAFErp6uMTyTCAAAAABJRU5ErkJggg==',
  T1:'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAA/0lEQVR42u3aPQ6CQBCGYTBT0XA/vQGFFm7DCWhobLiBB6ShtkANBX+R3dkd805JgOzDfGSZhPx+vmaW65QZLwAAABgvmT3aPh8JrtVdbkTISoTWu6Zc63kmQgAAAAAAAAAAAH8J6Gv7HejrtivarjA8D7y/yD8GVw12AGUzDjTTDiQo2e7Ad62zkugY2X/qrCR6W+SHa6YLjR4wOXj9esAUJOLrRrEk4v2OyhIJ11wdiSi8Z0ElkilWiC1FFRBiS4kD8LilRAbsCtj4YV82qQM2A2ZvInPV4Kph6dmbGimXDQz1AAAAAAAAAIBwE1ma/90QoZQq58dXAAAAADhSL82XaQeyJRBnAAAAAElFTkSuQmCC',
  T2:'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAxUlEQVR42u3aOw2AMBSFYSDseKkIUNAFHOAABTjAAQtVgAm84ICNiZSSPrhN/rOy3K+cpLlJy61vi5xTFZkHAAAAAAB4pbZ80+suZEozdFQoxwq5/MGocekwFQIAAAAAAAAAAAAAAIDs6EV5bWS/TXlOYVbKBAcZdydONqUZj8ed2LKU1/+OGPEP6EXdFfw6cfApw1co5YgegGZ+raDce0DOGXMTAwAAAAAAAAAAAJAap4VGzpsDKiQvJc8uAQAAAABAzrkAZHojy0cT8bsAAAAASUVORK5CYII=',
};
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
      multipart:{file:{name:'r6-synthetic-'+label+'.png',mimeType:'image/png',buffer:Buffer.from(syntheticPngBase64[label],'base64')},
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

  // Real extension-only native Chromium zoom on DISPOSABLE GitHub Windows.
  // The extension has tabs metadata permission, not scripting, and can only
  // inspect the local T2 React URL. No production hosts/credentials/PHI.
  const winZoom=process.platform==='win32' &&
    process.env.GITHUB_ACTIONS==='true' &&
    process.env.LOT07_R7_WINDOWS_NATIVE==='1';
  let context;
  if(winZoom){
    isolatedWindowsProfile=await fs.mkdtemp(path.join(os.tmpdir(),'r7b-win-profile-'));
    isolatedWindowsExtension=await fs.mkdtemp(path.join(os.tmpdir(),'r7b-win-zoom-extension-'));
    await fs.writeFile(path.join(isolatedWindowsExtension,'manifest.json'),JSON.stringify({
      manifest_version:3,name:'LOT07 R7B local synthetic zoom oracle',version:'1.0',
      permissions:['tabs'],host_permissions:[webBase+'/*'],
      background:{service_worker:'worker.js'},
    }));
    await fs.writeFile(path.join(isolatedWindowsExtension,'worker.js'),
      'chrome.runtime.onInstalled.addListener(()=>{});\n');
    context=await chromium.launchPersistentContext(isolatedWindowsProfile,{
      channel:'chromium',headless:false,
      viewport:{width:1440,height:900},locale:'fr-FR',
      reducedMotion:'reduce',
      args:['--disable-gpu',
        '--disable-extensions-except='+isolatedWindowsExtension,
        '--load-extension='+isolatedWindowsExtension,
        '--no-first-run','--disable-background-networking'],
    });
    // A persistent context is closeable like a Browser; no other context is
    // created. The extension service worker must genuinely exist.
    browser=context;
    zoomWorker=context.serviceWorkers()[0]||
      await context.waitForEvent('serviceworker',{timeout:25000});
    check('r7b-native-chromium-extension-service-worker',
      zoomWorker.url().startsWith('chrome-extension://') &&
      await zoomWorker.evaluate(()=>Boolean(chrome.tabs?.setZoom && chrome.tabs?.getZoom)));
  } else {
    browser=await chromium.launch({headless:process.platform!=='win32'});
    context=await browser.newContext({
      viewport:{width:1440,height:900},locale:'fr-FR',
      reducedMotion:'reduce',serviceWorkers:'block',
    });
  }
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
      network.push({path:url.pathname,from:url.searchParams.get('from_ordinal'),to:url.searchParams.get('to_ordinal'),status:response.status()});
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

  // Genuine browser popup; child has only the static patient-facing projection.
  // No route intercept, bearer token, patient URL or second API client.
  await page.locator('[data-testid="r6d-patient-presenter-control"]')
    .waitFor({state:'visible',timeout:30000});
  check('r6d-presenter-open-enabled-for-authenticated-clinician',
    await page.getByRole('button',{name:'Ouvrir sur un autre écran'}).isEnabled());
  const windowPromise=page.waitForEvent('popup',{timeout:25000});
  await page.getByRole('button',{name:'Ouvrir sur un autre écran'}).click();
  const popup=await windowPromise;
  await popup.locator('[data-testid="r6d-readonly-presenter"]')
    .waitFor({state:'visible',timeout:25000});
  check('r6d-actual-browser-detached-window',
    popup.url().startsWith(apiBase+'/api/ortho/presenter-window?'));
  const isolated=await popup.evaluate(()=>{
    let localStorageDenied=false,cookieDenied=false;
    try{localStorage.getItem('token');}catch{localStorageDenied=true;}
    try{document.cookie;}catch{cookieDenied=true;}
    return {origin:window.origin,urlOrigin:location.origin,localStorageDenied,cookieDenied,
      openerNull:window.opener===null,scriptCount:document.scripts.length};
  });
  const opaqueShell=await api.get('/api/ortho/presenter-window');
  const csp=opaqueShell.headers()['content-security-policy']||'';
  check('r6d-patient-window-HTTP-CSP-opaque-origin',
    opaqueShell.status()===200 && csp.includes('sandbox allow-scripts') &&
    !csp.includes('allow-same-origin') &&
    isolated.origin==='null' && isolated.localStorageDenied &&
    isolated.cookieDenied && isolated.openerNull &&
    isolated.scriptCount===0 && csp.includes("script-src 'sha256-") &&
    !csp.includes("script-src 'unsafe-inline'"),{status:opaqueShell.status(),security:isolated,
      cspHeaderSandbox:csp.includes('sandbox allow-scripts')});
  check('r6d-three-canonic-panels',
    await popup.locator('[data-r6d-ordinal]').count()===3);
  check('r6d-readonly-no-controls',
    await popup.locator('button,input,form,textarea,select,a').count()===0);
  const projected=await popup.locator('body').innerText();
  check('r6d-only-canonical-source-ids',Object.values(clinicalAssets).every(
    id=>projected.includes('source #'+id)));
  check('r6d-no-clinical-notes-credentials',
    !projected.includes('R6_PRIVATE_SYNTHETIC_NOTE_DO_NOT_RENDER') &&
    !projected.includes(auth.access_token) &&
    !projected.includes(patient.numero_dossier) &&
    !popup.url().includes('/patients/'));
  await capture(popup,'r6d-02-detached-readonly-1440');

  for(const [from,to] of [[0,1],[1,2],[0,2]]) {
    const cached=network.find(r=>r.path==='/api/patients/'+patient.id+'/ortho-case/'+caseId+'/compare' &&
      r.from===String(from) && r.to===String(to) && r.status===200);
    const watch=cached ? null : page.waitForResponse(r=>{
      const u=new URL(r.url());
      return u.pathname==='/api/patients/'+patient.id+'/ortho-case/'+caseId+'/compare' &&
        u.searchParams.get('from_ordinal')===String(from) &&
        u.searchParams.get('to_ordinal')===String(to);
    },{timeout:40000});
    await triple.getByRole('button',{name:'T'+from+' → T'+to,exact:true}).click();
    check('real-click-selected-pair-'+from+'-'+to,
      await triple.getByRole('button',{name:'T'+from+' → T'+to,exact:true})
        .getAttribute('aria-pressed')==='true');
    const responseStatus=watch ? (await watch).status() : cached.status;
    check('real-browser-response-pair-'+from+'-'+to,responseStatus===200,
      {status:responseStatus,previouslyObserved:Boolean(cached)});
    await page.locator('[data-ortho-f3-compare]').getByText('Mesures communes',{exact:true})
      .waitFor({state:'visible',timeout:25000});
    await page.waitForFunction(({from,to}) => { const a=Array.from(document.querySelectorAll('[data-ortho-compare-timepoint]'), el=>Number(el.getAttribute('data-ortho-compare-timepoint'))); return a.length===2 && a[0]===from && a[1]===to; }, {from,to},{timeout:25000});
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
  check('r6d-popup-closed-on-patient-B',await popup.isClosed());
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

  if(process.env.LOT07_R7_DESKTOP_CERT === '1') {
    await verifyR7DesktopMatrix({
      context, webBase, patient, patientB, clinicalAssets, check, capture, report,
      zoomWorker,
    });
  }
  check('no-unhandled-browser-errors',errors.length===0,{errors:errors.slice(0,2)});
  report.pass=report.checks.every(c=>c.pass) && report.screenshots.length>=6;
  console.log('LOT07_R6D_FUE_I_PASS',report.checks.length,sha);
} catch(error) {
  report.error=String(error?.stack||error).slice(0,1400);
  if(page)try {await capture(page,'failure-snapshot');}catch{/* page may have closed */}
  throw error;
} finally {
  await fs.writeFile(path.join(directory,'report.json'),JSON.stringify(report,null,2));
  await browser?.close();
  if(isolatedWindowsExtension)await fs.rm(isolatedWindowsExtension,{
    recursive:true,force:true,maxRetries:6,retryDelay:150,
  }).catch(()=>{});
  if(isolatedWindowsProfile)await fs.rm(isolatedWindowsProfile,{
    recursive:true,force:true,maxRetries:6,retryDelay:150,
  }).catch(()=>{});
  for(const context of contexts)await context.dispose();
  await api.dispose();
  console.log('LOT07_R6D_FUE_I_RESULT',JSON.stringify({
    sha,pass:report.pass,checks:report.checks.length,screenshots:report.screenshots.length,
    error:report.error,
  }));
}
