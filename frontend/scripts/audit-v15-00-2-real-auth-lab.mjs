// FUE-I 00.2 — true UI login to Cabinet on disposable T2, NEVER a clinic.
// The bootstrap API login is only used to legitimately enroll a workstation.
// The browser receives ONLY the station identity cookie, not any user auth token.
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.EVALUATED_SHA;
const email = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!/^[0-9a-f]{40}$/.test(head || '') || !email || !password) {
  throw new Error('Exact candidate SHA and disposable T2 credentials required');
}
if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' || process.env.ENVIRONMENT !== 'test') {
  throw new Error('Refusing FUE 00.2 outside isolated T2 runtime');
}
const backend = 'http://127.0.0.1:8005';
const ui = 'http://127.0.0.1:5173';
const out = path.resolve('../artifacts/v15-00-2-real-auth');
await fs.mkdir(out, { recursive: true });
const profiles = [
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 900 },
];
const evidence = {
  head, isolated: true, protocol: 'FUE-I V1.5-00.2 real UI login on disposable T2',
  workstation: 'real API enrollment, only dc_workstation cookie in fresh browser',
  profiles: [], failures: [], success: false,
};
const browser = await chromium.launch({ headless: true });
try {
  for (const vp of profiles) {
    const item = {
      viewport: vp.name, dimensions: [vp.width, vp.height], checks: {},
      pictures: [], errors: [], http5xx: [], timingsMs: {},
    };
    const api = await request.newContext({ baseURL: backend });
    let ctx = null;
    const start = Date.now();
    try {
      const login = await api.post('/api/auth/login', {
        form: { username: email, password },
      });
      if (login.status() !== 200) throw new Error('T2 enrollment precondition login HTTP ' + login.status());
      const access = (await login.json()).access_token;
      if (!access) throw new Error('T2 enrollment precondition missing access token');
      const enrolled = await enrollT2Workstation(api, access, password);
      const cookies = enrolled.cookies.filter(cookie => cookie.name === 'dc_workstation');
      if (cookies.length !== 1) throw new Error('Expected exactly one legitimate workstation cookie');
      if (enrolled.cookies.some(cookie => /access|refresh|auth/i.test(cookie.name))) {
        throw new Error('Unexpected auth cookies in browser workstation state');
      }
      item.checks.serverEnrolledWorkstation = true;
      ctx = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        reducedMotion: 'reduce', storageState: { cookies, origins: [] },
      });
      const page = await ctx.newPage();
      page.on('pageerror', error => item.errors.push(error.message));
      page.on('response', response => {
        if (response.status() >= 500) {
          item.http5xx.push({ status: response.status(), path: new URL(response.url()).pathname });
        }
      });
      const capture = async name => {
        const meta = await page.evaluate(() => {
          const root = document.documentElement;
          return {
            width: root.clientWidth, scrollWidth: root.scrollWidth,
            clinicalContent: Boolean(document.querySelector('[data-patient-chart], [data-clinical-dashboard]')),
          };
        });
        if (meta.scrollWidth > meta.width + 1) throw new Error('Page overflow at ' + name);
        const filename = vp.name + '-' + name + '.png';
        await page.screenshot({ path: path.join(out, filename), fullPage: true, animations: 'disabled' });
        item.pictures.push(filename);
      };
      await page.goto(ui + '/hub?select=1', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.locator('[data-hub-experience="cabinet"]').waitFor({ state: 'visible', timeout: 30000 });
      const firstCards = await page.locator('[data-hub-experience]').count();
      if (firstCards !== 3) throw new Error('Expected 3 Hub choices, got ' + firstCards);
      const noAuth = await page.evaluate(() =>
        !localStorage.getItem('token') && !localStorage.getItem('refresh_token'));
      if (!noAuth) throw new Error('Fresh browser already has application authentication');
      item.checks.freshUnauthenticatedHub = true;
      item.timingsMs.hubReady = Date.now() - start;
      await capture('01-before-hub');

      // First enforce negative permission without issuing any simulated auth.
      await page.goto(ui + '/dashboard', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForURL(url => new URL(url).pathname === '/login', { timeout: 30000 });
      if (await page.locator('[data-clinical-dashboard]').count()) {
        throw new Error('Anonymous direct Dashboard leaked clinical content');
      }
      item.checks.anonymousDirectDashboardDenied = true;
      await capture('02-anonymous-refusal');

      await page.goto(ui + '/hub?select=1', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.locator('[data-hub-experience="cabinet"]').click();
      await page.waitForURL(url => new URL(url).pathname === '/login', { timeout: 30000 });
      item.checks.cabinetCardDemandsRealLogin = true;
      await capture('03-after-cabinet-choice-login');

      // Real login UI, no test-only injection of localStorage auth tokens.
      await page.locator('input[type=email]').fill(email);
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
      await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 60000 });
      await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({ state: 'visible', timeout: 30000 });
      if (!await page.evaluate(() => Boolean(localStorage.getItem('token')))) {
        throw new Error('Real UI login did not establish authenticated browser session');
      }
      item.checks.realUiLoginOpensDashboard = true;
      item.timingsMs.firstAuthenticatedValue = Date.now() - start;
      await capture('04-after-real-ui-login-dashboard');

      // This is a direct-URL Hub return, not a claimed on-screen Back button.
      await page.goto(ui + '/hub?select=1', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.locator('[data-hub-experience="control"]').waitFor({ state: 'visible', timeout: 30000 });
      item.checks.directHubReturn = true;
      await capture('05-back-hub-direct-url');
      await page.locator('[data-hub-experience="control"]').click();
      await page.waitForURL(url => new URL(url).pathname === '/control-center', { timeout: 30000 });
      await page.locator('[data-workstation-experience="control-center"]').waitFor({ state: 'visible', timeout: 30000 });
      item.checks.controlCenterNavigation = true;
      await capture('06-control-center');

      if (item.errors.length > 0 || item.http5xx.length > 0) {
        throw new Error('Unexpected JS errors or HTTP 5xx: ' +
          JSON.stringify({ errors: item.errors, http5xx: item.http5xx }));
      }
      if (item.pictures.length !== 6) throw new Error('Missing browser screenshots');
      evidence.profiles.push(item);
    } catch (error) {
      evidence.failures.push({
        viewport: vp.name, error: String(error).slice(0, 450),
        completedChecks: item.checks, pictures: item.pictures,
      });
      if (ctx) {
        const pages = ctx.pages();
        if (pages[0]) await pages[0].screenshot({
          path: path.join(out, vp.name + '-FAIL.png'), fullPage: true,
        }).catch(() => {});
      }
    } finally {
      if (ctx) await ctx.close();
      await api.dispose();
    }
  }
} finally { await browser.close(); }
evidence.success =
  evidence.failures.length === 0 &&
  evidence.profiles.length === profiles.length &&
  evidence.profiles.every(p => p.pictures.length === 6 &&
    Object.keys(p.checks).length === 7 &&
    Object.values(p.checks).every(Boolean));
await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(evidence, null, 2));
console.log('FUE_00_2_REAL_AUTH_SUMMARY', JSON.stringify({
  head: evidence.head, isolated: evidence.isolated, success: evidence.success,
  profiles: evidence.profiles.map(p => ({
    viewport: p.viewport, screenshots: p.pictures.length,
    checks: p.checks, timingsMs: p.timingsMs,
  })),
  failures: evidence.failures,
}));
if (!evidence.success) throw new Error('FUE-I 00.2 T2 real-auth path failed closed');
