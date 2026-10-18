/**
 * CB-01 Windows-native Chromium zoom LAB, deliberately separate from existing
 * REQUIRED & experimental jobs. Real CrownBotChat React component, synthetic API.
 * Browser zoom proof MUST come from Chrome extension tabs.setZoom/getZoom.
 * Browser emulation/font scaling is forbidden as a substitute.
 */
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

if (process.platform !== 'win32'
    || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.CB01_NATIVE_ZOOM_EXPERIMENT !== '1'
    || !/^[a-f0-9]{40}$/.test(process.env.CB01_SOURCE_HEAD || '')) {
  throw new Error('REFUSED: Windows isolated CB-01 native zoom experiment only');
}
const sourceHead = process.env.CB01_SOURCE_HEAD;
const origin = 'http://127.0.0.1:5173';
const out = path.resolve('../artifacts/cb01-windows-native-zoom');
await fs.mkdir(out, { recursive: true });
const extensionPath = await fs.mkdtemp(path.join(os.tmpdir(), 'cb01-zoom-ext-'));
const profilePath = await fs.mkdtemp(path.join(os.tmpdir(), 'cb01-zoom-profile-'));
const extensionManifest = {
  manifest_version: 3,
  name: 'CB01 Synthetic Zoom Verification',
  version: '1.0.0',
  permissions: ['tabs'],
  host_permissions: [origin + '/*'],
  background: { service_worker: 'service-worker.js' },
};
await fs.writeFile(path.join(extensionPath, 'manifest.json'),
  JSON.stringify(extensionManifest));
await fs.writeFile(path.join(extensionPath, 'service-worker.js'),
  "chrome.runtime.onInstalled.addListener(() => {});\nchrome.tabs.onUpdated.addListener(() => {});\n");

let vite = null;
let context = null;
const report = {
  schema: 'CB01_WINDOWS_CHROMIUM_NATIVE_ZOOM_V1',
  sourceHead,
  os: 'windows-latest',
  browser: null,
  nativeZoomKind: 'CHROME_EXTENSION_TABS_SETZOOM_GETZOOM',
  nativeZoom200Percent: 'NOT_RUN',
  screenReaderNVDA: 'NOT_RUN_NO_SPEECH_OR_HUMAN_VALIDATION',
  realClinicalBackend: 'NOT_USED_SYNTHETIC_API_INTERCEPT',
  realPatientData: false,
  clinicalMutations: 0,
  humanClinicalE2E: 0,
  screenshots: [],
  cases: [],
  error: null,
};
const assert = (condition, message) => {
  if (!condition) throw new Error('FAIL: ' + message);
};
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
async function serveFixture(route) {
  const req = route.request(), url = new URL(req.url()), method = req.method();
  const p = url.pathname;
  const cors = {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
  if (method === 'OPTIONS') {
    return route.fulfill({status:204,headers:cors});
  }
  if (method === 'GET' && p === '/api/bot/sessions') {
    return route.fulfill({ status: 200, contentType: 'application/json', body: '[]',
      headers: cors });
  }
  if (method === 'GET' && p === '/api/bot/workflows/cabinet-day') {
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({
        day:'2026-10-18', timezone:'Africa/Casablanca',
        start_date:'2026-10-18T00:00:00',
        end_date:'2026-10-18T23:59:59.999', consulted_at:'16:00',
      }), headers:cors });
  }
  if (method === 'GET' && p === '/api/appointments/') {
    return route.fulfill({ status: 200, contentType: 'application/json', body:'[]',
      headers:cors });
  }
  if (method === 'POST' && p === '/api/bot/workflows/preview') {
    const data = req.postDataJSON();
    assert(Array.isArray(data?.messages) && ['/rdv', '/patient'].includes(data.messages[0]),
      'unexpected synthetic preview API transcript');
    return route.fulfill({ status: 200, contentType:'application/json',
      body: JSON.stringify({
        status:'clarification', message:data.messages[0]==='/rdv'
          ? 'Patient : saisissez un nom ou dossier' : 'Patient : quel dossier souhaitez-vous consulter ?',
        proposal:null,
      }), headers:cors });
  }
  throw new Error('REFUSED: unmocked API call ' + method + ' ' + p);
}
async function waitForVite() {
  for (let i = 0; i < 45; i++) {
    if (vite.exitCode !== null) throw new Error('Vite exited early: '+vite.exitCode);
    try {
      const resp = await fetch(origin+'/cb01-native-zoom-lab.html',
        {signal:AbortSignal.timeout(900)});
      if (resp.ok) return;
    } catch {}
    await pause(1000);
  }
  throw new Error('Windows isolated Vite did not start');
}
async function nativeZoom(worker, factor) {
  const result = await worker.evaluate(async factor => {
    const tabs = await chrome.tabs.query({});
    const tab = tabs.find(t => t.url?.startsWith('http://127.0.0.1:5173/cb01-native-zoom-lab.html'));
    if (!tab?.id) throw new Error('Extension could not locate synthetic Crown Bot tab');
    await chrome.tabs.setZoom(tab.id, factor);
    return {tabId:tab.id, observed:await chrome.tabs.getZoom(tab.id)};
  },factor);
  assert(Math.abs(result.observed - factor) < 0.01,
    'Chrome getZoom differs from requested native '+factor);
  return result;
}
async function snapshot(page, zoom, width, filename) {
  const state = await page.evaluate(() => {
    const panel = document.querySelector('[data-cb01-native-lab-panel]');
    const tab = document.querySelector('[role="tab"][aria-selected="true"]');
    const ctas = [...document.querySelectorAll('[aria-label="Assistant Crown Bot — consultation"] button')]
      .filter(el=>['Mon programme','Trouver un patient','Préparer un RDV']
        .includes(el.textContent?.trim()||''));
    const rect = panel?.getBoundingClientRect();
    return {
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      devicePixelRatio: window.devicePixelRatio,
      visualViewportScale: window.visualViewport?.scale,
      rootClientWidth: document.documentElement.clientWidth,
      rootScrollWidth: document.documentElement.scrollWidth,
      panel: rect && { x:rect.x,y:rect.y,width:rect.width,height:rect.height,right:rect.right },
      tabRole:tab?.getAttribute('role'),
      tabName:tab?.textContent?.trim(),
      buttons:ctas.map(el=>el.textContent?.trim()),
    };
  });
  assert(state.buttons.length === 3, 'missing one-click first-value buttons at '+width+'/'+zoom);
  assert(state.rootScrollWidth <= state.rootClientWidth + 2,
    'horizontal page overflow at '+width+'/'+zoom);
  await page.screenshot({ path: path.join(out, filename), animations:'disabled' });
  report.screenshots.push(filename);
  return state;
}
try {
  // These two opt-ins affect ONLY the local isolated Vite child process.
  const env = {
    ...process.env,
    VITE_CB01_NATIVE_A11Y_LAB: 'true',
    VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED: 'true',
    VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED: 'true',
    VITE_TELEMETRY_ENABLED: 'false',
  };
  vite = spawn(process.execPath, [
    path.resolve('node_modules/vite/bin/vite.js'),
    '--host','127.0.0.1','--port','5173','--strictPort',
  ], {cwd:process.cwd(), env, stdio:['ignore','pipe','pipe'], windowsHide:true});
  vite.stdout.on('data', chunk => process.stdout.write('[vite] '+String(chunk)));
  vite.stderr.on('data', chunk => process.stderr.write('[vite] '+String(chunk)));
  await waitForVite();

  context = await chromium.launchPersistentContext(profilePath, {
    channel:'chromium', headless:true,
    viewport:{width:1600,height:900},
    args:[
      '--disable-extensions-except='+extensionPath,
      '--load-extension='+extensionPath,
      '--no-first-run', '--disable-background-networking',
    ],
  });
  report.browser = await context.browser()?.version() || 'chromium-persistent';
  const worker = context.serviceWorkers()[0]
    || await context.waitForEvent('serviceworker',{timeout:20000});
  assert(worker.url().startsWith('chrome-extension://'),
    'no actual Chrome zoom extension service worker');
  const page = await context.newPage();
  const pageErrors = [], clinicalWrites=[];
  page.on('pageerror',err=>pageErrors.push(String(err)));
  page.on('request',req=>{
    const u=new URL(req.url());
    if (req.method()!=='GET'
        && (/\/api\/(?:bot\/execute|appointments\/?|patients\/?|devis\/?)/.test(u.pathname))) {
      clinicalWrites.push(req.method()+' '+u.pathname);
    }
  });
  await page.route(/\/api\//,serveFixture);
  await page.goto(origin+'/cb01-native-zoom-lab.html',
    {waitUntil:'domcontentloaded',timeout:45000});
  const panel=page.locator('[data-cb01-native-lab-panel]');
  await panel.getByRole('tablist',{name:'Vues de Crown Bot'}).waitFor({state:'visible'});
  const chat=panel.getByRole('tab',{name:'Chat',exact:true});
  assert(await chat.getAttribute('aria-selected')==='true',
    'Chat not initially selected in real component');
  const browserBefore=await nativeZoom(worker,1);
  for (const width of [1280,1600]) {
    await page.setViewportSize({width,height:900});
    await nativeZoom(worker,1);
    const at100=await snapshot(page,1,width, 'cb01-win-native-'+width+'-100.png');
    const browserAt200=await nativeZoom(worker,2);
    const at200=await snapshot(page,2,width, 'cb01-win-native-'+width+'-200.png');
    assert(at200.innerWidth < at100.innerWidth,
      'actual Chromium CSS viewport did not shrink at native 200% zoom');
    assert(at200.innerWidth <= Math.ceil(at100.innerWidth*0.6),
      'CSS viewport shrink is not compatible with native zoom 2');
    await chat.focus();
    await page.keyboard.press('ArrowLeft');
    const brain=panel.getByRole('tab',{name:/Mémoire contextuelle/});
    assert(await brain.getAttribute('aria-selected')==='true',
      'keyboard ArrowLeft failed at native zoom 200');
    await page.keyboard.press('End');
    assert(await chat.getAttribute('aria-selected')==='true',
      'keyboard End failed at native zoom 200');
    await panel.getByRole('button',{name:'Préparer un RDV'}).click();
    await panel.getByText('Patient : saisissez un nom ou dossier').waitFor({state:'visible',timeout:12000});
    assert(clinicalWrites.length===0, 'clinical write during native zoom workflow');
    report.cases.push({
      width, zoom100:1, zoom200:browserAt200.observed,
      pixels100:at100, pixels200:at200, keyboardAria:'PASS',
      previewReadOnly:'PASS_SYNTHETIC_API',
      screenshots:['cb01-win-native-'+width+'-100.png','cb01-win-native-'+width+'-200.png'],
    });
    await nativeZoom(worker,1);
    await panel.getByRole('button',{name:'Réinitialiser la simulation'}).click();
  }
  assert(Math.abs(browserBefore.observed-1)<0.01,'initial zoom not 100%');
  assert(pageErrors.length===0,'uncaught page exceptions: '+JSON.stringify(pageErrors));
  assert(clinicalWrites.length===0,'attempted clinical writes: '+JSON.stringify(clinicalWrites));
  report.nativeZoom200Percent='PASS_BROWSER_EXTENSION_VERIFIED';
  report.clinicalMutations=clinicalWrites.length;
  console.log('CB01_NATIVE_WINDOWS_ZOOM_200: PASS', JSON.stringify({
    sourceHead, cases:report.cases.length, zoom:2,
    browser:report.browser, clinicalWrites:clinicalWrites.length,
    screenReader:report.screenReaderNVDA,
  }));
} catch(error) {
  report.error=String(error?.stack || error);
  report.nativeZoom200Percent='FAIL_OR_NOT_RUN';
  console.error('CB01_NATIVE_WINDOWS_ZOOM_200: NOT_CERTIFIED',report.error);
  process.exitCode=1;
} finally {
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  await context?.close().catch(()=>{});
  if (vite && vite.exitCode===null) vite.kill();
  await fs.rm(extensionPath,{recursive:true,force:true}).catch(()=>{});
  await fs.rm(profilePath,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
