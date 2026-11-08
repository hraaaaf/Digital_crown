/** DC-DOS-01 authenticated multi-tenant patient-switch FUE. Synthetic isolated T2 only. */
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';
const checkTrue = (x,msg)=>{if(!x)throw Error(msg)};
const head=process.env.PRODUCT_HEAD,password=process.env.T2_PASSWORD;
const f=JSON.parse(process.env.DC_DOS01_FIXTURE||'{}');
checkTrue(process.env.ENVIRONMENT==='test' && process.env.DIGITALCROWN_ISOLATED_RUNTIME==='1'
  && /^[a-f0-9]{40}$/.test(head||'') && password && f.synthetic_only===true
  && ['patient_a','patient_b','patient_x','study_a','study_b','tenant_x_user'].every(x=>Number.isSafeInteger(f[x]))
  && new Set([f.patient_a,f.patient_b,f.patient_x]).size===3
  && ['a','b','x'].every(x=>Number.isSafeInteger(f.archives?.[x]?.id) &&
    /^[a-f0-9]{64}$/.test(f.archives?.[x]?.sha256||'')),
  'Refusing unverified T2-only synthetic multitenant fixture');
const root='http://127.0.0.1:5173', backend='http://127.0.0.1:8005';
const output=path.resolve('../artifacts/ceph-v1-dos01-multitenant');
await fs.mkdir(output,{recursive:true});
const proof={head,case_id:'DC-DOS-01',synthetic_only:true,official_fue_complete:false,
  clinical_release:false,checks:[],shots:[],errors:[],status:'NOT_RUN'};
let browser,page,foreignPage,ownerApi,foreignApi,ownerContext,foreignContext;
async function shot(name,p=page) {
  if (!p) return;
  await p.screenshot({path:path.join(output,name+'.png'),animations:'disabled'});
  proof.shots.push(name+'.png');
}
async function verify(id,fn) {
  try {
    const result=await fn();
    proof.checks.push({id,status:'PASS',evidence:result||{}});
    console.log('DC_DOS01_PASS',id);
    return result;
  }catch(e) {
    proof.checks.push({id,status:'FAIL',error:String(e)});
    proof.errors.push(id+': '+String(e));
    await shot('failure-'+id.toLowerCase()).catch(()=>{});
    console.log('DC_DOS01_FAIL',id,String(e));
    throw e;
  }
}
async function login(api,email) {
  const res=await api.post('/api/auth/login',{form:{username:email,password}});
  checkTrue(res.status()===200,'JWT login failed '+res.status());
  return (await res.json()).access_token;
}
async function importPhoto(api,token,pid,file) {
  const res=await api.post('/api/patients/'+pid+'/ortho-media-record/photos/EXTRA_PROFILE',{
    headers:{Authorization:'Bearer '+token},
    multipart:{file:{name:'synthetic.png',mimeType:'image/png',buffer:await fs.readFile(file)},
      timepoint:'T0',acquired_at:'2026-11-08T09:00:00+00:00'},
  });
  checkTrue(res.status()===201,'Media import patient '+pid+' HTTP '+res.status()+' '+(await res.text()).slice(0,400));
  const data=await res.json();
  checkTrue(data.schema_version==='ORTHO_MEDIA_RECORD_V1' &&
    data.slot_id==='EXTRA_PROFILE' && data.asset?.patient_id===pid &&
    Number.isSafeInteger(data.asset?.id),'Media asset identity mismatch');
  return data.asset.id;
}
const get=(api,token,url)=>api.get(url,{headers:{Authorization:'Bearer '+token}});
async function deny(api,token,url) {
  const res=await get(api,token,url);
  checkTrue([403,404].includes(res.status()),'Cross-tenant HTTP '+res.status()+' at '+url);
  return res.status();
}
async function own(api,token,url) {
  const res=await get(api,token,url);
  checkTrue(res.status()===200,'Own-patient HTTP '+res.status()+' at '+url);
  return res.json();
}
async function browserLogin(context,email) {
  const p=await context.newPage();
  await p.goto(root+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
  await p.locator('[data-hub-experience="cabinet"]').click();
  await p.locator('input[type=email]').fill(email);
  await p.locator('input[type=password]').fill(password);
  await p.getByRole('button',{name:'Se connecter',exact:true}).click();
  await p.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
  checkTrue(await p.evaluate(()=>Boolean(localStorage.getItem('token'))),'Real UI JWT missing');
  return p;
}
async function openPatient(p,id,fresh=false,tab='radiology') {
  const routeTab=tab==='archives'?'?tab=archives':
    tab==='media'?'?tab=radiology&radioTab=media':'?tab=radiology&radioTab=cephalo';
  const url=root+'/patients/'+id+routeTab;
  if(fresh)await p.goto(url,{waitUntil:'domcontentloaded',timeout:45000});
  else await p.evaluate(dest=>{
    history.pushState({},'',dest);
    dispatchEvent(new PopStateEvent('popstate',{state:{}}));
  },url);
}
async function selectStudy(p,id) {
  await p.getByRole('button',{name:'Historique',exact:true}).click();
  const choice=p.locator('[data-cephalo-history-analysis-id="'+id+'"]');
  await choice.waitFor({state:'visible',timeout:30000});
  await choice.click();
  await p.locator('[data-cephalo-selected-analysis-id="'+id+'"]')
    .waitFor({state:'visible',timeout:30000});
}
async function showProfile(p) {
  await p.getByRole('button',{name:'Passer aux moulages',exact:true}).click();
  const image=p.locator('[data-ortho-photo-slot="EXTRA_PROFILE"] img[alt="Vue orthodontique"]');
  await image.waitFor({state:'visible',timeout:30000});
  const src=await image.getAttribute('src');
  checkTrue(src?.startsWith('blob:'),'Protected Media Core preview did not render a blob');
  return src;
}
try {
  ownerApi=await request.newContext({baseURL:backend});
  foreignApi=await request.newContext({baseURL:backend});
  browser=await chromium.launch({headless:true});
  const ownerJwt=await login(ownerApi,'t2-browser@cabinet.ma');
  const foreignJwt=await login(foreignApi,'t2-dos01-foreign@cabinet.ma');
  const ownerEnrolled=await enrollT2Workstation(ownerApi,ownerJwt,password);
  const foreignEnrolled=await enrollT2Workstation(foreignApi,foreignJwt,password);
  checkTrue(ownerEnrolled.cookies.some(x=>x.name==='dc_workstation') &&
    foreignEnrolled.cookies.some(x=>x.name==='dc_workstation'),'Isolated cabinet enrollment missing');
  const assets=await verify('REAL_JWT_UPLOADS_TO_THREE_SYNTHETIC_PATIENTS',async()=>{
    const a=await importPhoto(ownerApi,ownerJwt,f.patient_a,f.images.a);
    const b=await importPhoto(ownerApi,ownerJwt,f.patient_b,f.images.b);
    const x=await importPhoto(foreignApi,foreignJwt,f.patient_x,f.images.x);
    checkTrue(new Set([a,b,x]).size===3,'Asset IDs collided across patients');
    return {a,b,x};
  });
  await verify('PATIENT_SCOPED_MEDIA_TIMELINE_AND_ORTHO_SLOTS',async()=>{
    const triple=[[ownerApi,ownerJwt,f.patient_a,assets.a,f.archives.a.id],
                  [ownerApi,ownerJwt,f.patient_b,assets.b,f.archives.b.id],
                  [foreignApi,foreignJwt,f.patient_x,assets.x,f.archives.x.id]];
    for(const [api,jwt,pid,aid,documentId] of triple) {
      const media=await own(api,jwt,'/api/patients/'+pid+'/ortho-media-record?timepoint=T0');
      checkTrue(media.patient_id===pid && media.timepoint==='T0','Wrong patient media record');
      const profile=media.photo_slots.find(x=>x.slot_id==='EXTRA_PROFILE');
      checkTrue(profile?.state==='FILLED'&&profile.asset.asset_id===aid,'Wrong source asset');
      const timeline=await own(api,jwt,'/api/patients/'+pid+'/assets');
      checkTrue(timeline.items.length===1 && timeline.items[0].id===aid &&
        timeline.items[0].patient_id===pid,'Duplicate/cross-patient timeline');
      checkTrue(!('storage_key' in timeline.items[0]) && !('sha256' in timeline.items[0]),
        'Asset storage metadata leaked');
      const documents=await own(api,jwt,'/api/patients/'+pid+'/documents');
      checkTrue(Array.isArray(documents) && documents.length===1 &&
        documents[0].id===String(documentId) && documents[0].file_exists===true,
        'Own patient PDF archive absent or another patient document included');
      const blob=await get(api,jwt,'/api/patients/'+pid+'/assets/'+aid+'/content');
      checkTrue(blob.status()===200 && (await blob.body()).length>100,'Own blob not available');
    }
    return {real_http:true,patient_records:3,one_asset_per_timeline:true};
  });
  await verify('SAME_TENANT_PATIENT_ASSET_REBIND_DENIED',async()=>{
    const a=await deny(ownerApi,ownerJwt,'/api/patients/'+f.patient_b+'/assets/'+assets.a+'/content');
    const b=await deny(ownerApi,ownerJwt,'/api/patients/'+f.patient_a+'/assets/'+assets.b+'/content');
    return {a_to_b:a,b_to_a:b};
  });
  await verify('FOREIGN_TENANT_ASSETS_PATIENTS_STUDY_DENIED',async()=>{
    let denied=0;
    const subjects=[[foreignApi,foreignJwt,f.patient_a,assets.a,f.archives.a.id],
      [foreignApi,foreignJwt,f.patient_b,assets.b,f.archives.b.id],
      [ownerApi,ownerJwt,f.patient_x,assets.x,f.archives.x.id]];
    for(const [api,jwt,pid,aid,documentId] of subjects) {
      for(const suffix of ['', '/assets','/documents','/ortho-media-record?timepoint=T0',
          '/assets/'+aid+'/content']) {
        await deny(api,jwt,'/api/patients/'+pid+suffix);
        denied++;
      }
      await deny(api,jwt,'/api/documents/'+documentId+'/download');
      denied++;
    }
    const study=await get(foreignApi,foreignJwt,'/api/ia/analyses/'+f.study_a);
    checkTrue([403,404].includes(study.status()),'Cross-tenant science GET returned '+study.status());
    return {refused_http:denied+1,foreign_study_http:study.status()};
  });
  ownerContext=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce',
    storageState:{cookies:ownerEnrolled.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
  page=await browserLogin(ownerContext,'t2-browser@cabinet.ma');
  const aBlob=await verify('REAL_REACT_PATIENT_A_PROFILE',async()=>{
    await openPatient(page,f.patient_a,true);
    await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:40000});
    await selectStudy(page,f.study_a);
    const src=await showProfile(page);
    await shot('01-patient-a-media');
    return {blob_visible:true,source:'A_MEDIA_CORE'};
  });
  await verify('REAL_REACT_SPA_PATIENT_A_TO_B_NO_STALE_PHOTO',async()=>{
    const oldSrc=await page.locator('[data-ortho-photo-slot="EXTRA_PROFILE"] img').getAttribute('src');
    await openPatient(page,f.patient_b);
    await page.waitForURL(u=>new URL(u).pathname==='/patients/'+f.patient_b,{timeout:30000});
    await page.waitForFunction(name=>
      document.querySelector('[data-ortho-workspace-patient]')?.textContent?.includes(name),
      'SYNTHETIC_B',{timeout:35000});
    checkTrue(await page.locator('img[src="'+oldSrc+'"]').count()===0,
      'Patient A blob remained visible after patient B route transition');
    await shot('02-patient-b-before-study');
    await selectStudy(page,f.study_b);
    const newSrc=await showProfile(page);
    checkTrue(newSrc!==oldSrc,'Old A blob was repainted as B');
    checkTrue(await page.locator('img[src="'+oldSrc+'"]').count()===0,'A blob visible in B UI');
    await shot('03-patient-b-own-media');
    return {old_blob_hidden:true,new_blob_authenticated:true};
  });
  await verify('REAL_REACT_A_B_DOCUMENTS_ROUTE_ISOLATION',async()=>{
    await openPatient(page,f.patient_a,false,'archives');
    await page.locator('[data-flow-patient-surface="archives"]').waitFor({state:'visible',timeout:35000});
    await page.getByPlaceholder("Rechercher dans l'historique...").waitFor({state:'visible',timeout:35000});
    await page.getByText('DC-DOS01-SYNTH-A.pdf').waitFor({state:'visible',timeout:35000});
    checkTrue(await page.getByText('DC-DOS01-SYNTH-B.pdf').count()===0,
      'Patient B PDF appeared on patient A archive tab');
    await shot('04-patient-a-synthetic-archives');

    // Observe actual HTTP PDF bytes, patient-bound in-dossier iframe, and
    // URL.create/revoke. An external noopener window is no longer launched.
    await page.evaluate(()=>{
      const audit={created:[],revoked:[],opened:[]};
      window.__dcDosPdfAudit=audit;
      const create=URL.createObjectURL.bind(URL);
      const revoke=URL.revokeObjectURL.bind(URL);
      URL.createObjectURL=blob=>{const url=create(blob);audit.created.push(url);return url;};
      URL.revokeObjectURL=url=>{audit.revoked.push(url);return revoke(url);};
      window.open=(url,target,features)=>{
        audit.opened.push({url:String(url),target,features});
        return {closed:false};
      };
    });
    const checkCanvas=async dialog=>{
      const canvas=dialog.locator('canvas[data-testid="patient-pdf-page-canvas"][data-pdf-rendered="true"]');
      await canvas.waitFor({state:'visible',timeout:35000});
      const pixels=await canvas.evaluate(el=>{
        const ctx=el.getContext('2d');
        if(!ctx)return {width:0,height:0,ink:0};
        const data=ctx.getImageData(0,0,el.width,el.height).data;
        let ink=0;
        for(let k=0;k<data.length;k+=64)
          if(data[k]<160 && data[k+1]<160 && data[k+2]<160) ink++;
        return {width:el.width,height:el.height,ink};
      });
      checkTrue(pixels.width>450 && pixels.height>500 && pixels.ink>12,
        'BLANK_PDF_CANVAS '+JSON.stringify(pixels));
      checkTrue(await dialog.locator('iframe').count()===0,
        'Old iframe viewer remained mounted');
      return pixels;
    };
    const resA=page.waitForResponse(r=>r.url().includes('/api/documents/'+f.archives.a.id+'/download') && r.status()===200);
    await page.getByRole('button',{name:'Voir',exact:true}).click();
    const bytesA=await (await resA).body();
    checkTrue(crypto.createHash('sha256').update(bytesA).digest('hex')===f.archives.a.sha256,
      'The real patient A PDF response bytes differ from seeded SHA256');
    const previewA=page.getByRole('dialog',{name:/Aperçu PDF du patient/});
    await previewA.waitFor({state:'visible',timeout:15000});
    const pixelsA=await checkCanvas(previewA);
    const openedA=await page.evaluate(()=>window.__dcDosPdfAudit);
    checkTrue(openedA.created.length===0 && openedA.opened.length===0,
      'Patient A PDF preview created a detached blob URL or native window');
    await shot('04a-patient-a-inline-pdf-viewer');

    await openPatient(page,f.patient_b,false,'archives');
    await page.waitForURL(u=>new URL(u).pathname==='/patients/'+f.patient_b,{timeout:30000});
    await page.locator('[data-flow-patient-surface="archives"]').waitFor({state:'visible',timeout:35000});
    await page.getByText('DC-DOS01-SYNTH-B.pdf').waitFor({state:'visible',timeout:35000});
    checkTrue(await page.locator('canvas[data-testid="patient-pdf-page-canvas"]').count()===0,
      'Patient A canvas persisted in patient B dossier');
    checkTrue(await page.getByRole('dialog',{name:/Aperçu PDF du patient/}).count()===0,
      'Patient A PDF dialog remained mounted after A -> B');
    const auditB=await page.evaluate(()=>window.__dcDosPdfAudit);
    checkTrue(auditB.created.length===0 && auditB.opened.length===0 &&
      await page.getByText('DC-DOS01-SYNTH-A.pdf').count()===0,
      'Patient A PDF or detached preview persisted after navigation to B');
    checkTrue(await page.locator('[data-ortho-workspace-patient]').count()===0,
      'Patient B archive tab retained patient A cephalo workspace');
    await shot('05-patient-b-synthetic-archives');
    const resB=page.waitForResponse(r=>r.url().includes('/api/documents/'+f.archives.b.id+'/download') && r.status()===200);
    await page.getByRole('button',{name:'Voir',exact:true}).click();
    const bytesB=await (await resB).body();
    checkTrue(crypto.createHash('sha256').update(bytesB).digest('hex')===f.archives.b.sha256 &&
      f.archives.b.sha256!==f.archives.a.sha256,
      'Patient B PDF did not match its distinct fixture content');
    const previewB=page.getByRole('dialog',{name:/Aperçu PDF du patient/});
    await previewB.waitFor({state:'visible',timeout:15000});
    const pixelsB=await checkCanvas(previewB);
    checkTrue((await previewB.innerText()).includes('DC-DOS01-SYNTH-B.pdf') &&
      !(await previewB.innerText()).includes('DC-DOS01-SYNTH-A.pdf'),
      'Patient B PDF viewer contains patient A identity');
    const afterB=await page.evaluate(()=>window.__dcDosPdfAudit);
    checkTrue(afterB.created.length===0 && afterB.opened.length===0,
      'Patient B PDF preview created a detachable URL');
    await shot('05a-patient-b-inline-pdf-viewer');
    await page.keyboard.press('Escape');
    checkTrue(await page.locator('canvas[data-testid="patient-pdf-page-canvas"]').count()===0,
      'Patient B PDF canvas persisted after Escape');
    checkTrue(await page.getByRole('dialog',{name:/Aperçu PDF du patient/}).count()===0,
      'Patient B PDF dialog failed to close on Escape');
    return {real_pdf_bytes_sha256_A:true,real_pdf_bytes_sha256_B:true,
      pdf_canvas_A_pixels_confirmed:pixelsA.ink>12,pdf_canvas_B_pixels_confirmed:pixelsB.ink>12,
      no_pdf_preview_blob_url_created:true,patient_a_document_absent_in_B:true,
      inline_pdf_preview_patient_bound:true,zero_native_popup_open_attempts:true,
      escape_closes_pdf_preview:true,synthetic_official_archives_created:0};
  });
  await page.setViewportSize({width:1920,height:1080});
  await verify('REAL_R3_DESKTOP_SPLIT_A_B_NO_STALE_PANES',async()=>{
    const splitSelector='[data-r3-1-split="two-columns"]';
    const dossierSelector=splitSelector+' [data-v15-071-viewslot="dossier"]';
    const mediaSelector=splitSelector+' [data-v15-071-viewslot="imagerie"]';
    await openPatient(page,f.patient_a,false,'media');
    await page.locator(splitSelector).waitFor({state:'visible',timeout:40000});
    const dossierA=page.locator(dossierSelector);
    await page.waitForFunction(sel=>document.querySelector(sel)?.textContent?.includes('T2-0001'),
      dossierSelector,{timeout:25000});
    checkTrue((await dossierA.innerText()).includes('T2-0001'),
      'Patient A true Desktop R3 dossier panel not bound to patient A');
    const mediaA=page.locator(mediaSelector);
    await mediaA.locator('[data-testid="media-asset-rail"] article').first()
      .waitFor({state:'visible',timeout:35000});
    const sourceA=mediaA.locator('[data-testid="media-asset-rail"] [data-clinical-asset-id]').first();
    const sourceAId=Number(await sourceA.getAttribute('data-clinical-asset-id'));
    const selectedAId=Number(await mediaA.locator('[data-testid="media-inline-viewer"]').getAttribute('data-clinical-asset-id'));
    checkTrue(sourceAId===assets.a && selectedAId===assets.a,
      'DC-DOS-02 patient A split duplicated or rebound the original imported ClinicalAsset ID');
    const imageA=mediaA.locator('img[src^="blob:"]').first();
    await imageA.waitFor({state:'visible',timeout:30000});
    const srcA=await imageA.getAttribute('src');
    checkTrue(srcA?.startsWith('blob:'),'Patient A genuine media pane lacks authenticated blob');
    checkTrue(await mediaA.getByRole('button',{name:'Importer'}).count()===0,
      'Read-only MultiView mistakenly exposes media import');
    await shot('08-r3-split-patient-a');

    await openPatient(page,f.patient_b,false,'media');
    await page.waitForURL(u=>new URL(u).pathname==='/patients/'+f.patient_b,{timeout:30000});
    await page.locator(splitSelector).waitFor({state:'visible',timeout:40000});
    await page.waitForFunction(sel=>document.querySelector(sel)?.textContent?.includes('T2-DC-DOS01-B'),
      dossierSelector,{timeout:35000});
    const dossierB=await page.locator(dossierSelector).innerText();
    checkTrue(dossierB.includes('T2-DC-DOS01-B') && !dossierB.includes('T2-0001'),
      'Patient A dossier identity persisted in the R3 split of B');
    const mediaB=page.locator(mediaSelector);
    await mediaB.locator('[data-testid="media-asset-rail"] article').first()
      .waitFor({state:'visible',timeout:35000});
    const sourceB=mediaB.locator('[data-testid="media-asset-rail"] [data-clinical-asset-id]').first();
    const sourceBId=Number(await sourceB.getAttribute('data-clinical-asset-id'));
    const selectedBId=Number(await mediaB.locator('[data-testid="media-inline-viewer"]').getAttribute('data-clinical-asset-id'));
    checkTrue(sourceBId===assets.b && selectedBId===assets.b && sourceAId!==sourceBId,
      'DC-DOS-02 patient B split reused A original media ID or created a shadow source');
    const imageB=mediaB.locator('img[src^="blob:"]').first();
    await imageB.waitFor({state:'visible',timeout:30000});
    const srcB=await imageB.getAttribute('src');
    checkTrue(srcA!==srcB && await page.locator('img[src="'+srcA+'"]').count()===0,
      'Patient A media blob remained visible in true Desktop R3 split of B');
    await page.waitForFunction(url=>window.__dcDosPdfAudit?.revoked?.includes(url),
      srcA,{timeout:15000});
    checkTrue(await mediaB.getByRole('button',{name:'Importer'}).count()===0,
      'Patient B split mounted editable media actions');
    await shot('09-r3-split-patient-b');
    return {desktop_1920_two_real_panes:true,patient_a_identity_verified:true,
      patient_b_identity_verified:true,stale_a_panel_absent:true,
      old_media_blob_revoked:true,no_media_write_controls:true,
      dc_dos02_a_b_canonical_asset_ids_preserved:true,clinical_release:false};
  });
  foreignContext=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce',
    storageState:{cookies:foreignEnrolled.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
  foreignPage=await browserLogin(foreignContext,'t2-dos01-foreign@cabinet.ma');
  await verify('REAL_REACT_FOREIGN_CABINET_OWN_AND_DENIED',async()=>{
    await openPatient(foreignPage,f.patient_x,true);
    await foreignPage.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:40000});
    const label=await foreignPage.locator('[data-ortho-workspace-patient]').innerText();
    checkTrue(label.includes('SYNTHETIC_X'),'Foreign dentist cannot view own X synthetic patient');
    await shot('06-foreign-own-patient',foreignPage);
    await openPatient(foreignPage,f.patient_a);
    await foreignPage.waitForURL(u=>new URL(u).pathname==='/patients/'+f.patient_a,{timeout:30000});
    await foreignPage.waitForTimeout(500);
    checkTrue(await foreignPage.locator('[data-ortho-photo-slot] img[alt="Vue orthodontique"]').count()===0,
      'Foreign Cabinet displayed A media');
    await shot('07-foreign-cannot-open-a',foreignPage);
    return {foreign_own_visible:true,foreign_A_photo_hidden:true};
  });
  await foreignPage.setViewportSize({width:1920,height:1080});
  await verify('REAL_R3_FOREIGN_CABINET_X_SPLIT_AND_A_DENIAL',async()=>{
    const split='[data-r3-1-split="two-columns"]';
    const dossier=split+' [data-v15-071-viewslot="dossier"]';
    await openPatient(foreignPage,f.patient_x,false,'media');
    await foreignPage.locator(split).waitFor({state:'visible',timeout:40000});
    await foreignPage.waitForFunction(sel=>document.querySelector(sel)?.textContent?.includes('T2-DC-DOS01-X'),
      dossier,{timeout:35000});
    const content=await foreignPage.locator(dossier).innerText();
    checkTrue(content.includes('T2-DC-DOS01-X') &&
      !content.includes('T2-0001') && !content.includes('T2-DC-DOS01-B'),
      'Foreign Cabinet X split contains an A/B dossier');
    await foreignPage.locator(split+' [data-v15-071-viewslot="imagerie"]')
      .locator('[data-testid="media-asset-rail"] article').first()
      .waitFor({state:'visible',timeout:35000});
    const foreignMedia=foreignPage.locator(split+' [data-v15-071-viewslot="imagerie"]');
    const foreignOriginal=Number(await foreignMedia.locator('[data-testid="media-asset-rail"] [data-clinical-asset-id]')
      .first().getAttribute('data-clinical-asset-id'));
    const foreignSelected=Number(await foreignMedia.locator('[data-testid="media-inline-viewer"]')
      .getAttribute('data-clinical-asset-id'));
    checkTrue(foreignOriginal===assets.x && foreignSelected===assets.x,
      'DC-DOS-02 foreign cabinet X split lost its original imported ClinicalAsset ID');
    await shot('10-r3-foreign-own-patient-x',foreignPage);

    await openPatient(foreignPage,f.patient_a,false,'media');
    await foreignPage.waitForURL(u=>new URL(u).pathname==='/patients/'+f.patient_a,
      {timeout:30000});
    await foreignPage.waitForTimeout(800);
    checkTrue(await foreignPage.locator(split).count()===0,
      'Foreign Cabinet rendered real MultiView panels from patient A');
    checkTrue(await foreignPage.getByText('T2-0001').count()===0 &&
      await foreignPage.locator('img[src^="blob:"]').count()===0,
      'Foreign Cabinet retained A dossier identity or media blob');
    await shot('11-r3-foreign-cannot-open-a',foreignPage);
    return {foreign_own_x_two_panes:true,foreign_patient_a_split_denied:true,
      dc_dos02_x_canonical_asset_id_preserved:true};
  });
  proof.status='SUBLOT_AUTOMATED_PASS';
}catch(e) {
  proof.status='SUBLOT_FAILED';
  proof.errors.push('RUN_STOPPED: '+String(e));
}finally{
  await ownerContext?.close().catch(()=>{});
  await foreignContext?.close().catch(()=>{});
  await ownerApi?.dispose().catch(()=>{});
  await foreignApi?.dispose().catch(()=>{});
  await browser?.close().catch(()=>{});
  await fs.writeFile(path.join(output,'report.json'),JSON.stringify(proof,null,2));
}
console.log('DC_DOS01_SYNTHETIC_REAL_CABINET_RESULT',JSON.stringify({
  head,status:proof.status,checks:proof.checks.map(x=>({id:x.id,status:x.status})),
  screenshots:proof.shots.length,
}));
checkTrue(proof.status==='SUBLOT_AUTOMATED_PASS' &&
  proof.checks.length===10 && proof.checks.every(x=>x.status==='PASS'),
  'DC-DOS-01 sublot not proven: read report.json, never claim official FUE PASS');
