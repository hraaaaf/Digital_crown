/** R23-G FUE-G: REAL public JPEG bytes inside REAL authenticated Cabinet T2.
 * NO real patient, anatomical annotation, calibration or scientific goldset.
 * Browser proves source binding and refuses to turn absent evidence into values.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {chromium, request} from 'playwright';
import {enrollT2Workstation} from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
const manifest = JSON.parse(process.env.CEPH_REAL_PUBLIC_STUDIES || '{}');
if (process.env.ENVIRONMENT !== 'test'
    || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.DATABASE_URL !== 'sqlite:///./t2-runtime-cert.db'
    || !/^[0-9a-f]{40}$/.test(head || '')
    || !password || !Number.isSafeInteger(manifest.patient_id)
    || Object.keys(manifest.cases || {}).sort().join(',') !== 'anug,challiyan'
    || manifest.scientific_goldset !== false)
  throw Error('REFUSED: not the disposable exact-HEAD two-originals T2 lab');

const root = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
const output = path.resolve('../artifacts/ceph-r23g-public-real-cabinet');
await fs.mkdir(output, {recursive:true});
const report = {head, mode:'FUE-G REAL PUBLIC RADIO / REAL CABINET / SCIENCE BLOCKED',
  source:'Wikimedia Commons 2 public originals; attribution CC BY-SA 4.0',
  clinical_release:false, scientific_goldset:false, patient_real:false,
  landmarks_validated:0, calibrations_verified:0, viewports:[], overall:'NOT_TESTED'};
const browser = await chromium.launch({headless:true});
let failed = false;

const sha256 = data => crypto.createHash('sha256').update(data).digest('hex');

async function execute(viewport) {
  const label = viewport.width+'x'+viewport.height;
  const rec = {viewport:label, checks:[], screenshots:[], errors:[], valid:false};
  const api = await request.newContext({baseURL:backend});
  let context, page;
  const shot = async name => {
    const filename = label+'-'+name+'.png';
    await page.screenshot({path:path.join(output,filename),animations:'disabled',fullPage:false});
    rec.screenshots.push(filename);
  };
  const check = async (id,fn) => {
    try {
      const evidence = await fn();
      rec.checks.push({id,status:'PASS',evidence:evidence ?? null});
    } catch(e) {
      rec.checks.push({id,status:'FAIL',reason:String(e)});
      rec.errors.push(id+': '+String(e));
      try {if(page)await shot('failure-'+id.toLowerCase());}catch{}
      throw e;
    }
  };
  try {
    const login = await api.post('/api/auth/login',{
      form:{username:'t2-browser@cabinet.ma',password}
    });
    if(login.status()!==200)throw Error('Login T2 HTTP '+login.status());
    const token=(await login.json()).access_token;
    if(!token)throw Error('No JWT');
    const station=await enrollT2Workstation(api,token,password);
    const cookies=station.cookies.filter(c=>c.name==='dc_workstation');
    if(cookies.length!==1)throw Error('No exact Cabinet workstation cookie');

    context=await browser.newContext({viewport,reducedMotion:'reduce',
      storageState:{cookies,origins:[]},acceptDownloads:true});
    page=await context.newPage();
    page.setDefaultTimeout(30000);
    page.on('pageerror',e=>rec.errors.push('PageError '+e.message));

    await check('REAL_UI_LOGIN_AND_PATIENT_IMAGING',async()=>{
      await page.goto(root+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
      await page.locator('[data-hub-experience="cabinet"]').waitFor({state:'visible'});
      await page.locator('[data-hub-experience="cabinet"]').click();
      await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button',{name:'Se connecter',exact:true}).click();
      await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
      await page.getByRole('heading',{name:/^Bonjour,/}).waitFor({state:'visible'});
      await page.getByRole('button',{name:'Chercher un patient'}).click();
      await page.getByRole('textbox',{name:'Chercher un patient'}).fill('CERTIFICATION');
      await page.locator('#dashboard-patient-search-results button')
        .filter({hasText:'T2-0001'}).click();
      await page.waitForURL(u=>new URL(u).pathname==='/patients/'+manifest.patient_id);
      await page.getByRole('button',{name:'Imagerie',exact:true}).click();
      await page.locator('[aria-label="Modalités d’imagerie"]')
        .getByRole('button',{name:'Céphalométrie',exact:true}).click();
      await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
      await shot('before-public-studies');
      return {patient_id:manifest.patient_id,real_frontend:true,real_fastapi:true};
    });

    for (const name of ['anug','challiyan']) {
      const spec = manifest.cases[name];
      await check(name.toUpperCase()+'_SOURCE_IDENTITY_AND_PROTECTED_JPEG',async()=>{
        if(!Number.isSafeInteger(spec.study_id)||spec.calibration!==null
            ||spec.landmark_count!==0||spec.clinical_release!==false
            ||spec.license!=='CC BY-SA 4.0')throw Error('Seed evidence contract changed');
        const source = await api.get('/'+spec.source_path,{
          headers:{Authorization:'Bearer '+token,Origin:root}
        });
        const data = await source.body();
        if(source.status()!==200 || !String(source.headers()['content-type']).startsWith('image/jpeg')
            || sha256(data)!==spec.sha256)throw Error('Protected JPEG not exact original');
        // IMPORTANT: the authenticated APIRequestContext keeps login/station
        // cookies. An "unauthenticated" request in that context is NOT anonymous.
        // Build a wholly separate, clean context to test the denial accurately.
        const anonymousApi=await request.newContext({baseURL:backend});
        let unauthStatus;
        try {
          const unauth=await anonymousApi.get('/'+spec.source_path);
          unauthStatus=unauth.status();
        } finally {
          await anonymousApi.dispose();
        }
        if(unauthStatus===200)throw Error('Unauthenticated protected media exposed');
        if(![401,403,404].includes(unauthStatus))
          throw Error('Unexpected unauthenticated media response '+unauthStatus);
        const analysis=await api.get('/api/ia/analyses/'+spec.study_id,{
          headers:{Authorization:'Bearer '+token}
        });
        if(analysis.status()!==200)throw Error('Study API HTTP '+analysis.status());
        const x=await analysis.json();
        if(x.id!==spec.study_id || x.image_original_path!==spec.source_path
            || x.is_calibrated!==false || x.mm_per_pixel!=null
            || x.calibration_data!=null || !Array.isArray(x.landmarks_data)
            || x.landmarks_data.length!==0 || (x.angles_data && Object.keys(x.angles_data).length))
          throw Error('Public study has invented evidence or wrong original');
        return {case:name,image_sha256:spec.sha256,width:spec.width,height:spec.height,
          source_http:source.status(),unauth_media_http:unauthStatus,
          study_id:spec.study_id,landmarks:0,calibration:null};
      });

      await check(name.toUpperCase()+'_BEFORE_ACTION_AFTER_TRUE_BROWSER_IMAGE',async()=>{
        await page.getByRole('button',{name:'Historique',exact:true}).click();
        await page.locator('[data-cephalo-history-analysis-id="'+spec.study_id+'"]')
          .waitFor({state:'visible'});
        await shot('before-'+name+'-selection');
        await page.locator('[data-cephalo-history-analysis-id="'+spec.study_id+'"]').click();
        await page.locator('[data-cephalo-selected-analysis-id="'+spec.study_id+'"]')
          .waitFor({state:'visible',timeout:30000});
        await page.waitForFunction(()=>{
          const source=document.querySelector('svg[data-cephalo-viewport="base"] image');
          const url=source?.getAttribute('href') || source?.getAttribute('xlink:href') || '';
          return url.startsWith('blob:');
        },null,{timeout:30000});
        const displayed=await page.evaluate(async()=>{
          const source=document.querySelector('svg[data-cephalo-viewport="base"] image');
          const url=source?.getAttribute('href') || source?.getAttribute('xlink:href');
          if(!url?.startsWith('blob:'))throw Error('Actual protected media did not load as a blob');
          const img=new Image(); img.src=url; await img.decode();
          const bytes=await (await fetch(url)).arrayBuffer();
          const digest=await crypto.subtle.digest('SHA-256',bytes);
          return {width:img.naturalWidth,height:img.naturalHeight,
            sha256:Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,'0')).join(''),
            bytes:bytes.byteLength};
        });
        if(displayed.sha256!==spec.sha256 || displayed.width!==spec.width
           ||displayed.height!==spec.height||displayed.bytes<10000)
          throw Error('Displayed image not exact public JPEG: '+JSON.stringify(displayed));
        await shot('after-'+name+'-actual-public-radio');
        return {...displayed,selected_study:spec.study_id};
      });

      await check(name.toUpperCase()+'_REFERENCE_FAIL_CLOSED_WITHOUT_EVIDENCE',async()=>{
        const selector=page.locator('#cephalo-ready-analysis');
        await selector.waitFor({state:'visible'});
        // Query the REAL authenticated BFF; empty study MUST NOT become VERIFIED.
        const responsePromise=page.waitForResponse(r=>{
          const u=new URL(r.url());
          return u.pathname==='/api/ia/analyses/'+spec.study_id+'/r23g2-reference-profiles'
            && r.request().method()==='GET';
        },{timeout:45000});
        await selector.selectOption('ricketts');
        const response=await responsePromise;
        if(response.status()>=500)
          throw Error('Server error on source-only reference '+response.status());
        let atlasRows=0,gregoretRows=0;
        if(response.status()===200) {
          const payload=await response.json();
          if(payload.analysis_id!==spec.study_id || payload.clinical_release!==false
             || payload.reference_display_only!==true)
            throw Error('Unsafe reference payload identity/authority');
          for(const [slot,expected] of [['ricketts_atlas2009',33],['ricketts_gregoret13',13]]) {
            const rows=payload.profiles?.[slot]?.rows;
            if(!Array.isArray(rows)||rows.length!==expected)
              throw Error('Reference contract rows missing for '+slot);
            for(const row of rows) {
              if(row.availability_status==='AVAILABLE'||row.value!==null
                 ||row.focus_evidence!==undefined||row.classification_authority!==false)
                throw Error('FABRICATED_RUNTIME_OR_FOCUS on real unannotated image '+slot+
                  ' '+row.canonical_measurement_id);
            }
            if(slot==='ricketts_atlas2009')atlasRows=rows.length;
            else gregoretRows=rows.length;
          }
          if(payload.active_chain==='VERIFIED')
            throw Error('Source-less study has falsely VERIFIED active graph');
        } else if(![400,401,403,404,409,422].includes(response.status())) {
          throw Error('Unexpected non-fail-closed reference status '+response.status());
        }
        if(await page.locator('[data-r23g4-focus-authority="verified-runtime"]').count())
          throw Error('Falsely promoted Ricketts Focus in UI');
        await shot('after-'+name+'-ricketts-refusal');
        return {http:response.status(),atlasRows,gregoretRows,
          verified_ricketts_values:0,verified_focus:0,clinical_release:false};
      });
    }
    await check('DESKTOP_LAYOUT_NO_HORIZONTAL_OVERFLOW',async()=>{
      const x=await page.evaluate(()=>({window:innerWidth,
        body:document.body.scrollWidth,html:document.documentElement.scrollWidth}));
      if(Math.max(x.body,x.html)>x.window+2)throw Error('Horizontal overflow '+JSON.stringify(x));
      return x;
    });
    if(rec.errors.length)throw Error(rec.errors.join(' | '));
    rec.valid=true;
  }catch(e){
    if(!rec.errors.some(x=>x.includes(String(e))))rec.errors.push(String(e));
  }finally{
    if(context)await context.close();
    await api.dispose();
  }
  return rec;
}

for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]) {
  const record=await execute(viewport);
  report.viewports.push(record);
  if(!record.valid)failed=true;
  console.log('CEPH_FUE_REAL_PUBLIC',record.viewport,record.valid?'PASS':'FAIL',
    record.checks.map(x=>x.id+':'+x.status).join(','),
    record.errors.join('; '));
}
await browser.close();
report.overall=failed?'FUE_G_FAIL':'FUE_G_PUBLIC_ORIGINALS_REAL_CABINET_NONCLINICAL_PASS';
await fs.writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
await fs.writeFile(path.join(output,'PUBLIC-LICENSE-AND-SCIENCE-LIMITS.json'),
  JSON.stringify({head,scientific_goldset:false,clinical_release:false,
    real_patient:false,annotation_source:'NO HUMAN ANNOTATIONS',
    mm_per_pixel:'UNKNOWN',landmarks_validated:0,
    images:Object.fromEntries(Object.entries(manifest.cases).map(([name,x])=>[name,{
      author:x.author,source:x.source,sha1:x.sha1,sha256:x.sha256,
      license:x.license,dimensions:[x.width,x.height]}])),
    derived_screenshots_license:'CC BY-SA 4.0, based on Wikimedia public originals; marked nonclinical'},
  null,2));
if(failed)process.exitCode=1;
