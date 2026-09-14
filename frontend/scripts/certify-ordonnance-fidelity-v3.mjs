import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/ordonnance-fidelity-v3');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();

const patients = await api.get('/api/patients', {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patientList = await patients.json();
const patient = patientList.find((p) => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2 certification patient not found');

const browser = await chromium.launch({ headless: true });
const captures = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function resetScrollableAncestors(page) {
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      const style = getComputedStyle(el);
      if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight) {
        el.scrollTop = 0;
      }
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(180);
}

async function measure(page) {
  return page.evaluate(() => {
    const rect = (selector) => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height };
    };
    const visible = (el) => {
      const style = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && r.width > 0 && r.height > 0;
    };
    const inViewport = (r) => Boolean(r && r.bottom > 0 && r.top < window.innerHeight);
    const touchSelectors = [
      '[data-prescription-intelligence-studio="v1"] button',
      '[data-patient-clinical-context="c1"] input',
      '[data-patient-clinical-context="c1"] select',
      '[data-patient-clinical-context="c1"] textarea',
      '[data-patient-clinical-context="c1"] button',
      '[data-prescription-indication="document"] textarea',
      '[data-ordonnance-drug-card] button',
      '[data-ordonnance-prescription-composer] select',
    ];
    const touchHeights = touchSelectors.flatMap(selector =>
      [...document.querySelectorAll(selector)].filter(visible).map(el => el.getBoundingClientRect().height),
    );
    const addLine = [...document.querySelectorAll('button')].find(el => visible(el) && /ajouter une ligne/i.test(el.textContent || ''));
    if (addLine) touchHeights.push(addLine.getBoundingClientRect().height);
    const doc = document.documentElement;
    const studio = rect('[data-prescription-intelligence-studio="v1"]');
    const clinicalContext = rect('[data-patient-clinical-context="c1"]');
    const prescriptionIndication = rect('[data-prescription-indication="document"]');
    const clinicalBlocked = rect('[data-clinical-rule-status="blocked"]');
    const safety = rect('[data-safety-status]');
    const drugCard = rect('[data-ordonnance-drug-card]');
    const addLineRect = addLine ? addLine.getBoundingClientRect() : null;
    const desktopPreview = rect('[data-ordonnance-desktop-preview="inline"]');
    const clinicalRoot = document.querySelector('[data-patient-clinical-context="c1"]');
    const clinicalFields = clinicalRoot
      ? [...clinicalRoot.querySelectorAll('input, select, textarea')].filter(visible).length
      : 0;
    return {
      studio,
      clinicalContext,
      prescriptionIndication,
      clinicalBlocked,
      safety,
      drugCard,
      drugCardInViewport: inViewport(drugCard),
      addLine: addLineRect ? { height: addLineRect.height, top: addLineRect.top, bottom: addLineRect.bottom } : null,
      addLineInViewport: inViewport(addLineRect),
      clinicalExpanded: clinicalRoot?.getAttribute('data-context-expanded') === 'true',
      clinicalFields,
      desktopPreview,
      visibleEditorWidth: studio && desktopPreview ? Math.max(0, desktopPreview.left - studio.left) : null,
      touchMin: touchHeights.length ? Math.min(...touchHeights) : null,
      touchCount: touchHeights.length,
      noHorizontalOverflow: doc.scrollWidth <= doc.clientWidth + 2,
    };
  });
}

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));

  const url = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=ordonnance`;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.locator('[data-prescription-intelligence-studio="v1"]').waitFor({ state: 'attached', timeout: 30000 });
  await page.locator('[data-patient-clinical-context="c1"]').waitFor({ state: 'attached', timeout: 30000 });
  await page.locator('[data-prescription-indication="document"]').waitFor({ state: 'attached', timeout: 30000 });
  await page.locator('[data-clinical-rule-status="blocked"]').waitFor({ state: 'attached', timeout: 30000 });
  await resetScrollableAncestors(page);

  const topMetrics = await measure(page);
  const topShot = `ordonnance-fidelity-v3-${viewport.width}x${viewport.height}-top.png`;
  await page.screenshot({ path: path.join(outDir, topShot), fullPage: false });

  const addLine = page.getByRole('button', { name: /ajouter une ligne/i }).first();
  if (!(await addLine.count())) throw new Error('Add medication line action not found');
  await addLine.scrollIntoViewIfNeeded();
  await page.waitForTimeout(180);
  const planningMetrics = await measure(page);
  const planningShot = `ordonnance-fidelity-v3-${viewport.width}x${viewport.height}-planning.png`;
  await page.screenshot({ path: path.join(outDir, planningShot), fullPage: false });

  const contextToggle = page.getByRole('button', { name: /renseigner/i }).first();
  if (!(await contextToggle.count())) throw new Error('C1 context expand action not found');
  await contextToggle.scrollIntoViewIfNeeded();
  await contextToggle.click();
  await page.locator('[data-patient-clinical-context="c1"][data-context-expanded="true"]').waitFor({ state: 'attached', timeout: 10000 });
  await page.waitForTimeout(180);
  const clinicalMetrics = await measure(page);
  const clinicalShot = `ordonnance-fidelity-v3-${viewport.width}x${viewport.height}-clinical.png`;
  await page.screenshot({ path: path.join(outDir, clinicalShot), fullPage: false });

  const reduceContext = page.getByRole('button', { name: /réduire/i }).first();
  if (!(await reduceContext.count())) throw new Error('C1 context reduce action not found');
  await reduceContext.click();
  await page.waitForTimeout(120);

  let previewScene = null;
  if (viewport.width >= 1280) {
    const previewButton = page.getByRole('button', { name: /aperçu/i }).first();
    if (!(await previewButton.count())) throw new Error('Desktop preview action not found');
    await previewButton.click();
    const inlinePreview = page.locator('[data-ordonnance-desktop-preview="inline"]');
    await inlinePreview.waitFor({ state: 'visible', timeout: 30000 });
    await page.waitForTimeout(250);
    const previewMetrics = await measure(page);
    const previewShot = `ordonnance-fidelity-v3-${viewport.width}x${viewport.height}-preview.png`;
    await page.screenshot({ path: path.join(outDir, previewShot), fullPage: false });
    previewScene = { screenshot: previewShot, metrics: previewMetrics };
  }

  captures.push({
    viewport,
    top: { screenshot: topShot, metrics: topMetrics },
    planning: { screenshot: planningShot, metrics: planningMetrics },
    clinical: { screenshot: clinicalShot, metrics: clinicalMetrics },
    preview: previewScene,
    pageErrors,
  });

  await context.close();
}

const failures = [];
for (const capture of captures) {
  for (const scene of ['top', 'planning']) {
    const metrics = capture[scene].metrics;
    if (!metrics.studio) failures.push(`${capture.viewport.width}-${scene}: V1 studio missing`);
    if (!metrics.clinicalContext) failures.push(`${capture.viewport.width}-${scene}: C1 clinical context missing`);
    if (metrics.clinicalExpanded) failures.push(`${capture.viewport.width}-${scene}: C1 must be compact by default`);
    if (!metrics.prescriptionIndication) failures.push(`${capture.viewport.width}-${scene}: document-scoped indication missing`);
    if (!metrics.clinicalBlocked) failures.push(`${capture.viewport.width}-${scene}: fail-closed clinical status missing`);
    if (!metrics.noHorizontalOverflow) failures.push(`${capture.viewport.width}-${scene}: horizontal overflow`);
    if (metrics.touchMin !== null && metrics.touchMin < 43.5) failures.push(`${capture.viewport.width}-${scene}: touch target ${metrics.touchMin}`);
  }

  const planningMetrics = capture.planning.metrics;
  if (!planningMetrics.drugCard) failures.push(`${capture.viewport.width}-planning: medication card missing`);
  if (!planningMetrics.drugCardInViewport) failures.push(`${capture.viewport.width}-planning: medication card not visible with add-line planning scene`);
  if (!planningMetrics.addLineInViewport) failures.push(`${capture.viewport.width}-planning: add-line action not visible`);

  const clinicalMetrics = capture.clinical.metrics;
  if (!clinicalMetrics.clinicalContext) failures.push(`${capture.viewport.width}-clinical: C1 context missing`);
  if (!clinicalMetrics.clinicalExpanded) failures.push(`${capture.viewport.width}-clinical: C1 context did not expand`);
  if (clinicalMetrics.clinicalFields < 4) failures.push(`${capture.viewport.width}-clinical: expected structured C1 fields visible`);
  if (!clinicalMetrics.noHorizontalOverflow) failures.push(`${capture.viewport.width}-clinical: horizontal overflow`);
  if (clinicalMetrics.touchMin !== null && clinicalMetrics.touchMin < 43.5) failures.push(`${capture.viewport.width}-clinical: touch target ${clinicalMetrics.touchMin}`);

  if (capture.viewport.width >= 1280) {
    const previewMetrics = capture.preview?.metrics;
    if (!previewMetrics?.desktopPreview) failures.push(`${capture.viewport.width}-preview: inline preview missing`);
    if ((previewMetrics?.desktopPreview?.width || 0) < 270) failures.push(`${capture.viewport.width}-preview: inline preview too narrow`);
    if ((previewMetrics?.studio?.width || 0) < 530) failures.push(`${capture.viewport.width}-preview: editor layout width below 530px`);
    if ((previewMetrics?.visibleEditorWidth || 0) < 495) failures.push(`${capture.viewport.width}-preview: visible editor width below 495px`);
    if (!previewMetrics?.clinicalContext) failures.push(`${capture.viewport.width}-preview: C1 clinical context missing`);
    if (previewMetrics?.clinicalExpanded) failures.push(`${capture.viewport.width}-preview: C1 should be compact after explicit reduce`);
    if (!previewMetrics?.prescriptionIndication) failures.push(`${capture.viewport.width}-preview: document-scoped indication missing`);
    if (!previewMetrics?.clinicalBlocked) failures.push(`${capture.viewport.width}-preview: fail-closed clinical status missing`);
    if (!previewMetrics?.noHorizontalOverflow) failures.push(`${capture.viewport.width}-preview: horizontal overflow`);
  }
  if (capture.pageErrors.length) failures.push(`${capture.viewport.width}: page errors ${capture.pageErrors.join(' | ')}`);
}

const report = {
  status: failures.length ? 'FAIL' : 'PASS',
  patientId: patient.id,
  viewports: viewports.map(v => `${v.width}x${v.height}`),
  captures,
  failures,
};
fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify(report, null, 2));

await browser.close();
await api.dispose();
console.log(JSON.stringify(report, null, 2));
if (failures.length) process.exit(1);
