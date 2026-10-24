/** ODF V5 first-user LAB: actual browser, JWT, public radiograph and signed
 * notes on a disposable SQLite T2 cabinet. NOTHING may reach a clinical DB.
 *
 * Clinical truth: the real X-ray is a licensed *visual illustration*. Landmark
 * coordinates and Angle class in the lab are independent simulated inputs.
 */
import fs from 'node:fs/promises';
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
  const scientific=(await revResponse.json()).angles_data.scientific_read_path;
  check(scientific.active_chain==='VERIFIED','SYNTHETIC_STUDY_SOURCE_VERIFIED_NOT_REAL_DIAGNOSIS');
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

  const blocked=await api.get(
    '/api/patients/'+ids.patient_id+'/ortho-bilan/'+ids.latest_id+'/notes',
    {headers,params:{expected_revision:2}});
  check(blocked.status()===200 && !(await blocked.json()).approved,
    'A_NOTES_NOT_APPROVED_ON_DISTINCT_STUDY_B');

  const secretary=await api.post('/api/auth/login',
    {form:{username:'odf-lab-secretaire@example.com',password}});
  check(secretary.status()===200,'RESTRICTED_TEST_STAFF_HAS_REAL_LOGIN');
  const denied=await api.post(noteUrl+'/approve',{
    headers:{Authorization:'Bearer '+(await secretary.json()).access_token},
    data:{expected_revision:scientific.revision,
       expected_draft_version:signedBody.draft_version,
       confirmation:'JE_CONFIRME_MES_NOTES'},
  });
  check(denied.status()===403,'SECRETARY_CANNOT_APPROVE');
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
