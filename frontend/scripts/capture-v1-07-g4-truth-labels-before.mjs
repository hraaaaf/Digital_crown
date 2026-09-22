import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir=path.resolve('../artifacts/t2-browser/g4-truth-labels-before');
fs.mkdirSync(outDir,{recursive:true});
const user=process.env.T2_USER,password=process.env.T2_PASSWORD;
if(!user||!password) throw new Error('T2 credentials required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:user,password}});
if(!login.ok()) throw new Error('truth BEFORE login failed');
const tokens=await login.json(),headers={Authorization:`Bearer ${tokens.access_token}`};
const patients=await api.get('/api/patients',{headers});
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('truth BEFORE patient missing');

async function fieldAfter(page,label){
  return page.getByText(label,{exact:true}).locator('..').locator('input');
}

const browser=await chromium.launch({headless:true});
const evidence=[];
for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
  const context=await browser.newContext({viewport,colorScheme:'light'});
  const page=await context.newPage();
  await page.addInitScript(({a,r})=>{
    localStorage.setItem('token',a);
    localStorage.setItem('refresh_token',r||'');
    localStorage.setItem('appMode','prod');
  },{a:tokens.access_token,r:tokens.refresh_token});
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));

  const base=`http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=`;

  await page.goto(base+'honoraires',{waitUntil:'networkidle',timeout:90000});
  const treasury=page.getByRole('button',{name:/Procéder à l'Encaissement/i});
  await treasury.waitFor({state:'visible',timeout:30000});
  await treasury.click();
  await page.getByText('Encaissement',{exact:true}).waitFor({state:'visible',timeout:10000});
  const honorairesShot=`before-honoraires-treasury-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({path:path.join(outDir,honorairesShot),fullPage:false,animations:'disabled'});
  await page.getByRole('button',{name:'Fermer',exact:true}).click();

  await page.goto(base+'echeancier',{waitUntil:'networkidle',timeout:90000});
  await page.getByRole('button',{name:'Nouveau plan',exact:true}).click();
  await (await fieldAfter(page,'Montant Total Prévu (MAD)')).fill('1000');
  await (await fieldAfter(page,'Avance (MAD)')).fill('200');
  await (await fieldAfter(page,'Nbre Mensualités')).fill('2');
  await page.getByRole('button',{name:/Générer le tableau des échéances/i}).click();
  await page.getByDisplayValue('Mensualité 1').waitFor({state:'visible',timeout:10000});
  await page.getByRole('button',{name:'Enregistrer le plan',exact:true}).waitFor({state:'visible'});
  const footerSave=page.getByRole('button',{name:'Enregistrer',exact:true});
  await footerSave.waitFor({state:'visible',timeout:10000});
  await footerSave.scrollIntoViewIfNeeded();
  const installmentShot=`before-echeancier-footer-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({path:path.join(outDir,installmentShot),fullPage:false,animations:'disabled'});

  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
  if(overflow) throw new Error('truth BEFORE horizontal overflow');
  if(errors.length) throw new Error('truth BEFORE page errors: '+errors.join(' | '));
  evidence.push({viewport,honorairesShot,installmentShot});
  await context.close();
}
await browser.close();
await api.dispose();
const summary={
  status:'PASS',
  phase:'BEFORE',
  expected:{
    honoraires:'pre-patch treasury modal captured without asserting proposed replacement copy',
    echeancier:'Enregistrer'
  },
  evidence
};
fs.writeFileSync(path.join(outDir,'summary.json'),JSON.stringify(summary,null,2));
console.log('G4_TRUTH_LABELS_BEFORE '+JSON.stringify(summary));
