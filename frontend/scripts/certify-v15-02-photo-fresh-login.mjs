// FUE-G02 first-login extension. Disposable T2 backend; never a real patient/cabinet.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const email = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
const head = process.env.EVALUATED_SHA;
if (!email || !password || !/^[0-9a-f]{40}$/.test(head || '')) {
  throw new Error('T2 credentials and exact evaluated SHA required');
}
if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' || process.env.ENVIRONMENT !== 'test') {
  throw new Error('Refuse FUE photo writes outside the isolated T2 test runtime');
}
const ui = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
const root = path.resolve('../artifacts/v15-02-4-photo-lifecycle');
await fs.mkdir(root, { recursive: true });

// Already-used, high-contrast synthetic square fixture. No real patient imagery.
const portrait = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAIAAABt+uBvAAABsElEQVR42u3a0U0DQQyE4YtFB3RCBYhukKgAiSdaQKKbiF54pgcqSHS3a3vWvn9fI8XjT3OrRMnl9/1p49w+BgFAAAEEEEAAAQQQB6CB87BCiMe371sv/X29arNdVN/F7qAshSUAGqARMqUCTdJImKyijvu76YEi9skxCn/EEtYIfdysuk70FD4o6oDS7tHQWdZAJ3Si9dCJm8sdlA6kqk/QdBqUC6StT0QGGgQQQGWAVriA3JPQIIAAAggggAACCKD5I/8dPSIJDQIIoEpAK1xDvhloUDqQtkTu02mQAkhVooi5ViirZKKVS5w8iztICpRTotApGf9y/bw+x735x8tPaPgooFCUTCx/IAlNHJMnkJwmgskHaCkaXyZrrOOSzRrruCS03jrzOa29zmRaO4POTGY7ic5wcjuPzlh+vs27AlWvz8AWNMgPqEd9ju5Cg5yAOtXn0EY0CCCA9ED9LqD9e9EggAACCCCAAAIIoDsn+h8UqrNnLxoEEEBLAPW7hnZuRIP8gDqVaP8uNMgVqEeJDm1Bg7yBqpfoaH5LmFFXZ/wRq2g0ltmS59XS2bbtH1pkla0CIqybAAAAAElFTkSuQmCC',
  'base64',
);

const api = await request.newContext({ baseURL: backend });
const ownerLogin = await api.post('/api/auth/login', { form: { username: email, password } });
if (!ownerLogin.ok()) throw new Error('Isolated owner workstation enrollment login failed: ' + ownerLogin.status());
const ownerToken = (await ownerLogin.json()).access_token;
const ownerHeaders = { Authorization: 'Bearer ' + ownerToken };
const storage = await enrollT2Workstation(api, ownerToken, password);
const workstationCookies = storage.cookies.filter(cookie => cookie.name === 'dc_workstation');
if (workstationCookies.length !== 1) throw new Error('Expected one legitimate dc_workstation cookie');
const initialStorage = { cookies: workstationCookies, origins: [] };
if (initialStorage.cookies.some(cookie => /access|refresh|auth/i.test(cookie.name))) {
  throw new Error('An authentication cookie leaked into the new browser');
}
const patientResponse = await api.get('/api/patients/', { headers: ownerHeaders });
if (!patientResponse.ok()) throw new Error('Owner patient fixture read failed');
const patients = await patientResponse.json();
const patient = patients.find(x => x.numero_dossier === 'T2-0001');
if (!patient) throw new Error('Expected exact isolated patient T2-0001, not an arbitrary patient');
const patientId = patient.id;
const fullName = (String(patient.nom).toUpperCase() + ' ' + String(patient.prenom)).trim();
const photoPath = '/api/patients/' + patientId + '/photo';
const report = { head, isolated: true, workstation: 'legitimately enrolled, only dc_workstation cookie transferred', noAuthTokenInjection: true, viewports: [], denials: [], success: false };
const browser = await chromium.launch({ headless: true });

async function capture(page, name, result) {
  const file = 'fresh-login-' + name + '.png';
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
  if (overflow) throw new Error('Horizontal overflow at ' + name);
  await page.screenshot({ path: path.join(root, file), fullPage: false, animations: 'disabled' });
  result.images.push(file);
}
async function loginInUi(page, actorEmail) {
  await page.goto(ui + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.locator('input[type=email]').waitFor({ state: 'visible', timeout: 30000 });
  const before = await page.evaluate(() => ({
    token: localStorage.getItem('token'),
    refresh: localStorage.getItem('refresh_token'),
  }));
  if (before.token || before.refresh) throw new Error('Browser was already authenticated before UI login');
  await page.locator('input[type=email]').fill(actorEmail);
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
  await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 45000 });
  await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({ state: 'visible', timeout: 30000 });
  if (!await page.evaluate(() => Boolean(localStorage.getItem('token')))) {
    throw new Error('UI login did not establish authenticated browser session');
  }
}
async function verifyNegativeApis() {
  const before = await api.get(photoPath, { headers: ownerHeaders });
  if (before.status() !== 200) throw new Error('Owner must read the current photo before negative checks');
  const beforeHash = crypto.createHash('sha256').update(await before.body()).digest('hex');

  const anonymous = await request.newContext({ baseURL: backend });
  try {
    const denied = await anonymous.get(photoPath);
    if (![401, 403].includes(denied.status())) throw new Error('Anonymous photo GET unexpectedly ' + denied.status());
    report.denials.push({ actor: 'anonymous', method: 'GET', status: denied.status() });
  } finally { await anonymous.dispose(); }

  for (const actor of [
    { email: 't2-restricted@cabinet.ma', role: 'no-patients-permission', allowed: [403] },
    { email: 't2-setup-390@cabinet.ma', role: 'different-tenant', allowed: [403, 404] },
  ]) {
    // The T2 backend enforces a cabinet-scoped workstation identity BEFORE RBAC.
    // A 423 without an enrolled workstation is NOT proof that the patient's
    // permission/tenant scope denied an authenticated request.
    // Staff use the owner's legitimate workstation; the independent dentist
    // must enroll their OWN tenant workstation (never reuse the owner's cookie).
    const sameTenant = actor.role === 'no-patients-permission';
    const scoped = await request.newContext({
      baseURL: backend,
      storageState: sameTenant ? initialStorage : { cookies: [], origins: [] },
    });
    try {
      const response = await scoped.post('/api/auth/login', { form: { username: actor.email, password } });
      if (!response.ok()) throw new Error(actor.role + ' login failure: ' + response.status());
      const token = (await response.json()).access_token;
      const headers = { Authorization: 'Bearer ' + token };
      if (!sameTenant) {
        const independent = await enrollT2Workstation(scoped, token, password);
        if (independent.cookies.filter(cookie => cookie.name === 'dc_workstation').length !== 1) {
          throw new Error('Independent tenant did not get its own workstation identity');
        }
      }
      const workstation = await scoped.get('/api/workstation/state', { headers });
      if (workstation.status() !== 200) {
        throw new Error(actor.role + ' workstation not authorized: ' + workstation.status());
      }
      // Independently prove this actor has reached the backend authorization
      // layer; do not accept workstation-level refusal as a patient RBAC result.
      const patientList = await scoped.get('/api/patients/', { headers });
      if (sameTenant && patientList.status() !== 403) {
        throw new Error('Staff lacks patients permission, expected 403: ' + patientList.status());
      }
      if (!sameTenant) {
        if (patientList.status() !== 200) {
          throw new Error('Independent dentist patient list unavailable: ' + patientList.status());
        }
        const visiblePatients = await patientList.json();
        if (visiblePatients.some(row => Number(row.id) === Number(patientId))) {
          throw new Error('Independent tenant can enumerate the owner patient');
        }
      }
      const tests = [
        ['GET', () => scoped.get(photoPath, { headers })],
        ['POST', () => scoped.post(photoPath, { headers, multipart: {
          file: { name: 'negative-fixture.png', mimeType: 'image/png', buffer: portrait },
        } })],
        ['DELETE', () => scoped.delete(photoPath, { headers })],
      ];
      for (const [method, act] of tests) {
        const denied = await act();
        if (!actor.allowed.includes(denied.status())) {
          throw new Error(actor.role + ' photo ' + method + ' unexpectedly ' + denied.status());
        }
        report.denials.push({ actor: actor.role, method, status: denied.status() });
      }
    } finally { await scoped.dispose(); }
  }
  const after = await api.get(photoPath, { headers: ownerHeaders });
  if (after.status() !== 200) throw new Error('Restricted requests altered owner photo visibility');
  const afterHash = crypto.createHash('sha256').update(await after.body()).digest('hex');
  if (beforeHash !== afterHash) throw new Error('Restricted requests mutated the owner photo');
  report.denialPhotoPreserved = true;
}

try {
  for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
    const reset = await api.delete(photoPath, { headers: ownerHeaders });
    if (![204, 404].includes(reset.status())) throw new Error('Isolated initial photo reset failed: ' + reset.status());
    const context = await browser.newContext({
      viewport, reducedMotion: 'reduce', storageState: initialStorage,
    });
    const result = { viewport, images: [], steps: [], pageErrors: [] };
    const page = await context.newPage();
    page.on('pageerror', error => result.pageErrors.push(String(error)));
    try {
      await page.goto(ui + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.locator('input[type=email]').waitFor({ state: 'visible', timeout: 30000 });
      if (await page.evaluate(() => Boolean(localStorage.getItem('token')))) throw new Error('Non-blank login baseline');
      await capture(page, viewport.width + '-01-login-before', result);
      await loginInUi(page, email);
      result.steps.push('Fresh empty-storage browser performed actual product login');
      await capture(page, viewport.width + '-02-dashboard-after-login', result);

      await page.goto(ui + '/patients/' + patientId + '/edit', { waitUntil: 'networkidle', timeout: 90000 });
      await page.locator('[data-patient-photo-editor]').waitFor({ state: 'visible', timeout: 30000 });
      await page.getByLabel('Initiales du patient').waitFor({ state: 'visible', timeout: 30000 });
      await capture(page, viewport.width + '-03-before-photo', result);
      await page.getByLabel('Importer une photo du patient').setInputFiles({
        name: 'fue-synthetic-portrait.png', mimeType: 'image/png', buffer: portrait,
      });
      const dialog = page.getByRole('dialog', { name: 'Recadrer la photo' });
      await dialog.waitFor({ state: 'visible', timeout: 30000 });
      await dialog.getByRole('button', { name: 'Enregistrer la photo' }).click();
      await dialog.waitFor({ state: 'detached', timeout: 30000 });
      await page.getByRole('button', { name: 'Supprimer', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
      const ownerGet = await api.get(photoPath, { headers: ownerHeaders });
      if (ownerGet.status() !== 200) throw new Error('Real UI photo save did not persist canonical asset');
      result.steps.push('Authenticated UI file import, crop, save, canonical backend photo read');
      await capture(page, viewport.width + '-04-photo-saved', result);

      if (viewport.width === 390) await verifyNegativeApis();
      await page.evaluate(() => localStorage.setItem('patient_list_view_mode', 'table'));
      await page.goto(ui + '/patients', { waitUntil: 'networkidle', timeout: 90000 });
      const badges = page.locator('[data-testid="patient-list-score-badges"][data-patient-id="' + patientId + '"]');
      await badges.waitFor({ state: 'visible', timeout: 30000 });
      await badges.getByRole('button', { name: 'Tag cabinet manuel' }).waitFor({ state: 'visible', timeout: 30000 });
      await badges.scrollIntoViewIfNeeded();
      await page.mouse.move(2, 2);
      const badgeMetrics = await badges.evaluate(element => {
        const labels = Array.from(element.querySelector(':scope > div')?.children || [])
          .filter(node => node.matches('span, button'));
        const rects = labels.map(node => {
          const rect = node.getBoundingClientRect();
          return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom,
            textClipped: node.scrollWidth > node.clientWidth + 1 };
        });
        return { count: labels.length, rects, visible: rects.length >= 3 &&
          rects.every(box => box.left >= 0 && box.right <= innerWidth + 1 &&
            box.top >= 0 && box.bottom <= innerHeight + 1 && !box.textClipped) };
      });
      if (!badgeMetrics.visible) throw new Error('Badges not visibly within viewport after scroll: ' + JSON.stringify(badgeMetrics));
      result.badgeMetrics = badgeMetrics;
      result.steps.push('Scrolled actual three-badge row visibly into the viewport');
      await capture(page, viewport.width + '-05-patient-badges-scrolled', result);

      await page.goto(ui + '/patients/' + patientId + '/edit', { waitUntil: 'networkidle', timeout: 90000 });
      const del = page.getByRole('button', { name: 'Supprimer', exact: true });
      await del.waitFor({ state: 'visible', timeout: 30000 });
      await del.click();
      await del.waitFor({ state: 'detached', timeout: 30000 });
      await page.getByLabel('Initiales du patient').waitFor({ state: 'visible', timeout: 30000 });
      const gone = await api.get(photoPath, { headers: ownerHeaders });
      if (gone.status() !== 404) throw new Error('Photo still accessible after UI deletion: ' + gone.status());
      result.steps.push('UI delete restored initials and denied missing canonical photo');
      await capture(page, viewport.width + '-06-photo-deleted', result);
      if (result.pageErrors.length) throw new Error('Unexpected JS exceptions: ' + result.pageErrors.join('; '));
      report.viewports.push(result);
    } finally { await context.close(); }
  }

  const restricted = await browser.newContext({
    viewport: { width: 390, height: 844 }, reducedMotion: 'reduce', storageState: initialStorage,
  });
  try {
    const page = await restricted.newPage();
    await loginInUi(page, 't2-restricted@cabinet.ma');
    await page.goto(ui + '/patients/' + patientId + '/edit', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 30000 });
    if (await page.locator('[data-patient-photo-editor]').count()) {
      throw new Error('Restricted user reached patient photo editor');
    }
    await page.screenshot({
      path: path.join(root, 'fresh-login-restricted-390-denied.png'),
      fullPage: false, animations: 'disabled',
    });
    report.restrictedUiRedirected = true;
  } finally { await restricted.close(); }
  report.success = report.viewports.length === 2 && report.denials.length === 7 &&
    report.restrictedUiRedirected && report.denialPhotoPreserved;
  if (!report.success) throw new Error('Incomplete first-login or negative-role matrix');
} finally {
  try { await api.delete(photoPath, { headers: ownerHeaders }); } catch { /* disposable cleanup */ }
  await browser.close();
  await api.dispose();
  await fs.writeFile(path.join(root, 'fresh-login-photo-evidence.json'), JSON.stringify(report, null, 2));
}
console.log('V15_02_FUE_FRESH_LOGIN_PASS', JSON.stringify({
  head, viewports: report.viewports.length, denied: report.denials.length, success: report.success,
}));
if (!report.success) process.exitCode = 1;
