// LOT07/07-C — authentic T2 FastAPI + React browser FUE, synthetic disposable DB only.
// No production writes, no mocks, no release activation, no substitute for human/native-zoom approval.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request, devices } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha = process.env.EVALUATED_SHA;
const password = process.env.T2_PASSWORD;
assert.match(sha || '', /^[a-f0-9]{40}$/);
assert.ok(password && process.env.ENVIRONMENT === 'test' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1' &&
  process.env.VITE_COMMAND_CABINET_LAB === 'true', 'Disposable T2 lab must be explicit');
const apiBase = 'http://127.0.0.1:8005';
const uiBase = 'http://127.0.0.1:5173';
const dest = path.resolve('../artifacts/lot07-07c-command-cabinet-fue-g');
const report = {
  sha, surface: 'REAL_AUTH_REACT_APP_FASTAPI_T2_ONLY', backendMocked: false,
  clinicalProductionData: false, commandRelease: false, nativeZoom200: false,
  humanVisualApproval: false, pass: false, checks: [], failures: [],
};
await fs.mkdir(dest, { recursive: true });
const setup = await request.newContext({ baseURL: apiBase });
const browser = await chromium.launch({ headless: true });
const point = (name, details) => report.checks.push({ name, details });
const capture = (page, label) => page.screenshot({
  path: path.join(dest, label + '.png'), fullPage: true, animations: 'disabled',
});
const loginToken = async email => {
  const response = await setup.post('/api/auth/login', { form: { username: email, password } });
  assert.equal(response.status(), 200, 'Real backend login '+email);
  const token = (await response.json()).access_token;
  assert.ok(token, 'Real JWT '+email);
  return token;
};
const authGET = async (token, relativePath, cookies=[]) => {
  const ctx = await request.newContext({ baseURL: apiBase, storageState: { cookies, origins: [] } });
  try {
    const response = await ctx.get(relativePath, { headers: { Authorization: 'Bearer '+token } });
    const status = response.status();
    const body = status === 200 ? await response.json() : null;
    return { status, body };
  } finally { await ctx.dispose(); }
};
const appointmentPath = '/api/appointments/';
const actorEmail = {
  owner: 't2-browser@cabinet.ma',
  restricted: 't2-restricted@cabinet.ma',
  denied: 't2-command-denied@cabinet.ma',
  otherTenant: 't2-command-other-owner@cabinet.ma',
};
let cookies;
try {
  const ownerToken = await loginToken(actorEmail.owner);
  const enrollment = await enrollT2Workstation(setup, ownerToken, password);
  cookies = enrollment.cookies.filter(x => x.name === 'dc_workstation');
  assert.equal(cookies.length, 1, 'Exactly one real enrollment cookie');
  point('real-owner-login-and-enrolled-workstation', { enrollmentCookies: cookies.length });

  const noAuth = await setup.get(appointmentPath);
  assert.notEqual(noAuth.status(), 200, 'Unprivileged REST access refused');
  point('backend-anonymous-request-denied', { httpStatus: noAuth.status() });

  const fresh = await authGET(ownerToken, '/api/clinics/init-status');
  assert.equal(fresh.status, 423, 'No workstation should be authorized for clinical initialization');
  point('backend-fresh-workstation-denied', { httpStatus: fresh.status });

  const ownerGet = await authGET(ownerToken, appointmentPath, cookies);
  assert.equal(ownerGet.status, 200, 'Owner can GET appointments through real API');
  assert.ok(Array.isArray(ownerGet.body), 'Owner appointments response array');
  const ownerFixture = ownerGet.body.find(x => x.patient_name === 'T2 COMMAND SYNTHETIC');
  assert.ok(ownerFixture, 'Seeded owner appointment exists on actual backend');
  assert.match(ownerFixture.datetime_start, /T09:15:00$/);
  const firstId = ownerFixture.id;
  point('backend-owner-appointment', { httpStatus: 200, id: firstId, status: ownerFixture.status, start: ownerFixture.datetime_start });

  const restrictedToken = await loginToken(actorEmail.restricted);
  const restrictedGet = await authGET(restrictedToken, appointmentPath, cookies);
  assert.equal(restrictedGet.status, 200, 'Agenda-only staff may read appointment schedule');
  assert.ok(restrictedGet.body.some(x => x.id === firstId), 'Agenda-only staff same tenant');
  point('backend-agenda-only-staff', { httpStatus: restrictedGet.status, sameAppointment: firstId });

  const deniedToken = await loginToken(actorEmail.denied);
  const deniedGet = await authGET(deniedToken, appointmentPath, cookies);
  assert.equal(deniedGet.status, 403, 'Staff without Agenda permission must be denied by backend');
  point('backend-agenda-permission-refused', { httpStatus: deniedGet.status });

  const otherToken = await loginToken(actorEmail.otherTenant);
  const otherGet = await authGET(otherToken, appointmentPath, cookies);
  // An owner on another cabinet may need their own workstation enrollment. Either
  // tenant separation is proven via 200-scoped list, or it is explicitly unproven.
  if (otherGet.status === 200) {
    assert.ok(!otherGet.body.some(x => x.id === firstId), 'No foreign tenant appointment');
    assert.ok(otherGet.body.some(x => x.patient_name === 'OTHER CABINET SYNTHETIC'));
    point('backend-cross-tenant-isolation', { status: 200, foreignIdVisible: false });
  } else {
    point('backend-cross-tenant-unresolved', { httpStatus: otherGet.status, certified: false });
  }

  const visit = async (actor, { expectAllowed, expectName }) => {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce',
      storageState: { cookies, origins: [] },
    });
    const item = { actor, fullLogin: false, signatureStatus: null, commandStatus: null };
    try {
      const page = await context.newPage();
      const writeCalls = [];
      page.on('request', req => {
        if (/\/api\/appointments\//.test(req.url()) && req.method() !== 'GET') {
          writeCalls.push(req.method());
        }
      });
      await page.goto(uiBase + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.locator('input[type=email]').waitFor({ state: 'visible', timeout: 40000 });
      await page.locator('input[type=email]').fill(actorEmail[actor]);
      await page.locator('input[type=password]').fill(password);
      await capture(page, actor + '-00-login-before');
      await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
      await page.waitForURL(x => new URL(x).pathname === '/dashboard', { timeout: 60000 });
      await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({ state: 'visible', timeout: 40000 });
      item.fullLogin = true;
      assert.ok(await page.evaluate(() => Boolean(localStorage.getItem('token'))), 'Real UI session token');
      const dashboardResponsePromise = expectAllowed
        ? page.waitForResponse(r => r.url().includes('/api/appointments/') && r.request().method() === 'GET', { timeout: 30000 })
        : null;
      await page.reload({ waitUntil: 'domcontentloaded' });
      if (expectAllowed) {
        const signatureResponse = await dashboardResponsePromise;
        item.signatureStatus = signatureResponse.status();
        assert.equal(item.signatureStatus, 200, 'Signature uses authenticated real API');
        const signatureData = await signatureResponse.json();
        assert.ok(signatureData.some(x => x.id === firstId), 'Signature got original seeded appointment ID');
        await capture(page, actor + '-01-signature-before');
        item.signature = signatureData.map(({ id, status, datetime_start }) => ({ id, status, datetime_start }));
      } else {
        await capture(page, actor + '-01-dashboard-before');
      }
      const commandResponsePromise = expectAllowed
        ? page.waitForResponse(r => r.url().includes('/api/appointments/') && r.request().method() === 'GET', { timeout: 30000 })
        : null;
      await page.goto(uiBase + '/command-cabinet-lab', { waitUntil: 'domcontentloaded' });
      if (expectAllowed) {
        const commandResponse = await commandResponsePromise;
        item.commandStatus = commandResponse.status();
        assert.equal(item.commandStatus, 200, 'Command uses authenticated real API');
        const commandData = await commandResponse.json();
        item.command = commandData.map(({ id, status, datetime_start }) => ({ id, status, datetime_start }));
        assert.deepEqual(item.command, item.signature, 'Signature and Command receive the same exact backend appointments');
        await page.locator('[data-testid="command-cabinet-readonly"]').waitFor({ state: 'visible', timeout: 25000 });
        await page.locator('tbody tr').first().waitFor({ state: 'visible', timeout: 25000 });
        const line = (await page.locator('tbody tr').allTextContents()).join('\n');
        assert.ok(line.includes('09:15'), 'Actual Cabinet wall clock time must render');
        assert.ok(line.includes(ownerFixture.status), 'Same actual appointment status must render');
        assert.equal(Number((await page.locator('[data-testid="command-count"]').innerText()).trim()), commandData.length);
        if (expectName) assert.ok(line.includes('T2 COMMAND SYNTHETIC'), 'Owner identity is permitted');
        else assert.ok(!line.includes('T2 COMMAND SYNTHETIC'), 'Agenda-only staff patient identity redacted');
        assert.equal(await page.getByRole('button', { name: 'Actualiser les rendez-vous' }).count(), 1);
        await capture(page, actor + '-02-command-after');
        if (actor === 'owner') {
          await page.evaluate(() => { document.body.style.zoom = '200%'; });
          const viewport = await page.evaluate(() => ({
            clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth,
          }));
          item.cssZoom200 = viewport;
          await capture(page, actor + '-03-command-csszoom200');
          assert.ok(viewport.scrollWidth <= viewport.clientWidth + 2, 'Body must not overflow at CSS 200% lab approximation');
        }
      } else {
        await page.waitForURL(x => new URL(x).pathname === '/dashboard', { timeout: 45000 });
        assert.equal(await page.locator('[data-testid="command-cabinet-readonly"]').count(), 0);
        item.commandDenied = true;
        await capture(page, actor + '-02-command-denied-after');
      }
      assert.deepEqual(writeCalls, [], 'Navigation and refresh must not write appointments');
      point('real-ui-'+actor, item);
    } finally { await context.close(); }
  };
  await visit('owner', { expectAllowed: true, expectName: true });
  await visit('restricted', { expectAllowed: true, expectName: false });
  await visit('denied', { expectAllowed: false, expectName: false });

  const mobile = await browser.newContext({
    ...devices['iPhone 13'], storageState: { cookies, origins: [] }, reducedMotion: 'reduce',
  });
  try {
    const page = await mobile.newPage();
    await page.goto(uiBase + '/command-cabinet-lab', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    assert.equal(await page.locator('[data-testid="command-cabinet-readonly"]').count(), 0);
    point('mobile-command-not-rendered', { viewport: 390, userAgent: 'iPhone 13 synthetic device' });
    await capture(page, 'mobile-390-no-command');
  } finally { await mobile.close(); }
} catch (error) {
  report.failures.push({ error: String(error?.stack || error).slice(0, 2500) });
} finally {
  await browser.close();
  await setup.dispose();
}
report.pass = report.failures.length === 0 &&
  report.checks.some(x => x.name === 'real-ui-owner') &&
  report.checks.some(x => x.name === 'real-ui-restricted') &&
  report.checks.some(x => x.name === 'real-ui-denied');
await fs.writeFile(path.join(dest, 'report.json'), JSON.stringify(report, null, 2));
console.log('LOT07_07C_REAL_CABINET_FUE_G', JSON.stringify({
  sha, pass: report.pass, checks: report.checks.map(x => x.name), failures: report.failures,
}));
if (!report.pass) process.exitCode = 1;
