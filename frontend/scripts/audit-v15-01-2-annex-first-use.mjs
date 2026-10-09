import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { randomInt } from 'node:crypto';

/**
 * V1.5-01.2 scoped FUE-I.
 * Uses only the synthetic T2 backend and disposable browsers.
 * Proves manual handoff between two browser origins over loopback.
 * This is NOT proof of LAN HTTPS trust, physical discovery or cabinet deployment.
 */
const outDir = path.resolve('../artifacts/fue-v15-01-2');
fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });
const report = {
  productHead: process.env.PRODUCT_HEAD || 'UNKNOWN',
  scope: 'V1.5-01.2 FUE-I: fresh browser, origin handoff, authenticated single-use pairing code',
  exclusions: ['physical LAN discovery', 'LAN TLS/certificate trust', 'real cabinet', 'multi-PC reboot/PIN'],
  cases: [],
  success: false,
};
const base = 'http://127.0.0.1:5173';
const remote = 'http://localhost:8005';
const email = process.env.T2_USER || 't2-browser@cabinet.ma';
const password = process.env.T2_PASSWORD;
if (!password) throw new Error('Missing isolated T2_PASSWORD');
// Synthetic owner issues pairing codes on the isolated backend. They are never logged.
const owner = await request.newContext({ baseURL: remote });
const ownerLogin = await owner.post('/api/auth/login', { form: { username: email, password } });
if (!ownerLogin.ok()) throw new Error('Isolated owner bootstrap login failed: ' + ownerLogin.status());
const ownerToken = (await ownerLogin.json()).access_token;
const pin = String(randomInt(100000, 1000000));
const ownerHeaders = { Authorization: 'Bearer ' + ownerToken };
const configurePin = await owner.post('/api/workstation/owner-pin', { data: { accountPassword: password, newPin: pin }, headers: ownerHeaders });
if (!configurePin.ok()) throw new Error('Cannot configure isolated pairing PIN: ' + configurePin.status());

const profiles = [
  { name: 'mobile390', width: 390, height: 844 },
  { name: 'mobile430', width: 430, height: 932 },
  { name: 'tablet768', width: 768, height: 1024 },
  { name: 'desktop1280', width: 1280, height: 900 },
];
const browser = await chromium.launch({ headless: true });
for (const p of profiles) {
  const record = { profile: p.name, viewport: [p.width, p.height], steps: [], errors: [], failures: [] };
  report.cases.push(record);
  const context = await browser.newContext({ viewport: { width: p.width, height: p.height }, storageState: { cookies: [], origins: [] } });
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  page.on('pageerror', e => record.errors.push(e.message));
  const snapshot = async label => {
    await page.screenshot({ path: path.join(outDir, p.name + '-' + label + '.png'), fullPage: true });
    record.steps.push({ label, url: page.url(), horizontalOverflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1) });
  };
  try {
    const codeResponse = await owner.post('/api/workstation/pairing-code', {
      data: { ownerPin: pin },
      headers: ownerHeaders,
    });
    if (!codeResponse.ok()) throw new Error('Cannot issue isolated pairing code: ' + codeResponse.status());
    const pairingCode = (await codeResponse.json()).code;
    const start = Date.now();
    await page.goto(base + '/hub?select=1', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.locator('[data-hub-experience="control"]').waitFor({ state: 'visible' });
    await snapshot('01-hub-before');
    await page.locator('[data-hub-experience="control"]').click();
    await page.waitForURL('**/control-center');
    const target = page.locator('[data-control-center-target]');
    await target.waitFor({ state: 'visible' });
    await snapshot('02-control-before');
    await target.fill('http://192.168.1.20:8005');
    await page.locator('[data-control-center-probe]').click();
    await page.getByRole('alert').filter({ hasText: 'HTTPS est obligatoire' }).waitFor();
    await snapshot('03-unsafe-lan-rejected');
    await target.fill('https://example.com:8005');
    await page.locator('[data-control-center-probe]').click();
    await page.getByRole('alert').filter({ hasText: 'adresse locale du cabinet' }).waitFor();

    // The app must not silently send a probe to a different origin.
    const premature = [];
    const listener = req => { if (req.url().startsWith(remote)) premature.push(req.url()); };
    page.on('request', listener);
    await target.fill(remote);
    await page.locator('[data-control-center-probe]').click();
    await page.getByText('Aucune requête n’est envoyée à une origine distante', { exact: false }).waitFor();
    await snapshot('04-explicit-origin-handoff');
    page.off('request', listener);
    if (premature.length) throw new Error('Premature cross-origin request');
    await page.locator('[data-control-center-open]').click();
    await page.waitForURL(remote + '/control-center', { timeout: 20000 });
    await page.locator('[data-control-center-backend]').filter({ hasText: 'Joignable' }).waitFor({ timeout: 15000 });
    await page.locator('[data-control-center-db]').filter({ hasText: 'Disponible' }).waitFor({ timeout: 15000 });
    await page.locator('[data-control-center-auth]').filter({ hasText: 'Connexion requise' }).waitFor({ timeout: 15000 });
    record.originHandoffMs = Date.now() - start;
    await snapshot('05-remote-anonymous-after');

    await page.goto(remote + '/patients', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/login', { timeout: 20000 });
    await page.getByPlaceholder('nom@cabinet.com').waitFor({ state: 'visible', timeout: 12000 });
    await snapshot('06-protected-route-refused');
    await page.getByPlaceholder('nom@cabinet.com').fill(email);
    await page.getByPlaceholder('••••••••').fill(password);
    await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
    await page.waitForURL(url => new URL(url).pathname === '/hub', { timeout: 30000 });
    await page.locator('[data-workstation-enrollment]').waitFor({ state: 'visible', timeout: 15000 });
    // A 423 from /api/clinics/me is authorization, not server unavailability.
    // Wait for the actual Hub identity check (not just its initial render) so
    // the regression cannot accidentally pass before the fetch settles.
    await page.locator('[data-hub-server-state="restricted"]').waitFor({ state: 'visible', timeout: 15000 });
    if (await page.locator('[data-hub-offline]').count()) {
      throw new Error('False offline Hub banner on HTTP 423 workstation enrollment');
    }
    await snapshot('07-enrollment-required');
    await page.getByPlaceholder('Ex. Accueil 1').fill('Annexe ' + p.name);
    await page.getByPlaceholder('000000').fill(pairingCode);
    await page.getByRole('button', { name: 'Appairer cette borne' }).click();
    await page.getByText('Borne appairée et identifiée.', { exact: false }).waitFor({ timeout: 15000 });
    await snapshot('08-workstation-paired');
    await page.goto(remote + '/control-center', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-control-center-target]').waitFor({ state: 'visible' });
    if (await page.locator('label[for="cabinet-server-target"]').count() !== 1) {
      throw new Error('Control Center address input label missing');
    }
    if (await page.locator('[data-control-center-target]').getAttribute('aria-describedby') !== 'cabinet-server-help') {
      throw new Error('Control Center address accessible instructions missing');
    }
    await page.evaluate(() => { document.documentElement.style.fontSize = '32px'; });
    await snapshot('09-control-text200');
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) {
      throw new Error('Control Center horizontal overflow at 200 percent text');
    }
    await page.goto(remote + '/cabinet', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/dashboard', { timeout: 30000 });
    await page.getByRole('main').first().waitFor({ state: 'visible', timeout: 18000 });
    const authState = await page.evaluate(async () => {
      const token = localStorage.getItem('token') || '';
      const resp = await fetch('/api/auth/me', {
        credentials: 'include',
        headers: token ? { Authorization: 'Bearer ' + token } : undefined,
      });
      return resp.status;
    });
    if (authState !== 200) throw new Error('Login did not establish authenticated API session: ' + authState);
    record.authenticatedApiStatus = authState;
    record.firstAuthenticatedMs = Date.now() - start;
    await snapshot('10-authenticated-dashboard-after');
    if (record.steps.some(s => s.horizontalOverflow)) throw new Error('Horizontal overflow');
    if (record.errors.length) throw new Error('Uncaught page errors: ' + record.errors.length);
    record.result = 'PASS';
  } catch (error) {
    record.result = 'FAIL';
    record.failures.push(String(error?.message || error).slice(0, 800));
    await page.screenshot({ path: path.join(outDir, p.name + '-FAIL.png'), fullPage: true }).catch(() => {});
  } finally {
    await context.close();
  }
}
await browser.close();
await owner.dispose();
report.success = report.cases.every(c => c.result === 'PASS');
fs.writeFileSync(path.join(outDir, 'fue-v15-01-2-report.json'), JSON.stringify(report, null, 2));
console.log('FUE_V15_01_2_SUMMARY ' + JSON.stringify({
  head: report.productHead,
  success: report.success,
  cases: report.cases.map(c => ({ name: c.profile, result: c.result, failures: c.failures, screenshots: c.steps.length })),
}));
if (!report.success) process.exitCode = 1;
