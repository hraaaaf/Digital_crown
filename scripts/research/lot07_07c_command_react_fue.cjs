// LOT07/07-C FUE laboratory: two separate fresh browser contexts, not independent AI agents.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createRequire}=require('node:module');
const pw=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const out=path.resolve('artifacts/lot07-07c-command-react/fue');fs.mkdirSync(out,{recursive:true});
const sha=process.env.SOURCE_HEAD||process.env.GITHUB_SHA||'UNKNOWN';
const target='http://127.0.0.1:5193/command-target.html';
const results=[];
function check(name,pass,detail=''){results.push({name,pass:Boolean(pass),detail:String(detail).slice(0,220),score:pass?10:0,gate:'REQUIRED'});}
async function shot(page,label){const file=path.join(out,label+'.png');await page.screenshot({path:file,animations:'disabled'});return {file:path.basename(file),sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')};}
async function patient(page){return page.locator('.cmd-shell').getAttribute('data-active-patient-id');}
(async()=>{
 const browser=await pw.chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  // FUE-A: first-user synthetic workflow, isolated fresh browser profile.
  const a=await browser.newContext({viewport:{width:430,height:900},reducedMotion:'reduce'});
  const pa=await a.newPage(),requests=[];
  pa.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:5193/'))requests.push(r.url().slice(0,100));});
  await pa.goto(target,{waitUntil:'networkidle'});
  const beforeA=await shot(pa,'A-before');
  check('A initial TEST-001',await patient(pa)==='TEST-001');
  const pause=pa.getByRole('button',{name:'Mettre en pause'});
  await pause.click();check('A pause visible',await pa.getByRole('button',{name:/Reprendre \(simulation\)/}).isVisible());
  await pa.getByRole('button',{name:/Reprendre \(simulation\)/}).click();
  check('A resume visible',await pa.getByRole('button',{name:'Mettre en pause'}).isVisible());
  const next=pa.getByRole('button',{name:'Patient suivant (même praticien)'});
  check('A next same practitioner available',await next.isEnabled());
  if(await next.isEnabled()){
   await next.click();
   check('A switch requires confirmation',await pa.getByRole('alertdialog').isVisible()&&await patient(pa)==='TEST-001');
   const pending=await shot(pa,'A-action-confirm');
   await pa.getByRole('button',{name:'Confirmer le changement de patient'}).click();
   const after=await patient(pa);
   check('A confirmed switch changes identity',after!=='TEST-001',after);
   await shot(pa,'A-after');
  }
  check('A no external network requests',requests.length===0,JSON.stringify(requests));
  await a.close();
  // FUE-B: independent browser storage/profile, adversarial keyboard/cancel/identity.
  const b=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const pb=await b.newPage(),external=[];
  pb.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:5193/'))external.push(r.url().slice(0,100));});
  await pb.goto(target,{waitUntil:'networkidle'});
  check('B fresh context resets TEST-001',await patient(pb)==='TEST-001');
  await shot(pb,'B-before');
  const nextB=pb.getByRole('button',{name:'Patient suivant (même praticien)'});
  if(await nextB.isEnabled()){
   await nextB.focus();await pb.keyboard.press('Enter');
   check('B modal traps initial focus',await pb.evaluate(()=>document.activeElement?.textContent?.includes('Confirmer le changement')));
   await shot(pb,'B-action-confirm');
   await pb.keyboard.press('Escape');
   check('B Escape preserves identity',await patient(pb)==='TEST-001'&&await pb.getByRole('alertdialog').count()===0);
   check('B Escape restores opener focus',await nextB.evaluate(el=>el===document.activeElement));
   await nextB.click();
   await pb.getByRole('button',{name:'Annuler le changement'}).click();
   check('B cancel preserves identity',await patient(pb)==='TEST-001');
  }else check('B next practitioner available',false);
  const tabs=pb.getByRole('tab');
  await tabs.first().focus();await pb.keyboard.press('ArrowRight');
  check('B keyboard tab navigation',await pb.getByRole('tab',{name:'Dossier',exact:true}).getAttribute('aria-selected')==='true');
  check('B patient panel remains scoped',await pb.locator('#cmd-cards').getAttribute('data-patient-id')==='TEST-001');
  check('B no external network requests',external.length===0,JSON.stringify(external));
  await shot(pb,'B-after');
  await b.close();
  const report={sourceHead:sha,source:'STANDALONE_SYNTHETIC_REACT_ONLY',browser:'Chromium',isolatedBrowserContexts:true,independentAgents:false,realLogin:false,backend:false,humanApproval:false,checks:results,pass:results.every(x=>x.pass),evidence:{beforeA},limitations:['Two scripted personas in one CI job are not two independent blind-user AI agents','No real Cabinet login, patient data, RBAC or clinical validation','No human visual approval']};
  fs.writeFileSync(path.join(out,'fue-report.json'),JSON.stringify(report,null,2)+'\n');
  console.log('LOT07_FUE_LAB '+JSON.stringify({head:sha,pass:report.pass,passed:results.filter(x=>x.pass).length,total:results.length,independentAgents:false}));
  if(!report.pass)process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{fs.writeFileSync(path.join(out,'fue-error.txt'),String(e.stack||e));console.error('LOT07_FUE_LAB_ERROR '+e.message);process.exitCode=1;});
