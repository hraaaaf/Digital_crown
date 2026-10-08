import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');
const root = 'http://127.0.0.1:5173';
const api = 'http://127.0.0.1:8005';
const out = path.resolve('../artifacts/t2-browser/fue-d');
fs.mkdirSync(out, { recursive: true });
const first = await request.newContext({ baseURL: api });
const bootstrap = await first.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password } });
if (!bootstrap.ok()) throw new Error('Owner bootstrap login rejected: ' + bootstrap.status());
const tokens = await bootstrap.json();
const enrolled = await enrollT2Workstation(first, tokens.access_token, password);
await first.dispose();
const stationState = {
  ...enrolled,
  cookies: (enrolled.cookies || []).filter(c => !['access_token', 'refresh_token'].includes(c.name)),
};
const browser = await chromium.launch({ headless: true });
const results = [];
let passed = false;
try {
  for (const profile of [
    { name: 'mobile', width: 390, height: 844, first: 'Mobile' },
    { name: 'desktop', width: 1280, height: 900, first: 'Desktop' },
  ]) {
    const dir = path.join(out, profile.name);
    fs.mkdirSync(dir, { recursive: true });
    const ctx = await browser.newContext({
      viewport: { width: profile.width, height: profile.height },
      colorScheme: 'light',
      storageState: stationState,
    });
    const page = await ctx.newPage();
    const started = Date.now();
    const errors = { page: [], console: [], server: [] };
    const screenshots = [];
    let interactions = 0;
    const snap = async name => {
      const overflow = await page.evaluate(() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > innerWidth + 1);
      const file = name + '.png';
      await page.screenshot({ path: path.join(dir, file), fullPage: true, animations: 'disabled' });
      screenshots.push({ name, file, ms: Date.now() - started, interactions, overflow });
      if (overflow) throw new Error(profile.name + ' horizontal overflow: ' + name);
    };
    page.on('pageerror', e => errors.page.push(String(e.message)));
    page.on('console', msg => { if (msg.type() === 'error') errors.console.push(msg.text()); });
    page.on('response', res => { if (res.status() >= 500) errors.server.push({ status: res.status(), pathname: new URL(res.url()).pathname }); });
    try {
      await page.goto(root + '/login', { waitUntil: 'domcontentloaded' });
      await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.getByPlaceholder('nom@cabinet.com').waitFor({ state: 'visible', timeout: 15000 });
      await snap('01-before-login');
      await page.getByPlaceholder('nom@cabinet.com').fill('t2-browser@cabinet.ma'); interactions++;
      await page.getByPlaceholder('••••••••').fill(password); interactions++;
      await page.getByRole('button', { name: 'Se connecter', exact: true }).click(); interactions++;
      await page.waitForURL(url => !['/login', '/setup'].includes(url.pathname), { timeout: 20000 });
      const state = await ctx.request.get(api + '/api/clinics/init-status');
      if (state.status() !== 200 || (await state.json()).is_initialized !== true) throw new Error('Cabinet not initialized');
      const authorized = await ctx.request.get(api + '/api/patients/?limit=1');
      if (authorized.status() !== 200) throw new Error('Patient authorization=' + authorized.status());
      await page.goto(root + '/patients', { waitUntil: 'domcontentloaded' }); interactions++;
      await page.getByRole('heading', { name: 'Dossiers Patients' }).waitFor({ timeout: 15000 });
      await snap('02-patient-entry');
      await page.getByRole('link', { name: 'Créer un dossier' }).click(); interactions++;
      await page.waitForURL('**/patients/new');
      await page.locator('input[name="nom"]').waitFor({ state: 'visible' });
      await page.evaluate(() => window.scrollTo(0, 0));
      await snap('03-form-before');
      let posts = 0;
      page.on('request', req => { if (req.method() === 'POST' && new URL(req.url()).pathname === '/api/patients/') posts++; });
      await page.getByRole('button', { name: 'Créer le dossier', exact: true }).click(); interactions++;
      if (posts !== 0) throw new Error('Invalid form sent create request');
      const required = await page.locator('body').innerText();
      if (!required.includes('Le nom est requis') || !required.includes('Le prénom est requis')) throw new Error('Required-field refusal not understandable');
      await page.evaluate(() => window.scrollTo(0, 0));
      await snap('04-validation');
      const idtag = 'FUED-' + profile.name.toUpperCase() + '-' + String(Date.now()).slice(-9);
      const nom = 'FUEDTEST';
      await page.locator('input[name="nom"]').fill(nom); interactions++;
      await page.locator('input[name="prenom"]').fill(profile.first); interactions++;
      await page.locator('input[name="date_naissance"]').fill('1990-01-01'); interactions++;
      await page.locator('select[name="sexe"]').selectOption('F'); interactions++;
      await page.locator('input[name="numero_dossier"]').fill(idtag); interactions++;
      await page.evaluate(() => window.scrollTo(0, 0));
      await snap('05-form-filled');
      const createResponse = page.waitForResponse(res => res.request().method() === 'POST' && new URL(res.url()).pathname === '/api/patients/', { timeout: 25000 });
      await page.getByRole('button', { name: 'Créer le dossier', exact: true }).click(); interactions++;
      const response = await createResponse;
      if (!response.ok()) throw new Error('Create HTTP ' + response.status());
      const created = await response.json();
      if (!Number.isInteger(created.id) || created.id <= 0) throw new Error('Create response lacks real positive ID');
      if (String(created.nom).toUpperCase() !== nom || String(created.prenom).toLowerCase() !== profile.first.toLowerCase()) throw new Error('Create ACK identity mismatch');
      const read = await ctx.request.get(api + '/api/patients/' + created.id);
      if (read.status() !== 200) throw new Error('Independent GET patient=' + read.status());
      const persisted = await read.json();
      if (persisted.id !== created.id || String(persisted.nom).toUpperCase() !== nom || String(persisted.prenom).toLowerCase() !== profile.first.toLowerCase()) throw new Error('Persisted record mismatch');
      await page.waitForURL(new RegExp('/patients/' + created.id + '(?:\\?|$)'), { timeout: 15000 });
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.getByText(nom, { exact: false }).first().waitFor({ state: 'visible', timeout: 15000 });
      await snap('06-after-reload');
      const ms = Date.now() - started;
      if (errors.page.length || errors.server.length) throw new Error('Browser/server errors ' + JSON.stringify(errors));
      results.push({ viewport: profile.name, dimensions: [profile.width, profile.height], firstValueMs: ms, interactions, createStatus: response.status(), readStatus: read.status(), patientId: created.id, screenshotCount: screenshots.length, screenshots, errors });
      await ctx.close();
    } catch (e) {
      results.push({ viewport: profile.name, failed: String(e?.stack || e), interactions, screenshots, errors });
      await ctx.close();
      throw e;
    }
  }

  // Independent adversarial permission check: restricted secretary patients=false.
  const restrictedCtx = await request.newContext({ baseURL: api });
  try {
    const auth = await restrictedCtx.post('/api/auth/login', { form: { username: 't2-restricted@cabinet.ma', password } });
    if (!auth.ok()) throw new Error('Restricted persona login status=' + auth.status());
    const restrictedToken = (await auth.json()).access_token;
    const client = await request.newContext({ baseURL: api, storageState: stationState, extraHTTPHeaders: { Authorization: 'Bearer ' + restrictedToken } });
    try {
      const data = { nom: 'FUEDDENIED', prenom: 'Unauthorized', date_naissance: '1990-01-01', sexe: 'F' };
      const read = await client.get('/api/patients/');
      const create = await client.post('/api/patients/', { data });
      const duplicate = await client.post('/api/patients/check-duplicate', { data });
      if ([read.status(), create.status(), duplicate.status()].some(code => code !== 403)) {
        throw new Error('patients=false boundary failed: ' + [read.status(), create.status(), duplicate.status()].join(','));
      }
      results.push({ viewport: 'restricted-api', listStatus: read.status(), createStatus: create.status(), duplicateStatus: duplicate.status() });
    } finally { await client.dispose(); }
  } finally { await restrictedCtx.dispose(); }
  passed = true;
} finally {
  await browser.close();
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify({ productHead: process.env.PRODUCT_HEAD || null, passed, completedAt: new Date().toISOString(), results }, null, 2));
}
if (!passed) throw new Error('FUE-D not certified');
console.log('FUE_D_PATIENT_CREATION_PASS ' + JSON.stringify(results.map(({ viewport, firstValueMs, interactions, createStatus, readStatus }) => ({ viewport, firstValueMs, interactions, createStatus, readStatus }))));
