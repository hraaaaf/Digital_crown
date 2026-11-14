/** FUE-G: real Cabinet browser -> authenticated A4 preview -> print or archive
 * -> persisted SQLite + authenticated PDF re-read, synthetic only.
 * This is NOT a clinical signoff or physical printer test (LOT10).
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha=process.env.PRODUCT_HEAD;
const pwd=process.env.T2_PASSWORD;
const seed=JSON.parse(process.env.CEPH_ODF_CASE_JSON||'{}');
const testOnly=process.env.ENVIRONMENT==='test'
  && process.env.DIGITALCROWN_ISOLATED_RUNTIME==='1'
  && process.env.CLOUD_AI_ENABLED==='false'
  && process.env.DATABASE_URL==='sqlite:///./t2-runtime-cert.db'
  && /^[a-f0-9]{40}$/.test(sha||'') && !!pwd
  && seed.fixture_name==='T2-CEPH-ODF-E2E-01'
  && seed.clinical_release===false
  && Number.isSafeInteger(seed.patient_id)
  && Number.isSafeInteger(seed.analysis_id);
if(!testOnly) throw Error('FUE_G_DISPOSABLE_SYNTHETIC_T2_ENV_REQUIRED');

const url='http://127.0.0.1:5173';
const backend='http://127.0.0.1:8005';
const output=path.resolve('../artifacts/ceph-a4-fue-g');
await fs.mkdir(output,{recursive:true});
const report={
  kind:'CEPH_A4_V1_FUE_G_FIRST_USER_EXPERIENCE',
  head:sha,synthetic:true,real_clinical_data:false,
  actual_ui:true,actual_backend:true,actual_sqlite:true,
  physical_printer_test:false,clinical_release:false,
  patient_id:seed.patient_id,analysis_id:seed.analysis_id,
  viewport:'1280x900',checks:[],screenshots:[],failures:[],
  status:'NOT_TESTED',
};
const assert=(yes,reason)=>{if(!yes)throw Error(reason)};
const digest=(bytes)=>crypto.createHash('sha256').update(bytes).digest('hex');
const authHeaders=token=>({Authorization:'Bearer '+token});
let context=null,page=null,api=null,browser=null,prepared=null,token=null;
async function snap(label){
  if(!page)return;
  const file=label+'.png';
  await page.screenshot({path:path.join(output,file),fullPage:false,animations:'disabled'});
  report.screenshots.push(file);
}
async function checkpoint(name,fn){
  try{
    const value=await fn();
    report.checks.push({name,status:'PASS',evidence:value??null});
    console.log('CEPH_A4_FUE_G_PASS '+name);
    return true;
  }catch(error){
    const msg=String(error);
    report.checks.push({name,status:'FAIL',error:msg});
    report.failures.push(name+': '+msg);
    console.error('CEPH_A4_FUE_G_FAIL '+name+' '+msg);
    await snap('fail-'+name.toLowerCase()).catch(()=>{});
    return false;
  }
}
async function documents(){
  const response=await api.get('/api/patients/'+seed.patient_id+'/documents',
    {headers:authHeaders(token)});
  assert(response.status()===200,'DOCUMENT_LIST_HTTP_'+response.status());
  const body=await response.json();
  assert(Array.isArray(body),'DOCUMENT_LIST_INVALID');
  return body;
}
const patientArchiveRows=rows=>rows.filter(item=>
  String(item.clinical_data?.cephalo_analysis_id)===String(seed.analysis_id)
  && String(item.type).includes('RAPPORT_CEPHALO'));

try {
  api=await request.newContext({baseURL:backend});
  browser=await chromium.launch({headless:true});
  const loginOk=await checkpoint('AUTHENTICATED_CABINET_LOGIN',async()=>{
    const res=await api.post('/api/auth/login',{form:{
      username:'t2-browser@cabinet.ma',password:pwd}});
    assert(res.status()===200,'AUTH_HTTP_'+res.status());
    token=(await res.json()).access_token;
    const station=await enrollT2Workstation(api,token,pwd);
    context=await browser.newContext({
      viewport:{width:1280,height:900},acceptDownloads:true,
      storageState:{cookies:station.cookies.filter(c=>c.name==='dc_workstation'),origins:[]},
    });
    page=await context.newPage();
    page.setDefaultTimeout(24000);
    await page.goto(url+'/hub?select=1',{waitUntil:'domcontentloaded'});
    await page.locator('[data-hub-experience="cabinet"]').click();
    await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
    await page.locator('input[type=password]').fill(pwd);
    await page.getByRole('button',{name:'Se connecter',exact:true}).click();
    await page.waitForURL(p=>new URL(p).pathname==='/dashboard',{timeout:50000});
    assert(Boolean(await page.evaluate(()=>localStorage.getItem('token'))),
      'FRONTEND_SESSION_MISSING');
    // A route redirect alone can still display the global splash.
    await page.getByRole('heading',{name:/^Bonjour,/})
      .waitFor({state:'visible',timeout:45000});
    await snap('01-before-open-patient');
    return 'real browser login, workstation cookie, local FastAPI';
  });

  const entered=loginOk&&await checkpoint('OPEN_SELECTED_STUDY_DOCUMENTS',async()=>{
    await page.goto(url+'/patients/'+seed.patient_id+'?tab=radiology&radioTab=cephalo',
      {waitUntil:'domcontentloaded'});
    await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:35000});
    const selected=page.locator('[data-cephalo-selected-analysis-id="'+seed.analysis_id+'"]');
    if(!(await selected.isVisible().catch(()=>false))){
      await page.getByRole('button',{name:'Historique',exact:true}).click();
      await page.locator('[data-cephalo-history-analysis-id="'+seed.analysis_id+'"]').click();
    }
    await selected.waitFor({state:'visible',timeout:30000});
    const exit=page.getByRole('button',{
      name:'Quitter le mode Focus tracé et revenir au dossier'});
    if(await exit.isVisible().catch(()=>false)) await exit.click();
    const step=page.getByRole('button',{name:'4. Documents & stratégie',exact:true});
    await step.click();
    const button=page.getByRole('button',{name:"Préparer l'aperçu A4 à valider"});
    await button.waitFor({state:'visible',timeout:20000});
    const until=Date.now()+24000;
    while(await button.isDisabled()&&Date.now()<until)await page.waitForTimeout(400);
    if (!(await button.isEnabled())) {
      const checks=await page.locator('div').filter({hasText:'Checklist de cohérence documentaire'}).last().innerText().catch(()=>'?');
      const serverAnalysis=await api.get('/api/ia/analyses/'+seed.analysis_id,{headers:authHeaders(token)});
      const analysis=serverAnalysis.status()===200?await serverAnalysis.json():{};
      const scientific=analysis.angles_data?.scientific_read_path ?? {};
      const revision=scientific.revision;
      const validation=Number.isSafeInteger(revision)?await api.get(
        '/api/patients/'+seed.patient_id+'/cephalo-validation?analysis_id='+seed.analysis_id+'&expected_revision='+revision,
        {headers:authHeaders(token)}
      ):null;
      const val=validation?.status()===200?await validation.json():{};
      const diagnosis={
        checks:checks.slice(0,1200),
        analysis_http:serverAnalysis.status(),
        is_calibrated:analysis.is_calibrated,
        mm_per_pixel:analysis.mm_per_pixel,
        scientific_revision:revision,
        validation_http:validation?.status()??null,
        validation_valid:val.valid,
        fatals:val.fatals,
        warnings:val.warnings,
        saveButtonEnabled:await button.isEnabled(),
      };
      report.preflight_diagnostics=diagnosis;
      console.error('CEPH_A4_FUE_G_BLOCKER_DIAGNOSTICS '+JSON.stringify(diagnosis));
      await snap('02-approval-disabled-diagnostics');
    }
    assert(await button.isEnabled(),'APPROVAL_PREVIEW_BUTTON_DISABLED_IN_REAL_UI');
    const before=await documents();
    assert(patientArchiveRows(before).length===0,'ARCHIVE_ALREADY_EXISTS_BEFORE_PREVIEW');
    await snap('02-before-preparation');
    return 'selected study '+seed.analysis_id+' Step4 real button enabled';
  });

  const previewOk=entered&&await checkpoint('REAL_UI_PREPARE_EXACT_A4',async()=>{
    const button=page.getByRole('button',{name:"Préparer l'aperçu A4 à valider"});
    const responsePromise=page.waitForResponse(res=>
      res.request().method()==='POST'
      &&new URL(res.url()).pathname==='/api/patients/'+seed.patient_id+'/cephalo-a4/prepare',
      {timeout:45000});
    await button.click();
    const response=await responsePromise;
    assert(response.status()===200,'PREPARE_HTTP_'+response.status()
      +' '+(await response.text()).slice(0,280));
    prepared=await response.json();
    assert(prepared.analysis_id===seed.analysis_id,'STUDY_ID_MISMATCH');
    assert(prepared.expected_revision>0,'REVISION_MISSING');
    assert(prepared.document_kind==='CEPH_A4_DESCRIPTIVE_APPROVAL_V1','NOT_DESCRIPTIVE');
    assert(prepared.clinical_diagnosis_validated===false,'UNSAFE_CLINICAL_VALIDATION');
    const pdf=Buffer.from(prepared.pdf_base64,'base64');
    assert(pdf.subarray(0,4).equals(Buffer.from('%PDF')),'INVALID_PDF_BYTES');
    assert(digest(pdf)===prepared.pdf_sha256,'PREVIEW_SHA_MISMATCH');
    await page.getByRole('dialog',{name:'Vérification finale du bilan A4'})
      .waitFor({state:'visible',timeout:25000});
    const print=page.getByRole('button',{name:'Imprimer ce bilan A4'});
    const archive=page.getByRole('button',{name:'Valider et archiver ce bilan A4'});
    assert(await print.isDisabled()&&await archive.isDisabled(),
      'APPROVAL_CHECKBOX_DID_NOT_ENFORCE_GATING');
    assert(patientArchiveRows(await documents()).length===0,
      'PDF_PREVIEW_SILENTLY_ARCHIVED');
    const verifiedPreview=page.locator('[data-ceph-a4-pdf-preview="ready"]');
    const confirmation=page.getByRole('checkbox',{
      name:/personnellement vérifié les repères/i,
    });
    assert(await confirmation.isDisabled(),
      'APPROVAL_CHECKBOX_ENABLED_BEFORE_PDF_READY');
    // Ready = exact SHA matched and every PDF.js page painted on real canvas.
    await verifiedPreview.waitFor({state:'visible',timeout:60000});
    const rendered=verifiedPreview.locator('canvas[data-ceph-a4-page-rendered="true"]');
    const renderedCount=await rendered.count();
    assert(renderedCount>0,'A4_PDF_NO_RENDERED_CANVAS');
    assert(await rendered.first().evaluate(el=>el.width>0&&el.height>0),
      'A4_PDF_RENDERED_CANVAS_EMPTY');
    assert(await confirmation.isEnabled(),
      'APPROVAL_CHECKBOX_NOT_AVAILABLE_AFTER_PDF_READY');
    report.preview_sha256=prepared.pdf_sha256;
    report.revision=prepared.expected_revision;
    report.preapproval_pdf_pages_rendered=renderedCount;
    await snap('03-after-a4-preview-before-approval');
    await rendered.first().scrollIntoViewIfNeeded();
    await snap('03b-exact-a4-pdf-review-viewport');
    return {pdf_sha256:prepared.pdf_sha256,bytes:pdf.length,
      revision:prepared.expected_revision,archive_count:0};
  });

  const printOk=previewOk&&await checkpoint('PRINT_ACTION_NEVER_ARCHIVES',async()=>{
    await page.getByRole('checkbox',{
      name:/personnellement vérifié les repères/i,
    }).check();
    const before=patientArchiveRows(await documents()).length;
    let archivePosts=0;
    const watcher=r=>{
      if(r.method()==='POST'
        &&r.url().includes('/cephalo-a4/archive'))archivePosts++;
    };
    page.on('request',watcher);
    const popupP=page.waitForEvent('popup',{timeout:15000});
    await page.getByRole('button',{name:'Imprimer ce bilan A4'}).click();
    const popup=await popupP;
    await popup.locator('iframe').waitFor({state:'attached',timeout:12000});
    const blobSource=await popup.locator('iframe').getAttribute('src');
    assert(blobSource?.startsWith('blob:'),'PRINT_DID_NOT_OPEN_REVIEWED_PDF');
    assert(archivePosts===0,'PRINT_CALLED_ARCHIVE_ENDPOINT');
    assert(patientArchiveRows(await documents()).length===before,
      'PRINT_PERSISTED_OFFICIAL_ARCHIVE');
    await snap('04-after-print-no-archive');
    await popup.close();
    page.off('request',watcher);
    return {archive_post_requests:0,archive_count:before,print_viewer:'blob PDF'};
  });

  const negativeOk=printOk&&await checkpoint('REFUSE_UNAPPROVED_OR_ALTERED_PDF',async()=>{
    const payload={
      analysis_id:seed.analysis_id,
      expected_revision:prepared.expected_revision,
      approval_token:prepared.approval_token,
      pdf_base64:prepared.pdf_base64,approved:false,
    };
    const reject=await api.post('/api/patients/'+seed.patient_id+'/cephalo-a4/archive',
      {headers:authHeaders(token),data:payload});
    assert(reject.status()===422,'MISSING_APPROVAL_NOT_REJECTED_'+reject.status());
    payload.approved=true;
    payload.pdf_base64=Buffer.concat([
      Buffer.from(prepared.pdf_base64,'base64'),Buffer.from('MUTATED')
    ]).toString('base64');
    const altered=await api.post('/api/patients/'+seed.patient_id+'/cephalo-a4/archive',
      {headers:authHeaders(token),data:payload});
    assert(altered.status()===409,'PDF_TAMPER_NOT_REJECTED_'+altered.status());
    assert(patientArchiveRows(await documents()).length===0,
      'NEGATIVE_PATH_PERSISTED_ARCHIVE');
    return {no_checkbox:422,tampered_pdf:409,archive_count:0};
  });

  const archived=negativeOk&&await checkpoint('APPROVE_AND_ARCHIVE_FROM_REAL_UI',async()=>{
    const responseP=page.waitForResponse(res=>
      res.request().method()==='POST'
      &&new URL(res.url()).pathname==='/api/patients/'+seed.patient_id+'/cephalo-a4/archive',
      {timeout:45000});
    await snap('05-before-confirm-archive');
    await page.getByRole('button',{name:'Valider et archiver ce bilan A4'}).click();
    const response=await responseP;
    assert(response.status()===200,'ARCHIVE_HTTP_'+response.status());
    assert(response.headers()['x-cephalo-archive-replayed']==='false',
      'FIRST_ARCHIVE_WRONGLY_REPLAYED');
    assert(response.headers()['x-cephalo-analysis-id']===String(seed.analysis_id),
      'ARCHIVE_IDENTITY_MISMATCH');
    const body=await response.body();
    assert(digest(body)===prepared.pdf_sha256,'ARCHIVE_BYTES_NOT_PREVIEW_BYTES');
    report.archive_id=response.headers()['x-cephalo-archive-id'];
    assert(Number.isSafeInteger(Number(report.archive_id)),'ARCHIVE_DB_ID_MISSING');
    const rows=patientArchiveRows(await documents());
    assert(rows.length===1,'NOT_EXACTLY_ONE_ARCHIVE_AFTER_APPROVAL');
    assert(String(rows[0].id)===String(report.archive_id),'ARCHIVE_LIST_ID_MISMATCH');
    await snap('06-after-confirm-archive');
    return {archive_id:report.archive_id,
      sha256:prepared.pdf_sha256,archive_count:rows.length};
  });

  if(archived) await checkpoint('PERSISTED_RELOAD_DOWNLOAD_AND_IDEMPOTENT_REPLAY',async()=>{
    await page.reload({waitUntil:'domcontentloaded'});
    await page.getByRole('heading',{name:'FICTION-ODF E2E',exact:true})
      .waitFor({state:'visible',timeout:45000});
    const list=patientArchiveRows(await documents());
    assert(list.length===1,'ARCHIVE_MISSING_AFTER_RELOAD');
    const row=list[0];
    assert(row.url==='/api/documents/'+report.archive_id+'/download',
      'OFFICIAL_DOWNLOAD_LINK_NOT_AUTHENTICATED');
    const file=await api.get(row.url,{headers:authHeaders(token)});
    assert(file.status()===200,'OFFICIAL_REDOWNLOAD_'+file.status());
    const fileBytes=await file.body();
    assert(digest(fileBytes)===prepared.pdf_sha256,
      'RETRIEVED_FILE_SHA_MISMATCH');
    const replay=await api.post('/api/patients/'+seed.patient_id+'/cephalo-a4/archive',
      {headers:authHeaders(token),data:{
        analysis_id:seed.analysis_id,expected_revision:prepared.expected_revision,
        approval_token:prepared.approval_token,
        pdf_base64:prepared.pdf_base64,approved:true,
      }});
    assert(replay.status()===200,'REPLAY_HTTP_'+replay.status());
    assert(replay.headers()['x-cephalo-archive-replayed']==='true',
      'REPLAY_DUPLICATED_NEW_ARCHIVE');
    assert(digest(await replay.body())===prepared.pdf_sha256,'REPLAY_BYTES_MISMATCH');
    assert(patientArchiveRows(await documents()).length===1,
      'REPLAY_ADDED_A_DUPLICATE_ARCHIVE');
    // An actual patient UI reload, not only a backend/SQLite readback.
    await page.goto(url+'/patients/'+seed.patient_id+'?tab=archives',
      {waitUntil:'domcontentloaded'});
    await page.locator('[data-flow-patient-surface="archives"]')
      .waitFor({state:'visible',timeout:45000});
    const archiveCard=page.locator('[data-document-kind="canonical"]').filter({
      has:page.getByRole('button',{
        name:'Actions du document '+row.name,exact:true,
      }),
    });
    await archiveCard.waitFor({state:'visible',timeout:45000});
    assert(await archiveCard.count()===1,'ARCHIVE_NOT_UNIQUE_IN_REAL_UI');
    await archiveCard.scrollIntoViewIfNeeded();
    await snap('07-after-reload-persistent-archive');
    // The same approved bytes must be rendered by the authenticated PDF.js UI.
    const uiDownload=page.waitForResponse(res=>
      res.request().method()==='GET'
      &&new URL(res.url()).pathname===row.url,
      {timeout:30000});
    await archiveCard.getByRole('button',{name:'Voir',exact:true}).click();
    const uiPdfResponse=await uiDownload;
    assert(uiPdfResponse.status()===200,
      'UI_PDF_VIEW_HTTP_'+uiPdfResponse.status());
    assert(digest(await uiPdfResponse.body())===prepared.pdf_sha256,
      'UI_VIEWED_PDF_SHA_MISMATCH');
    const pdfCanvas=page.locator(
      '[data-document-pdf-preview] [data-pdf-rendered="true"]');
    await pdfCanvas.waitFor({state:'visible',timeout:45000});
    assert(await pdfCanvas.evaluate(el=>el.width>0&&el.height>0),
      'UI_PDF_CANVAS_EMPTY');
    await snap('08-after-reload-authenticated-pdf-rendered');
    return {authenticated_download:true,exact_sha:true,replay:true,
      archive_count:1,visible_archived_card:true,
      ui_pdf_sha_matches_preview:true,ui_pdf_canvas_rendered:true};
  });
  report.status=report.failures.length===0&&report.checks.length===7
    &&report.checks.every(c=>c.status==='PASS')
    ?'FUE_G_REAL_UI_HTTP_SQLITE_ARCHIVE_CONVERGED_SYNTHETIC'
    :'FUE_G_NO_GO';
}catch(error){
  report.failures.push('UNEXPECTED '+String(error));
  report.status='FUE_G_NO_GO';
}finally{
  await fs.writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
  console.log('CEPH_A4_FUE_G_RESULT '+report.status+' '+
    JSON.stringify({head:sha,passes:report.checks.map(c=>c.name),
      failures:report.failures,clinical_release:false}));
  if(context)await context.close().catch(()=>{});
  if(browser)await browser.close().catch(()=>{});
  if(api)await api.dispose().catch(()=>{});
}
if(report.status!=='FUE_G_REAL_UI_HTTP_SQLITE_ARCHIVE_CONVERGED_SYNTHETIC')
  process.exitCode=1;
