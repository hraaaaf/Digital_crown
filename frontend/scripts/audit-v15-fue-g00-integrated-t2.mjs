// FUE-G 00: real Hub/Dispatcher interaction with disposable isolated T2 backend.
// A first-login browser is NOT a physical, unprovisioned cabinet PC:
// the workstation is legitimately pre-enrolled using the public test API.
// Product mode/PIN/Station escape are changed only by real UI interactions.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.EVALUATED_SHA;
const email = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
const isolated = process.env.ENVIRONMENT === 'test' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1';
if (!isolated || !/^[a-f0-9]{40}$/.test(head || '') || !email || !password) {
  throw new Error('FUE-G00 requires disposable T2, exact SHA and generated credentials');
}
const root = path.resolve('../artifacts/v15-fue-g00-integrated');
const ui = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
await fs.mkdir(root, { recursive: true });
const matrix = { head, isolated, type: 'FUE-G00 real backend integration LAB ONLY',
  limitations: ['API pre-enrolled workstation (not physical virgin PC)',
    'No physical LAN/TLS or recovery/reboot', 'No real clinic patients',
    'Human UX approval is separate'], cases: [], failures: [], success: false };
const browser = await chromium.launch({ headless: true });
const viewports = [{ name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 900 }];
try {
  for (const v of viewports) {
    const test = { name: v.name, viewport: [v.width, v.height], checks: {},
      images: [], pageErrors: [], http5xx: [], timingsMs: {} };
    const api = await request.newContext({ baseURL: backend });
    const start = Date.now();
    let context, page;
    try {
      const bootstrapLogin = await api.post('/api/auth/login', {
        form: { username: email, password } });
      if (bootstrapLogin.status() !== 200) throw Error('T2 bootstrap owner login failed');
      const accessToken = (await bootstrapLogin.json()).access_token;
      if (!accessToken) throw Error('No owner token for legitimate workstation enrollment');
      const state = await enrollT2Workstation(api, accessToken, password);
      const stationCookies = state.cookies.filter(c => c.name === 'dc_workstation');
      if (stationCookies.length !== 1) throw Error('Expected exactly one enrolled workstation cookie');
      context = await browser.newContext({ viewport: { width: v.width, height: v.height },
        reducedMotion: 'reduce', storageState: { cookies: stationCookies, origins: [] } });
      page = await context.newPage();
      page.on('pageerror', e => test.pageErrors.push(e.message));
      page.on('response', r => { if (r.status() >= 500) test.http5xx.push({
        status: r.status(), path: new URL(r.url()).pathname }); });
      const yes = (name, condition) => {
        test.checks[name] = Boolean(condition);
        if (!condition) throw Error('FAILED: ' + name);
      };
      const screenshot = async label => {
        const meta = await page.evaluate(() => ({
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          hasClinicalChart: !!document.querySelector('[data-patient-chart]')
        }));
        if (meta.scrollWidth > meta.clientWidth + 1) throw Error('Horizontal overflow: ' + label);
        const filename = v.name + '-' + label + '.png';
        await page.screenshot({ path: path.join(root, filename),
          fullPage: true, animations: 'disabled' });
        test.images.push(filename);
      };
      const goto = async route => page.goto(ui + route, {
        waitUntil: 'domcontentloaded', timeout: 45000 });
      const at = async pathname => page.waitForURL(
        url => new URL(url).pathname === pathname, { timeout: 30000 });
      const visible = async selector => page.locator(selector).waitFor({
        state: 'visible', timeout: 30000 });
      const waitLogin = async () => {
        await visible('input[type=email]');
        await page.waitForFunction(() => {
          const field = document.querySelector('input[type=email]');
          const panel = field?.closest('div.max-w-md');
          return !!panel && Number.parseFloat(getComputedStyle(panel).opacity) >= 0.98;
        }, null, { timeout: 15000 });
      };

      await goto('/hub?select=1');
      await visible('[data-hub-experience="cabinet"]');
      yes('freshBrowserNoAppAuth', await page.evaluate(() =>
        !localStorage.getItem('token') && !localStorage.getItem('refresh_token')));
      yes('exactlyThreeHubDestinations',
        await page.locator('[data-hub-experience]').count() === 3);
      await screenshot('01-hub-anonymous');
      test.timingsMs.hub = Date.now() - start;

      // Unauthenticated clinical navigation always reaches the login, not Dashboard.
      await goto('/dashboard');
      await at('/login');
      await waitLogin();
      yes('anonymousDashboardDenied', await page.locator('[data-clinical-dashboard]').count() === 0);
      await screenshot('02-login-denial');
      await goto('/hub?select=1');
      await page.locator('[data-hub-experience="cabinet"]').click();
      await at('/login');
      await waitLogin();
      yes('cabinetChoiceRequestsLogin', true);
      await page.locator('input[type=email]').fill(email);
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
      await at('/dashboard');
      await visible('button');
      await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({
        state: 'visible', timeout: 30000 });
      yes('actualUiAuthAndDashboard', await page.evaluate(() =>
        !!localStorage.getItem('token')));
      test.timingsMs.firstClinicalValue = Date.now() - start;
      await screenshot('03-cabinet-authenticated');

      // Control Center is a real Hub card; its own UI provides an explicit back action.
      await goto('/hub?select=1');
      await visible('[data-workstation-admin]');
      await page.locator('[data-hub-experience="control"]').click();
      await at('/control-center');
      await visible('[data-control-center-topology]');
      await screenshot('04-control');
      const back = page.getByRole('button', { name: 'Continuer vers le Hub' });
      await back.waitFor({ state: 'visible', timeout: 20000 });
      await back.click();
      await at('/hub');
      await visible('[data-hub-experience="cabinet"]');
      yes('controlCenterBackViaRealUi', true);
      await screenshot('05-control-return-hub');

      // Establish owner PIN through UI, never by direct API mutation.
      await visible('[data-workstation-admin]');
      const admin = page.locator('[data-workstation-admin]');
      const summary = admin.locator('summary').filter({
        hasText: /Configurer le PIN propriétaire|Changer le PIN propriétaire/ }).first();
      await summary.waitFor({ state: 'visible', timeout: 20000 });
      await summary.click();
      const pin = String(crypto.randomInt(100000, 1000000));
      await admin.getByLabel('Mot de passe du compte', { exact: true }).fill(password);
      await admin.getByLabel('Nouveau PIN', { exact: true }).fill(pin);
      const pinResponse = page.waitForResponse(r =>
        new URL(r.url()).pathname === '/api/workstation/owner-pin' &&
        r.request().method() === 'POST', { timeout: 30000 });
      await admin.getByRole('button', { name: 'Enregistrer le PIN' }).click();
      yes('serverOwnerPinConfigured', (await pinResponse).status() === 200);
      await admin.getByText('PIN configuré', { exact: true }).waitFor({
        state: 'visible', timeout: 30000 });
      await screenshot('06-owner-pin-configured');

      // Choose Station through the actual Hub admin; negative direct routing then lock.
      await admin.getByRole('button', { name: "Station d'accueil", exact: true }).click();
      yes('stationModeUiSelected',
        (await admin.getByRole('button', { name: "Station d'accueil", exact: true })
          .getAttribute('aria-pressed')) === 'true');
      await admin.getByLabel('PIN propriétaire', { exact: true }).fill(pin);
      const modeResponse = page.waitForResponse(r =>
        new URL(r.url()).pathname === '/api/workstation/mode' &&
        r.request().method() === 'POST', { timeout: 30000 });
      await admin.getByRole('button', { name: 'Appliquer ce mode' }).click();
      yes('serverAcceptedStationMode', (await modeResponse).status() === 200);
      await at('/station');
      await visible('[data-workstation-experience="station"]');
      await screenshot('07-station');

      await goto('/hub?select=1');
      await at('/station');
      yes('lockedStationRejectsDirectHub', true);
      await goto('/control-center');
      await at('/station');
      yes('lockedStationRejectsDirectControl', true);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await visible('[data-workstation-experience="station"]');
      yes('stationLockSurvivesReload', new URL(page.url()).pathname === '/station');
      await screenshot('08-lock-after-reload');

      // Open owner admin with the production keyboard shortcut.
      await page.keyboard.press('Control+Alt+h');
      await visible('[data-station-admin]');
      const stationAdmin = page.locator('[data-station-admin]');
      await screenshot('09-owner-escape-ui');
      await stationAdmin.getByLabel('PIN propriétaire').fill('0000');
      const deniedResponse = page.waitForResponse(r =>
        new URL(r.url()).pathname === '/api/workstation/station/escape' &&
        r.request().method() === 'POST', { timeout: 30000 });
      await stationAdmin.getByRole('button', { name: 'Autoriser l’accès au Hub' }).click();
      yes('badOwnerPinDeniedByServer', (await deniedResponse).status() === 403);
      yes('badPinRemainsInStation', new URL(page.url()).pathname === '/station');
      await stationAdmin.getByLabel('PIN propriétaire').fill(pin);
      const escapeResponse = page.waitForResponse(r =>
        new URL(r.url()).pathname === '/api/workstation/station/escape' &&
        r.request().method() === 'POST', { timeout: 30000 });
      await stationAdmin.getByRole('button', { name: 'Autoriser l’accès au Hub' }).click();
      yes('goodOwnerPinAcceptedByServer', (await escapeResponse).status() === 200);
      await at('/hub');
      await visible('[data-hub-experience="cabinet"]');
      yes('stationEscapeReturnsViaRealUi', true);
      await screenshot('10-station-owner-return-hub');

      if (test.pageErrors.length || test.http5xx.length) {
        throw Error('Unexpected JS/page errors or HTTP5xx');
      }
      yes('allTenEvidenceImagesSaved', test.images.length === 10);
      matrix.cases.push(test);
    } catch (e) {
      matrix.failures.push({ viewport: v.name, reason: String(e).slice(0,650),
        checks: test.checks, images: test.images });
      if (page) await page.screenshot({ path: path.join(root, v.name + '-FAIL.png'),
        fullPage: true }).catch(() => {});
    } finally {
      if (context) await context.close();
      await api.dispose();
    }
  }
} finally { await browser.close(); }
matrix.success = matrix.cases.length === viewports.length &&
  matrix.failures.length === 0 &&
  matrix.cases.every(c => c.images.length === 10 &&
    Object.values(c.checks).every(Boolean));
await fs.writeFile(path.join(root, 'report.json'), JSON.stringify(matrix, null, 2));
console.log('FUE_G00_INTEGRATED_SUMMARY', JSON.stringify({
  head: matrix.head, isolated: matrix.isolated, success: matrix.success,
  profiles: matrix.cases.map(c => ({ viewport: c.name, evidenceImages: c.images.length,
    checks: c.checks, timingsMs: c.timingsMs })),
  failures: matrix.failures }));
if (!matrix.success) throw Error('FUE-G00 integrated T2 gate FAILED');
