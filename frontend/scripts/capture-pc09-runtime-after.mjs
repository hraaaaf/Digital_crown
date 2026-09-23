import fs from 'node:fs';
import path from 'node:path';
import { chromium, webkit, request } from 'playwright';

const apiUrl = process.env.PC09_API_URL || 'http://127.0.0.1:8005';
const appUrl = process.env.PC09_APP_URL || 'http://127.0.0.1:5173';
const outDir = path.resolve(process.env.PC09_RUNTIME_AFTER_DIR || '../artifacts/pc09-runtime-after');
const user = process.env.T2_USER;
const pass = process.env.T2_PASSWORD;
const productHead = process.env.PRODUCT_HEAD || null;
if (!user || !pass) throw new Error('Isolated staff credentials unavailable');

fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const api = await request.newContext({ baseURL: apiUrl });
const login = await api.post('/api/auth/login', { form: { username: user, password: pass } });
if (!login.ok()) throw new Error('staff login ' + login.status());
const tokens = await login.json();
const authHeaders = { Authorization: 'Bearer ' + tokens.access_token };

const patientsResponse = await api.get('/api/patients', { headers: authHeaders });
if (!patientsResponse.ok()) throw new Error('patients ' + patientsResponse.status());
const patients = await patientsResponse.json();
const patient = patients.find(item => item.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('No isolated seeded patient');

async function invitation(relationshipType) {
  const response = await api.post(
    '/api/patient-companion/admin/patients/' + patient.id + '/local-invitation',
    { headers: authHeaders, data: { relationship_type: relationshipType, expires_in_minutes: 60 } },
  );
  if (!response.ok()) throw new Error('invitation ' + relationshipType + ' ' + response.status());
  const body = await response.json();
  if (!body.manual_code) throw new Error('Invitation missing manual code');
  return body.manual_code;
}

async function pair(browserType, relationshipType, viewport) {
  const browser = await browserType.launch({ headless: true });
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });

  const code = await invitation(relationshipType);
  await page.goto(appUrl + '/companion', { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Code manuel').fill(code);
  await page.getByText('Appairer avec le code', { exact: true }).click();
  await page.locator('[data-pc00-cabinet-link]').waitFor({ state: 'visible', timeout: 30000 });
  await page.locator('[data-pc00-cabinet-link]').click();
  await page.getByText('Cabinet joignable ✓', { exact: true }).waitFor({ timeout: 30000 });

  const panel = page.locator('[data-pc09-patient]');
  await panel.waitFor({ state: 'visible', timeout: 30000 });
  return { browser, context, page, panel, pageErrors, consoleErrors, relationshipType };
}

const chromiumPatient = await pair(chromium, 'SELF', { width: 390, height: 844 });
const webkitPatient = await pair(webkit, 'PARENT', { width: 390, height: 844 });

const staffBrowser = await chromium.launch({ headless: true });
const staffContext = await staffBrowser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
const staffPage = await staffContext.newPage();
const staffPageErrors = [];
const staffConsoleErrors = [];
staffPage.on('pageerror', error => staffPageErrors.push(String(error)));
staffPage.on('console', message => { if (message.type() === 'error') staffConsoleErrors.push(message.text()); });
await staffPage.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });

const staffResponse = await staffPage.goto(
  appUrl + '/patients/' + patient.id + '?tab=companion',
  { waitUntil: 'networkidle', timeout: 90000 },
);
if (staffResponse?.status() !== 200) throw new Error('staff page ' + staffResponse?.status());
const staffPanel = staffPage.locator('[data-pc09-staff]');
await staffPanel.waitFor({ state: 'visible', timeout: 30000 });

const teleResponse = await api.get(
  '/api/patient-companion/admin/patients/' + patient.id + '/teleconsultations',
  { headers: authHeaders },
);
if (!teleResponse.ok()) throw new Error('teleconsult list ' + teleResponse.status());
const tele = await teleResponse.json();
const accesses = tele.accesses || [];
if (accesses.length < 2) throw new Error('expected SELF + PARENT teleconsult accesses');
const selfAccess = accesses.find(item => item.relationship_type === 'SELF');
const parentAccess = accesses.find(item => item.relationship_type === 'PARENT');
if (!selfAccess || !parentAccess) throw new Error('teleconsult access labels incomplete');

for (const access of [selfAccess, parentAccess]) {
  const response = await api.post(
    '/api/patient-companion/admin/patients/' + patient.id + '/teleconsultations',
    { headers: authHeaders, data: { access_id: access.access_id, ttl_minutes: 60 } },
  );
  if (!response.ok()) throw new Error('create teleconsult ' + access.relationship_type + ' ' + response.status());
}

for (const target of [chromiumPatient, webkitPatient]) {
  await target.page.getByRole('button', { name: 'Actualiser' }).click();
  await target.panel.getByText('Prête à rejoindre', { exact: true }).waitFor({ timeout: 30000 });
  await target.panel.getByRole('button', { name: 'Accepter et rejoindre' }).waitFor({ state: 'visible' });
}

const patientCaptures = [];
for (const viewport of [
  { width: 360, height: 800, label: '360x800' },
  { width: 390, height: 844, label: '390x844' },
]) {
  await chromiumPatient.page.setViewportSize({ width: viewport.width, height: viewport.height });
  await chromiumPatient.panel.scrollIntoViewIfNeeded();
  const overflow = await chromiumPatient.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (overflow) throw new Error('chromium patient overflow ' + viewport.label);
  const shot = 'chromium-patient-pc09-' + viewport.label + '.png';
  await chromiumPatient.page.screenshot({ path: path.join(outDir, shot), fullPage: false });
  patientCaptures.push({ browser: 'chromium', viewport, shot, overflow });
}

await webkitPatient.page.setViewportSize({ width: 390, height: 844 });
await webkitPatient.panel.scrollIntoViewIfNeeded();
const webkitOverflow = await webkitPatient.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
if (webkitOverflow) throw new Error('webkit patient overflow 390x844');
await webkitPatient.page.screenshot({ path: path.join(outDir, 'webkit-patient-pc09-390x844.png'), fullPage: false });
patientCaptures.push({ browser: 'webkit', viewport: { width: 390, height: 844, label: '390x844' }, shot: 'webkit-patient-pc09-390x844.png', overflow: webkitOverflow });

const staffCaptures = [];
for (const viewport of [
  { width: 390, height: 844, label: '390x844' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
]) {
  await staffPage.setViewportSize({ width: viewport.width, height: viewport.height });
  if (viewport.width >= 1024) {
    await staffPage.evaluate(() => {
      const appScroller = document.querySelector('main.overflow-y-auto');
      const panel = document.querySelector('[data-pc09-staff]');
      const stickyHeader = document.querySelector('header.lg\\:sticky');
      if (!(appScroller instanceof HTMLElement) || !(panel instanceof HTMLElement)) throw new Error('PC-09 geometry target missing');
      const panelRect = panel.getBoundingClientRect();
      const headerRect = stickyHeader?.getBoundingClientRect();
      const desiredTop = headerRect ? headerRect.bottom + 16 : 16;
      const targetTop = appScroller.scrollTop + (panelRect.top - desiredTop);
      appScroller.scrollTo({ top: Math.max(0, targetTop), left: 0, behavior: 'instant' });
    });
  } else {
    await staffPanel.evaluate(element => element.scrollIntoView({ block: 'center', inline: 'nearest' }));
  }
  const geometry = await staffPage.evaluate(() => {
    const panel = document.querySelector('[data-pc09-staff]');
    const stickyHeader = document.querySelector('header.lg\\:sticky');
    if (!panel) return { visible: false, overlappedByHeader: false };
    const panelRect = panel.getBoundingClientRect();
    const headerRect = stickyHeader?.getBoundingClientRect();
    return {
      visible: panelRect.bottom > 0 && panelRect.top < window.innerHeight,
      overlappedByHeader: Boolean(headerRect && panelRect.top < headerRect.bottom && panelRect.bottom > headerRect.top),
    };
  });
  if (!geometry.visible || geometry.overlappedByHeader) throw new Error('staff geometry invalid ' + viewport.label + ': ' + JSON.stringify(geometry));
  const overflow = await staffPage.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (overflow) throw new Error('staff overflow ' + viewport.label);
  const shot = 'staff-pc09-' + viewport.label + '.png';
  await staffPage.screenshot({ path: path.join(outDir, shot), fullPage: false });
  staffCaptures.push({ viewport, shot, overflow });
}

const allErrors = {
  chromiumPatient: { pageErrors: chromiumPatient.pageErrors, consoleErrors: chromiumPatient.consoleErrors },
  webkitPatient: { pageErrors: webkitPatient.pageErrors, consoleErrors: webkitPatient.consoleErrors },
  staff: { pageErrors: staffPageErrors, consoleErrors: staffConsoleErrors },
};
for (const [key, value] of Object.entries(allErrors)) {
  if (value.pageErrors.length || value.consoleErrors.length) throw new Error(key + ' runtime errors: ' + JSON.stringify(value));
}

const report = {
  productHead,
  patientId: patient.id,
  evidence: {
    statesCaptured: ['AVAILABLE_TO_JOIN'],
    mediaConnectionClaimed: false,
    note: 'Visual evidence intentionally does not simulate a network-connected call. Real connection truth is covered by deterministic contracts; remote TURN E2E remains a separate infrastructure gate.',
    accessRelationships: accesses.map(item => item.relationship_type),
  },
  patientCaptures,
  staffCaptures,
  runtimeErrors: allErrors,
};
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));

await staffContext.close();
await staffBrowser.close();
await chromiumPatient.context.close();
await chromiumPatient.browser.close();
await webkitPatient.context.close();
await webkitPatient.browser.close();
await api.dispose();
