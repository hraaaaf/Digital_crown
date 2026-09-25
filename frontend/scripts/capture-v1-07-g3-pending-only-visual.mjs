import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const baselineSha='aef6a80afbdfcb5045fb681aae329a1fbe7793fc';
const sourcePath=path.resolve('src/features/agenda/AgendaStudio.tsx');
const artifactDir=path.resolve('artifacts/g3-pending-only-visual');
fs.mkdirSync(artifactDir,{recursive:true});

const repoRoot=path.resolve('..');
const currentHead=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8',cwd:repoRoot}).trim();
const currentSource=fs.readFileSync(sourcePath,'utf8');
const baselineSource=execFileSync(
  'git',
  ['show',baselineSha+':frontend/src/features/agenda/AgendaStudio.tsx'],
  {encoding:'utf8',cwd:repoRoot}
);

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G3 visual login failed');
const tokens=await login.json();

const browser=await chromium.launch({headless:true});
const viewports=[
  {name:'360',width:360,height:800},
  {name:'390',width:390,height:844},
  {name:'768',width:768,height:1024},
  {name:'1280',width:1280,height:900},
];

async function capturePhase(phase){
  for(const viewport of viewports){
    const ctx=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},colorScheme:'light'});
    const page=await ctx.newPage();
    await page.addInitScript(v=>{
      localStorage.setItem('token',v.access);
      localStorage.setItem('refresh_token',v.refresh||'');
      localStorage.setItem('appMode','prod');
    },{access:tokens.access_token,refresh:tokens.refresh_token});

    await page.route('**/api/appointments/pending',route=>route.fulfill({
      status:200,
      contentType:'application/json',
      body:JSON.stringify([{
        id:7001,
        patient_name:'Pending Browser',
        phone:'0600000000',
        motif:'Contrôle',
        datetime_start:'2030-01-15T10:00:00',
        duration_minutes:30,
        status:'EN_ATTENTE_DEMANDE',
        source:'visual-cert',
        expires_at:'2030-01-15T12:00:00'
      }])
    }));

    await page.goto('http://127.0.0.1:5173/agenda',{waitUntil:'networkidle',timeout:90000});
    const pendingOnly=page.getByRole('button',{name:'Afficher seulement',exact:true});
    await pendingOnly.waitFor({state:'visible',timeout:10000});
    await pendingOnly.click();
    await page.getByRole('button',{name:'Afficher tout',exact:true}).waitFor({state:'visible',timeout:5000});
    await page.getByText('Pending Browser',{exact:true}).waitFor({state:'visible',timeout:5000});

    await page.screenshot({
      path:path.join(artifactDir,phase+'-'+viewport.name+'.png'),
      fullPage:true,
    });
    await ctx.close();
  }
}

try{
  fs.writeFileSync(sourcePath,baselineSource,'utf8');
  await new Promise(resolve=>setTimeout(resolve,1200));
  await capturePhase('before');

  fs.writeFileSync(sourcePath,currentSource,'utf8');
  await new Promise(resolve=>setTimeout(resolve,1200));
  await capturePhase('after');

  fs.writeFileSync(path.join(artifactDir,'manifest.json'),JSON.stringify({
    baselineSha,
    currentHead,
    viewports,
    action:'Click Afficher seulement with one pending request visible',
    goal:'Pending-only mode keeps pending requests visible and hides the active agenda view until Afficher tout is clicked.',
    reference:'Same Agenda shell and pending-request section; only the active agenda view is removed in pending-only mode.'
  },null,2));
} finally {
  fs.writeFileSync(sourcePath,currentSource,'utf8');
  await browser.close();
  await api.dispose();
}

console.log('G3_PENDING_ONLY_VISUAL_CAPTURE',JSON.stringify({status:'PASS',baselineSha,currentHead,viewports:viewports.map(v=>v.name)}));
