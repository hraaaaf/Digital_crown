// FUE-A: actual first installer use of TWO fresh, uninitialized clinic accounts.
// Test-only SQLite fixtures from scripts/t2_runtime_server.py. NOT production setup.
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const password = process.env.T2_PASSWORD;
const head = process.env.PRODUCT_HEAD;
if (!password || !/^[0-9a-f]{40}$/.test(head || '')) throw Error('FUE-A requires masked CI password and exact product HEAD');
const backend = 'http://127.0.0.1:8005';
const frontend = 'http://127.0.0.1:5173';
const out = path.resolve('../artifacts/t2-browser/first-user-experience');
await fs.mkdir(out, { recursive: true });
const cases = [
  { label: 'mobile-390', width: 390, height: 844, user: 't2-setup-390@cabinet.ma' },
  { label: 'desktop-1280', width: 1280, height: 900, user: 't2-setup-1280@cabinet.ma' },
];
const browser = await chromium.launch({ headless: true });
const results = [];

for (const item of cases) {
  const evidence = { role: 'fresh owner', viewport: item.label, checks: [], screenshots: [], status: 'FAIL' };
  const api = await request.newContext({ baseURL: backend });
  let ctx = null;
  try {
    const login = await api.post('/api/auth/login', { form: { username: item.user, password } });
    if (!login.ok()) throw Error('Synthetic uninitialized owner rejected HTTP ' + login.status());
    const tokens = await login.json();
    const enrolled = await enrollT2Workstation(api, tokens.access_token, password);
    // Station enrollment is not user login: never preload owner auth cookies/JWT.
    const stationState = { cookies: enrolled.cookies.filter(c => c.name === 'dc_workstation'), origins: [] };
    if (stationState.cookies.length !== 1) throw Error('Expected exactly one bound workstation cookie');
    const init = await api.get('/api/clinics/init-status', { headers: { Authorization: 'Bearer ' + tokens.access_token } });
    if (!init.ok() || (await init.json()).is_initialized !== false) {
      throw Error('Fresh owner did not start as uninitialized clinic');
    }
    evidence.checks.push('Fresh synthetic owner has no initialized clinic');
    ctx = await browser.newContext({
      viewport: { width: item.width, height: item.height },
      storageState: stationState, reducedMotion: 'reduce',
    });
    const page = await ctx.newPage();
    const pageErrors = [];
    page.on('pageerror', err => pageErrors.push(err.message));
    const capture = async label => {
      const file = item.label + '-' + label + '.png';
      await page.screenshot({ path: path.join(out, file), fullPage: true, animations: 'disabled' });
      evidence.screenshots.push(file);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
      if (overflow) throw Error('Horizontal overflow: ' + label);
    };
    // This is a REAL login form, not only an injected JWT.
    await page.goto(frontend + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.locator('input[type=email]').fill(item.user);
    await page.locator('input[type=password]').fill(password);
    await capture('01-login-before');
    await page.getByRole('button', { name: 'Se connecter' }).click();
    await page.waitForURL('**/setup', { timeout: 45000 });
    await page.getByRole('heading', { name: 'Profil Cabinet' }).waitFor({ state: 'visible', timeout: 20000 });
    evidence.checks.push('Real login redirects uninitialized owner to setup wizard');
    await capture('02-setup-step1');
    // A fresh clinic MUST NOT access clinical Dashboard before setup completion.
    await page.goto(frontend + '/dashboard', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForURL('**/setup', { timeout: 25000 });
    evidence.checks.push('Uninitialized clinic cannot bypass setup with direct Dashboard URL');
    // Validate required step-1 fields, then walk all seven real product steps.
    await page.getByRole('button', { name: /Continuer/i }).click();
    await page.getByRole('heading', { name: 'Profil Cabinet' }).waitFor();
    await page.getByPlaceholder(/Ex: Cabinet Dentaire Alami|Ex: Centre Dentaire Al Massira/).fill('Cabinet FUE ' + item.label);
    await page.getByPlaceholder('Étage, Résidence, Rue, Ville...').fill('Adresse de test - environnement jetable');
    await page.getByPlaceholder('Dr. Jean Dupont').fill('Dr FUE ' + item.label);
    for (let step = 2; step <= 7; step++) {
      await page.getByRole('button', { name: /Continuer/i }).click();
      // The progress label is visually hidden on some responsive layouts.
      // Assert the real rendered wizard content and its active step instead.
      await page.locator('[data-flow-step="' + step + '"]').waitFor({ state: 'visible', timeout: 15000 });
    }
    evidence.checks.push('Required fields validated and seven wizard steps traversed');
    await capture('03-setup-step7');
    await page.getByRole('button', { name: /Finaliser l.Installation/i }).click();
    await page.waitForURL('**/dashboard', { timeout: 60000 });
    const after = await api.get('/api/clinics/init-status', { headers: { Authorization: 'Bearer ' + tokens.access_token } });
    if (!after.ok() || (await after.json()).is_initialized !== true) {
      throw Error('Setup UI navigated but server did not persist initialized cabinet');
    }
    evidence.checks.push('Setup completion acknowledged by real clinic backend');
    await capture('04-dashboard-after');
    await page.goto(frontend + '/setup', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/dashboard', { timeout: 25000 });
    evidence.checks.push('Initialized clinic cannot reopen installation wizard via deep link');
    if (pageErrors.length) throw Error('Uncaught browser error(s): ' + pageErrors.length);
    evidence.status = 'PASS';
    console.log(JSON.stringify({ phase: 'FUE-A', role: evidence.role, viewport: item.label, status: 'PASS', head }));
  } catch (err) {
    evidence.failure = String(err?.message || err).slice(0, 500);
    console.log(JSON.stringify({ phase: 'FUE-A', viewport: item.label, status: 'FAIL', reason: evidence.failure, head }));
  } finally {
    results.push(evidence);
    await ctx?.close();
    await api.dispose();
  }
}
await browser.close();
const summary = {
  head, scope: 'real browser login → uninitialized wizard → seven stages → backend setup completion; synthetic disposable T2 users only',
  status: results.every(x => x.status === 'PASS') ? 'PASS' : 'FAIL', cases: results,
};
await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(summary, null, 2));
if (summary.status !== 'PASS') process.exitCode = 1;
