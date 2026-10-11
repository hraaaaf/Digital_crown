#!/usr/bin/env node
// Source-locked research: actual React panel + real Zustand store in isolated
// Chromium. NO FACAD, clinical case, live API, or product code modification.
import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {existsSync} from 'node:fs';
import {mkdir,readFile,rm,writeFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const ROOT=path.resolve(import.meta.dirname,'../../..');
const FRONTEND=path.join(ROOT,'frontend');
const OUTPUT=process.env.FACAD_ANB_BROWSER_OUTPUT||path.join(os.tmpdir(),'facad-anb-workspace-http');
const PROOF_FILE=process.env.FACAD_ANB_SYNTHETIC_FIXTURES_PATH;
const ENTRY=path.join(FRONTEND,'src','facad-anb-workspace-http-entry.tsx');
const HTML=path.join(FRONTEND,'facad-anb-workspace-http.html');
const PORT=5278,API_PORT=5281,APP_URL='http://127.0.0.1:'+PORT+'/facad-anb-workspace-http.html';
const VIEWPORTS=[{name:'mobile',width:390,height:844},{name:'desktop',width:1280,height:900}];
if(!PROOF_FILE||!existsSync(PROOF_FILE))throw Error('Missing pinned Python oracle output');
const proof=JSON.parse(await readFile(PROOF_FILE,'utf8'));
const expected=new Set(['F1_STRADDLE','F1_MIRROR','F2_VERTICAL','F3_SAME_SIDE']);
if(proof.schema!=='FACAD_F01_13_ANB_SOURCE_PINNED_RUNTIME_BOUNDARY_RESEARCH_V1'
 ||proof.tested_facad_numeric_runtime!==false||proof.fac03_d3!=='OPEN_RED'||proof.f01_13!=='OPEN'
 ||proof.source_route_assertions?.length!==8||Object.keys(proof.git_blob_source_pins||{}).length!==6
 ||proof.synthetic_cases?.length!==4||proof.synthetic_cases.some(x=>!expected.has(x.fixture)||x.facad_vendor_numeric_output!==null))
 throw Error('Source-oracle contract is not trusted');
const cases=proof.synthetic_cases.map(x=>({id:x.fixture,
 legacy:x.pinned_dc_typed_legacy_parity_deg,
 unsignedHypothesis:x.independent_unsigned_vertex_at_n_hypothesis_deg}));
if(cases.some(x=>!Number.isFinite(x.legacy)||!Number.isFinite(x.unsignedHypothesis)))throw Error('Nonfinite synthetic oracle');

const entry=[
 "import React from 'react';",
 "import {createRoot} from 'react-dom/client';",
 "import {CephaloWorkspace} from './features/ortho/CephaloWorkspace';",
 "import {MemoryRouter} from 'react-router-dom';",
 "import {useOrthoStore} from './features/ortho/stores/useOrthoStore';",
 "import './index.css';",
 "const cases=FIXTURE_CASES;",
 "const P={bg:'#111827',bgPanel:'#172033',bgCard:'#1e293b',bgInput:'#0f172a',border:'#475569',borderFocus:'#38bdf8',text:'#f8fafc',textMuted:'#cbd5e1',textDim:'#94a3b8',accent:'#38bdf8',accentSuccess:'#22c55e',accentWarning:'#f59e0b',accentError:'#f87171',shadow:'none',shadowLg:'none'};",
 "function dataFor(row,sourceMode){",
 " const v=row.legacy,canon=sourceMode==='divergent'?+(v+1).toFixed(1):v;",
 " const sr={canonical_measurement_id:'M_ANB_DEG_V1',label:'ANB',layer:'STEINER_1953_BASE',value:canon,unit:'°',availability_status:'AVAILABLE',measurement_refs:['synthetic:ANB'],value_authority_method_id:'STEINER_ANB_DEG_V1',historical_reference:null,reference_delta:null,reference_authority:'REFERENCE_DISPLAY_ONLY',classification_authority:false,interpretation_status:'REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION'};",
 " return {metrics:{analyse_osseuse:{ANB:{valeur:v,status:'N/A'}},analyse_dentaire:{},analyse_esthetique:{}},scientific_read_path:{authority:sourceMode==='invalid'?'LEGACY_ONLY':'EVIDENCE_GRAPH_V1',active_chain:sourceMode==='invalid'?'UNVERIFIED':'VERIFIED',canonical_measurements:[{canonical_measurement_id:'M_ANB_DEG_V1',value:canon,unit:'°',availability_status:'AVAILABLE',measurement_refs:['synthetic:ANB']}],protocol_profiles:{steiner:{protocol_profile_id:'STEINER_STATIC_PROTOCOL_PROFILE_V1',source_lock_gate:{gate:'ORTHO_ANALYSIS_PROTOCOLS_SOURCE_LOCKED',status:'SATISFIED'},final_gate:{gate:'ORTHO_ANALYSIS_PROTOCOLS_VERIFIED',status:'OPEN'},norm_set:{authority:'REFERENCE_DISPLAY_ONLY'},rows:[sr]}}}};",
 "}",
  "useOrthoStore.setState({patientId:918,patientName:'SYNTHETIC NO PATIENT',analysisId:null,imageSrc:'data:image/svg+xml;charset=utf-8,'+encodeURIComponent('<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1200\" height=\"1600\"><rect width=\"1200\" height=\"1600\" fill=\"#0f172a\"/><text x=\"220\" y=\"600\" fill=\"#64748b\" font-size=\"55\">SYNTHETIC NO PATIENT</text></svg>'),imgDim:{w:1200,h:1600},mmPerPixel:0.2,isCalibrated:true,step:1,completedSteps:new Set([1]),anglesData:dataFor(cases[0],'valid'),local:{...useOrthoStore.getState().local,landmarks:[],version:1}});",
 "function App(){",
 " const [index,setIndex]=React.useState(0); const [scenario,setScenario]=React.useState('valid');",
 " function swap(i,s){useOrthoStore.setState({anglesData:dataFor(cases[i],s)});setIndex(i);setScenario(s)}",
 " return <main style={{width:'100%',height:'100vh',boxSizing:'border-box',padding:16,background:P.bg,color:P.text}}>",
 "  <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:10}}><span data-testid='workspace-route'>Digital Crown Workspace / synthetic HTTP stub / no patient</span></div>",
 "  <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:8}}>{cases.map((c,i)=><button key={c.id} data-testid={'fixture-'+c.id} onClick={()=>swap(i,'valid')}>{c.id}</button>)}</div>",
 "  <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:12}}><button data-testid='source-valid' onClick={()=>swap(index,'valid')}>Source valide</button><button data-testid='source-invalid' onClick={()=>swap(index,'invalid')}>Source non vérifiée</button><button data-testid='source-divergent' onClick={()=>swap(index,'divergent')}>Divergence injectée</button></div>",
 "  <div data-testid='fixture-id'>{cases[index].id}</div><div data-testid='fixture-mode'>{scenario}</div>",
 "  <div style={{height:1120,minHeight:900,width:'100%',maxWidth:1500}}><MemoryRouter initialEntries={['/patients/918/cephalo']}><div style={{height:'100%'}}><CephaloWorkspace patientId={918} patientName='Synthetic Fixture — no real patient'/></div></MemoryRouter></div>",
 " </main>",
 "}",
 "createRoot(document.getElementById('root')).render(<App/>);"
].join('\n').replace('FIXTURE_CASES',JSON.stringify(cases));
const html='<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body style="margin:0"><div id="root"></div><script type="module" src="/src/facad-anb-workspace-http-entry.tsx"></script></body></html>';
if(!APP_URL.endsWith(path.basename(HTML))||!html.includes('/src/'+path.basename(ENTRY)))throw Error('Fixture entry and URL mismatch');
if(existsSync(ENTRY)||existsSync(HTML))throw Error('Fixture collision: refuse overwrite');
await mkdir(OUTPUT,{recursive:true});
let server,browser,stub,viteLog='';
const httpObserved=[];
const captures=[],traces=[],networkBlocked=[],occlusionObservations=[],detectorControls=[],navigationChecks=[];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function waitVite(){
 for(let i=0;i<120;i++){
  if(server?.exitCode!==null&&server?.exitCode!==undefined)throw Error('Vite failed early');
  try{if((await fetch(APP_URL)).ok)return}catch{}
  await sleep(250);
 }
 throw Error('Vite did not start');
}
function displayed(cell){
 const m=cell.match(/([−-]?\d+,\d)\s*°/);
 if(!m)throw Error('Missing degree value in actual UI: '+cell);
 return Number(m[1].replace('−','-').replace(',','.'));
}
async function rowText(page,key){
 const row=page.locator('[data-r19-metric="'+key+'"]');
 await row.waitFor({state:'visible',timeout:20000});
 return await row.locator('td').nth(1).innerText();
}
async function mode(page,key){
 await page.locator('[data-analysis="'+key+'"]').click();
 await page.locator('[data-r19-analysis-panel="'+key+'"]').waitFor({state:'visible'});
}

// Hit-test the actual numeric cell: DOM visibility or a valid bounding box
// cannot prove that a fixed button is not painted on top of the ANB value.
async function inspectNumericCellOcclusion(page,key){
 const row=page.locator('[data-r19-metric="'+key+'"]');
 const cell=row.locator('td').nth(1);
 await cell.scrollIntoViewIfNeeded({timeout:10000});
 return cell.evaluate(el=>{
  const r=el.getBoundingClientRect();
  const factors=[0.15,0.35,0.5,0.65,0.85];
  const samples=[];
  for(const fx of factors)for(const fy of factors){
   const x=r.left+r.width*fx,y=r.top+r.height*fy;
   if(x<0||y<0||x>=innerWidth||y>=innerHeight){
    samples.push({fx,fy,inViewport:false,blocked:true,reason:'OUTSIDE_VIEWPORT'});
    continue;
   }
   const hit=document.elementFromPoint(x,y);
   const clear=Boolean(hit && (hit===el||el.contains(hit)));
   samples.push({fx,fy,inViewport:true,blocked:!clear,
    hitTag:hit?.tagName??null,
    hitLabel:(hit?.textContent||'').trim().slice(0,65)});
  }
  return {cellRect:{x:r.x,y:r.y,width:r.width,height:r.height},
    cellText:(el.textContent||'').trim().slice(0,80),
    inViewportSamples:samples.filter(z=>z.inViewport).length,
    obstructionSamples:samples.filter(z=>z.blocked).length,
    blockedByOtherElement:samples.some(z=>z.blocked&&z.inViewport),samples};
 });
}

async function assertDetectorRejectsInjectedOverlay(page,key){
 const cell=page.locator('[data-r19-metric="'+key+'"] td').nth(1);
 await cell.scrollIntoViewIfNeeded({timeout:10000});
 await cell.evaluate(el=>{
  const r=el.getBoundingClientRect();
  const blocker=document.createElement('button');
  blocker.type='button';blocker.dataset.anbHitTestSentinel='overlay';
  blocker.textContent='Synthetic occlusion sentinel';
  Object.assign(blocker.style,{position:'fixed',zIndex:'2147483600',
   left:(r.left+r.width*0.22)+'px',top:(r.top+r.height*0.20)+'px',
   width:(r.width*0.56)+'px',height:(r.height*0.6)+'px'});
  document.body.appendChild(blocker);
 });
 try {
  const probe=await inspectNumericCellOcclusion(page,key);
  if(!probe.blockedByOtherElement)throw Error('NEGATIVE CONTROL FAILED: detector misses synthetic overlay');
  return {detector_negative_control:'REJECTED_INJECTED_OVERLAY',blocked_samples:probe.obstructionSamples};
 } finally {
  await page.evaluate(()=>document.querySelector('[data-anb-hit-test-sentinel]')?.remove());
 }
}

try{
 stub=createServer((req,res)=>{
  const url=new URL(req.url||'/', 'http://127.0.0.1:'+API_PORT);
  const method=req.method||'UNKNOWN';
  httpObserved.push({method,path:url.pathname,query:url.search});
  res.setHeader('Access-Control-Allow-Origin','http://127.0.0.1:'+PORT);
  res.setHeader('Access-Control-Allow-Credentials','true');
  res.setHeader('Access-Control-Allow-Headers','Authorization,Content-Type');
  res.setHeader('Access-Control-Allow-Methods','GET,OPTIONS');
  res.setHeader('Cache-Control','no-store');
  res.setHeader('Content-Type','application/json');
  if(method==='OPTIONS'){res.statusCode=204;res.end();return}
  if(method==='GET' && url.pathname==='/api/patients/918'){
   res.statusCode=200;res.end(JSON.stringify({id:918,age:34,sexe:'M',synthetic_fixture:true}));return;
  }
  res.statusCode=405;res.end(JSON.stringify({detail:'STRICT_SYNTHETIC_STUB_DENY'}));
 });
 await new Promise((resolve,reject)=>{stub.once('error',reject);stub.listen(API_PORT,'127.0.0.1',resolve)});
 await writeFile(ENTRY,entry);
 await writeFile(HTML,html);
 const vitePath=path.join(FRONTEND,'node_modules','vite','bin','vite.js');
 if(!existsSync(vitePath))throw Error('npm ci must run before browser probe');
 server=spawn(process.execPath,[vitePath,'--host','127.0.0.1','--port',String(PORT),'--strictPort'],{cwd:FRONTEND,env:{...process.env,VITE_ENABLE_HTTPS:'false',VITE_API_URL:'http://127.0.0.1:'+API_PORT},stdio:['ignore','pipe','pipe']});
 server.stdout.on('data',x=>{viteLog+=x});
 server.stderr.on('data',x=>{viteLog+=x});
 await waitVite();
 browser=await chromium.launch({headless:true});
 for(const v of VIEWPORTS){
  const ctx=await browser.newContext({viewport:{width:v.width,height:v.height},locale:'fr-FR',reducedMotion:'reduce',serviceWorkers:'block'});
  const page=await ctx.newPage();const errors=[];
  page.on('pageerror',err=>errors.push(err.message));
  await page.route('**/*',route=>{
   const u=new URL(route.request().url());
   if(u.hostname==='127.0.0.1'&&(Number(u.port)===PORT||Number(u.port)===API_PORT))return route.continue();
   networkBlocked.push(u.origin);return route.abort('blockedbyclient');
  });
  try{
   await page.goto(APP_URL,{waitUntil:'domcontentloaded',timeout:45000});
   try {
    await page.locator('[data-r19-analysis-panel="all"]').waitFor({state:'visible',timeout:12000});
   } catch(err) {
    const body=(await page.locator('body').innerText().catch(()=>''))?.slice(0,1800);
    const details={url:page.url(),body,errors,httpObserved,blockedOrigins:networkBlocked,viteLog:viteLog.slice(-1200)};
    console.error('F01_13_WORKSPACE_RENDER_DIAGNOSTIC='+JSON.stringify(details));
    await page.screenshot({path:path.join(OUTPUT,v.name+'-startup-failure.png'),fullPage:false}).catch(()=>{});
    throw err;
   }
   const mobileNav=page.locator('[data-ortho-mobile-next-step] button');
   const footerNav=page.locator('[data-ortho-next-step-footer]');
   const mobileShown=await mobileNav.isVisible();
   const footerShown=await footerNav.isVisible();
   if(v.name==='mobile' && (!mobileShown || footerShown))throw Error('Mobile step-1 navigation duplicated or hidden');
   if(v.name==='desktop' && (mobileShown || !footerShown))throw Error('Desktop step-1 footer navigation unexpectedly moved');
   if(v.name==='mobile'){
    await mobileNav.scrollIntoViewIfNeeded({timeout:10000});
    const mobileNavBox=await mobileNav.boundingBox();
    if(!mobileNavBox || mobileNavBox.y<0 || mobileNavBox.y+mobileNavBox.height>v.height)throw Error('Relocated mobile action not accessible within viewport');
    if(!/Passer aux moulages/i.test(await mobileNav.innerText()))throw Error('Mobile step-1 action label changed');
    await page.screenshot({path:path.join(OUTPUT,'mobile-NAV-step1-visible.png'),fullPage:false});
   }
   navigationChecks.push({viewport:v.name,mobile_cta_visible:mobileShown,desktop_footer_visible:footerShown,duplicate_visible:false});
   for(const fixture of cases){
    await page.getByTestId('fixture-'+fixture.id).click();
    await mode(page,'all');
    const a=displayed(await rowText(page,'ANB'));
    await mode(page,'steiner');
    const b=displayed(await rowText(page,'M_ANB_DEG_V1'));
    if(a!==fixture.legacy||b!==fixture.legacy)throw Error('ANB render mismatch '+fixture.id+' '+a+' '+b+' expected '+fixture.legacy);
    traces.push({viewport:v.name,fixture:fixture.id,all_mode_anb:a,steiner_mode_anb:b,facad_numeric_output:null});
    if(fixture.id==='F1_STRADDLE'){
     await mode(page,'all');
     const beforeRow=page.locator('[data-r19-metric="ANB"]');
     await beforeRow.scrollIntoViewIfNeeded({timeout:10000});
     const beforeBox=await beforeRow.boundingBox();
     if(!beforeBox || beforeBox.height<8 || beforeBox.y<0 || beforeBox.y+beforeBox.height>v.height)throw Error('BEFORE ANB row not visible in screenshot '+v.name);
     await page.screenshot({path:path.join(OUTPUT,v.name+'-BEFORE-all.png'),fullPage:false});
     occlusionObservations.push({viewport:v.name,mode:'all',key:'ANB',probe:await inspectNumericCellOcclusion(page,'ANB')});
     await mode(page,'steiner');
     const afterRow=page.locator('[data-r19-metric="M_ANB_DEG_V1"]');
     await afterRow.scrollIntoViewIfNeeded({timeout:10000});
     const afterBox=await afterRow.boundingBox();
     if(!afterBox || afterBox.height<8 || afterBox.y<0 || afterBox.y+afterBox.height>v.height)throw Error('AFTER ANB row not visible in screenshot '+v.name);
     await page.screenshot({path:path.join(OUTPUT,v.name+'-AFTER-steiner.png'),fullPage:false});
     occlusionObservations.push({viewport:v.name,mode:'steiner',key:'M_ANB_DEG_V1',probe:await inspectNumericCellOcclusion(page,'M_ANB_DEG_V1')});
     detectorControls.push({viewport:v.name,...await assertDetectorRejectsInjectedOverlay(page,'M_ANB_DEG_V1')});
     captures.push({viewport:v.name,width:v.width,height:v.height,before:'BEFORE-all',after:'AFTER-steiner'});
    }
   }
   await page.getByTestId('fixture-F1_STRADDLE').click();
   await page.getByTestId('source-invalid').click();await mode(page,'steiner');
   const bad=(await rowText(page,'M_ANB_DEG_V1')).trim();
   if(bad!=='NC')throw Error('Unverified canonical source did not fail closed: '+bad);
   await mode(page,'all');
   if(displayed(await rowText(page,'ANB'))!==0)throw Error('Legacy fixture unexpectedly changed');
   traces.push({viewport:v.name,case:'UNVERIFIED_AUTHORITY',steiner:'NC',all:0,guard:'PASS'});
   await page.getByTestId('source-divergent').click();
   await mode(page,'all');const a=displayed(await rowText(page,'ANB'));
   await mode(page,'steiner');const b=displayed(await rowText(page,'M_ANB_DEG_V1'));
   if(a!==0||b!==1)throw Error('Deliberately divergent payload was not visible');
   traces.push({viewport:v.name,case:'INTENTIONAL_PAYLOAD_DIVERGENCE',all:a,steiner:b,warning:'NO_AUTOMATIC_INTER_MODE_WARNING_ASSERTED',production_defect_confirmed:false});
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Page horizontal overflow '+v.name);
   if(errors.length)throw Error('React page errors '+JSON.stringify(errors));
  }finally{await ctx.close()}
 }
 if(!httpObserved.some(x=>x.method==='GET'&&x.path==='/api/patients/918'))throw Error('Real Workspace did not fetch synthetic demographics through HTTP');
 if(httpObserved.some(x=>!['GET','OPTIONS'].includes(x.method)||x.path!=='/api/patients/918'))throw Error('Forbidden synthetic backend request observed');
 const result={schema:'FACAD_F01_13_ANB_WORKSPACE_ISOLATED_HTTP_STUB_V1',
  status:'RESEARCH_WORKSPACE_HTTP_STUB_PASS',head:process.env.GITHUB_SHA||'LOCAL',
  viewport_count:2,fixture_count:cases.length,synthetic_only:true,
  real_react_panel_rendered:true,real_zustand_store_used:true,real_cephalo_workspace_rendered:true,synthetic_backend_http_get_verified:true,http_requests:httpObserved,real_fastapi_db_backend_executed:false,
  authenticated_product_e2e:false,facad_vendor_numeric_oracle_executed:false,
  patient_data_used:false,external_api_traffic_allowed:false,product_runtime_modified:false,
  expected_inter_mode_values_equal:true,unverified_steiner_fail_closed:true,
  explicit_divergence_visible:true,clinical_bug_confirmed:false,
  caveat:'BEFORE and AFTER are two display modes on one unchanged build, not a software change',
  captures,traces,occlusionObservations,detectorControls,navigationChecks,visualNoOcclusion:occlusionObservations.every(x=>x.probe.obstructionSamples===0),blocked_external_requests:[...new Set(networkBlocked)]};
 await writeFile(path.join(OUTPUT,'report.json'),JSON.stringify(result,null,2)+'\n');
 console.log('ANB_REAL_WORKSPACE_ISOLATED_HTTP_STUB_PASS=true');
 console.log('ANB_VIEWPORTS=2 ANB_FIXTURES=4 ANB_FAIL_CLOSED=true');
 console.log('ANB_VENDOR_NUMERIC_ORACLE_NOT_TESTED=true');
 console.log('ANB_VISUAL_OCCLUSION_OBSERVATIONS='+JSON.stringify(occlusionObservations.map(x=>({viewport:x.viewport,mode:x.mode,blocked:x.probe.obstructionSamples,rect:x.probe.cellRect}))));
 console.log(JSON.stringify({captures,traces},null,2));
 if(result.visualNoOcclusion!==true)throw Error('F01_13_ANB_VISUAL_OCCLUSION_DETECTED: see report.json/screenshots');
}finally{
 if(browser)await browser.close().catch(()=>{});
 if(server){server.kill('SIGTERM');await Promise.race([once(server,'exit'),sleep(1500)]).catch(()=>{})}
 if(stub)await new Promise(resolve=>stub.close(resolve)).catch(()=>{});
 await writeFile(path.join(OUTPUT,'vite.log'),viteLog).catch(()=>{});
 await rm(ENTRY,{force:true});await rm(HTML,{force:true});
}
