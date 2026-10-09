// FUE-B: first use of a restricted staff member in an EXISTING synthetic clinic.
// Real login, authenticated tenant API, workstation identity and deep-link RBAC.
// Uses only disposable T2 accounts. Deliberately fails if the UI shows a false cabinet.
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
if (!password || !/^[0-9a-f]{40}$/.test(head || '')) throw Error('FUE-B requires exact HEAD and isolated CI credential');
const backend = 'http://127.0.0.1:8005';
const frontend = 'http://127.0.0.1:5173';
const out = path.resolve('../artifacts/t2-browser/first-user-experience-b');
await fs.mkdir(out, { recursive: true });
const owner = 't2-browser@cabinet.ma';
const employee = 't2-restricted@cabinet.ma';
const api = await request.newContext({ baseURL: backend });
const browser = await chromium.launch({ headless: true });
const results = [];
try {
  const ownerLogin = await api.post('/api/auth/login', { form: { username: owner, password } });
  if (!ownerLogin.ok()) throw Error('Synthetic owner login failed HTTP ' + ownerLogin.status());
  const ownerToken = (await ownerLogin.json()).access_token;
  // A legitimate existing cabinet first enrolls/owns the machine. No bypassing workstation gate.
  const stationState = await enrollT2Workstation(api, ownerToken, password);
  for (const viewport of [{ label: 'mobile-390', width: 390, height: 844 },
                           { label: 'desktop-1280', width: 1280, height: 900 }]) {
    const evidence = { role: 'new restricted staff in existing clinic', viewport: viewport.label, checks: [], screenshots: [], status: 'FAIL' };
    const ctx = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      storageState: stationState, reducedMotion: 'reduce',
    });
    const page = await ctx.newPage();
    const pageErrors = [];
    page.on('pageerror', err => pageErrors.push(err.message));
    const snap = async label => {
      const file = viewport.label + '-' + label + '.png';
      await page.screenshot({ path: path.join(out, file), animations: 'disabled', fullPage: true });
      evidence.screenshots.push(file);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
      if (overflow) throw Error('Horizontal overflow: ' + label);
    };
    try {
      await page.goto(frontend + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.locator('input[type=email]').fill(employee);
      await page.locator('input[type=password]').fill(password);
      await snap('01-login-before');
      await page.getByRole('button', { name: 'Se connecter' }).click();
      await page.waitForURL('**/dashboard', { timeout: 45000 });
      await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({ state: 'visible', timeout: 30000 });
      evidence.checks.push('Real staff login reaches existing clinic Dashboard');
      await snap('02-dashboard-after');
      const token = await page.evaluate(() => localStorage.getItem('token'));
      if (!token) throw Error('Real staff login did not persist its own access token');
      const staffApi = await request.newContext({ baseURL: backend, storageState: await ctx.storageState() });
      try {
        const headers = { Authorization: 'Bearer ' + token };
        const expected = await staffApi.get('/api/admin/cabinet/me', { headers });
        if (!expected.ok()) throw Error('Staff cabinet identity endpoint denied HTTP ' + expected.status());
        const clinic = await expected.json();
        const name = String(clinic?.nom_cabinet || '').trim();
        if (name !== 'Cabinet T2 Certification') throw Error('Staff tenant identity not canonical synthetic cabinet');
        evidence.checks.push('Staff cabinet identity resolved from real tenant API');
        const patient = await staffApi.get('/api/patients/', { headers });
        if (patient.status() !== 403) throw Error('Restricted staff patient API must be HTTP 403, got ' + patient.status());
        evidence.checks.push('Real backend denies restricted staff access to patients');
        if (viewport.width >= 1024) {
          // Product header must reflect the authenticated tenant, not hardcoded localStorage.
          const display = page.getByText(name, { exact: true });
          await display.first().waitFor({ state: 'visible', timeout: 10000 });
          evidence.checks.push('Desktop header reflects the actual clinic for restricted staff');
        }
      } finally {
        await staffApi.dispose();
      }
      if (await page.getByRole('link', { name: 'Patients', exact: true }).count()) {
        throw Error('Restricted staff sees patient navigation');
      }
      await page.goto(frontend + '/patients', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.waitForURL('**/dashboard', { timeout: 25000 });
      await page.goto(frontend + '/settings', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.waitForURL('**/dashboard', { timeout: 25000 });
      evidence.checks.push('Deep links /patients and /settings are refused for restricted staff');
      await page.goto(frontend + '/agenda', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.waitForURL('**/agenda', { timeout: 25000 });
      await page.getByRole('heading', { name: 'Agenda', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
      await page.locator('[data-testid="agenda-active-view"]').waitFor({ state: 'visible', timeout: 30000 });
      evidence.checks.push('Permitted staff agenda renders actual calendar');
      await snap('03-agenda-permitted');
      if (pageErrors.length) throw Error('Uncaught browser exception(s): ' + pageErrors.length);
      evidence.status = 'PASS';
      console.log(JSON.stringify({ phase: 'FUE-B', viewport: viewport.label, status: 'PASS', head }));
    } catch (err) {
      evidence.failure = String(err?.message || err).slice(0,500);
      console.log(JSON.stringify({ phase: 'FUE-B', viewport: viewport.label, status: 'FAIL', reason: evidence.failure, head }));
    } finally {
      results.push(evidence);
      await ctx.close();
    }
  }
} catch (err) {
  results.push({ phase: 'bootstrap', status: 'FAIL', failure: String(err?.message || err).slice(0,500) });
} finally {
  await browser.close();
  await api.dispose();
}
const summary = {
  head, scope: 'real staff login in seeded existing clinic; authenticated tenant identity, patient RBAC, route guard and agenda; synthetic workstation',
  status: results.length === 2 && results.every(x => x.status === 'PASS') ? 'PASS' : 'FAIL', cases: results,
};
await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(summary, null, 2));
if (summary.status !== 'PASS') process.exitCode = 1;
