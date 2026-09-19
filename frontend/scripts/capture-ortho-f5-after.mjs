import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'ortho-f5-after-artifacts');
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
import { OrthoLongitudinalComparePanel } from './features/ortho/OrthoLongitudinalComparePanel';
import { PatientJourney } from './features/patients/components/PatientJourney';
import './index.css';

const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={client}>
    <MemoryRouter initialEntries={['/patients/915?tab=tracking']}>
      <main style={{maxWidth:'1200px', margin:'0 auto', padding:'24px 16px'}}>
        <div style={{display:'grid',gap:'24px'}}>
          <OrthoLongitudinalComparePanel patientId={915} />
          <PatientJourney patientId={915} />
        </div>
      </main>
    </MemoryRouter>
  </QueryClientProvider>
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Ortho F5 AFTER</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/ortho-f5-after-entry.tsx"></script></body></html>`;

const journey = {
  patient_id:915, window_months:12, truncated:false, total_events_available:3,
  summary:{active_plan_steps:1,total_plan_steps:4,remaining_due:0,has_billing_data:false,next_appointment:'2026-10-12T10:00:00',last_document_date:null},
  events:[
    {event_key:'cephalo_analysis:31',source:'cephalo_analysis',type:'cephalometrie',ref_id:31,date:'2026-09-18T10:00:00',title:'Analyse céphalométrique',status:'CALIBRE',phase_hint:'radio',navigation_target:'RADIOLOGY_TAB',related_event_key:null},
    {event_key:'appointment:40',source:'appointment',type:'consultation',ref_id:40,date:'2026-02-12T10:00:00',title:'Consultation orthodontique',status:'TERMINE',phase_hint:'consultation',navigation_target:'INLINE',related_event_key:null},
  ],
};
const orthoCase = {id:12,patient_id:915,lifecycle_status:'ACTIVE',current_phase_key:'ALIGNEMENT'};
const timepoints = [
  {id:10,ortho_case_id:12,patient_id:915,ordinal:0,occurred_at:'2026-03-18T10:00:00',note:'Initial',created_by:1,created_at:'2026-03-18T10:00:00',evidences:[{id:1,clinical_asset_id:71,cephalo_analysis_id:null,panoramic_analysis_id:null,created_by:1,created_at:'2026-03-18T10:00:00'}]},
  {id:11,ortho_case_id:12,patient_id:915,ordinal:1,occurred_at:'2026-09-18T10:00:00',note:'Contrôle',created_by:1,created_at:'2026-09-18T10:00:00',evidences:[{id:2,clinical_asset_id:null,cephalo_analysis_id:32,panoramic_analysis_id:null,created_by:1,created_at:'2026-09-18T10:00:00'}]},
];
const comparison = {
  patient_id:915, ortho_case_id:12,
  from_timepoint:{id:10,ordinal:0,occurred_at:'2026-03-18T10:00:00',note:'Initial',evidences:[
    {kind:'CLINICAL_ASSET',ref_id:71,recorded_at:'2026-03-18T10:00:00',label:'PHOTO'},
    {kind:'CEPHALO',ref_id:31,recorded_at:'2026-03-18T10:00:00',label:'Céphalométrie calibrée'},
  ]},
  to_timepoint:{id:11,ordinal:1,occurred_at:'2026-09-18T10:00:00',note:'Contrôle',evidences:[
    {kind:'CLINICAL_ASSET',ref_id:72,recorded_at:'2026-09-18T10:00:00',label:'PHOTO'},
    {kind:'CEPHALO',ref_id:32,recorded_at:'2026-09-18T10:00:00',label:'Céphalométrie calibrée'},
  ]},
  measurements:[
    {key:'SNA',label:'SNA',unit:'deg',from_value:82,to_value:83.2,delta:1.2},
    {key:'SNB',label:'SNB',unit:'deg',from_value:80,to_value:79.5,delta:-0.5},
    {key:'Surplomb',label:'Surplomb',unit:'mm',from_value:4,to_value:2.5,delta:-1.5},
  ],
  measurement_status:'AVAILABLE',
  interpretation_policy:'NUMERIC_ONLY_CLINICIAN_INTERPRETATION',
};
const f5Context = {
  patient_id:915, ortho_case_id:12,
  from_source:{timepoint_id:10,timepoint_ordinal:0,occurred_at:'2026-03-18T10:00:00',cephalo_analysis_id:31,is_calibrated:true,mm_per_pixel:0.1},
  to_source:{timepoint_id:11,timepoint_ordinal:1,occurred_at:'2026-09-18T10:00:00',cephalo_analysis_id:32,is_calibrated:true,mm_per_pixel:0.1},
  quantitative_mm_allowed:true,
  applicability_status:'ADULT_ENGINEERING_SCOPE_ONLY',
  method_id:'ACB_STRUCTURAL_FEATURE_SIMILARITY',
  method_version:'1',
  quality_status:'ENGINE_ESTIMATE_ONLY',
  clinically_validated:false,
};
const analysis31 = {id:31,image_original_path:'api/static/uploads/radios/f5-t0.svg',angles_data:{},landmarks_data:{},is_calibrated:true,mm_per_pixel:0.1,created_at:'2026-03-18T10:00:00'};
const analysis32 = {id:32,image_original_path:'api/static/uploads/radios/f5-t1.svg',angles_data:{},landmarks_data:{},is_calibrated:true,mm_per_pixel:0.1,created_at:'2026-09-18T10:00:00'};
const f5Estimate = {
  context:f5Context,
  registration:{
    method_id:'ACB_STRUCTURAL_FEATURE_SIMILARITY',method_version:'1',quality_status:'ENGINE_ESTIMATE_ONLY',clinically_validated:false,
    transform_direction:'moving_to_reference',matrix:[[0.9994,0.0349,-7.2],[-0.0349,0.9994,5.4]],
    rotation_degrees:-2,uniform_scale:1,translation_px:{x:-7.2,y:5.4},good_match_count:42,inlier_count:35,
    reference_roi:{x:225,y:105,width:300,height:190},moving_roi:{x:230,y:110,width:295,height:185},
    reference_size_px:{width:800,height:600},moving_size_px:{width:800,height:600},
    algorithm:{feature:'SIFT',matcher:'BFMatcher_L2_KNN',ratio_test:0.7}
  }
};
const cephSvg = (shift=0) => `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<rect width="800" height="600" fill="#0f172a"/>
<g transform="translate(${shift} 0)" fill="none" stroke="#cbd5e1" stroke-width="4">
<ellipse cx="390" cy="270" rx="205" ry="220"/>
<path d="M275 155 Q360 95 470 135 Q560 180 570 280 Q552 390 472 448 Q365 500 282 418 Q225 330 242 230 Q248 190 275 155"/>
<path d="M255 215 Q330 200 400 222 Q465 240 522 220"/>
<path d="M320 305 Q382 278 455 302"/>
<path d="M335 360 Q398 342 460 372"/>
</g>
<g fill="#94a3b8">
<circle cx="${350+shift}" cy="180" r="5"/><circle cx="${470+shift}" cy="190" r="5"/><circle cx="${420+shift}" cy="235" r="5"/>
<circle cx="${300+shift}" cy="270" r="5"/><circle cx="${505+shift}" cy="310" r="5"/>
</g></svg>`;

function json(body,status=200){return {status,contentType:'application/json',body:JSON.stringify(body)};}
async function waitForServer(url,timeoutMs=30000){const s=Date.now();while(Date.now()-s<timeoutMs){try{const r=await fetch(url);if(r.ok)return;}catch{}await new Promise(x=>setTimeout(x,250));}throw new Error('Vite unavailable');}

await rm(OUTPUT_DIR,{recursive:true,force:true});
await mkdir(OUTPUT_DIR,{recursive:true});
await writeFile(path.join(FRONTEND_DIR,'src','ortho-f5-after-entry.tsx'),entrySource,'utf8');
await writeFile(path.join(FRONTEND_DIR,'ortho-f5-after.html'),htmlSource,'utf8');

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
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-case')return route.fulfill(json(orthoCase));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-case/12/timepoints')return route.fulfill(json(timepoints));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-case/12/compare')return route.fulfill(json(comparison));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/journey')return route.fulfill(json(journey));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/ortho-case/12/superimposition/context')return route.fulfill(json(f5Context));
      if(req.method()==='POST'&&url.pathname==='/api/patients/915/ortho-case/12/superimposition/estimate')return route.fulfill(json(f5Estimate));
      if(req.method()==='GET'&&url.pathname==='/api/ia/analyses/31')return route.fulfill(json(analysis31));
      if(req.method()==='GET'&&url.pathname==='/api/ia/analyses/32')return route.fulfill(json(analysis32));
      if(req.method()==='GET'&&url.pathname==='/api/static/uploads/radios/f5-t0.svg')return route.fulfill({status:200,contentType:'image/svg+xml',body:cephSvg(0)});
      if(req.method()==='GET'&&url.pathname==='/api/static/uploads/radios/f5-t1.svg')return route.fulfill({status:200,contentType:'image/svg+xml',body:cephSvg(8)});
      if(req.method()==='GET'&&url.pathname==='/api/actes/patient/915')return route.fulfill(json([]));
      if(req.method()==='GET'&&url.pathname==='/api/patients/915/documents')return route.fulfill(json([]));
      return route.fulfill(json({detail:'neutralized'},418));
    }
    if(url.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:'/* offline */'});
    blockedExternalRequests.push({viewport:viewport.name,url:req.url(),method:req.method()}); return route.abort('blockedbyclient');
  });
  try{
    await waitForServer(`${BASE_URL}/ortho-f5-after.html`);
    const response=await page.goto(`${BASE_URL}/ortho-f5-after.html`,{waitUntil:'domcontentloaded',timeout:30000});
    await page.locator('[data-ortho-f3-compare]').waitFor({state:'visible',timeout:30000});
    await page.getByText(/Variation numérique/i).waitFor({state:'visible',timeout:30000});
    await page.getByRole('button',{name:/Superposition scientifique/i}).click();
    await page.locator('[data-ortho-f5-viewer]').waitFor({state:'visible',timeout:30000});
    const drawRoi = async (selector) => {
      const box = await page.locator(selector).boundingBox();
      if(!box) throw new Error('Missing ROI box '+selector);
      await page.mouse.move(box.x + box.width*0.28, box.y + box.height*0.24);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width*0.70, box.y + box.height*0.63,{steps:8});
      await page.mouse.up();
    };
    await drawRoi('[data-f5-roi="from"]');
    await drawRoi('[data-f5-roi="to"]');
    await page.getByRole('button',{name:/Calculer la superposition/i}).click();
    await page.locator('[data-f5-overlay-canvas]').waitFor({state:'visible',timeout:30000});
    const metrics=await page.evaluate(()=>{
      const text=(document.body.textContent||'').toLowerCase(); const doc=document.documentElement;
      return {
        innerWidth,scrollWidth:Math.max(doc.scrollWidth,document.body.scrollWidth),
        horizontalOverflow:Math.max(doc.scrollWidth,document.body.scrollWidth)>innerWidth+1,
        hasCompareSurface:Boolean(document.querySelector('[data-ortho-f3-compare]')),
        hasT0:text.includes('t0'),hasT1:text.includes('t1'),
        hasEvidence:text.includes('céphalométrie calibrée')&&text.includes('photo'),
        hasNumericCaption:text.includes('variation numérique')&&text.includes('interprétation clinique par le praticien'),
        hasDelta:text.includes('+1,2 deg')||text.includes('+1.2 deg'),
        hasF5Viewer:Boolean(document.querySelector('[data-ortho-f5-viewer]')),
        hasF5Canvas:Boolean(document.querySelector('[data-f5-overlay-canvas]')),
        hasEngineeringStatus:text.includes('engine_estimate_only')&&text.includes('validation clinique non établie'),
        forbidden:['amélior','aggrav','succès thérapeutique','echec thérapeutique','échec thérapeutique','worsen','improv'].filter(k=>text.includes(k)),
      };
    });
    const valid=response?.status()===200&&!metrics.horizontalOverflow&&metrics.hasCompareSurface&&metrics.hasT0&&metrics.hasT1&&metrics.hasEvidence&&metrics.hasNumericCaption&&metrics.hasDelta&&metrics.hasF5Viewer&&metrics.hasF5Canvas&&metrics.hasEngineeringStatus&&metrics.forbidden.length===0&&consoleErrors.length===0&&pageErrors.length===0;
    await page.screenshot({path:path.join(OUTPUT_DIR,`after-superimposition-${viewport.name}.png`),fullPage:true});
    captures.push({viewport:viewport.name,httpStatus:response?.status()??null,metrics,consoleErrors,pageErrors,valid});
  }catch(error){
    captures.push({viewport:viewport.name,httpStatus:null,metrics:null,consoleErrors,pageErrors:[...pageErrors,error instanceof Error?error.message:String(error)],valid:false});
  }finally{await context.close().catch(()=>{});await browser.close().catch(()=>{});}
}
if(!server.killed)server.kill('SIGTERM'); await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{});
await writeFile(path.join(OUTPUT_DIR,'vite.log'),serverLog,'utf8');
const invalid=captures.filter(c=>!c.valid);
const report={lot:'V1-05-F5',phase:'AFTER',productHead:PRODUCT_HEAD,viewports:viewports.map(v=>v.name),captures,blockedExternalRequests,invalidCount:invalid.length};
await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8');
console.log(JSON.stringify(report,null,2));
if(invalid.length||blockedExternalRequests.length)process.exitCode=1;
