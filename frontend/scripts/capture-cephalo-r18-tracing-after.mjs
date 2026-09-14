import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'cephalo-r18-tracing-after-artifacts');
const PORT = 5193;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];
const modes = ['all', 'steiner', 'tweed', 'mcnamara', 'ricketts'];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { CephaloWorkspace } from './features/ortho/CephaloWorkspace';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import './index.css';

document.body.dataset.theme = 'dark';
const fixture = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(\`
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600">
<defs><radialGradient id="g"><stop offset="0" stop-color="#475569"/><stop offset="1" stop-color="#020617"/></radialGradient></defs>
<rect width="1200" height="1600" fill="url(#g)"/><path d="M410 210 C720 250 820 480 760 760 C710 1000 560 1210 390 1390" fill="none" stroke="#cbd5e1" stroke-width="18" opacity=".26"/><ellipse cx="610" cy="600" rx="250" ry="350" fill="none" stroke="#94a3b8" stroke-width="10" opacity=".18"/></svg>\`);
const landmarks = [
{id:'S',x:430,y:370},{id:'N',x:650,y:360},{id:'A',x:690,y:620},{id:'B',x:675,y:790},
{id:'Po',x:390,y:500},{id:'Or',x:650,y:520},{id:'Go',x:430,y:980},{id:'Me',x:680,y:1040},
{id:'Co',x:410,y:430},{id:'Gn',x:690,y:1010},{id:'ANS',x:685,y:610},
{id:'Occ_Ant',x:715,y:760},{id:'Occ_Post',x:500,y:790},
{id:'U1_apex',x:640,y:650},{id:'U1_incisal',x:690,y:770},{id:'L1_apex',x:650,y:900},{id:'L1_incisal',x:700,y:785},
{id:'G_soft',x:720,y:300},{id:'N_soft',x:760,y:355},{id:'Prn',x:835,y:515},{id:'Cm',x:790,y:575},{id:'Sn_soft',x:760,y:610},
{id:'A_soft',x:770,y:650},{id:'Ls_soft',x:805,y:700},{id:'St',x:795,y:755},{id:'Li_soft',x:810,y:805},{id:'B_soft',x:770,y:875},{id:'Pog_soft',x:790,y:965},{id:'Me_soft',x:750,y:1060}
];
useOrthoStore.setState({
 patientId: 918, patientName: 'Patient Démo R18', analysisId: 9918, imageSrc: fixture,
 imgDim:{w:1200,h:1600}, local:{landmarks,version:1}, mmPerPixel:0.2, isCalibrated:true,
 completedSteps:new Set([1]), step:1,
 etape3Data:{...useOrthoStore.getState().etape3Data,selectedAnalysis:'COM'}
});
ReactDOM.createRoot(document.getElementById('root')).render(<MemoryRouter><div style={{height:'100vh'}}><CephaloWorkspace patientId={918} patientName="Patient Démo R18" /></div></MemoryRouter>);
`;
const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Cephalo R18 AFTER</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-r18-tracing-after-entry.tsx"></script></body></html>`;

function json(body,status=200){return{status,contentType:'application/json',body:JSON.stringify(body)}}
async function waitForServer(url,timeoutMs=30000){const start=Date.now();while(Date.now()-start<timeoutMs){try{const r=await fetch(url);if(r.ok)return}catch{}await new Promise(r=>setTimeout(r,250))}throw new Error(`Vite unavailable ${url}`)}

function modeContract(mode, metrics) {
  if (metrics.analysis !== mode || !metrics.hasAnalysisSelector || metrics.horizontalOverflow) return false;
  const labels = new Set(metrics.landmarkLabels);
  if (mode === 'all') return metrics.svgLines > 8 && metrics.selectorButtons.length === 5;
  if (mode === 'steiner') return labels.has('S') && labels.has('N') && labels.has('A') && labels.has('B') && !labels.has('Po') && !labels.has('McNamara');
  if (mode === 'tweed') return labels.has('Po') && labels.has('Or') && labels.has('Go') && labels.has('Me') && !labels.has('S') && !labels.has('McNamara');
  if (mode === 'mcnamara') return labels.has('McNamara') && labels.has("A'") && labels.has("B'") && labels.has('Wits') && !labels.has('S') && !labels.has('U1_apex');
  if (mode === 'ricketts') return labels.has('Prn') && labels.has('Ls_soft') && labels.has('Li_soft') && !labels.has('S') && !labels.has('Go') && !labels.has('McNamara') && metrics.rickettsConstructionCount >= 1;
  return false;
}

await rm(OUTPUT_DIR,{recursive:true,force:true}); await mkdir(OUTPUT_DIR,{recursive:true});
await writeFile(path.join(FRONTEND_DIR,'src','cephalo-r18-tracing-after-entry.tsx'),entrySource,'utf8');
await writeFile(path.join(FRONTEND_DIR,'cephalo-r18-tracing-after.html'),htmlSource,'utf8');
const viteBin=path.join(FRONTEND_DIR,'node_modules','.bin',process.platform==='win32'?'vite.cmd':'vite');
const server=spawn(viteBin,['--host','127.0.0.1','--port',String(PORT)],{cwd:FRONTEND_DIR,env:{...process.env,BROWSER:'none',VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']});
let serverLog=''; server.stdout.on('data',c=>serverLog+=c); server.stderr.on('data',c=>serverLog+=c);
const captures=[]; const blockedExternalRequests=[];

async function captureViewport(viewport,attempt){
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},reducedMotion:'reduce',locale:'fr-FR'});
 const page=await context.newPage();
 const pageErrors=[]; const consoleErrors=[];
 page.on('pageerror',e=>pageErrors.push(e.message)); page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
 await page.route('**/*',async route=>{const req=route.request();const u=new URL(req.url());if(u.hostname==='127.0.0.1'&&u.port===String(PORT))return route.continue();if(u.hostname==='127.0.0.1'&&u.port==='8005'){if(req.method()==='GET'&&u.pathname==='/api/patients/918')return route.fulfill(json({id:918,age:34,sexe:'M'}));return route.fulfill(json({detail:'neutralized'},418));}if(u.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});blockedExternalRequests.push({viewport:viewport.name,attempt,url:req.url()});return route.abort('blockedbyclient')});
 try{
  const response=await page.goto(`${BASE_URL}/cephalo-r18-tracing-after.html`,{waitUntil:'domcontentloaded',timeout:30000});
  await page.getByRole('heading',{name:'Studio Céphalométrique'}).waitFor({state:'visible',timeout:30000});
  await page.locator('[aria-label="Analyse du tracé"]').waitFor({state:'visible',timeout:10000});
  const states=[];
  for(const mode of modes){
   await page.locator(`[data-analysis="${mode}"]`).click();
   await page.waitForFunction(expected=>document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis')===expected,mode,{timeout:5000});
   await page.waitForTimeout(120);
   const metrics=await page.evaluate(()=>({
    analysis:document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis')||null,
    hasAnalysisSelector:Boolean(document.querySelector('[aria-label="Analyse du tracé"]')),
    selectorButtons:Array.from(document.querySelectorAll('[aria-label="Analyse du tracé"] button')).map(n=>n.getAttribute('data-analysis')),
    svgLines:document.querySelectorAll('svg line').length,
    svgPaths:document.querySelectorAll('svg path').length,
    landmarkLabels:Array.from(document.querySelectorAll('svg text')).map(n=>n.textContent?.trim()).filter(Boolean),
    rickettsConstructionCount:document.querySelectorAll('[data-r18-construction^="ricketts-"]').length,
    horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1
   }));
   const valid=modeContract(mode,metrics);
   await page.screenshot({path:path.join(OUTPUT_DIR,`after-tracing-${mode}-${viewport.name}.png`),fullPage:false});
   states.push({mode,valid,metrics});
  }
  const valid=response?.status()===200&&!pageErrors.length&&!consoleErrors.length&&states.every(s=>s.valid);
  return {viewport:viewport.name,attempt,valid,pageErrors,consoleErrors,states};
 }catch(error){return{viewport:viewport.name,attempt,valid:false,pageErrors:[...pageErrors,error instanceof Error?error.message:String(error)],consoleErrors,states:[]}}
 finally{await context.close().catch(()=>{});await browser.close().catch(()=>{})}
}

try{
 await waitForServer(`${BASE_URL}/cephalo-r18-tracing-after.html`);
 for(const viewport of viewports){
  const attempts=[await captureViewport(viewport,1)];
  if(!attempts[0].valid)attempts.push(await captureViewport(viewport,2));
  const finalAttempt=attempts.at(-1);
  captures.push({...finalAttempt,attempts:attempts.map(a=>({attempt:a.attempt,valid:a.valid,pageErrors:a.pageErrors,consoleErrors:a.consoleErrors,states:a.states})),recoveredTransientRender:attempts.length===2&&!attempts[0].valid&&attempts[1].valid});
 }
}finally{if(!server.killed)server.kill('SIGTERM');await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{});await writeFile(path.join(OUTPUT_DIR,'vite.log'),serverLog,'utf8')}
const invalid=captures.filter(c=>!c.valid); const report={lot:'CEPHALO-R18-TRACING',phase:'AFTER',productHead:PRODUCT_HEAD,viewports:viewports.map(v=>v.name),modes,capturePolicy:'Same deterministic R18 fixture and same 390/768/1280 viewports as BEFORE; fresh Chromium per viewport; one retry only after invalid first render.',captures,blockedExternalRequests,invalidCount:invalid.length};
await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8'); console.log(JSON.stringify(report,null,2)); if(invalid.length||blockedExternalRequests.length)process.exitCode=1;
