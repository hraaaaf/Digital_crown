/**
 * CB-03 G4 Windows hosted native Chrome zoom + real NVDA speech.
 *
 * Standalone G3 React lab with synthetic INTERCEPTED responses. The only
 * certification scope here is native zoom/keyboard/NVDA accessibility of the
 * real G3 component; it is NOT a human Windows clinic rehearsal.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
import { nvda } from '@guidepup/guidepup';

const HEAD = process.env.CB03_G4_SOURCE_HEAD || '';
const origin = 'http://127.0.0.1:5173';
const url = origin + '/cb03-g3-visual-lab.html';
if (process.platform !== 'win32' || process.env.GITHUB_ACTIONS !== 'true' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    process.env.CB03_G4_WINDOWS_NVDA_EXPERIMENT !== '1' ||
    !/^[0-9a-f]{40}$/.test(HEAD)) {
  throw Error('REFUSED: exact-head isolated Windows NVDA G4 CI only');
}
const out = path.resolve('../artifacts/cb03-g4/windows-nvda-native');
await fs.mkdir(out, { recursive:true });
const extension = await fs.mkdtemp(path.join(os.tmpdir(), 'cb03-g4-ext-'));
const profile = await fs.mkdtemp(path.join(os.tmpdir(), 'cb03-g4-profile-'));
await fs.writeFile(path.join(extension, 'manifest.json'), JSON.stringify({
  manifest_version:3, name:'CB03 G4 Native Zoom Guard', version:'1.0.0',
  permissions:['tabs'], host_permissions:[origin+'/*'],
  background:{service_worker:'worker.js'},
}));
await fs.writeFile(path.join(extension,'worker.js'),
  'chrome.runtime.onInstalled.addListener(() => {});\n');

const report = {
  schema:'CB03_G4_WINDOWS_REAL_NVDA_NATIVE_ZOOM_V1',
  sourceHead:HEAD, realNvdaSpeech:false, nativeZoomAtSpeech:null,
  nativeZoomMethod:'extension_chrome_tabs_setZoom_getZoom',
  sourceScope:'ISOLATED_REAL_REACT_G3_MOCKED_BACKEND',
  screenshots:[], spokenPhrases:[], controls:{}, keyboard:{},
  allFlagsOffExceptDisposableLab:true, status:'NOT_CERTIFIED', error:null,
};
let server, browser, nvdaStarted=false;
const sleep = ms => new Promise(r=>setTimeout(r,ms));
async function untilServer() {
  for(let i=0;i<55;i++){
    try {
      if(server?.exitCode!==null) throw Error('Vite terminated');
      const r=await fetch(url,{signal:AbortSignal.timeout(1000)});
      if(r.ok)return;
    }catch {}
    await sleep(800);
  }
  throw Error('REFUSED: no loopback G3 lab');
}
async function zoom(worker, value) {
  const z=await worker.evaluate(async ({url, value})=>{
    const tabs=await chrome.tabs.query({});
    const candidates=tabs.filter(t=>t.id&&t.url?.startsWith(url));
    if(candidates.length!==1)throw Error('NOT_CERTIFIED: expected unique lab tab');
    const id=candidates[0].id;
    if(value!==null)await chrome.tabs.setZoom(id,value);
    return {id,value:await chrome.tabs.getZoom(id)};
  },{url,value});
  if(value!==null && Math.abs(z.value-value)>0.01)
    throw Error('NOT_CERTIFIED: native getZoom does not match requested factor');
  return z;
}
const descriptors = {
  create: /pr[eé]parer un nouveau rdv/i,
  status: /changer le statut d.un rdv/i,
  input: /votre demande en fran[cç]ais/i,
  prepare: /v[eé]rifier et pr[eé]parer/i,
};
const roleMatches = {
  create: s => descriptors.create.test(s) && /button|bouton/i.test(s),
  status: s => descriptors.status.test(s) && /button|bouton/i.test(s),
  input: s => descriptors.input.test(s) && /edit|edition|[eé]dition|textbox|multiline/i.test(s),
  prepare: s => descriptors.prepare.test(s) && /button|bouton/i.test(s),
};
const found=Object.fromEntries(Object.keys(roleMatches).map(k=>[k,false]));
async function collect(stage) {
  const raw=await nvda.spokenPhraseLog();
  const phrases=(Array.isArray(raw)?raw:[raw]).map(String);
  report.spokenPhrases=phrases.slice(-250);
  for(const [key,fn] of Object.entries(roleMatches))
    found[key] ||= phrases.some(fn);
  report.controls={...found};
  console.log('CB03_G4_NVDA_SPEECH_STAGE',JSON.stringify({
    stage,count:phrases.length,controls:found,last:phrases.slice(-4),
  }));
  return Object.values(found).every(Boolean);
}
try {
  server=spawn(process.execPath,[
    path.resolve('node_modules/vite/bin/vite.js'),
    '--host','127.0.0.1','--port','5173','--strictPort',
  ],{
    cwd:process.cwd(),windowsHide:true,
    env:{...process.env,VITE_CB03_G3_VISUAL_LAB:'true',
      VITE_CROWN_BOT_CB03_G3_ENABLED:'true'},
    stdio:['ignore','pipe','pipe'],
  });
  server.stdout.on('data',d=>process.stdout.write('[G3-Vite] '+String(d)));
  server.stderr.on('data',d=>process.stderr.write('[G3-Vite] '+String(d)));
  await untilServer();
  browser=await chromium.launchPersistentContext(profile,{
    headless:false, channel:'chromium', viewport:{width:1280,height:900},
    args:['--disable-extensions-except='+extension,'--load-extension='+extension,
      '--no-first-run','--disable-background-networking'],
  });
  const worker=browser.serviceWorkers()[0] ||
    await browser.waitForEvent('serviceworker',{timeout:20000});
  if(!worker.url().startsWith('chrome-extension://'))
    throw Error('NOT_CERTIFIED: no Chrome extension to read native zoom');
  const page=browser.pages()[0]||await browser.newPage();
  const requests=[];
  page.on('request',req=>{if(req.method()==='POST'&&/\/api\//.test(req.url()))
    requests.push(req.method()+' '+new URL(req.url()).pathname);});
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.route('**/api/bot/guided/**',async route=>{
    const req=route.request();
    const headers={'access-control-allow-origin':origin,
      'access-control-allow-credentials':'true',
      'access-control-allow-headers':'authorization,content-type',
      'access-control-allow-methods':'GET,POST,OPTIONS'};
    if(req.method()==='OPTIONS'){
      await route.fulfill({status:204,headers});return;
    }
    if(req.method()!=='POST'||!req.url().endsWith('/prepare-appointment'))
      throw Error('REFUSED: unexpected or executable request in NVDA lab');
    if(req.postDataJSON().utterance!=='Prépare un RDV demain 10h pour Mme Benali contrôle')
      throw Error('REFUSED: wrong G3 synthetic text');
    await route.fulfill({status:200,headers,contentType:'application/json',
      body:JSON.stringify({status:'prepared',executable:false,
        preparation_id:'d4a97731-cdcb-4b9c-94d3-f1d21c242a21',
        expires_at:'2026-11-01T12:30:00',
        summary:{patient:{id:21,nom:'Benali',prenom:'Salma',numero_dossier:'S-21'},
          praticien_id:9,resource_id:null,datetime_start:'2026-11-07T10:00:00',
          duration_minutes:30,motif:'CONTROLE'}})});
  });
  await page.goto(url,{waitUntil:'load',timeout:45000});
  const panel=page.getByRole('region',{name:'CB-03 G3 — actions guidées'});
  await panel.waitFor();
  const controls={
    create:page.getByRole('button',{name:'Préparer un nouveau RDV'}),
    status:page.getByRole('button',{name:'Changer le statut d’un RDV'}),
    input:page.getByRole('textbox',{name:'Votre demande en français'}),
    prepare:page.getByRole('button',{name:/Vérifier et préparer/}),
  };
  for(const [key,loc] of Object.entries(controls))
    if(!(await loc.isVisible()))throw Error('NOT_CERTIFIED: missing visible control '+key);
  const sw=await page.evaluate(async()=>({
    controller:!!navigator.serviceWorker?.controller,
    count:navigator.serviceWorker?(await navigator.serviceWorker.getRegistrations()).length:0,
  }));
  if(sw.controller||sw.count)throw Error('NOT_CERTIFIED: PWA controls G4 lab');
  await page.bringToFront();
  const before=await zoom(worker,1);
  await page.screenshot({path:path.join(out,'g3-native-100-before.png')});
  report.screenshots.push('g3-native-100-before.png');
  const after=await zoom(worker,2);
  if(before.id!==after.id || Math.abs(after.value-2)>0.01)
    throw Error('NOT_CERTIFIED: native zoom tab changed');
  const overflow=await page.evaluate(()=>
    document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
  if(overflow)throw Error('NOT_CERTIFIED: horizontal overflow under native zoom 200');
  await page.screenshot({path:path.join(out,'g3-native-200-before.png')});
  report.screenshots.push('g3-native-200-before.png');
  await controls.input.fill('Prépare un RDV demain 10h pour Mme Benali contrôle');
  await controls.input.focus();
  await page.keyboard.press('Tab');
  if(!await controls.prepare.evaluate(el=>document.activeElement===el))
    throw Error('NOT_CERTIFIED: keyboard focus cannot reach prepare at native 200%');
  await page.keyboard.press('Shift+Tab');
  if(!await controls.input.evaluate(el=>document.activeElement===el))
    throw Error('NOT_CERTIFIED: Shift+Tab cannot return to input at native 200%');
  report.keyboard={tabToSubmit:true,shiftTabReturn:true};
  await nvda.start({capture:true});
  nvdaStarted=true;
  await sleep(700);
  await page.bringToFront();
  await nvda.clearSpokenPhraseLog();
  try {await nvda.perform(nvda.keyboardCommands.exitFocusMode);}catch {}
  await nvda.press('Control+Home');
  await sleep(300);
  await collect('home');
  for(let i=0;i<26 && !Object.values(found).every(Boolean);i++){
    try {await nvda.next();}
    catch {break;}
    await sleep(180);
    await collect('virtual-'+i);
  }
  if(!Object.values(found).every(Boolean)){
    await nvda.press('Control+Home');
    for(let i=0;i<12 && !Object.values(found).every(Boolean);i++){
      try {await nvda.perform(nvda.keyboardCommands.moveToNextFormField);}
      catch {break;}
      await sleep(250);
      await collect('form-'+i);
    }
  }
  report.nativeZoomAtSpeech=(await zoom(worker,null)).value;
  if(Math.abs(report.nativeZoomAtSpeech-2)>0.01)
    throw Error('NOT_CERTIFIED: native zoom not 200 at NVDA speech');
  if(!Object.values(found).every(Boolean))
    throw Error('NOT_CERTIFIED: not all 4 G3 controls spoken with real NVDA role+name');
  report.realNvdaSpeech=true;
  await nvda.stop();nvdaStarted=false;
  await page.bringToFront();
  if(await controls.input.inputValue()!=='Prépare un RDV demain 10h pour Mme Benali contrôle')
    throw Error('NOT_CERTIFIED: React input lost after NVDA');
  await controls.prepare.click();
  await page.getByText('Salma Benali · Dossier S-21').waitFor();
  const confirm=page.getByRole('button',{name:'Confirmer explicitement cette action'});
  if(await confirm.isEnabled())throw Error('NOT_CERTIFIED: confirmation enabled without checkbox');
  if(requests.length!==1||!requests[0].endsWith('/prepare-appointment'))
    throw Error('NOT_CERTIFIED: unexpected request from standalone lab');
  await page.screenshot({path:path.join(out,'g3-native-200-prepared.png')});
  report.screenshots.push('g3-native-200-prepared.png');
  report.status='PASS_HOSTED_REAL_NVDA_NATIVE_ZOOM_SYNTHETIC_G3';
  console.log('CB03_G4_WINDOWS_REAL_NVDA_ZOOM_PASS',JSON.stringify({
    sourceHead:HEAD,zoom:report.nativeZoomAtSpeech,roles:report.controls,
    httpPosts:requests,
  }));
  if(errors.length)throw Error('NOT_CERTIFIED: browser runtime error '+errors.join(';'));
}catch(error){
  report.status='NOT_CERTIFIED';
  report.error=String(error?.stack||error);
  process.exitCode=1;
  console.error('CB03_G4_WINDOWS_REAL_NVDA_ZOOM_NOT_CERTIFIED',report.error);
}finally{
  try {if(nvdaStarted) await nvda.stop();}catch {}
  try {await browser?.close();}catch {}
  if(server?.exitCode===null)server.kill();
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  await fs.rm(extension,{recursive:true,force:true}).catch(()=>{});
  await fs.rm(profile,{recursive:true,force:true,maxRetries:6,retryDelay:120}).catch(()=>{});
}
