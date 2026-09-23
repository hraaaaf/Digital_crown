import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir=path.resolve('../artifacts/t2-browser/g4-panoramic-trash-before');
fs.mkdirSync(outDir,{recursive:true});
const user=process.env.T2_USER,password=process.env.T2_PASSWORD;
if(!user||!password) throw new Error('T2 credentials required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:user,password}});
if(!login.ok()) throw new Error('panoramic BEFORE login failed');
const tokens=await login.json(),headers={Authorization:`Bearer ${tokens.access_token}`};
const patients=await api.get('/api/patients',{headers});
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('panoramic BEFORE patient missing');

const png=Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEANmpCD8ongcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfUJxAYTIfIvQAAAAAElFTkSuQmCC',
  'base64'
);
const seeded=await api.post(`/api/ia/upload-panoramic?patient_id=${patient.id}`,{
  headers,
  multipart:{file:{name:'g4-panoramic-trash-before.png',mimeType:'image/png',buffer:png}}
});
if(!seeded.ok()) throw new Error(`panoramic BEFORE seed failed: ${seeded.status()}`);

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

  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=radiology&radioTab=panoramic`,{
    waitUntil:'networkidle',timeout:90000
  });
  await page.getByRole('button',{name:'Historique',exact:true}).click();
  await page.locator('[data-m4b-history]').waitFor({state:'visible',timeout:15000});
  await page.getByText('Corbeille récupérable',{exact:true}).waitFor({state:'visible',timeout:10000});
  await page.getByRole('button',{name:"Mettre l'examen panoramique à la corbeille",exact:true}).first().waitFor({state:'visible'});
  const shot=`before-panoramic-trash-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({path:path.join(outDir,shot),fullPage:false,animations:'disabled'});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
  if(overflow) throw new Error('panoramic BEFORE horizontal overflow');
  if(errors.length) throw new Error('panoramic BEFORE page errors: '+errors.join(' | '));
  evidence.push({viewport,shot});
  await context.close();
}
await browser.close();
await api.dispose();
const summary={status:'PASS',phase:'BEFORE',expectedCopy:'Corbeille récupérable',evidence};
fs.writeFileSync(path.join(outDir,'summary.json'),JSON.stringify(summary,null,2));
console.log('G4_PANORAMIC_TRASH_BEFORE '+JSON.stringify(summary));
