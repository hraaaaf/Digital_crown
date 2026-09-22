import fs from 'node:fs';
import path from 'node:path';
import { chromium, webkit, request } from 'playwright';

const apiUrl = process.env.PC08_API_URL || 'http://127.0.0.1:8005';
const appUrl = process.env.PC08_APP_URL || 'http://127.0.0.1:5173';
const outDir = path.resolve(process.env.PC08_RUNTIME_AFTER_DIR || '../artifacts/pc08-runtime-after');
const user = process.env.T2_USER;
const pass = process.env.T2_PASSWORD;
const productHead = process.env.PRODUCT_HEAD || null;
if (!user || !pass) throw new Error('Isolated staff credentials unavailable');

fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const api = await request.newContext({ baseURL: apiUrl });
const login = await api.post('/api/auth/login', { form: { username: user, password: pass } });
if (!login.ok()) throw new Error(`staff login ${login.status()}`);
const tokens = await login.json();
const authHeaders = { Authorization: `Bearer ${tokens.access_token}` };

const patientsResponse = await api.get('/api/patients', { headers: authHeaders });
if (!patientsResponse.ok()) throw new Error(`patients ${patientsResponse.status()}`);
const patients = await patientsResponse.json();
const patient = patients.find(item => item.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('No isolated seeded patient');

async function invitation(relationshipType) {
  const response = await api.post(
    `/api/patient-companion/admin/patients/${patient.id}/local-invitation`,
    {
      headers: authHeaders,
      data: { relationship_type: relationshipType, expires_in_minutes: 60 },
    },
  );
  if (!response.ok()) throw new Error(`invitation ${relationshipType} ${response.status()}`);
  const body = await response.json();
  if (!body.manual_code) throw new Error('Invitation missing manual code');
  return body.manual_code;
}

async function pairPatient(browserType, relationshipType, viewport) {
  const browser = await browserType.launch({ headless: true });
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });

  const code = await invitation(relationshipType);
  await page.goto(`${appUrl}/companion`, { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Code manuel').fill(code);
  await page.getByText('Appairer avec le code', { exact: true }).click();
  await page.locator('[data-pc00-cabinet-link]').waitFor({ state: 'visible', timeout: 30000 });

  const transportWarning = page.getByText('Transport sécurisé non initialisé pour cet accès.', { exact: true });
  if (await transportWarning.count()) throw new Error(`remote transport missing for ${relationshipType}`);

  await page.locator('[data-pc00-cabinet-link]').click();
  await page.getByText('Cabinet joignable ✓', { exact: true }).waitFor({ timeout: 30000 });
  const section = page.locator('[data-pc08-secure-messaging]');
  await section.waitFor({ state: 'visible', timeout: 30000 });
  await page.getByRole('button', { name: 'Ouvrir la conversation' }).click();

  return { browser, context, page, pageErrors, consoleErrors, relationshipType };
}

const self = await pairPatient(chromium, 'SELF', { width: 390, height: 844 });
const selfBody = 'Suivi sécurisé patient — ' + 'A'.repeat(700);
await self.page.getByPlaceholder('Écrire au cabinet…').fill(selfBody);
const selfSend = self.page.getByRole('button', { name: 'Envoyer' });
await selfSend.waitFor({ state: 'visible' });
await selfSend.click();
await self.page.getByText('Reçu par le cabinet', { exact: true }).waitFor({ timeout: 30000 });

const parent = await pairPatient(webkit, 'PARENT', { width: 390, height: 844 });
const parentBody = 'Message parent via WebKit';
await parent.page.getByPlaceholder('Écrire au cabinet…').fill(parentBody);
await parent.page.getByRole('button', { name: 'Envoyer' }).click();
await parent.page.getByText('Reçu par le cabinet', { exact: true }).waitFor({ timeout: 30000 });

const staffBrowser = await chromium.launch({ headless: true });
const staffContext = await staffBrowser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
const staffPage = await staffContext.newPage();
const staffPageErrors = [];
const staffConsoleErrors = [];
staffPage.on('pageerror', error => staffPageErrors.push(String(error)));
staffPage.on('console', message => {
  if (message.type() === 'error') staffConsoleErrors.push(message.text());
});
await staffPage.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });

const staffResponse = await staffPage.goto(
  `${appUrl}/patients/${patient.id}?tab=companion`,
  { waitUntil: 'networkidle', timeout: 90000 },
);
if (staffResponse?.status() !== 200) throw new Error(`staff page ${staffResponse?.status()}`);
const staffPanel = staffPage.locator('[data-pc08-staff-messaging]');
await staffPanel.waitFor({ state: 'visible', timeout: 30000 });

const selector = staffPage.getByLabel('Accès destinataire');
await selector.waitFor({ state: 'visible', timeout: 30000 });
const optionTexts = await selector.locator('option').allTextContents();
if (!optionTexts.includes('Patient') || !optionTexts.includes('Parent')) {
  throw new Error(`multi-access selector incomplete: ${JSON.stringify(optionTexts)}`);
}
const staffReadResponsePromise = staffPage.waitForResponse(
  response => response.url().includes('/messages/read') && response.request().method() === 'POST',
  { timeout: 30000 },
);
await selector.selectOption({ label: 'Patient' });
await staffPage.getByText(selfBody, { exact: true }).waitFor({ timeout: 30000 });
const staffReadResponse = await staffReadResponsePromise;
if (!staffReadResponse.ok()) {
  throw new Error(`staff read mutation failed: ${staffReadResponse.status()}`);
}
const staffMessageBubble = staffPage.getByText(selfBody, { exact: true }).locator('..');
await staffMessageBubble.getByText(/· Lu$/, { exact: false }).waitFor({ timeout: 30000 });

const staffReply = 'Réponse sécurisée du cabinet — votre message a bien été consulté.';
await staffPage.getByPlaceholder('Écrire au patient…').fill(staffReply);
await staffPage.getByRole('button', { name: 'Envoyer' }).click();
await staffPage.getByText(staffReply, { exact: true }).waitFor({ timeout: 30000 });
const staffReplyBubble = staffPage.getByText(staffReply, { exact: true }).locator('..');
await staffReplyBubble.getByText(/· Envoyé depuis le cabinet$/, { exact: false }).waitFor({ timeout: 30000 });

const staffCaptures = [];
for (const viewport of [
  { width: 390, height: 844, label: '390x844' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
]) {
  await staffPage.setViewportSize({ width: viewport.width, height: viewport.height });
  await staffPanel.scrollIntoViewIfNeeded();
  const overflow = await staffPage.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (overflow) throw new Error(`staff overflow ${viewport.label}`);
  const shot = `staff-after-${viewport.label}.png`;
  await staffPage.screenshot({ path: path.join(outDir, shot), fullPage: false });
  staffCaptures.push({ viewport, shot, overflow });
}

await self.page.getByRole('button', { name: 'Synchroniser les messages' }).click();
await self.page.getByText(staffReply, { exact: true }).waitFor({ timeout: 30000 });
const selfSection = self.page.locator('[data-pc08-secure-messaging]');
await selfSection.getByText('Lu par le cabinet', { exact: true }).waitFor({ timeout: 30000 });
await selfSection.getByText('Lu', { exact: true }).waitFor({ timeout: 30000 });

await self.page.route(
  '**/api/patient-companion/contexts/*/messages/remote-command',
  route => route.fulfill({
    status: 503,
    contentType: 'application/json',
    body: JSON.stringify({ detail: 'PC-08 isolated offline fixture' }),
  }),
);
const pendingBody = 'Message hors connexion — ' + 'Z'.repeat(650);
await selfSection.getByPlaceholder('Écrire au cabinet…').fill(pendingBody);
await selfSection.getByRole('button', { name: 'Envoyer' }).click();
await selfSection.getByText('Enregistré localement · non envoyé', { exact: true }).waitFor({ timeout: 30000 });

const patientCaptures = [];
for (const viewport of [
  { width: 360, height: 800, label: '360x800' },
  { width: 390, height: 844, label: '390x844' },
]) {
  await self.page.setViewportSize({ width: viewport.width, height: viewport.height });
  const section = self.page.locator('[data-pc08-secure-messaging]');
  await section.scrollIntoViewIfNeeded();
  const overflow = await self.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (overflow) throw new Error(`chromium patient overflow ${viewport.label}`);
  const shot = `chromium-patient-after-${viewport.label}.png`;
  await self.page.screenshot({ path: path.join(outDir, shot), fullPage: false });
  patientCaptures.push({ browser: 'chromium', viewport, shot, overflow });
}

const webkitCaptures = [];
for (const viewport of [
  { width: 360, height: 800, label: '360x800' },
  { width: 390, height: 844, label: '390x844' },
]) {
  await parent.page.setViewportSize({ width: viewport.width, height: viewport.height });
  const section = parent.page.locator('[data-pc08-secure-messaging]');
  await section.scrollIntoViewIfNeeded();
  const overflow = await parent.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (overflow) throw new Error(`webkit patient overflow ${viewport.label}`);
  const shot = `webkit-patient-after-${viewport.label}.png`;
  await parent.page.screenshot({ path: path.join(outDir, shot), fullPage: false });
  webkitCaptures.push({ browser: 'webkit', viewport, shot, overflow });
}

const expectedOfflineConsoleErrors = self.consoleErrors.filter(error => error.includes('503 (Service Unavailable)') && error.includes('Failed to load resource'));
const unexpectedSelfConsoleErrors = self.consoleErrors.filter(error => !error.includes('503 (Service Unavailable)'));
if (expectedOfflineConsoleErrors.length !== 1) {
  throw new Error(`chromium patient expected exactly one isolated offline 503, got ${expectedOfflineConsoleErrors.length}`);
}
if (self.pageErrors.length || unexpectedSelfConsoleErrors.length) {
  throw new Error(`chromium patient runtime errors: ${JSON.stringify({ pageErrors: self.pageErrors, consoleErrors: unexpectedSelfConsoleErrors })}`);
}
if (parent.pageErrors.length || parent.consoleErrors.length) {
  throw new Error(`webkit patient runtime errors: ${JSON.stringify({ pageErrors: parent.pageErrors, consoleErrors: parent.consoleErrors })}`);
}
if (staffPageErrors.length || staffConsoleErrors.length) {
  throw new Error(`staff runtime errors: ${JSON.stringify({ pageErrors: staffPageErrors, consoleErrors: staffConsoleErrors })}`);
}

const report = {
  productHead,
  patientId: patient.id,
  evidence: {
    multiAccess: optionTexts,
    patientCanonicalReceived: true,
    patientStaffReadObserved: true,
    cabinetReplyObserved: true,
    patientReplyReadObserved: true,
    offlinePendingObserved: true,
  },
  patientCaptures: [...patientCaptures, ...webkitCaptures],
  staffCaptures,
  runtimeErrors: {
    chromiumPatient: { pageErrors: self.pageErrors, consoleErrors: self.consoleErrors },
    webkitPatient: { pageErrors: parent.pageErrors, consoleErrors: parent.consoleErrors },
    staff: { pageErrors: staffPageErrors, consoleErrors: staffConsoleErrors },
  },
};
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));

await staffContext.close();
await staffBrowser.close();
await self.context.close();
await self.browser.close();
await parent.context.close();
await parent.browser.close();
await api.dispose();
