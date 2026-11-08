/**
 * Screenshot-only synthetic FUE for the exact Step4Documents React component.
 * BEFORE = approved parent PR #1213 source. AFTER = PR #1219 source.
 * Does not run a backend, inspect any clinical database, or authorize signing.
 */
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { readFile, writeFile, rm, mkdir } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const productFile = path.join(root, 'src/features/ortho/components/Step4Documents.tsx');
const baselineFile = path.resolve(process.env.CEPH_BASELINE_FILE || '../baseline/frontend/src/features/ortho/components/Step4Documents.tsx');
const entryFile = path.join(root, 'src/ceph-archive-hold-visual-fixture.tsx');
const htmlFile = path.join(root, 'ceph-archive-hold-visual.html');
const output = path.join(root, 'ceph-unsigned-archive-visual-proof');
const port = 5198;
const origin = 'http://127.0.0.1:' + port;
const head = process.env.CEPH_PRODUCT_HEAD;
const baseSha = process.env.CEPH_BASE_SHA;
if (!/^[0-9a-f]{40}$/.test(head || '') || !/^[0-9a-f]{40}$/.test(baseSha || '')) {
  throw Error('Exact SHA of both UI versions is mandatory');
}
const originalSource = await readFile(productFile, 'utf8');
const baselineSource = await readFile(baselineFile, 'utf8');
if (!originalSource.includes('Archivage suspendu') || !baselineSource.includes('Archiver le bilan')) {
  throw Error('BEFORE / AFTER exact UI anchors not present; refuse screenshot proof');
}
const entry = [
  "import React from 'react';",
  "import ReactDOM from 'react-dom/client';",
  "import { Step4Documents } from './features/ortho/components/Step4Documents';",
  "import { REQUIRED_LANDMARKS } from './features/ortho/cephaloShared';",
  "import { getCephaloPalette } from './features/ortho/cephaloTheme';",
  "import { useOrthoStore } from './features/ortho/stores/useOrthoStore';",
  "import { cephaloRepository } from './features/ortho/cephaloRepository';",
  "import { api } from './services/api';",
  "import './index.css';",
  "const landmarks = REQUIRED_LANDMARKS.map((id, i) => ({ id, x: 100+i*2, y: 200+i*3 }));",
  "const fakeImage = 'data:image/svg+xml,'+encodeURIComponent('<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"900\" height=\"1100\"><rect width=\"900\" height=\"1100\" fill=\"#dce5ed\"/></svg>');",
  "useOrthoStore.setState({patientId:915,patientName:'CAS TEST SYNTHÉTIQUE',analysisId:9915,imageSrc:fakeImage,isCalibrated:true,local:{landmarks,version:1},diag:{synthese_diagnostique:'Note fictive de test',strategie_therapeutique:''},anglesData:{SNA:82,SNB:80,ANB:2}});",
  "cephaloRepository.getAnalysis = async () => ({id:9915,angles_data:{scientific_read_path:{revision:1}}});",
  "api.get = async () => ({data:{analysis_id:9915,analysis_revision:1,valid:true,fatals:[],warnings:[]}});",
  "document.body.dataset.theme='light';",
  "ReactDOM.createRoot(document.getElementById('root')).render(<div style={{padding:16,margin:'0 auto',maxWidth:1480}}><Step4Documents P={getCephaloPalette()}/></div>);",
].join('\n');
const html = '<!doctype html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CEPH unsigned A4 archival visual fixture</title></head><body><div id="root"></div><script type="module" src="/src/ceph-archive-hold-visual-fixture.tsx"></script></body></html>';
let server;
let browser;
const contexts=[];
const proof={head,baseline_sha:baseSha,source:'Real Step4Documents React UI, synthetic fixture only',no_real_patient:true,no_clinical_approval:true,viewports:[],errors:[]};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function waitForServer() {
  for(let i=0;i<100;i++){
    try { const r=await fetch(origin+'/ceph-archive-hold-visual.html'); if(r.ok)return; } catch {}
    await sleep(250);
  }
  throw Error('Vite fixture server did not start');
}
try {
  await rm(output,{recursive:true,force:true});
  await mkdir(output,{recursive:true});
  await writeFile(productFile,baselineSource,'utf8');
  await writeFile(entryFile,entry,'utf8');
  await writeFile(htmlFile,html,'utf8');
  const vite = path.join(root,'node_modules/.bin/vite');
  server=spawn(vite,['--host','127.0.0.1','--port',String(port), '--strictPort'],{cwd:root,env:{...process.env,BROWSER:'none',VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']});
  await waitForServer();
  browser=await chromium.launch({headless:true});
  const viewports=[{name:'desktop-1280x900',width:1280,height:900},{name:'mobile-390x844',width:390,height:844}];
  for (const viewport of viewports) {
    const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},reducedMotion:'reduce'});
    contexts.push(context);
    const page=await context.newPage();
    page.on('pageerror',err=>proof.errors.push(viewport.name+': '+err.message));
    await page.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.abort());
    await page.goto(origin+'/ceph-archive-hold-visual.html',{waitUntil:'networkidle',timeout:35000});
    const archive=page.getByRole('button',{name:'Archiver le bilan'});
    await archive.waitFor({state:'visible',timeout:20000});
    await page.waitForFunction(()=>{const b=[...document.querySelectorAll('button')].find(el=>el.textContent?.includes('Archiver le bilan'));return b && !b.disabled;},{timeout:12000});
    await archive.scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(output,viewport.name+'-BEFORE.png'),animations:'disabled'});
    // Close BEFORE page before replacing the source: Vite HMR can abort an
    // in-flight page.reload when the component switches during navigation.
    // AFTER uses a clean page in the same viewport/context, not an HMR race.
    await page.close();
    proof.viewports.push({name:viewport.name,before:'Archiver le bilan enabled by science-only check',context});
  }
  await writeFile(productFile,originalSource,'utf8');
  await sleep(500);
  for(const entry of proof.viewports) {
    const page=await entry.context.newPage();
    page.on('pageerror',err=>proof.errors.push(entry.name+': '+err.message));
    await page.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.abort());
    await page.goto(origin+'/ceph-archive-hold-visual.html',{waitUntil:'domcontentloaded',timeout:35000});
    const archive=page.getByRole('button',{name:'Archivage suspendu'});
    await archive.waitFor({state:'visible',timeout:20000});
    if(!await archive.isDisabled())throw Error(entry.name+' archive must be disabled');
    const draft=page.getByRole('button',{name:'Brouillon PDF'});
    if(!await draft.isEnabled())throw Error(entry.name+' draft export should remain available');
    const message=page.getByTestId('unsigned-cephalo-archive-hold');
    if(!/signature vérifiable du document exact/i.test(await message.innerText()))throw Error('Missing user-facing reason');
    await archive.scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(output,entry.name+'-AFTER.png'),animations:'disabled'});
    entry.after='Archivage suspendu disabled; draft button enabled; explicit unsigned reason';
    await page.close();
    delete entry.context;
  }
  if(proof.errors.length)throw Error('React browser runtime errors: '+proof.errors.join('; '));
  await writeFile(path.join(output,'evidence.json'),JSON.stringify(proof,null,2),'utf8');
  console.log('CEPH_UNSIGNED_A4_VISUAL_BEFORE_AFTER_SYNTHETIC_PASS '+JSON.stringify({head,baseSha,viewports:proof.viewports.map(v=>v.name)}));
} finally {
  for(const ctx of contexts)await ctx.close().catch(()=>{});
  if(browser)await browser.close().catch(()=>{});
  if(server){server.kill('SIGTERM');await sleep(250);}
  await writeFile(productFile,originalSource,'utf8');
  await rm(entryFile,{force:true});
  await rm(htmlFile,{force:true});
}
