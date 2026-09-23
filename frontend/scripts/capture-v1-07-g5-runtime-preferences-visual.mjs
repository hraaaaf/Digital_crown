import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const baselineSha='915ac3f048803cb7aa82687130233622a1de0fb7';
const sourcePath=path.resolve('src/features/admin/Settings/tabs/IATab.tsx');
const artifactDir=path.resolve('artifacts/g5-runtime-preferences-visual');
fs.mkdirSync(artifactDir,{recursive:true});

const currentSource=fs.readFileSync(sourcePath,'utf8');
const baselineSource=execFileSync(
  'git',
  ['show',baselineSha+':frontend/src/features/admin/Settings/tabs/IATab.tsx'],
  {encoding:'utf8',cwd:path.resolve('..')}
);

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G5 visual login failed');
const tokens=await login.json();

const browser=await chromium.launch({headless:true});
const viewports=[
  {name:'360',width:360,height:800},
  {name:'390',width:390,height:844},
  {name:'768',width:768,height:1024},
  {name:'1280',width:1280,height:900},
];

async function capturePhase(phase,expectedLabel){
  for(const viewport of viewports){
    const ctx=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},colorScheme:'light'});
    const page=await ctx.newPage();
    await page.addInitScript(v=>{
      localStorage.setItem('token',v.access);
      localStorage.setItem('refresh_token',v.refresh||'');
      localStorage.setItem('appMode','prod');
    },{access:tokens.access_token,refresh:tokens.refresh_token});

    await page.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
    const tab=page.getByRole('button',{name:'Performance & Assistance',exact:true});
    await tab.waitFor({state:'visible',timeout:10000});
    await tab.click();
    await page.getByRole('button',{name:expectedLabel,exact:true}).waitFor({state:'visible',timeout:10000});
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
  await capturePhase('before','Conseils cliniques contextuels');

  fs.writeFileSync(sourcePath,currentSource,'utf8');
  await new Promise(resolve=>setTimeout(resolve,1200));
  await capturePhase('after','Animation d’activité IA');

  fs.writeFileSync(path.join(artifactDir,'manifest.json'),JSON.stringify({
    baselineSha,
    currentHead:process.env.GITHUB_SHA||null,
    viewports,
    beforeLabel:'Conseils cliniques contextuels',
    afterLabel:'Animation d’activité IA',
    goal:'Align visible Settings copy with the actual non-clinical AI activity animation behavior.',
  },null,2));
} finally {
  fs.writeFileSync(sourcePath,currentSource,'utf8');
  await browser.close();
  await api.dispose();
}

console.log('G5_RUNTIME_VISUAL_CAPTURE',JSON.stringify({status:'PASS',baselineSha,viewports:viewports.map(v=>v.name)}));
