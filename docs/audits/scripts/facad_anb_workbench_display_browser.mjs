#!/usr/bin/env node
// Source-locked research: actual React panel + real Zustand store in isolated
// Chromium. NO FACAD, clinical case, live API, or product code modification.
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {existsSync} from 'node:fs';
import {mkdir,readFile,rm,writeFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const ROOT=path.resolve(import.meta.dirname,'../../..');
const FRONTEND=path.join(ROOT,'frontend');
const OUTPUT=process.env.FACAD_ANB_BROWSER_OUTPUT||path.join(os.tmpdir(),'facad-anb-display');
const PROOF_FILE=process.env.FACAD_ANB_SYNTHETIC_FIXTURES_PATH;
const ENTRY=path.join(FRONTEND,'src','facad-anb-research-fixture-entry.tsx');
const HTML=path.join(FRONTEND,'facad-anb-research-fixture.html');
const PORT=5278,APP_URL='http://127.0.0.1:'+PORT+'/facad-anb-research-fixture.html';
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
 "import {CephaloAnalysisWorkbenchPanel} from './features/ortho/components/CephaloAnalysisWorkbenchPanel';",
 "import {useOrthoStore} from './features/ortho/stores/useOrthoStore';",
 "import './index.css';",
 "const cases=FIXTURE_CASES;",
 "const P={bg:'#111827',bgPanel:'#172033',bgCard:'#1e293b',bgInput:'#0f172a',border:'#475569',borderFocus:'#38bdf8',text:'#f8fafc',textMuted:'#cbd5e1',textDim:'#94a3b8',accent:'#38bdf8',accentSuccess:'#22c55e',accentWarning:'#f59e0b',accentError:'#f87171',shadow:'none',shadowLg:'none'};",
 "function dataFor(row,sourceMode){",
 " const v=row.legacy,canon=sourceMode==='divergent'?+(v+1).toFixed(1):v;",
 " const sr={canonical_measurement_id:'M_ANB_DEG_V1',label:'ANB',layer:'STEINER_1953_BASE',value:canon,unit:'°',availability_status:'AVAILABLE',measurement_refs:['synthetic:ANB'],value_authority_method_id:'STEINER_ANB_DEG_V1',historical_reference:null,reference_delta:null,reference_authority:'REFERENCE_DISPLAY_ONLY',classification_authority:false,interpretation_status:'REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION'};",
 " return {metrics:{analyse_osseuse:{ANB:{valeur:v,status:'N/A'}},analyse_dentaire:{},analyse_esthetique:{}},scientific_read_path:{authority:sourceMode==='invalid'?'LEGACY_ONLY':'EVIDENCE_GRAPH_V1',active_chain:sourceMode==='invalid'?'UNVERIFIED':'VERIFIED',canonical_measurements:[{canonical_measurement_id:'M_ANB_DEG_V1',value:canon,unit:'°',availability_status:'AVAILABLE',measurement_refs:['synthetic:ANB']}],protocol_profiles:{steiner:{protocol_profile_id:'STEINER_STATIC_PROTOCOL_PROFILE_V1',source_lock_gate:{gate:'ORTHO_ANALYSIS_PROTOCOLS_SOURCE_LOCKED',status:'SATISFIED'},final_gate:{gate:'ORTHO_ANALYSIS_PROTOCOLS_VERIFIED',status:'OPEN'},norm_set:{authority:'REFERENCE_DISPLAY_ONLY'},rows:[sr]}}}};",
 "}",
 "useOrthoStore.setState({anglesData:dataFor(cases[0],'valid'),local:{...useOrthoStore.getState().local,landmarks:[],version:1}});",
 "function App(){",
 " const [analysis,setAnalysis]=React.useState('all'); const [index,setIndex]=React.useState(0); const [scenario,setScenario]=React.useState('valid');",
 " function swap(i,s){useOrthoStore.setState({anglesData:dataFor(cases[i],s)});setIndex(i);setScenario(s)}",
 " return <main style={{width:'100%',height:'100vh',boxSizing:'border-box',padding:16,background:P.bg,color:P.text}}>",
 "  <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:10}}><button data-testid='mode-all' onClick={()=>setAnalysis('all')}>Toutes analyses</button><button data-testid='mode-steiner' onClick={()=>setAnalysis('steiner')}>Steiner</button></div>",
 "  <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:8}}>{cases.map((c,i)=><button key={c.id} data-testid={'fixture-'+c.id} onClick={()=>swap(i,'valid')}>{c.id}</button>)}</div>",
 "  <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:12}}><button data-testid='source-valid' onClick={()=>swap(index,'valid')}>Source valide</button><button data-testid='source-invalid' onClick={()=>swap(index,'invalid')}>Source non vérifiée</button><button data-testid='source-divergent' onClick={()=>swap(index,'divergent')}>Divergence injectée</button></div>",
 "  <div data-testid='fixture-id'>{cases[index].id}</div><div data-testid='fixture-mode'>{scenario}</div>",
 "  <div style={{height:'calc(100vh - 210px)',minHeight:390,maxWidth:850,display:'flex'}}><div style={{width:'100%',height:'100%',minWidth:0,display:'flex'}}><CephaloAnalysisWorkbenchPanel P={P} analysis={analysis}/></div></div>",
 " </main>",
 "}",
 "createRoot(document.getElementById('root')).render(<App/>);"
].join('\n').replace('FIXTURE_CASES',JSON.stringify(cases));
const html='<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body style="margin:0"><div id="root"></div><script type="module" src="/src/facad-anb-research-fixture-entry.tsx"></script></body></html>';
if(existsSync(ENTRY)||existsSync(HTML))throw Error('Fixture collision: refuse overwrite');
await mkdir(OUTPUT,{recursive:true});
let server,browser,viteLog='';
const captures=[],traces=[],networkBlocked=[];
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
 await page.getByTestId('mode-'+key).click();
 await page.locator('[data-r19-analysis-panel="'+key+'"]').waitFor({state:'visible'});
}
try{
 await writeFile(ENTRY,entry);
 await writeFile(HTML,html);
 const vitePath=path.join(FRONTEND,'node_modules','vite','bin','vite.js');
 if(!existsSync(vitePath))throw Error('npm ci must run before browser probe');
 server=spawn(process.execPath,[vitePath,'--host','127.0.0.1','--port',String(PORT),'--strictPort'],{cwd:FRONTEND,env:{...process.env,VITE_ENABLE_HTTPS:'false'},stdio:['ignore','pipe','pipe']});
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
   if(u.hostname==='127.0.0.1'&&Number(u.port)===PORT)return route.continue();
   networkBlocked.push(u.origin);return route.abort('blockedbyclient');
  });
  try{
   await page.goto(APP_URL,{waitUntil:'domcontentloaded',timeout:45000});
   await page.locator('[data-r19-analysis-panel="all"]').waitFor({state:'visible'});
   for(const fixture of cases){
    await page.getByTestId('fixture-'+fixture.id).click();
    await mode(page,'all');
    const a=displayed(await rowText(page,'ANB'));
    await mode(page,'steiner');
    const b=displayed(await rowText(page,'M_ANB_DEG_V1'));
    if(a!==fixture.legacy||b!==fixture.legacy)throw Error('ANB render mismatch '+fixture.id+' '+a+' '+b+' expected '+fixture.legacy);
    traces.push({viewport:v.name,fixture:fixture.id,all_mode_anb:a,steiner_mode_anb:b,facad_numeric_output:null});
    if(fixture.id==='F1_STRADDLE'){
     await mode(page,'all');await page.screenshot({path:path.join(OUTPUT,v.name+'-BEFORE-all.png'),fullPage:false});
     await mode(page,'steiner');await page.screenshot({path:path.join(OUTPUT,v.name+'-AFTER-steiner.png'),fullPage:false});
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
 const result={schema:'FACAD_F01_13_ANB_DUAL_DISPLAY_BROWSER_RESEARCH_V1',
  status:'RESEARCH_BROWSER_COMPONENT_PASS',head:process.env.GITHUB_SHA||'LOCAL',
  viewport_count:2,fixture_count:cases.length,synthetic_only:true,
  real_react_panel_rendered:true,real_zustand_store_used:true,
  authenticated_product_e2e:false,facad_vendor_numeric_oracle_executed:false,
  patient_data_used:false,external_api_traffic_allowed:false,product_runtime_modified:false,
  expected_inter_mode_values_equal:true,unverified_steiner_fail_closed:true,
  explicit_divergence_visible:true,clinical_bug_confirmed:false,
  caveat:'BEFORE and AFTER are two display modes on one unchanged build, not a software change',
  captures,traces,blocked_external_requests:[...new Set(networkBlocked)]};
 await writeFile(path.join(OUTPUT,'report.json'),JSON.stringify(result,null,2)+'\n');
 console.log('ANB_REAL_REACT_CHROMIUM_PASS=true');
 console.log('ANB_VIEWPORTS=2 ANB_FIXTURES=4 ANB_FAIL_CLOSED=true');
 console.log('ANB_VENDOR_NUMERIC_ORACLE_NOT_TESTED=true');
 console.log(JSON.stringify({captures,traces},null,2));
}finally{
 if(browser)await browser.close().catch(()=>{});
 if(server){server.kill('SIGTERM');await Promise.race([once(server,'exit'),sleep(1500)]).catch(()=>{})}
 await writeFile(path.join(OUTPUT,'vite.log'),viteLog).catch(()=>{});
 await rm(ENTRY,{force:true});await rm(HTML,{force:true});
}
