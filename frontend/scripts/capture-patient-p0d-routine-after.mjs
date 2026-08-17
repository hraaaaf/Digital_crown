import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-p0d-routine-after');
fs.mkdirSync(outDir, { recursive: true });
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password: 'T2BrowserPass123!' } });
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const patients = await api.get('/api/patients', { headers: { Authorization: `Bearer ${tokens.access_token}` } });
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find((p) => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2-0001 patient not found');

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function openClinical(page) {
  await seedAuth(page);
  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=clinical`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: /Examen Clinique Complet/i }).waitFor({ state: 'visible', timeout: 30000 });
}

async function positionFocus(page, focus) {
  await focus.scrollIntoViewIfNeeded();
  await focus.evaluate((el) => {
    const header = document.querySelector('header');
    const headerBottom = header ? header.getBoundingClientRect().bottom : 0;
    const requiredTop = headerBottom + 24;
    const currentTop = el.getBoundingClientRect().top;
    const delta = currentTop - requiredTop;

    let parent = el.parentElement;
    while (parent && parent !== document.body && parent !== document.documentElement) {
      const style = getComputedStyle(parent);
      const scrollable = /(auto|scroll)/.test(style.overflowY) && parent.scrollHeight > parent.clientHeight + 1;
      if (scrollable) {
        parent.scrollBy({ top: delta, behavior: 'instant' });
        return;
      }
      parent = parent.parentElement;
    }

    window.scrollBy({ top: delta, behavior: 'instant' });
  });
  await page.waitForTimeout(180);
}

async function snap(page, phase, viewport, pageErrors, httpErrors) {
  const focus = phase === 'result'
    ? page.getByText(/Proposition clinique à valider/).first().locator('xpath=..')
    : page.getByText(/Synthèse clinique structurée/).first();
  await focus.waitFor({ state: 'visible', timeout: 12000 });
  await positionFocus(page, focus);

  const focusedText = await focus.innerText();
  const geometry = await focus.evaluate((el) => {
    const rect = el.getBoundingClientRect();
    const header = document.querySelector('header');
    const headerBottom = header ? header.getBoundingClientRect().bottom : 0;
    return {
      top: rect.top,
      bottom: rect.bottom,
      left: rect.left,
      right: rect.right,
      width: rect.width,
      height: rect.height,
      headerBottom,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      visibleBelowHeader: rect.top >= headerBottom + 8 && rect.bottom > headerBottom + 24,
      horizontallyVisible: rect.left >= -1 && rect.right <= window.innerWidth + 1,
    };
  });
  const metrics = await page.evaluate(() => ({
    pathname: location.pathname,
    search: location.search,
    noHorizontalOverflow: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
  }));

  const screenshot = `patient-p0d-routine-${phase}-after-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false });

  let focusScreenshot = null;
  if (phase === 'result') {
    focusScreenshot = `patient-p0d-routine-result-card-after-${viewport.width}x${viewport.height}.png`;
    await focus.screenshot({ path: path.join(outDir, focusScreenshot) });
  }

  evidence.push({
    phase,
    viewport,
    screenshot,
    focusScreenshot,
    focusedText,
    geometry,
    metrics,
    pageErrors: [...pageErrors],
    httpErrors: [...httpErrors],
  });
}

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const httpErrors = [];
  page.on('pageerror', e => pageErrors.push(String(e)));
  page.on('response', r => { if (r.status() >= 400) httpErrors.push({ status: r.status(), url: r.url() }); });

  await openClinical(page);
  await page.getByRole('button', { name: /Examen Clinique Complet/i }).click();
  await page.getByRole('button', { name: /Contrôle de routine \/ Bilan/i }).click();

  await page.getByText('Antécédents médicaux', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Cardiopathie \/ Prothèse valvulaire/i }).click();
  await page.getByText('Hygiène bucco-dentaire', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Médiocre — tartre abondant/i }).click();
  await page.getByText('Statut parodontal', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Parodontite sévère/i }).click();
  await page.getByText('Statut dentaire', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Caries actives présentes/i }).click();
  await page.getByText('Examen occlusal', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Bruxisme \/ usure marquée/i }).click();
  await page.getByText('Examen des tissus mous', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Lésion suspecte/i }).click();

  await snap(page, 'calculating', viewport, pageErrors, httpErrors);
  await page.getByText(/Proposition clinique à valider/).waitFor({ state: 'visible', timeout: 12000 });
  await snap(page, 'result', viewport, pageErrors, httpErrors);
  await context.close();
}

const relevantHttpErrors = evidence.flatMap(e => e.httpErrors.map(err => ({ phase: e.phase, viewport: e.viewport, ...err })))
  .filter(e => !/\/api\/patients\/\d+\/master-plan$/.test(e.url) || e.status !== 404);
const results = evidence.filter(e => e.phase === 'result');

const bannedAutomaticActions = [
  /Antibioprophylaxie avant tout soin invasif/i,
  /Amox\s*2\s*g\s*,?\s*1h avant/i,
  /Phase I\s*:\s*surfaçage radiculaire/i,
  /Détartrage bi-maxillaire/i,
  /Bilan radiologique complet/i,
  /Bilan cariologique\s*\(radiographies/i,
  /Traitement des caries\s*\(composite\s*\/\s*amalgame\)/i,
  /Gouttière de protection nocturne/i,
  /\bIRM\s+ATM\b/i,
  /Biopsie\s*\/\s*cytodiagnostic/i,
  /Équilibration occlusale sélective/i,
];
const required = [/Observations recueillies/i, /Vigilance/i, /ne pose pas automatiquement de diagnostic/i, /décision du praticien/i];
const summary = {
  totalCaptures: evidence.length,
  overflowFindings: evidence.filter(e => !e.metrics.noHorizontalOverflow).map(e => ({ phase: e.phase, viewport: e.viewport })),
  pageErrorFindings: evidence.filter(e => e.pageErrors.length).map(e => ({ phase: e.phase, viewport: e.viewport, errors: e.pageErrors })),
  relevantHttpErrors,
  resultGeometryFindings: results
    .filter(e => !e.geometry.visibleBelowHeader || !e.geometry.horizontallyVisible)
    .map(e => ({ viewport: e.viewport, geometry: e.geometry })),
  resultContracts: results.map(e => ({
    viewport: e.viewport,
    bannedMatches: bannedAutomaticActions.filter(pattern => pattern.test(e.focusedText)).map(pattern => pattern.source),
    hasRequiredSafetyText: required.every(pattern => pattern.test(e.focusedText)),
    visibleBelowHeader: e.geometry.visibleBelowHeader,
    horizontallyVisible: e.geometry.horizontallyVisible,
  })),
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
if (
  summary.totalCaptures !== 8 ||
  summary.overflowFindings.length ||
  summary.pageErrorFindings.length ||
  summary.relevantHttpErrors.length ||
  summary.resultGeometryFindings.length
) {
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
}
if (summary.resultContracts.some(e => e.bannedMatches.length || !e.hasRequiredSafetyText)) {
  console.error('Routine fail-closed contract failed.');
  console.error(JSON.stringify(summary.resultContracts, null, 2));
  process.exit(1);
}
await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
