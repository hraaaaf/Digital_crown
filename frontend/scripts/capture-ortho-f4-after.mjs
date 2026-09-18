import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'ortho-f4-after-artifacts');
const PORT = 5199;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { OrthoCockpitPanel } from './features/ortho/OrthoCockpitPanel';
import { OrthoLongitudinalComparePanel } from './features/ortho/OrthoLongitudinalComparePanel';
import { PatientJourney } from './features/patients/components/PatientJourney';
import './index.css';

const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={client}>
    <MemoryRouter initialEntries={['/patients/915?tab=tracking']}>
      <main style={{maxWidth:'1200px', margin:'0 auto', padding:'24px 16px'}}>
        <div style={{display:'grid',gap:'24px'}}>
          <OrthoCockpitPanel patientId={915} />
          <OrthoLongitudinalComparePanel patientId={915} />
          <PatientJourney patientId={915} />
        </div>
      </main>
    </MemoryRouter>
  </QueryClientProvider>
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Ortho F4 AFTER</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/ortho-f4-after-entry.tsx"></script></body></html>`;

const cockpit = {
  patient_id:915,
  case:{case_id:12,started_at:'2026-03-18T10:00:00',lifecycle_status:'ACTIVE',current_phase_key:'ALIGNEMENT',closed_at:null,controls_count:4},
  latest_control:{id:21,occurred_at:'2026-09-18T09:00:00',phase_key:'ALIGNEMENT',notable_event:'Bracket 12 recollé.',next_planned_step:"Contrôle de l'alignement antérieur.",next_control_at:'2026-10-12T10:00:00',appointment_id:null},
  next_appointment:{id:50,datetime_start:'2026-10-14T10:00:00',status:'PRÉVU',motif:'Contrôle orthodontique'},
  latest_timepoint:{id:11,ordinal:1,occurred_at:'2026-09-18T10:00:00',note:'Contrôle',evidence_count:2},
  latest_cephalo:{kind:'CEPHALO',ref_id:32,recorded_at:'2026-09-18T10:00:00',label:'Céphalométrie calibrée',timepoint_ordinal:1},
  latest_panoramic:{kind:'PANORAMIC',ref_id:41,recorded_at:'2026-09-18T10:00:00',label:'Panoramique',timepoint_ordinal:1},
  latest_clinical_asset:{kind:'CLINICAL_ASSET',ref_id:72,recorded_at:'2026-09-18T10:00:00',label:'PHOTO',timepoint_ordinal:1},
  attention:['NEXT_PLANNED_STEP_PRESENT'],
};
const journey = {
  patient_id:915, window_months:12, truncated:false, total_events_available:3,
  summary:{active_plan_steps:1,total_plan_steps:4,remaining_due:0,has_billing_data:false,next_appointment:'2026-10-14T10:00:00',last_document_date:null},
  events:[
    {event_key:'ortho_control:21',source:'ortho_control',type:'CONTROLE',ref_id:21,date:'2026-09-18T09:00:00',title:'Contrôle orthodontique — Alignement',status:'ENREGISTRE',phase_hint:'alignement',navigation_target:'INLINE',related_event_key:null},
    {event_key:'cephalo_analysis:31',source:'cephalo_analysis',type:'cephalometrie',ref_id:31,date:'2026-09-18T10:00:00',title:'Analyse céphalométrique',status:'CALIBRE',phase_hint:'radio',navigation_target:'RADIOLOGY_TAB',related_event_key:null},
  ],
};
const orthoCase = {id:12,patient_id:915,lifecycle_status:'ACTIVE',current_phase_key:'ALIGNEMENT'};
const timepoints = [
  {id:10,ortho_case_id:12,patient_id:915,ordinal:0,occurred_at:'2026-03-18T10:00:00',note:'Initial',created_by:1,created_at:'2026-03-18T10:00:00',evidences:[{id:1,clinical_asset_id:71,cephalo_analysis_id:null,panoramic_analysis_id:null,created_by:1,created_at:'2026-03-18T10:00:00'}]},
  {id:11,ortho_case_id:12,patient_id:915,ordinal:1,occurred_at:'2026-09-18T10:00:00',note:'Contrôle',created_by:1,created_at:'2026-09-18T10:00:00',evidences:[{id:2,clinical_asset_id:null,cephalo_analysis_id:32,panoramic_analysis_id:null,created_by:1,created_at:'2026-09-18T10:00:00'}]},
];
const comparison = {
  patient_id:915, ortho_case_id:12,
  from_timepoint:{id:10,ordinal:0,occurred_at:'2026-03-18T10:00:00',note:'Initial',evidences:[{kind:'CLINICAL_ASSET',ref_id:71,recorded_at:'2026-03-18T10:00:00',label:'PHOTO'},{kind:'CEPHALO',ref_id:31,recorded_at:'2026-03-18T10:00:00',label:'Céphalométrie calibrée'}]},
  to_timepoint:{id:11,ordinal:1,occurred_at:'2026-09-18T10:00:00',note:'Contrôle',evidences:[{kind:'CEPHALO',ref_id:32,recorded_at:'2026-09-18T10:00:00',label:'Céphalométrie calibrée'}]},
  measurements:[{key:'SNA',label:'SNA',unit:'deg',from_value:82,to_value:83.2,delta:1.2}],
  measurement_status:'AVAILABLE', interpretation_policy:'NUMERIC_ONLY_CLINICIAN_INTERPRETATION',
};

function json(body,status=200){return {status,contentType:'application/json',body:JSON.stringify(body)};}
async function waitForServer(url,timeoutMs=30000){const s=Date.now();while(Date.now()-s<timeoutMs){try{const r=await fetch(url);if(r.ok)return;}catch{}await new Promise(x=>setTimeout(x,250));}throw new Error('Vite unavailable');}

await rm(OUTPUT_DIR,{recursive:true,force:true});
await mkdir(OUTPUT_DIR,{recursive:true});
await writeFile(path.join(FRONTEND_DIR,'src','ortho-f4-after-entry.tsx'),entrySource,'utf8');
await writeFile(path.join(FRONTEND_DIR,'ortho-f4-after.html'),htmlSource,'utf8');

const viteBin=path.join(FRONTEND_DIR,'node_modules','.bin',process.platform==='win32'?'vite.cmd':'vite');
const server=spawn(viteBin,['--host','127.0.0.1','--port',String(PORT)],{cwd:FRONTEND_DIR,env:{...process.env,BROWSER:'none',VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']});
let serverLog=''; server.stdout.on('data',x=>serverLog+=x.toString()); server.stderr.on('data',x=>serverLog+=x.toString());
const captures=[]; const blockedExternalRequests=[];

for(const viewport of viewports){
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},reducedMotion:'reduce',locale:'fr-FR'});
  const page=await context.newPage(); const consoleErrors=[]; const pageErrors=[];
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())}); page.on('pageerror',e=>pageErrors.push(e.message));
  await page.route('**/*',async route=>{
    const req=route.request(); const url=new URL(req.url());
    if(url.hostname==='127.0.0.1'&&url.port===String(PORT))return route.continue();
    if(url.hostname==='127.0.0.1'&&url.port==='8005'){
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-cockpit')return route.fulfill(json(cockpit));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-case')return route.fulfill(json(orthoCase));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-case/12/timepoints')return route.fulfill(json(timepoints));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-case/12/compare')return route.fulfill(json(comparison));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/journey')return route.fulfill(json(journey));
      if(req.method()==='GET'&&url.pathname==='/api/actes/patient/915')return route.fulfill(json([]));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/documents')return route.fulfill(json([]));
      return route.fulfill(json({detail:'neutralized'},418));
    }
    if(url.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:'/* offline */'});
    blockedExternalRequests.push({viewport:viewport.name,url:req.url(),method:req.method()}); return route.abort('blockedbyclient');
  });
  try{
    await waitForServer(`${BASE_URL}/ortho-f4-after.html`);
    const response=await page.goto(`${BASE_URL}/ortho-f4-after.html`,{waitUntil:'domcontentloaded',timeout:30000});
    await page.locator('[data-ortho-f4-cockpit]').waitFor({state:'visible',timeout:30000});
    await page.getByText('RDV réel').waitFor({state:'visible',timeout:30000});
    const metrics=await page.evaluate(()=>{
      const text=(document.body.textContent||'').toLowerCase(); const doc=document.documentElement;
      const cockpit=document.querySelector('[data-ortho-f4-cockpit]');
      const compare=document.querySelector('[data-ortho-f3-compare]');
      return {
        innerWidth,scrollWidth:Math.max(doc.scrollWidth,document.body.scrollWidth),
        horizontalOverflow:Math.max(doc.scrollWidth,document.body.scrollWidth)>innerWidth+1,
        hasF4:Boolean(cockpit),hasF3:Boolean(compare),
        f4BeforeF3:Boolean(cockpit&&compare&&(cockpit.compareDocumentPosition(compare)&Node.DOCUMENT_POSITION_FOLLOWING)),
        hasPlannedControl:text.includes('contrôle prévu'),
        hasRealAppointment:text.includes('rdv réel'),
        hasEvidence:text.includes('céphalométrie calibrée')&&text.includes('panoramique')&&text.includes('photo'),
        forbidden:['score de progression','succès thérapeutique','échec thérapeutique','amélioration automatique','aggravation automatique'].filter(k=>text.includes(k)),
      };
    });
    const valid=response?.status()===200&&!metrics.horizontalOverflow&&metrics.hasF4&&metrics.hasF3&&metrics.f4BeforeF3&&metrics.hasPlannedControl&&metrics.hasRealAppointment&&metrics.hasEvidence&&metrics.forbidden.length===0&&consoleErrors.length===0&&pageErrors.length===0;
    await page.screenshot({path:path.join(OUTPUT_DIR,`after-overview-${viewport.name}.png`),fullPage:true});
    captures.push({viewport:viewport.name,httpStatus:response?.status()??null,metrics,consoleErrors,pageErrors,valid});
  }catch(error){
    captures.push({viewport:viewport.name,httpStatus:null,metrics:null,consoleErrors,pageErrors:[...pageErrors,error instanceof Error?error.message:String(error)],valid:false});
  }finally{await context.close().catch(()=>{});await browser.close().catch(()=>{});}
}
if(!server.killed)server.kill('SIGTERM'); await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{});
await writeFile(path.join(OUTPUT_DIR,'vite.log'),serverLog,'utf8');
const invalid=captures.filter(c=>!c.valid);
const report={lot:'V1-05-F4',phase:'AFTER',productHead:PRODUCT_HEAD,viewports:viewports.map(v=>v.name),captures,blockedExternalRequests,invalidCount:invalid.length};
await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8');
console.log(JSON.stringify(report,null,2));
if(invalid.length||blockedExternalRequests.length)process.exitCode=1;
