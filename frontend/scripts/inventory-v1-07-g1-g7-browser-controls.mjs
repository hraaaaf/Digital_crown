import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const out=path.resolve('../artifacts/v1-07-g1-g7-browser-inventory');
fs.mkdirSync(out,{recursive:true});
const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('browser inventory login failed');
const tokens=await login.json();
const auth={access:tokens.access_token,refresh:tokens.refresh_token};
const patients=await api.get('/api/patients',{headers:{Authorization:'Bearer '+tokens.access_token}});
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001');

const publicPages=[
 ['g1-landing','/landing'],['g1-login','/login'],['g1-register','/register'],
 ['g1-download','/download'],['g1-activate','/activate']
];
const protectedPages=[
 ['g2-dashboard','/dashboard'],['g2-patients','/patients'],['g2-patient-create','/patients/new'],
 ['g3-agenda','/agenda'],['g5-settings','/settings'],['g6-super-admin','/super-admin'],
 ['g7-stock','/stock'],['g7-marketplace','/approvisionnement'],
 ['g7-library','/bibliotheque'],['g7-science-hub','/science-hub']
];
if(patient){
 protectedPages.push(['g2-patient-overview','/patients/'+patient.id],['g2-patient-edit','/patients/'+patient.id+'/edit']);
}
const settingsTabs=['Profil Cabinet','Design & Ambiance','Catalogue Actes','Horaires & Agenda','Performance & Assistance','Sécurité & Backup','Mon Équipe'];
const viewports=[{width:390,height:844},{width:1280,height:900}];
const base='http://127.0.0.1:5173';
const browser=await chromium.launch({headless:true});
const evidence=[];

function slug(v){return v.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');}
async function seed(page){await page.addInitScript(v=>{localStorage.setItem('token',v.access);localStorage.setItem('refresh_token',v.refresh||'');localStorage.setItem('appMode','prod');},auth);}
async function snapshot(page,surface,viewport){
 await page.waitForTimeout(250);
 const controls=await page.evaluate(()=>{
  const q='button,input,select,textarea,a[href],summary,[contenteditable="true"],[role="button"],[role="switch"],[role="tab"],[role="checkbox"],[role="radio"],[role="menuitem"],[role="option"],[role="slider"],[role="combobox"],[tabindex]:not([tabindex="-1"])';
  const vis=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity||1)>0&&r.width>0&&r.height>0;};
  const label=e=>e.getAttribute('aria-label')||e.textContent?.replace(/\s+/g,' ').trim()||e.getAttribute('title')||e.getAttribute('placeholder')||e.getAttribute('name')||'';
  return [...new Set([...document.querySelectorAll(q)].filter(vis))].map(e=>({tag:e.tagName.toLowerCase(),role:e.getAttribute('role')||'',type:e.getAttribute('type')||'',label:label(e).slice(0,240),disabled:Boolean(e.disabled||e.getAttribute('aria-disabled')==='true'),href:e.getAttribute('href')||''}));
 });
 const layout=await page.evaluate(()=>({c:document.documentElement.clientWidth,s:document.documentElement.scrollWidth}));
 const shot=slug(surface)+'-'+viewport.width+'x'+viewport.height+'.png';
 await page.screenshot({path:path.join(out,shot),fullPage:true,animations:'disabled'});
 return {surface,url:page.url(),controls,controlCount:controls.length,horizontalOverflow:layout.s>layout.c+2,screenshot:shot};
}
async function visit(surface,url,viewport,authenticated){
 const ctx=await browser.newContext({viewport,colorScheme:'light'}),page=await ctx.newPage();
 if(authenticated) await seed(page);
 const pageErrors=[],http5xx=[];
 page.on('pageerror',e=>pageErrors.push(String(e)));
 page.on('response',r=>{if(r.status()>=500)http5xx.push({url:r.url(),status:r.status()});});
 await page.goto(base+url,{waitUntil:'networkidle',timeout:90000});
 const row=await snapshot(page,surface,viewport);
 evidence.push({viewport,row,pageErrors,http5xx});
 await ctx.close();
}

for(const viewport of viewports){
 for(const [s,u] of publicPages) await visit(s,u,viewport,false);
 for(const [s,u] of protectedPages) await visit(s,u,viewport,true);

 const ctx=await browser.newContext({viewport,colorScheme:'light'}),page=await ctx.newPage();
 await seed(page);
 await page.goto(base+'/settings',{waitUntil:'networkidle',timeout:90000});
 for(const label of settingsTabs){
  const b=page.getByRole('button',{name:label,exact:true});
  if(await b.count()){
   await b.click(); await page.waitForTimeout(250);
   evidence.push({viewport,row:await snapshot(page,'g5-settings-'+slug(label),viewport),pageErrors:[],http5xx:[]});
  }
 }
 await ctx.close();
}
await browser.close(); await api.dispose();

const unique=new Map(),failures=[];
for(const e of evidence){
 for(const c of e.row.controls){const k=[e.row.surface,c.tag,c.role,c.type,c.label].join('|');if(!unique.has(k))unique.set(k,{surface:e.row.surface,...c});}
 if(e.row.controlCount===0) failures.push({surface:e.row.surface,reason:'zero-controls'});
 if(e.row.horizontalOverflow) failures.push({surface:e.row.surface,reason:'horizontal-overflow',viewport:e.viewport});
 for(const x of e.pageErrors) failures.push({surface:e.row.surface,reason:'pageerror',error:x});
 for(const x of e.http5xx) failures.push({surface:e.row.surface,reason:'http5xx',...x});
}
const inventory=[...unique.values()].sort((a,b)=>a.surface.localeCompare(b.surface)||a.label.localeCompare(b.label));
const byGate={};for(const r of inventory){const g=r.surface.split('-')[0];byGate[g]=(byGate[g]||0)+1;}
const summary={status:failures.length?'FAIL':'PASS',surfaceRuns:evidence.length,uniqueControlSignatures:inventory.length,byGate,failures};
fs.writeFileSync(path.join(out,'inventory.json'),JSON.stringify({summary,inventory,evidence},null,2));
fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(summary,null,2));
fs.writeFileSync(path.join(out,'inventory.md'),['# V1-07 G1→G7 browser denominator','',JSON.stringify(byGate),'','| Surface | Control | State |','|---|---|---|',...inventory.map(r=>'| '+r.surface+' | '+(r.label||'(sans libellé)').replace(/\|/g,'\\|')+' | '+(r.disabled?'disabled':'enabled')+' |'),'','Inventory only: browser action proof is still required.'].join('\n'));
console.log('G1_G7_BROWSER_INVENTORY',JSON.stringify(summary));
if(failures.length) process.exit(1);
