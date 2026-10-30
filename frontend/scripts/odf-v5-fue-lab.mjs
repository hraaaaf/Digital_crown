/** ODF V5 first-user LAB: actual browser, JWT, public radiograph and signed
 * notes on a disposable SQLite T2 cabinet. NOTHING may reach a clinical DB.
 *
 * Clinical truth: the real X-ray is a licensed *visual illustration*. Landmark
 * coordinates and Angle class in the lab are independent simulated inputs.
 */
import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head=process.env.PRODUCT_HEAD;
const password=process.env.T2_PASSWORD;
const ids=JSON.parse(process.env.P2TER_STUDIES || '{}');
const isolated=process.env.ENVIRONMENT==='test'
 && process.env.DIGITALCROWN_ISOLATED_RUNTIME==='1'
 && process.env.DATABASE_URL==='sqlite:///./t2-runtime-cert.db';
if(!isolated || !/^[a-f0-9]{40}$/.test(head||'') || !password
  || !Number.isSafeInteger(ids.patient_id) || !Number.isSafeInteger(ids.older_id)
  || !Number.isSafeInteger(ids.latest_id))
  throw Error('LAB_ISOLATION_IDENTITY_GUARD_REFUSED');

const root='http://127.0.0.1:5173',backend='http://127.0.0.1:8005';
const out=path.resolve('../artifacts/ortho-v5-first-user-lab');
await fs.mkdir(out,{recursive:true});
const report={head,lab:'ODF_V5_FIRST_USER_ISOLATED', patient_real:false,
  clinical_validation:false,film_diagnosis:false,analysis_from_film:false,
  angle_source:'FICTIONAL_CAST_OBSERVATION_NOT_RADIOGRAPH',
  checks:[],screenshots:[],failures:[],success:false};
const browser=await chromium.launch({headless:true});
const api=await request.newContext({baseURL:backend});
let ctx,page;
const check=(cond,label)=>{if(!cond)throw Error(label);report.checks.push(label)};
const snap=async label=>{
  const name='first-user-'+label+'.png';
  await page.screenshot({path:path.join(out,name),fullPage:false,animations:'disabled'});
  report.screenshots.push(name);
};
try{
  const auth=await api.post('/api/auth/login',
    {form:{username:'odf-lab-dentiste@example.com',password}});
  check(auth.status()===200,'REAL_CABINET_LOGIN_API');
  const token=(await auth.json()).access_token;
  const headers={Authorization:'Bearer '+token};
  const film=await api.get('/api/static/uploads/radios/t2-cephalo-seeded.png',{headers});
  check(film.status()===200,'PUBLIC_LATERAL_CEPHALOGRAM_SERVABLE');
  const media=await film.body();
  check(media.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))
    && media.length > 100000,'REAL_CEPHALOGRAM_IMAGE_NOT_GREY_DUMMY');

  const station=await enrollT2Workstation(api,token,password);
  const stationCookie=station.cookies.filter(c=>c.name==='dc_workstation');
  check(stationCookie.length===1,'REAL_WORKSTATION_ENROLLMENT');

  ctx=await browser.newContext({viewport:{width:1280,height:900},
    acceptDownloads:true,reducedMotion:'reduce',
    storageState:{cookies:stationCookie,origins:[]}});
  page=await ctx.newPage();
  await page.goto(root+'/hub?select=1',{waitUntil:'domcontentloaded'});
  await snap('01-welcome');
  await page.locator('[data-hub-experience="cabinet"]').click();
  await page.locator('input[type=email]').fill('odf-lab-dentiste@example.com');
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/dashboard',{timeout:45000});
  check(await page.evaluate(()=>Boolean(localStorage.getItem('token'))),'REAL_BROWSER_JWT_LOGIN');
  await snap('02-authenticated-dashboard');

  // True first-user discovery: visible dashboard search, patient click,
  // then Imagerie -> Cephalometrie. No deep-link to a seeded study.
  await page.getByRole('heading',{name:/^Bonjour,/}).waitFor({state:'visible',timeout:30000});
  await page.getByRole('button',{name:'Chercher un patient'}).click();
  const search=page.getByRole('textbox',{name:'Chercher un patient'});
  await search.fill('ESSAI-ODF');
  const option=page.locator('#dashboard-patient-search-results button')
    .filter({hasText:'T2-0001'});
  await option.waitFor({state:'visible',timeout:30000});
  await snap('02b-discovered-fictitious-patient');
  await option.click();
  await page.waitForURL(u=>new URL(u).pathname==='/patients/'+ids.patient_id,
    {timeout:30000});
  check(true,'REAL_FIRST_USER_DASHBOARD_PATIENT_DISCOVERY');
  await page.getByRole('button',{name:'Imagerie',exact:true}).click();
  await page.waitForURL(u=>new URL(u).searchParams.get('tab')==='radiology',
    {timeout:30000});
  const modalities=page.locator('[aria-label="Modalités d’imagerie"]');
  await modalities.getByRole('button',{name:'Céphalométrie',exact:true}).click();
  await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:35000});
  check(true,'REAL_IMAGING_AND_CEPHALOMETRY_NAVIGATION');
  await page.getByRole('button',{name:'Historique',exact:true}).click();
  await page.locator('[data-cephalo-history-analysis-id="'+ids.older_id+'"]').click();
  await page.locator('[data-cephalo-selected-analysis-id="'+ids.older_id+'"]')
      .waitFor({state:'visible',timeout:20000});
  await snap('03-real-public-film-selected');
  check(true,'SELECT_EXACT_OLDER_SYNTHETIC_STUDY');
  if(process.env.ODF_G3_MATCHED_ANNOTATIONS==='1'){
    const sourceRead=await api.get('/api/ia/analyses/'+ids.older_id,{headers});
    check(sourceRead.status()===200,'G3_SELECTED_STUDY_READABLE');
    const bound=await sourceRead.json();
    check(bound.image_original_path==='api/static/uploads/radios/t2-cephalo-seeded.png'
      && bound.angles_data?.odf_lab_image_landmark_alignment==='VERIFIED_AARIZ_EXPERT_PAIR'
      && bound.is_calibrated===false && bound.mm_per_pixel==null,
      'G3_SOURCE_BOUND_UNCALIBRATED_EXPERT_STUDY');
    check(createHash('sha256').update(media).digest('hex')===bound.angles_data.odf_lab_display_png_sha256,
      'G3_REAL_DISPLAYED_IMAGE_SHA256_MATCHES_EXPERT_TRACING');
    report.analysis_from_film=true; // Geometric angles only, never diagnosis or metric distances.
  }

  await page.getByRole('button',{name:'3. Synthèse clinique',exact:true}).click();
  await page.getByRole('button',{name:/3. Examen des moulages/}).click();
  await page.locator('textarea[placeholder^="Note libre — auteur non vérifié"]').fill(
    'LAB EXCLUSIVEMENT — Examen fictif des moulages : Angle classe I bilatérale; '
    +'légère DDM maxillaire de -2 mm et mandibulaire de -1 mm. '
    +'Ne provient pas de la radiographie publique.');
  await page.locator('textarea[placeholder^="Note diagnostique libre"]').fill(
    'LAB EXCLUSIVEMENT — Synthèse fictive : relations molaires et canines de '
    +'classe I selon moulages simulés, discret encombrement antérieur. '
    +'Classe squelettique et maturité non déterminées sur cette radio.');
  await page.getByRole('button',{name:/5. Note thérapeutique libre/}).click();
  await page.locator('textarea[placeholder^="Note thérapeutique libre"]').fill(
    'LAB EXCLUSIVEMENT — Plan de démonstration : documenter la croissance, '
    +'réaliser l’examen clinique complet et discuter les objectifs avec le praticien. '
    +'Aucun acte, appareil, extraction ou prescription réelle décidée.');
  // Avoid overwriting the four Angle selections with a late asynchronous
  // "load empty notes" response. The form MUST hydrate before becoming editable.
  await page.getByTestId('odf-note-source-ready').waitFor({state:'attached',timeout:20000});
  for(const name of ['molaire-droite','molaire-gauche','canine-droite','canine-gauche']){
    const select=page.getByTestId('odf-angle-'+name);
    await select.selectOption('Classe I');
    check((await select.inputValue())==='Classe I','ANGLE_CLINICIAN_SELECTION_'+name);
  }
  await snap('04-angle-class-one-fictional-casts');

  const saveButton=page.getByRole('button',{name:'1. Enregistrer le brouillon'});
  await saveButton.click();
  await page.getByRole('status').getByText(/Brouillon enregistré/).waitFor({timeout:40000});
  check(true,'REAL_HTTP_SAVE_DRAFT');
  await snap('05-draft-saved');

  const revResponse=await api.get('/api/ia/analyses/'+ids.older_id,{headers});
  check(revResponse.status()===200,'READ_ACTUAL_SCIENTIFIC_REVISION');
  const persistedStudy=(await revResponse.json()).angles_data;
  const scientific=persistedStudy.scientific_read_path;
  check(scientific.active_chain==='VERIFIED','SYNTHETIC_STUDY_SOURCE_VERIFIED_NOT_REAL_DIAGNOSIS');
  if(process.env.ODF_G4_REQUIRE_TRACE === '1'){
    check(persistedStudy.odf_lab_image_landmark_alignment === 'VERIFIED_AARIZ_EXPERT_PAIR',
      'G4_SOURCE_PAIR_REVOKED_OR_LOST_ON_CLINICIAN_DRAFT_SAVE');
    check(createHash('sha256').update(media).digest('hex')===persistedStudy.odf_lab_display_png_sha256,
      'G4_ACTUAL_FILM_HASH_MUST_SURVIVE_UNCHANGED_CLINICIAN_SAVE');
    check(Array.isArray(persistedStudy._evidence_graph_v1?.landmarks)
          && persistedStudy._evidence_graph_v1.landmarks.length >= 19,
      'G4_PERSISTED_EXPERT_LANDMARKS_MUST_SURVIVE_CLINICIAN_SAVE');
  }
  const noteUrl='/api/patients/'+ids.patient_id+'/ortho-bilan/'+ids.older_id+'/notes';
  const pending=await api.get(noteUrl,{headers,params:{expected_revision:scientific.revision}});
  check(pending.status()===200 && !(await pending.json()).approved,
    'DRAFT_NOT_APPROVED_BEFORE_DENTIST_CONFIRMATION');

  await page.getByRole('button',{name:'2. Approuver mes notes'}).click();
  await page.getByRole('status').getByText(/Notes approuvées par le dentiste/).waitFor({timeout:20000});
  check(true,'REAL_DENTIST_EXPLICIT_APPROVAL');
  await snap('06-notes-approved');
  const signed=await api.get(noteUrl,{headers,params:{expected_revision:scientific.revision}});
  const signedBody=await signed.json();
  check(signed.status()===200 && signedBody.approved===true
    && signedBody.notes.moulages.classe_molaire_droite==='Classe I'
    && signedBody.notes.moulages.classe_molaire_gauche==='Classe I',
    'PERSISTED_STRUCTURED_ANGLE_BILATERAL_AND_SIGNED');

  // Write G5 anatomy AFTER final G3 note-save/revision persistence.
  // Otherwise silentSave could change source digest and revoke a signed curve.
  // G5 TECHNICAL FUE: the automation operates the real SVG drawing UI.
  // Coordinates are synthetic TEST strokes, explicitly NOT anatomical
  // annotations. Only a human-reviewed expert contour can pass visual GO.
  if(process.env.ODF_G5_E2E_SYNTHETIC_STROKES==='1'){
    const g5Url='/api/patients/'+ids.patient_id+'/ortho-bilan/'
      +ids.older_id+'/anatomical-trace';
    const studyRead=await api.get('/api/ia/analyses/'+ids.older_id,{headers});
    check(studyRead.status()===200,'G5_STUDY_READABLE');
    const studyData=(await studyRead.json()).angles_data;
    const revision=studyData.scientific_read_path?.revision;
    check(Number.isSafeInteger(revision) && revision>0,'G5_REVISION_READABLE');
    const surface=page.getByTestId('odf-g5-drawing-surface');
    await surface.waitFor({state:'visible',timeout:30000});
    const ui=page.getByTestId('odf-g5-manual-tracing');
    await ui.getByRole('button',{name:/Base du crâne/}).waitFor({state:'visible'});
    await page.waitForFunction(()=>{const b=[...document.querySelectorAll(
      '[data-testid="odf-g5-manual-tracing"] button')].find(
      b=>b.textContent?.includes('Base du crâne'));
      return Boolean(b && !b.disabled);
    },{timeout:30000});
    // Source-bound VISUAL GUIDE: no coordinates may be copied to a draft.
    // The film is source-matched G3; only explicit user action can reveal the
    // non-clinical, pointer-transparent reference.
    const referenceToggle=ui.getByTestId('g5-reference-toggle');
    await referenceToggle.waitFor({state:'visible'});
    const browserProbe=await page.evaluate(async()=>{
      const url='/api/static/uploads/radios/t2-cephalo-seeded.png';
      const response=await fetch(url,{credentials:'same-origin',cache:'no-store'});
      const b=await response.arrayBuffer();
      const hasCrypto=Boolean(globalThis.crypto?.subtle);
      const digest=hasCrypto?await crypto.subtle.digest('SHA-256',b):null;
      const sha=digest?Array.from(new Uint8Array(digest))
        .map(i=>i.toString(16).padStart(2,'0')).join(''):null;
      return {status:response.status,mime:response.headers.get('content-type'),
        length:b.byteLength,hasCrypto,sha};
    });
    const referenceStudy=(await (await api.get('/api/ia/analyses/'+ids.older_id,
      {headers})).json());
    console.log('G5_REFERENCE_SOURCE_PROBE',JSON.stringify({
      browser:browserProbe,backendFilmSha:createHash('sha256').update(media).digest('hex'),
      studyPath:referenceStudy.image_original_path,
      alignment:referenceStudy.angles_data?.odf_lab_image_landmark_alignment,
      studySha:referenceStudy.angles_data?.odf_lab_display_png_sha256,
      uiStatus:await ui.getByTestId('g5-reference-source-status').innerText(),
      toggleDisabled:await referenceToggle.isDisabled(),
    }));
    const moduleProbe=await page.evaluate(async analysisId=>{
      try{
        const {api,API_BASE}=await import('/src/services/api.ts');
        const ref=await import('/src/features/ortho/utils/g5VisualReference.ts');
        const study=(await api.get('/ia/analyses/'+analysisId)).data;
        const response=await api.get('/static/uploads/radios/t2-cephalo-seeded.png',
          {responseType:'arraybuffer'});
        const bytes=response.data;
        const hash=bytes instanceof ArrayBuffer
          ?Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)))
            .map(v=>v.toString(16).padStart(2,'0')).join(''):null;
        return {apiBase:API_BASE,eligible:ref.isG5ReferenceStudy(study),
          verified:await ref.verifyG5ReferenceFilm(study),
          studyPath:study.image_original_path,
          shaSource:study.angles_data?.odf_lab_display_png_sha256,
          bytesType:Object.prototype.toString.call(bytes),
          mime:response.headers['content-type'],size:bytes?.byteLength,hash};
      }catch(e){return {error:String(e)};}
    },ids.older_id);
    console.log('G5_BROWSER_REFERENCE_MODULE_PROBE',JSON.stringify(moduleProbe));
    await page.waitForFunction(()=>{const el=document.querySelector(
      '[data-testid="g5-reference-toggle"]');return Boolean(el&&!el.hasAttribute('disabled'));},
      null,{timeout:8000});
    check(await referenceToggle.getAttribute('aria-pressed')==='false'
      &&await ui.getByTestId('g5-visual-reference-overlay').count()===0,
      'G5_VISUAL_REFERENCE_HIDDEN_BY_DEFAULT');
    check((await ui.getByTestId('g5-reference-source-status').innerText())
      .includes('Source Aariz vérifiée'),
      'G5_VISUAL_REFERENCE_ACTUAL_FILM_SHA_VERIFIED');
    // The film displayed under the guide must be the authenticated PNG
    // we SHA-verified, not Vite's 200/HTML fallback on a relative /api path.
    await page.waitForFunction(()=>document.querySelector(
      '[data-testid="g5-source-film-image"]')?.getAttribute('href')?.startsWith('blob:'),
      null,{timeout:12000});
    const shownBlob=await page.evaluate(async()=>{
      const href=document.querySelector('[data-testid="g5-source-film-image"]')
        ?.getAttribute('href');
      if(!href||!href.startsWith('blob:'))return null;
      const response=await fetch(href);
      const bytes=await response.arrayBuffer();
      const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)))
        .map(byte=>byte.toString(16).padStart(2,'0')).join('');
      return {size:bytes.byteLength,sha256:actual,
        signature:[...new Uint8Array(bytes.slice(0,8))]};
    });
    check(Boolean(shownBlob&&shownBlob.size>100000
      &&shownBlob.sha256===createHash('sha256').update(media).digest('hex')
      &&JSON.stringify(shownBlob.signature)===JSON.stringify([137,80,78,71,13,10,26,10])),
      'G5_VERIFIED_FILM_BLOB_REAL_SOURCE_PIXELS_RENDERED');
    await referenceToggle.click();
    const reference=ui.getByTestId('g5-visual-reference-overlay');
    await reference.waitFor({state:'visible'});
    check(await reference.locator('path').count()===6
      &&await reference.locator('path[stroke-dasharray="18 18"]').count()===4,
      'G5_VISUAL_REFERENCE_SIX_LAYERS_FOUR_DASHED');
    check((await ui.getByTestId('g5-reference-warning').innerText()).includes('jamais copiée'),
      'G5_VISUAL_REFERENCE_EXPLICIT_NONCLINICAL_WARNING');
    await snap('g5-00-source-verified-reference-readonly');
    const before=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const beforeData=await before.json();
    check(before.status()===200 && beforeData.draft_version===0
      &&!beforeData.approved
      &&beforeData.contours.every(c=>c.points.length===0),
      'G5_REFERENCE_OVERLAY_DOES_NOT_WRITE_OR_APPROVE_DRAFT');
    await referenceToggle.click();
    check(await ui.getByTestId('g5-visual-reference-overlay').count()===0,
      'G5_REFERENCE_HIDE_REMOVES_OVERLAY_WITHOUT_EDIT');

    const noContourApproval=await api.post(g5Url+'/approve',{
      headers,data:{expected_revision:revision,expected_draft_version:1,
        confirmation:'JE_VALIDE_LE_TRACE_ANATOMIQUE'}});
    check(noContourApproval.status()===409,'G5_CANNOT_APPROVE_WITHOUT_MANUAL_STROKES');
    const shortCurve=await api.put(g5Url+'/draft',{headers,data:{
      expected_revision:revision,expected_draft_version:0,
      contours:['cranial_base','maxilla','mandible','upper_incisor',
        'lower_incisor','soft_tissue_profile'].map(id=>({
          id,points:[[100,100],[200,200]],
        })),
    }});
    check(shortCurve.status()===422,'G5_MISSING_REAL_CURVE_LENGTH_REFUSED');

    // Distinct smooth pointer strokes are executed in the actual browser.
    // Their positions are AUTOMATION DEMO, not expert ceph traces.
    const layers=['Base du crâne','Maxillaire','Mandibule',
      'Incisive supérieure','Incisive inférieure','Profil cutané'];
    for(const [i,label] of layers.entries()){
      await ui.getByRole('button',{name:new RegExp(label)}).click();
      await surface.scrollIntoViewIfNeeded();
      const bounds=await surface.boundingBox();
      check(Boolean(bounds&&bounds.width>200&&bounds.height>300),
        'G5_ACTUAL_DRAWING_CANVAS_VISIBLE_'+i);
      const left=bounds.x + 64;
      const top=bounds.y + 34 + i*68;
      await page.mouse.move(left,top);
      await page.mouse.down();
      for(let n=1;n<=27;n++){
        await page.mouse.move(left+n*10,top+n*4+Math.sin(n/3)*9);
      }
      await page.mouse.up();
      const count=await ui.getByRole('button',{name:new RegExp(label)})
        .innerText();
      check(/2[0-9]\/\d+ points minimum/.test(count),
        'G5_BROWSER_POINTER_STROKE_RECORDED_'+i);
    }
    await snap('g5-01-six-browser-strokes-lab-only');
    await ui.getByRole('button',{name:'Enregistrer les six contours'}).click();
    await ui.getByRole('status')
      .getByText(/Brouillon manuel enregistré/).waitFor({timeout:25000});
    const saved=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const savedData=await saved.json();
    check(saved.status()===200&&savedData.draft_version===1
      &&!savedData.approved&&savedData.contours?.length===6,
      'G5_BROWSER_SAVED_SIX_DISTINCT_STROKES');
    await snap('g5-02-manual-strokes-saved-unapproved');

    // Important: a login response updates the request context cookie jar.
    // Do NOT login as secretary using the dentist's APIRequestContext:
    // otherwise subsequent stale-revision probes accidentally run as secretary
    // and report 403 instead of the source-bound 409.
    // Share ONLY the already-enrolled workstation credential. Separate
    // HTTP contexts still isolate dentist/secretary access-token cookie jars.
    const secretaryApi=await request.newContext({
      baseURL:backend,storageState:{cookies:stationCookie,origins:[]},
    });
    try{
      const secretaryLogin=await secretaryApi.post('/api/auth/login',{
        form:{username:'odf-lab-secretaire@example.com',password}});
      check(secretaryLogin.status()===200,'G5_SECRETARY_TEST_ACCOUNT');
      const unauthorized=await secretaryApi.post(g5Url+'/approve',{
        headers:{Authorization:'Bearer '+(await secretaryLogin.json()).access_token},
        data:{expected_revision:revision,expected_draft_version:1,
          confirmation:'JE_VALIDE_LE_TRACE_ANATOMIQUE'},
      });
      const deniedStatus=unauthorized.status();
      console.log('G5_SECRETARY_APPROVAL_PROBE',JSON.stringify({
        http_status:deniedStatus,body:(await unauthorized.text()).slice(0,280),
      }));
      check(deniedStatus===403,'G5_SECRETARY_FORBIDDEN_APPROVAL');
    }finally{
      await secretaryApi.dispose();
    }
    const forgedRevision=await api.get(g5Url,{
      headers,params:{expected_revision:revision+1}});
    const forgedStatus=forgedRevision.status();
    const forgedBody=await forgedRevision.text();
    console.log('G5_STALE_REVISION_PROBE',JSON.stringify({
      requested_revision:revision+1,current_revision:revision,
      http_status:forgedStatus,body:forgedBody.slice(0,350),
    }));
    check(forgedStatus===409,'G5_OTHER_REVISION_REFUSED_HTTP_'+forgedStatus);
    const changedStudy=await api.get(
      '/api/patients/'+ids.patient_id+'/ortho-bilan/'
        +ids.latest_id+'/anatomical-trace',
      {headers,params:{expected_revision:2}});
    check([403,404,409].includes(changedStudy.status()),
      'G5_DIFFERENT_STUDY_NOT_SHARED');
    const outsider=await request.newContext({baseURL:backend});
    const anon=await outsider.get(g5Url,{params:{expected_revision:revision}});
    check(anon.status()===401,'G5_ANONYMOUS_TRACE_REFUSED');
    await outsider.dispose();

    await ui.getByRole('button',{name:'Approuver explicitement le tracé'}).click();
    await ui.getByRole('status')
      .getByText(/Six contours approuvés/).waitFor({timeout:25000});
    const final=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const finalData=await final.json();
    check(final.status()===200&&finalData.approved
      &&finalData.contours.length===6,
      'G5_REAL_BROWSER_EXPLICIT_DENTIST_TEST_APPROVAL');
    await snap('g5-03-six-browser-strokes-test-approved');
    // Prove the real browser PDF action before the reload. After reload,
    // the clinician-notes fingerprint deliberately fails closed; do not
    // bypass it or silently re-save the study (which can revoke G5).
    const [preV2BrowserDownload]=await Promise.all([
      page.waitForEvent('download',{timeout:40000}),
      page.getByRole('button',{name:'3. Exporter le PDF approuvé'}).click(),
    ]);
    const preV2BrowserPdfFile=path.join(out,'V5-Bilan-ODF-Pre-V2-Browser-LAB.pdf');
    await preV2BrowserDownload.saveAs(preV2BrowserPdfFile);
    const preV2BrowserPdf=await fs.readFile(preV2BrowserPdfFile);
    check(preV2BrowserPdf.subarray(0,4).toString('latin1')==='%PDF',
      'SIGNED_NOTES_REAL_PDF_DOWNLOADED');
    check(preV2BrowserPdf.length>200000,'G5_V1_BROWSER_PDF_NONEMPTY');
    report.g5_browser_pre_v2_pdf=path.basename(preV2BrowserPdfFile);
    // G5 V2 E2E: synthetic Bézier nodes are not research/clinical contours.
    // Follow the ACTUAL API save/read/sign/revoke cycle, not only pure unit tests.
    const synthNodes=[
      {anchor:[1300,850],incoming:[1300,850],outgoing:[1340,900]},
      {anchor:[1410,1010],incoming:[1370,955],outgoing:[1450,1065]},
      {anchor:[1540,1180],incoming:[1500,1130],outgoing:[1540,1180]},
    ];
    function sampleG5(nodes){
      const out=[];
      for(let i=0;i<nodes.length-1;i++){
        const a=nodes[i].anchor,c1=nodes[i].outgoing;
        const c2=nodes[i+1].incoming,b=nodes[i+1].anchor;
        const dist=(u,v)=>Math.hypot(u[0]-v[0],u[1]-v[1]);
        const steps=Math.max(2,Math.ceil((dist(a,c1)+dist(c1,c2)+dist(c2,b))/6));
        for(let k=i===0?0:1;k<=steps;k++){
          const t=k/steps,q=1-t;
          const w0=q*q*q,w1=3*q*q*t,w2=3*q*t*t,w3=t*t*t;
          const pt=[0,1].map(d=>Math.round((
            w0*a[d]+w1*c1[d]+w2*c2[d]+w3*b[d])*10)/10);
          if(out.length&&dist(out[out.length-1],pt)<0.5)continue;
          out.push(pt);
        }
      }
      return out;
    }
    const v2Contours=finalData.contours.map(c=>c.id==='soft_tissue_profile'
      ?{id:c.id,points:sampleG5(synthNodes)}
      :{id:c.id,points:c.points});
    const v2Write=await api.put(g5Url+'/draft',{headers,data:{
      expected_revision:revision,expected_draft_version:1,
      contours:v2Contours,bezier_profile_nodes:synthNodes,
    }});
    const v2WriteBody=await v2Write.json();
    check(v2Write.status()===200&&!v2WriteBody.approved&&v2WriteBody.draft_version===2,
      'G5_V2_SAVED_REVOKES_OLD_DENTIST_APPROVAL');
    const v2Read=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const v2ReadBody=await v2Read.json();
    check(v2Read.status()===200&&v2ReadBody.draft_version===2
      &&JSON.stringify(v2ReadBody.bezier_profile_nodes)===JSON.stringify(synthNodes)
      &&JSON.stringify(v2ReadBody.contours.find(c=>c.id==='soft_tissue_profile').points)
        ===JSON.stringify(sampleG5(synthNodes)),
      'G5_V2_REOPEN_HANDLES_AND_PIXEL_SAMPLES_IDENTICAL');
    const badNodes=structuredClone(synthNodes);
    badNodes[1].incoming[0]+=25;
    const v2Mismatch=await api.put(g5Url+'/draft',{headers,data:{
      expected_revision:revision,expected_draft_version:2,
      contours:v2Contours,bezier_profile_nodes:badNodes,
    }});
    check(v2Mismatch.status()===422,'G5_V2_TAMPERED_HANDLE_REFUSED');
    // Reopen the actual React UI, not just the API JSON. A full reload
    // resets the selected modality, study and clinical tab; never rely on
    // React memory or deep-linking directly into an assumed editor.
    async function reopenSelectedG5Study(){
      await page.reload({waitUntil:'domcontentloaded'});
      await page.getByRole('button',{name:'Imagerie',exact:true}).click();
      await page.locator('[aria-label="Modalités d’imagerie"]')
        .getByRole('button',{name:'Céphalométrie',exact:true}).click();
      await page.locator('[data-ortho-workspace-title]')
        .waitFor({state:'visible',timeout:35000});
      await page.getByRole('button',{name:'Historique',exact:true}).click();
      await page.locator('[data-cephalo-history-analysis-id="'+ids.older_id+'"]').click();
      await page.locator('[data-cephalo-selected-analysis-id="'+ids.older_id+'"]')
        .waitFor({state:'visible',timeout:20000});
      await page.getByRole('button',{name:'3. Synthèse clinique',exact:true}).click();
      await page.getByTestId('odf-g5-manual-tracing')
        .waitFor({state:'visible',timeout:30000});
    }
    await reopenSelectedG5Study();
    const reopened=page.getByTestId('odf-g5-manual-tracing');
    await reopened.waitFor({state:'visible',timeout:30000});
    await reopened.getByRole('button',{name:/Profil cutané/}).click();
    const bezierToggle=page.getByTestId('g5-bezier-mode-toggle');
    await bezierToggle.waitFor({state:'visible',timeout:15000});
    await bezierToggle.click();
    const reopenedCanvas=page.getByTestId('odf-g5-bezier-surface');
    await reopenedCanvas.waitFor({state:'visible'});
    const reopenedToggle=page.getByTestId('g5-reference-toggle');
    check(await reopenedToggle.getAttribute('aria-pressed')==='false',
      'G5_REFERENCE_HIDDEN_AGAIN_AFTER_FULL_RELOAD');
    const afterReloadStudy=(await (await api.get(
      '/api/ia/analyses/'+ids.older_id,{headers})).json());
    const afterReloadProbe=await page.evaluate(async id=>{
      try{
        const {api,API_BASE}=await import('/src/services/api.ts');
        const ref=await import('/src/features/ortho/utils/g5VisualReference.ts');
        const study=(await api.get('/ia/analyses/'+id)).data;
        const response=await api.get('/static/uploads/radios/t2-cephalo-seeded.png',
          {responseType:'arraybuffer'});
        const bytes=response.data;
        const sha=bytes instanceof ArrayBuffer
          ?Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)))
            .map(v=>v.toString(16).padStart(2,'0')).join(''):null;
        return {apiBase:API_BASE,eligible:ref.isG5ReferenceStudy(study),
          verified:await ref.verifyG5ReferenceFilm(study),
          studyPath:study.image_original_path,
          align:study.angles_data?.odf_lab_image_landmark_alignment,
          studySha:study.angles_data?.odf_lab_display_png_sha256,
          sha,bytesType:Object.prototype.toString.call(bytes)};
      }catch(e){return {error:String(e)};}
    },ids.older_id);
    console.log('G5_REFERENCE_REOPEN_PROBE',JSON.stringify({
      frontend:afterReloadProbe,backendStudySha:
        afterReloadStudy.angles_data?.odf_lab_display_png_sha256,
      backendAlignment:
        afterReloadStudy.angles_data?.odf_lab_image_landmark_alignment,
      sourceStatus:await reopened.getByTestId('g5-reference-source-status').innerText(),
      toggleDisabled:await reopenedToggle.isDisabled(),
      studyRevision:afterReloadStudy.angles_data?.scientific_read_path?.revision,
    }));
    if(await reopenedToggle.isDisabled()){
      check((await reopened.getByTestId('g5-reference-source-status').innerText())
        .includes('Référence indisponible'),
        'G5_REFERENCE_RELOAD_NETWORK_FAILURE_FAILS_CLOSED');
      const recover=reopened.getByTestId('g5-reference-retry');
      await recover.click();
      await page.waitForFunction(()=>{const toggle=document.querySelector(
        '[data-testid="g5-reference-toggle"]');
        return Boolean(toggle&&!toggle.hasAttribute('disabled'));},
        null,{timeout:25000});
      check(await reopenedToggle.isEnabled(),
        'G5_REFERENCE_EXPLICIT_SOURCE_REVERIFY_AFTER_RELOAD');
    }
    await reopenedToggle.click();
    check(await reopenedCanvas.getByTestId('g5-visual-reference-overlay')
      .locator('path').count()===6,
      'G5_REFERENCE_VISIBLE_IN_BEZIER_MODE');
    await snap('g5-v2-04b-signed-unsigned-reference-in-bezier-test-only');
    await reopenedToggle.click();
    check(await page.getByTestId('g5-bezier-anchor-2').count()===1
      &&await page.getByTestId('g5-bezier-handle-1-incoming').count()===1,
      'G5_V2_BROWSER_REOPEN_VISIBLE_SAVED_ANCHORS_AND_HANDLES');
    await snap('g5-v2-04-reopened-editable-bezier-test-only');
    // Real Chromium pointer interaction: hit the actual SVG handle, let
    // React process pointer capture/move/up, and read source-pixel coordinates
    // from the rendered circle. No DOM event injection or API edit here.
    const handle=page.getByTestId('g5-bezier-handle-1-incoming');
    const anchor=page.getByTestId('g5-bezier-anchor-1');
    await handle.scrollIntoViewIfNeeded();
    const beforeHandle=await handle.evaluate(el=>({
      x:Number(el.getAttribute('cx')),y:Number(el.getAttribute('cy')),
    }));
    const beforeAnchor=await anchor.evaluate(el=>({
      x:Number(el.getAttribute('cx')),y:Number(el.getAttribute('cy')),
    }));
    const hit=await handle.boundingBox();
    const surfaceRect=await reopenedCanvas.boundingBox();
    check(Boolean(hit&&surfaceRect&&hit.width>0&&hit.height>0
      &&surfaceRect.width>250),'G5_V2_REAL_POINTER_HANDLE_HIT_TARGET');
    const fromX=hit.x+hit.width/2,fromY=hit.y+hit.height/2;
    await page.mouse.move(fromX,fromY);
    await page.mouse.down();
    for(let i=1;i<=8;i++){
      await page.mouse.move(fromX+12*i/8,fromY-8*i/8);
    }
    await page.mouse.up();
    const afterHandle=await handle.evaluate(el=>({
      x:Number(el.getAttribute('cx')),y:Number(el.getAttribute('cy')),
    }));
    const afterAnchor=await anchor.evaluate(el=>({
      x:Number(el.getAttribute('cx')),y:Number(el.getAttribute('cy')),
    }));
    check(Number.isFinite(afterHandle.x)&&Number.isFinite(afterHandle.y)
      &&afterHandle.x-beforeHandle.x>25
      &&afterHandle.x-beforeHandle.x<70
      &&beforeHandle.y-afterHandle.y>12
      &&beforeHandle.y-afterHandle.y<60,
      'G5_V2_REAL_MOUSE_DRAG_MOVED_SOURCE_PIXEL_HANDLE');
    check(JSON.stringify(beforeAnchor)===JSON.stringify(afterAnchor)
      &&await page.getByTestId('g5-bezier-anchor-2').count()===1,
      'G5_V2_REAL_DRAG_PRESERVES_ANCHORS_AND_NODE_COUNT');
    const edited=structuredClone(synthNodes);
    edited[1].incoming=[afterHandle.x,afterHandle.y];
    check(JSON.stringify(sampleG5(edited))!==JSON.stringify(sampleG5(synthNodes)),
      'G5_V2_REAL_DRAG_CHANGED_SAMPLED_GEOMETRY');
    await snap('g5-v2-05-real-mouse-drag-before-save-test-only');
    const unchangedOnServer=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const unchangedBody=await unchangedOnServer.json();
    check(unchangedOnServer.status()===200
      &&unchangedBody.draft_version===2
      &&JSON.stringify(unchangedBody.bezier_profile_nodes)===JSON.stringify(synthNodes),
      'G5_V2_DRAG_NOT_PERSISTED_BEFORE_EXPLICIT_SAVE');
    // Save with the REAL UI button, not the previously used API shortcut.
    await reopened.getByRole('button',{name:'Enregistrer les six contours'}).click();
    await reopened.getByRole('status')
      .getByText(/Brouillon manuel enregistré/).waitFor({timeout:25000});
    const editedRead=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const editedBody=await editedRead.json();
    check(editedRead.status()===200&&editedBody.draft_version===3
      &&editedBody.approved===false
      &&JSON.stringify(editedBody.bezier_profile_nodes)===JSON.stringify(edited)
      &&JSON.stringify(editedBody.contours.find(c=>c.id==='soft_tissue_profile').points)
        ===JSON.stringify(sampleG5(edited)),
      'G5_V2_EDIT_RESAVE_REVOCATION');
    check(true,'G5_V2_REAL_MOUSE_DRAG_UI_SAVED_EXACT_SOURCE_GEOMETRY');
    await snap('g5-v2-06-real-mouse-drag-saved-test-only');
    await reopened.getByRole('button',{name:'Approuver explicitement le tracé'}).click();
    await reopened.getByRole('status')
      .getByText(/Six contours approuvés/).waitFor({timeout:25000});
    const verifiedV2=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const verifiedV2Body=await verifiedV2.json();
    check(verifiedV2.status()===200&&verifiedV2Body.approved
      &&verifiedV2Body.draft_version===3
      &&JSON.stringify(verifiedV2Body.bezier_profile_nodes)===JSON.stringify(edited),
      'G5_V2_SIGNED_HANDLES_PERSIST_IN_SAME_STUDY');
    check(true,'G5_V2_SYNTHETIC_EXPLICIT_DENTIST_APPROVAL');
    // A second genuine reload must restore the edited handle and the
    // signed source-pixel polyline, not only a stale local SVG.
    await reopenSelectedG5Study();
    const afterReloadEditor=page.getByTestId('odf-g5-manual-tracing');
    await afterReloadEditor.getByRole('button',{name:/Profil cutané/}).click();
    await page.getByTestId('g5-bezier-mode-toggle').click();
    const loadedHandle=page.getByTestId('g5-bezier-handle-1-incoming');
    await loadedHandle.waitFor({state:'visible',timeout:15000});
    const loadedSource=await loadedHandle.evaluate(el=>({
      x:Number(el.getAttribute('cx')),y:Number(el.getAttribute('cy')),
    }));
    check(JSON.stringify(loadedSource)===JSON.stringify(afterHandle)
      &&await page.getByTestId('g5-bezier-anchor-2').count()===1,
      'G5_V2_REAL_DRAG_EXACT_HANDLE_SURVIVES_FULL_RELOAD');
    const finalRead=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    const finalBody=await finalRead.json();
    check(finalRead.status()===200&&finalBody.approved
      &&JSON.stringify(finalBody.contours.find(c=>c.id==='soft_tissue_profile').points)
        ===JSON.stringify(sampleG5(edited)),
      'G5_V2_REAL_DRAG_SIGNED_POLYLINE_SURVIVES_RELOAD');
    await snap('g5-v2-07-signed-real-drag-reopened-test-only');
    report.g5v2={mode:'SYNTHETIC_BEZIER_NODES_NOT_REAL_ANATOMY',
      status:'V2_REAL_MOUSE_DRAG_UI_SAVE_APPROVE_RELOAD_AND_SIGNED_PDF',
      node_count:edited.length,sampled_points:sampleG5(edited).length,
      browser_mouse_drag:true,ui_saved:true,ui_approved:true,
      handle_index:1,handle_kind:'incoming',
      before_source_px:beforeHandle,after_source_px:afterHandle,
      approved_test_dentist:true,expert_anatomical_validation:false};
    report.g5={mode:'SYNTHETIC_BROWSER_STROKES_NOT_EXPERT_CONTOURS',
      status:'TECHNICAL_E2E_ONLY',approved_test_dentist:true,
      contour_count:6,expert_anatomical_validation:false};
  }


  const blocked=await api.get(
    '/api/patients/'+ids.patient_id+'/ortho-bilan/'+ids.latest_id+'/notes',
    {headers,params:{expected_revision:2}});
  check(blocked.status()===200 && !(await blocked.json()).approved,
    'A_NOTES_NOT_APPROVED_ON_DISTINCT_STUDY_B');

  const secretaryNotesApi=await request.newContext({
    baseURL:backend,storageState:{cookies:stationCookie,origins:[]},
  });
  try{
    const secretary=await secretaryNotesApi.post('/api/auth/login',
      {form:{username:'odf-lab-secretaire@example.com',password}});
    check(secretary.status()===200,'RESTRICTED_TEST_STAFF_HAS_REAL_LOGIN');
    const denied=await secretaryNotesApi.post(noteUrl+'/approve',{
      headers:{Authorization:'Bearer '+(await secretary.json()).access_token},
      data:{expected_revision:scientific.revision,
         expected_draft_version:signedBody.draft_version,
         confirmation:'JE_CONFIRME_MES_NOTES'},
    });
    check(denied.status()===403,'SECRETARY_CANNOT_APPROVE');
  }finally{
    await secretaryNotesApi.dispose();
  }
  const anonymous=await request.newContext({baseURL:backend});
  const deniedAnon=await anonymous.get(noteUrl,
    {params:{expected_revision:scientific.revision}});
  check(deniedAnon.status()===401,'ANONYMOUS_NOTES_ACCESS_REFUSED');
  await anonymous.dispose();

  const pdfFile=path.join(out,'V5-Bilan-ODF-Classe-I-LAB-1280.pdf');
  if(process.env.ODF_G5_E2E_SYNTHETIC_STROKES==='1'){
    // Reload invalidates the browser-only clinician-notes fingerprint. This
    // is deliberate: the UI must refuse export until an explicit re-sign.
    // We have already proven live browser PDF download *before* the reload.
    const uiPdfButton=page.getByRole('button',{name:'3. Exporter le PDF approuvé'});
    check(await uiPdfButton.isDisabled()
      &&await page.getByText(/Après modification ou rechargement du dossier/).isVisible(),
      'G5_V2_RELOADED_NOTES_BROWSER_PDF_FAIL_CLOSED');
    // Now verify the actual signed V2 PDF using the authenticated app API,
    // preserving the source revision and avoiding a silentSave mutation.
    const finalPdfResponse=await api.post('/api/patients/'+ids.patient_id+'/pdf',{
      headers,data:{analysis_id:ids.older_id,
        expected_revision:scientific.revision,archive:false},
    });
    const pdfHeaders=finalPdfResponse.headers();
    check(finalPdfResponse.status()===200
      &&pdfHeaders['x-cephalo-analysis-id']===String(ids.older_id)
      &&pdfHeaders['x-cephalo-revision']===String(scientific.revision),
      'G5_V2_SIGNED_PDF_API_SOURCE_AND_REVISION_BOUND');
    await fs.writeFile(pdfFile,await finalPdfResponse.body());
  }else{
    // Non-G5 flows still prove a real browser-triggered PDF download.
    const [download]=await Promise.all([
      page.waitForEvent('download',{timeout:40000}),
      page.getByRole('button',{name:'3. Exporter le PDF approuvé'}).click(),
    ]);
    await download.saveAs(pdfFile);
    check(true,'SIGNED_NOTES_REAL_PDF_DOWNLOADED');
  }
  const pdf=await fs.readFile(pdfFile);
  check(pdf.subarray(0,4).toString('latin1')==='%PDF','SIGNED_NOTES_REAL_PDF_VALID');
  if(process.env.ODF_G5_E2E_SYNTHETIC_STROKES==='1'){
    check(pdf.length>200000,'G5_REAL_PDF_TWO_VIEWS_NONEMPTY');
    report.g5.pdf=path.basename(pdfFile);
  }
  await snap('07-first-use-success');
  const headerPosition = await page.locator('[data-patient-record-header]').evaluate(
    el => getComputedStyle(el).position);
  check(headerPosition !== 'sticky' && headerPosition !== 'fixed',
    'PATIENT_HEADER_DOES_NOT_OVERLAY_CEPHALOMETRIC_FORMS');
  await snap('07b-no-sticky-header-overlap');
  report.pdf=path.basename(pdfFile);
  report.study={patient_id:ids.patient_id,analysis_id:ids.older_id,
    revision:scientific.revision,draft_version:signedBody.draft_version};

  // Visual responsive continuation, using the SAME authenticated session.
  for(const [width,height] of [[430,932],[768,1024]]){
    await page.setViewportSize({width,height});
    await snap('08-approved-mobile-'+width);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);
    check(!overflow,'NO_GLOBAL_OVERFLOW_'+width);
  }
  report.success=true;
}catch(error){
  report.failures.push(String(error?.stack||error));
  console.error('ODF_LAB_FUE_FAILED',error);
}finally{
  await fs.writeFile(path.join(out,'fue-report.json'),JSON.stringify(report,null,2));
  await ctx?.close();
  await api.dispose();
  await browser.close();
}
if(!report.success)throw Error('ODF_V5_FIRST_USER_LAB_NOT_CERTIFIED');
console.log('ODF_V5_REAL_BROWSER_FUE_PASS',JSON.stringify({head,checks:report.checks.length}));
