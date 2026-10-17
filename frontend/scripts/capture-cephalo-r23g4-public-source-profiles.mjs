/**
 * R23-G4 — reproducible NONCLINICAL visual audit on attributed public radiographs.
 * Real Wikimedia JPEG pixels; deliberately unregistered synthetic landmarks and
 * synthetic/not-computable profile records. NEVER claim measured anatomy or diagnosis.
 * Same script runs BEFORE (fixed predecessor SHA) and AFTER (exact PR HEAD).
 */
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createHash } from 'node:crypto';
import { readFile, mkdir, rm, writeFile, stat } from 'node:fs/promises';
import path from 'node:path';

const head=process.env.PRODUCT_HEAD;
const phase=process.env.CEPHALO_G4_PHASE;
// R23-G6 adds a bounded mobile zoom/pan audit to the same public, NONCLINICAL fixture.
const g6Audit=process.env.CEPHALO_G6_AUDIT==='1';
const caseId=process.env.CEPHALO_PUBLIC_CASE;
if(!head || !['BEFORE','AFTER'].includes(phase) || !['anug','challiyan'].includes(caseId))
  throw new Error('PRODUCT_HEAD, CEPHALO_G4_PHASE=BEFORE|AFTER and CEPHALO_PUBLIC_CASE required');

const SOURCES={
  anug:{author:'ANUG',year:2014,width:2272,height:1818,sha1:'2a284993c666790a72d0c004044b35a92534ce9d',page:'https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG',license:'CC BY-SA 4.0'},
  challiyan:{author:'Challiyan',year:2023,width:1000,height:1255,sha1:'66c74c588af3c54dfc581f8a870c5276c3427498',page:'https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg',license:'CC BY-SA 4.0'}
};
const radio=SOURCES[caseId];
const input=await readFile(path.join('public-radio-input',caseId+'.jpg'));
const actualSha1=createHash('sha1').update(input).digest('hex');
if(actualSha1!==radio.sha1)throw new Error('Wikimedia source SHA1 mismatch for '+caseId);
const sha256=createHash('sha256').update(input).digest('hex');
const image='data:image/jpeg;base64,'+input.toString('base64');
const frontend=process.cwd();
const root=path.resolve(frontend,'..');
const json=async file=>JSON.parse(await readFile(path.join(root,file),'utf8'));
const atlas=await json('backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json');
const gregoret=await json('backend/data/cephalometry/ricketts_gregoret13_protocol_profile_v1.json');
const ledger=await json('backend/data/cephalometry/clinical_reference_profiles_v1.json');
const rows=(items,id,kind)=>items.map((r,i)=>({
  order:i+1,
  canonical_measurement_id:r.measurement_id,
  label:r.label||r.measurement_id,
  unit:r.measurement_id.includes('_DEG_')?'deg':'mm',
  value:null,availability_status:'NOT_COMPUTABLE',
  contract_state:kind==='ricketts'?r.state:r.contract_state,
  contract_gate:r.gate||null,
  classification_authority:false,source_contract:id,
  measurement_refs:[],value_authority_method_id:null
}));
const mcnamaraId='MCNAMARA_1984_SINGLE_FILM_V1';
const atlasId='RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1';
const gregoretId='RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1';
const fakeProfiles={
  mcnamara:{protocol_profile_id:mcnamaraId,profile_status:'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL',source_lock_gate:'HISTORICAL_WORKING_REFERENCE_ONLY',classification_authority:false,rows:rows(ledger.profiles.mcnamara.rows,mcnamaraId,'historical')},
  ricketts_atlas2009:{protocol_profile_id:atlasId,profile_status:atlas.status,source_lock_gate:'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED',classification_authority:false,rows:rows(atlas.measurements,atlasId,'ricketts')},
  ricketts_gregoret13:{protocol_profile_id:gregoretId,profile_status:gregoret.status,source_lock_gate:'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED',classification_authority:false,rows:rows(gregoret.measurements,gregoretId,'ricketts')}
};
if(fakeProfiles.mcnamara.rows.length!==13||fakeProfiles.ricketts_atlas2009.rows.length!==33||fakeProfiles.ricketts_gregoret13.rows.length!==13)
  throw new Error('Protocol source drift; never silently truncate fixture');
const basePoints=[
['S',430,370],['N',650,360],['A',690,620],['B',675,790],['Po',390,500],['Or',650,520],
['Go',430,980],['Me',680,1040],['Co',410,430],['Gn',690,1010],['ANS',685,610],
['Occ_Ant',715,760],['Occ_Post',500,790],['U1_apex',640,650],['U1_incisal',690,770],
['L1_apex',650,900],['L1_incisal',700,785],['G_soft',720,300],['N_soft',760,355],
['Prn',835,515],['Cm',790,575],['Sn_soft',760,610],['A_soft',770,650],
['Ls_soft',805,700],['St',795,755],['Li_soft',810,805],['B_soft',770,875],
['Pog_soft',790,965],['Me_soft',750,1060],
['Po_anatomic',375,492],['Pog_hard',675,980],['Co_anatomic',405,440],
['Gn_anatomic',700,1030],['Pt_Ricketts',620,590],['PTM_McNamara',601,567],
['Ba',435,325],['Xi_Ricketts',520,900],['PM_Ricketts',570,1020]
];
if(basePoints.length!==38||new Set(basePoints.map(x=>x[0])).size!==38)throw new Error('Expected 38 unique simulated source handles');
const scaled=basePoints.map(([id,x,y])=>({id,x:x*radio.width/1200,y:y*radio.height/1600}));
const out=path.join(frontend,g6Audit?'cephalo-r23g6-mobile-zoom-evidence':'cephalo-r23g4-public-evidence',phase.toLowerCase(),caseId);
await rm(out,{recursive:true,force:true});await mkdir(out,{recursive:true});
const attribution={...radio,sourceCaseId:caseId,actualSha1,sha256,licenseUrl:'https://creativecommons.org/licenses/by-sa/4.0/',phase,productHead:head,
  caveat:'PUBLIC JPEG + UNREGISTERED SYNTHETIC POINTS + NO VERIFIED PATIENT/MEASUREMENT EVIDENCE. VISUAL UX ONLY.'};
await writeFile(path.join(out,'PUBLIC-SOURCE-LICENSE.json'),JSON.stringify(attribution,null,2));
const entry=[
"import React from 'react';",
"import ReactDOM from 'react-dom/client';",
"import { MemoryRouter } from 'react-router-dom';",
"import { CephaloWorkspace } from './features/ortho/CephaloWorkspace';",
"import { useOrthoStore } from './features/ortho/stores/useOrthoStore';",
"import './index.css';",
"const source="+JSON.stringify(image)+";",
"const points="+JSON.stringify(scaled)+";",
"const profiles="+JSON.stringify(fakeProfiles)+";",
"const anglesData={metrics:{analyse_dentaire:{},analyse_osseuse:{},analyse_esthetique:{}},scientific_read_path:{authority:'EVIDENCE_GRAPH_V1',active_chain:'VERIFIED',protocol_profiles:profiles},calibration_status:'unverified',visual_debug:{}};",
"window.__cephaloG4Audit={synthetic:true,events:[]};",
"Object.assign(window,{__cephaloG6Evidence:()=>useOrthoStore.getState().local.landmarks.map(p=>({id:p.id,x:p.x,y:p.y}))});",
"window.addEventListener('digital-crown:cephalo-metric',ev=>window.__cephaloG4Audit.events.push(ev.detail));",
"useOrthoStore.setState({patientId:919,patientName:'R23-G4 · UX FICTIVE',analysisId:9919,imageSrc:source,imgDim:{w:"+radio.width+",h:"+radio.height+"},local:{landmarks:points,version:1},completedSteps:new Set([1]),step:1,anglesData,isCalibrated:false,mmPerPixel:null});",
"ReactDOM.createRoot(document.getElementById('root')).render(<MemoryRouter><div style={{height:'100vh'}}><CephaloWorkspace patientId={919} patientName='R23-G4 · UX FICTIVE'/></div></MemoryRouter>);"
].join('\n');
const html="<!doctype html><html lang='fr'><head><meta charset='UTF-8'/><meta name='viewport' content='width=device-width,initial-scale=1.0'/><title>R23-G4 source-only UX</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id='root'></div><script type='module' src='/src/cephalo-r23g4-public-entry.tsx'></script></body></html>";
await writeFile(path.join(frontend,'src/cephalo-r23g4-public-entry.tsx'),entry);
await writeFile(path.join(frontend,'cephalo-r23g4-public.html'),html);
const port=5197;const base='http://127.0.0.1:'+port;
const vite=path.join(frontend,'node_modules/vite/bin/vite.js');
const server=spawn(process.execPath,[vite,'--host','127.0.0.1','--port',String(port)],{cwd:frontend,env:{...process.env,VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']});
let viteLog='';server.stdout.on('data',x=>viteLog+=x);server.stderr.on('data',x=>viteLog+=x);
const viewports=g6Audit
 ? [{width:390,height:844},{width:430,height:932},{width:1280,height:900}]
 : [{width:390,height:844},{width:430,height:932},{width:768,height:1024},{width:1280,height:900},{width:1600,height:1000}];
const report={phase,caseId,productHead:head,provenance:attribution,viewports:[],blockedRequests:[],invalidCount:0,g6Audit};
const allowed=async route=>{
  const req=route.request();const u=new URL(req.url());
  if(u.hostname==='127.0.0.1'&&u.port===String(port))return route.continue();
  if(u.hostname==='127.0.0.1'&&u.port==='8005'&&req.method()==='GET'&&u.pathname==='/api/patients/919')
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:919,age:34,sexe:'M'})});
  if(u.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});
  report.blockedRequests.push(req.url());return route.abort('blockedbyclient');
};
const fail=(message)=>{throw new Error(message)};
async function waitServer(){
  for(let i=0;i<100;i++){try{const r=await fetch(base+'/cephalo-r23g4-public.html');if(r.ok)return}catch{}
    await new Promise(r=>setTimeout(r,250))}
  fail('Vite not responding');
}
async function auditG6ZoomPan(page, viewport, viewportName) {
  const isMobile=viewport.width<1280;
  // G4 ends in COM mode, which intentionally filters landmark handles. G6 must
  // inspect the full 38 source points, so return to Ricketts before snapshots.
  await page.locator('#cephalo-ready-analysis').selectOption('ricketts');
  await page.locator('[data-r23g2-protocol-panel="ricketts"]').waitFor({state:'attached',timeout:10000});
  // BEFORE is a *known* technical limitation: mobile controls disabled, desktop active.
  const expectedControls=phase==='AFTER'||!isMobile;
  const stage=page.locator('[data-r20-radiograph-stage]');
  await stage.scrollIntoViewIfNeeded();
  const controls=page.locator('[data-cephalo-zoom-controls]');
  const present=await controls.count();
  if(Boolean(present)!==expectedControls)fail('G6 mobile zoom availability mismatch '+viewportName+' '+phase+': '+present);
  const snapshot=()=>page.evaluate(()=>{
    const base=document.querySelector('svg[data-cephalo-viewport="base"]');
    const overlay=document.querySelector('svg[data-cephalo-viewport="overlay"]');
    const handles=Array.from(document.querySelectorAll('[data-ceph03b-drag-handle]'))
      .map(x=>[x.getAttribute('data-ceph03b-drag-handle'),x.getAttribute('cx'),x.getAttribute('cy'),x.getAttribute('transform')]);
    return {
      base:base?.getAttribute('viewBox')??null,
      overlay:overlay?.getAttribute('viewBox')??null,
      handles,
      storeLandmarks:typeof window.__cephaloG6Evidence==='function'?window.__cephaloG6Evidence():null,
      documentWidth:document.documentElement.scrollWidth,
      viewportWidth:document.documentElement.clientWidth,
      label:document.querySelector('[data-cephalo-zoom-level]')?.textContent?.trim()??null,
      focusUnavailable:document.querySelectorAll('[data-r23g3-focus-source="active-runtime"]').length===0,
    };
  });
  const initial=await snapshot();
  if(!initial.base||initial.base!==initial.overlay||initial.handles.length!==38||initial.storeLandmarks?.length!==38)
    fail('G6 initial SVG/handle alignment invalid '+viewportName+' '+JSON.stringify({base:initial.base,overlay:initial.overlay,domHandleCount:initial.handles.length,storeCount:initial.storeLandmarks?.length??null,storeType:typeof initial.storeLandmarks}));
  const untouched=phase.toLowerCase()+'-g6-'+viewportName+'-100.png';
  await page.screenshot({path:path.join(out,untouched),fullPage:false});
  if(!expectedControls)return {mobile:isMobile,available:false,initial,fullImageScreenshot:untouched,expectedBlock:'MOBILE_ZOOM_DISABLED_BEFORE'};
  const activate=async label=>{const btn=controls.getByRole('button',{name:label});
    return isMobile ? btn.tap() : btn.click();};
  for(let i=0;i<4;i++)await activate('Agrandir la radiographie');
  const zoomed=await snapshot();
  if(zoomed.label!=='200 %'||zoomed.base!==zoomed.overlay)
    fail('G6 zoom 200% or overlay desync '+viewportName+' '+JSON.stringify(zoomed).slice(0,500));
  const [,,iw,ih]=initial.base.split(/\s+/).map(Number);
  const [,,zw,zh]=zoomed.base.split(/\s+/).map(Number);
  if(Math.abs(zw-iw/2)>0.01||Math.abs(zh-ih/2)>0.01)
    fail('G6 expected exact 200% viewBox crop '+viewportName);
  if(JSON.stringify(initial.handles)!==JSON.stringify(zoomed.handles)||
    JSON.stringify(initial.storeLandmarks)!==JSON.stringify(zoomed.storeLandmarks))
    fail('G6 zoom changed anatomical SVG coordinates '+viewportName);
  const screenshot200=phase.toLowerCase()+'-g6-'+viewportName+'-200.png';
  await page.screenshot({path:path.join(out,screenshot200),fullPage:false});
  await activate('Déplacer la radiographie à droite');
  const panned=await snapshot();
  if(panned.base===zoomed.base||panned.base!==panned.overlay)
    fail('G6 pan movement or overlay desync '+viewportName);
  if(JSON.stringify(initial.handles)!==JSON.stringify(panned.handles)||
    JSON.stringify(initial.storeLandmarks)!==JSON.stringify(panned.storeLandmarks))
    fail('G6 pan changed anatomical SVG coordinates '+viewportName);
  const screenshotPan=phase.toLowerCase()+'-g6-'+viewportName+'-pan.png';
  await page.screenshot({path:path.join(out,screenshotPan),fullPage:false});
  await activate('Afficher toute la radiographie');
  const restored=await snapshot();
  if(restored.label!=='100 %'||restored.base!==initial.base||restored.overlay!==initial.overlay||
    JSON.stringify(restored.storeLandmarks)!==JSON.stringify(initial.storeLandmarks))
    fail('G6 reset did not restore the original viewBox '+viewportName);
  if(![zoomed,panned,restored].every(x=>x.documentWidth-x.viewportWidth<=2&&x.focusUnavailable))
    fail('G6 overflow or unauthorized scientific Focus '+viewportName);
  // A Vite dev hot-navigation can briefly produce an all-white frame between
  // the reset click and its next paint. Require a *stable* rendered SVG before
  // capturing; never accept a blank screenshot as proof.
  await page.waitForTimeout(550);
  await page.locator('svg[data-cephalo-viewport="base"] image').waitFor({state:'visible',timeout:15000});
  await stage.scrollIntoViewIfNeeded();
  const stableRestored=await snapshot();
  if(stableRestored.base!==initial.base||stableRestored.overlay!==initial.overlay||
    stableRestored.label!=='100 %'||
    JSON.stringify(stableRestored.storeLandmarks)!==JSON.stringify(initial.storeLandmarks))
    fail('G6 post-render reset state changed unexpectedly '+viewportName);
  const screenshotReset=phase.toLowerCase()+'-g6-'+viewportName+'-reset.png';
  await page.screenshot({path:path.join(out,screenshotReset),fullPage:false});
  const resetBytes=(await stat(path.join(out,screenshotReset))).size;
  if(resetBytes<10000)fail('G6 reset captured blank or incomplete viewport '+viewportName+' bytes='+resetBytes);
  return {mobile:isMobile,available:true,initial,zoomed,panned,restored:stableRestored,screenshots:[untouched,screenshot200,screenshotPan,screenshotReset]};
}
async function capture(v){
 const viewportName=v.width+'x'+v.height;
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:v,locale:'fr-FR',reducedMotion:'reduce',
  isMobile:g6Audit&&v.width<1280,hasTouch:g6Audit&&v.width<1280});
 const page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.route('**/*',allowed);
 const states=[];
 try {
  const response=await page.goto(base+'/cephalo-r23g4-public.html',{waitUntil:'domcontentloaded',timeout:45000});
  if(response?.status()!==200)fail('Bad Vite response');
  await page.getByRole('heading',{name:'Céphalométrie',exact:true}).waitFor({state:'visible',timeout:40000});
  const decoded=await page.evaluate(async()=>{
    const image=document.querySelector('svg[data-cephalo-viewport="base"] image');
    const img=new Image();img.src=image?.getAttribute('href')||'';await img.decode();
    return {width:img.naturalWidth,height:img.naturalHeight};
  });
  if(decoded.width!==radio.width||decoded.height!==radio.height)fail('Public image did not decode');
  await page.evaluate((metadata)=>{
    const label=document.createElement('div');label.dataset.r23g4AuditBanner='true';
    label.textContent='R23-G4 '+metadata.phase+' · '+metadata.author+' (Wikimedia / CC BY-SA 4.0) · REPÈRES ET PROFILS FICTIFS · AUCUNE MESURE CLINIQUE';
    Object.assign(label.style,{position:'fixed',top:'4px',left:'4px',maxWidth:'90vw',
      padding:'5px 6px',borderRadius:'5px',fontFamily:'system-ui',fontSize:'10px',fontWeight:'800',
      background:'#fff9dc',color:'#5e3600',border:'1px solid #b57b00',
      zIndex:'99999',pointerEvents:'none'});
    document.body.append(label);
  },{phase,author:radio.author});
  for(const kind of ['mcnamara','ricketts']){
    // On narrow Cabinet layouts the floating tracing tabs are not visible.
    // The actual accessible workflow entrypoint is the ready-analysis select.
    await page.locator('#cephalo-ready-analysis').selectOption(kind);
    const panel=page.locator('[data-r23g2-protocol-panel="'+kind+'"]');
    await panel.waitFor({state:'attached',timeout:10000});
    const variants=kind==='ricketts'?['atlas','gregoret']:['historical'];
    for(const variant of variants){
      if(kind==='ricketts')await page.locator('[data-r23g2-ricketts-version="'+variant+'"]').click();
      const expected=kind==='ricketts'&&variant==='atlas'?33:13;
      const count=await panel.locator('[data-r23g2-measurement-id]').count();
      const c=await panel.locator('[data-r23g2-coverage]').innerText();
      if(count!==expected||!c.includes('0/'+expected))fail('Wrong profile cardinality '+kind+'/'+variant+'/'+count+' '+c);
      const first=panel.locator('[data-r23g3-focus-select]').first();
      await first.click();
      const failClosed=await panel.locator('[data-r23g3-focus-source="not-authorized"]').count();
      if(failClosed!==1)fail('Blocked evidence unexpectedly got a visual focus');
      const values=await panel.locator('tbody tr td:first-of-type').allTextContents();
      if(values.length!==expected||values.some(x=>x.trim()!=='NC'))fail('Synthetic fixture supplied an unexpected numeric clinical value');
      const handles=await page.locator('[data-ceph03b-drag-handle]').count();
      // All source handles MUST stay accessible; zero are to be inferred.
      if(handles!==38)fail('Lost source handles in '+kind+'/'+variant+': '+handles+'/38');
      const geometry=await page.evaluate(()=>{
        const q=id=>document.querySelector('[data-r18-construction="'+id+'"]');
        const f=q('ricketts-frankfort');const np=q('ricketts-n-pog');
        return {fX1:f?.getAttribute('x1')||null,npX2:np?.getAttribute('x2')||null};
      });
      if(kind==='ricketts'&&(!geometry.fX1||!geometry.npX2))fail('Ricketts anatomical source overlay missing');
      const scroll=await page.evaluate(()=>({
        documentWidth:document.documentElement.scrollWidth,viewportWidth:document.documentElement.clientWidth
      }));
      if(scroll.documentWidth-scroll.viewportWidth>2)fail('Document horizontal overflow '+JSON.stringify(scroll));
      // Preserve BOTH the actual public radiograph viewport and the table:
      // scrolling mobile to the table must never masquerade as proof of image UX.
      await page.locator('[data-r20-radiograph-stage]').scrollIntoViewIfNeeded();
      const stageFilename=phase.toLowerCase()+'-'+kind+'-'+variant+'-radiograph-'+viewportName+'.png';
      await page.screenshot({path:path.join(out,stageFilename),fullPage:false});
      await panel.scrollIntoViewIfNeeded();
      const filename=phase.toLowerCase()+'-'+kind+'-'+variant+'-'+viewportName+'.png';
      await page.screenshot({path:path.join(out,filename),fullPage:false});
      states.push({kind,variant,rows:count,handles,geometry,scroll,focus:'not-authorized',filename,stageFilename,valid:true});
    }
  }
  await page.locator('#cephalo-ready-analysis').selectOption('com');
  const com=page.locator('[data-r19-analysis-panel="com"]');
  await com.waitFor({state:'attached',timeout:10000});
  const comRows=await com.locator('[data-r19-metric]').count();
  if(comRows!==10)fail('COM legacy regression: '+comRows);
  await page.locator('[data-r20-radiograph-stage]').scrollIntoViewIfNeeded();
  const comStage=phase.toLowerCase()+'-com-legacy-radiograph-'+viewportName+'.png';
  await page.screenshot({path:path.join(out,comStage),fullPage:false});
  await com.scrollIntoViewIfNeeded();
  const comFile=phase.toLowerCase()+'-com-legacy-'+viewportName+'.png';
  await page.screenshot({path:path.join(out,comFile),fullPage:false});
  states.push({kind:'com',variant:'legacy',rows:comRows,filename:comFile,stageFilename:comStage,valid:true});
  const zoomEvidence=g6Audit ? await auditG6ZoomPan(page,v,viewportName) : undefined;
  if(errors.length)fail('Page errors: '+errors.join(' | ').slice(0,1200));
  return{viewportName,decoded,valid:true,states,pageErrors:errors,zoomEvidence};
 }catch(e){
   return{viewportName,valid:false,states,pageErrors:[...errors,String(e)]};
 }finally{await context.close().catch(()=>{});await browser.close().catch(()=>{})}
}
try {
 await waitServer();
 // One browser context per viewport, with a deterministic synthetic fixture.
 for(const v of viewports){
  const first=await capture(v);
  // Vite's first dependency optimization may navigate a page while
  // Chromium decodes the public JPEG. Retry ONLY that transient navigation
  // with a NEW browser context; preserve both attempts in the evidence.
  const navigationRace=!first.valid && first.pageErrors.some(
    error=>error.includes('Execution context was destroyed') &&
      error.includes('navigation')
  );
  const retry=navigationRace ? await capture(v) : null;
  const result=retry ?? first;
  report.viewports.push({
    ...result,
    recoveredTransientNavigation:Boolean(retry?.valid),
    attempts:retry
      ? [{valid:first.valid,errors:first.pageErrors}, {valid:retry.valid,errors:retry.pageErrors}]
      : [{valid:first.valid,errors:first.pageErrors}],
  });
  if(!result.valid)report.invalidCount++;
 }
}finally{
 if(!server.killed)server.kill('SIGTERM');
 await Promise.race([once(server,'exit'),new Promise(resolve=>setTimeout(resolve,3000))]).catch(()=>{});
 await writeFile(path.join(out,'vite.log'),viteLog);
 await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
}
console.log(JSON.stringify({phase,caseId,head,invalid:report.invalidCount,
  captures:report.viewports.map(v=>({viewport:v.viewportName,valid:v.valid,modes:v.states.map(s=>s.kind+'/'+s.variant),errors:v.pageErrors}))},null,2));
if(report.invalidCount || report.blockedRequests.length)process.exitCode=1;
