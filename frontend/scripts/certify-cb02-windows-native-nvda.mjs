/** CB-02 NEW panel: hosted Windows REAL Chromium native 200% and NVDA speech.
 * Separate from a full FastAPI user session: this exercises the real React
 * component against an explicitly synthetic browser stub only. No clinic data.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
import { nvda } from '@guidepup/guidepup';

const sourceHead = process.env.CB02_SOURCE_HEAD;
if (process.platform !== 'win32'
    || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.CB02_NATIVE_ZOOM_EXPERIMENT !== '1'
    || !/^[a-f0-9]{40}$/.test(sourceHead || '')) {
  throw Error('REFUSED: Windows-only isolated CB-02 native-zoom experiment');
}
const origin = 'http://127.0.0.1:5173';
const target = origin + '/cb02-native-zoom-lab.html';
const out = path.resolve('../artifacts/cb02-guided-native-windows');
await fs.mkdir(out, { recursive: true });
const ext = await fs.mkdtemp(path.join(os.tmpdir(), 'cb02-native-extension-'));
const profile = await fs.mkdtemp(path.join(os.tmpdir(), 'cb02-native-profile-'));
await fs.writeFile(path.join(ext, 'manifest.json'), JSON.stringify({
  manifest_version: 3, name: 'CB02 Native Zoom Synthetic Lab', version: '1.0.0',
  permissions: ['tabs'], host_permissions: [origin + '/*'],
  background: { service_worker: 'worker.js' },
}));
await fs.writeFile(path.join(ext, 'worker.js'), 'chrome.runtime.onInstalled.addListener(() => {});\n');
const report = {
  sourceHead, kind: 'NEW_CB02_REACT_SYNTHETIC_BROWSER_STUB',
  isolated: true, nativeZoomFactor: null, nativeZoomAtSpeech: 'NOT_RUN',
  nvdaSpeechCaptured: 'NOT_RUN', spoken: [], controlNamesAnnounced: {},
  uiResponse: 'NOT_RUN', writes: [], screenshots: [], status: 'NOT_CERTIFIED',
  browser: null, error: null,
};
let server, browser, startedNvda = false;
const sleep = ms => new Promise(done => setTimeout(done, ms));
async function waitForVite() {
  for (let i = 0; i < 50; i++) {
    if (server?.exitCode !== null) throw Error('Vite exited');
    try {
      const resp = await fetch(target, { signal: AbortSignal.timeout(1500) });
      if (resp.ok) return;
    } catch {}
    await sleep(1000);
  }
  throw Error('REFUSED: no loopback-only Vite lab');
}
async function readZoom(worker, set) {
  const result = await worker.evaluate(async ({target, set}) => {
    const tabs = await chrome.tabs.query({});
    const list = tabs.filter(tab => tab.id && tab.url?.startsWith(target));
    if (list.length !== 1) throw Error('Expected one synthetic test tab');
    if (set !== null) await chrome.tabs.setZoom(list[0].id, set);
    return { id: list[0].id, value: await chrome.tabs.getZoom(list[0].id) };
  }, {target, set});
  if (set !== null && Math.abs(result.value-set)>0.01)
    throw Error('NOT_CERTIFIED: extension native setZoom/getZoom disagreed');
  return result;
}
async function dimensions(page) {
  return page.evaluate(() => ({
    inner: window.innerWidth, dpr: window.devicePixelRatio,
    documentScroll: document.documentElement.scrollWidth,
    documentClient: document.documentElement.clientWidth,
    panelScroll: document.querySelector('[data-cb02-native-lab-panel]')?.scrollWidth,
    panelClient: document.querySelector('[data-cb02-native-lab-panel]')?.clientWidth,
  }));
}
try {
  server = spawn(process.execPath, [
    path.resolve('node_modules/vite/bin/vite.js'),
    '--host', '127.0.0.1', '--port', '5173', '--strictPort',
  ], {
    cwd: process.cwd(),
    env: { ...process.env, VITE_CB02_NATIVE_A11Y_LAB: 'true',
      VITE_CROWN_BOT_GUIDED_NLU_ENABLED: 'true',
      VITE_TELEMETRY_ENABLED: 'false' },
    windowsHide: true, stdio: ['ignore','pipe','pipe'],
  });
  server.stdout.on('data', data => process.stdout.write('[Vite] ' + String(data)));
  server.stderr.on('data', data => process.stderr.write('[Vite] ' + String(data)));
  await waitForVite();
  browser = await chromium.launchPersistentContext(profile, {
    channel: 'chromium', headless: false, viewport: { width: 1280, height: 900 },
    args: ['--disable-extensions-except=' + ext, '--load-extension=' + ext,
      '--no-first-run', '--disable-background-networking'],
  });
  report.browser = browser.browser()?.version() || 'Chromium-persistent';
  const worker = browser.serviceWorkers()[0]
    || await browser.waitForEvent('serviceworker', {timeout: 20000});
  if (!worker.url().startsWith('chrome-extension://'))
    throw Error('NOT_CERTIFIED: no real Chrome extension');
  const page = browser.pages()[0] || await browser.newPage();
  page.on('request', req => {
    const u = new URL(req.url());
    if (req.method() !== 'GET' &&
        /^\/api\/(?:bot\/execute|appointments|patients|devis)\b/.test(u.pathname))
      report.writes.push(req.method() + ':' + u.pathname);
  });
  page.on('pageerror', err => { report.error = 'Browser error: ' + String(err); });
  // Only a pure read-only fake response, explicitly NOT a real API proof.
  await page.route(/\/api\//, async route => {
    const req = route.request(), url = new URL(req.url());
    if (url.pathname === '/api/bot/guided/preview' && req.method() === 'OPTIONS') {
      await route.fulfill({status:204, headers:{'Access-Control-Allow-Origin':origin,
        'Access-Control-Allow-Credentials':'true',
        'Access-Control-Allow-Headers':'Content-Type,Authorization',
        'Access-Control-Allow-Methods':'POST,OPTIONS'}});
      return;
    }
    if (url.pathname !== '/api/bot/guided/preview' || req.method() !== 'POST')
      throw Error('REFUSED unexpected API in standalone CB-02 OS lab ' + url.pathname);
    const data = req.postDataJSON();
    if (data?.utterance !== 'Mon agenda demain' || Object.keys(data).length !== 1)
      throw Error('REFUSED unexpected CB-02 input');
    await route.fulfill({ status: 200, contentType: 'application/json',
      headers: { 'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Credentials': 'true' },
      body: JSON.stringify({
        status: 'requires_server_authorization', intent: 'AGENDA_READ',
        fields: {date: {value:'2026-10-23', source:'deterministic_relative_or_explicit',
          rule:'CABINET_LOCAL_DAY'}},
        message: 'Syntaxe comprise ; contrôles serveur obligatoires.',
        proposal: null, executable: false,
      }) });
  });
  // This explicit loopback-only Vite lab disables DEV PWA registration at
  // config level. Never force a reload into Workbox's offline index fallback,
  // which can silently replace this lab's React entry with the normal App.
  // Fail if a service worker unexpectedly takes control or the document
  // later reloads while real NVDA speech is being certified.
  let documentLoads=0;
  page.on('load',()=>{documentLoads++;});
  await page.goto(target, { waitUntil:'domcontentloaded', timeout:45000 });
  const panel = page.getByRole('region', {name:'Français guidé Crown Bot CB-02'});
  await panel.waitFor({state:'visible'});
  const input = panel.getByRole('textbox', {name:'Votre demande en français'});
  const submit = panel.getByRole('button', {name:'Comprendre la demande'});
  await input.waitFor(); await submit.waitFor();
  // Count the fully loaded initial lab document, not a late 'load' event.
  await page.waitForLoadState('load',{timeout:20000});
  const sw = await page.evaluate(async () => ({
    controlled: !!navigator.serviceWorker?.controller,
    registrations: navigator.serviceWorker ? (await navigator.serviceWorker.getRegistrations()).length : 0,
  }));
  report.devPwaLab={...sw, disabledByEnvironment:true};
  if(sw.controlled || sw.registrations)
    throw Error('NOT_CERTIFIED: isolated CB-02 lab unexpectedly controlled by a PWA service worker');
  const warmDocumentLoads=documentLoads;
  await page.bringToFront();
  const zoom100 = await readZoom(worker, 1);
  const before = await dimensions(page);
  await page.screenshot({path:path.join(out,'cb02-new-ui-native-100-before.png')});
  report.screenshots.push('cb02-new-ui-native-100-before.png');
  const zoom200 = await readZoom(worker, 2);
  const after = await dimensions(page);
  if (zoom200.id !== zoom100.id || Math.abs(zoom200.value-2)>0.01
      || after.inner >= before.inner
      || after.dpr <= before.dpr
      || after.documentScroll > after.documentClient + 2
      || after.panelScroll > after.panelClient + 2) {
    throw Error('NOT_CERTIFIED: native 200% layout/zoom drift or horizontal overflow '
      + JSON.stringify({ before, after, zoom200 }));
  }
  // Force a genuine React onChange in the warmed-up document; the browser
  // may preserve the textarea DOM value through an HMR reload while React
  // state silently resets to empty (leaving submit disabled).
  await input.fill('');
  await input.fill('Mon agenda demain');
  if (!(await submit.isEnabled()))
    throw Error('NOT_CERTIFIED: React draft button disabled before NVDA');
  report.reactSubmitEnabledBeforeNvda=true;
  // Prove keyboard Tab / Shift+Tab in real headed Chromium *before* NVDA
  // starts intercepting global keyboard navigation. This still fails closed
  // if the real form order is wrong at native zoom 200%.
  await input.focus();
  await page.keyboard.press('Tab');
  if (!(await submit.evaluate(el=>document.activeElement===el)))
    throw Error('NOT_CERTIFIED: browser Tab cannot reach CB-02 submit at native 200%');
  await page.keyboard.press('Shift+Tab');
  if (!(await input.evaluate(el=>document.activeElement===el)))
    throw Error('NOT_CERTIFIED: browser Shift+Tab cannot return to CB-02 edit at native 200%');
  report.realBrowserTabOrderAt200='PASS_REAL_TAB_AND_SHIFT_TAB';
  await page.screenshot({path:path.join(out,'cb02-new-ui-native-200-before.png')});
  report.screenshots.push('cb02-new-ui-native-200-before.png');
  // Guidepup defaults to initial-page speech capture; this lab needs ALL
  // subsequent real NVDA announcements after keyboard/virtual navigation.
  // capture:true preserves the strict speech-only role+label oracle.
  await nvda.start({capture: true});
  startedNvda=true;
  await sleep(800);
  await page.bringToFront();
  // NVDA virtual navigation can begin *after* a focused multiline edit.
  // The previous oracle walked forward from the textarea straight to the
  // submit button and kept repeating that final control. Explicitly visit
  // BOTH controls via REAL keyboard focus, and independently use NVDA's
  // reverse/forward virtual cursor. Nothing is inferred from the DOM as speech.
  await nvda.clearSpokenPhraseLog();
  const proof = [];
  const seen = {
    requestInput: false,
    understandButton: false,
  };
  const collect = async stage => {
    const raw = await nvda.spokenPhraseLog();
    const phrases = Array.isArray(raw) ? raw.map(String) : [String(raw)];
    report.spoken = phrases.slice(-250);
    // The role and label must occur in the same genuinely spoken phrase:
    // prose, ARIA labels retrieved by Playwright, or screen pixels cannot PASS.
    const editPhrase = phrase => /votre demande en fran[cç]ais/i.test(phrase)
      && /edit|edition|édition|textbox|multiline|multi-line/i.test(phrase);
    const buttonPhrase = phrase => /comprendre la demande/i.test(phrase)
      && /button|bouton/i.test(phrase);
    seen.requestInput ||= phrases.some(editPhrase);
    seen.understandButton ||= phrases.some(buttonPhrase);
    report.controlNamesAnnounced = {...seen};
    proof.push({stage, phraseCount:phrases.length, controls:{...seen},
      last:phrases.slice(-6)});
    console.log('CB02_REAL_NVDA_OBSERVATION',JSON.stringify(proof.at(-1)));
    return Object.values(seen).every(Boolean);
  };
  // Guidepup/NVDA keyboard commands operate on the OS virtual cursor.
  // A focused textarea can hold NVDA in focus mode: `next()` then just
  // reiterates the last element or emits empty speech. Return to BROWSE,
  // start at document top, and explicitly visit actual form fields.
  // The independent real-browser Tab order was already certified at 200%.
  // THIS phase accepts only role+name from real NVDA spokenPhraseLog.
  await page.bringToFront();
  await input.focus();
  const navigationErrors=[];
  const doNavigation = async (stage, callback) => {
    try {
      await callback();
      await sleep(350);
      await collect(stage);
    } catch (error) {
      navigationErrors.push({stage, error:String(error)});
      console.log('CB02_NVDA_NAVIGATION_DIAGNOSTIC', JSON.stringify(navigationErrors.at(-1)));
    }
    return Object.values(seen).every(Boolean);
  };
  // Guidepup documented NVDA keys: Escape leaves automatic focus mode;
  // Control+Home starts from top of browse document. Neither inserts text.
  await doNavigation('nvda-exit-focus-mode',
    ()=>nvda.perform(nvda.keyboardCommands.exitFocusMode));
  await doNavigation('nvda-browse-document-home',
    ()=>nvda.press('Control+Home'));
  for(let i=0;i<5;i++){
    if(await doNavigation('nvda-next-form-field-'+(i+1),
      ()=>nvda.perform(nvda.keyboardCommands.moveToNextFormField))) break;
  }
  if(!Object.values(seen).every(Boolean)){
    await doNavigation('nvda-refresh-browse-document',
      ()=>nvda.perform(nvda.keyboardCommands.refreshBrowseDocument));
    await doNavigation('nvda-home-after-refresh',()=>nvda.press('Control+Home'));
    for(let i=0;i<5;i++){
      if(await doNavigation('nvda-next-form-after-refresh-'+(i+1),
        ()=>nvda.perform(nvda.keyboardCommands.moveToNextFormField))) break;
    }
  }
  if(!Object.values(seen).every(Boolean)){
    await doNavigation('nvda-go-back-to-top',()=>nvda.press('Control+Home'));
    for(let i=0;i<14;i++){
      if(await doNavigation('nvda-forward-browse-'+(i+1),()=>nvda.next()))break;
    }
  }
  report.speechNavigationProof=proof.slice(-65);
  report.nvdaNavigationErrors=navigationErrors;
  report.nvdaItemTextDiagnostics=(await nvda.itemTextLog()).slice(-35);
  // ItemText diagnostics NEVER satisfy speech checks, including if labels
  // show in the accessibility tree but NVDA has spoken nothing.
  const zoomAtSpeech = await readZoom(worker, null);
  if (zoomAtSpeech.id !== zoom200.id || Math.abs(zoomAtSpeech.value-2)>0.01)
    throw Error('NOT_CERTIFIED: native zoom not 200% when real NVDA spoke');
  if (!Object.values(report.controlNamesAnnounced).every(Boolean))
    throw Error('NOT_CERTIFIED: real NVDA did not announce BOTH new CB-02 form controls');
  report.nativeZoomFactor=zoomAtSpeech.value;
  report.nativeZoomAtSpeech='PASS_EXTENSION_GETZOOM_2_REAL_NVDA';
  report.nvdaSpeechCaptured='PASS_REAL_NVDA_2_CONTROLS';
  // Speech alone is insufficient: prove the same warmed-up React form
  // remained live through NVDA and retained valid user-entered state.
  const currentText=await input.inputValue();
  const isEnabled=await submit.isEnabled();
  report.reactDraftAtNvdaEnd={currentText,buttonEnabled:isEnabled,
    documentLoads,warmDocumentLoads};
  if(documentLoads!==warmDocumentLoads)
    throw Error('NOT_CERTIFIED: unexpected Vite/HMR page reload during NVDA test');
  if(currentText!=='Mon agenda demain'||!isEnabled)
    throw Error('NOT_CERTIFIED: React form state lost or submit unavailable during NVDA');
  await submit.click({timeout:10000});
  await panel.getByText('Syntaxe comprise ; contrôles serveur obligatoires.').waitFor({
    state:'visible', timeout:15000 });
  report.uiResponse='PASS_SYNTHETIC_NON_EXECUTABLE';
  await page.screenshot({path:path.join(out,'cb02-new-ui-native-200-after.png')});
  report.screenshots.push('cb02-new-ui-native-200-after.png');
  if (report.writes.length || report.error)
    throw Error('NOT_CERTIFIED: UI script error or clinical write: '
      + JSON.stringify({writes:report.writes,error:report.error}));
  report.status='PASS_SYNTHETIC_NATIVE_NVDA_NEW_CB02';
  console.log('CB02_WINDOWS_NATIVE_NVDA_NEW_PANEL: PASS',
    JSON.stringify({head:sourceHead,spoken:report.spoken.length,
      controls:report.controlNamesAnnounced,zoom:report.nativeZoomFactor,
      writes:report.writes.length}));
} catch (error) {
  report.error = String(error?.stack || error);
  report.status='NOT_CERTIFIED';
  console.error('CB02_WINDOWS_NATIVE_NVDA_NEW_PANEL: NOT_CERTIFIED', report.error);
  process.exitCode=1;
} finally {
  try { if (startedNvda) await nvda.stop(); }
  catch (err) {report.cleanupError=String(err);process.exitCode=1;}
  try { await browser?.close(); } catch {}
  if (server?.exitCode===null) server.kill();
  await fs.writeFile(path.join(out,'report.json'), JSON.stringify(report,null,2));
  await fs.rm(ext,{recursive:true,force:true}).catch(()=>{});
  await fs.rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
