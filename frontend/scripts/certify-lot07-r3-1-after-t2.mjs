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
  // P2: exercise the real read-only DOCUMENT and RADIOLOGY adapters with
  // deliberately non-clinical, synthetic media in the disposable T2 database.
  // Never intercept network responses or use patient files.
  // P5: renderable, explicitly NONCLINICAL one-page PDF for the isolated T2
  // screenshot lab. No real chart, patient documents or synthetic diagnosis.
  const syntheticPdf=(()=>{
    const stream='BT /F1 21 Tf 48 180 Td (QA R3 - DOCUMENT NON CLINIQUE) Tj\n'+
      '/F1 12 Tf 0 -36 Td (Fixture synthetique - aucune donnee patient.) Tj\n'+
      '0 -24 Td (Lecture seule - verification du rendu documentaire.) Tj ET\n';
    const objects=[
      '<< /Type /Catalog /Pages 2 0 R >>',
      '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
      '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 250] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
      '<< /Length '+Buffer.byteLength(stream,'ascii')+' >>\nstream\n'+stream+'endstream',
      '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ];
    let body='%PDF-1.4\n';
    const offsets=[0];
    objects.forEach((obj,index)=>{
      offsets.push(Buffer.byteLength(body,'ascii'));
      body+=(index+1)+' 0 obj\n'+obj+'\nendobj\n';
    });
    const startxref=Buffer.byteLength(body,'ascii');
    body+='xref\n0 '+offsets.length+'\n0000000000 65535 f \n'+
      offsets.slice(1).map(offset=>String(offset).padStart(10,'0')+' 00000 n ').join('\n')+
      '\ntrailer\n<< /Size '+offsets.length+' /Root 1 0 R >>\nstartxref\n'+startxref+'\n%%EOF\n';
    return Buffer.from(body,'ascii');
  })();
  for (const asset of [
    {kind:'DOCUMENT',name:'QA-R3-document-synthetique.pdf',mime:'application/pdf',buffer:syntheticPdf},
    {kind:'RADIOGRAPH',name:'QA-R3-radiographie-synthetique.png',mime:'image/png',buffer:fakePng},
  ]) {
    const imported=await api.post('/api/patients/'+patient.id+'/assets/import',{
      headers:head,multipart:{file:{name:asset.name,mimeType:asset.mime,buffer:asset.buffer},
        asset_type:asset.kind,source_kind:'UPLOAD'},
    });
    pass('real authenticated P2 synthetic '+asset.kind+' media import',imported.ok(),
      {status:imported.status()});
  }
  const p2AssetsResponse=await api.get('/api/patients/'+patient.id+'/assets',{headers:head});
  pass('real authenticated P2 synthetic asset index',p2AssetsResponse.status()===200,
    {status:p2AssetsResponse.status()});
  const p2Assets=await p2AssetsResponse.json();
  for (const kind of ['DOCUMENT','RADIOGRAPH']) {
    pass('persisted synthetic '+kind+' exists in real patient asset API',
      p2Assets.items?.some(item=>item.asset_type===kind),
      {kind,total:p2Assets.items?.length});
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
  const cephPair={T0:Number(process.env.R3_T2_CEPHALO_T0_ID),T1:Number(process.env.R3_T2_CEPHALO_T1_ID)};
  pass('two separate persisted synthetic CEPHALO record ids from isolated T2',
    Number.isSafeInteger(cephPair.T0)&&cephPair.T0>0 &&
    Number.isSafeInteger(cephPair.T1)&&cephPair.T1>0 &&
    cephPair.T0!==cephPair.T1,cephPair);
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
    const cephLink=await api.post('/api/patients/'+patient.id+'/ortho-case/'+orthoCaseId+
      '/timepoints/'+tpId+'/evidences',{headers:head,data:{cephalo_analysis_id:cephPair[timepoint]}});
    pass('real authenticated persisted CEPHALO evidence linked '+timepoint,
      cephLink.status()===201 && (await cephLink.json()).cephalo_analysis_id===cephPair[timepoint],
      {status:cephLink.status(),ordinal});
  }
  const actualCompareResponse=await api.get('/api/patients/'+patient.id+'/ortho-case/'+orthoCaseId+
    '/compare?from_ordinal=0&to_ordinal=1',{headers:head});
  pass('real authenticated F3 compare endpoint with two synthetic CEPHALO sources',
    actualCompareResponse.status()===200,{status:actualCompareResponse.status()});
  const actualCompare=await actualCompareResponse.json();
  const t0Sources=(actualCompare.from_timepoint?.evidences||[]).filter(e=>e.kind==='CEPHALO');
  const t1Sources=(actualCompare.to_timepoint?.evidences||[]).filter(e=>e.kind==='CEPHALO');
  pass('F3 server returns distinct verified T0/T1 CEPHALO bindings and numerical SNA delta',
    actualCompare.patient_id===patient.id && actualCompare.ortho_case_id===orthoCaseId &&
    t0Sources.length===1 && t1Sources.length===1 &&
    t0Sources[0].ref_id===cephPair.T0 && t1Sources[0].ref_id===cephPair.T1 &&
    actualCompare.measurement_status==='AVAILABLE' &&
    actualCompare.interpretation_policy==='NUMERIC_ONLY_CLINICIAN_INTERPRETATION' &&
    actualCompare.measurements.some(m=>m.key==='SNA' && Math.abs(m.from_value-82)<0.01 &&
      Math.abs(m.to_value-83.2)<0.01),
    {status:actualCompare.measurement_status,t0:t0Sources.length,t1:t1Sources.length});
  // Seed an actually populated R-only dashboard through the real encrypted T2
  // database and authenticated endpoint, not through intercepted network data.
  const day=new Date().toISOString().slice(0,10);
  const agendaSeed=await api.get('/api/appointments/?start_date='+day+'T00:00:00&end_date='+day+'T23:59:59',{headers:head});
  pass('authentic synthetic T2 Agenda GET populated',agendaSeed.status()===200,{status:agendaSeed.status()});
  const agendaRows=await agendaSeed.json();
  pass('three persisted and server-authorized distinct T2 agenda rows',
    agendaRows.length===3 && new Set(agendaRows.map(a=>a.id)).size===3 &&
    agendaRows.every(a=>a.employer_id===auth.user?.id || a.patient_id===patient.id) &&
    agendaRows.every(a=>typeof a.motif==='string' && a.motif.startsWith('QA R3')),
    {count:agendaRows.length});
  // Master Plan seed via the REAL authenticated clinical API, never mocked.
  const syntheticPlan=await api.put('/api/patients/'+patient.id+'/master-plan',{
    headers:head,data:[
      {title:'Bilan initial synthétique',assistant:'Clinique',status:'done',date_str:'2026-10-01'},
      {title:'Contrôle de suivi synthétique',assistant:'Clinique',status:'pending',date_str:'2026-11-01'},
      {title:'Réévaluation synthétique',assistant:'Clinique',status:'postponed',date_str:'2026-12-10'},
    ],
  });
  pass('real authenticated synthetic Master Plan stored',syntheticPlan.ok(),{status:syntheticPlan.status()});
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
  const agendaRoadmapReady=await page.locator('select[aria-label="Disposition MultiView"] option[value="vue-ensemble"]').count()===1;
  const followupRoadmapReady=await page.locator('select[aria-label="Disposition MultiView"] option[value="suivi-clinique"]').count()===1;
  const imagerieRoadmapReady=await page.locator('select[aria-label="Disposition MultiView"] option[value="imagerie"]').count()===1;
  const treatmentRoadmapReady=await page.locator('select[aria-label="Disposition MultiView"] option[value="planification-traitements"]').count()===1;
  const orthoRoadmapReady=await page.locator('select[aria-label="Disposition MultiView"] option[value="comparaison-orthodontique"]').count()===1;
  const presentationRoadmapReady=await page.locator('select[aria-label="Disposition MultiView"] option[value="presentation-patient"]').count()===1;
  const provenRoadmapCount=(agendaRoadmapReady ? 4 : 0)+(followupRoadmapReady ? 1 : 0)+(imagerieRoadmapReady ? 1 : 0)
    +(treatmentRoadmapReady?1:0)+(orthoRoadmapReady?1:0)+(presentationRoadmapReady?1:0);
  pass('only proven roadmap presets unlocked, all others denied',
    await page.locator('select[aria-label="Disposition MultiView"] option:disabled').count()===9-provenRoadmapCount);

  const pane=page.locator('[data-r3-1-split="two-columns"]');
  await pane.waitFor({state:'visible',timeout:25000});
  const patientHeader=page.locator('[data-r3-1-patient-header="nonsticky"]');
  pass('R3 premium patient header is not sticky over clinical controls',
    await patientHeader.count()===1 &&
    await patientHeader.evaluate(el=>getComputedStyle(el).position!=='sticky'));
  pass('R3 premium controls are grouped without changing R-only permissions',
    await page.locator('[data-testid="r3-1-premium-actions"]').count()===1 &&
    await page.locator('[data-testid="r3-1-dossier-readonly-help"]').count()===1);
  pass('R3-1 explicit DEV splitter mounted, not legacy R2',
    await page.locator('[data-testid="r3-1-grid"]').count()===1 &&
    await page.locator('[data-v15-071-multiview-grid]').count()===0);
  const separator=page.locator('[data-testid="r3-1-separator"]');
  pass('R3 grip offers a visible semantic resize handle',
    await separator.locator('[aria-hidden="true"]').count()===1);
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
    Boolean(document.elementFromPoint(x,y)?.closest('[data-testid="r3-1-separator"]')),
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
  const rowGrid=page.locator('[data-testid="r3-1-grid"]');
  await rowGrid.scrollIntoViewIfNeeded();
  const rowVisibility=await rowGrid.evaluate(el=>{
    const a=el.querySelector('[aria-label="Panneau 1"]')?.getBoundingClientRect();
    const b=el.querySelector('[aria-label="Panneau 2"]')?.getBoundingClientRect();
    const view=window.innerHeight;
    const visible=(r)=>r?Math.max(0,Math.min(view,r.bottom)-Math.max(0,r.top)):0;
    return {a:visible(a),b:visible(b),viewport:view};
  });
  pass('R3-1 two-row real modules are both visible in a 1080p viewport',
    rowVisibility.a>=160 && rowVisibility.b>=160,rowVisibility);
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
  const fit=await page.locator('[data-testid="r3-1-grid"]').evaluate(el=>{
    const a=el.querySelector('[aria-label="Panneau 1"]')?.getBoundingClientRect();
    const b=el.querySelector('[aria-label="Panneau 2"]')?.getBoundingClientRect();
    return {firstHeight:a?.height||0,secondHeight:b?.height||0};
  });
  pass('R3-1 content-fit caps dossier while preserving media height',
    fit.firstHeight>0 && fit.firstHeight<=342 && fit.secondHeight>=219,fit);
  await capture(page,'after-r3-1-two-rows-content-fit-high-contrast-1920.png');
  // Return to Ghost Elite light-blue palette after explicit contrast-theme QA.
  await page.evaluate(()=>{
    document.documentElement.removeAttribute('data-theme');
    document.body.removeAttribute('data-theme');
  });
  const defaultColors=await page.evaluate(()=>{
    const s=getComputedStyle(document.documentElement);
    return {primary:s.getPropertyValue('--primary').trim().toLowerCase(),
      surface:s.getPropertyValue('--bg-medical-pearl').trim().toLowerCase()};
  });
  pass('R3 principal screenshots use default blue instead of test dark theme',
    defaultColors.primary==='#003380' && defaultColors.surface==='#f8fafc',defaultColors);
  const realRoadmapReady=await select.locator('option[value="vue-ensemble"]').count()===1;
  pass('roadmap presets unlock only with real Agenda adapter and remain fail-closed otherwise',
    await select.locator('option:disabled').count()===9-provenRoadmapCount);
  // R3-2: the third opt-in is independent, and the three modules are TRUE
  // authenticated patient views. Every focus transition unmounts other viewers.
  if(process.env.VITE_V15_07_1_R3_2_FOCUS_LAB==='1') {
    await select.selectOption('dossier-media-suivi-3cols');
    await page.getByRole('button',{name:'Aperçu',exact:true}).click();
    await page.getByRole('button',{name:'Appliquer',exact:true}).click();
    const three=page.locator('[data-testid="r3-2-three-real-panes"]');
    await three.waitFor({state:'visible',timeout:30000});
    pass('R3-2 three authenticated read-only panel slots mounted',
      await three.locator('[data-v15-071-viewslot]').count()===3 &&
      await three.locator('[data-v15-071-viewslot="imagerie"]').count()===1 &&
      await three.locator('[data-v15-071-viewslot="dossier"]').count()===1 &&
      await three.locator('[data-v15-071-viewslot="suivi"]').count()===1);
    pass('R3-2 single real media and true longitudinal source',
      await three.locator('[data-testid="patient-media-timeline"]').count()===1 &&
      await three.locator('[data-v15-071-viewslot="suivi"]').count()===1);
    pass('R3-2 remaining unintegrated roadmap presets are still unavailable',
      await select.locator('option:disabled').count()===9-provenRoadmapCount);
    await three.scrollIntoViewIfNeeded();
    await capture(page,'after-r3-2-three-columns-1920.png');

    await page.getByRole('button',{name:'Agrandir le panneau 2 : imagerie'}).click();
    const focused=page.locator('[data-testid="r3-2-single-focus"]');
    await focused.waitFor({state:'visible'});
    pass('R3-2 focus unmounts dossier and longitudinal rather than hiding them',
      await focused.locator('[data-v15-071-viewslot]').count()===1 &&
      await page.locator('[data-v15-071-viewslot="dossier"]').count()===0 &&
      await page.locator('[data-v15-071-viewslot="suivi"]').count()===0);
    pass('R3-2 focused media is still a single actual clinical viewer',
      await focused.locator('[data-testid="patient-media-timeline"]').count()===1);
    await capture(page,'after-r3-2-focus-media-1920.png');
    await page.getByRole('button',{name:'Restaurer les trois panneaux'}).click();
    pass('R3-2 restoration remounts all three authorized read-only views',
      await page.locator('[data-testid="r3-2-three-real-panes"] [data-v15-071-viewslot]').count()===3);
    await capture(page,'after-r3-2-restored-three-columns-1920.png');

    await select.selectOption('dossier-media-suivi-hero');
    await page.getByRole('button',{name:'Aperçu',exact:true}).click();
    await page.getByRole('button',{name:'Appliquer',exact:true}).click();
    const hero=page.locator('[data-testid="r3-2-three-real-panes"] [data-v15-071-geometry="hero-two"]');
    await hero.waitFor({state:'visible'});
    pass('R3-2 three REAL modules use 1+2 hierarchy',
      await hero.locator('[data-v15-071-viewslot]').count()===3);
    await hero.scrollIntoViewIfNeeded();
    await capture(page,'after-r3-2-hero-two-1920.png');
    await page.getByRole('button',{name:'Agrandir le panneau 3 : suivi'}).click();
    pass('R3-2 longitudinal focus is sole active clinical pane',
      await page.locator('[data-testid="r3-2-single-focus"] [data-v15-071-viewslot="suivi"]').count()===1 &&
      await page.locator('[data-testid="patient-media-timeline"]').count()===0);
    await capture(page,'after-r3-2-focus-suivi-1920.png');
    pass('R3-2 authenticated T2 Agenda permission enables 3 exact roadmap presets',
      realRoadmapReady &&
      await select.locator('option[value="consultation"]').count()===1 &&
      await select.locator('option[value="agenda-cabinet"]').count()===1);
    for (const [id,expectedModules,filename] of [
      ['vue-ensemble',['dossier','agenda','imagerie'],'after-r3-2-real-vue-ensemble-1920.png'],
      ['consultation',['dossier','agenda'],'after-r3-2-real-consultation-1920.png'],
      ['agenda-cabinet',['agenda','dossier'],'after-r3-2-real-agenda-cabinet-1920.png'],
      ['suivi-clinique',['suivi','photos'],'after-r3-2-real-suivi-clinique-1920.png'],
      ['imagerie',['imagerie','galerie'],'after-r3-2-real-imagerie-1920.png'],
      ['gestion-administrative',['agenda','documents'],'after-r3-2-real-gestion-administrative-1920.png'],
    ]) {
      await select.selectOption(id);
      await page.getByRole('button',{name:'Aperçu',exact:true}).click();
      await page.getByRole('button',{name:'Appliquer',exact:true}).click();
      const slots=await page.locator('[data-v15-071-viewslot]').evaluateAll(items =>
        items.map(item=>item.getAttribute('data-v15-071-viewslot')));
      if(['vue-ensemble','consultation','agenda-cabinet','gestion-administrative'].includes(id)){
        const agendaView=page.locator('[data-v15-071-layout="'+id+'"] [data-testid="r3-real-agenda"]');
        await agendaView.locator('tbody tr').first().waitFor({state:'visible',timeout:30000});
        pass('R3 populated real T2 Agenda in '+id,
          await agendaView.locator('tbody tr').count()===3 &&
          await agendaView.getAttribute('data-r3-agenda-state')==='populated',
          {id,rows:await agendaView.locator('tbody tr').count()});
      }
      // P4: the true 3-row agenda is compact, without collapsing either
      // independently scrollable 50/50 pane or altering permissions.
      if (['consultation','agenda-cabinet','gestion-administrative'].includes(id)) {
        const g=await page.locator('[data-v15-071-layout="'+id+'"][data-r3-1-split="two-columns"] [data-testid="r3-1-grid"]')
          .evaluate(el=>{
            const panes=[...el.querySelectorAll(':scope > section[data-v15-071-viewslot]')];
            return {height:Math.round(el.getBoundingClientRect().height),
              widths:panes.map(p=>Math.round(p.getBoundingClientRect().width)),
              scrolling:panes.map(p=>getComputedStyle(p).overflowY)};
          });
        pass('P4 compact sparse '+id+' is equal-width and scrollable',
          g.height>=379 && g.height<=426 && g.widths.length===2 &&
          Math.abs(g.widths[0]-g.widths[1])<=3 &&
          g.scrolling.every(v=>v==='auto'),g);
      }
      const realSourceVerified=id==='suivi-clinique'
        ? await page.locator('[data-v15-071-viewslot="photos"] select[aria-label="Filtrer par type"]').inputValue()==='PHOTO'
          && await page.locator('[data-v15-071-viewslot="photos"] select[aria-label="Filtrer par type"]').isDisabled()
        : id==='imagerie'
          ? await page.locator('[data-v15-071-viewslot="imagerie"] select[aria-label="Filtrer par type"]').inputValue()==='RADIOGRAPH'
            && await page.locator('[data-v15-071-viewslot="galerie"] select[aria-label="Filtrer par type"]').inputValue()==='PHOTO'
            && await page.locator('[data-v15-071-viewslot="imagerie"] select[aria-label="Filtrer par type"]').isDisabled()
            && await page.locator('[data-v15-071-viewslot="galerie"] select[aria-label="Filtrer par type"]').isDisabled()
          : id==='gestion-administrative'
            ? await page.locator('[data-testid="r3-real-agenda"]').count()===1
              && await page.locator('[data-v15-071-viewslot="documents"] select[aria-label="Filtrer par type"]').inputValue()==='DOCUMENT'
              && await page.locator('[data-v15-071-viewslot="documents"] select[aria-label="Filtrer par type"]').isDisabled()
            : await page.locator('[data-testid="r3-real-agenda"]').count()===1;
      pass('R3-2 real roadmap preset '+id,
        slots.join(',')===expectedModules.join(',') && realSourceVerified &&
        await select.locator('option:disabled').count()===9-provenRoadmapCount,
        {id,slots});
      // P5: verify the REAL narrow-slot media header does not use desktop-xl
      // toolbar geometry. Check the computed browser boxes, not just a CSS rule.
      if (id==='imagerie' || id==='gestion-administrative') {
        const module=id==='imagerie'?'imagerie':'documents';
        const geometry=await page.locator('[data-v15-071-viewslot="'+module+'"] [data-testid="patient-media-timeline"]')
          .evaluate(root=>{
            const header=root.firstElementChild?.firstElementChild;
            const filters=root.querySelector('[aria-label="Recherche et filtres médias"]');
            if (!(header instanceof HTMLElement) || !(filters instanceof HTMLElement)) return null;
            const box=filters.getBoundingClientRect();
            const children=[...filters.children].map(el=>el.getBoundingClientRect());
            const outside=children.some(b=>b.left<box.left-2 || b.right>box.right+2);
            const overlap=children.some((b,i)=>children.slice(i+1).some(c=>
              Math.min(b.right,c.right)-Math.max(b.left,c.left)>2 &&
              Math.min(b.bottom,c.bottom)-Math.max(b.top,c.top)>2));
            return {direction:getComputedStyle(header).flexDirection,
              width:Math.round(box.width),controls:children.length,outside,overlap};
          });
        pass('P5 readable authenticated media controls '+id,
          geometry?.direction==='column' && geometry.width>400 &&
          geometry.width<960 && geometry.controls===4 &&
          !geometry.outside && !geometry.overlap,geometry||{missing:true});
      }
      if (id==='suivi-clinique') {
        const split=await page.locator('[data-v15-071-layout="suivi-clinique"][data-r3-1-split="two-rows"] [data-testid="r3-1-grid"]')
          .evaluate(el=>({height:Math.round(el.getBoundingClientRect().height),
            panels:el.querySelectorAll(':scope > section[data-v15-071-viewslot]').length}));
        pass('P5 Follow-up makes more T0/T1 visible in original two-row split',
          split.height>=620 && split.height<=700 && split.panels===2,split);
      }
      await page.locator('[data-v15-071-viewslot]').first().scrollIntoViewIfNeeded();
      await capture(page,filename);
      // Integrated 9-view acceptance: accessible full T0/T1 focus must re-gate
      // and unmount the photo viewer until the original 50/50 is restored.
      if (id==='suivi-clinique') {
        await page.getByRole('button',{name:'Agrandir le suivi T0/T1'}).click();
        const focused=page.getByTestId('r3-1-followup-focus');
        await focused.waitFor({state:'visible'});
        pass('integrated Follow-up focus shows only verified T0/T1 read-only',
          await focused.locator('[data-v15-071-viewslot="suivi"]').count()===1 &&
          await page.locator('[data-v15-071-viewslot="photos"]').count()===0 &&
          await focused.locator('[aria-label="Comparaison orthodontique"]').count()===1);
        await capture(page,'after-r3-followup-t0-t1-focus-1920.png');
        await page.getByRole('button',{name:'Restaurer le partage 50/50'}).click();
        pass('integrated Follow-up restores authenticated equal split',
          await page.locator('[data-v15-071-layout="suivi-clinique"][data-r3-1-split="two-rows"] [data-testid="r3-1-separator"][aria-valuenow="50"]').count()===1 &&
          await page.locator('[data-v15-071-viewslot="photos"]').count()===1);
      }
    }
  }
  if(process.env.VITE_V15_07_1_R3_2_FOCUS_LAB==='1') {
    const chooser=page.getByRole('combobox',{name:'Disposition MultiView'});
    await chooser.selectOption('planification-traitements');
    await page.getByRole('button',{name:'Aperçu',exact:true}).click();
    await page.getByRole('button',{name:'Appliquer',exact:true}).click();
    const recorded=page.locator('[data-testid="r3-real-treatment"]');
    await recorded.waitFor({state:'visible'});
    await recorded.getByText(/Contrôle de suivi synthétique/).waitFor({state:'visible'});
    pass('R3 treatment preset reads canonical authenticated plan, no editor',
      await recorded.innerText().then(t=>t.includes('Lecture seule')&&t.includes('Contrôle de suivi synthétique')));
    await capture(page,'after-r3-real-treatment-1920.png');
    await chooser.selectOption('presentation-patient');
    await page.getByRole('button',{name:'Aperçu',exact:true}).click();
    await page.getByRole('button',{name:'Appliquer',exact:true}).click();
    const presentation=page.locator('[data-testid="r3-patient-presentation"]');
    await presentation.waitFor({state:'visible'});
    pass('R3 patient presentation remains masked before explicit action',
      await presentation.getByText('Présentation masquée').count()===1 &&
      await page.locator('[data-testid="r3-presentation-visible"]').count()===0);
    await capture(page,'after-r3-presentation-masked-1920.png');
    await presentation.getByRole('button',{name:'Présenter sur cet écran'}).click();
    await presentation.getByText('T2 CERTIFICATION').waitFor({state:'visible',timeout:20000});
    pass('synthetic patient presentation visible only after clinician-triggered action',
      await page.locator('[data-testid="r3-presentation-visible"]').count()===1 &&
      (await presentation.innerText()).includes('Contrôle de suivi synthétique'));
    await capture(page,'after-r3-presentation-active-t2-only-1920.png');
    await presentation.getByRole('button',{name:'Masquer immédiatement'}).click();
    pass('synthetic patient presentation completely hides on clinician demand',
      await page.locator('[data-testid="r3-presentation-visible"]').count()===0);

    await chooser.selectOption('comparaison-orthodontique');
    await page.getByRole('button',{name:'Aperçu',exact:true}).click();
    // 1920px viewport has <1704px of effective clinical workspace. Keep the
    // fail-closed three-cephalo/photo geometry gate, do not fake a narrow PASS.
    const applyOrtho=page.getByRole('button',{name:'Appliquer',exact:true});
    const widthAt1920=await page.locator('[data-v15-071-real-cabinet-lab]').evaluate(
      el=>Math.floor(el.getBoundingClientRect().width));
    pass('three-pane cephalo refuses unreadable 1920px nested workspace',
      widthAt1920<1704 && await applyOrtho.isDisabled(),{cssWidth:widthAt1920});

    // The DEV-only R3 patient media route can occupy a genuine >=1704px
    // workspace on a wider monitor; widen the real browser, not a mock element.
    await page.setViewportSize({width:2560,height:1080});
    await page.waitForFunction(()=> {
      const root=document.querySelector('[data-v15-071-real-cabinet-lab]');
      const apply=Array.from(document.querySelectorAll('button')).find(b=>b.textContent?.trim()==='Appliquer');
      return Boolean(root && root.getBoundingClientRect().width>=1704 && apply && !apply.disabled);
    },null,{timeout:15000});
    const widthAt2560=await page.locator('[data-v15-071-real-cabinet-lab]').evaluate(
      el=>Math.floor(el.getBoundingClientRect().width));
    pass('wider real Cabinet DEV workspace enables readable triple cephalo layout',
      widthAt2560>=1704 && widthAt2560<=2200 && await applyOrtho.isEnabled(),
      {cssWidth:widthAt2560});
    await applyOrtho.click();
    const clinicalT0=page.getByTestId('r3-cephalo-t0');
    const clinicalT1=page.getByTestId('r3-cephalo-t1');
    await clinicalT0.getByText('Analyse source #'+cephPair.T0).waitFor({state:'visible'});
    await clinicalT1.getByText('Analyse source #'+cephPair.T1).waitFor({state:'visible'});
    pass('real isolated T0/T1 clinical GET-only panels render distinct canonical source ids',
      await clinicalT0.getByText('SNA').count()===1 &&
      await clinicalT1.getByText('SNA').count()===1 &&
      (await clinicalT0.innerText()).includes('82') &&
      (await clinicalT1.innerText()).includes('83,2') &&
      await page.locator('[data-v15-071-viewslot="cephalo"]').count()===2 &&
      await page.locator('[data-testid="r3-cephalo-missing-t0"]').count()===0 &&
      await page.locator('[data-testid="r3-cephalo-missing-t1"]').count()===0,
      {T0:cephPair.T0,T1:cephPair.T1});
    // Visual acceptance: a 3rd Photos pane on a 2560px monitor is still a
    // ~700px inline-size container. Its desktop-xl media filter cannot overlap.
    const photosFilters=page.locator('[data-v15-071-viewslot="photos"] [aria-label="Recherche et filtres médias"]');
    const photosFilterFit=await photosFilters.evaluate(element=>{
      const outer=element.getBoundingClientRect();
      const boxes=Array.from(element.children).map(el=>el.getBoundingClientRect());
      const overflow=boxes.some(b=>b.left<outer.left-2||b.right>outer.right+2);
      const collision=boxes.some((b,i)=>boxes.slice(i+1).some(c=>
        Math.min(b.right,c.right)-Math.max(b.left,c.left)>2 &&
        Math.min(b.bottom,c.bottom)-Math.max(b.top,c.top)>2));
      return {width:outer.width,overflow,collision,controls:boxes.length};
    });
    pass('R3 T0/T1 Photos controls fit their actual narrow third pane without overlap',
      photosFilterFit.width>200 && photosFilterFit.controls===4 &&
      !photosFilterFit.overflow && !photosFilterFit.collision,photosFilterFit);
    await capture(page,'after-r3-real-ortho-t0-t1-synthetic-records-2560.png');
  }
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
