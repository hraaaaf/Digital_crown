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
  await page.locator('[data-testid="patient-media-timeline"]').getByText('T0',{exact:true}).first()
    .waitFor({state:'visible',timeout:30000});
  await page.locator('[data-testid="patient-media-timeline"]').getByText('T1',{exact:true}).first()
    .waitFor({state:'visible',timeout:30000});
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
  await page.locator('[data-v15-071-viewslot="suivi"] [data-ortho-f3-compare]')
    .waitFor({state:'visible',timeout:30000});
  pass('third clinical panel renders populated genuine T0/T1 comparison',
    await page.locator('[data-v15-071-viewslot="suivi"] [data-ortho-f3-compare]').count()===1);
  pass('three real module slots applied',await page.locator('[data-v15-071-viewslot]').count()===3);
  pass('no CephaloWorkspace duplicate',await page.locator('[data-v15-071-viewslot="cephalo"]').count()===0);
  await capture(page,'after-three-columns-1920.png');

  await page.setViewportSize({width:390,height:844});
  await page.locator('[data-v15-071-real-cabinet-lab]').waitFor({state:'detached',timeout:25000}).catch(()=>{});
  pass('mobile no MultiView workspace slots',await page.locator('[data-v15-071-viewslot]').count()===0);
  pass('mobile keeps original authenticated media',await page.locator('[data-testid="patient-media-timeline"]').count()===1);
  await capture(page,'mobile-single-media-regression-390.png');
  // React Router navigation in the same Chromium tab, not a full page reload.
  await page.setViewportSize({width:1920,height:1080});
  const goPatient=async(id)=>{
    await page.evaluate(url=>{
      window.history.pushState({},'',url);
      window.dispatchEvent(new PopStateEvent('popstate'));
    },'/patients/'+id+'?tab=radiology&radioTab=media');
  };
  await goPatient(patientB.id);
  await page.locator('[data-testid="multiview-real-dossier"]')
    .getByText(patientB.numero_dossier,{exact:true})
    .waitFor({state:'visible',timeout:30000});
  pass('patient A detail not retained on B route',
    await page.getByText(patient.numero_dossier,{exact:true}).count()===0);
  await page.getByText('Aucun média longitudinal',{exact:true})
    .waitFor({state:'visible',timeout:30000});
  pass('patient A media not retained on B route',
    await page.getByText('Aucun média longitudinal',{exact:true}).count()===1);
  await capture(page,'after-client-route-patient-B-1920.png');
  await goPatient(patient.id);
  await page.locator('[data-testid="multiview-real-dossier"]')
    .getByText(patient.numero_dossier,{exact:true})
    .waitFor({state:'visible',timeout:30000});
  await page.locator('[data-testid="patient-media-timeline"]')
    .getByText('T0',{exact:true}).first().waitFor({state:'visible',timeout:30000});
  pass('A→B→A restores only patient A verified dossier',
    await page.getByText(patientB.numero_dossier,{exact:true}).count()===0);
  await capture(page,'after-client-route-patient-A-return-1920.png');
  pass('no browser JavaScript page errors',errors.length===0,{errors:errors.slice(0,5)});

  // RBAC proof cannot be inferred from HTTP 423 (missing workstation).
  // Enroll the owner with the product endpoint, and give staff ONLY the opaque
  // workstation cookie. Never share the owner bearer token with staff.
  const enrolled=await api.post('/api/workstation/enroll',{
    headers:head,data:{accountPassword:secret},
  });
  pass('authentic synthetic owner workstation enrollment',enrolled.status()===200,
    {status:enrolled.status()});
  const ownerState=await api.storageState();
  const workstationCookies=ownerState.cookies.filter(c=>c.name==='dc_workstation');
  pass('workstation identity cookie available',workstationCookies.length===1);
  const restrictedContext=await request.newContext({
    baseURL:'http://127.0.0.1:8005',
    storageState:{cookies:workstationCookies,origins:[]},
  });
  otherContexts.push(restrictedContext);
  const deniedLogin=await restrictedContext.post('/api/auth/login',{
    form:{username:'t2-restricted@cabinet.ma',password:secret},
  });
  pass('restricted actor login',deniedLogin.ok(),{status:deniedLogin.status()});
  const deniedAuth=await deniedLogin.json();
  const restrictedHead={Authorization:'Bearer '+deniedAuth.access_token};
  const restrictedBootstrap=await restrictedContext.get('/api/workstation/bootstrap',{
    headers:restrictedHead,
  });
  pass('restricted actor has a valid synthetic workstation',
    restrictedBootstrap.status()===200,{status:restrictedBootstrap.status()});
  const forbidden=await restrictedContext.get('/api/patients/'+patient.id,{headers:restrictedHead});
  pass('patient read is denied by RBAC rather than workstation',
    forbidden.status()===403,{status:forbidden.status()});
  evidence.denials.push({actor:'synthetic-restricted',resource:'patient-by-id',
    status:forbidden.status(),workstationValidated:true});

  // Distinct synthetic DENTISTE owner in a second tenant, enrolled normally.
  // A denied foreign patient and its media must not be misreported as RBAC-only.
  const foreignContext=await request.newContext({baseURL:'http://127.0.0.1:8005'});
  otherContexts.push(foreignContext);
  const foreignLogin=await foreignContext.post('/api/auth/login',{
    form:{username:'t2-setup-1280@cabinet.ma',password:secret},
  });
  pass('independent synthetic tenant B login',foreignLogin.ok(),
    {status:foreignLogin.status()});
  const foreignAuth=await foreignLogin.json();
  const foreignHead={Authorization:'Bearer '+foreignAuth.access_token};
  const foreignEnrollment=await foreignContext.post('/api/workstation/enroll',{
    headers:foreignHead,data:{accountPassword:secret},
  });
  pass('independent tenant B workstation enrolled',
    foreignEnrollment.status()===200,{status:foreignEnrollment.status()});
  const foreignPatient=await foreignContext.get('/api/patients/'+patient.id,{
    headers:foreignHead,
  });
  pass('different tenant cannot read patient A (not workstation 423)',
    foreignPatient.status()===403,{status:foreignPatient.status()});
  const foreignMedia=await foreignContext.get('/api/patients/'+patient.id+'/assets',{
    headers:foreignHead,
  });
  pass('different tenant cannot list patient A media',
    foreignMedia.status()===403,{status:foreignMedia.status()});
  evidence.denials.push({actor:'synthetic-foreign-tenant',resource:'patient-and-media',
    patientStatus:foreignPatient.status(),mediaStatus:foreignMedia.status(),
    workstationValidated:true});
  console.log('LOT07 07.1 FUE-I REAL T2 PASS '+evidence.tests.length+' authentic assertions on '+sha);
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
