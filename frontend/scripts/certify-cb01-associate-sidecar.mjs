/**
 * CB-01 Associate Sidecar — isolated synthetic responsive visual acceptance.
 * This is a preview-only desktop shell, never the real cabinet baseline.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1') {
  throw new Error('REFUSED: isolated T2 required');
}
const apiOrigin = process.env.CB01_T2_API_URL || 'http://127.0.0.1:8005';
const appOrigin = process.env.CB01_T2_APP_URL || 'http://127.0.0.1:5173';
for (const u of [apiOrigin, appOrigin]) {
  const parsed = new URL(u);
  if (parsed.protocol !== 'http:' || !['localhost', '127.0.0.1'].includes(parsed.hostname)
      || parsed.username || parsed.password || parsed.search || parsed.hash
      || (parsed.pathname !== '' && parsed.pathname !== '/')) {
    throw new Error('REFUSED: loopback origins only');
  }
}
const user = process.env.T2_USER, password = process.env.T2_PASSWORD;
const patientId = process.env.T2_PATIENT_ID || '';
if (!user?.startsWith('t2-') || !password || !/^[1-9][0-9]{0,9}$/.test(patientId)) {
  throw new Error('REFUSED: synthetic identity and patient ID needed');
}
const output = path.resolve('../artifacts/cb01-associate-sidecar');
fs.mkdirSync(output, { recursive: true });
const api = await request.newContext({ baseURL: apiOrigin });
const login = await api.post('/api/auth/login', { form: { username:user, password } });
if (!login.ok()) throw new Error('Synthetic auth rejected');
const tokens = await login.json();
const browser = await chromium.launch({ headless:true });
const evidence = [];
try {
  for (const width of [390, 430, 1280, 1440, 1920]) {
    const desktop = width >= 1280;
    const height = desktop ? 900 : 844;
    const context = await browser.newContext({ viewport:{width,height} });
    await context.addInitScript(({access,refresh}) => {
      localStorage.setItem('token',access);
      localStorage.setItem('refresh_token',refresh||'');
      localStorage.setItem('appMode','prod');
    }, {access:tokens.access_token,refresh:tokens.refresh_token});
    const page = await context.newPage();
    const errors=[],writes=[];
    page.on('pageerror',error => errors.push(String(error)));
    page.on('request',req => {
      if (/\/api\/(bot\/execute|appointments\/?|patients\/?|devis\/?)/.test(req.url())
          && req.method() !== 'GET') writes.push(req.method());
    });
    await page.goto(appOrigin+'/dashboard',{waitUntil:'domcontentloaded',timeout:90000});
    const opener=page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
    await opener.waitFor({state:'visible',timeout:30000});
    await page.screenshot({path:path.join(output,'before-'+width+'.png')});
    await opener.click();
    const sidecar=page.locator('[data-cb01-associate-sidecar]');
    const overlay=page.locator('[data-ux1-c-crownbot-overlay]');
    if (desktop) {
      await sidecar.waitFor({state:'visible',timeout:15000});
      if(await overlay.count()) throw new Error('FAIL: hidden duplicate chatbot mounted');
    } else {
      await overlay.waitFor({state:'visible',timeout:15000});
      if(await sidecar.count()) throw new Error('FAIL: sidecar wrongly mounted on fallback');
    }
    const result=await page.evaluate(() => {
      const root=document.documentElement;
      const sidecar=document.querySelector('[data-cb01-associate-sidecar]');
      const overlay=document.querySelector('[data-ux1-c-crownbot-overlay]');
      const main=document.querySelector('main');
      const rect=el => {
        if(!el) return null;
        const r=el.getBoundingClientRect();
        return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right};
      };
      return {
        viewport:root.clientWidth,
        overflow:root.scrollWidth>root.clientWidth+2,
        main:rect(main),sidecar:rect(sidecar),overlay:rect(overlay),
        chatCount:document.querySelectorAll('[data-cb01-associate-sidecar] [aria-label="Simulation ZERO-LLM Crown Bot"], [data-ux1-c-crownbot-overlay] [aria-label="Simulation ZERO-LLM Crown Bot"]').length,
      };
    });
    if (errors.length || writes.length || result.overflow) {
      throw new Error('FAIL: browser errors, writes or page overflow at '+width);
    }
    if (desktop && (!result.sidecar || !result.main
      || result.sidecar.width < 350 || result.sidecar.width > 485
      || result.main.width < 400 || result.main.right>result.sidecar.x+3
      || result.sidecar.right > width+3)) {
      throw new Error('FAIL: sidecar does not preserve clinical workspace at '+width+
        ' '+JSON.stringify(result));
    }
    let staffSearchChecks = 'NOT_RUN_WEB_FALLBACK';
    if (desktop) {
      // S02/S04 browser-backed synthetic staff scenario, not full human UX.
      const panel=page.locator('[data-cb01-associate-sidecar]');
      await panel.getByRole('button',{name:'Chat',exact:true}).click();
      const preview=panel.getByRole('region',{name:'Simulation ZERO-LLM Crown Bot'});
      await preview.waitFor({state:'visible'});
      const findPatient=async selector => {
        await preview.getByRole('button',{name:'Réinitialiser la simulation'}).click();
        await preview.getByRole('button',{name:'/patient'}).click();
        await preview.getByText('Patient : saisissez un identifiant',{exact:false}).waitFor();
        await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill(selector);
        await preview.getByRole('button',{name:'Envoyer'}).click();
      };
      await findPatient('dossier:CB01-N-101');
      await preview.getByText('Patient identifié dans votre cabinet.').waitFor();
      await preview.getByText('Patient identifié : AMINA BENALI — Dossier CB01-N-101').waitFor();

      await findPatient('BENALI');
      await preview.getByText('Plusieurs patients correspondent.',{exact:false}).waitFor();
      const matches=preview.locator('[aria-label="Choisir le dossier patient"] button');
      if(await matches.count()!==2) throw new Error('FAIL: homonyms must show both choices');
      await preview.getByRole('button',{name:/AMINA BENALI.*CB01-N-101/}).click();
      await preview.getByText('Patient identifié : AMINA BENALI — Dossier CB01-N-101').waitFor();

      await findPatient(patientId);
      await preview.getByText('Plusieurs patients correspondent.',{exact:false}).waitFor();
      await preview.getByRole('button',{name:/T2 CERTIFICATION.*T2-0001/}).click();
      await preview.getByText('Patient identifié : T2 CERTIFICATION — Dossier T2-0001').waitFor();
      staffSearchChecks='PASS_DOSSIER_HOMONYMS_NUMERIC_COLLISION';
    }
    await page.screenshot({path:path.join(output,'after-'+width+'.png')});
    evidence.push({width,mode:desktop?'sidecar-reflow':'web-floating-fallback',
      staffSearchChecks,
      result,errors:errors.length,writes:writes.length});
    if(desktop) {
      await page.getByRole('button',{name:'Réduire le panneau Crown Bot'}).click();
      if(await sidecar.count()) throw new Error('FAIL: sidecar did not collapse');
      if(!(await page.getByRole('button',{name:'Ouvrir CrownBot'}).count())) {
        throw new Error('FAIL: Crown Bot reopen control missing');
      }
    }
    await context.close();
  }
  const summary={kind:'CB01_SYNTHETIC_PREVIEW_ONLY',flagDependent:true,
    bSidecarShell:true,clinicalStaffE2E:'NOT_RUN',realCabinetBefore:'NOT_CAPTURED',
    browserZoom200Percent:'NOT_RUN', sourceHead:process.env.CB01_SOURCE_HEAD||'UNVERIFIED',
    evidence};
  fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(summary,null,2));
  console.log('CB01_ASSOCIATE_SIDECAR_VISUAL: PASS',JSON.stringify(evidence));
} finally {
  await browser.close();
  await api.dispose();
}
