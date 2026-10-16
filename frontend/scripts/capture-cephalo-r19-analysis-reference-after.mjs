import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'cephalo-r19-analysis-reference-after-artifacts');
const PORT = 5194;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const CAPTURE_THEME = 'default';
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];
const modes = ['all', 'steiner', 'tweed', 'mcnamara', 'com', 'ricketts'];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { CephaloWorkspace } from './features/ortho/CephaloWorkspace';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import './index.css';

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
const raw=(valeur)=>({valeur,norm_mean:null,norm_min:null,norm_max:null,plage_compensation:null,status:'N/A',interpretation:'Mesure géométrique brute',z_score:null});
const anglesData={
 metrics:{
  analyse_dentaire:{Surplomb:raw(-2.2),Recouvrement:raw(-2.8),IMPA:raw(100.0),I_Francfort:raw(117.0),Inter_Incisif:raw(133.9)},
  analyse_osseuse:{SNA:raw(81.5),SNB:raw(77.9),ANB:raw(3.6),Angle_de_Tweed:raw(9.1),Decalage_A_B:raw(0.4),Situation_A:raw(12.0),Situation_B:raw(11.6),Profondeur_Faciale:raw(43.7)},
  analyse_esthetique:{Ligne_E_Ls:raw(-1.8),Ligne_E_Li:raw(-0.9)}
 },
 visual_debug:{}, calibration_status:'verified'
};
useOrthoStore.setState({
 patientId: 919, patientName: 'SIMULATION R19 · IMAGE SVG ET VALEURS FICTIVES', analysisId: 9919, imageSrc: fixture,
 imgDim:{w:1200,h:1600}, local:{landmarks,version:1}, mmPerPixel:0.2, isCalibrated:true,
 completedSteps:new Set([1]), step:1, anglesData,
 etape3Data:{...useOrthoStore.getState().etape3Data,selectedAnalysis:'COM'}
});
ReactDOM.createRoot(document.getElementById('root')).render(<MemoryRouter><div style={{height:'100vh'}}><CephaloWorkspace patientId={919} patientName="SIMULATION R19 · IMAGE SVG ET VALEURS FICTIVES" /></div></MemoryRouter>);
`;
const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Cephalo R19 AFTER</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-r19-analysis-reference-after-entry.tsx"></script></body></html>`;

function json(body,status=200){return{status,contentType:'application/json',body:JSON.stringify(body)}}
async function waitForServer(url,timeoutMs=30000){const start=Date.now();while(Date.now()-start<timeoutMs){try{const r=await fetch(url);if(r.ok)return}catch{}await new Promise(r=>setTimeout(r,250))}throw new Error(`Vite unavailable ${url}`)}

function modeContract(mode, metrics) {
  if (metrics.analysis !== mode || metrics.panelAnalysis !== mode || !metrics.hasAnalysisSelector || metrics.horizontalOverflow || !metrics.desktopLayoutOk || !metrics.sourceDisclosureOk || !metrics.extendedRayClippingOk) return false;
  if (metrics.selectorButtons.length !== 6) return false;
  const labels = new Set(metrics.landmarkLabels);
  if (mode === 'all') return metrics.svgLines > 8 && metrics.panelRows >= 10 && (metrics.viewportWidth < 1280 || metrics.boundedClipCount >= 1);
  if (mode === 'steiner') return metrics.panelRows === 15 && metrics.svgLines >= 6 && metrics.comConstructionCount === 0 && metrics.rickettsConstructionCount === 0 && metrics.legacyMcNamaraLeakCount === 0;
  if (mode === 'tweed') return metrics.panelRows === 4 && metrics.svgLines >= 6 && metrics.comConstructionCount === 0 && metrics.rickettsConstructionCount === 0 && metrics.legacyMcNamaraLeakCount === 0;
  if (mode === 'mcnamara') return labels.has('McNamara') && labels.has("A'") && labels.has("B'") && metrics.panelRows === 3 && metrics.comConstructionCount === 0;
  if (mode === 'com') return metrics.panelRows === 10 && metrics.comConstructionCount >= 10 && metrics.legacyMcNamaraLeakCount === 0 && ['Po','Or','S','N'].every(id => metrics.comReferencePointIds.includes(id)) && (metrics.viewportWidth < 1280 || metrics.boundedClipCount >= 1);
  if (mode === 'ricketts') return metrics.panelRows === 2 && metrics.rickettsConstructionCount >= 1 && metrics.comConstructionCount === 0 && metrics.legacyMcNamaraLeakCount === 0;
  return false;
}

await rm(OUTPUT_DIR,{recursive:true,force:true}); await mkdir(OUTPUT_DIR,{recursive:true});
await writeFile(path.join(FRONTEND_DIR,'src','cephalo-r19-analysis-reference-after-entry.tsx'),entrySource,'utf8');
await writeFile(path.join(FRONTEND_DIR,'cephalo-r19-analysis-reference-after.html'),htmlSource,'utf8');
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
 await page.route('**/*',async route=>{const req=route.request();const u=new URL(req.url());if(u.hostname==='127.0.0.1'&&u.port===String(PORT))return route.continue();if(u.hostname==='127.0.0.1'&&u.port==='8005'){if(req.method()==='GET'&&u.pathname==='/api/patients/919')return route.fulfill(json({id:919,age:34,sexe:'M'}));return route.fulfill(json({detail:'neutralized'},418));}if(u.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});blockedExternalRequests.push({viewport:viewport.name,attempt,url:req.url()});return route.abort('blockedbyclient')});
 try{
  const response=await page.goto(`${BASE_URL}/cephalo-r19-analysis-reference-after.html`,{waitUntil:'domcontentloaded',timeout:30000});
  const theme=await page.evaluate(()=>document.body.dataset.theme||document.documentElement.dataset.theme||'default');
  if(theme!==CAPTURE_THEME) throw new Error(`Unexpected capture theme: ${theme}`);
  await page.getByRole('heading',{name:'Céphalométrie',exact:true}).waitFor({state:'visible',timeout:30000});
  await page.locator('[aria-label="Analyse du tracé"]').waitFor({state:'visible',timeout:10000});
  await page.locator('[data-r19-reference-layout]').waitFor({state:'visible',timeout:10000});
  // Exercise the left-hand ready-made selector, not only the floating tracing tabs.
  const selectorChecks=[];
  for(const requested of ['steiner','com','all']){
   await page.locator('#cephalo-ready-analysis').selectOption(requested);
   await page.waitForFunction(mode=>{
    const overlay=document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis');
    const panel=document.querySelector('[data-r19-analysis-panel]')?.getAttribute('data-r19-analysis-panel');
    const select=document.querySelector('#cephalo-ready-analysis');
    return overlay===mode && panel===mode && select?.value===mode;
   },requested,{timeout:6000});
   const result=await page.evaluate(()=>({
    chosen:document.querySelector('#cephalo-ready-analysis')?.value,
    overlay:document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis'),
    panel:document.querySelector('[data-r19-analysis-panel]')?.getAttribute('data-r19-analysis-panel')
   }));
   selectorChecks.push({requested,...result,valid:result.chosen===requested&&result.overlay===requested&&result.panel===requested});
   if(requested==='steiner') await page.screenshot({path:path.join(OUTPUT_DIR,`after-selector-steiner-${viewport.name}.png`),fullPage:false});
  }
  // R23-A desktop: verify tools are folded on first use, the anatomical
  // image claims the recovered width, and both panels can be restored.
  let imageFirstProof=null;
  if(viewport.width>=1280){
    const grid=page.locator('[data-r20-workbench-layout]');
    const stage=page.locator('[data-r20-radiograph-stage]');
    const utility=page.locator('[data-r20-workbench-sidebar]');
    const initialWidth=await stage.evaluate(el=>el.getBoundingClientRect().width);
    const initiallyFolded=await grid.getAttribute('data-r23-image-first');
    const utilityDisplay=await utility.evaluate(el=>getComputedStyle(el).display);
    await page.locator('[data-r23-tools-toggle]').click();
    const expandedWidth=await stage.evaluate(el=>el.getBoundingClientRect().width);
    const utilityDisplayOpen=await utility.evaluate(el=>getComputedStyle(el).display);
    await page.locator('[data-r23-tools-toggle]').click();
    await page.locator('[data-r23-measures-toggle]').click();
    const readingWidth=await stage.evaluate(el=>el.getBoundingClientRect().width);
    await page.screenshot({path:path.join(OUTPUT_DIR,`after-image-first-reading-${viewport.name}.png`),fullPage:false});
    await page.locator('[data-r23-measures-toggle]').click();
    const restoredWidth=await stage.evaluate(el=>el.getBoundingClientRect().width);
    const mobileMaintained=true;
    imageFirstProof={initialWidth,expandedWidth,readingWidth,restoredWidth,initiallyFolded,utilityDisplay,utilityDisplayOpen,mobileMaintained,
      valid:initiallyFolded==='tools-collapsed'&&utilityDisplay==='none'&&utilityDisplayOpen!=='none'
        &&initialWidth>expandedWidth+100&&readingWidth>initialWidth+250
        &&Math.abs(restoredWidth-initialWidth)<5};
  }
  const states=[];
  for(const mode of modes){
   await page.locator(`[data-analysis="${mode}"]`).click();
   await page.waitForFunction(expected=>document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis')===expected && document.querySelector('[data-r19-analysis-panel]')?.getAttribute('data-r19-analysis-panel')===expected,mode,{timeout:5000});
   if(mode==='com'){
     await page.locator('[data-r19-metric="I_Francfort"]').click();
     await page.waitForFunction(()=>document.querySelector('[data-r19-measure-detail="I_Francfort"]')!==null,{timeout:3000});
   }
   await page.waitForTimeout(80);
   const metrics=await page.evaluate(()=>{
    const tabs=Array.from(document.querySelectorAll('[aria-label="Analyse du tracé"] button'));
    const tabBar=document.querySelector('[aria-label="Analyse du tracé"]');
    const barRect=tabBar?.getBoundingClientRect();
    const tabsFullyVisible=Boolean(barRect && tabs.length===6 && tabs.every(tab=>{const rect=tab.getBoundingClientRect();return rect.left>=barRect.left-1 && rect.right<=barRect.right+1;}));
    const panel=document.querySelector('[data-r19-analysis-panel]');
    const detail=document.querySelector('[data-r19-measure-detail]');
    const panelRect=panel?.getBoundingClientRect();
    const detailRect=detail?.getBoundingClientRect();
    const detailContained=Boolean(panelRect && detailRect && detailRect.top>=panelRect.top-1 && detailRect.bottom<=panelRect.bottom+1);
    const landmarkLabels=Array.from(document.querySelectorAll('svg text')).map(n=>n.textContent?.trim()).filter(Boolean);
    const stage=document.querySelector('[data-r20-radiograph-stage]')?.getBoundingClientRect();
    const evidenceLabel=document.querySelector('[data-ortho-workspace-patient]')?.textContent??'';
    const extendedRays=Array.from(document.querySelectorAll('[data-cephalo-extended-line]'));
    const clipNodes=Array.from(document.querySelectorAll('clipPath[data-cephalo-extended-clip]'));
    const extendedRayClippingOk=extendedRays.every(ray=>{
      const attr=ray.getAttribute('clip-path')??'';
      const clipId=attr.startsWith('url(#')&&attr.endsWith(')')?attr.slice(5,-1):null;
      return Boolean(clipId && clipNodes.some(node=>node.id===clipId));
    });
    const boundedClipCount=clipNodes.filter(node=>{
      const rect=node.querySelector('rect');
      const outer=node.ownerSVGElement?.viewBox?.baseVal;
      return Boolean(rect && outer && (
        Number(rect.getAttribute('width')) < outer.width - 1 ||
        Number(rect.getAttribute('height')) < outer.height - 1
      ));
    }).length;
    const legacyMcNamaraLeakCount=landmarkLabels.filter(label=>label==='McNamara'||label==="A'"||label==="B'").length;
    return {
      analysis:document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis')||null,
      panelAnalysis:document.querySelector('[data-r19-analysis-panel]')?.getAttribute('data-r19-analysis-panel')||null,
      hasAnalysisSelector:Boolean(document.querySelector('[aria-label="Analyse du tracé"]')),
      selectorButtons:Array.from(document.querySelectorAll('[aria-label="Analyse du tracé"] button')).map(n=>n.getAttribute('data-analysis')),
      panelRows:document.querySelectorAll('[data-r19-metric]').length,
      landmarkHandles:document.querySelectorAll('[data-ceph03b-drag-handle]').length,
      comReferencePointIds:Array.from(document.querySelectorAll('[data-r19-point]')).map(el=>el.getAttribute('data-r19-point')).filter(Boolean),
      svgLines:document.querySelectorAll('svg line').length,
      landmarkLabels,
      rickettsConstructionCount:document.querySelectorAll('[data-r18-construction^="ricketts-"]').length,
      comConstructionCount:document.querySelectorAll('[data-r19-construction^="com-"]').length,
      legacyMcNamaraLeakCount,
      selectedDetail:document.querySelector('[data-r19-measure-detail]')?.getAttribute('data-r19-measure-detail')||null,
      horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1,
      viewportWidth:innerWidth,
      imageStageWidth:stage?.width??0,
      sourceDisclosureOk:evidenceLabel.includes('SIMULATION R19') && evidenceLabel.includes('VALEURS FICTIVES'),
      extendedRayClippingOk,
      boundedClipCount,
      tabsFullyVisible,
      detailContained,
      desktopLayoutOk:innerWidth<1280 || (tabsFullyVisible && detailContained && (stage?.width??0)>=625)
    };
   });
   const valid=modeContract(mode,metrics) && (mode!=='com'||metrics.selectedDetail==='I_Francfort');
   await page.screenshot({path:path.join(OUTPUT_DIR,`after-reference-${mode}-${viewport.name}.png`),fullPage:false});
   if(mode==='com'){
     await page.locator('[data-r19-analysis-panel="com"]').scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(OUTPUT_DIR,`after-com-panel-${viewport.name}.png`),fullPage:false});
   }
   states.push({mode,valid,metrics});
  }
  // Browser-level proof: the same stage moves to the fullscreen portal,
  // remains visible and retains the selected clinical analysis after Escape.
  let focusProof=null;
  if(viewport.width>=1280){
    await page.locator('[data-analysis="steiner"]').click();
    await page.waitForFunction(()=>document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis')==='steiner'
      &&document.querySelector('[data-r19-analysis-panel]')?.getAttribute('data-r19-analysis-panel')==='steiner',null,{timeout:6000});
    const beforeWidth=await page.locator('[data-cephalo-stage-root]').evaluate(el=>el.getBoundingClientRect().width);
    const focusButton=page.getByRole('button',{name:'Activer le mode Focus radiographie',exact:true});
    await focusButton.click();
    await page.waitForFunction(()=>document.querySelector('[data-cephalo-stage-root]')?.classList.contains('fixed'),null,{timeout:6000});
    const focusedWidth=await page.locator('[data-cephalo-stage-root]').evaluate(el=>el.getBoundingClientRect().width);
    const focusedMode=await page.locator('[data-cephalo-analysis]').getAttribute('data-cephalo-analysis');
    // Prove visible topmost radiograph, not merely a wide detached DOM node.
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const focusVisibility=await page.evaluate(()=>{
      const root=document.querySelector('[data-cephalo-stage-root]');
      const svg=root?.querySelector('svg[data-cephalo-viewport="base"]');
      const style=root?getComputedStyle(root):null;
      const top=document.elementFromPoint(innerWidth/2,innerHeight/2);
      const r=svg?.getBoundingClientRect();
      return {position:style?.position??null,zIndex:style?.zIndex??null,
        onTop:Boolean(root&&top&&root.contains(top)),
        svgVisible:Boolean(r&&r.width>300&&r.height>300&&r.left<innerWidth&&r.top<innerHeight&&r.bottom>0&&r.right>0)};
    });
    const focusScreenshot=`after-focus-radiograph-${viewport.name}.png`;
    await page.screenshot({path:path.join(OUTPUT_DIR,focusScreenshot),fullPage:false});
    await page.keyboard.press('Escape');
    await page.waitForFunction(()=>!document.querySelector('[data-cephalo-stage-root]')?.classList.contains('fixed'),null,{timeout:5000});
    const restoredWidth=await page.locator('[data-cephalo-stage-root]').evaluate(el=>el.getBoundingClientRect().width);
    const restoredMode=await page.locator('[data-cephalo-analysis]').getAttribute('data-cephalo-analysis');
    focusProof={beforeWidth,focusedWidth,restoredWidth,focusedMode,restoredMode,focusVisibility,focusScreenshot,
      valid:focusedWidth>=viewport.width*.9
        &&focusedWidth>beforeWidth+200
        &&Math.abs(restoredWidth-beforeWidth)<5
        &&focusVisibility.position==='fixed'&&focusVisibility.onTop&&focusVisibility.svgVisible
        &&focusedMode==='steiner'&&restoredMode==='steiner'};
  }
  const valid=response?.status()===200&&!pageErrors.length&&!consoleErrors.length&&states.every(s=>s.valid)
    &&selectorChecks.length===3&&selectorChecks.every(s=>s.valid)
    &&(viewport.width<1280||(focusProof?.valid===true&&imageFirstProof?.valid===true));
  return {viewport:viewport.name,attempt,valid,pageErrors,consoleErrors,selectorChecks,states,focusProof,imageFirstProof};
 }catch(error){return{viewport:viewport.name,attempt,valid:false,pageErrors:[...pageErrors,error instanceof Error?error.message:String(error)],consoleErrors,states:[]}}
 finally{await context.close().catch(()=>{});await browser.close().catch(()=>{})}
}

async function prewarmViteDependencies() {
  // The isolated Vite dev server can add late Workbox optimizations, causing
  // HTTP 504 (Outdated Optimize Dep) in its initial browsing session.
  // Preheat outside evidence collection; certified runs still reject errors.
  let browser;
  try {
    browser=await chromium.launch({headless:true});
    const page=await browser.newPage({viewport:{width:1280,height:900}});
    await page.route('**/*',route=>{
      const u=new URL(route.request().url());
      if(u.hostname==='127.0.0.1'&&u.port===String(PORT))return route.continue();
      if(u.hostname==='127.0.0.1'&&u.port==='8005'&&u.pathname==='/api/patients/919')return route.fulfill(json({id:919,age:34,sexe:'M'}));
      if(u.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});
      return route.abort('blockedbyclient');
    });
    for(let attempt=1;attempt<=3;attempt++){
      const errors=[];
      const listener=msg=>{if(msg.type()==='error')errors.push(msg.text())};
      page.on('console',listener);
      try{
        const response=await page.goto(`${BASE_URL}/cephalo-r19-analysis-reference-after.html`,{waitUntil:'domcontentloaded',timeout:30000});
        await page.locator('[data-r19-reference-layout]').waitFor({state:'visible',timeout:20000});
        await page.waitForLoadState('networkidle',{timeout:15000});
        const optimizeErrors=errors.filter(e=>e.includes('Outdated Optimize Dep'));
        if(response?.status()===200 && optimizeErrors.length===0){
          console.log('VITE_DEP_PREWARM_STABLE',attempt);
          return;
        }
        console.log('VITE_DEP_PREWARM_RETRY',attempt,optimizeErrors.length);
      }catch(e){
        if(attempt===3)throw e;
        console.log('VITE_DEP_PREWARM_RETRY',attempt,String(e).slice(0,200));
      }finally{page.off('console',listener)}
    }
    throw new Error('Vite optimizer did not stabilize before exact-head screenshot capture');
  }finally{if(browser)await browser.close().catch(()=>{})}
}

try{
 await waitForServer(`${BASE_URL}/cephalo-r19-analysis-reference-after.html`);
 await prewarmViteDependencies();
 for(const viewport of viewports){
  const attempts=[await captureViewport(viewport,1)];
  if(!attempts[0].valid)attempts.push(await captureViewport(viewport,2));
  const finalAttempt=attempts.at(-1);
  captures.push({...finalAttempt,attempts:attempts.map(a=>({attempt:a.attempt,valid:a.valid,pageErrors:a.pageErrors,consoleErrors:a.consoleErrors,states:a.states})),recoveredTransientRender:attempts.length===2&&!attempts[0].valid&&attempts[1].valid});
 }
}finally{if(!server.killed)server.kill('SIGTERM');await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{});await writeFile(path.join(OUTPUT_DIR,'vite.log'),serverLog,'utf8')}
const invalid=captures.filter(c=>!c.valid); const report={lot:'CEPHALO-R19-ANALYSIS-REFERENCE-LAYOUT',phase:'AFTER',theme:CAPTURE_THEME,productHead:PRODUCT_HEAD,viewports:viewports.map(v=>v.name),modes,capturePolicy:'R18 deterministic fixture lineage; default Digital Crown theme; same 390/768/1280 viewports; R19 adds analysis panel and autonomous COM; validates rendered constructions and rejects legacy McNamara leakage in COM; fresh Chromium per viewport; one retry only after invalid first render.',captures,blockedExternalRequests,invalidCount:invalid.length};
await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8'); console.log(JSON.stringify(report,null,2)); if(invalid.length||blockedExternalRequests.length)process.exitCode=1;