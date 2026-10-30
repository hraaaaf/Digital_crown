// POLISH-02 R5: genuine native Chromium zoom on headed Windows in isolated T2.
// Real login + synthetic patient. Never a simulated CSS viewport substitute.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha=process.env.CB01_SOURCE_HEAD;
assert.ok(process.platform==='win32' && process.env.GITHUB_ACTIONS==='true' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME==='1' &&
  process.env.ENVIRONMENT==='test' && /^[0-9a-f]{40}$/.test(sha||'') &&
  process.env.T2_USER==='t2-browser@cabinet.ma' && process.env.T2_PASSWORD,
  'REFUSED: native R5 zoom requires Windows synthetic isolated exact HEAD');
const origin='http://127.0.0.1:5173', apiOrigin='http://127.0.0.1:8005';
const out=path.resolve('../artifacts/lot07-r5-native-zoom-windows');
await fs.mkdir(out,{recursive:true});
const ext=await fs.mkdtemp(path.join(os.tmpdir(),'dc-r5-zoom-ext-'));
const profile=await fs.mkdtemp(path.join(os.tmpdir(),'dc-r5-zoom-profile-'));
const report={sourceHead:sha,lab:'POLISH02_REAL_WINDOWS_NATIVE_CHROME_TABS_ZOOM',
  syntheticOnly:true,actualFastAPI:true,clinicalWritesAttempted:[],
  zoomBefore:null,zoomAfter:null,at100:null,at200:null,reflow:null,
  screenshots:[],pass:false,error:null,humanVisualApproval:false};
let vite=null,browser=null,api=null;
const snapshot=async page=>page.evaluate(()=>{
  const width=document.documentElement.clientWidth;
  const box=(testid)=>{
    const e=document.querySelector('[data-testid="'+testid+'"]');
    if(!e)return {present:false,visible:false,fits:false};
    const r=e.getBoundingClientRect();
    return {present:true,visible:r.width>0&&r.height>0,
      fits:r.left>=-2&&r.right<=width+2,
      left:Math.round(r.left),right:Math.round(r.right)};
  };
  return {innerWidth:innerWidth,devicePixelRatio:devicePixelRatio,
    clientWidth:width,scrollWidth:document.documentElement.scrollWidth,
    signature:box('r5-signature-prefs'),
    signatureToggle:box('r5-signature-toggle'),
    multiview:box('r5-multiview-prefs'),
    mobileSafe:box('multiview-mobile-safe-view'),
    clinicalFallback:box('multiview-responsive-single-media-fallback')};
});
async function zoom(worker,pathname,factor){
  const result=await worker.evaluate(async ({pathname,factor})=>{
    const tabs=await chrome.tabs.query({});
    const candidates=tabs.filter(t=>t.id &&
      t.url?.startsWith('http://127.0.0.1:5173'+pathname));
    if(candidates.length!==1)throw Error('Native extension: R5 patient tab not unique');
    await chrome.tabs.setZoom(candidates[0].id,factor);
    return {tabId:candidates[0].id,observed:await chrome.tabs.getZoom(candidates[0].id)};
  },{pathname,factor});
  assert.ok(Math.abs(result.observed-factor)<0.01,'REFUSED: getZoom not '+factor);
  return result;
}
try{
  await fs.writeFile(path.join(ext,'manifest.json'),JSON.stringify({
    manifest_version:3,name:'POLISH02 R5 Native Zoom Proof',version:'1.0.0',
    permissions:['tabs'],host_permissions:[origin+'/*'],
    background:{service_worker:'service-worker.js'},
  }));
  await fs.writeFile(path.join(ext,'service-worker.js'),
    'chrome.runtime.onInstalled.addListener(() => {});\n');
  vite=spawn(process.execPath,[
    path.resolve('node_modules/vite/bin/vite.js'),
    '--host','127.0.0.1','--port','5173','--strictPort',
  ],{cwd:process.cwd(),env:{...process.env,
    VITE_V15_07_R4_SIGNATURE_LAB:'true',
    VITE_V15_07_R5_PREFS_LAB:'true',
    VITE_V15_07_1_MULTIVIEW_LAB:'1',
    VITE_TELEMETRY_ENABLED:'false',
  },stdio:['ignore','pipe','pipe'],windowsHide:true});
  vite.stdout.on('data',x=>process.stdout.write('[R5 Vite] '+String(x)));
  vite.stderr.on('data',x=>process.stderr.write('[R5 Vite] '+String(x)));
  let ready=false;
  for(let n=0;n<60;n++){
    if(vite.exitCode!==null)break;
    try{
      const r=await fetch(origin+'/login',{signal:AbortSignal.timeout(1500)});
      if(r.ok){ready=true;break;}
    }catch{}
    await new Promise(resolve=>setTimeout(resolve,1000));
  }
  assert.ok(ready,'R5 Vite did not start on isolated Windows runner');
  api=await request.newContext({baseURL:apiOrigin});
  const login=await api.post('/api/auth/login',{
    form:{username:process.env.T2_USER,password:process.env.T2_PASSWORD}});
  assert.equal(login.status(),200,'Real synthetic owner login');
  const token=(await login.json()).access_token;
  assert.ok(token,'Owner token required');
  const enrolled=await enrollT2Workstation(api,token,process.env.T2_PASSWORD);
  const station=enrolled.cookies.filter(c=>c.name==='dc_workstation'&&c.httpOnly);
  assert.equal(station.length,1,'Verified HttpOnly T2 workstation required');
  const patientResponse=await api.get('/api/patients/',{
    headers:{Authorization:'Bearer '+token}});
  assert.equal(patientResponse.status(),200,'Real synthetic clinic patients');
  const patient=(await patientResponse.json()).find(p=>p.numero_dossier==='T2-0001');
  assert.ok(Number.isSafeInteger(patient?.id)&&patient.id>0,'T2-0001 fixture required');
  browser=await chromium.launchPersistentContext(profile,{
    channel:'chromium',headless:false,viewport:{width:1920,height:900},
    args:['--disable-extensions-except='+ext,'--load-extension='+ext,
      '--no-first-run','--disable-background-networking'],
  });
  const worker=browser.serviceWorkers()[0]||
    await browser.waitForEvent('serviceworker',{timeout:20000});
  assert.ok(worker.url().startsWith('chrome-extension://'),'Real zoom extension missing');
  await browser.addCookies(station);
  const page=browser.pages()[0]||await browser.newPage();
  page.on('request',req=>{
    const p=new URL(req.url()).pathname;
    if(req.method()!=='GET'&&
      /\/api\/(?:patients\/|documents\/|appointments\/|devis\/)/.test(p))
      report.clinicalWritesAttempted.push(req.method()+' '+p);
  });
  await page.goto(origin+'/login',{waitUntil:'domcontentloaded',timeout:90000});
  await page.locator('input[type=email]').fill(process.env.T2_USER);
  await page.locator('input[type=password]').fill(process.env.T2_PASSWORD);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/dashboard',{timeout:60000});
  const patientPath='/patients/'+patient.id;
  await page.goto(origin+patientPath+'?tab=radiology&radioTab=media',{
    waitUntil:'domcontentloaded',timeout:90000});
  const sign=page.locator('[data-testid="r5-signature-prefs"]');
  const multi=page.locator('[data-testid="r5-multiview-prefs"]');
  await sign.waitFor({state:'visible',timeout:60000});
  await multi.waitFor({state:'visible',timeout:60000});
  assert.equal(await page.locator('[data-lot07-polish02]')
    .getAttribute('data-lot07-polish02'),'clinical-first',
    'R5 patient workspace not gated as clinical-first');
  report.zoomBefore=await zoom(worker,patientPath,1);
  report.at100=await snapshot(page);
  assert.ok(report.at100.signature.visible&&report.at100.multiview.visible,
    'R5 real 100% signature/MultiView rails missing');
  await page.screenshot({path:path.join(out,'R5-native-100-desktop.png')});
  report.screenshots.push('R5-native-100-desktop.png');
  report.zoomAfter=await zoom(worker,patientPath,2);
  await page.waitForFunction(before=>
    innerWidth<=Math.ceil(before.innerWidth*0.6) &&
    devicePixelRatio>before.devicePixelRatio,
    {innerWidth:report.at100.innerWidth,devicePixelRatio:report.at100.devicePixelRatio},
    {timeout:20000,polling:'raf'});
  report.at200=await snapshot(page);
  const getZoom=await worker.evaluate(async pathname=>{
    const tabs=await chrome.tabs.query({});
    const target=tabs.filter(t=>t.id &&
      t.url?.startsWith('http://127.0.0.1:5173'+pathname));
    if(target.length!==1)throw Error('Native R5 tab changed at 200%');
    return {tabId:target[0].id,observed:await chrome.tabs.getZoom(target[0].id)};
  },patientPath);
  assert.equal(getZoom.tabId,report.zoomAfter.tabId,'R5 zoom tab identity changed');
  assert.ok(Math.abs(getZoom.observed-2)<0.01,'R5 native zoom not retained');
  assert.ok(report.at200.scrollWidth<=report.at200.clientWidth+2,
    'R5 clinical page horizontal overflow at native 200%');
  assert.ok(report.at200.signature.visible&&report.at200.signature.fits &&
    report.at200.signatureToggle.visible&&report.at200.signatureToggle.fits,
    'R5 Signature rail/control not reachable at native 200%');
  assert.ok((report.at200.mobileSafe.visible&&report.at200.mobileSafe.fits) ||
    (report.at200.clinicalFallback.visible&&report.at200.clinicalFallback.fits),
    'R5 patient safe read-only fallback not visible at native 200%');
  await page.screenshot({path:path.join(out,'R5-native-200-patient-top.png')});
  report.screenshots.push('R5-native-200-patient-top.png');
  await sign.scrollIntoViewIfNeeded();
  await page.locator('[data-testid="r5-signature-toggle"]').focus();
  await page.screenshot({path:path.join(out,'R5-native-200-signature-focused.png')});
  report.screenshots.push('R5-native-200-signature-focused.png');
  assert.equal(report.clinicalWritesAttempted.length,0,
    'Clinical API mutation attempted during native zoom');
  report.reflow='PASS_TRUE_CHROME_EXTENSION_GETZOOM_2_R5_REAL_PATIENT_SAFE';
  report.pass=true;
  console.log('POLISH02_R5_NATIVE_ZOOM_RESULT',JSON.stringify({
    sourceHead:sha,pass:true,at100:report.at100.innerWidth,
    at200:report.at200.innerWidth,zoom:getZoom.observed,
    noHorizontalOverflow:true}));
}catch(e){
  report.error=String(e?.stack||e);
  console.error('POLISH02_R5_NATIVE_ZOOM_FAILED',report.error);
  process.exitCode=1;
}finally{
  try{await browser?.close();}catch{}
  try{await api?.dispose();}catch{}
  if(vite?.exitCode===null)vite.kill();
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  await fs.rm(ext,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
  await fs.rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
