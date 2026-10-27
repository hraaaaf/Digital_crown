// LOT07 R4 07-B/07-C — authentic T2 FastAPI + React browser FUE for 4 surfaces + Iconic.
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
  process.env.VITE_COMMAND_CABINET_LAB === 'true' &&
  process.env.VITE_V15_07_R4_SIGNATURE_LAB === 'true', 'Disposable R4 T2 lab must be explicit');
const apiBase = 'http://127.0.0.1:8005';
const uiBase = 'http://127.0.0.1:5173';
const dest = path.resolve('../artifacts/lot07-r4-iconic-command-fue-g');
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
const authPOST = async (token, relativePath, json, cookies=[]) => {
  const ctx = await request.newContext({ baseURL: apiBase, storageState: { cookies, origins: [] } });
  try {
    const response = await ctx.post(relativePath, {
      headers: { Authorization: 'Bearer '+token }, data: json,
    });
    const status = response.status();
    return { status, body: status === 200 ? await response.json() : null };
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
  assert.equal(ownerFixture.motif, 'T2_PRIVATE_MOTIF_CANARY', 'Owner must keep meaningful appointment motif');
  assert.equal(ownerFixture.notes, 'T2_PRIVATE_NOTE_CANARY', 'Owner must retain clinic notes');
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
  assert.ok(!/T2 COMMAND SYNTHETIC|T2_PRIVATE_MOTIF_CANARY|T2_PRIVATE_NOTE_CANARY|0600000000/
    .test(JSON.stringify(restrictedGet.body)),
    'Agenda-only HTTP response MUST NOT contain names, notes, reason or phone');
  assert.equal(restrictedAppointment.datetime_start, ownerFixture.datetime_start);
  assert.equal(restrictedAppointment.status, ownerFixture.status);
  point('backend-agenda-only-staff', { httpStatus: restrictedGet.status, sameAppointment: firstId, httpIdentityRedacted: true });


  // C07C-11: the separate Frontdesk router must not bypass the same Patients
  // privacy boundary. All requests below use the REAL disposable T2 backend.
  const frontdeskPayload = {
    first_name: 'PRIVATE-FIRST-07C', last_name: 'PRIVATE-LAST-07C',
    phone: '0699990011', appointment_reason: 'PRIVATE-MOTIF-07C',
    notes: 'PRIVATE-NOTES-07C',
    requested_start: new Date(Date.now() + 3*86400000).toISOString(),
    source: 'frontdesk',
  };
  const ownerCreated = await authPOST(ownerToken, '/api/frontdesk/appointment-request', frontdeskPayload, cookies);
  assert.equal(ownerCreated.status, 200, 'Owner may create Frontdesk appointment');
  assert.equal(ownerCreated.body.patient_name, 'PRIVATE-LAST-07C PRIVATE-FIRST-07C');
  assert.equal(ownerCreated.body.phone, frontdeskPayload.phone);
  const frontdeskId = ownerCreated.body.id;
  point('frontdesk-owner-create-preserves-patient-fields', {status: 200});

  const ownerPending = await authGET(ownerToken, '/api/appointments/pending', cookies);
  assert.equal(ownerPending.status, 200);
  const ownerRow = ownerPending.body.find(x => x.id === frontdeskId);
  assert.ok(ownerRow, 'Owner sees synthetic pending Frontdesk appointment');
  assert.equal(ownerRow.patient_name, ownerCreated.body.patient_name);
  assert.equal(ownerRow.motif, frontdeskPayload.appointment_reason);
  point('frontdesk-owner-pending-visible', {status: 200});

  const restrictedPending = await authGET(restrictedToken, '/api/appointments/pending', cookies);
  assert.equal(restrictedPending.status, 200);
  const restrictedRow = restrictedPending.body.find(x => x.id === frontdeskId);
  assert.ok(restrictedRow, 'Agenda-only staff retains anonymous Frontdesk schedule metadata');
  for (const key of ['patient_name', 'phone', 'motif', 'source']) {
    assert.equal(restrictedRow[key], null, 'Restricted Frontdesk must redact '+key);
  }
  assert.equal(restrictedRow.datetime_start, ownerRow.datetime_start);
  assert.ok(!/PRIVATE-FIRST-07C|PRIVATE-LAST-07C|PRIVATE-MOTIF-07C|0699990011|PRIVATE-NOTES-07C/
    .test(JSON.stringify(restrictedPending.body)), 'No Frontdesk personal canary in Agenda-only HTTP');
  point('frontdesk-restricted-pending-redacted', {status: 200, fieldsRedacted: true});

  const blindCreated = await authPOST(restrictedToken, '/api/frontdesk/appointment-request',
    { ...frontdeskPayload, first_name: 'BLIND-07C' }, cookies);
  assert.equal(blindCreated.status, 200, 'Agenda-only user may blind-submit a schedule request');
  for (const key of ['patient_name', 'phone', 'motif', 'source']) {
    assert.equal(blindCreated.body[key], null, 'Blind submission must not echo '+key);
  }
  assert.ok(!JSON.stringify(blindCreated.body).includes('BLIND-07C'));
  point('frontdesk-restricted-create-no-personal-echo', {status: 200});

  const restrictedLetter = await authPOST(restrictedToken,
    '/api/appointments/'+frontdeskId+'/request-confirmation', {}, cookies);
  assert.equal(restrictedLetter.status, 403,
    'Agenda-only actor must not receive a patient-addressed Frontdesk letter');
  const afterForbidden = await authGET(ownerToken, '/api/appointments/pending', cookies);
  assert.ok(afterForbidden.body.some(x => x.id === frontdeskId && x.status === 'EN_ATTENTE_DEMANDE'),
    'Rejected letter must not change appointment status');
  point('frontdesk-restricted-letter-denied-no-mutation', {status: 403});

  const patientDetailGet = await authGET(restrictedToken, '/api/appointments/patient/'+ownerFixture.patient_id, cookies);
  assert.equal(patientDetailGet.status, 403, 'Agenda-only user cannot fetch another patient appointment history');
  point('backend-patient-history-forbidden', { httpStatus: 403 });

  const patientPlanGet = await authGET(restrictedToken,
    '/api/appointments/suggest/'+ownerFixture.patient_id, cookies);
  assert.equal(patientPlanGet.status, 403,
    'Agenda-only staff MUST NOT read treatment-plan-derived appointment suggestions');
  assert.ok(!/implant|couronne|traitement|endodont|T2 COMMAND SYNTHETIC/i.test(
    JSON.stringify(patientPlanGet.body)),
    '403 denial must not disclose treatment-plan details');
  point('backend-treatment-plan-suggestion-forbidden', { httpStatus: 403 });

  // Conflicts are legitimate schedule metadata, never a route to recover a
  // concealed patient's name/notes through a different HTTP error body.
  const restrictedConflict = await authGET(restrictedToken,
    '/api/appointments/check-conflicts?datetime_start='+
      encodeURIComponent(ownerFixture.datetime_start)+
      '&duration_minutes=30&praticien_id='+ownerFixture.praticien_id, cookies);
  assert.ok([200, 409, 422].includes(restrictedConflict.status),
    'Agenda-only schedule availability must not produce an unhandled error');
  assert.ok(!/T2 COMMAND SYNTHETIC|T2_PRIVATE_MOTIF_CANARY|T2_PRIVATE_NOTE_CANARY|0600000000/
    .test(JSON.stringify(restrictedConflict.body)),
    'Conflict response must not disclose synthetic patient identity or free text');
  point('backend-conflict-identity-not-leaked', { httpStatus: restrictedConflict.status });

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
    const otherPatient = await authGET(otherToken, '/api/patients/' + ownerFixture.patient_id, otherCookies);
    assert.ok([403, 404].includes(otherPatient.status),
      'Owner B cannot access owner A patient detail even with a separately enrolled workstation');
    const ownerAgain = await authGET(ownerToken, '/api/patients/' + ownerFixture.patient_id, cookies);
    assert.equal(ownerAgain.status, 200, 'A must still access own patient after B denial');
    assert.equal(ownerAgain.body.id, ownerFixture.patient_id, 'A patient identity intact');
    point('r4-patient-tenant-a-b-a',{A:200,B:otherPatient.status,Aagain:200});
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
        if (/\/api\/(?:appointments|patients|documents)\//.test(req.url()) &&
          !['GET', 'HEAD', 'OPTIONS'].includes(req.method())) {
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
      // Genuine Dashboard: reversible local Iconic style never changes the active clinic theme.
      await page.locator('[data-testid="r4-real-signature-preview"]').waitFor({state:'visible',timeout:20000});
      const originalTheme = await page.evaluate(() => document.documentElement.dataset.theme || '');
      assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
      await page.getByRole('button',{name:'Signature Iconic'}).click();
      assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
      await capture(page, actor+'-r4-dashboard-iconic');
      await page.getByRole('button',{name:'Signature Core'}).click();
      assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme || ''),originalTheme);
      point('r4-reversible-iconic-real-dashboard-'+actor,{route:'/dashboard',initial:'core',after:'core',themeUnchanged:true});
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
        await page.locator('[data-testid="r4-command-four-surfaces"]').waitFor({state:'visible',timeout:25000});
        assert.equal(await page.getByRole('navigation',{name:'Quatre surfaces Command'}).getByRole('button').count(),4);
        await page.locator('[data-testid="command-count"]').waitFor({state:'visible',timeout:25000});
        assert.equal(Number((await page.locator('[data-testid="command-count"]').innerText()).trim()),commandData.length);
        await page.getByRole('navigation',{name:'Quatre surfaces Command'})
          .getByRole('button',{name:'Agenda'}).click();
        await page.locator('tbody tr').first().waitFor({ state: 'visible', timeout: 25000 });
        const line = (await page.locator('tbody tr').allTextContents()).join('\n');
        assert.ok(line.includes('09:15'), 'Actual Cabinet wall clock time must render');
        assert.ok(line.includes(ownerFixture.status), 'Same actual appointment status must render');
        if (expectName) assert.ok(line.includes('T2 COMMAND SYNTHETIC'), 'Owner identity is permitted');
        else assert.ok(!line.includes('T2 COMMAND SYNTHETIC'), 'Agenda-only staff patient identity redacted');
        assert.equal(await page.getByRole('button', { name: 'Actualiser les rendez-vous' }).count(), 1);
        assert.equal(await page.locator('[data-ux1-c-crownbot-floating]').count(), 0,
          'CrownBot floating control must not overlay the 07-C Command lab');
        await capture(page, actor + '-02-command-after');
        // Four genuine Command surfaces. Patients-only views never fetch for agenda-only staff.
        if (actor === 'owner') {
          const nav = page.getByRole('navigation',{name:'Quatre surfaces Command'});
          await nav.getByRole('button',{name:'Dossier patient'}).click();
          await page.getByLabel('Sélectionner un dossier autorisé').waitFor({state:'visible',timeout:30000});
          await page.getByLabel('Sélectionner un dossier autorisé')
            .selectOption(String(ownerFixture.patient_id));
          await page.locator('[data-testid="r4-verified-dossier"]').waitFor({state:'visible',timeout:30000});
          assert.ok((await page.locator('[data-testid="r4-verified-dossier"]').innerText()).includes('T2-0001'),
            'Dossier must display real selected patient identifier');
          await page.locator('[data-testid="multiview-bilan-readonly"]').waitFor({state:'visible',timeout:30000});
          await capture(page,'owner-r4-dossier-real');
          await nav.getByRole('button',{name:'Imagerie'}).click();
          await page.locator('[data-testid="r4-verified-imagerie"]').waitFor({state:'visible',timeout:30000});
          await page.locator('[data-testid="patient-media-timeline"]').waitFor({state:'visible',timeout:30000});
          await capture(page,'owner-r4-imagerie-real');
          point('r4-four-real-surfaces-owner',{dashboard:true,agenda:true,dossierId:ownerFixture.patient_id,imagerieReadOnly:true});
          // Confirm the SAME Iconic button, card and border inherit active Cabinet theme
          // tokens. Simulate the existing applyTheme data-theme mechanism in this isolated
          // browser only; restore all inline overrides and attributes, no settings writes.
          await page.getByRole('button', {name:'Signature Iconic'}).click();
          const themeSamples = await page.evaluate(() => {
            const nodes = [document.documentElement, document.body];
            const saved = nodes.map(el => ({
              theme: el.getAttribute('data-theme'),
              primary: el.style.getPropertyValue('--primary'),
              priority: el.style.getPropertyPriority('--primary'),
            }));
            const button = document.querySelector('.dc07-r4-signature-controls button[aria-pressed="true"]');
            const controls = document.querySelector('.dc07-r4-signature-controls');
            if (!(button instanceof HTMLElement) || !(controls instanceof HTMLElement)) {
              throw new Error('Iconic controls must be mounted on the real Cabinet');
            }
            const sample = {};
            try {
              for (const theme of ['emerald', 'prestige']) {
                for (const el of nodes) {
                  el.setAttribute('data-theme', theme);
                  el.style.removeProperty('--primary');
                }
                sample[theme] = {
                  buttonColor: getComputedStyle(button).color,
                  cardColor: getComputedStyle(controls).backgroundColor,
                  borderColor: getComputedStyle(controls).borderTopColor,
                };
              }
            } finally {
              for (let i = 0; i < nodes.length; i++) {
                if (saved[i].theme === null) nodes[i].removeAttribute('data-theme');
                else nodes[i].setAttribute('data-theme', saved[i].theme);
                if (saved[i].primary) {
                  nodes[i].style.setProperty('--primary', saved[i].primary, saved[i].priority);
                } else nodes[i].style.removeProperty('--primary');
              }
            }
            return sample;
          });
          await page.getByRole('button', {name:'Signature Core'}).click();
          for (const key of ['buttonColor', 'cardColor', 'borderColor']) {
            assert.notEqual(themeSamples.emerald[key], themeSamples.prestige[key],
              'R4 ' + key + ' MUST inherit selected theme rather than hardcoded colors');
          }
          point('r4-live-active-theme-token-inheritance', themeSamples);
          // Switch Iconic/Core on Command's true authenticated components at multiple widths.
          for (const width of [1280,1920,2560]) {
            await page.setViewportSize({width,height:900});
            await page.getByRole('button',{name:'Signature Iconic'}).click();
            assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
            await capture(page,'owner-r4-iconic-command-'+width);
            await page.getByRole('button',{name:'Signature Core'}).click();
            assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
          }
          await page.setViewportSize({width:1440,height:900});
        } else {
          const nav = page.getByRole('navigation',{name:'Quatre surfaces Command'});
          for (const surface of ['Dossier patient','Imagerie']) {
            await nav.getByRole('button',{name:surface}).click();
            await page.locator('[data-testid="r4-patient-denied"]').waitFor({state:'visible',timeout:8000});
            assert.equal(await page.getByLabel('Sélectionner un dossier autorisé').count(),0);
          }
          point('r4-no-patient-or-media-mount-agenda-only',{refused:['dossier','imagerie']});
        }
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
          // Validate Iconic on THREE other true Signature routes, not merely
          // Command tabs. Navigate the actual protected React Router workflow.
          for (const target of [
            {label:'agenda',url:'/agenda'},
            {label:'dossier',url:'/patients/'+ownerFixture.patient_id+'?tab=tracking'},
            {label:'imagerie',url:'/patients/'+ownerFixture.patient_id+'?tab=radiology&radioTab=media'},
          ]) {
            await page.goto(uiBase+target.url,{waitUntil:'domcontentloaded',timeout:90000});
            await page.locator('[data-testid="r4-real-signature-preview"]').waitFor({state:'visible',timeout:40000});
            assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
            if (target.label === 'imagerie') {
              await page.locator('[data-testid="patient-media-timeline"]').waitFor({state:'visible',timeout:40000});
            } else if (target.label === 'dossier') {
              await page.getByText('T2-0001',{exact:false}).first().waitFor({state:'visible',timeout:40000});
            }
            await capture(page,'owner-r4-signature-'+target.label+'-core');
            await page.getByRole('button',{name:'Signature Iconic'}).click();
            assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
            await capture(page,'owner-r4-signature-'+target.label+'-iconic');
            await page.getByRole('button',{name:'Signature Core'}).click();
            assert.equal(await page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
            point('r4-signature-real-'+target.label,{core:true,iconic:true,rollback:true});
          }
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
console.log('LOT07_R4_REAL_CABINET_FUE_G', JSON.stringify({
  sha, pass: report.pass, checks: report.checks.map(x => x.name), failures: report.failures,
}));
if (!report.pass) process.exitCode = 1;
