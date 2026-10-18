/**
 * CB-01 ONLY — real NVDA speech verification using the real CrownBotChat
 * React component, disposable synthetic user and mocked read-only API.
 *
 * This is NOT an axe/ARIA tree mock: PASS requires actual Guidepup NVDA
 * speech output captured after NVDA was started and driven on Windows.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
import { nvda } from '@guidepup/guidepup';

const head = process.env.CB01_SOURCE_HEAD;
if (process.platform !== 'win32'
    || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.CB01_NVDA_EXPERIMENT !== '1'
    || !/^[a-f0-9]{40}$/.test(head || '')) {
  throw new Error('REFUSED: experimental Windows-only isolated CB-01 NVDA test');
}
const origin = 'http://127.0.0.1:5173';
const target = origin + '/cb01-native-zoom-lab.html';
const out = path.resolve('../artifacts/cb01-windows-nvda');
await fs.mkdir(out, { recursive: true });
const report = {
  schema: 'CB01_WINDOWS_NVDA_REAL_SPEECH_V1',
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
const expectedControls = {
  brainTab: /^tab,\s*(?:selected,\s*)?Mémoire contextuelle(?:\s|$)/iu,
  chatTab: /^tab,\s*(?:selected,\s*)?Chat(?:\s|$)/iu,
  programmeButton: /^button,\s*Mon programme(?:\s|$)/iu,
  findPatientButton: /^button,\s*Trouver un patient(?:\s|$)/iu,
  rdvButton: /^button,\s*Préparer un RDV(?:\s|$)/iu,
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
  browser=await chromium.launch({channel:'chromium',headless:false,
    args:['--no-first-run','--disable-background-networking']});
  const context=await browser.newContext({viewport:{width:1280,height:900}});
  const page=await context.newPage();
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
  await page.screenshot({path:path.join(out,'cb01-windows-nvda-ui.png')});
  report.screenshots.push('cb01-windows-nvda-ui.png');
  await page.bringToFront();

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
  console.log('CB01_WINDOWS_REAL_NVDA: PASS',JSON.stringify({
    sourceHead:head,terms:report.observedTerms,roles:report.observedAccessibleControls,
    spoken:report.spokenPhrases.length,keyboardActions:report.keyboardActions.length,
    clinicalWrites:report.clinicalWritesAttempted.length,
  }));
} catch(err) {
  report.error=String(err?.stack||err);
  report.nvdaSpeechCaptured='NOT_CERTIFIED';
  console.error('CB01_WINDOWS_REAL_NVDA: NOT_CERTIFIED',report.error);
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
}
