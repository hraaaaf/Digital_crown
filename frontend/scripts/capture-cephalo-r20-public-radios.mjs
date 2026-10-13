import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
// Public photos are ephemeral CI inputs; synthetic landmarks do not follow actual anatomy.
const radios = {
 anug: {author:'ANUG',year:2014,width:2272,height:1818,sha1:'2a284993c666790a72d0c004044b35a92534ce9d',page:'https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG',original:'https://upload.wikimedia.org/wikipedia/commons/6/66/Cephalometric_radiograph.JPG'},
 challiyan: {author:'Challiyan',year:2023,width:1000,height:1255,sha1:'66c74c588af3c54dfc581f8a870c5276c3427498',page:'https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg',original:'https://upload.wikimedia.org/wikipedia/commons/8/8e/A_lateral_cephalogram_without_true_vertical.jpg'}
};
const caseId=process.env.CEPHALO_PUBLIC_CASE;
if(!caseId||!Object.hasOwn(radios,caseId))throw new Error('Set CEPHALO_PUBLIC_CASE=anug|challiyan');
const radio=radios[caseId];
const bytes=await readFile(path.join(process.cwd(),'public-radio-input',caseId+'.jpg'));
const sha1=createHash('sha1').update(bytes).digest('hex');
if(sha1!==radio.sha1)throw new Error('Wikimedia SHA1 mismatch '+caseId);
const sha256=createHash('sha256').update(bytes).digest('hex');
const radioDataUri='data:image/jpeg;base64,'+bytes.toString('base64');
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR,'cephalo-r20-public-radio-artifacts',caseId);
const PORT = 5195;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const CAPTURE_THEME = 'default';
const viewports = [{ name:'1280x900',width:1280,height:900 }];
const modes = ['all','com'];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { CephaloWorkspace } from './features/ortho/CephaloWorkspace';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import './index.css';

const fixture = ${JSON.stringify(radioDataUri)};
const landmarks = [
{id:'S',x:430,y:370},{id:'N',x:650,y:360},{id:'A',x:690,y:620},{id:'B',x:675,y:790},
{id:'Po',x:390,y:500},{id:'Or',x:650,y:520},{id:'Go',x:430,y:980},{id:'Me',x:680,y:1040},
{id:'Co',x:410,y:430},{id:'Gn',x:690,y:1010},{id:'ANS',x:685,y:610},
{id:'Occ_Ant',x:715,y:760},{id:'Occ_Post',x:500,y:790},
{id:'U1_apex',x:640,y:650},{id:'U1_incisal',x:690,y:770},{id:'L1_apex',x:650,y:900},{id:'L1_incisal',x:700,y:785},
{id:'G_soft',x:720,y:300},{id:'N_soft',x:760,y:355},{id:'Prn',x:835,y:515},{id:'Cm',x:790,y:575},{id:'Sn_soft',x:760,y:610},
{id:'A_soft',x:770,y:650},{id:'Ls_soft',x:805,y:700},{id:'St',x:795,y:755},{id:'Li_soft',x:810,y:805},{id:'B_soft',x:770,y:875},{id:'Pog_soft',x:790,y:965},{id:'Me_soft',x:750,y:1060}
].map(p=>({...p,x:p.x*${radio.width}/1200,y:p.y*${radio.height}/1600}));
// THESE DEMO LANDMARKS ARE SYNTHETIC; NOT ANATOMICALLY REGISTERED.

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
 patientId: 919, patientName: 'DÉMO UX — POINTS FICTIFS', analysisId: 9919, imageSrc: fixture,
 imgDim:{w:${radio.width},h:${radio.height}}, local:{landmarks,version:1}, mmPerPixel:0.2, isCalibrated:true,
 completedSteps:new Set([1]), step:1, anglesData,
 etape3Data:{...useOrthoStore.getState().etape3Data,selectedAnalysis:'COM'}
});
ReactDOM.createRoot(document.getElementById('root')).render(<MemoryRouter><div style={{height:'100vh'}}><CephaloWorkspace patientId={919} patientName="DÉMO UX — POINTS FICTIFS" /></div></MemoryRouter>);
`;
const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Cephalo R20 PUBLIC RADIO UX</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-r20-public-radio-entry.tsx"></script></body></html>`;

function json(body,status=200){return{status,contentType:'application/json',body:JSON.stringify(body)}}
async function waitForServer(url,timeoutMs=30000){const start=Date.now();while(Date.now()-start<timeoutMs){try{const r=await fetch(url);if(r.ok)return}catch{}await new Promise(r=>setTimeout(r,250))}throw new Error(`Vite unavailable ${url}`)}

function modeContract(mode, metrics) {
  if (metrics.analysis !== mode || metrics.panelAnalysis !== mode || !metrics.hasAnalysisSelector || metrics.horizontalOverflow || !metrics.desktopLayoutOk) return false;
  if (metrics.selectorButtons.length !== 6) return false;
  const labels = new Set(metrics.landmarkLabels);
  if (mode === 'all') return metrics.svgLines > 8 && metrics.panelRows >= 10 && metrics.labelModeContract
    && (metrics.landmarkTitleCount===null || metrics.landmarkTitleCount===29)
    && (metrics.labelOverlapCount===null || metrics.labelOverlapCount===0);
  if (mode === 'steiner') return metrics.panelRows === 15 && metrics.svgLines >= 6 && metrics.comConstructionCount === 0 && metrics.rickettsConstructionCount === 0 && metrics.legacyMcNamaraLeakCount === 0;
  if (mode === 'tweed') return metrics.panelRows === 4 && metrics.svgLines >= 6 && metrics.comConstructionCount === 0 && metrics.rickettsConstructionCount === 0 && metrics.legacyMcNamaraLeakCount === 0;
  if (mode === 'mcnamara') return labels.has('McNamara') && labels.has("A'") && labels.has("B'") && metrics.panelRows === 3 && metrics.comConstructionCount === 0;
  if (mode === 'com') return metrics.panelRows === 10 && metrics.comConstructionCount >= 10 && metrics.legacyMcNamaraLeakCount === 0 && labels.has('Po') && labels.has('Or') && labels.has('S') && labels.has('N')
    && (metrics.crossLayerOverlapCount===null || (metrics.overlayLabelCount===3 && metrics.crossLayerOverlapCount===0 && metrics.overlayContrastContract));
  if (mode === 'ricketts') return metrics.panelRows === 2 && metrics.rickettsConstructionCount >= 1 && metrics.comConstructionCount === 0 && metrics.legacyMcNamaraLeakCount === 0;
  return false;
}

await rm(OUTPUT_DIR,{recursive:true,force:true}); await mkdir(OUTPUT_DIR,{recursive:true});
await writeFile(path.join(OUTPUT_DIR,'PUBLIC-SOURCE-LICENSE.json'),JSON.stringify({...radio,caseId,actualSha1:sha1,actualSha256:sha256,license:'CC BY-SA 4.0',licenseUrl:'https://creativecommons.org/licenses/by-sa/4.0/',landmarks:'SYNTHETIC UNREGISTERED NONCLINICAL',screenshots:'Derived composite UX test, preserve Wikimedia author/license/changes'},null,2));
await writeFile(path.join(FRONTEND_DIR,'src','cephalo-r20-public-radio-entry.tsx'),entrySource,'utf8');
await writeFile(path.join(FRONTEND_DIR,'cephalo-r20-public-radio.html'),htmlSource,'utf8');
const viteBin=path.join(FRONTEND_DIR,'node_modules','.bin',process.platform==='win32'?'vite.cmd':'vite');
const server=spawn(viteBin,['--host','127.0.0.1','--port',String(PORT)],{cwd:FRONTEND_DIR,env:{...process.env,BROWSER:'none',VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']});
let serverLog=''; server.stdout.on('data',c=>serverLog+=c); server.stderr.on('data',c=>serverLog+=c);
const captures=[]; const blockedExternalRequests=[];

async function readZoomState(page) {
 return page.evaluate(() => {
  const base=document.querySelector('svg[data-cephalo-viewport="base"]');
  const overlay=document.querySelector('svg[data-cephalo-viewport="analysis"]');
  const image=base?.querySelector('image');
  return {
   percent:document.querySelector('[data-cephalo-zoom-level]')?.textContent?.trim()??null,
   baseViewBox:base?.getAttribute('viewBox')??null,
   overlayViewBox:overlay?.getAttribute('viewBox')??null,
   imageGeometry:image?['x','y','width','height'].map(a=>image.getAttribute(a)).join(','):null,
   crossLayerOverlapCount:(()=>{
     const labels=Array.from(document.querySelectorAll('svg[data-cephalo-viewport="base"] [data-cephalo-landmark-label],svg[data-cephalo-viewport="analysis"] [data-cephalo-overlay-label]'));
     return labels.reduce((count,a,i)=>{
       const x=a.getBoundingClientRect();
       return count+labels.slice(i+1).filter(b=>{
         const y=b.getBoundingClientRect();
         return Math.min(x.right,y.right)-Math.max(x.left,y.left)>1 && Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>1;
       }).length;
     },0);
   })(),
   landmarkCoordinates:Array.from(base?.querySelectorAll('g > title')||[]).map(t=>{
     const marker=t.parentElement?.querySelector('circle[cx][cy]');
     return marker ? [t.textContent,marker.getAttribute('cx'),marker.getAttribute('cy')].join(':') : null;
   }).filter(Boolean).sort().join('|'),
  };
 });
}
const boxValues = value => typeof value==='string' ? value.split(' ').map(Number) : [];

async function captureViewport(viewport,attempt){
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},reducedMotion:'reduce',locale:'fr-FR'});
 const page=await context.newPage();
 const pageErrors=[]; const consoleErrors=[];
 page.on('pageerror',e=>pageErrors.push(e.message)); page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
 await page.route('**/*',async route=>{const req=route.request();const u=new URL(req.url());if(u.hostname==='127.0.0.1'&&u.port===String(PORT))return route.continue();if(u.hostname==='127.0.0.1'&&u.port==='8005'){if(req.method()==='GET'&&u.pathname==='/api/patients/919')return route.fulfill(json({id:919,age:34,sexe:'M'}));return route.fulfill(json({detail:'neutralized'},418));}if(u.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});blockedExternalRequests.push({viewport:viewport.name,attempt,url:req.url()});return route.abort('blockedbyclient')});
 try{
  const response=await page.goto(`${BASE_URL}/cephalo-r20-public-radio.html`,{waitUntil:'domcontentloaded',timeout:30000});
  const theme=await page.evaluate(()=>document.body.dataset.theme||document.documentElement.dataset.theme||'default');
  if(theme!==CAPTURE_THEME) throw new Error(`Unexpected capture theme: ${theme}`);
  await page.getByRole('heading',{name:'Céphalométrie',exact:true}).waitFor({state:'visible',timeout:30000});
  await page.locator('[aria-label="Analyse du tracé"]').waitFor({state:'visible',timeout:10000});
  await page.locator('[data-r19-reference-layout]').waitFor({state:'visible',timeout:10000});
  const decodedImage=await page.evaluate(async()=>{
    const href=document.querySelector('svg[data-cephalo-viewport="base"] image')?.getAttribute('href');
    if(!href?.startsWith('data:image/jpeg;base64,'))throw new Error('Public JPEG not loaded');
    const img=new Image();img.src=href;await img.decode();
    return {width:img.naturalWidth,height:img.naturalHeight};
  });
  if(decodedImage.width!==radio.width||decodedImage.height!==radio.height)throw new Error('Public image natural resolution mismatch');
  // Deliberately added by the isolated test harness, never by application runtime.
  // Make the origin and synthetic measurements unambiguous on every evidence PNG.
  await page.evaluate(({author})=>{
    const label=document.createElement('div');
    label.setAttribute('data-r20-audit-banner','true');
    label.textContent='TEST UX SEUL — RADIO '+author+' (Wikimedia / CC BY-SA 4.0) — REPÈRES, CALIBRATION ET MESURES FICTIFS';
    Object.assign(label.style,{position:'fixed',top:'8px',left:'300px',maxWidth:'570px',
      padding:'5px 8px',borderRadius:'5px',fontFamily:'system-ui',fontSize:'10px',
      fontWeight:'800',background:'#fff9dc',color:'#5e3600',border:'1px solid #b57b00',
      zIndex:'9999',pointerEvents:'none'});
    document.body.append(label);
  },{author:radio.author});

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
    const legacyMcNamaraLeakCount=landmarkLabels.filter(label=>label==='McNamara'||label==="A'"||label==="B'").length;
    const baseSvg=document.querySelector('svg[data-cephalo-viewport="base"]');
    const markerTitles=Array.from(baseSvg?.querySelectorAll('g > title')||[]).filter(t=>t.parentElement?.querySelector('circle[cx][cy]'));
    const compactTexts=Array.from(baseSvg?.querySelectorAll('[data-cephalo-landmark-label]')||[]);
    const comOnlyTexts=Array.from(document.querySelectorAll('svg[data-cephalo-viewport="analysis"] [data-cephalo-overlay-label]'));
    const allLabelNodes=[...compactTexts,...comOnlyTexts];
    const labelHeights=compactTexts.map(n=>n.getBoundingClientRect().height);
    const labelPxHeightMin=labelHeights.length?Math.round(Math.min(...labelHeights)*10)/10:null;
    const labelPxHeightMax=labelHeights.length?Math.round(Math.max(...labelHeights)*10)/10:null;
     const overlayHeights=comOnlyTexts.map(n=>n.getBoundingClientRect().height);
     const overlayPxHeightMin=overlayHeights.length?Math.round(Math.min(...overlayHeights)*10)/10:null;
    const overlayContrastContract=comOnlyTexts.every(text=>
      text.style.paintOrder==='stroke' && text.style.strokeWidth==='4px' && text.style.strokeLinejoin==='round'
    );
    const overlapCount=compactTexts.reduce((count,a,i)=>{
      const x=a.getBoundingClientRect();
      return count+compactTexts.slice(i+1).filter(b=>{
        const y=b.getBoundingClientRect();
        return Math.min(x.right,y.right)-Math.max(x.left,y.left)>1 && Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>1;
      }).length;
    },0);
    const totalOverlapCount=allLabelNodes.reduce((count,a,i)=>{
      const x=a.getBoundingClientRect();
      return count+allLabelNodes.slice(i+1).filter(b=>{
        const y=b.getBoundingClientRect();
        return Math.min(x.right,y.right)-Math.max(x.left,y.left)>1 && Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>1;
      }).length;
    },0);
    const incisal=baseSvg?.querySelector('[data-cephalo-landmark-label="U1_incisal"]');
    const incisalFullId=incisal?.closest('g')?.querySelector('title')?.textContent;
    const labelModeContract=innerWidth>=1280
      ? incisal?.textContent==='U1i' && Number(incisal?.getAttribute('font-size'))>0 && incisal.getBoundingClientRect().height>=12.5 && incisalFullId==='U1_incisal'
      : incisal?.textContent==='U1_incisal' && incisal?.getAttribute('font-size')==='10';
    return {
      analysis:document.querySelector('[data-cephalo-analysis]')?.getAttribute('data-cephalo-analysis')||null,
      panelAnalysis:document.querySelector('[data-r19-analysis-panel]')?.getAttribute('data-r19-analysis-panel')||null,
      hasAnalysisSelector:Boolean(document.querySelector('[aria-label="Analyse du tracé"]')),
      selectorButtons:Array.from(document.querySelectorAll('[aria-label="Analyse du tracé"] button')).map(n=>n.getAttribute('data-analysis')),
      panelRows:document.querySelectorAll('[data-r19-metric]').length,
      svgLines:document.querySelectorAll('svg line').length,
      landmarkLabels,
      landmarkTitleCount:innerWidth>=1280 ? markerTitles.length : null,
      visibleCompactLabelCount:innerWidth>=1280 ? compactTexts.length : null,
      labelPxHeightMin:innerWidth>=1280 ? labelPxHeightMin : null,
      labelPxHeightMax:innerWidth>=1280 ? labelPxHeightMax : null,
      overlayPxHeightMin:innerWidth>=1280 ? overlayPxHeightMin : null,
      labelOverlapCount:innerWidth>=1280 ? overlapCount : null,
      overlayLabelCount:innerWidth>=1280 ? comOnlyTexts.length : null,
      overlayContrastContract:innerWidth>=1280 ? overlayContrastContract : null,
      crossLayerOverlapCount:innerWidth>=1280 ? totalOverlapCount : null,
      labelModeContract,
      rickettsConstructionCount:document.querySelectorAll('[data-r18-construction^="ricketts-"]').length,
      comConstructionCount:document.querySelectorAll('[data-r19-construction^="com-"]').length,
      legacyMcNamaraLeakCount,
      selectedDetail:document.querySelector('[data-r19-measure-detail]')?.getAttribute('data-r19-measure-detail')||null,
      horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1,
      tabsFullyVisible,
      detailContained,
      desktopLayoutOk:innerWidth<1280 || (tabsFullyVisible && detailContained)
    };
   });
   let zoomCheck=null;
   if (viewport.width>=1280 && ['all','steiner','com'].includes(mode)) {
     const initial=await readZoomState(page);
     await page.getByRole('button',{name:'Agrandir la radiographie'}).click();
     await page.getByRole('button',{name:'Agrandir la radiographie'}).click();
     await page.waitForFunction(()=>document.querySelector('[data-cephalo-zoom-level]')?.textContent?.trim()==='150 %',{timeout:3000});
     const enlarged=await readZoomState(page);
     const zoomBox=boxValues(enlarged.baseViewBox);
     const aligned=enlarged.overlayViewBox===null || enlarged.overlayViewBox===enlarged.baseViewBox;
     await page.screenshot({path:path.join(OUTPUT_DIR,`after-zoom-${mode}-${viewport.name}.png`),fullPage:false});
     // Move the displayed crop, not stored points; keep base and COM aligned.
     await page.getByRole('button',{name:'Déplacer la radiographie à droite'}).click();
     await page.getByRole('button',{name:'Déplacer la radiographie vers le bas'}).click();
     const panned=await readZoomState(page);
     const panBox=boxValues(panned.baseViewBox);
     const overlayPanAligned=panned.overlayViewBox===null || panned.overlayViewBox===panned.baseViewBox;
     await page.screenshot({path:path.join(OUTPUT_DIR,`after-pan-${mode}-${viewport.name}.png`),fullPage:false});
     await page.getByRole('button',{name:'Déplacer la radiographie à gauche'}).click();
     await page.getByRole('button',{name:'Déplacer la radiographie vers le haut'}).click();
     const panRestored=await readZoomState(page);
     await page.getByRole('button',{name:'Afficher toute la radiographie'}).click();
     await page.waitForFunction(()=>document.querySelector('[data-cephalo-zoom-level]')?.textContent?.trim()==='100 %',{timeout:3000});
     const restored=await readZoomState(page);
     zoomCheck={valid:initial.percent==='100 %' && initial.baseViewBox===`0 0 ${radio.width} ${radio.height}`
       && enlarged.percent==='150 %' && zoomBox.length===4 && zoomBox.every(Number.isFinite)
       && Math.abs(zoomBox[2]-(radio.width/1.5))<0.01 && Math.abs(zoomBox[3]-(radio.height/1.5))<0.01
       && aligned && (mode==='steiner'||enlarged.overlayViewBox!==null)
       && (mode!=='com' || (enlarged.crossLayerOverlapCount===0 && panned.crossLayerOverlapCount===0))
       && initial.imageGeometry===enlarged.imageGeometry && enlarged.imageGeometry===restored.imageGeometry
       && panBox.length===4 && panBox[0]>zoomBox[0] && panBox[1]>zoomBox[1]
       && panBox[0]>=0 && panBox[1]>=0
       && panBox[0]+panBox[2]<=radio.width+.001 && panBox[1]+panBox[3]<=radio.height+.001
       && overlayPanAligned && panned.imageGeometry===enlarged.imageGeometry
       && initial.landmarkCoordinates===enlarged.landmarkCoordinates
       && initial.landmarkCoordinates===panned.landmarkCoordinates
       && initial.landmarkCoordinates===panRestored.landmarkCoordinates
       && initial.landmarkCoordinates===restored.landmarkCoordinates
       && panRestored.baseViewBox===enlarged.baseViewBox && panRestored.overlayViewBox===enlarged.overlayViewBox
       && restored.baseViewBox===initial.baseViewBox && restored.overlayViewBox===initial.overlayViewBox,
       initial,enlarged,panned,panRestored,restored};
   }
   const valid=(metrics.labelPxHeightMin===null||metrics.labelPxHeightMin>=12.5) && (metrics.overlayPxHeightMin===null||metrics.overlayPxHeightMin>=12.5) && modeContract(mode,metrics) && (mode!=='com'||metrics.selectedDetail==='I_Francfort') && (zoomCheck===null||zoomCheck.valid);
   await page.screenshot({path:path.join(OUTPUT_DIR,`after-reference-${mode}-${viewport.name}.png`),fullPage:false});
   if(mode==='com'){
     await page.locator('[data-r19-analysis-panel="com"]').scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(OUTPUT_DIR,`after-com-panel-${viewport.name}.png`),fullPage:false});
   }
   states.push({mode,valid,metrics,zoomCheck});
  }
  const valid=response?.status()===200&&!pageErrors.length&&!consoleErrors.length&&states.every(s=>s.valid)&&selectorChecks.length===3&&selectorChecks.every(s=>s.valid);
  return {viewport:viewport.name,attempt,valid,pageErrors,consoleErrors,decodedImage,selectorChecks,states};
 }catch(error){return{viewport:viewport.name,attempt,valid:false,pageErrors:[...pageErrors,error instanceof Error?error.message:String(error)],consoleErrors,states:[]}}
 finally{await context.close().catch(()=>{});await browser.close().catch(()=>{})}
}

try{
 await waitForServer(`${BASE_URL}/cephalo-r20-public-radio.html`);
 for(const viewport of viewports){
  const attempts=[await captureViewport(viewport,1)];
  if(!attempts[0].valid)attempts.push(await captureViewport(viewport,2));
  const finalAttempt=attempts.at(-1);
  captures.push({...finalAttempt,attempts:attempts.map(a=>({attempt:a.attempt,valid:a.valid,pageErrors:a.pageErrors,consoleErrors:a.consoleErrors,states:a.states})),recoveredTransientRender:attempts.length===2&&!attempts[0].valid&&attempts[1].valid});
 }
}finally{if(!server.killed)server.kill('SIGTERM');await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{});await writeFile(path.join(OUTPUT_DIR,'vite.log'),serverLog,'utf8')}
const invalid=captures.filter(c=>!c.valid); const report={lot:'CEPHALO-R20-PUBLIC-RADIO-UX',caseId,provenance:{...radio,sha1,sha256,landmarks:'SYNTHETIC UNREGISTERED'},phase:'AFTER',theme:CAPTURE_THEME,productHead:PRODUCT_HEAD,viewports:viewports.map(v=>v.name),modes,capturePolicy:'EXPERIMENTAL 1280x900: two attributed Wikimedia original radiographs with simulated nonclinical landmarks, 100/150/pan all/COM, no anatomical registration or clinical proof.',captures,blockedExternalRequests,invalidCount:invalid.length};
await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8'); console.log(JSON.stringify(report,null,2)); if(invalid.length||blockedExternalRequests.length)process.exitCode=1;