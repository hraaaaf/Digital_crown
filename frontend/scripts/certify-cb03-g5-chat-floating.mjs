/**
 * G5 screenshots of the ACTUAL CrownBotChat mounted in a temporary floating
 * shell. Clinical HTTP deliberately intercepted. This is not MainLayout E2E,
 * nor PostgreSQL, Windows NVDA or a real cabinet.
 */
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';

const sha=process.env.CB03_G5_SOURCE_HEAD || '';
if (process.env.GITHUB_ACTIONS!=='true'
    || process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
    || process.env.CB03_G5_VISUAL_LAB!=='1'
    || !/^[0-9a-f]{40}$/.test(sha))
  throw Error('REFUSED: exact HEAD disposable G5 browser lab only');
const origin='http://127.0.0.1:5173';
const out=path.resolve('../artifacts/cb03-g5/chat-actual-component');
await fs.mkdir(out,{recursive:true});
const ID='d4a97731-cdcb-4b9c-94d3-f1d21c242a21';
const phrase='Prépare un RDV demain 10h pour Mme Benali contrôle';
let vite=null,browser=null;
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const requests=[];
const errors=[];
try {
  vite=spawn(process.execPath,['node_modules/vite/bin/vite.js',
    '--host','127.0.0.1','--port','5173','--strictPort'],{
    cwd:process.cwd(),
    env:{...process.env,
      VITE_CB03_G5_CHAT_LAB:'true',
      VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED:'true',
      VITE_CROWN_BOT_GUIDED_NLU_ENABLED:'true',
      VITE_CROWN_BOT_CB03_G3_ENABLED:'true',
      VITE_CROWN_BOT_CB03_CHAT_ENABLED:'true',
      VITE_CB03_G4_NATIVE_A11Y_LAB:'true',
      VITE_API_URL:'http://127.0.0.1:8005'},
    stdio:['ignore','pipe','pipe'],
  });
  vite.stdout.on('data',chunk=>process.stdout.write('[Vite]'+String(chunk)));
  vite.stderr.on('data',chunk=>process.stderr.write('[Vite]'+String(chunk)));
  let ready=false;
  for(let i=0;i<40;i++){
    try{ const res=await fetch(origin+'/cb03-g5-chat-lab.html',{signal:AbortSignal.timeout(850)});
      if(res.ok){ready=true;break;}
    }catch{}
    await sleep(500);
  }
  if(!ready)throw Error('NOT_CERTIFIED: G5 Vite loopback unavailable');
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1280,height:900},locale:'fr-FR'});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/bot/sessions',async route=>{
    await route.fulfill({status:200,contentType:'application/json',body:'[]',headers:{
      'access-control-allow-origin':origin,'access-control-allow-credentials':'true'}});
  });
  await page.route('**/api/bot/guided/**',async route=>{
    const r=route.request();
    const headers={'access-control-allow-origin':origin,'access-control-allow-credentials':'true',
      'access-control-allow-methods':'GET,POST,OPTIONS',
      'access-control-allow-headers':'authorization,content-type'};
    if(r.method()==='OPTIONS'){await route.fulfill({status:204,headers});return;}
    requests.push({method:r.method(),path:new URL(r.url()).pathname});
    if(r.method()==='POST'&&r.url().endsWith('/prepare-appointment')){
      if(r.postDataJSON()?.utterance!==phrase)throw Error('Wrong untrusted speech');
      await route.fulfill({status:200,headers,contentType:'application/json',body:JSON.stringify({
        status:'prepared',executable:false,preparation_id:ID,expires_at:'2026-11-01T12:30:00',
        summary:{patient:{id:21,prenom:'Salma',nom:'Benali',numero_dossier:'S-21'},
          datetime_start:'2026-11-07T10:00:00',praticien_id:9,resource_id:null,
          duration_minutes:30,motif:'CONTROLE'}
      })});
      return;
    }
    if(r.method()==='POST'&&r.url().endsWith('/confirm')){
      if(r.postDataJSON()?.preparation_id!==ID || r.postDataJSON()?.confirm!==true)
        throw Error('No explicit confirm');
      await route.fulfill({status:200,headers,contentType:'application/json',body:JSON.stringify({
        preparation_id:ID,status:'executed',result:{appointment_id:81,status:'CREATED'}
      })});
      return;
    }
    throw Error('REFUSED: unexpected G5 lab request '+r.method()+' '+r.url());
  });
  await page.goto(origin+'/cb03-g5-chat-lab.html',{waitUntil:'domcontentloaded'});
  await page.getByRole('button',{name:'Ouvrir CrownBot'}).click();
  const chat=page.getByRole('region',{name:'Conversation Crown Bot — actions guidées CB-03'});
  await chat.waitFor();
  if(await page.getByText('Actions guidées · confirmation sécurisée').count())
    throw Error('NOT_CERTIFIED: standalone G3 form instead of CrownBotChat');
  await page.screenshot({path:path.join(out,'g5-real-chat-floating-open.png'),fullPage:true});
  await page.getByRole('textbox',{name:'Votre message à Crown Bot'}).fill(phrase);
  await page.getByRole('button',{name:'Envoyer'}).click();
  await page.getByText('Salma Benali · Dossier S-21').waitFor();
  const confirm=page.getByRole('button',{name:'Confirmer explicitement cette action'});
  if(await confirm.isEnabled())throw Error('NOT_CERTIFIED: confirm enabled without checkbox');
  await page.screenshot({path:path.join(out,'g5-real-chat-server-prepared.png'),fullPage:true});
  await page.getByRole('checkbox',{name:/J’ai vérifié le patient/}).check();
  if(!await confirm.isEnabled())throw Error('NOT_CERTIFIED: no explicit confirmation');
  await confirm.click();
  await page.getByText(/Action exécutée et vérifiée · RDV #81/).waitFor();
  if(await page.getByRole('button',{name:'Confirmer explicitement cette action'}).count())
    throw Error('NOT_CERTIFIED: repeatable confirmation');
  await page.screenshot({path:path.join(out,'g5-real-chat-receipt.png'),fullPage:true});
  if(requests.length!==2 || requests[0].path!=='/api/bot/guided/prepare-appointment'
      || requests[1].path!=='/api/bot/guided/confirm')
    throw Error('NOT_CERTIFIED: wrong/duplicate G1-G2 request pattern');
  if(errors.length)throw Error('NOT_CERTIFIED: browser JS exceptions '+errors.join('; '));
  const report={schema:'CB03_G5_ACTUAL_CROWNBOTCHAT_SYNTHETIC_VISUAL_V1',
    head:sha,actualReactComponent:'CrownBotChat mounted into temporary floating shell',
    realMainLayout:false,realBackend:false,realDatabase:false,
    clinicalHttpIntercepted:true,clinicalWrite:false,
    flagsOutsideLab:false,posts:requests,blockedImplicitConfirm:true,
    screenshots:['g5-real-chat-floating-open.png',
      'g5-real-chat-server-prepared.png','g5-real-chat-receipt.png']};
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  console.log('CB03_G5_ACTUAL_CROWNBOT_CHAT_SYNTHETIC_VISUAL_PASS',JSON.stringify(report));
}finally{
  await browser?.close();
  if(vite?.exitCode===null)vite.kill();
}
