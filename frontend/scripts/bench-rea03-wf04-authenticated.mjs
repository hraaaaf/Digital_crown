/** BENCH-REA-03: real authenticated Chromium observation of WF04.
 * Synthetic T2 only; never calls FACAD, never writes clinical records.
 * WF07 is verified separately by the existing P2ter authenticated browser script.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
const ids = JSON.parse(process.env.P2TER_STUDIES || '{}');
if (process.env.ENVIRONMENT !== 'test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    !/^[a-f0-9]{40}$/.test(head || '') ||
    !password || ![ids.patient_id, ids.older_id, ids.latest_id].every(Number.isSafeInteger))
  throw Error('WF04 benchmark requires exact product HEAD, isolated T2, and synthetic study IDs');

const output = path.resolve('../artifacts/bench-rea03-wf04-wf07');
await fs.mkdir(output, { recursive: true });
const base = 'http://127.0.0.1:5173';
const browser = await chromium.launch({headless: true});
const evidence = {
  head, source: 'DRAFT P2TER+ descendants, NOT integrated master',
  dataset: 'SYNTHETIC T2 ONLY', vendor_runtime_executed: false,
  vendor_functional_parity_proven: false, clinical_release: false,
  viewports: [],
};

async function inspect(width,height) {
  const record = {viewport: width+'x'+height, checks:[], screens:[], profiles:[], valid:false};
  const api = await request.newContext({baseURL:'http://127.0.0.1:8005'});
  let context;
  try {
    const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
    if(login.status()!==200) throw Error('T2 login HTTP '+login.status());
    const token=(await login.json()).access_token;
    const enrolled=await enrollT2Workstation(api,token,password);
    const workstation=enrolled.cookies.filter(c=>c.name==='dc_workstation');
    if(workstation.length!==1)throw Error('T2 workstation cookie missing');
    context=await browser.newContext({
      viewport:{width,height},acceptDownloads:false,reducedMotion:'reduce',
      storageState:{cookies:workstation,origins:[]},
    });
    const page=await context.newPage();
    const pageErrors=[];
    page.on('pageerror',e=>pageErrors.push(e.message));
    const shot=async(name)=>{
      const file=record.viewport+'-'+name+'.png';
      await page.screenshot({path:path.join(output,file),animations:'disabled'});
      record.screens.push(file);
    };
    await page.goto(base+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
    await page.locator('[data-hub-experience="cabinet"]').click();
    await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
    await page.locator('input[type=password]').fill(password);
    await page.getByRole('button',{name:'Se connecter',exact:true}).click();
    await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
    if (!await page.evaluate(()=>Boolean(localStorage.getItem('token'))))
      throw Error('Actual Cabinet browser JWT not present');
    record.checks.push('JWT_AUTHENTICATED_BROWSER');
    await page.goto(base+'/patients/'+ids.patient_id+'?tab=radiology&radioTab=cephalo',
      {waitUntil:'domcontentloaded',timeout:45000});
    await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible',timeout:35000});
    await page.getByRole('button',{name:'Historique',exact:true}).click();
    await page.locator('[data-cephalo-history-analysis-id="'+ids.older_id+'"]').click();
    await page.locator('[data-cephalo-selected-analysis-id="'+ids.older_id+'"]')
      .waitFor({state:'visible',timeout:15000});
    const chooser=page.locator('select#cephalo-ready-analysis');
    await chooser.waitFor({state:'visible',timeout:15000});
    record.checks.push('WF04_SELECTED_OLDER_STUDY_AND_STEP1');
    await shot('before-selection');

    async function profile(mode, expectedCount, variant) {
      await chooser.selectOption(mode);
      const panel=page.locator('[data-r23g2-protocol-panel="'+mode+'"]');
      await panel.waitFor({state:'visible',timeout:15000});
      if (variant) {
        const versionButton=panel.locator('[data-r23g2-ricketts-version="'+variant+'"]');
        await versionButton.click();
        if ((await versionButton.getAttribute('aria-pressed'))!=='true')
          throw Error('Ricketts version not active '+variant);
      }
      const table=panel.locator('[data-r23g2-row-count]');
      await table.waitFor({state:'visible',timeout:15000});
      const actual=Number(await table.getAttribute('data-r23g2-row-count'));
      const rows=await panel.locator('[data-r23g2-measurement-id]').count();
      const protocol=await panel.getAttribute('data-r23g2-protocol-id');
      if (actual!==expectedCount || rows!==expectedCount || !protocol || protocol==='UNVERIFIED')
        throw Error('WF04 unexpected '+mode+'/'+(variant||'default')+' rows='+rows+' attr='+actual+' profile='+protocol);
      const ids=await panel.locator('[data-r23g2-measurement-id]').evaluateAll(
        nodes=>nodes.map(n=>n.getAttribute('data-r23g2-measurement-id')));
      if(new Set(ids).size!==expectedCount || ids.some(x=>!x))
        throw Error('WF04 duplicate or missing canonical measurement IDs');
      const summary=await panel.locator('[data-r23g2-coverage]').innerText();
      const entry={mode,variant:variant||null,rows,protocol,unique_canonical_ids:true,coverage_text:summary};
      record.profiles.push(entry);
      await shot(mode+'-'+(variant||'default'));
      return panel;
    }
    const mcnamara=await profile('mcnamara',13,null);
    const selected=mcnamara.locator('[data-r23g3-focus-select]').first();
    await selected.click();
    if ((await selected.getAttribute('aria-pressed'))!=='true')
      throw Error('WF04 focus selection unavailable');
    record.checks.push('WF04_CANONICAL_FOCUS_INTERACTION');
    const atlas=await profile('ricketts',33,'atlas');
    if (await atlas.locator('[data-r23g3-focus-select][aria-pressed="true"]').count()!==0)
      throw Error('WF04 previous analysis focus leaked to Ricketts');
    record.checks.push('WF04_CLEARS_FOCUS_ON_ANALYSIS_SWITCH');
    const firstAtlas=atlas.locator('[data-r23g3-focus-select]').first();
    await firstAtlas.click();
    if ((await firstAtlas.getAttribute('aria-pressed'))!=='true')
      throw Error('WF04 Atlas factor selection unavailable');
    await profile('ricketts',13,'gregoret');
    if(await atlas.locator('[data-r23g3-focus-select][aria-pressed="true"]').count()!==0)
      throw Error('WF04 Atlas focus leaked into Gregoret');
    record.checks.push('WF04_CLEARS_FOCUS_ON_PROFILE_SWITCH');
    if(pageErrors.length)throw Error('Chromium page errors '+JSON.stringify(pageErrors.slice(0,3)));
    record.checks.push('NO_UNCAUGHT_BROWSER_PAGE_ERRORS');
    record.valid=true;
    evidence.viewports.push(record);
    return record;
  } finally {
    await context?.close();
    await api.dispose();
  }
}
try {
  for (const [w,h] of [[1280,900],[1600,1000]]) await inspect(w,h);
  if(evidence.viewports.length!==2 || evidence.viewports.some(v=>!v.valid))
    throw Error('Both browser viewports required');
  await fs.writeFile(path.join(output,'wf04-report.json'),JSON.stringify(evidence,null,2));
  console.log('BENCH_REA03_WF04_PROOF',JSON.stringify(evidence));
} finally {
  await browser.close();
}
