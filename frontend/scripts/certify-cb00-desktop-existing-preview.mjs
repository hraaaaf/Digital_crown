/**
 * CB-00: existing FLAGGED desktop preview only, not owner-selected B.
 * Synthetic CI at 1280/1440/1920; click to useful DOM.
 */
import fs from 'node:fs';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { chromium, request } from 'playwright';

const loopback = value => {
  const u = new URL(value);
  if (u.protocol !== 'http:' || !['127.0.0.1','localhost'].includes(u.hostname)
      || u.username || u.password || u.pathname !== '/' || u.search || u.hash) {
    throw new Error('REFUSED: isolated HTTP loopback only');
  }
  return u.origin;
};
if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1') {
  throw new Error('REFUSED: T2 isolation assertion missing');
}
const appUrl = loopback(process.env.CB00_T2_APP_URL || 'http://127.0.0.1:5173');
const apiUrl = loopback(process.env.CB00_T2_API_URL || 'http://127.0.0.1:8005');
const user = process.env.T2_USER, password = process.env.T2_PASSWORD;
const patientId = process.env.T2_PATIENT_ID || '';
if (!user?.startsWith('t2-') || !password || !/^[1-9]\d{0,9}$/.test(patientId)) {
  throw new Error('REFUSED: synthetic user/password/patient ID required');
}
const output = path.resolve('../artifacts/cb00-desktop-existing-preview');
fs.mkdirSync(output, { recursive: true });
const percentile = (values, f) => {
  const a = [...values].sort((x,y) => x-y), x = (a.length-1)*f;
  const lo = Math.floor(x), hi = Math.ceil(x);
  return Math.round((a[lo] + (a[hi]-a[lo])*(x-lo))*100)/100;
};
const api = await request.newContext({ baseURL: apiUrl });
const login = await api.post('/api/auth/login', { form: { username:user, password } });
if (!login.ok()) throw new Error('Synthetic login failed');
const tokens = await login.json();
const browser = await chromium.launch({ headless:true });
const results = [];
try {
  for (const width of [1280,1440,1920]) {
    const context = await browser.newContext({ viewport:{ width, height:900 } });
    await context.addInitScript(({ access,refresh }) => {
      localStorage.setItem('token', access);
      localStorage.setItem('refresh_token',refresh||'');
      localStorage.setItem('appMode','prod');
    }, { access:tokens.access_token, refresh:tokens.refresh_token });
    const page = await context.newPage(), errors=[], writes=[];
    page.on('pageerror',e=>errors.push(String(e)));
    page.on('request',req=>{
      if (/\/api\/(bot\/execute|appointments\/?|patients\/?|devis\/?)/.test(req.url())
          && req.method()!=='GET') writes.push(req.method());
    });
    await page.goto(appUrl+'/dashboard',{waitUntil:'domcontentloaded',timeout:90000});
    const opener = page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
    await opener.waitFor({state:'visible',timeout:30000});
    const t0=performance.now();
    await opener.click();
    const overlay=page.locator('[data-ux1-c-crownbot-overlay]');
    await overlay.waitFor({state:'visible',timeout:15000});
    const firstOpenMs=performance.now()-t0;
    await page.getByRole('button',{name:'Chat',exact:true}).click();
    const preview=page.getByRole('region',{name:'Simulation ZERO-LLM Crown Bot'});
    await preview.waitFor({state:'visible'});
    const before='existing-flagged-preview-'+width+'.png';
    await page.screenshot({path:path.join(output,before)});
    const samples=[];
    for(let i=0;i<31;i++){
      await preview.getByRole('button',{name:'Réinitialiser la simulation'}).click();
      await preview.getByRole('button',{name:'/patient'}).click();
      await preview.getByText('Identifiant numérique du patient ?').waitFor({state:'visible'});
      await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill(patientId);
      const started=performance.now();
      const responsePromise=page.waitForResponse(r=>
        r.url().includes('/api/bot/workflows/preview') && r.request().method()==='POST',
        {timeout:15000});
      await preview.getByRole('button',{name:'Envoyer'}).click();
      const response=await responsePromise;
      if(response.status()!==200)throw new Error('Useful read HTTP '+response.status());
      await preview.getByText('Patient identifié dans votre cabinet.').waitFor({
        state:'visible',timeout:15000,
      });
      if(i>0)samples.push(performance.now()-started);
    }
    const after='existing-flagged-preview-useful-'+width+'.png';
    await page.screenshot({path:path.join(output,after)});
    const geometry=await page.evaluate(()=>{
      const el=document.querySelector('[aria-label="Simulation ZERO-LLM Crown Bot"]');
      const r=el?.getBoundingClientRect();
      return {
        overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+2,
        panelOverflow:Boolean(el&&el.scrollWidth>el.clientWidth+2),
        bounds:r?{x:r.x,width:r.width}:null,
      };
    });
    if(errors.length||writes.length||geometry.overflow||geometry.panelOverflow||
       !geometry.bounds||geometry.bounds.x < -1||
       geometry.bounds.x+geometry.bounds.width>width+1){
      throw new Error('Runtime errors, clinical writes or overflow at '+width);
    }
    results.push({
      viewport:{width,height:900},before,after,firstOpenMs:Number(firstOpenMs.toFixed(2)),
      samples:30,warmClickDomP50Ms:percentile(samples,.5),
      warmClickDomP95Ms:percentile(samples,.95),
      maxMs:Math.round(Math.max(...samples)*100)/100,
      errors:errors.length,writes:writes.length,geometry,
      note:'Existing flagged preview only; NOT shipped flag-OFF baseline, B or AFTER',
    });
    await context.close();
  }
  const summary={
    kind:'CB00_EXISTING_FLAGGED_PREVIEW_SYNTHETIC_CI',
    sourceHead:process.env.CB00_SOURCE_HEAD||'UNVERIFIED',
    bImplemented:false,humanValidation:'NOT_RUN',databaseDelta:'NOT_MEASURED',
    realCabinetBefore:'NOT_CAPTURED',results,
  };
  fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(summary,null,2));
  console.log('CB00_DESKTOP_SYNTHETIC_METRICS',JSON.stringify(results.map(
    r=>({width:r.viewport.width,firstOpenMs:r.firstOpenMs,
         warmClickDomP50Ms:r.warmClickDomP50Ms,warmClickDomP95Ms:r.warmClickDomP95Ms})
  )));
} finally {
  await browser.close();
  await api.dispose();
}
