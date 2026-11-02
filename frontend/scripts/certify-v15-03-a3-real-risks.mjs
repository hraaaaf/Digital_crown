/**
 * A3: extra real negative checks AFTER the existing G03.21 positive Chromium run.
 * Genuine localhost HTTP only: no page.route(), fetch interception or mocked API.
 * All accounts, workstations and patients are invented in a disposable test database.
 */
import { chromium, request } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const HEAD = process.env.EVALUATED_SHA;
if (process.env.ENVIRONMENT !== 'test'
    || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.T2_STATION_FUE !== '1'
    || process.env.DATABASE_URL !== 'sqlite:///./t2-runtime-cert.db'
    || !HEAD || !process.env.T2_PASSWORD) {
  throw new Error('A3 FAIL CLOSED: exact HEAD, disposable T2 DB, credentials and isolation flags required');
}
const baseURL = 'http://127.0.0.1:8005';
const uiURL = 'http://127.0.0.1:5173';
const out = path.resolve('artifacts/v15-03-a3-real');
await fs.mkdir(out, { recursive: true });
const fixture = JSON.parse(await fs.readFile(path.join(out, 'seed.json'), 'utf8'));
const baseFixture = JSON.parse(
  await fs.readFile(path.resolve('artifacts/v15-03-real-integration/seed.json'), 'utf8')
).patients;
const evidence = { head: HEAD, scope: 'Synthetic-only localhost Chromium/FastAPI disposable SQL, no HTTP mocking',
  scenarios: {}, http: [], screenshots: [] };
const expect = (ok, label) => { if (!ok) throw new Error(label); };
const check = async (response, label, codes) => {
  evidence.http.push({ label, status: response.status() });
  expect(codes.includes(response.status()), label + ': unexpected HTTP ' + response.status());
  return response;
};
const mark = (name, condition) => {
  expect(condition, 'A3 scenario FAIL: ' + name);
  evidence.scenarios[name] = true;
};
const password = process.env.T2_PASSWORD;
const pin = '2468'; // Disposable synthetic test-only PIN from G03.21 lab.
const allApis = [];
let browser;

async function login(email, createWorkstation = false, setPin = false) {
  const api = await request.newContext({ baseURL, timeout: 30000 });
  allApis.push(api);
  const response = await check(await api.post('/api/auth/login', {
    form: { username: email, password }
  }), 'login synthetic actor ' + email, [200]);
  const tokens = await response.json();
  const headers = { Authorization: 'Bearer ' + tokens.access_token };
  let workstationId = null;
  if (createWorkstation) {
    const enroll = await check(await api.post('/api/workstation/enroll', {
      headers, data: { accountPassword: password }
    }), 'enroll synthetic workstation ' + email, [200]);
    workstationId = (await enroll.json()).workstationId;
    expect(Boolean(workstationId), 'workstation enrollment not persisted');
    if (setPin) await check(await api.post('/api/workstation/owner-pin', {
      headers, data: { accountPassword: password, newPin: pin }
    }), 'foreign owner PIN', [200]);
    await check(await api.post('/api/workstation/mode', {
      headers, data: { mode: 'station', ownerPin: pin }
    }), 'station mode ' + email, [200]);
  }
  return { api, headers, tokens, workstationId };
}

async function wallPageFor(actor, label) {
  const ctx = await browser.newContext({
    storageState: await actor.api.storageState(),
    viewport: { width: 1280, height: 900 },
    colorScheme: 'light',
  });
  const page = await ctx.newPage();
  await page.addInitScript(value => {
    localStorage.setItem('token', value.access);
    localStorage.setItem('refresh_token', value.refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: actor.tokens.access_token, refresh: actor.tokens.refresh_token });
  page.on('pageerror', error => { evidence.http.push({ label: label + ' pageerror', error: error.name }); });
  await page.goto(uiURL + '/station/wall', { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.locator('[data-workstation-experience="station-wall"]').waitFor({ state: 'visible', timeout: 45000 });
  return { page, ctx };
}
async function screenshot(page, filename) {
  await page.screenshot({ path: path.join(out, filename), animations: 'disabled', fullPage: true });
  evidence.screenshots.push(filename);
}

try {
  browser = await chromium.launch({ headless: true });

  // Prepare the public Wall immediately, before the 20-second prior call can expire.
  const wallForExpiry = await login(process.env.T2_USER, true);
  const expiry = await wallPageFor(wallForExpiry, 'expiry');
  await expiry.page.locator('[data-wall-state="calling"]').waitFor({ state: 'visible', timeout: 16000 });
  await expiry.page.getByText('N° 308').waitFor({ state: 'visible', timeout: 8000 });
  await screenshot(expiry.page, 'a3-public-call-before.png');

  const primary = await login(process.env.T2_USER);
  const foreign = await login('a3-other-owner@cabinet.ma', true, true);
  const restricted = await login('a3-no-agenda@cabinet.ma');
  const anonymous = await request.newContext({ baseURL, timeout: 30000 });
  allApis.push(anonymous);

  // Distinct tenant has its own genuine waiting patient (#901), never #307/308.
  const otherFeed = await check(await foreign.api.get('/api/workstation/wall-display', {
    headers: foreign.headers
  }), 'foreign wall read', [200]);
  const otherData = await otherFeed.json();
  mark('crossTenantWallIsolated', otherData.waitingCount === 1
    && otherData.entries.some(item => item.ticketNumber === 901)
    && !otherData.entries.some(item => [307, 308].includes(item.ticketNumber)));

  await check(await foreign.api.post(
    '/api/workstation/wall-display/appointments/' + baseFixture.single.appointmentIds[0] + '/call',
    { headers: foreign.headers, data: { ticketNumber: 307 } }
  ), 'cross-tenant foreign call', [404]);
  await check(await primary.api.post(
    '/api/workstation/wall-display/appointments/' + fixture.foreignAppointmentId + '/call',
    { headers: primary.headers, data: { ticketNumber: 901 } }
  ), 'cross-tenant primary call', [404]);
  mark('crossTenantCallDenied', true);

  await check(await restricted.api.get('/api/workstation/staff-assistance', {
    headers: restricted.headers
  }), 'no-agenda restricted receptionist feed', [403]);
  mark('restrictedFeedDenied', true);
  await check(await restricted.api.post(
    '/api/workstation/wall-display/appointments/' + baseFixture.single.appointmentIds[0] + '/call',
    { headers: restricted.headers, data: { ticketNumber: 307 } }
  ), 'no-agenda restricted receptionist call', [403]);
  mark('restrictedCallDenied', true);
  await check(await anonymous.post(
    '/api/workstation/wall-display/appointments/' + baseFixture.single.appointmentIds[0] + '/call',
    { data: { ticketNumber: 307 } }
  ), 'anonymous call', [401]);
  mark('anonymousCallDenied', true);

  // Real browser clock and poll; after call expiry no public caller is retained.
  await expiry.page.locator('[data-wall-state="waiting"]').waitFor({ state: 'visible', timeout: 35000 });
  expect(await expiry.page.getByText('N° 308').count() === 0, 'expired Wall still shows last call');
  await screenshot(expiry.page, 'a3-public-call-expired-after.png');
  mark('callExpired', true);

  // The owner revokes ONLY the newly-enrolled isolated Wall, not the earlier base actors.
  const revoked = await login(process.env.T2_USER);
  await check(await revoked.api.post(
    '/api/workstation/' + wallForExpiry.workstationId + '/revoke',
    { headers: revoked.headers, data: { ownerPin: pin } }
  ), 'owner Wall revoke', [200]);
  await check(await wallForExpiry.api.get('/api/workstation/wall-display', {
    headers: wallForExpiry.headers
  }), 'revoked Wall access', [423]);
  mark('revokeDenied', true);
  await expiry.page.locator('[data-wall-state="unavailable"]').waitFor({ state: 'visible', timeout: 15000 });
  expect(!(await expiry.page.locator('main').innerText()).includes('OTHER-CABINET-ONLY'),
    'revoked Wall leaks other-tenant identity');
  await screenshot(expiry.page, 'a3-revoked-wall-after.png');
  mark('revokedWallUnavailable', true);

  // Independent active Wall: actually stop the test FastAPI process, no HTTP mocking.
  const outageWall = await login(process.env.T2_USER, true);
  const outage = await wallPageFor(outageWall, 'outage');
  await outage.page.locator('[data-wall-state="waiting"]').waitFor({ state: 'visible', timeout: 12000 });
  const serverPid = Number(process.env.A3_LOCAL_BACKEND_PID);
  expect(Number.isSafeInteger(serverPid) && serverPid > 1,
    'Missing dedicated local backend PID: cannot assert a real outage');
  process.kill(serverPid, 'SIGTERM');
  await outage.page.locator('[data-wall-state="unavailable"]').waitFor({ state: 'visible', timeout: 16000 });
  const publicText = await outage.page.locator('main').innerText();
  expect(!publicText.includes('OTHER-CABINET-ONLY')
    && !publicText.includes('STATION-FICTIF')
    && !publicText.includes('N° 308'), 'outage leaked old public identity or call');
  await screenshot(outage.page, 'a3-backend-outage-after.png');
  mark('outageWallUnavailable', true);

  await outage.ctx.close();
  await expiry.ctx.close();
  expect(!evidence.http.some(item => item.error), 'real browser JavaScript error during A3');
  console.log('A3_REAL_BROWSER_NEGATIVE_PASS ' + JSON.stringify(evidence.scenarios));
} finally {
  if (browser) await browser.close();
  await Promise.allSettled(allApis.map(api => api.dispose()));
  await fs.writeFile(path.join(out, 'evidence-after.json'), JSON.stringify(evidence, null, 2));
}
