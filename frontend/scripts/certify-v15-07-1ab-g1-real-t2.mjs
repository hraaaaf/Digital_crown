/**
 * LOT07 / 07.1 G1 genuine UI+FastAPI FUE-I (isolated synthetic T2 only).
 * No route interception or fake patient/media replies; only ephemeral test DB.
 */
import fs from 'node:fs';
import path from 'node:path';
import {chromium,request} from 'playwright';

const sha=process.env.SOURCE_HEAD;
const secret=process.env.T2_PASSWORD;
if (!sha || !secret || process.env.ENVIRONMENT!=='test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1' ||
    process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db') {
  throw Error('Unsafe or incomplete disposable runtime attestation');
}
const root=path.resolve('../artifacts/lot07-071-g1-real-t2');
fs.mkdirSync(root,{recursive:true});
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
let browser;
const evidence={sourceHead:sha,tests:[],screens:[],denials:[]};
function pass(name,okay,details={}) {
  evidence.tests.push({name,pass:Boolean(okay),...details});
  if (!okay) throw Error('FUE-I assertion failed: '+name+' '+JSON.stringify(details));
}
async function capture(page,filename) {
  const p=path.join(root,filename);
  await page.screenshot({path:p,fullPage:false});
  evidence.screens.push(filename);
}
try {
  const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password:secret}});
  pass('owner login',login.ok(),{status:login.status()});
  const auth=await login.json();
  const head={Authorization:'Bearer '+auth.access_token};
  const read=await api.get('/api/patients/',{headers:head});
  pass('owner authenticated patients',read.ok(),{status:read.status()});
  const rows=await read.json();
  const patient=rows.find(p=>p.numero_dossier==='T2-0001');
  pass('synthetic patient bound',Boolean(patient?.id));
  const fakePng=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEANmpCD8ongcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfUJxAYTIfIvQAAAAAElFTkSuQmCC','base64');
  for(const timepoint of ['T0','T1']){
    const r=await api.post('/api/patients/'+patient.id+'/assets/import',{
      headers:head,multipart:{file:{name:'071-test-'+timepoint+'.png',mimeType:'image/png',buffer:fakePng},
        asset_type:'PHOTO',source_kind:'UPLOAD',timepoint},
    });
    pass('real authenticated synthetic media import '+timepoint,r.ok(),{status:r.status()});
  }
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1920,height:1080},locale:'fr-FR'});
  await context.addInitScript(({access,refresh})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('refresh_token',refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:auth.access_token,refresh:auth.refresh_token});
  const page=await context.newPage();
  const errors=[],responses=[];
  page.on('pageerror',err=>errors.push(String(err).slice(0,400)));
  page.on('response',r=>{
    const url=new URL(r.url());
    if(url.pathname.startsWith('/api/patients/')||url.pathname.startsWith('/api/workstation/')) {
      responses.push({path:url.pathname,status:r.status()});
    }
  });
  await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'?tab=radiology&radioTab=media',{
    waitUntil:'domcontentloaded',timeout:90000,
  });
  await page.locator('[data-v15-071-real-cabinet-lab]').waitFor({state:'visible',timeout:90000});
  await page.locator('[data-v15-071-viewslot="dossier"]').waitFor({state:'visible',timeout:90000});
  await page.locator('[data-v15-071-viewslot="imagerie"]').waitFor({state:'visible',timeout:90000});
  pass('real patient route re-read',responses.some(r=>r.path==='/api/patients/'+patient.id && r.status===200));
  pass('server registered workstation revalidated',responses.some(r=>r.path==='/api/workstation/bootstrap' && r.status===200));
  pass('real media API response',responses.some(r=>r.path.includes('/assets') && r.status===200));
  pass('exactly one live real Media Timeline',await page.locator('[data-testid="patient-media-timeline"]').count()===1);
  pass('real patient dossier name', (await page.locator('[data-testid="multiview-real-dossier"]').innerText()).includes(patient.numero_dossier));
  pass('nine product directions explicitly unavailable',await page.locator('select[aria-label="Disposition MultiView"] option:disabled').count()===9);
  await capture(page,'after-real-cabinet-two-columns-1920.png');

  const select=page.getByRole('combobox',{name:'Disposition MultiView'});
  await select.selectOption('dossier-media-suivi-3cols');
  await page.getByRole('button',{name:'Aperçu',exact:true}).click();
  pass('no extra clinical viewer during preview',await page.locator('[data-v15-071-viewslot]').count()===2);
  pass('nonpersistent schematic preview',await page.locator('[data-testid="multiview-schematic-preview"]').isVisible());
  await capture(page,'preview-schema-only-1920.png');
  await page.getByRole('button',{name:'Annuler',exact:true}).click();
  pass('cancel restores applied layout',await select.inputValue()==='dossier-media-2cols');
  await select.selectOption('dossier-media-2rows');
  await page.getByRole('button',{name:'Aperçu',exact:true}).click();
  await page.getByRole('button',{name:'Appliquer',exact:true}).click();
  pass('vertical split applied',await page.locator('[data-v15-071-multiview-grid]').evaluate(n=>getComputedStyle(n).gridTemplateRows.split(' ').length===2));
  pass('still one authenticated media module',await page.locator('[data-testid="patient-media-timeline"]').count()===1);
  await capture(page,'after-two-rows-1920.png');

  await select.selectOption('dossier-media-suivi-3cols');
  await page.getByRole('button',{name:'Aperçu',exact:true}).click();
  await page.getByRole('button',{name:'Appliquer',exact:true}).click();
  await page.locator('[data-v15-071-viewslot="suivi"]').waitFor({state:'visible',timeout:30000});
  pass('three real module slots applied',await page.locator('[data-v15-071-viewslot]').count()===3);
  pass('no CephaloWorkspace duplicate',await page.locator('[data-v15-071-viewslot="cephalo"]').count()===0);
  await capture(page,'after-three-columns-1920.png');

  await page.setViewportSize({width:390,height:844});
  await page.locator('[data-v15-071-real-cabinet-lab]').waitFor({state:'detached',timeout:25000}).catch(()=>{});
  pass('mobile no MultiView workspace slots',await page.locator('[data-v15-071-viewslot]').count()===0);
  pass('mobile keeps original authenticated media',await page.locator('[data-testid="patient-media-timeline"]').count()===1);
  await capture(page,'mobile-single-media-regression-390.png');
  pass('no browser JavaScript page errors',errors.length===0,{errors:errors.slice(0,5)});

  const deniedLogin=await api.post('/api/auth/login',{form:{username:'t2-restricted@cabinet.ma',password:secret}});
  pass('restricted actor login',deniedLogin.ok(),{status:deniedLogin.status()});
  const deniedAuth=await deniedLogin.json();
  const forbidden=await api.get('/api/patients/'+patient.id,{headers:{Authorization:'Bearer '+deniedAuth.access_token}});
  pass('restricted actor cannot read patient',!forbidden.ok(),{status:forbidden.status()});
  evidence.denials.push({actor:'synthetic-restricted',resource:'patient-by-id',status:forbidden.status()});
  fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify(evidence,null,2));
  console.log('LOT07 07.1 FUE-I REAL T2 PASS '+evidence.tests.length+' authentic assertions on '+sha);
} finally {
  await browser?.close();
  await api.dispose();
}
