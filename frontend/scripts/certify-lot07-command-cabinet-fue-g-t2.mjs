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
let authenticatedOwnerState;
try {
  const ownerToken = await loginToken(actorEmail.owner);
  const enrollment = await enrollT2Workstation(setup, ownerToken, password);
  cookies = enrollment.cookies.filter(x => x.name === 'dc_workstation');
  assert.equal(cookies.length, 1, 'Exactly one real enrollment cookie');
  point('real-owner-login-and-enrolled-workstation', { enrollmentCookies: cookies.length });

  // The setup context has just authenticated and enrolled a workstation.
  // Do not reuse it for the anonymous probe: Playwright shares its cookie jar.
  const anonymous = await request.newContext({
    baseURL: apiBase,
    storageState: { cookies: [], origins: [] },
  });
  try {
    const noAuth = await anonymous.get(appointmentPath);
    assert.ok([401, 403, 423].includes(noAuth.status()),
      'Fresh HTTP context without JWT/cookies must be rejected; got '+noAuth.status());
    const state = await anonymous.storageState();
    assert.equal(state.cookies.length, 0, 'Anonymous probe must remain cookie-free');
    point('backend-anonymous-request-denied', { httpStatus: noAuth.status(), cookieCount: 0 });
  } finally {
    await anonymous.dispose();
  }

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
  const restrictedAppointment = restrictedGet.body.find(x => x.id === firstId);
  assert.ok(restrictedAppointment, 'Agenda-only staff keeps anonymized timetable row');
  for (const key of ['patient_name', 'patient_id', 'motif', 'notes', 'phone', 'source', 'confirmed_by_id']) {
    assert.equal(restrictedAppointment[key], null, 'Agenda-only response MUST minimize '+key);
  }
  assert.ok(!JSON.stringify(restrictedGet.body).includes('T2 COMMAND SYNTHETIC'),
    'Agenda-only HTTP response MUST NOT contain a patient identifier');
  assert.equal(restrictedAppointment.datetime_start, ownerFixture.datetime_start);
  assert.equal(restrictedAppointment.status, ownerFixture.status);
  point('backend-agenda-only-staff', { httpStatus: restrictedGet.status, sameAppointment: firstId, httpIdentityRedacted: true });

  const patientDetailGet = await authGET(restrictedToken, '/api/appointments/patient/'+ownerFixture.patient_id, cookies);
  assert.equal(patientDetailGet.status, 403, 'Agenda-only user cannot fetch another patient appointment history');
  point('backend-patient-history-forbidden', { httpStatus: 403 });

  const deniedToken = await loginToken(actorEmail.denied);
  const deniedGet = await authGET(deniedToken, appointmentPath, cookies);
  assert.equal(deniedGet.status, 403, 'Staff without Agenda permission must be denied by backend');
  point('backend-agenda-permission-refused', { httpStatus: deniedGet.status });

  const otherToken = await loginToken(actorEmail.otherTenant);
  // A workstation is bound to one cabinet; never use the first owner's cookie to
  // "prove" isolation of an independent second cabinet. Both owners must enroll.
  const foreignCookieGet = await authGET(otherToken, appointmentPath, cookies);
  assert.equal(foreignCookieGet.status, 423,
    'A second cabinet must reject the first cabinet workstation identity');
  point('backend-foreign-workstation-denied', { httpStatus: foreignCookieGet.status });
  const independentEnrollment = await request.newContext({
    baseURL: apiBase, storageState: { cookies: [], origins: [] },
  });
  try {
    const secondState = await enrollT2Workstation(independentEnrollment, otherToken, password);
    const otherCookies = secondState.cookies.filter(x => x.name === 'dc_workstation');
    assert.equal(otherCookies.length, 1, 'Other owner must enroll one distinct legitimate workstation');
    assert.notEqual(otherCookies[0].value, cookies[0].value,
      'Workstation identities must not be shared between cabinets');
    const otherGet = await authGET(otherToken, appointmentPath, otherCookies);
    assert.equal(otherGet.status, 200, 'Second owner reads own cabinet using its enrolled workstation');
    assert.ok(Array.isArray(otherGet.body), 'Second cabinet GET is a real response array');
    assert.ok(!otherGet.body.some(x => x.id === firstId), 'No cross-tenant appointment ID disclosure');
    assert.ok(!otherGet.body.some(x => x.patient_name === 'T2 COMMAND SYNTHETIC'),
      'First cabinet patient name cannot appear in second cabinet response');
    assert.ok(otherGet.body.some(x => x.patient_name === 'OTHER CABINET SYNTHETIC'),
      'Independent owner must see their own appointment to prove meaningful scoping');
    point('backend-cross-tenant-isolation', {
      status: otherGet.status, otherCabinetAppointmentVisible: true,
      foreignIdVisible: false, separateWorkstation: true,
    });
  } finally {
    await independentEnrollment.dispose();
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
      // A staff member with agenda=false and patients=false has no quick-action button.
      // Check the real Dashboard heading, which is present for all authenticated roles.
      await page.getByRole('heading', { name: /^Bonjour,/ }).waitFor({ state: 'visible', timeout: 40000 });
      item.fullLogin = true;
      const sessionToken = await page.evaluate(() => localStorage.getItem('token'));
      assert.ok(sessionToken, 'Real UI session token');
      if (actor === 'owner') authenticatedOwnerState = await context.storageState();
      // Match Dashboard's exact getLocalDayBounds URL on the same browser-local
      // calendar day, rather than comparing all historical appointments.
      const todayKey = await page.evaluate(() => {
        const today = new Date();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${today.getFullYear()}-${month}-${day}`;
      });
      const todayPath = `${appointmentPath}?start_date=${todayKey}T00:00:00&end_date=${todayKey}T23:59:59`;
      const dashboardResponsePromise = expectAllowed
        ? page.waitForResponse(r => r.url().includes('/api/appointments/') && r.request().method() === 'GET', { timeout: 30000 })
        : null;
      await page.reload({ waitUntil: 'domcontentloaded' });
      if (expectAllowed) {
        const signatureResponse = await dashboardResponsePromise;
        item.signatureStatus = signatureResponse.status();
        assert.equal(item.signatureStatus, 200, 'Signature uses authenticated real API');
        // Network.getResponseBody on a navigation/reload may already be released
        // by Chromium CDP. Assert the real Dashboard GET and obtain its schema
        // from an independent authenticated REST read using the same UI JWT.
        // This does NOT claim the legacy Signature rows have visual parity.
        const signatureGet = await authGET(sessionToken, todayPath, cookies);
        assert.equal(signatureGet.status, 200, 'Signature actor must read a live Cabinet agenda');
        const signatureData = signatureGet.body;
        assert.ok(Array.isArray(signatureData), 'Signature actor agenda response is an array');
        assert.ok(signatureData.some(x => x.id === firstId), 'Signature actor gets seeded appointment ID');
        item.signature = signatureData.map(({ id, status, datetime_start }) => ({ id, status, datetime_start }));
        item.sourceParity = 'Actual Signature Dashboard GET 200, canonical real Cabinet response and rendered room label/time';
        await page.getByText('File d\'attente & Arrivées du Jour', { exact: false }).waitFor({ state: 'visible', timeout: 30000 });
        await page.getByText('09:15', { exact: true }).first().waitFor({ state: 'visible', timeout: 30000 });
        if (expectName) {
          await page.getByText('T2 COMMAND SYNTHETIC').first().waitFor({ state: 'visible', timeout: 30000 });
        } else {
          assert.ok(!await page.locator('body').innerText().then(x => x.includes('T2 COMMAND SYNTHETIC')),
            'Agenda-only Signature DOM must not disclose patient name');
          assert.ok(!signatureData.some(x => x.patient_name != null || x.patient_id != null),
            'Agenda-only Signature REST must not disclose patient name or id');
        }
        assert.ok(!await page.locator('body').innerText().then(x => x.includes('Invalid Date')),
          'Signature Dashboard must NOT show an invalid appointment date');
        item.signatureRealDomParity = true;
        point('signature-real-cabinet-display-'+actor, { time: '09:15', identityShown: expectName });
        await capture(page, actor + '-01-signature-after');
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
        // The real Command GET was observed from this page. Compare stable
        // live backend snapshots with the same browser's JWT on both screens,
        // then verify that Command actually rendered their IDs/time/status.
        const commandGet = await authGET(sessionToken, todayPath, cookies);
        assert.equal(commandGet.status, 200, 'Command actor must read a live Cabinet agenda');
        const commandData = commandGet.body;
        assert.ok(Array.isArray(commandData), 'Command actor agenda response is an array');
        item.command = commandData.map(({ id, status, datetime_start }) => ({ id, status, datetime_start }));
        assert.deepEqual(item.command, item.signature,
          'Real backend data must be stable under the same actor across Signature and Command');
        await page.locator('[data-testid="command-cabinet-readonly"]').waitFor({ state: 'visible', timeout: 25000 });
        await page.locator('tbody tr').first().waitFor({ state: 'visible', timeout: 25000 });
        const line = (await page.locator('tbody tr').allTextContents()).join('\n');
        assert.ok(line.includes('09:15'), 'Actual Cabinet wall clock time must render');
        assert.ok(line.includes(ownerFixture.status), 'Same actual appointment status must render');
        assert.equal(Number((await page.locator('[data-testid="command-count"]').innerText()).trim()), commandData.length);
        if (expectName) assert.ok(line.includes('T2 COMMAND SYNTHETIC'), 'Owner identity is permitted');
        else assert.ok(!line.includes('T2 COMMAND SYNTHETIC'), 'Agenda-only staff patient identity redacted');
        assert.equal(await page.getByRole('button', { name: 'Actualiser les rendez-vous' }).count(), 1);
        assert.equal(await page.locator('[data-ux1-c-crownbot-floating]').count(), 0,
          'CrownBot floating control must not overlay the 07-C Command lab');
        await capture(page, actor + '-02-command-after');
        if (actor === 'owner') {
          await page.evaluate(() => { document.body.style.zoom = '200%'; });
          const viewport = await page.evaluate(() => ({
            clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth,
          }));
          item.cssZoom200 = viewport;
          await capture(page, actor + '-03-command-csszoom200');
          assert.equal(await page.locator('[data-ux1-c-crownbot-floating]').count(), 0,
            '200% Command must not be overlapped by floating CrownBot');
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

  assert.ok(authenticatedOwnerState, 'Real owner UI must have completed before mobile smoke');
  const mobile = await browser.newContext({
    ...devices['iPhone 13'], storageState: authenticatedOwnerState, reducedMotion: 'reduce',
  });
  try {
    const page = await mobile.newPage();
    await page.goto(uiBase + '/command-cabinet-lab', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    assert.ok(await page.evaluate(() => Boolean(localStorage.getItem('token'))), 'Mobile smoke must have authenticated owner session');
    assert.equal(await page.locator('[data-testid="command-cabinet-readonly"]').count(), 0);
    point('mobile-command-not-rendered', { viewport: 390, authenticated: true, userAgent: 'iPhone 13 Playwright device' });
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
