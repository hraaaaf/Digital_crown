/**
 * CB-01 ONLY — real NVDA speech verification using the real CrownBotChat
 * React component, disposable synthetic user and mocked read-only API.
 *
 * This is NOT an axe/ARIA tree mock: PASS requires actual Guidepup NVDA
 * speech output captured after NVDA was started and driven on Windows.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
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
const target = origin + '/cb01-native-zoom-lab.html';
const out = path.resolve('../artifacts/cb01-windows-nvda-zoom-combined');
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
  schema: 'CB01_WINDOWS_NVDA_NATIVE_ZOOM_COMBINED_V1',
  evidenceType: 'REAL_NVDA_AND_EXTENSION_GETZOOM_IN_SAME_CHROMIUM_TAB',
  sourceScope: 'ISOLATED_REACT_SYNTHETIC_API_NO_CLINICAL_BACKEND',
  zoomKind: 'CHROME_EXTENSION_TABS_SETZOOM_GETZOOM',
  nativeZoomAtSpeech: 'NOT_RUN',
  zoomBefore: null,
  zoomAtSpeech: null,
  zoomMeasurements: null,
  browserVersion: null,
  simultaneousPass: false,
  sourceHead: head,
  scope: 'REAL_CROWNBOTCHAT_REACT_SYNTHETIC_LOOPBACK',
  nvdaStarted: false,
  nvdaSpeechCaptured: 'NOT_RUN',
  spokenPhrases: [],
  lastSpokenPhrase: null,
  observedTerms: [],
  observedAccessibleControls: {},
  keyboardActions: [],
  screenshots: [],
  clinicalWritesAttempted: [],
  actualClinicalBackend: 'NOT_USED',
  speechHardwareAudioRecording: 'NOT_RUN',
  nvdaHumanReview: 'NOT_RUN',
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
function replyApi(route) {
  const req=route.request();
  const url=new URL(req.url());
  const method=req.method(), pathname=url.pathname;
  const cors={
    'Access-Control-Allow-Origin':origin,
    'Access-Control-Allow-Credentials':'true',
    'Access-Control-Allow-Headers':'Content-Type,Authorization',
    'Access-Control-Allow-Methods':'GET,POST,OPTIONS',
  };
  if(method==='OPTIONS')return route.fulfill({status:204,headers:cors});
  if(method==='GET'&&pathname==='/api/bot/sessions')
    return route.fulfill({status:200,contentType:'application/json',body:'[]',headers:cors});
  if(method==='GET'&&pathname==='/api/bot/workflows/cabinet-day')
    return route.fulfill({status:200,contentType:'application/json',
      body:JSON.stringify({day:'2026-10-18',timezone:'Africa/Casablanca',
        start_date:'2026-10-18T00:00:00',end_date:'2026-10-18T23:59:59.999',consulted_at:'17:00'}),
      headers:cors});
  if(method==='GET'&&pathname==='/api/appointments/')
    return route.fulfill({status:200,contentType:'application/json',body:'[]',headers:cors});
  if(method==='POST'&&pathname==='/api/bot/workflows/preview') {
    const body=req.postDataJSON();
    if(!Array.isArray(body?.messages)
       || !['/patient','/rdv'].includes(body.messages[0]))
      throw new Error('Unexpected preview transcript in isolated NVDA lab');
    return route.fulfill({status:200,contentType:'application/json',
      body:JSON.stringify({status:'clarification',proposal:null,
        message:'Identifiant numérique du patient ?'}),headers:cors});
  }
  throw new Error('REFUSED unexpected synthetic API request '+method+' '+pathname);
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
    const tab = tabs.find(t => t.url?.startsWith('http://127.0.0.1:5173/cb01-native-zoom-lab.html'));
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
    const matches=tabs.filter(tab => tab.url?.startsWith('http://127.0.0.1:5173/cb01-native-zoom-lab.html'));
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
      VITE_CB01_NATIVE_A11Y_LAB:'true',
      VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED:'true',
      VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED:'true',
      VITE_TELEMETRY_ENABLED:'false',
    },
    stdio:['ignore','pipe','pipe'],windowsHide:true,
  });
  server.stdout.on('data',x=>process.stdout.write('[vite] '+String(x)));
  server.stderr.on('data',x=>process.stderr.write('[vite] '+String(x)));
  await waitForLocal();

  // NVDA reads the real operating system accessibility stack, which needs a
  // headed browser/window. Headless or Playwright's accessibility tree is NOT proof.
  browser=await chromium.launchPersistentContext(profilePath,{
    channel:'chromium', headless:false, viewport:{width:1280,height:900},
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
  page.on('request',req=>{
    const p=new URL(req.url()).pathname;
    if(req.method()!=='GET'
      && /\/api\/(?:bot\/execute|appointments\/?|patients\/?|devis\/?)/.test(p))
      report.clinicalWritesAttempted.push(req.method()+' '+p);
  });
  await page.route(/\/api\//,replyApi);
  await page.goto(target,{waitUntil:'domcontentloaded',timeout:45000});
  const panel=page.locator('[data-cb01-native-lab-panel]');
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
  console.log('CB01_WINDOWS_NVDA_NATIVE_ZOOM_COMBINED: PASS',JSON.stringify({
    sourceHead:head,terms:report.observedTerms,roles:report.observedAccessibleControls,
    spoken:report.spokenPhrases.length,keyboardActions:report.keyboardActions.length,
    nativeZoomAtSpeech:report.zoomAtSpeech.observed,
    clinicalWrites:report.clinicalWritesAttempted.length,
  }));
} catch(err) {
  report.error=String(err?.stack||err);
  report.nvdaSpeechCaptured='NOT_CERTIFIED';
  console.error('CB01_WINDOWS_NVDA_NATIVE_ZOOM_COMBINED: NOT_CERTIFIED',report.error);
  process.exitCode=1;
} finally {
  try {if(nvdaActive)await nvda.stop();}catch(e){
    console.error('CB01_NVDA_CLEANUP_FAILURE',String(e));
    report.nvdaCleanupError=String(e);
    process.exitCode=1;
  }
  try {await browser?.close();}catch {}
  if(server?.exitCode===null)server.kill();
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  await fs.rm(extensionPath,{recursive:true,force:true}).catch(()=>{});
  await fs.rm(profilePath,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
