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
page.on('pageerror', (error) => pageErrors.push(String(error)));
page.on('request', (req) => {
  if (req.url().includes('ai-diagnostic')) aiDiagnosticRequests.push(req.url());
});

await page.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });

const pathFor = (patientId, documentTab = 'libre') =>
  `/patients/${patientId}?tab=admin&documentTab=${documentTab}`;

async function spaNavigate(relativePath) {
  await page.evaluate((nextPath) => {
    window.history.pushState({}, '', nextPath);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }, relativePath);
}

async function waitForDocumentTab(slug) {
  await page.waitForFunction(
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

await spaNavigate(pathFor(patientA.id));
await Promise.race([
  firstDelayedA,
  new Promise((_, reject) => setTimeout(() => reject(new Error('No delayed patient A request observed')), 15000)),
]);

await spaNavigate(bPath);
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

await waitForDocumentTab('libre');
await page.getByText('Document Libre', { exact: true }).first().waitFor({ timeout: 30000 });
const libreEditor = page.locator('textarea').first();
await libreEditor.waitFor({ state: 'visible', timeout: 30000 });
const dirtyMarker = 'T1 URL dirty boundary — conserver si annulation';
await libreEditor.fill(dirtyMarker);

await spaNavigate(pathFor(patientB.id, 'certificat'));
const discardDialog = page.getByRole('dialog').filter({ hasText: 'Document en cours' }).last();
await discardDialog.waitFor({ state: 'visible', timeout: 15000 });
await page.screenshot({ path: path.join(outDir, 't1-url-dirty-dialog.png'), fullPage: false });
await discardDialog.getByRole('button', { name: 'Annuler', exact: true }).click();
await discardDialog.waitFor({ state: 'hidden', timeout: 10000 });
await waitForDocumentTab('libre');
const cancelRestoredUrl = new URLSearchParams(new URL(page.url()).search).get('documentTab') === 'libre';
const cancelPreservedDraft = (await libreEditor.inputValue()) === dirtyMarker;

await spaNavigate(pathFor(patientB.id, 'certificat'));
await discardDialog.waitFor({ state: 'visible', timeout: 15000 });
await discardDialog.getByRole('button', { name: 'Continuer', exact: true }).click();
await discardDialog.waitFor({ state: 'hidden', timeout: 10000 });
await waitForDocumentTab('certificat');
await page.getByText('Certificat', { exact: true }).first().waitFor({ timeout: 30000 });
const confirmReachedTarget = new URLSearchParams(new URL(page.url()).search).get('documentTab') === 'certificat';

const companionAbsent = (await page.locator('[data-tour="tab-strategie"]').count()) === 0
  && (await page.getByText('Compagnon Diagnostique', { exact: true }).count()) === 0;
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
    confirmReachedTarget,
    pass: cancelRestoredUrl && cancelPreservedDraft && confirmReachedTarget,
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

await context.close();
await browser.close();
await api.dispose();

if (evidence.status !== 'PASS') process.exit(1);
