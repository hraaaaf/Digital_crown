/** CEPH-UXCLIN-01 / R23-G4. Authenticated REAL Cabinet desktop UI,
 * disposable T2 patient and two source-locked revisions only.
 * An SVG/clinical truth or historical master COM BEFORE is NOT certified.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
const ids = JSON.parse(process.env.P2TER_STUDIES || '{}');
if (process.env.ENVIRONMENT !== 'test' || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
  || !/^[a-f0-9]{40}$/.test(head || '') || !password
  || ![ids.patient_id, ids.older_id, ids.latest_id].every(Number.isSafeInteger)
  || ids.older_id >= ids.latest_id) {
  throw Error('R23-G4 evidence requires disposable exact-HEAD T2 context and two synthetic studies');
}
const root = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
const output = path.resolve('../artifacts/ceph-r23g4-reference-ui');
await fs.mkdir(output, {recursive:true});
const report = {head, scope:'CEPH-UXCLIN-01/R23-G4 STAGE3 DESKTOP REFERENCE ONLY',
  clinical_release:false, independent_ortho_review:false,
  before_semantics:'stable all-analysis tab at same viewport, NOT prior COM master screenshot',
  after_semantics:'new opt-in verified reference tab',
  viewports:[], overall:'NOT_TESTED'};
const browser = await chromium.launch({headless:true});

async function viewportRun(viewport) {
  const label = viewport.width + 'x' + viewport.height;
  const rec = {viewport:label, checks:[], shots:[], errors:[], valid:false};
  let heldComRowId = null;
  const api = await request.newContext({baseURL:backend});
  let context;
  let page;
  // Keep medically relevant toasts fully functional. A stable AFTER
  // screenshot must wait for the transient toast to fade, never hide/alter it.
  const waitForTransientToasts = async () => {
    await page.waitForFunction(() => {
      const statuses = Array.from(document.querySelectorAll('[data-rht-toaster] [role="status"]'));
      return statuses.every(node => {
        const s = window.getComputedStyle(node);
        const r = node.getBoundingClientRect();
        return s.display === 'none' || s.visibility === 'hidden'
          || Number(s.opacity) < 0.02 || r.width === 0 || r.height === 0;
      });
    }, null, {timeout:15000});
  };
  const shot = async name => {
    // Only AFTER is UI-approval material; real-time toasts are not removed.
    if (name.startsWith('after-')) await waitForTransientToasts();
    const filename = label + '-' + name + '.png';
    await page.screenshot({path:path.join(output, filename), fullPage:false, animations:'disabled'});
    rec.shots.push(filename);
  };
  const check = async (id, run) => {
    try {
      const value = await run();
      rec.checks.push({id,status:'PASS', evidence:value ?? null});
    } catch(error) {
      rec.checks.push({id,status:'FAIL',reason:String(error)});
      rec.errors.push(id + ': ' + String(error));
      try {if(page)await shot('failure-'+id.toLowerCase());} catch {}
      throw error;
    }
  };
  try {
    const login = await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
    if(login.status()!==200)throw Error('T2 auth cannot bootstrap: '+login.status());
    const token=(await login.json()).access_token;
    const station=await enrollT2Workstation(api,token,password);
    const cookies=station.cookies.filter(c=>c.name==='dc_workstation');
    if(cookies.length!==1)throw Error('Expected exact Cabinet workstation cookie');
    context=await browser.newContext({viewport, acceptDownloads:true,reducedMotion:'reduce',
      storageState:{cookies,origins:[]}});
    page=await context.newPage();
    page.setDefaultTimeout(30000);
    page.on('pageerror',err=>rec.errors.push('PageError: '+err.message));
    await check('GENUINE_CABINET_LOGIN_AND_STUDY_SELECTION',async()=>{
      await page.goto(root+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
      await page.locator('[data-hub-experience="cabinet"]').waitFor({state:'visible'});
      await page.locator('[data-hub-experience="cabinet"]').click();
      await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button',{name:'Se connecter',exact:true}).click();
      await page.waitForURL(url=>new URL(url).pathname==='/dashboard',{timeout:45000});
      await page.getByRole('heading',{name:/^Bonjour,/}).waitFor({state:'visible'});
      await page.getByRole('button',{name:'Chercher un patient'}).click();
      await page.getByRole('textbox',{name:'Chercher un patient'}).fill('CERTIFICATION');
      const result=page.locator('#dashboard-patient-search-results button').filter({hasText:'T2-0001'});
      await result.waitFor({state:'visible'});
      await result.click();
      await page.waitForURL(url=>new URL(url).pathname==='/patients/'+ids.patient_id);
      await page.getByRole('button',{name:'Imagerie',exact:true}).click();
      await page.waitForURL(url=>new URL(url).searchParams.get('tab')==='radiology');
      const modalities=page.locator('[aria-label="Modalités d’imagerie"]');
      await modalities.getByRole('button',{name:'Céphalométrie',exact:true}).click();
      await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
      await page.getByRole('button',{name:'Historique',exact:true}).click();
      await page.locator('[data-cephalo-history-analysis-id="'+ids.older_id+'"]').click();
      await page.locator('[data-cephalo-selected-analysis-id="'+ids.older_id+'"]').waitFor({state:'visible'});
      await page.locator('#cephalo-ready-analysis').waitFor({state:'visible'});
      await shot('before-from-stable-all');
      return {patient_id:ids.patient_id,study_id:ids.older_id,legitimate_user_ui:true};
    });
    await check('COM10_SOURCE_ROWS_EXACT_REVISION',async()=>{
      const responsePromise=page.waitForResponse(res=>{
        const uri=new URL(res.url());
        return uri.pathname==='/api/ia/analyses/'+ids.older_id+'/r23g2-reference-profiles'
            && uri.searchParams.get('expected_revision')!==null
            && res.request().method()==='GET';
      },{timeout:45000});
      await page.locator('#cephalo-ready-analysis').selectOption('com');
      const response=await responsePromise;
      if(response.status()!==200)throw Error('R23-G4 opt-in API returned '+response.status());
      const data=await response.json();
      if(data.analysis_id!==ids.older_id || !Number.isSafeInteger(data.revision) || data.revision<=0
        || data.clinical_release!==false || data.reference_display_only!==true
        || data.profiles?.com?.rows?.length!==10)throw Error('Source/identity safety contract absent');
      // Choose a row without explicit runtime Focus evidence. Do not search for
      // the text "NC": it also occurs inside the French word "interincisif".
      heldComRowId=data.profiles.com.rows.find(row=>!row.focus_evidence)?.canonical_measurement_id ?? null;
      const panel=page.locator('[data-r23g4-reference-panel="com"]');
      await panel.waitFor({state:'visible'});
      const table=panel.locator('table[data-r23g4-row-count="10"]');
      await table.waitFor({state:'visible'});
      if(await table.locator('tbody tr').count()!==10)throw Error('COM table cardinality not ten');
      if(await panel.getByText('non certifiée cliniquement',{exact:false}).count()!==1)
        throw Error('Clinical HOLD label absent');
      if(await panel.locator('[data-r23g4-qa-image]').count()!==1)
        throw Error('T2 QA raster must be explicitly identified as synthetic, never patient radiography');
      await shot('after-com-ten-factor');
      return {analysis_id:data.analysis_id,revision:data.revision,count:10,clinical_release:false};
    });
    await check('NO_FABRICATED_FOCUS_ON_COM_HOLD',async()=>{
      const panel=page.locator('[data-r23g4-reference-panel="com"]');
      if(!heldComRowId)throw Error('No COM row without source Focus evidence to test');
      const held=panel.locator(`tbody tr[data-r23g4-factor="${heldComRowId}"]`);
      if(await held.count()!==1)throw Error('Exact COM row without Focus evidence is absent');
      await held.locator('button[data-r23g4-focus-select]').click();
      const evidence=held.locator('[data-r23g4-focus-authority="refused"]');
      await evidence.waitFor({state:'visible'});
      if(await evidence.getByText('Focus non autorisé',{exact:false}).count()!==1)
        throw Error('NC Focus not explicitly denied');
      await shot('after-com-focus-hold');
      return 'Row remains NC and no Focus event/geometry is authorized';
    });
    await check('RICKETTS_ATLAS33_VS_GREGORET13',async()=>{
      await page.locator('#cephalo-ready-analysis').selectOption('ricketts');
      const panel=page.locator('[data-r23g4-reference-panel="ricketts"]');
      await panel.waitFor({state:'visible'});
      await panel.locator('table[data-r23g4-row-count="33"]').waitFor({state:'visible'});
      await shot('after-ricketts-atlas33');
      await panel.locator('[data-r23g4-version="gregoret"]').click();
      await panel.locator('table[data-r23g4-row-count="13"]').waitFor({state:'visible'});
      await shot('after-ricketts-gregoret13');
      return 'Source-locked Atlas 33 and Gregoret 13 without classification';
    });
    await check('SECOND_STUDY_HAS_NO_STALE_REFERENCE',async()=>{
      await page.getByRole('button',{name:'Historique',exact:true}).click();
      await page.locator('[data-cephalo-history-analysis-id="'+ids.latest_id+'"]').click();
      await page.locator('[data-cephalo-selected-analysis-id="'+ids.latest_id+'"]').waitFor({state:'visible'});
      const selector=page.locator('#cephalo-ready-analysis');
      await selector.waitFor({state:'visible'});
      // A newly selected study opens in the default "all" view.
      // Fetch the opt-in reference only once COM is selected on study B.
      const responsePromise=page.waitForResponse(res=>new URL(res.url()).pathname
        ==='/api/ia/analyses/'+ids.latest_id+'/r23g2-reference-profiles'
          && res.request().method()==='GET',{timeout:45000});
      await selector.selectOption('com');
      const response=await responsePromise;
      if(response.status()!==200)throw Error('Other study reference HTTP '+response.status());
      const data=await response.json();
      if(data.analysis_id!==ids.latest_id || data.clinical_release!==false)
        throw Error('Cross-study reference leaked/was not rebound');
      await page.locator('[data-r23g4-reference-panel="com"] table[data-r23g4-row-count="10"]').waitFor({state:'visible'});
      if(await page.locator('[data-r23g4-focus-authority="verified-runtime"]').count())
        throw Error('Stale prior Focus was retained across selected study');
      await shot('after-other-study-rebound');
      return {study_id:data.analysis_id,revision:data.revision};
    });
    await check('COM_LAST_FACTOR_ACCESSIBLE_AND_UNOBSCURED',async()=>{
      const panel=page.locator('[data-r23g4-reference-panel="com"]');
      const scroller=panel.locator('.overflow-auto').first();
      const table=panel.locator('table[data-r23g4-row-count="10"]');
      const last=table.locator('tbody tr').last();
      await last.scrollIntoViewIfNeeded();
      await waitForTransientToasts();
      const readable=await page.evaluate(() => {
        const panel=document.querySelector('[data-r23g4-reference-panel="com"]');
        const scroller=panel?.querySelector('.overflow-auto');
        const row=panel?.querySelector('tbody tr:last-child');
        if(!scroller||!row)return null;
        const r=row.getBoundingClientRect(),c=scroller.getBoundingClientRect();
        return {rowTop:r.top,rowBottom:r.bottom,scrollTop:c.top,scrollBottom:c.bottom,
          bottomPadding:parseFloat(getComputedStyle(scroller).paddingBottom)||0,
          viewportHeight:innerHeight};
      });
      if(!readable || readable.bottomPadding<120 || readable.rowBottom>readable.scrollBottom+1
        || readable.rowTop<readable.scrollTop-1)
        throw Error('Reference last factor is unreachable or unsafe toasts obstruct its scrolling: '+JSON.stringify(readable));
      await shot('after-com-last-factor-accessible');
      return readable;
    });
    await check('NO_DESKTOP_VIEWPORT_OVERFLOW',async()=>{
      const dimensions=await page.evaluate(()=>({width:innerWidth,
        body:document.body.scrollWidth,html:document.documentElement.scrollWidth}));
      if(Math.max(dimensions.body,dimensions.html)>dimensions.width+2)
        throw Error('Horizontal overflow '+JSON.stringify(dimensions));
      return dimensions;
    });
    if(rec.errors.length)throw Error('Browser page errors: '+rec.errors.join(' | '));
    rec.valid=true;
  } catch(error) {
    if(!rec.errors.some(x=>x.includes(String(error))))rec.errors.push(String(error));
  } finally {
    if(context)await context.close();
    await api.dispose();
  }
  return rec;
}
try {
  for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]) {
    report.viewports.push(await viewportRun(viewport));
  }
  report.overall=report.viewports.length===2 && report.viewports.every(x=>x.valid)
    ? 'R23_G4_EXPERIMENTAL_DESKTOP_AFTER_PASS' : 'FAIL';
} finally {
  await browser.close();
  await fs.writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
}
console.log('R23_G4_REFERENCE_UI_DESKTOP_PROOF',JSON.stringify(report));
if(report.overall==='FAIL')process.exitCode=1;
