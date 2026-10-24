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
    const before=await api.get(g5Url,{headers,params:{expected_revision:revision}});
    check(before.status()===200 && (await before.json()).draft_version===0,
      'G5_NO_INHERITED_ANATOMY_CONTOURS_BEFORE_DRAWING');
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
      check(deniedStatus===403,'G5_SECRETARY_FORBIDDEN_APPROVAL_HTTP_'+deniedStatus);
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

  // Browser download is triggered by the REAL "Exporter le PDF approuvé" button.
  const downloadPromise=page.waitForEvent('download',{timeout:40000});
  await page.getByRole('button',{name:'3. Exporter le PDF approuvé'}).click();
  const download=await downloadPromise;
  const pdfFile=path.join(out,'V5-Bilan-ODF-Classe-I-LAB-1280.pdf');
  await download.saveAs(pdfFile);
  const pdf=await fs.readFile(pdfFile);
  check(pdf.subarray(0,4).toString('latin1')==='%PDF','SIGNED_NOTES_REAL_PDF_DOWNLOADED');
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
