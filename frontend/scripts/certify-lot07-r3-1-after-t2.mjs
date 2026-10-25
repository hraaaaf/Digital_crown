/**
 * LOT07 / 07.1 G1 genuine UI+FastAPI FUE-I (isolated synthetic T2 only).
 * No route interception or fake patient/media replies; only ephemeral test DB.
 */
import fs from 'node:fs';
import path from 'node:path';
import {chromium,request} from 'playwright';

const sha=process.env.SOURCE_HEAD;
const secret=process.env.T2_PASSWORD;
if (!sha || !secret || process.env.VITE_V15_07_1_R3_SPLIT_LAB!=='1' ||
    process.env.VITE_V15_07_1_MULTIVIEW_LAB!=='1' || process.env.ENVIRONMENT!=='test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1' ||
    process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db') {
  throw Error('Unsafe or incomplete disposable runtime attestation');
}
const root=path.resolve('../artifacts/lot07-r3-1-after');
fs.mkdirSync(root,{recursive:true});
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
let browser;
let page;
const otherContexts=[];
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
  // A third clinical panel is meaningful only with genuine, seeded T0/T1 data.
  // Create an orthodontic case via the real authenticated API in the disposable T2 DB.
  const syntheticMediaList=await api.get('/api/patients/'+patient.id+'/assets',{headers:head});
  pass('real synthetic media index before ortho linkage',syntheticMediaList.status()===200,
    {status:syntheticMediaList.status()});
  const mediaIndex=await syntheticMediaList.json();
  const byTimepoint=Object.fromEntries(['T0','T1'].map(timepoint=>
    [timepoint,mediaIndex.items?.find(item=>item.timepoint===timepoint)?.id]));
  pass('two persisted synthetic clinical asset ids',Boolean(byTimepoint.T0 && byTimepoint.T1),
    {timepoints:Object.keys(byTimepoint)});
  const orthoCase=await api.post('/api/patients/'+patient.id+'/ortho-case',{
    headers:head,data:{started_at:'2026-01-02T09:00:00'},
  });
  pass('authenticated real synthetic ortho case created',orthoCase.status()===201,
    {status:orthoCase.status()});
  const orthoCaseId=(await orthoCase.json()).id;
  for (const [ordinal,timepoint,occurredAt] of
    [[0,'T0','2026-01-02T09:00:00'],[1,'T1','2026-06-02T09:00:00']]) {
    const tp=await api.post('/api/patients/'+patient.id+'/ortho-case/'+orthoCaseId+'/timepoints',{
      headers:head,data:{ordinal,occurred_at:occurredAt,note:'Repère entièrement synthétique '+timepoint},
    });
    pass('real synthetic ortho '+timepoint+' created',tp.status()===201,
      {status:tp.status()});
    const tpId=(await tp.json()).id;
    const link=await api.post('/api/patients/'+patient.id+'/ortho-case/'+orthoCaseId+
      '/timepoints/'+tpId+'/evidences',{headers:head,data:{clinical_asset_id:byTimepoint[timepoint]}});
    pass('real synthetic evidence linked '+timepoint,link.status()===201,{status:link.status()});
  }
  // Distinct patient B in the SAME disposable cabinet for real SPA A→B→A.
  const otherPatientResponse=await api.post('/api/patients/',{
    headers:head,data:{numero_dossier:'T2-0002',nom:'ISOLATION',prenom:'BETA',
      date_naissance:'1992-05-04',sexe:'F'},
  });
  pass('second synthetic patient B created',otherPatientResponse.ok(),
    {status:otherPatientResponse.status()});
  const patientB=await otherPatientResponse.json();
  pass('patient B has distinct identity',Boolean(patientB.id && patientB.id!==patient.id));
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1920,height:1080},locale:'fr-FR'});
  await context.addInitScript(({access,refresh})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('refresh_token',refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:auth.access_token,refresh:auth.refresh_token});
  page=await context.newPage();
  const errors=[],responses=[];
  evidence.browserErrors=errors;
  evidence.network=responses;
  page.on('pageerror',err=>errors.push(String(err).slice(0,400)));
  page.on('response',r=>{
    const url=new URL(r.url());
    if(url.pathname.startsWith('/api/patients/')||url.pathname.startsWith('/api/workstation/')) {
      responses.push({path:url.pathname,status:r.status()});
    }
  });
  // Register the actual network oracle BEFORE navigating: the clinical media list
  // is loaded asynchronously after the container mounts, not when the slot appears.
  const mediaListResponsePromise=page.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/patients/'+patient.id+'/assets' &&
    r.request().method()==='GET',
    {timeout:60000});
  await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'?tab=radiology&radioTab=media',{
    waitUntil:'domcontentloaded',timeout:90000,
  });
  await page.locator('[data-v15-071-real-cabinet-lab]').waitFor({state:'visible',timeout:90000});
  await page.locator('[data-v15-071-viewslot="dossier"]').waitFor({state:'visible',timeout:90000});
  await page.locator('[data-v15-071-viewslot="imagerie"]').waitFor({state:'visible',timeout:90000});
  pass('real patient route re-read',responses.some(r=>r.path==='/api/patients/'+patient.id && r.status===200));
  pass('server registered workstation revalidated',responses.some(r=>r.path==='/api/workstation/bootstrap' && r.status===200));
  const mediaListResponse=await mediaListResponsePromise;
  const mediaListPayload=mediaListResponse.status()===200 ? await mediaListResponse.json() : null;
  pass('real media API response',mediaListResponse.status()===200 &&
    Array.isArray(mediaListPayload?.items),{status:mediaListResponse.status()});
  const mediaTimepoints=new Set(mediaListPayload.items.map(item=>item.timepoint));
  pass('T0 and T1 synthetic media returned by API',
    mediaTimepoints.has('T0') && mediaTimepoints.has('T1'),
    {timepoints:[...mediaTimepoints].sort()});
  // Do not capture a premature empty timeline before React commits the response.
  await page.locator('[data-testid="media-asset-rail"] section[aria-label="Temps T0"]')
    .waitFor({state:'visible',timeout:30000});
  await page.locator('[data-testid="media-asset-rail"] section[aria-label="Temps T1"]')
    .waitFor({state:'visible',timeout:30000});
  pass('exactly one live real Media Timeline',await page.locator('[data-testid="patient-media-timeline"]').count()===1);
  pass('real patient dossier name', (await page.locator('[data-testid="multiview-real-dossier"]').innerText()).includes(patient.numero_dossier));
  pass('nine product directions explicitly unavailable',await page.locator('select[aria-label="Disposition MultiView"] option:disabled').count()===9);

  const pane=page.locator('[data-r3-1-split="two-columns"]');
  await pane.waitFor({state:'visible',timeout:25000});
  pass('R3-1 explicit DEV splitter mounted, not legacy R2',
    await page.locator('[data-testid="r3-1-grid"]').count()===1 &&
    await page.locator('[data-v15-071-multiview-grid]').count()===0);
  const separator=page.locator('[data-testid="r3-1-separator"]');
  pass('genuine vertical splitter starts 50/50',
    await separator.getAttribute('aria-orientation')==='vertical' &&
    await separator.getAttribute('aria-valuenow')==='50');
  pass('real clinical media remains read-only and single-instance',
    await page.locator('[data-testid="patient-media-timeline"]').count()===1 &&
    await page.locator('[data-v15-071-viewslot="imagerie"]').count()===1);

  const themes=['default','emerald','rose','ocean','graphite','prestige','dark','high-contrast'];
  async function themeAfter(theme,label) {
    await page.evaluate(theme=>{
      if(theme==='default') document.documentElement.removeAttribute('data-theme');
      else document.documentElement.setAttribute('data-theme',theme);
    },theme);
    await page.waitForTimeout(620); // settle actual theme transitions before AFTER evidence
    const frame=page.locator('[data-r3-1-split]');
    const computed=await frame.evaluate(el=>{
      const s=getComputedStyle(el);
      const sep=el.querySelector('[data-testid="r3-1-separator"]');
      return {bg:s.backgroundColor,text:s.color,border:s.borderColor,
        splitter:sep?getComputedStyle(sep).backgroundColor:null,
        theme:document.documentElement.getAttribute('data-theme')||'default'};
    });
    pass('theme '+theme+' affects actual R3-1 frame '+label,
      computed.theme===theme && computed.bg!=='rgba(0, 0, 0, 0)' &&
      computed.text!=='rgba(0, 0, 0, 0)' && Boolean(computed.splitter),computed);
    await capture(page,'after-r3-1-'+label+'-'+theme+'-1920.png');
  }
  for(const theme of themes) await themeAfter(theme,'two-columns-50');
  await page.evaluate(()=>document.documentElement.setAttribute('data-theme','dark'));
  await separator.focus();
  await separator.press('ArrowRight');
  pass('R3-1 genuine keyboard resize',await separator.getAttribute('aria-valuenow')==='55');
  await capture(page,'after-r3-1-two-columns-keyboard-55-dark-1920.png');
  await page.getByRole('button',{name:'Égaliser 50/50'}).click();
  pass('R3-1 reset restores strict 50/50',await separator.getAttribute('aria-valuenow')==='50');

  // Keyboard focus and reset can scroll the page. Mouse coordinates alone do not
  // auto-scroll a DOM target: prove the actual separator is under the pointer.
  await separator.scrollIntoViewIfNeeded();
  await separator.hover();
  const grip=await separator.boundingBox();
  const bounds=await page.locator('[data-testid="r3-1-grid"]').boundingBox();
  if(!grip || !bounds)throw Error('Real R3-1 separator geometry missing');
  const gripX=grip.x+grip.width/2;
  const gripY=grip.y+grip.height/2;
  const hit=await page.evaluate(({x,y})=>
    document.elementFromPoint(x,y)?.closest('[data-testid="r3-1-separator"]')!==null,
    {x:gripX,y:gripY});
  pass('R3-1 Chromium pointer target is really hit-testable',hit,
    {gripX,gripY,viewport:{width:1920,height:1080}});
  await page.mouse.move(gripX,gripY);
  await page.mouse.down();
  await page.mouse.move(bounds.x+bounds.width*0.6,grip.y+grip.height/2,{steps:9});
  await page.mouse.up();
  const dragged=Number(await separator.getAttribute('aria-valuenow'));
  pass('R3-1 real Chromium pointer drag adjusts live grid',dragged>=55&&dragged<=63,{dragged});
  await capture(page,'after-r3-1-two-columns-pointer-'+dragged+'-dark-1920.png');

  const select=page.getByRole('combobox',{name:'Disposition MultiView'});
  await select.selectOption('dossier-media-2rows');
  await page.getByRole('button',{name:'Aperçu',exact:true}).click();
  await page.getByRole('button',{name:'Appliquer',exact:true}).click();
  await page.locator('[data-r3-1-split="two-rows"]').waitFor({state:'visible'});
  const rowSep=page.locator('[data-testid="r3-1-separator"]');
  pass('real R3-1 horizontal 50/50 with accessible separator',
    await rowSep.getAttribute('aria-orientation')==='horizontal' &&
    await rowSep.getAttribute('aria-valuenow')==='50');
  for(const theme of ['default','dark','high-contrast']) await themeAfter(theme,'two-rows-50');
  await rowSep.focus();
  await rowSep.press('ArrowDown');
  pass('R3-1 horizontal keyboard resize',await rowSep.getAttribute('aria-valuenow')==='55');
  await capture(page,'after-r3-1-two-rows-keyboard-55-high-contrast-1920.png');
  await page.getByRole('button',{name:'Ajuster au contenu'}).click();
  pass('R3-1 content-fit explicit, without interactive separator',
    await page.locator('[data-r3-1-mode="content-fit"]').count()===1 &&
    await page.locator('[data-testid="r3-1-separator"]').count()===0);
  await capture(page,'after-r3-1-two-rows-content-fit-high-contrast-1920.png');
  pass('nine unintegrated presets still unavailable',
    await page.locator('select[aria-label="Disposition MultiView"] option:disabled').count()===9);
  pass('no browser JavaScript errors',errors.length===0,{errors:errors.slice(0,4)});
  console.log('R3-1 AUTHENTIC AFTER PASS '+evidence.tests.length+' tests, '+evidence.screens.length+
    ' synthetic screenshots, exact HEAD '+sha);
} catch (error) {
  evidence.failure=String(error).slice(0,700);
  if (page) {
    try { await capture(page,'failure-snapshot-1920.png'); } catch { /* page not available */ }
  }
  throw error;
} finally {
  // Persist evidence even when an assertion fails; never turn a failure into PASS.
  fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify(evidence,null,2));
  await browser?.close();
  for (const context of otherContexts) await context.dispose();
  await api.dispose();
}
