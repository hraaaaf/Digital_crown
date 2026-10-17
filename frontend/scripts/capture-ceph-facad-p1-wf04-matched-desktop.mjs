/** P1 WF04: same synthetic fixture, same real React component, desktop BEFORE / AFTER.
 * No vendor, medical data, real patient, authorization, or clinical claims.
 */
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const phase=process.env.PARITY_PHASE, head=process.env.PRODUCT_HEAD;
if(!['BEFORE','AFTER'].includes(phase)||!head)throw Error('Need PARITY_PHASE and PRODUCT_HEAD');
const dir=process.cwd(), out=path.join(dir,'ceph-facad-p1-wf04-evidence',phase.toLowerCase());
await rm(out,{recursive:true,force:true});await mkdir(out,{recursive:true});
const profiles={};
for(const [slot,id,count,status,lock] of [
  ['mcnamara','MCNAMARA_1984_SINGLE_FILM_V1',13,'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL','HISTORICAL_WORKING_REFERENCE_ONLY'],
  ['ricketts_atlas2009','RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1',33,'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL','COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED'],
  ['ricketts_gregoret13','RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1',13,'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__FAIL_CLOSED','COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED'],
]){
 profiles[slot]={protocol_profile_id:id,profile_status:status,source_lock_gate:lock,
 classification_authority:false,rows:Array.from({length:count},(_,i)=>({
 order:i+1,canonical_measurement_id:'M_TEST_'+String(i+1)+'_MM_V1',
 label:'Facteur '+String(i+1),unit:'mm',value:null,availability_status:'NOT_COMPUTABLE',
 contract_state:'CONDITIONAL_EXECUTABLE',classification_authority:false,source_contract:id,
 measurement_refs:[],value_authority_method_id:null
 }))};
}
const payload={scientific_read_path:{authority:'EVIDENCE_GRAPH_V1',active_chain:'VERIFIED',protocol_profiles:profiles}};
const entry=[
 "import React,{useState} from 'react';",
 "import{createRoot}from'react-dom/client';",
 "import{CephaloAnalysisWorkbenchPanel}from'./features/ortho/components/CephaloAnalysisWorkbenchPanel';",
 "import{useOrthoStore}from'./features/ortho/stores/useOrthoStore';",
 "import'./index.css';",
 "const dataset="+JSON.stringify(payload)+";",
 "useOrthoStore.setState({anglesData:dataset});",
 "const P={bg:'#fff',bgPanel:'#fff',bgCard:'#f8fafc',bgInput:'#fff',border:'#cbd5e1',borderFocus:'#2563eb',text:'#0f172a',textMuted:'#334155',textDim:'#475569',accent:'#2563eb',accentSuccess:'#15803d',accentWarning:'#b45309',accentError:'#b91c1c',shadow:'none',shadowLg:'none'};",
 "function App(){const[mode,setMode]=useState('mcnamara');return <main style={{padding:12,minHeight:'100vh',background:'#f8fafc'}}><div data-p1-synthetic='true' style={{font:'bold 12px system-ui',padding:8,color:'#7c2d12',background:'#fef3c7'}}>WF04 SYNTHETIC · NO PATIENT · NO CLINICAL VALIDATION</div><label htmlFor='wf04mode'>Profil à afficher</label><select id='wf04mode' aria-label='Profil à afficher' value={mode} onChange={e=>setMode(e.target.value)}><option value='mcnamara'>McNamara</option><option value='ricketts'>Ricketts</option></select><div data-p1-panel-container style={{height:'calc(100vh - 115px)',width:550,maxWidth:'100%',minHeight:500}}><CephaloAnalysisWorkbenchPanel P={P} analysis={mode}/></div></main>}",
 "createRoot(document.getElementById('root')).render(<App/>);"
].join('\n');
const html='<!doctype html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0"><div id="root"></div><script type="module" src="/src/ceph-facad-p1-entry.tsx"></script></body></html>';
await writeFile(path.join(dir,'src/ceph-facad-p1-entry.tsx'),entry);
await writeFile(path.join(dir,'ceph-facad-p1.html'),html);
const config="import{defineConfig}from'vite';import react from'@vitejs/plugin-react';export default defineConfig({plugins:[react()],build:{outDir:'ceph-facad-p1-static',emptyOutDir:true,rollupOptions:{input:'ceph-facad-p1.html'}},preview:{host:'127.0.0.1',port:5217,strictPort:true}});";
await writeFile(path.join(dir,'ceph-facad-p1-config.mjs'),config);
const vite=path.join(dir,'node_modules','vite','bin','vite.js');
async function processOnce(args){const child=spawn(process.execPath,[vite,...args],{cwd:dir,env:{...process.env,VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']});let log='';child.stdout.on('data',d=>log+=d);child.stderr.on('data',d=>log+=d);const [status]=await once(child,'close');return{status,log};}
const build=await processOnce(['build','--config','ceph-facad-p1-config.mjs']);
await writeFile(path.join(out,'build.log'),build.log);
if(build.status!==0)throw Error('Cannot build browser fixture: '+build.log.slice(-900));
const server=spawn(process.execPath,[vite,'preview','--config','ceph-facad-p1-config.mjs','--port','5217'],{cwd:dir,env:{...process.env,VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']});
let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
const report={phase,productHead:head,fixture:'same synthetic locked nonpatient profiles 13/33/13',viewports:[],browserErrors:[],vendorExecuted:false,clinicalRelease:false};
const expected=phase==='BEFORE'?{mcnamara:3,ricketts:2}:{mcnamara:13,atlas:33,gregoret:13};
async function readMode(page,label,mode,variant){
 await page.locator('#wf04mode').selectOption(mode);
 const host=phase==='BEFORE'?page.locator('[data-r19-analysis-panel="'+mode+'"]'):page.locator('[data-r23g2-protocol-panel="'+mode+'"]');
 await host.waitFor({state:'visible',timeout:15000});
 if(variant==='gregoret')await page.getByRole('button',{name:'Gregoret · 13 facteurs'}).click();
 const rows=await host.locator(phase==='BEFORE'?'[data-r19-metric]':'[data-r23g2-measurement-id]').count();
 const count=expected[label];
 if(rows!==count)throw Error(label+': expected '+count+' got '+rows);
 if(phase==='AFTER'){
  const valueCells=await host.locator('tbody tr td:first-of-type').allTextContents();
  if(valueCells.length!==rows||valueCells.some(x=>x.trim()!=='NC'))throw Error('False synthetic clinical value '+label);
  const coverage=await host.locator('[data-r23g2-coverage]').textContent();
  if(!coverage?.includes('0/'+count+' valeurs disponibles'))throw Error('False available counts '+label);
 }
 await page.screenshot({path:path.join(out,phase.toLowerCase()+'-'+label+'-'+page.viewportSize().width+'x'+page.viewportSize().height+'.png'),fullPage:false});
 return{mode:label,rows,valid:true,numericClinicalValues:0};
}
try{
 for(let i=0;i<120;i++){try{const r=await fetch('http://127.0.0.1:5217/ceph-facad-p1.html');if(r.ok)break;}catch{}if(i===119)throw Error('Preview timeout');await new Promise(r=>setTimeout(r,250));}
 for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport,locale:'fr-FR',reducedMotion:'reduce'});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',x=>{if(x.type()==='error')errors.push(x.text())});
  await page.route('**/*',route=>{const url=new URL(route.request().url());if(url.hostname==='127.0.0.1'&&url.port==='5217')return route.continue();if(url.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});if(url.hostname==='fonts.gstatic.com')return route.fulfill({status:204,body:''});report.browserErrors.push('unexpected external request: '+url.origin+url.pathname);return route.abort('blockedbyclient')});
  try{
   const response=await page.goto('http://127.0.0.1:5217/ceph-facad-p1.html',{waitUntil:'domcontentloaded',timeout:45000});
   if(response?.status()!==200)throw Error('Bad HTTP');
   await page.locator('[data-p1-synthetic="true"]').waitFor({state:'visible',timeout:30000});
   const states=[await readMode(page,'mcnamara','mcnamara')];
   if(phase==='BEFORE')states.push(await readMode(page,'ricketts','ricketts'));
   else {states.push(await readMode(page,'atlas','ricketts'));states.push(await readMode(page,'gregoret','ricketts','gregoret'));}
   const documentOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
   if(documentOverflow||errors.length)throw Error('Browser error/overflow: '+JSON.stringify({documentOverflow,errors}));
   report.viewports.push({viewport:viewport.width+'x'+viewport.height,valid:true,states,documentOverflow,pageErrors:[]});
  }catch(e){report.viewports.push({viewport:viewport.width+'x'+viewport.height,valid:false,error:String(e),pageErrors:errors});}
  finally{await context.close();await browser.close();}
 }
}finally{
 server.kill('SIGTERM');await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{});
 await writeFile(path.join(out,'preview.log'),serverLog);
 await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
}
if(report.browserErrors.length||report.viewports.length!==2||report.viewports.some(v=>!v.valid))throw Error('P1 matched browser evidence FAILED: '+JSON.stringify(report.viewports));
console.log(JSON.stringify(report));
