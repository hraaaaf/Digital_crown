// LOT07 P1 actual protected patient route — disposable FastAPI/T2 only.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {chromium, request} from 'playwright';

if(process.env.ENVIRONMENT!=='test' || process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
  || process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db')
  throw Error('T2 evidence may only run against the isolated test DB');
const head=process.env.SOURCE_HEAD;
if(!/^[0-9a-f]{40}$/.test(head||''))throw Error('Missing exact candidate SHA');
const out=path.resolve('../artifacts/lot07-p1-actual-t2');
await fs.mkdir(out,{recursive:true});

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{
  form:{username:process.env.T2_USER,password:process.env.T2_PASSWORD},
});
if(!login.ok())throw Error('T2 login rejected HTTP '+login.status());
const tokens=await login.json();
const list=await api.get('/api/patients/',{headers:{Authorization:'Bearer '+tokens.access_token}});
if(!list.ok())throw Error('T2 patient list unavailable HTTP '+list.status());
const patients=await list.json();
if(!Array.isArray(patients))throw Error('Expected patient list');
const patient=patients.find(p=>p.numero_dossier==='T2-0001');
if(!patient||!Number.isInteger(patient.id))throw Error('Missing exact T2-0001 synthetic patient');
const detail=await api.get('/api/patients/'+patient.id,{headers:{Authorization:'Bearer '+tokens.access_token}});
if(!detail.ok())throw Error('Cannot verify active T2 patient history');
const record=await detail.json();
if(record.id!==patient.id)throw Error('Patient API ID mismatch');
if(typeof record.antecedents_medicaux==='string'&&record.antecedents_medicaux.trim())
  throw Error('T2-0001 fixture does not represent missing history — do not fabricate clinical unknown');
const name=[patient.nom,patient.prenom].filter(Boolean).join(' ');
const browser=await chromium.launch({headless:true});
const evidence=[];
async function inject(page){
  await page.addInitScript(({access,refresh})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('refresh_token',refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:tokens.access_token,refresh:tokens.refresh_token});
}
async function checkPage(page,theme,width,zoomNative=false){
  const errors=[],failures=[];
  page.on('pageerror',e=>errors.push(String(e.message).slice(0,280)));
  page.on('response',r=>{if(r.status()>=500)failures.push({status:r.status(),path:new URL(r.url()).pathname});});
  await inject(page);
  await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'?tab=radiology&radioTab=media',{waitUntil:'domcontentloaded',timeout:90000});
  await page.getByText(name,{exact:false}).first().waitFor({state:'visible',timeout:60000});
  await page.getByRole('status',{name:'Antécédents médicaux non renseignés'}).waitFor({state:'visible',timeout:30000});
  const history=await page.getByRole('status',{name:'Antécédents médicaux non renseignés'}).innerText();
  if(!history.includes('ne confirme pas leur absence'))throw Error('Unknown history was misrepresented');
  const cta=page.getByRole('button',{name:'Compléter les antécédents dans la fiche patient'});
  if(await cta.count()!==1)throw Error('No unique protected dossier edit action');
  const note=page.locator('[data-v15-07-g1-inline-nba]');
  await note.waitFor({state:'visible',timeout:30000});
  const message=await note.innerText();
  if(!message.includes('Conseil clinique')||!message.includes('non exécutée'))
    throw Error('Actual backend NBA not displayed as text-only advice');
  const split=await page.locator('[data-v15-07-two-views]').count();
  const media=await page.locator('[data-testid="patient-media-timeline"]').count();
  const effectiveWidth=await page.evaluate(()=>innerWidth);
  if(split!==Number(effectiveWidth>=1280)||media!==1)
    throw Error('G1 split/reflow mismatch '+JSON.stringify({effectiveWidth,split,media}));
  if(effectiveWidth<600){
    const info=await page.getByText('Aucune information d’antécédents n’est enregistrée. Cela ne confirme pas leur absence.').boundingBox();
    const btn=await cta.boundingBox();
    if(!info||!btn||btn.y<info.y+info.height-1)throw Error('Mobile P1 CTA overlaps medical context');
  }
  if(theme==='dark')await page.evaluate(()=>document.documentElement.setAttribute('data-theme','dark'));
  const metrics=await page.evaluate(()=>({
    width:innerWidth,dpr:devicePixelRatio,outerWidth,visualScale:visualViewport?.scale||1,
    overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+2,
  }));
  if(metrics.overflow)throw Error('Horizontal overflow '+JSON.stringify(metrics));
  if(zoomNative && !(metrics.dpr>=1.9 && metrics.width>=600&&metrics.width<=850
    &&metrics.outerWidth>=1200&&metrics.visualScale===1&&split===0))
    throw Error('Native 200% zoom not demonstrated '+JSON.stringify(metrics));
  const file=theme+'-'+width+(zoomNative?'-native200':'')+'.png';
  await page.screenshot({path:path.join(out,file),animations:'disabled',fullPage:false});
  const image=await fs.stat(path.join(out,file));
  if(image.size<12000)throw Error('Blank image evidence '+file+' size='+image.size);
  if(errors.length||failures.length)throw Error('Browser errors '+JSON.stringify({errors,failures}));
  evidence.push({theme,width,zoomNative,split,media,metrics,file,imageBytes:image.size,
    description:'Authentic authenticated protected React patient route, disposable T2 FastAPI, no HTTP mocks'});
}
try{
  for(const theme of ['elite','dark']){
    for(const width of [1440,390]){
      const context=await browser.newContext({viewport:{width,height:900},locale:'fr-FR'});
      try{await checkPage(await context.newPage(),theme,width);}
      finally{await context.close();}
    }
  }
} finally{await browser.close();}
const zoomDir=await fs.mkdtemp(path.join(os.tmpdir(),'dc-p1-native-'));
await fs.mkdir(path.join(zoomDir,'Default'),{recursive:true});
const zoomLevel=Math.log(2)/Math.log(1.2);
await fs.writeFile(path.join(zoomDir,'Default','Preferences'),
  JSON.stringify({partition:{default_zoom_level:{x:zoomLevel}}}));
let zoomContext;
try{
  zoomContext=await chromium.launchPersistentContext(zoomDir,{
    headless:true,channel:'chromium',viewport:null,locale:'fr-FR',
    args:['--window-size=1440,900','--no-first-run','--no-default-browser-check'],
  });
  const storage=await api.storageState();
  if(!storage.cookies?.length)throw Error('No T2 workstation cookie for native-zoom browser');
  await zoomContext.addCookies(storage.cookies);
  await checkPage(await zoomContext.newPage(),'elite',1440,true);
} finally{await zoomContext?.close();await fs.rm(zoomDir,{force:true,recursive:true});await api.dispose();}
if(evidence.length!==5)throw Error('Five authentic captures required');
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({
  exactProductHead:head,runnerHead:process.env.GITHUB_SHA,
  fixture:'disposable T2-0001 from backend API',auth:'real API + enrolled workstation',
  nativeZoom:'Chrome profile default_zoom_level verified by DPR and CSS innerWidth',
  count:evidence.length,evidence,
},null,2));
console.log('LOT07_P1_AUTHENTIC_T2_SUCCESS '+JSON.stringify({head,records:evidence.length,nativeZoom:true}));
