import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'connect-hub-e-after-artifacts');
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { useAuthStore } from './stores/useAuthStore';
import { useSettingsStore } from './features/admin/Settings/hooks/useSettingsStore';
import './index.css';
useAuthStore.setState({ user: { id:'101', email:'demo@digitalcrown.local', role:'ADMIN', nom_complet:'Dr. Démo', employer_id:null, is_licensed:true }, isAuthenticated:true, isLoading:false });
useSettingsStore.setState({ activeCabinetId:'demo', cabinets:[{ id:'demo', nom:'Cabinet Démo', specialty:'Chirurgien Dentiste', primary_color:'#003380', accent_color:'#60a5fa', theme:'elite', caisse:0 }], profile:{ ...useSettingsStore.getState().profile, nom:'Dr. Démo', font_fr:'inter' } });
localStorage.setItem('active_cabinet_id','demo');
ReactDOM.createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/dashboard']}><div className="flex h-screen overflow-hidden bg-medical-pearl text-text-main"><Sidebar/><div className="relative min-w-0 flex-1 overflow-hidden"><Header/><main className="h-[calc(100vh-5rem)] p-3 sm:p-4 lg:p-8"><section className="h-full rounded-elite border border-border-main bg-card-bg/80 p-5 shadow-elite"><p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Tableau de bord</p><h1 className="mt-2 text-2xl font-black">Cabinet Démo</h1><p className="mt-2 text-sm font-semibold text-text-muted">LOT E — Connect Hub</p></section></main></div></div></MemoryRouter>);
`;
const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Connect Hub E AFTER</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/connect-hub-e-after-entry.tsx"></script></body></html>`;
const json = (body, status=200) => ({ status, contentType:'application/json', body:JSON.stringify(body) });
const viteBin = path.join(FRONTEND_DIR,'node_modules','.bin',process.platform==='win32'?'vite.cmd':'vite');

async function waitForServer(url){ for(let i=0;i<120;i++){ try{const r=await fetch(url);if(r.ok)return;}catch{} await new Promise(r=>setTimeout(r,250)); } throw new Error('Vite unavailable'); }
async function startServer(port){ await rm(path.join(FRONTEND_DIR,'node_modules','.vite'),{recursive:true,force:true}); const server=spawn(viteBin,['--host','127.0.0.1','--port',String(port),'--force'],{cwd:FRONTEND_DIR,env:{...process.env,BROWSER:'none',VITE_API_URL:'http://127.0.0.1:8005'},stdio:['ignore','pipe','pipe']}); await waitForServer(`http://127.0.0.1:${port}/connect-hub-e-after.html`); return {server,baseUrl:`http://127.0.0.1:${port}`}; }
async function stopServer(server){ if(!server.killed)server.kill('SIGTERM'); await Promise.race([once(server,'exit'),new Promise(r=>setTimeout(r,3000))]).catch(()=>{}); }

await rm(OUTPUT_DIR,{recursive:true,force:true}); await mkdir(OUTPUT_DIR,{recursive:true});
await writeFile(path.join(FRONTEND_DIR,'src','connect-hub-e-after-entry.tsx'),entrySource,'utf8'); await writeFile(path.join(FRONTEND_DIR,'connect-hub-e-after.html'),htmlSource,'utf8');
const captures=[]; const blockedExternalRequests=[];
const fixture={total:2,requires_attention:2,delivery_semantics:'source_state_only',items:[{id:'alert:901',source:'proactive_alert',category:'attention',title:'Contrôle patient à planifier',message:'Le contrôle de Sara El Mansouri nécessite votre attention.',patient_id:901,patient_name:'El Mansouri Sara',priority:'high',action:'Ouvrir le dossier',destination:'/dashboard',channel:'in_app',delivery_state:'source_state',delivery_verified:false},{id:'treasury:pending',source:'treasury_hub',category:'attention',title:'Relances de trésorerie',message:'3 dossier(s) à encaisser',patient_id:null,patient_name:null,priority:'high',action:'Ouvrir la trésorerie',destination:'/accounting?tab=treasury',channel:'in_app',delivery_state:'source_state',delivery_verified:false,meta:{pending_count:3,proactive_count:1}}]};

async function capture(viewport,index){ const port=5217+index; const {server,baseUrl}=await startServer(port); const browser=await chromium.launch({headless:true}); const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},reducedMotion:'reduce',locale:'fr-FR'}); const page=await context.newPage(); const pageErrors=[]; const consoleErrors=[]; page.on('pageerror',e=>pageErrors.push(e.message)); page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
 await page.route('**/*',async route=>{const req=route.request();const url=new URL(req.url());if(url.hostname==='127.0.0.1'&&url.port===String(port))return route.continue();if(url.hostname==='127.0.0.1'&&url.port==='8005'){if(url.pathname==='/api/clinics/me')return route.fulfill(json({nom_cabinet:'Cabinet Démo',nom_praticien:'Dr. Démo',header_lines_fr:['Dr. Démo','Chirurgien Dentiste']}));if(url.pathname==='/api/intelligence/connect-hub')return route.fulfill(json(fixture));if(url.pathname==='/api/intelligence/alerts/today')return route.fulfill(json([]));return route.fulfill(json({detail:'Neutralisé AFTER'},418));}if(url.hostname==='fonts.googleapis.com'||url.hostname==='fonts.gstatic.com')return route.fulfill({status:200,contentType:'text/css',body:'/* offline */'});blockedExternalRequests.push({viewport:viewport.name,url:req.url(),method:req.method()});return route.abort('blockedbyclient');});
 try{const response=await page.goto(`${baseUrl}/connect-hub-e-after.html`,{waitUntil:'networkidle',timeout:30000});await page.locator('header').waitFor({state:'visible'});await page.waitForTimeout(250);const closed=await page.evaluate(()=>({innerWidth,scrollWidth:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth),bellCount:document.querySelectorAll('header button svg.lucide-bell').length,hasCenter:(document.body.textContent||'').includes("Centre d’attention")}));await page.screenshot({path:path.join(OUTPUT_DIR,`after-shell-${viewport.name}.png`)});const bell=page.locator('header button').filter({has:page.locator('svg.lucide-bell')}).first();await bell.click();await page.getByText("Centre d’attention",{exact:true}).waitFor({state:'visible'});const open=await page.evaluate(()=>({innerWidth,scrollWidth:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth),hasCenter:(document.body.textContent||'').includes("Centre d’attention"),hasClinical:(document.body.textContent||'').includes('Contrôle patient à planifier'),hasTreasury:(document.body.textContent||'').includes('Relances de trésorerie'),hasTruth:(document.body.textContent||'').includes('aucune livraison externe déduite')}));await page.screenshot({path:path.join(OUTPUT_DIR,`after-bell-open-${viewport.name}.png`)});const valid=response?.status()===200&&!pageErrors.length&&!consoleErrors.length&&closed.bellCount===1&&!closed.hasCenter&&open.hasCenter&&open.hasClinical&&open.hasTreasury&&open.hasTruth&&closed.scrollWidth<=closed.innerWidth+1&&open.scrollWidth<=open.innerWidth+1;return{viewport:viewport.name,httpStatus:response?.status()??null,pageErrors,consoleErrors,closed,open,valid};}catch(error){return{viewport:viewport.name,pageErrors:[...pageErrors,error instanceof Error?error.message:String(error)],consoleErrors,valid:false};}finally{await context.close().catch(()=>{});await browser.close().catch(()=>{});await stopServer(server);}}
for(const [i,v] of viewports.entries())captures.push(await capture(v,i));
const invalid=captures.filter(c=>!c.valid);const report={lot:'LOT-E-CONNECT-HUB',phase:'AFTER',productHead:PRODUCT_HEAD,viewports:viewports.map(v=>v.name),fixturePolicy:'Production Header + Sidebar on exact LOT E HEAD; deterministic canonical Connect Hub read-model fixture; no target UI injected; external egress blocked.',captures,blockedExternalRequests,invalidCount:invalid.length};await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8');console.log(JSON.stringify(report,null,2));if(invalid.length||blockedExternalRequests.length)process.exitCode=1;
