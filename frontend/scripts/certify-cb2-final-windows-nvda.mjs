/**
 * CB2 G6 Windows hosted native Chrome zoom + real NVDA speech.
 *
 * Real MainLayout G6 synthetic lab with synthetic INTERCEPTED responses. The only
 * certification scope here is native zoom/keyboard/NVDA accessibility of the
 * real G6 component; it is NOT a human Windows clinic rehearsal.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
import { nvda } from '@guidepup/guidepup';

const HEAD = process.env.CB03_CB2_SOURCE_HEAD || '';
const origin = 'http://127.0.0.1:5173';
const url = origin + '/cb03-g6-mainlayout-lab.html';
if (process.platform !== 'win32' || process.env.GITHUB_ACTIONS !== 'true' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    process.env.CB03_CB2_WINDOWS_NVDA_EXPERIMENT !== '1' ||
    !/^[0-9a-f]{40}$/.test(HEAD)) {
  throw Error('REFUSED: exact-head isolated Windows NVDA G4 CI only');
}
const out = path.resolve('../artifacts/cb2-final/windows-nvda-g6');
await fs.mkdir(out, { recursive:true });
const extension = await fs.mkdtemp(path.join(os.tmpdir(), 'cb2-g6-ext-'));
const profile = await fs.mkdtemp(path.join(os.tmpdir(), 'cb2-g6-profile-'));
await fs.writeFile(path.join(extension, 'manifest.json'), JSON.stringify({
  manifest_version:3, name:'CB03 G4 Native Zoom Guard', version:'1.0.0',
  permissions:['tabs'], host_permissions:[origin+'/*'],
  background:{service_worker:'worker.js'},
}));
await fs.writeFile(path.join(extension,'worker.js'),
  'chrome.runtime.onInstalled.addListener(() => {});\n');

const report = {
  schema:'CB2_G6_WINDOWS_REAL_NVDA_NATIVE_ZOOM_V1',
  sourceHead:HEAD, realNvdaSpeech:false, nativeZoomAtSpeech:null,
  nativeZoomMethod:'extension_chrome_tabs_setZoom_getZoom',
  sourceScope:'REAL_MAINLAYOUT_G5_CHAT_MOCKED_HTTP_SYNTHETIC',
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
  throw Error('REFUSED: no loopback G6 lab');
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
  message: /votre message [àa] crown bot/i,
  send: /envoyer/i,
  confirmation: /confirmer explicitement cette action/i,
};
const roleMatches = {
  message: s=>descriptors.message.test(s) && /edit|[ée]dition|textbox/i.test(s),
  send: s=>descriptors.send.test(s) && /button|bouton/i.test(s),
  confirmation: s=>descriptors.confirmation.test(s) && /button|bouton/i.test(s),
};
const found=Object.fromEntries(Object.keys(roleMatches).map(k=>[k,false]));
async function collect(stage) {
  const raw=await nvda.spokenPhraseLog();
  const phrases=(Array.isArray(raw)?raw:[raw]).map(String);
  report.spokenPhrases=phrases.slice(-250);
  for(const [key,fn] of Object.entries(roleMatches))
    found[key] ||= phrases.some(fn);
  report.controls={...found};
  console.log('CB2_G6_NVDA_SPEECH_STAGE',JSON.stringify({
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
    // Reuse the existing DEV-only PWA blocker used by the CB-02 NVDA lab:
    // no service-worker registration or Workbox fallback in this disposable tab.
    env:{...process.env,VITE_CB03_G6_MAINLAYOUT_LAB:'true',
      VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED:'true',
      VITE_CROWN_BOT_GUIDED_NLU_ENABLED:'true',
      VITE_CROWN_BOT_CB03_CHAT_ENABLED:'true',
      VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED:'false',
      VITE_CROWN_BOT_CB03_G3_ENABLED:'true',
      VITE_CB03_G4_NATIVE_A11Y_LAB:'true'},
    stdio:['ignore','pipe','pipe'],
  });
  server.stdout.on('data',d=>process.stdout.write('[G6-Vite] '+String(d)));
  server.stderr.on('data',d=>process.stderr.write('[G6-Vite] '+String(d)));
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
  await page.route('**/api/bot/sessions',r=>r.fulfill({status:200,contentType:'application/json',body:'[]'}));
  await page.route('**/api/bot/guided/**',async route=>{
    const req=route.request(), headers={'access-control-allow-origin':origin,'access-control-allow-credentials':'true',
      'access-control-allow-headers':'authorization,content-type',
      'access-control-allow-methods':'GET,POST,OPTIONS'};
    if(req.method()==='OPTIONS'){await route.fulfill({status:204,headers});return;}
    if(req.method()==='POST' && req.url().endsWith('/prepare-appointment')){
      if(req.postDataJSON().utterance!=='Prépare un RDV demain 10h pour Mme Benali contrôle')
        throw Error('REFUSED: unexpected first-user request');
      await route.fulfill({status:200,headers,contentType:'application/json',
        body:JSON.stringify({status:'prepared',executable:false,
          preparation_id:'d4a97731-cdcb-4b9c-94d3-f1d21c242a21',expires_at:'2026-11-01T12:30:00',
          summary:{patient:{id:21,nom:'Benali',prenom:'Salma',numero_dossier:'S-21'},praticien_id:9,
          resource_id:null,datetime_start:'2026-11-07T10:00:00',duration_minutes:30,motif:'CONTROLE'}})});
      return;
    }
    if(req.method()==='POST'&&req.url().endsWith('/confirm')){
      if(req.postDataJSON().confirm!==true)throw Error('REFUSED: unconfirmed mutation');
      await route.fulfill({status:200,headers,contentType:'application/json',body:JSON.stringify({
        preparation_id:'d4a97731-cdcb-4b9c-94d3-f1d21c242a21',status:'executed',
        result:{appointment_id:81,status:'CREATED'}})});
      return;
    }
    throw Error('REFUSED: unsupported G6 request');
  });
  await page.goto(url,{waitUntil:'load',timeout:45000});
  const launcher=page.getByRole('button',{name:'Ouvrir CrownBot'});
  await launcher.waitFor();
  await launcher.click();
  const panel=page.getByRole('region',{name:'Conversation Crown Bot — actions guidées CB-03'});
  await panel.waitFor();
  const controls={
    message:page.getByRole('textbox',{name:'Votre message à Crown Bot'}),
    send:page.getByRole('button',{name:'Envoyer'}),
  };
  for(const [key,loc] of Object.entries(controls))
    if(!(await loc.isVisible()))throw Error('NOT_CERTIFIED: missing G6 control '+key);
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
  await controls.message.fill('Prépare un RDV demain 10h pour Mme Benali contrôle');
  const keyboardSequence=[controls.message,controls.send];
  await controls.message.focus();
  await page.keyboard.press('Tab');
  if(!await controls.send.evaluate(el=>document.activeElement===el))
    throw Error('NOT_CERTIFIED: message→send keyboard order');
  await page.keyboard.press('Shift+Tab');
  if(!await controls.message.evaluate(el=>document.activeElement===el))
    throw Error('NOT_CERTIFIED: send→message reverse keyboard order');
  report.keyboard={messageToSend:true,reverse:true};
  await nvda.start({capture:true});
  nvdaStarted=true;
  await sleep(700);
  await page.bringToFront();
  await nvda.clearSpokenPhraseLog();
  try {await nvda.perform(nvda.keyboardCommands.exitFocusMode);}catch {}
  await nvda.press('Control+Home');
  await sleep(300);
  // Navigate the real controls with NVDA's own keyboard path, not a detached
  // virtual-buffer walk which may get stuck reading the header repeatedly.
  await controls.send.focus();
  await nvda.press('Shift+Tab');
  await sleep(400);
  await collect('keyboard-message');
  await nvda.press('Tab');
  await sleep(400);
  await collect('keyboard-send');
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
  await controls.send.click();
  await page.getByText('Salma Benali · Dossier S-21').waitFor();
  const confirm=page.getByRole('button',{name:'Confirmer explicitement cette action'});
  if(await confirm.isEnabled())throw Error('NOT_CERTIFIED: default confirmation enabled');
  // The disabled confirmation is reached from the previous checkbox via Tab.
  // Both the focus path and the spoken button label must be observed.
  await confirm.focus();
  await nvda.press('Shift+Tab');
  await sleep(350);
  await collect('keyboard-checkbox');
  await nvda.press('Tab');
  await sleep(350);
  await collect('keyboard-confirmation');
  await collect('prepared');
  for(let i=0;i<45 && !found.confirmation;i++){
    try{await nvda.next();}catch{break;}
    await sleep(90);
    await collect('confirm-'+i);
  }
  report.nativeZoomAtSpeech=(await zoom(worker,null)).value;
  if(Math.abs(report.nativeZoomAtSpeech-2)>0.01)throw Error('NOT_CERTIFIED: zoom not 200');
  if(!found.message || !found.send || !found.confirmation)
    throw Error('NOT_CERTIFIED: NVDA did not speak G6 conversation / confirmation');
  await nvda.stop();nvdaStarted=false;
  await page.getByRole('checkbox',{name:/J’ai vérifié le patient/}).check();
  if(!await confirm.isEnabled())throw Error('NOT_CERTIFIED: checkbox did not unlock confirmation');
  await confirm.click();
  await page.getByText(/Action exécutée et vérifiée · RDV #81/).waitFor();
  if(requests.length!==2 || !requests[0].endsWith('/prepare-appointment') || !requests[1].endsWith('/confirm'))
    throw Error('NOT_CERTIFIED: G6 unexpected HTTP writes');
  await page.screenshot({path:path.join(out,'g6-real-nvda-200-receipt.png')});
  report.screenshots.push('g6-real-nvda-200-receipt.png');
  report.status='PASS_HOSTED_REAL_NVDA_NATIVE_ZOOM_SYNTHETIC_G6';
  console.log('CB2_G6_WINDOWS_REAL_NVDA_ZOOM_PASS',JSON.stringify({
    sourceHead:HEAD,zoom:report.nativeZoomAtSpeech,roles:report.controls,
    httpPosts:requests,
  }));
  if(errors.length)throw Error('NOT_CERTIFIED: browser runtime error '+errors.join(';'));
}catch(error){
  report.status='NOT_CERTIFIED';
  report.error=String(error?.stack||error);
  process.exitCode=1;
  console.error('CB2_G6_WINDOWS_REAL_NVDA_ZOOM_NOT_CERTIFIED',report.error);
}finally{
  try {if(nvdaStarted) await nvda.stop();}catch {}
  try {await browser?.close();}catch {}
  if(server?.exitCode===null)server.kill();
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  await fs.rm(extension,{recursive:true,force:true}).catch(()=>{});
  await fs.rm(profile,{recursive:true,force:true,maxRetries:6,retryDelay:120}).catch(()=>{});
}
