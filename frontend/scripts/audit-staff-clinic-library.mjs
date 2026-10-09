// Staff/Clinic/Library independent audit. Run on disposable T2 SQLite only.
// Real login and workstation enrollment for A/B owner and C/D staff in four
// isolated Chromium contexts. Reference library is local static data: this
// harness observes access without silently inventing clinical policy.
import { chromium, request } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD, password = process.env.T2_PASSWORD;
if (!/^[0-9a-f]{40}$/.test(head || '') || !password || process.env.T2_STAFF_AUDIT !== '1')
  throw Error('Exact HEAD and disposable staff fixture required');
const root = path.resolve('../artifacts/staff-library');
await fs.mkdir(root, { recursive: true });
const base = 'http://127.0.0.1:5173', backend = 'http://127.0.0.1:8005';
const actors = [
  { role: 'A', email: 't2-browser@cabinet.ma', staff: false, vp: { width: 1280, height: 900 } },
  { role: 'B', email: 't2-browser@cabinet.ma', staff: false, vp: { width: 390, height: 844 } },
  { role: 'C', email: 't2-restricted@cabinet.ma', staff: true, vp: { width: 1280, height: 900 } },
  { role: 'D', email: 't2-reception@cabinet.ma', staff: true, vp: { width: 390, height: 844 } },
];
const browser = await chromium.launch({ headless: true });
const results = [];
try {
  for (const actor of actors) {
    const item = { role: actor.role, staff: actor.staff, viewport: actor.vp, status: 'FAIL', checks: [], images: [] };
    const auth = await request.newContext({ baseURL: backend });
    let context;
    try {
      const ownerLogin = await auth.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password } });
      if (!ownerLogin.ok()) throw Error('Synthetic owner could not enroll workstation: ' + ownerLogin.status());
      const token = (await ownerLogin.json()).access_token;
      const enrolled = await enrollT2Workstation(auth, token, password);
      // Only the workstation attestation may cross browser identities.
      // The owner access/refresh login cookies must never authenticate staff.
      const station = { cookies: enrolled.cookies.filter(c => c.name === 'dc_workstation'), origins: [] };
      if (station.cookies.length !== 1) throw Error('Workstation identity cookie missing');
      context = await browser.newContext({ viewport: actor.vp, reducedMotion: 'reduce', storageState: station });
      const page = await context.newPage();
      const capture = async name => {
        await page.evaluate(() => document.fonts.ready);
        const file = actor.role + '-' + actor.vp.width + '-' + name + '.png';
        await page.screenshot({ path: path.join(root, file), animations: 'disabled', fullPage: true });
        item.images.push(file);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
        if (overflow) throw Error('Horizontal overflow at ' + name);
      };
      await page.goto(base + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.locator('input[type=email]').fill(actor.email);
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button', { name: 'Se connecter' }).click();
      await page.waitForURL('**/dashboard', { timeout: 45000 });
      await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({ state: 'visible', timeout: 30000 });
      item.checks.push('Actual product login and dashboard');
      await capture('dashboard-before-validation');
      const ownToken = await page.evaluate(() => localStorage.getItem('token'));
      if (!ownToken) throw Error('No authenticated browser token');
      const api = await request.newContext({ baseURL: backend, storageState: await context.storageState() });
      try {
        const headers = { Authorization: 'Bearer ' + ownToken };
        const clinicResponse = await api.get('/api/admin/cabinet/me', { headers });
        if (!clinicResponse.ok()) throw Error('Cabinet identity API failed ' + clinicResponse.status());
        const clinic = await clinicResponse.json();
        const canonicalName = String(clinic?.nom_cabinet || '').trim();
        if (canonicalName !== 'Cabinet T2 Certification') throw Error('Unexpected synthetic clinic context');
        item.checks.push('Tenant identity from authenticated backend');
        const header = await page.getByTestId('shared-header-cabinet-name').textContent();
        if (header?.trim() !== canonicalName) throw Error('Header not equal to API tenant identity');
        item.checks.push('Header is tenant-scoped');
        if (actor.staff) {
          // Staff must read their tenant identity from the backend, not receive
          // an unapproved tenant-switching control or an empty settings store.
          await page.getByTestId('staff-active-cabinet').waitFor({ state: 'attached', timeout: 20000 });
          await page.waitForFunction(name => {
            const el = document.querySelector('[data-testid="staff-active-cabinet"]');
            return el?.textContent?.trim() === name;
          }, canonicalName, { timeout: 20000 });
          if (await page.locator('.sidebar-cabinet-full select').count()) {
            throw Error('Restricted staff has an editable cabinet switcher');
          }
          item.selector = { mode: 'readonly', matchesBackend: true };
          item.checks.push('Staff sees backend-owned, read-only active clinic');
        } else {
          await page.locator('.sidebar-cabinet-full select').waitFor({ state: 'attached', timeout: 10000 });
          const selector = await page.locator('.sidebar-cabinet-full select').evaluate(el => ({
            selected: el.value, options: [...el.options].map(o => o.textContent?.trim() || ''),
          }));
          item.selector = { mode: 'owner', availableOptions: selector.options.length, selected: Boolean(selector.selected) };
          if (!selector.selected || !selector.options.some(x => x.includes(canonicalName))) {
            throw Error('Owner Cabinet Actif selector empty/wrong for authenticated tenant');
          }
          item.checks.push('Owner cabinet selector matches authenticated tenant');
        }
        const patient = await api.get('/api/patients/', { headers });
        if (actor.staff && patient.status() !== 403) throw Error('Restricted staff patient API not denied (HTTP ' + patient.status() + ')');
        if (!actor.staff && !patient.ok()) throw Error('Owner patient API unexpectedly denied (HTTP ' + patient.status() + ')');
        item.checks.push('Backend patient RBAC');
      } finally { await api.dispose(); }
      await capture('dashboard-identity');
      if (actor.staff) {
        if (await page.getByRole('link', { name: 'Patients', exact: true }).count()) throw Error('Restricted staff sees patient navigation');
        await page.goto(base + '/patients', { waitUntil: 'domcontentloaded' });
        await page.waitForURL('**/dashboard', { timeout: 20000 });
        await page.goto(base + '/settings', { waitUntil: 'domcontentloaded' });
        await page.waitForURL('**/dashboard', { timeout: 20000 });
        item.checks.push('Restricted staff forbidden patients/settings deep links');
      }
      const patientRequests = [];
      page.on('request', req => { if (/\/api\/(patients|consultations|patient-)/.test(new URL(req.url()).pathname)) patientRequests.push(req.method()); });
      await page.goto(base + '/bibliotheque', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.getByRole('heading', { name: /Bibliothèque clinique/i }).waitFor({ state: 'visible', timeout: 25000 });
      await page.getByTestId('library-protocol-list').waitFor({ state: 'visible', timeout: 25000 });
      if (patientRequests.length) throw Error('Static protocol library unexpectedly fetched patient data');
      item.checks.push('Static reference library visible without patient API request');
      await capture('library-reference');
      item.status = 'PASS';
      console.log(JSON.stringify({ role: actor.role, status: item.status, head, staff: actor.staff }));
    } catch (err) {
      item.failure = String(err?.message || err).slice(0, 450);
      // Keep a genuine browser image on failures for visual triage; isolated
      // synthetic users only, never expose login tokens in logs.
      try {
        const failedPage = context?.pages()?.[0];
        if (failedPage) {
          const file = actor.role + '-' + actor.vp.width + '-FAIL.png';
          await failedPage.screenshot({ path: path.join(root, file), fullPage: true, animations: 'disabled' });
          item.images.push(file);
        }
      } catch { /* Preserve original failure. */ }
      console.log(JSON.stringify({ role: actor.role, status: 'FAIL', reason: item.failure, head }));
    } finally {
      results.push(item);
      await context?.close();
      await auth.dispose();
    }
  }
} finally { await browser.close(); }
const report = {
  head,
  scope: 'synthetic actual login + four separate browser workstation contexts; tenant identity and sidebar selection; staff patient guards; static library observation ONLY; library access policy requires explicit owner decision',
  results, status: results.every(x => x.status === 'PASS') ? 'PASS' : 'FAIL',
};
await fs.writeFile(path.join(root, 'report.json'), JSON.stringify(report, null, 2));
if (report.status !== 'PASS') process.exitCode = 1;
