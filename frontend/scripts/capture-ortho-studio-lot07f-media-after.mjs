import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const PORT = 5207;
const BASE_URL = 'http://127.0.0.1:' + PORT;
const phases = [
  { name: 'normal', text200: false, dir: 'ortho-studio-lot07f-media-after-artifacts' },
  { name: 'text200', text200: true, dir: 'ortho-studio-lot07f-media-after-text200-artifacts' },
];
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '430x932', width: 430, height: 932 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const entryPath = path.join(FRONTEND_DIR, 'src', 'ortho-studio-lot07f-media-after-entry.tsx');
const htmlPath = path.join(FRONTEND_DIR, 'ortho-studio-lot07f-media-after.html');
const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { OrthoMediaRecordPanel } from './features/ortho/components/OrthoMediaRecordPanel';
import './index.css';
const P = {
  bg:'#f8fafc',bgPanel:'#ffffff',bgCard:'#ffffff',bgInput:'#f8fafc',
  border:'#e2e8f0',text:'#0f172a',textMuted:'#64748b',textDim:'#94a3b8',
  accent:'#2563eb',accentSuccess:'#16a34a',accentError:'#dc2626'
};
ReactDOM.createRoot(document.getElementById('root')!).render(
  <main style={{minHeight:'100vh',padding:'16px',background:P.bg}}>
    <OrthoMediaRecordPanel patientId={919} P={P} />
  </main>
);
`;
const htmlSource = '<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>LOT07F media AFTER</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/ortho-studio-lot07f-media-after-entry.tsx"></script></body></html>';
await writeFile(entryPath, entrySource, 'utf8');
await writeFile(htmlPath, htmlSource, 'utf8');

const server = spawn(process.platform === 'win32' ? 'npx.cmd' : 'npx', ['vite','--host','127.0.0.1','--port',String(PORT)], { cwd: FRONTEND_DIR, shell: true });
let serverLog='';
server.stdout.on('data',d=>serverLog+=d.toString());
server.stderr.on('data',d=>serverLog+=d.toString());

const waitForServer = async () => {
  const deadline=Date.now()+30000;
  while(Date.now()<deadline){
    try{ const r=await fetch(BASE_URL+'/ortho-studio-lot07f-media-after.html'); if(r.ok)return; }catch{}
    await new Promise(r=>setTimeout(r,250));
  }
  throw new Error('vite timeout');
};

const record = {
  schema_version:'ORTHO_MEDIA_RECORD_V1',patient_id:919,timepoint:'T0',
  photo_slots:[
    {slot_id:'EXTRA_FRONTAL_REPOSE',state:'FILLED',asset:{asset_id:101,mime_type:'image/png'}},
    {slot_id:'EXTRA_PROFILE',state:'FILLED',asset:{asset_id:102,mime_type:'image/png'}},
    {slot_id:'EXTRA_SMILE',state:'EMPTY',asset:null},
    {slot_id:'INTRA_FRONTAL',state:'FILLED',asset:{asset_id:103,mime_type:'image/png'}},
    {slot_id:'INTRA_RIGHT',state:'EMPTY',asset:null},
    {slot_id:'INTRA_LEFT',state:'EMPTY',asset:null},
    {slot_id:'INTRA_OCCLUSAL_MAXILLARY',state:'FILLED',asset:{asset_id:104,mime_type:'image/png'}},
    {slot_id:'INTRA_OCCLUSAL_MANDIBULAR',state:'EMPTY',asset:null},
  ],
  photo_complete:false,
  model_hooks:[
    {hook_id:'MAXILLARY_ARCH',accepted_formats:['STL','PLY','OBJ'],state:'VALIDATOR_NOT_IMPLEMENTED',measurement_authority:'NONE'},
    {hook_id:'MANDIBULAR_ARCH',accepted_formats:['STL','PLY','OBJ'],state:'VALIDATOR_NOT_IMPLEMENTED',measurement_authority:'NONE'},
    {hook_id:'OCCLUSION_RELATION',accepted_formats:['STL','PLY','OBJ'],state:'VALIDATOR_NOT_IMPLEMENTED',measurement_authority:'NONE'},
  ],
};

const tinyPng = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl0sAAAAASUVORK5CYII=','base64');
const reports=[];
try{
 await waitForServer();
 for(const phase of phases){
  const out=path.join(FRONTEND_DIR,phase.dir); await rm(out,{recursive:true,force:true}); await mkdir(out,{recursive:true});
  for(const vp of viewports){
   const browser=await chromium.launch({headless:true}); const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
   const page=await context.newPage(); const errors=[]; const blocked=[];
   page.on('pageerror',e=>errors.push(String(e)));
   page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
   await page.route('**/*',async route=>{
     const u=route.request().url();
     if(u.includes('/api/patients/919/ortho-media-record')){
       return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(record)});
     }
     if(u.includes('/api/patients/919/assets/') && u.endsWith('/content')){
       return route.fulfill({status:200,contentType:'image/png',body:tinyPng});
     }
     if(u.startsWith(BASE_URL)) return route.continue();
     blocked.push(u); return route.abort();
   });
   const response=await page.goto(BASE_URL+'/ortho-studio-lot07f-media-after.html',{waitUntil:'domcontentloaded'});
   if(phase.text200) await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
   await page.waitForSelector('[data-testid="ortho-media-record"]');
   await page.waitForTimeout(250);
   const metrics=await page.evaluate(()=>{
     const el=document.querySelector('[data-testid="ortho-media-record"]');
     const rect=el?.getBoundingClientRect();
     const body=document.body.getBoundingClientRect();
     return {
       photoSlots:document.querySelectorAll('[data-ortho-photo-slot]').length,
       modelHooks:document.querySelectorAll('[data-ortho-model-hook]').length,
       horizontalOverflow:document.documentElement.scrollWidth>document.documentElement.clientWidth,
       panelRight:rect?.right??null,viewport:window.innerWidth,bodyWidth:body.width,
     };
   });
   await page.screenshot({path:path.join(out,'after-media-'+vp.name+'.png'),fullPage:true});
   reports.push({phase:phase.name,viewport:vp.name,status:response?.status(),errors,blocked,metrics,valid:response?.status()===200&&errors.length===0&&blocked.length===0&&metrics.photoSlots===8&&metrics.modelHooks===3&&!metrics.horizontalOverflow});
   await context.close(); await browser.close();
  }
  await writeFile(path.join(out,'report.json'),JSON.stringify({productHead:PRODUCT_HEAD,phase:phase.name,reports:reports.filter(r=>r.phase===phase.name)},null,2),'utf8');
 }
} finally {
 if(!server.killed)server.kill('SIGTERM');
 await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{});
 await writeFile(path.join(FRONTEND_DIR,'lot07f-media-vite.log'),serverLog,'utf8');
}
console.log(JSON.stringify(reports,null,2));
if(reports.some(r=>!r.valid))process.exitCode=1;
