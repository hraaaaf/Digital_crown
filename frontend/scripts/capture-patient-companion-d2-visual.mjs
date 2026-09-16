import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const phase = String(process.env.D2_PHASE || '').toUpperCase();
if (!['BEFORE', 'AFTER'].includes(phase)) throw new Error(`Invalid D2_PHASE: ${phase}`);

const productHead = process.env.PRODUCT_HEAD || null;
const apiUrl = process.env.D2_API_URL || 'http://127.0.0.1:8005';
const appUrl = process.env.D2_APP_URL || 'http://127.0.0.1:5173';
const user = process.env.T2_USER;
const pass = process.env.T2_PASSWORD;
const outDir = path.resolve(process.env.D2_OUT_DIR || `patient-companion-d2-${phase.toLowerCase()}-artifacts`);
if (!user || !pass) throw new Error('Isolated staff credentials unavailable');

fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const api = await request.newContext({ baseURL: apiUrl });
const login = await api.post('/api/auth/login', { form: { username: user, password: pass } });
if (!login.ok()) throw new Error(`staff login ${login.status()}`);
const tokens = await login.json();
const patientsResponse = await api.get('/api/patients', {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
if (!patientsResponse.ok()) throw new Error(`patients ${patientsResponse.status()}`);
const patients = await patientsResponse.json();
const patient = patients.find(item => item.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('No isolated seeded patient');

const browser = await chromium.launch({ headless: true });
const viewports = [
  { width: 390, height: 844, label: '390x844' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
];
const captures = [];

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });

  const target = phase === 'AFTER'
    ? `${appUrl}/patients/${patient.id}?tab=companion`
    : `${appUrl}/patients/${patient.id}?tab=tracking`;
  const response = await page.goto(target, { waitUntil: 'networkidle', timeout: 90000 });
  const httpStatus = response?.status() ?? null;
  await page.getByRole('button', { name: 'Document', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await page.addStyleTag({ content: '*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important;caret-color:transparent!important}' });

  const hasCompanionTab = (await page.getByRole('button', { name: 'Companion', exact: true }).count()) > 0;
  let panelVisible = false;
  let ephemeralVisible = false;
  let detailShot = null;

  if (phase === 'AFTER') {
    const panel = page.locator('[data-patient-companion-admin]');
    await panel.waitFor({ state: 'visible', timeout: 30000 });
    panelVisible = await panel.isVisible();
    const email = page.getByPlaceholder('patient@email.com');
    await email.fill('patient@example.test');
    const invitationButton = page.getByRole('button', { name: /Créer une invitation|Réémettre une invitation/ });
    await invitationButton.click();
    const invitation = page.locator('[data-ephemeral-invitation]');
    await invitation.waitFor({ state: 'visible', timeout: 30000 });
    ephemeralVisible = await invitation.isVisible();

    // Visual evidence must represent the settled product, not the transient success toast.
    const generatedToast = page.getByText('Invitation Companion générée', { exact: true });
    if (await generatedToast.count()) {
      await generatedToast.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
    }

    // First AFTER frame: true page-top experience after transient invitation feedback settles.
    // Do not force the panel underneath the sticky patient header.
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'auto' }));
    await page.waitForTimeout(100);
  }

  const shot = `${phase.toLowerCase()}-patient-companion-${viewport.label}.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: false });

  if (phase === 'AFTER') {
    // Second AFTER frame: QR/manual-code area. This prevents mobile evidence from pretending
    // one 844px viewport can show both the complete admin surface and the ephemeral secret.
    const invitation = page.locator('[data-ephemeral-invitation]');
    await invitation.evaluate(element => element.scrollIntoView({ block: 'start', behavior: 'auto' }));
    await page.waitForTimeout(100);
    detailShot = `after-patient-companion-invitation-${viewport.label}.png`;
    await page.screenshot({ path: path.join(outDir, detailShot), fullPage: false });
  }

  const capture = {
    phase,
    viewport,
    httpStatus,
    hasCompanionTab,
    panelVisible,
    ephemeralVisible,
    pageErrors,
    consoleErrors,
    shot,
    detailShot,
  };
  captures.push(capture);

  if (httpStatus !== 200 || pageErrors.length || consoleErrors.length) {
    throw new Error(`Runtime error ${viewport.label}: ${JSON.stringify(capture)}`);
  }
  if (phase === 'BEFORE' && hasCompanionTab) {
    throw new Error(`Companion tab unexpectedly exists in BEFORE ${viewport.label}`);
  }
  if (phase === 'AFTER' && (!hasCompanionTab || !panelVisible || !ephemeralVisible || !detailShot)) {
    throw new Error(`Companion target incomplete in AFTER ${viewport.label}: ${JSON.stringify(capture)}`);
  }
  await context.close();
}

fs.writeFileSync(
  path.join(outDir, 'report.json'),
  JSON.stringify({ phase, productHead, patientId: patient.id, captures }, null, 2),
);

await browser.close();
await api.dispose();
