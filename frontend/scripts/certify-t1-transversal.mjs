import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser');
fs.mkdirSync(outDir, { recursive: true });

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T1 runtime probe requires T2_USER and T2_PASSWORD');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();

const patientsResponse = await api.get('/api/patients', {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
if (!patientsResponse.ok()) {
  throw new Error(`Patients fetch failed: ${patientsResponse.status()} ${await patientsResponse.text()}`);
}
const patients = await patientsResponse.json();
const patientA = patients.find((patient) => patient.numero_dossier === 'T2-0001');
const patientB = patients.find((patient) => patient.numero_dossier === 'T2-0002');
if (!patientA || !patientB) throw new Error('T1 runtime patients T2-0001/T2-0002 not found');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
const page = await context.newPage();
const pageErrors = [];
const aiDiagnosticRequests = [];

function observePage(targetPage) {
  targetPage.on('pageerror', (error) => pageErrors.push(String(error)));
  targetPage.on('request', (req) => {
    if (req.url().includes('ai-diagnostic')) aiDiagnosticRequests.push(req.url());
  });
}

async function installAuth(targetPage) {
  await targetPage.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

observePage(page);
await installAuth(page);

const pathFor = (patientId, documentTab = 'libre') =>
  `/patients/${patientId}?tab=admin&documentTab=${documentTab}`;

async function spaNavigate(targetPage, relativePath) {
  await targetPage.evaluate((nextPath) => {
    window.history.pushState({}, '', nextPath);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }, relativePath);
}

async function waitForDocumentTab(targetPage, slug) {
  await targetPage.waitForFunction(
    (expected) => new URLSearchParams(window.location.search).get('documentTab') === expected,
    slug,
    { timeout: 15000 },
  );
}

const patientBName = `${patientB.nom.toUpperCase()} ${patientB.prenom}`;
const patientAName = `${patientA.nom.toUpperCase()} ${patientA.prenom}`;
const bPath = pathFor(patientB.id);
try {
  await page.goto(`http://127.0.0.1:5173${bPath}`, { waitUntil: 'domcontentloaded', timeout: 90000 });
} catch (error) {
  if (!String(error).includes('net::ERR_ABORTED')) throw error;
}
await page.waitForURL((url) => url.pathname === `/patients/${patientB.id}`, { timeout: 30000 });
await page.getByRole('heading', { name: patientBName, exact: true }).waitFor({ timeout: 30000 });
await page.locator('[data-tour="patient-tabs"]').getByText('Documents', { exact: true }).waitFor({ timeout: 30000 });

let releaseDelayedA;
const releaseDelayedAPromise = new Promise((resolve) => { releaseDelayedA = resolve; });
let firstDelayedAResolve;
const firstDelayedA = new Promise((resolve) => { firstDelayedAResolve = resolve; });
let delayedARequests = 0;
let delayedAFulfilled = 0;
const delayedARouteErrors = [];
const delayedPattern = `**/api/patients/${patientA.id}`;

await page.route(delayedPattern, async (route) => {
  delayedARequests += 1;
  try {
    const response = await route.fetch();
    if (firstDelayedAResolve) {
      firstDelayedAResolve();
      firstDelayedAResolve = null;
    }
    await releaseDelayedAPromise;
    await route.fulfill({ response });
    delayedAFulfilled += 1;
  } catch (error) {
    delayedARouteErrors.push(String(error));
  }
});

await spaNavigate(page, pathFor(patientA.id));
await Promise.race([
  firstDelayedA,
  new Promise((_, reject) => setTimeout(() => reject(new Error('No delayed patient A request observed')), 15000)),
]);

await spaNavigate(page, bPath);
await page.getByRole('heading', { name: patientBName, exact: true }).waitFor({ timeout: 30000 });
const bAuthoritativeBeforeRelease = page.url().includes(`/patients/${patientB.id}`)
  && await page.getByRole('heading', { name: patientBName, exact: true }).isVisible();

releaseDelayedA();
await page.waitForTimeout(800);
await page.unroute(delayedPattern);

const bAuthoritativeAfterRelease = page.url().includes(`/patients/${patientB.id}`)
  && await page.getByRole('heading', { name: patientBName, exact: true }).isVisible()
  && !(await page.getByRole('heading', { name: patientAName, exact: true }).isVisible().catch(() => false));

await page.screenshot({ path: path.join(outDir, 't1-patient-b-authority.png'), fullPage: false });

const openDialog = page.getByRole('dialog').last();
if (await openDialog.isVisible({ timeout: 1000 }).catch(() => false)) {
  await page.keyboard.press('Escape');
  await openDialog.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
}

await waitForDocumentTab(page, 'libre');
await page.getByText('Document Libre', { exact: true }).first().waitFor({ timeout: 30000 });
const libreEditor = page.locator('textarea').first();
await libreEditor.waitFor({ state: 'visible', timeout: 30000 });
const dirtyMarker = 'T1 URL dirty boundary — conserver si annulation';
await libreEditor.fill(dirtyMarker);

await spaNavigate(page, pathFor(patientB.id, 'certificat'));
const discardDialog = page.getByRole('dialog').filter({ hasText: 'Document en cours' }).last();
await discardDialog.waitFor({ state: 'visible', timeout: 15000 });
await page.screenshot({ path: path.join(outDir, 't1-url-dirty-dialog.png'), fullPage: false });
await discardDialog.getByRole('button', { name: 'Annuler', exact: true }).click();
await discardDialog.waitFor({ state: 'hidden', timeout: 10000 });
await waitForDocumentTab(page, 'libre');
const cancelRestoredUrl = new URLSearchParams(new URL(page.url()).search).get('documentTab') === 'libre';
const cancelPreservedDraft = (await libreEditor.inputValue()) === dirtyMarker;
const cancelCompanionAbsent = (await page.locator('[data-tour="tab-strategie"]').count()) === 0
  && (await page.getByText('Compagnon Diagnostique', { exact: true }).count()) === 0;

// Certify explicit discard in a fresh browser realm so the confirmation path is
// independent from the asynchronous URL restoration performed by Cancel.
const confirmContext = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
const confirmPage = await confirmContext.newPage();
observePage(confirmPage);
await installAuth(confirmPage);
try {
  await confirmPage.goto(`http://127.0.0.1:5173${bPath}`, { waitUntil: 'domcontentloaded', timeout: 90000 });
} catch (error) {
  if (!String(error).includes('net::ERR_ABORTED')) throw error;
}
await confirmPage.getByRole('heading', { name: patientBName, exact: true }).waitFor({ timeout: 30000 });
await waitForDocumentTab(confirmPage, 'libre');
await confirmPage.getByText('Document Libre', { exact: true }).first().waitFor({ timeout: 30000 });
const confirmEditor = confirmPage.locator('textarea').first();
await confirmEditor.waitFor({ state: 'visible', timeout: 30000 });
const confirmDirtyMarker = 'T1 URL dirty boundary — abandon explicite';
await confirmEditor.fill(confirmDirtyMarker);
const confirmDirtyArmed = (await confirmEditor.inputValue()) === confirmDirtyMarker;
await spaNavigate(confirmPage, pathFor(patientB.id, 'certificat'));
const confirmDialog = confirmPage.getByRole('dialog').filter({ hasText: 'Document en cours' }).last();
await confirmDialog.waitFor({ state: 'visible', timeout: 15000 });
await confirmDialog.getByRole('button', { name: 'Continuer', exact: true }).click();
await confirmDialog.waitFor({ state: 'hidden', timeout: 10000 });
await waitForDocumentTab(confirmPage, 'certificat');
await confirmPage.getByText('Certificat', { exact: true }).first().waitFor({ timeout: 30000 });
const confirmReachedTarget = new URLSearchParams(new URL(confirmPage.url()).search).get('documentTab') === 'certificat';
const confirmCompanionAbsent = (await confirmPage.locator('[data-tour="tab-strategie"]').count()) === 0
  && (await confirmPage.getByText('Compagnon Diagnostique', { exact: true }).count()) === 0;

const companionAbsent = cancelCompanionAbsent && confirmCompanionAbsent;
const aiDiagnosticAbsent = aiDiagnosticRequests.length === 0;

const evidence = {
  patientBoundary: {
    patientA: { id: patientA.id, dossier: patientA.numero_dossier },
    patientB: { id: patientB.id, dossier: patientB.numero_dossier },
    delayedARequests,
    delayedAFulfilled,
    delayedARouteErrors,
    bAuthoritativeBeforeRelease,
    bAuthoritativeAfterRelease,
    pass: delayedARequests > 0
      && delayedAFulfilled > 0
      && delayedARouteErrors.length === 0
      && bAuthoritativeBeforeRelease
      && bAuthoritativeAfterRelease,
  },
  urlDirtyBoundary: {
    cancelRestoredUrl,
    cancelPreservedDraft,
    confirmDirtyArmed,
    confirmReachedTarget,
    isolatedConfirmationSession: true,
    pass: cancelRestoredUrl && cancelPreservedDraft && confirmDirtyArmed && confirmReachedTarget,
  },
  clinicalBoundary: {
    companionAbsent,
    aiDiagnosticRequests,
    aiDiagnosticAbsent,
    pass: companionAbsent && aiDiagnosticAbsent,
  },
  pageErrors,
};

evidence.status = evidence.patientBoundary.pass
  && evidence.urlDirtyBoundary.pass
  && evidence.clinicalBoundary.pass
  && pageErrors.length === 0
  ? 'PASS'
  : 'FAIL';

fs.writeFileSync(path.join(outDir, 't1-transversal.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));

await confirmContext.close();
await context.close();
await browser.close();
await api.dispose();

if (evidence.status !== 'PASS') process.exit(1);
