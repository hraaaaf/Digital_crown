/**
 * CB-01 ONLY — real NVDA speech verification using the real MainLayout + CrownBotChat + real FastAPI in a disposable T2 runtime.
 *
 * This is NOT an axe/ARIA tree mock: PASS requires actual Guidepup NVDA
 * speech output captured after NVDA was started and driven on Windows.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';
import { nvda } from '@guidepup/guidepup';

const head = process.env.CB01_SOURCE_HEAD;
if (process.platform !== 'win32'
    || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.CB01_NVDA_EXPERIMENT !== '1'
    || process.env.CB01_NVDA_ZOOM_EXPERIMENT !== '1'
    || !/^[a-f0-9]{40}$/.test(head || '')) {
  throw new Error('REFUSED: CB-01 Windows-only combined native zoom + NVDA isolated test');
}
const origin = 'http://127.0.0.1:5173';
const target = origin + '/dashboard';
const apiOrigin='http://127.0.0.1:8005';
if(process.env.T2_USER!=='t2-browser@cabinet.ma' ||
   process.env.T2_S05_USER!=='t2-s05-reception@cabinet.ma' ||
   process.env.T2_S06_USER!=='t2-s06-no-agenda@cabinet.ma' ||
   !process.env.T2_PASSWORD || !process.env.T2_S05_PASSWORD || !process.env.T2_S06_PASSWORD)
  throw new Error('REFUSED: isolated synthetic accounts missing');
const out = path.resolve('../artifacts/cb01-windows-fueg-combined');
await fs.mkdir(out, { recursive: true });
const extensionPath = await fs.mkdtemp(path.join(os.tmpdir(),'cb01-nvda-zoom-ext-'));
const profilePath = await fs.mkdtemp(path.join(os.tmpdir(),'cb01-nvda-zoom-profile-'));
await fs.writeFile(path.join(extensionPath,'manifest.json'),JSON.stringify({
  manifest_version:3, name:'CB01 NVDA Native Zoom Evidence', version:'1.0.0',
  permissions:['tabs'], host_permissions:[origin+'/*'],
  background:{service_worker:'service-worker.js'},
}));
await fs.writeFile(path.join(extensionPath,'service-worker.js'),
  'chrome.runtime.onInstalled.addListener(() => {});\n');
const report = {
  schema: 'CB01_WINDOWS_FUEG_FULL_FASTAPI_NVDA_ZOOM_V1',
  evidenceType: 'REAL_NVDA_AND_EXTENSION_GETZOOM_IN_SAME_CHROMIUM_TAB',
  sourceScope: 'REAL_MAINLAYOUT_REAL_FASTAPI_SYNTHETIC_DB',
  zoomKind: 'CHROME_EXTENSION_TABS_SETZOOM_GETZOOM',
  nativeZoomAtSpeech: 'NOT_RUN',
  zoomBefore: null,
  zoomAtSpeech: null,
  zoomMeasurements: null,
  browserVersion: null,
  simultaneousPass: false,
  sourceHead: head,
  scope: 'CABINET_WEB_MAINLAYOUT_STAFF_S05_SYNTHETIC',
  nvdaStarted: false,
  nvdaSpeechCaptured: 'NOT_RUN',
  spokenPhrases: [],
  lastSpokenPhrase: null,
  observedTerms: [],
  observedAccessibleControls: {},
  keyboardActions: [],
  screenshots: [],
  clinicalWritesAttempted: [],
  actualClinicalBackend: 'REAL_LOCAL_FASTAPI_SYNTHETIC_DB',
  apiMockCount: 0,
  roleProof:{s05:'NOT_RUN',s06:'NOT_RUN'},
  firstValue:{status:'NOT_RUN',elapsedMs:null,clicks:0,typedAnswers:0,httpStatuses:[],noActionId:false},
  clinicalState:'NOT_PROVEN',
  speechHardwareAudioRecording: 'NOT_RUN',
  nvdaHumanReview: 'NOT_RUN',
  nvdaOsFocusProbes: [],
  nvdaSpeechProbe: 'NOT_RUN',
  frontendStartup: {pageErrors:[],failedRequests:[],httpFailures:[],routes:[],initialAuthStatus:'NOT_RUN',clinicInitStatus:'NOT_RUN',snapshot:null},
  converged: false,
  error: null,
};
const expectedTerms = [
  { key:'chat', re: /\bchat\b/i },
  { key:'memory', re: /mémoire\s+contextuelle/i },
  { key:'programme', re: /mon\s+programme/i },
  { key:'find_patient', re: /trouver\s+un\s+patient/i },
  { key:'rdv', re: /préparer\s+un\s+rdv/i },
];
// Match real NVDA spoken *roles*, not incidental words in instructional prose.
// NVDA speech genuinely uses both "role, name" and "name, role"
// depending on virtual cursor vs form-field navigation. Require complete
// labels and actual spoken role; never derive PASS from DOM or prose.
const expectedControls = {
  brainTab: /^(?:tab,\s*(?:selected,\s*)?Mémoire contextuelle|Mémoire contextuelle,\s*tab(?:,\s*selected)?)(?:,|$)/iu,
  chatTab: /^(?:tab,\s*(?:selected,\s*)?Chat|Chat,\s*tab(?:,\s*selected)?)(?:,|$)/iu,
  programmeButton: /^(?:button,\s*Mon programme|Mon programme,\s*button)(?:,|$)/iu,
  findPatientButton: /^(?:button,\s*Trouver un patient|Trouver un patient,\s*button)(?:,|$)/iu,
  rdvButton: /^(?:button,\s*Préparer un RDV|Préparer un RDV,\s*button)(?:,|$)/iu,
};
function spokenControlStatus(phrases) {
  return Object.fromEntries(Object.entries(expectedControls).map(([key, regexp]) => [
    key, phrases.some(phrase => regexp.test(String(phrase).trim())),
  ]));
}
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let server = null;
let browser = null;
let nvdaActive = false;
let zoomWorker = null;
let apiOwner=null, apiStaff=null, staffToken=null;
let activePage=null;

async function waitForLocal() {
  for (let i = 0; i < 40; i++) {
    if (server?.exitCode!==null) throw new Error('Vite child terminated before test');
    try {
      const response = await fetch(target,{signal:AbortSignal.timeout(1200)});
      if (response.ok) return;
    } catch {}
    await sleep(1000);
  }
  throw new Error('Isolated Vite was not reachable');
}
function readTerms(phrases) {
  const joined=phrases.join('\n');
  return expectedTerms.filter(term=>term.re.test(joined)).map(term=>term.key);
}
async function captureSpeech(stage) {
  const lines=await nvda.spokenPhraseLog();
  const phrases=Array.isArray(lines)?lines.map(v=>String(v)):[String(lines)];
  report.spokenPhrases=phrases.slice(-250);
  report.observedTerms=readTerms(phrases);
  report.observedAccessibleControls=spokenControlStatus(phrases);
  report.lastSpokenPhrase=await nvda.lastSpokenPhrase();
  console.log('CB01_NVDA_SPOKEN_STAGE',JSON.stringify({
    stage,phraseCount:phrases.length,terms:report.observedTerms,
    roles:report.observedAccessibleControls,
    latest:report.lastSpokenPhrase?.slice(0,250),
  }));
}
async function nativeZoom(worker, factor) {
  const result = await worker.evaluate(async factor => {
    const tabs = await chrome.tabs.query({});
    const tab = tabs.find(t => t.url?.startsWith('http://127.0.0.1:5173/dashboard'));
    if (!tab?.id) throw new Error('Extension could not locate synthetic Crown Bot tab');
    await chrome.tabs.setZoom(tab.id, factor);
    return {tabId:tab.id, observed:await chrome.tabs.getZoom(tab.id)};
  },factor);
  if (!(Math.abs(result.observed - factor) < 0.01)) throw new Error('REFUSED: native zoom not actually '+factor);
  // 
  // checked above
  return result;
}

async function readNativeZoom(worker) {
  return worker.evaluate(async () => {
    const tabs=await chrome.tabs.query({});
    const matches=tabs.filter(tab => tab.url?.startsWith('http://127.0.0.1:5173/dashboard'));
    if (matches.length !== 1 || !matches[0].id) throw new Error('REFUSED: no unique target zoom tab');
    return {tabId:matches[0].id, observed:await chrome.tabs.getZoom(matches[0].id)};
  });
}
async function inspectZoomLayout(page) {
  return page.evaluate(() => ({
    innerWidth:window.innerWidth, devicePixelRatio:window.devicePixelRatio,
    scrollWidth:document.documentElement.scrollWidth,
    clientWidth:document.documentElement.clientWidth,
  }));
}
try {
  server=spawn(process.execPath,[
    path.resolve('node_modules/vite/bin/vite.js'),
    '--host','127.0.0.1','--port','5173','--strictPort',
  ],{
    cwd:process.cwd(),
    env:{
      ...process.env,
      VITE_CB01_NATIVE_A11Y_LAB:'false',
      VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED:'true',
      VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED:'true',
      VITE_TELEMETRY_ENABLED:'false',
    },
    stdio:['ignore','pipe','pipe'],windowsHide:true,
  });
  server.stdout.on('data',x=>process.stdout.write('[vite] '+String(x)));
  server.stderr.on('data',x=>process.stderr.write('[vite] '+String(x)));
  await waitForLocal();
  // Real API bootstrap on loopback only. The owner enrolls the device;
  // independent staff credentials may use the same tenant-scoped device cookie.
  apiOwner=await request.newContext({baseURL:apiOrigin,storageState:{cookies:[],origins:[]}});
  const ownerLogin=await apiOwner.post('/api/auth/login',{
    form:{username:process.env.T2_USER,password:process.env.T2_PASSWORD},
  });
  if(ownerLogin.status()!==200)throw Error('FAIL: synthetic owner login '+ownerLogin.status());
  const ownerToken=(await ownerLogin.json()).access_token;
  if(!ownerToken)throw Error('FAIL: no owner token');
  const enrolled=await enrollT2Workstation(apiOwner,ownerToken,process.env.T2_PASSWORD);
  const stationCookies=enrolled.cookies.filter(c=>c.name==='dc_workstation');
  if(stationCookies.length!==1||stationCookies[0].httpOnly!==true)
    throw Error('REFUSED: owner did not enroll workstation');
  for(const [kind,user,password]of [
    ['s06',process.env.T2_S06_USER,process.env.T2_S06_PASSWORD],
    ['s05',process.env.T2_S05_USER,process.env.T2_S05_PASSWORD],
  ]){
    const loginApi=await request.newContext({baseURL:apiOrigin,storageState:{cookies:[],origins:[]}});
    try{
      const login=await loginApi.post('/api/auth/login',{form:{username:user,password}});
      if(login.status()!==200)throw Error('FAIL: '+kind+' login '+login.status());
      const token=(await login.json()).access_token;
      const roleState=await loginApi.storageState();
      if(roleState.cookies.filter(c=>c.name==='access_token'&&c.value===token).length!==1
          || roleState.cookies.some(c=>c.name==='dc_workstation'))
        throw Error('REFUSED: '+kind+' principal not isolated');
      const roleApi=await request.newContext({baseURL:apiOrigin,
        storageState:{cookies:[...roleState.cookies,...stationCookies],origins:[]}});
      const boot=await roleApi.get('/api/workstation/bootstrap',{
        headers:{Authorization:'Bearer '+token}});
      if(boot.status()!==200||(await boot.json()).enrollmentRequired!==false)
        throw Error('FAIL: '+kind+' workstation rejected '+boot.status());
      const peek=await roleApi.post('/api/bot/workflows/preview',{data:{messages:['/rdv']},
        headers:{Authorization:'Bearer '+token}});
      if(peek.status()!==(kind==='s06'?403:200))
        throw Error('FAIL: '+kind+' wrong RBAC HTTP '+peek.status());
      if(kind==='s06'){
        const detail=await peek.json();
        if(detail?.detail!=='Accès refusé.'||JSON.stringify(detail).includes('T2-0001'))
          throw Error('FAIL: S06 leaked patient or missed denial');
        report.roleProof.s06='PASS_REAL_HTTP_403_NO_PATIENT';
        await roleApi.dispose();
      }else{
        report.roleProof.s05='PASS_REAL_HTTP_200_PREVIEW_ONLY';
        apiStaff=roleApi;
        staffToken=token;
      }
    } finally {await loginApi.dispose();}
  }
  if(!apiStaff||!staffToken)throw Error('REFUSED: no valid S05 session');
  // Read-only runtime probes before mounting React: never silently infer a
  // healthy Cabinet UI from successful login or workstation enrollment.
  const meProbe=await apiStaff.get('/api/auth/me',{headers:{Authorization:'Bearer '+staffToken}});
  report.frontendStartup.initialAuthStatus=meProbe.status();
  const initProbe=await apiStaff.get('/api/clinics/init-status',{headers:{Authorization:'Bearer '+staffToken}});
  report.frontendStartup.clinicInitStatus=initProbe.status();
  if(meProbe.status()!==200 || initProbe.status()!==200)
    throw Error('FAIL: synthetic staff real Cabinet auth/init preflight not 200');

  // NVDA reads the real operating system accessibility stack, which needs a
  // headed browser/window. Headless or Playwright's accessibility tree is NOT proof.
  browser=await chromium.launchPersistentContext(profilePath,{
    channel:'chromium', headless:false, viewport:{width:1920,height:900},
    args:['--disable-extensions-except='+extensionPath,
      '--load-extension='+extensionPath,
      '--no-first-run','--disable-background-networking'],
  });
  report.browserVersion=browser.browser()?.version()||'chromium-persistent';
  zoomWorker=browser.serviceWorkers()[0]||await browser.waitForEvent('serviceworker',{timeout:20000});
  if (!zoomWorker.url().startsWith('chrome-extension://')) throw new Error('REFUSED: native zoom extension not running');
  // Keep the initial tab: in a headed persistent Chromium profile, closing its
  // last tab can terminate the entire browser before newPage() is called.
  // Reuse it for the same isolated lab URL, rather than weakening any evidence.
  const page=browser.pages()[0] || await browser.newPage();
  activePage=page;
  // Only error categories, safe local URL pathnames and bounded exceptions;
  // never dump cookies, patient values, auth headers or full HTTP bodies.
  const safeMessage=value=>String(value||'').slice(0,240)
    .replace(/[A-Za-z0-9_-]{30,}\\.[A-Za-z0-9_-]{30,}\\.[A-Za-z0-9_-]{30,}/g,'[REDACTED_JWT]');
  page.on('pageerror',err=>{if(report.frontendStartup.pageErrors.length<12)
    report.frontendStartup.pageErrors.push(safeMessage(err?.message));});
  page.on('console',msg=>{if(msg.type()==='error'&&report.frontendStartup.pageErrors.length<12)
    report.frontendStartup.pageErrors.push('console: '+safeMessage(msg.text()));});
  page.on('requestfailed',req=>{if(report.frontendStartup.failedRequests.length<20) {
    const u=new URL(req.url());
    if(['127.0.0.1','localhost'].includes(u.hostname))
      report.frontendStartup.failedRequests.push({path:u.pathname,method:req.method(),reason:safeMessage(req.failure()?.errorText)});
  }});
  page.on('response',resp=>{if(resp.status()>=400&&report.frontendStartup.httpFailures.length<20){
    const u=new URL(resp.url());
    if(['127.0.0.1','localhost'].includes(u.hostname))
      report.frontendStartup.httpFailures.push({path:u.pathname,status:resp.status()});
  }});
  page.on('framenavigated',frame=>{if(frame===page.mainFrame()&&report.frontendStartup.routes.length<16)
    report.frontendStartup.routes.push(new URL(frame.url()).pathname);});
  page.on('request',req=>{
    const p=new URL(req.url()).pathname;
    if(req.method()!=='GET'
      && /\/api\/(?:bot\/execute|appointments\/?|patients\/?|devis\/?)/.test(p))
      report.clinicalWritesAttempted.push(req.method()+' '+p);
  });
  // NO page.route API mocking: every /api request reaches the real T2 FastAPI.
  if(!apiStaff)throw new Error('REFUSED: no role-scoped FastAPI authentication');
  const staffState=await apiStaff.storageState();
  if(staffState.cookies.filter(c=>c.name==='access_token').length!==1
      || staffState.cookies.filter(c=>c.name==='dc_workstation').length!==1)
    throw new Error('REFUSED: wrong staff+station cookies');
  await browser.addCookies(staffState.cookies);
  await browser.addInitScript(token=>{
    localStorage.setItem('token',token);
    localStorage.setItem('appMode','prod');
  },staffToken);
  await page.goto(target,{waitUntil:'domcontentloaded',timeout:45000});
  if(new URL(page.url()).pathname!=='/dashboard')throw new Error('FAIL: real MainLayout session redirected');
  try {
    await page.locator('main').first().waitFor({state:'visible',timeout:30000});
  } catch(err) {
    // A missing MainLayout may mean real auth/setup redirect, a React crash,
    // missing dynamic JS, a loading guard, or a failed API request. Capture
    // these distinctions before STOP; never retry or accept a fake main.
    report.frontendStartup.snapshot=await page.evaluate(()=>({
      pathname:location.pathname,documentTitle:document.title,
      readyState:document.readyState,rootPresent:!!document.getElementById('root'),
      rootChildren:document.getElementById('root')?.childElementCount ?? -1,
      mainPresent:!!document.querySelector('main'),
      loginVisible:!!document.querySelector('input[type=password]'),
      errorBoundaryVisible:document.body?.innerText?.includes('Erreur Inattendue')||false,
      loaderVisible:document.body?.innerText?.includes('Démarrage de Digital Crown')||false,
      appModePresent:!!localStorage.getItem('appMode'),
      authTokenPresent:!!localStorage.getItem('token'),
    })).catch(e=>({diagnosticError:String(e?.name||'unknown')}));
    await page.screenshot({path:path.join(out,'cb01-fueg-mainlayout-failed.png'),fullPage:false}).then(()=>
      report.screenshots.push('cb01-fueg-mainlayout-failed.png')).catch(()=>{});
    throw Error('NOT_CERTIFIED: real Cabinet MainLayout did not mount; '+
      JSON.stringify(report.frontendStartup));
  }
  const launcher=page.getByRole('button',{name:'Ouvrir CrownBot'});
  await launcher.waitFor({state:'visible',timeout:30000});
  await page.screenshot({path:path.join(out,'cb01-fueg-dashboard-before.png')});
  report.screenshots.push('cb01-fueg-dashboard-before.png');
  const fueStartedAt=performance.now();
  await launcher.click();
  const panel=page.locator('[data-cb01-associate-sidecar], [data-ux1-c-crownbot-overlay]');
  await panel.waitFor({state:'visible',timeout:30000});
  if(!await page.locator('[data-cb01-associate-sidecar]').isVisible())
    throw Error('FAIL: native 100% desktop did not show the real B Sidecar');
  const chat=panel.getByRole('tab',{name:'Chat',exact:true});
  await chat.waitFor({state:'visible',timeout:20000});
  for(const label of ['Mon programme','Trouver un patient','Préparer un RDV'])
    await panel.getByRole('button',{name:label}).waitFor();
  await page.bringToFront();
  report.zoomBefore=await nativeZoom(zoomWorker,1);
  const at100=await inspectZoomLayout(page);
  await page.screenshot({path:path.join(out,'cb01-combined-100.png')});
  report.screenshots.push('cb01-combined-100.png');
  await nativeZoom(zoomWorker,2);
  const at200=await inspectZoomLayout(page);
  report.zoomMeasurements={at100,at200};
  const floatingPanel=page.locator('[data-ux1-c-crownbot-overlay]');
  await floatingPanel.waitFor({state:'visible',timeout:30000});
  if(await page.locator('[data-cb01-associate-sidecar]').count())
    throw Error('FAIL: native 200% retained desktop sidecar instead of responsive overlay');
  // BEFORE this fix the 600px-tall fixed popup sat above a 450px viewport,
  // and the focused Chat tab was physically offscreen at top=-192px. Native
  // zoom is not accessible merely because an element is DOM-visible.
  const popupGeometry=await floatingPanel.evaluate(el=>{
    const box=el.getBoundingClientRect();
    return {top:box.top,bottom:box.bottom,height:box.height,
      viewportHeight:window.innerHeight};
  });
  report.zoomMeasurements.floatingPanelAt200=popupGeometry;
  if(popupGeometry.top<4 || popupGeometry.bottom>popupGeometry.viewportHeight-4)
    throw Error('NOT_CERTIFIED: CB-01 floating assistant escaped native 200% viewport; '+
      JSON.stringify(popupGeometry));
  const bounds=await Promise.all([
    panel.getByRole('tab',{name:'Chat',exact:true}),
    panel.getByRole('tab',{name:/Mémoire contextuelle/}),
    ...['Mon programme','Trouver un patient','Préparer un RDV']
      .map(label=>panel.getByRole('button',{name:label,exact:true})),
  ].map(async control=>control.evaluate(el=>{
    const r=el.getBoundingClientRect();
    return {top:r.top,bottom:r.bottom,viewportHeight:window.innerHeight};
  })));
  report.zoomMeasurements.controlBoundsAt200=bounds;
  if(bounds.some(r=>r.top<0||r.bottom>r.viewportHeight||r.bottom<=r.top))
    throw Error('NOT_CERTIFIED: required screen-reader controls outside native 200% viewport; '+
      JSON.stringify(bounds));
  if (!(at200.innerWidth<at100.innerWidth && at200.innerWidth<=Math.ceil(at100.innerWidth*0.6)
      && at200.devicePixelRatio>at100.devicePixelRatio
      && at200.scrollWidth<=at200.clientWidth+2))
    throw new Error('NOT_CERTIFIED: zoom 200% has no native reflow or causes page overflow');
  for(const label of ['Mon programme','Trouver un patient','Préparer un RDV']) {
    if (!(await panel.getByRole('button',{name:label,exact:true}).isVisible()))
      throw new Error('NOT_CERTIFIED: inaccessible button at native 200%: '+label);
  }
  // Check focus on real tabs at 200%, before NVDA starts reading the same tab.
  await chat.focus();
  await page.keyboard.press('ArrowLeft');
  const brain=panel.getByRole('tab',{name:/Mémoire contextuelle/});
  if (await brain.getAttribute('aria-selected')!=='true'||!await brain.evaluate(el=>el===document.activeElement))
    throw new Error('NOT_CERTIFIED: 200% roving keyboard tab focus failed');
  await page.keyboard.press('End');
  if (await chat.getAttribute('aria-selected')!=='true'||!await chat.evaluate(el=>el===document.activeElement))
    throw new Error('NOT_CERTIFIED: 200% chat focus restoration failed');
  await page.screenshot({path:path.join(out,'cb01-combined-200-before-nvda.png')});
  report.screenshots.push('cb01-combined-200-before-nvda.png');
  const measured=await readNativeZoom(zoomWorker);
  if (measured.observed!==2)throw new Error('NOT_CERTIFIED: zoom drifted before NVDA startup');

  // Must actually START NVDA. No NVDA process/spoken text => hard failure,
  // not green accessibility despite visible DOM ARIA.
  await nvda.start();
  nvdaActive=true;
  report.nvdaStarted=true;
  await nvda.clearSpokenPhraseLog();
  await sleep(800);

  // Unlike the isolated NVDA laboratory, a full MainLayout may leave Windows
  // focus in another application after NVDA.start(). Re-anchor the *OS*
  // Chromium window using real keyboard events, and verify the actual window
  // title spoken by NVDA. DOM focus alone must never be counted as speech.
  for (let attempt=1;attempt<=3;attempt++) {
    await page.bringToFront();
    await chat.scrollIntoViewIfNeeded();
    await chat.focus();
    await page.keyboard.press('Tab');
    await page.keyboard.press('Shift+Tab');
    if(!await chat.evaluate(el=>el===document.activeElement))
      await chat.focus();
    await nvda.perform(nvda.keyboardCommands.reportTitle);
    const spokenTitle=String((await nvda.lastSpokenPhrase())||'');
    const actualFocus=await chat.evaluate(el=>({
      documentTitle:document.title,
      chatFocused:el===document.activeElement,
      ariaHiddenAncestor:Boolean(el.closest('[aria-hidden="true"],[inert]')),
      boundingBox:(()=>{
        const r=el.getBoundingClientRect();
        return {top:Math.round(r.top),bottom:Math.round(r.bottom),
          viewportHeight:window.innerHeight};
      })(),
    }));
    report.nvdaOsFocusProbes.push({
      attempt,spokenWindowTitle:spokenTitle.slice(0,120),
      chatFocused:actualFocus.chatFocused,
      ariaHiddenAncestor:actualFocus.ariaHiddenAncestor,
      box:actualFocus.boundingBox,
    });
    if(actualFocus.ariaHiddenAncestor)
      throw Error('NOT_CERTIFIED: assistant tab hidden or inert in real MainLayout');
    if(actualFocus.chatFocused && /Digital Crown/i.test(spokenTitle)) break;
    // Only if focus verification fails: move between real OS windows, then
    // re-activate the Playwright-owned browser. Never mock a NVDA announcement.
    if(attempt<3) {
      await nvda.press('Alt+Escape');
      await sleep(500);
    }
  }
  if(!report.nvdaOsFocusProbes.some(p=>
      p.chatFocused && /Digital Crown/i.test(p.spokenWindowTitle)))
    throw Error('NOT_CERTIFIED: NVDA did not report foreground Digital Crown window; focus probes='+JSON.stringify(report.nvdaOsFocusProbes));

  await nvda.clearSpokenPhraseLog();
  await nvda.next();
  report.keyboardActions.push('NVDA.next.focus-probe');
  await captureSpeech('focused-app-initial');
  if(!report.spokenPhrases.some(phrase=>String(phrase).trim())) {
    // Diagnose missing real speech in seconds, rather than issuing 135 empty
    // NVDA commands for minutes. The 5/5 speech oracle remains mandatory.
    for(let attempt=1;attempt<=4;attempt++) {
      await nvda.next();
      report.keyboardActions.push('NVDA.next.focus-probe-'+attempt);
      await captureSpeech('focused-app-retry-'+attempt);
      if(report.spokenPhrases.some(phrase=>String(phrase).trim())) break;
    }
    if(!report.spokenPhrases.some(phrase=>String(phrase).trim()))
      throw Error('NOT_CERTIFIED: NVDA emitted no real speech after Windows foreground focus, 5 OS-level navigation attempts');
  }
  report.nvdaSpeechProbe='PASS_REAL_NONEMPTY_NVDA_PHRASE_IN_FULL_MAINLAYOUT';
  // Trigger real OS-level NVDA navigation, recording each command.
  // NVDA.next() navigates the screen reader virtual cursor, not Playwright DOM.
  for(let n=0;n<80;n++){
    await nvda.next();
    report.keyboardActions.push('NVDA.next');
    if(n%5===4) {
      await captureSpeech('next-'+(n+1));
      if(Object.values(report.observedAccessibleControls).every(Boolean)) break;
    }
  }
  // NVDA's initial virtual cursor is not guaranteed to start before both tabs.
  // Exercise genuine reverse NVDA navigation before declaring a missing control;
  // this preserves the strict 5/5 spoken role+name oracle (no DOM/ARIA fallback).
  if (!Object.values(report.observedAccessibleControls).every(Boolean)) {
    for (let n=0; n<35; n++) {
      await nvda.previous();
      report.keyboardActions.push('NVDA.previous');
      if (n%3===2) {
        await captureSpeech('previous-'+(n+1));
        if (Object.values(report.observedAccessibleControls).every(Boolean)) break;
      }
    }
    await captureSpeech('previous-final');
  }
  // NVDA-specific form navigation if virtual-cursor reading did not reach
  // all three CTA controls. Output still comes from the real NVDA speech log.
  if(!Object.values(report.observedAccessibleControls).every(Boolean)) {
    for(let i=0;i<20;i++){
      await nvda.perform(nvda.keyboardCommands.moveToNextFormField);
      report.keyboardActions.push('NVDA.moveToNextFormField');
      await captureSpeech('form-'+(i+1));
      if(Object.values(report.observedAccessibleControls).every(Boolean)) break;
    }
  }
  await captureSpeech('final');
  report.zoomAtSpeech=await readNativeZoom(zoomWorker); // read only: never setZoom here, cannot hide drift
  if (Math.abs(report.zoomAtSpeech.observed-2)>0.01
      || report.zoomAtSpeech.tabId!==report.zoomBefore.tabId)
    throw new Error('NOT_CERTIFIED: real NVDA speech not coincident with 200% native zoom on same tab');
  report.nativeZoomAtSpeech='PASS_VERIFIED_GETZOOM_2';
  await page.screenshot({path:path.join(out,'cb01-combined-200-after-nvda.png')});
  report.screenshots.push('cb01-combined-200-after-nvda.png');
  const missing=Object.entries(report.observedAccessibleControls)
    .filter(([,announced])=>!announced).map(([key])=>key);
  if(missing.length) {
    throw new Error('NOT_CERTIFIED: NVDA did not announce required role+name controls: '
      +JSON.stringify({ missing, observed:report.observedAccessibleControls,
        phrases:report.spokenPhrases.slice(-30) }));
  }
  if(report.clinicalWritesAttempted.length) {
    throw new Error('Clinical mutation was attempted during NVDA screen reader lab');
  }
  report.nvdaSpeechCaptured='PASS_REAL_NVDA_SPOKEN_PHRASES';
  report.simultaneousPass=true;
  // At this point real NVDA has spoken on the same native-zoomed tab.
  // Now complete the first meaningful FUE-C server result in that tab.
  const preview=panel.getByRole('region',{name:'Assistant Crown Bot — consultation'});
  await preview.waitFor({state:'visible',timeout:15000});
  const requestStatuses=[];
  const onPreviewResponse=resp=>{
    if(new URL(resp.url()).pathname==='/api/bot/workflows/preview'
       && resp.request().method()==='POST')requestStatuses.push(resp.status());
  };
  page.on('response',onPreviewResponse);
  const rdv=preview.getByRole('button',{name:'Préparer un RDV'});
  await rdv.click();
  await preview.getByText('Patient : saisissez un identifiant',{exact:false}).waitFor();
  const send=async(value,expected)=>{
    await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill(value);
    await preview.getByRole('button',{name:'Envoyer'}).click();
    await preview.getByText(expected,{exact:false}).waitFor();
  };
  await send('dossier:T2-0001','Date du rendez-vous au format');
  await send('2099-01-01','Heure du rendez-vous au format');
  await send('10:00','Durée : 15, 30, 45 ou 60');
  await send('30','Motif : consultation, détartrage ou couronne');
  await send('consultation','Tapez CONFIRMER');
  await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill('CONFIRMER');
  const finalResult=page.waitForResponse(resp=>
    new URL(resp.url()).pathname==='/api/bot/workflows/preview'
    && resp.request().method()==='POST', {timeout:30000});
  await preview.getByRole('button',{name:'Envoyer'}).click();
  const finalResponse=await finalResult, finalData=await finalResponse.json();
  const serialized=JSON.stringify(finalData);
  if(finalResponse.status()!==200||finalData?.status!=='proposal_only'
     ||finalData?.proposal?.type!=='CREATE_APPOINTMENT'
     ||finalData?.proposal?.params?.datetime_start!=='2099-01-01T10:00:00'
     ||finalData?.proposal?.params?.duration_minutes!==30
     ||!Number.isInteger(finalData?.proposal?.params?.patient_id)
     ||['pending_action_id','pendingActionId','action_id','actionId']
       .some(key=>serialized.includes('"'+key+'"')))
    throw Error('FAIL: FUE-G resulted in executable/invalid proposal');
  await preview.getByText('Rendez-vous proposé : aperçu uniquement, non enregistré et non exécutable.').waitFor();
  const elapsedMs=Math.round(performance.now()-fueStartedAt);
  if(elapsedMs<=0||requestStatuses.length!==7||requestStatuses.some(x=>x!==200))
    throw Error('FAIL: incomplete FUE-G FastAPI response chain');
  report.firstValue={status:'PASS_REAL_FASTAPI_PROPOSAL_ONLY_VISIBLE_AT_NATIVE_200',
    elapsedMs,clicks:8,typedAnswers:6,httpStatuses:requestStatuses,noActionId:true};
  report.zoomAfterFUE=await readNativeZoom(zoomWorker);
  if(report.zoomAfterFUE.tabId!==report.zoomAtSpeech.tabId
       ||Math.abs(report.zoomAfterFUE.observed-2)>0.01)
    throw Error('FAIL: zoom/page changed between NVDA speech and FUE first value');
  await page.screenshot({path:path.join(out,'cb01-fueg-native-200-proposal.png')});
  report.screenshots.push('cb01-fueg-native-200-proposal.png');
  if(report.clinicalWritesAttempted.length)throw Error('FAIL: clinical writes attempted');
  report.clinicalState='NO_CLINICAL_WRITE_ATTEMPT_BROWSER_DB_DIFF_SEPARATE_GATE';
  console.log('CB01_WINDOWS_FUEG_FULL_FASTAPI_NVDA_ZOOM: PASS',JSON.stringify({
    sourceHead:head,terms:report.observedTerms,roles:report.observedAccessibleControls,
    spoken:report.spokenPhrases.length,keyboardActions:report.keyboardActions.length,
    nativeZoomAtSpeech:report.zoomAtSpeech.observed,
    clinicalWrites:report.clinicalWritesAttempted.length,
  }));
} catch(err) {
  report.error=String(err?.stack||err);
  report.nvdaSpeechCaptured='NOT_CERTIFIED';
  console.error('CB01_WINDOWS_FUEG_FULL_FASTAPI_NVDA_ZOOM: NOT_CERTIFIED',report.error);
  process.exitCode=1;
} finally {
  try {if(nvdaActive)await nvda.stop();}catch(e){
    console.error('CB01_NVDA_CLEANUP_FAILURE',String(e));
    report.nvdaCleanupError=String(e);
    process.exitCode=1;
  }
  try {await browser?.close();}catch {}
  try {await apiStaff?.dispose();}catch {}
  try {await apiOwner?.dispose();}catch {}
  if(server?.exitCode===null)server.kill();
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  await fs.rm(extensionPath,{recursive:true,force:true}).catch(()=>{});
  await fs.rm(profilePath,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
