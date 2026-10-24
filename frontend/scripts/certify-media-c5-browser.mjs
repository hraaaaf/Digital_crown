import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/media-c5');
fs.mkdirSync(outDir, { recursive: true });
const runtimeUser = process.env.T2_USER;
const runtimePassword = process.env.T2_PASSWORD;
if (!runtimeUser || !runtimePassword) throw new Error('C5 requires isolated T2 credentials');

const viewports = [
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: runtimeUser, password: runtimePassword } });
if (!login.ok()) throw new Error(`C5 login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error(`C5 patients failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find((row) => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('C5 fixture patient T2-0001 missing');
await api.patch(`/api/patients/${patient.id}/ortho`, { headers, data: { is_ortho_active: true } });

const validPng = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEANmpCD8ongcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfUJxAYTIfIvQAAAAAElFTkSuQmCC', 'base64');
for (const [timepoint, assetType] of [['T0', 'PHOTO'], ['T1', 'RADIOGRAPH'], ['T2', 'PHOTO']]) {
  const upload = await api.post(`/api/patients/${patient.id}/assets/import`, {
    headers,
    multipart: {
      file: { name: `c5-${timepoint.toLowerCase()}.png`, mimeType: 'image/png', buffer: validPng },
      asset_type: assetType,
      source_kind: 'UPLOAD',
      timepoint,
    },
  });
  if (!upload.ok()) throw new Error(`C5 ${timepoint} import failed: ${upload.status()} ${await upload.text()}`);
}

const browser = await chromium.launch({ headless: true });
const evidence = [];
for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  // Exact same token initialization already verified by genuine G1
  // A→B→A test; token is minted by the live isolated FastAPI login above.
  await context.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
  const page = await context.newPage();
  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('response', (response) => {
    if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() });
  });

  // The existing G1 E2E verifies the same server-issued synthetic token
  // while checking real patient GET and workstation/bootstrap 200. C5 is a
  // responsive matrix, not a login-flow test: reuse that certified session
  // bootstrap rather than relying on a flaky portal redirect.
  const browserResponses = [];
  page.on('response', response => {
    const target = new URL(response.url());
    if (target.pathname === `/api/patients/${patient.id}` ||
        target.pathname === '/api/workstation/bootstrap' ||
        target.pathname === `/api/patients/${patient.id}/assets`) {
      browserResponses.push({
        route: target.pathname, status: response.status(),
        method: response.request().method(),
      });
    }
  });
  await page.goto(
    `http://127.0.0.1:5173/patients/${patient.id}?tab=radiology&radioTab=media`,
    { waitUntil: 'domcontentloaded', timeout: 90000 },
  );
  try {
    await page.locator('[data-flow-patient-surface="radiology"]').waitFor({
      state: 'visible', timeout: 45000,
    });
    await page.locator('[data-testid="patient-media-timeline"]').waitFor({
      state: 'visible', timeout: 45000,
    });
    await page.getByText('Médiathèque clinique', { exact: true }).waitFor({
      state: 'visible', timeout: 30000,
    });
  } catch (err) {
    // Capture the failing page instead of relying on the absence of a widget.
    await page.screenshot({
      path: path.join(outDir, `c5-route-diagnostic-${viewport.width}.png`),
      fullPage: false,
    });
    throw new Error('C5 authenticated patient route not rendered: ' + JSON.stringify({
      expectedPatientId: patient.id,
      actualUrl: page.url(),
      browserResponses,
      body: (await page.locator('body').innerText()).slice(0, 450),
      reason: String(err),
    }));
  }
  if (new URL(page.url()).pathname !== `/patients/${patient.id}`) {
    throw new Error('C5 unexpectedly left the authenticated patient route: ' + page.url());
  }
  const hasPatient200 = browserResponses.some(x => x.route === `/api/patients/${patient.id}` &&
    x.method === 'GET' && x.status === 200);
  const hasWorkstation200 = browserResponses.some(x => x.route === '/api/workstation/bootstrap' &&
    x.status === 200);
  const hasMedia200 = browserResponses.some(x => x.route === `/api/patients/${patient.id}/assets` &&
    x.method === 'GET' && x.status === 200);
  if (!hasPatient200 || !hasWorkstation200 || !hasMedia200) {
    throw new Error('C5 authenticated server access failed: ' + JSON.stringify(browserResponses));
  }

  // Exercise the real permission-filtered rail with a keyboard, not only CSS.
  let mobileNavigation = null;
  if (viewport.width === 390) {
    const rail = page.locator('#dc-radiology-patient-tabs');
    const nextButton = page.getByRole('button', { name: 'Afficher les autres onglets' });
    await nextButton.waitFor({ state: 'visible', timeout: 20000 });
    const before = await rail.evaluate(element => ({
      left: element.scrollLeft,
      max: element.scrollWidth - element.clientWidth,
    }));
    await nextButton.focus();
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => {
      const rail = document.getElementById('dc-radiology-patient-tabs');
      return rail !== null && rail.scrollLeft > 10;
    }, null, { timeout: 10000 });
    const after = await rail.evaluate(element => element.scrollLeft);
    mobileNavigation = { pass: before.max > 10 && after > before.left, before, after };
    if (!mobileNavigation.pass) {
      throw new Error('Mobile tab keyboard pagination did not scroll: ' + JSON.stringify(mobileNavigation));
    }
  }

  const search = page.getByLabel('Rechercher un média');
  await search.fill('radio');
  const filteredText = await page.getByText(/1\/1/).count();
  if (!filteredText) throw new Error('C5 server search did not narrow media list to 1/1');
  await search.fill('');

  const addButtons = page.getByRole('button', { name: 'Ajouter à la comparaison' });
  await addButtons.nth(0).click();
  await addButtons.nth(1).click();
  const comparePanel = page.getByTestId('media-compare-panel');
  await comparePanel.waitFor({ state: 'visible', timeout: 30000 });

  // Observe the application's own positioning. The certification must not scroll
  // the panel itself, otherwise it can hide or manufacture a sticky-header defect.
  await page.waitForTimeout(400);
  const visualFrame = await page.evaluate(() => {
    const header = document.querySelector('[data-dc-patient-radiology="true"] > header');
    const panel = document.querySelector('[data-testid="media-compare-panel"]');
    const workspace = document.querySelector('[data-testid="patient-media-timeline"]');
    if (!(header instanceof HTMLElement) || !(panel instanceof HTMLElement) || !(workspace instanceof HTMLElement)) {
      return { stickyOverlap: true, workspaceOverlap: true, missingLayout: true,
        headerBottom: null, panelTop: null, workspaceTop: null };
    }
    const headerStyle = getComputedStyle(header);
    // At <lg the patient header is intentionally in normal document flow,
    // not position:sticky. CSS class selectors such as 'header.sticky' cannot
    // detect conditional utility styles: inspect the resolved CSS instead.
    const headerIsSticky = ['sticky', 'fixed'].includes(headerStyle.position);
    const headerBottom = Math.round(header.getBoundingClientRect().bottom);
    const panelTop = Math.round(panel.getBoundingClientRect().top);
    const workspaceTop = Math.round(workspace.getBoundingClientRect().top);
    return {
      stickyOverlap: headerIsSticky && headerBottom > 0 && panelTop < headerBottom + 8,
      workspaceOverlap: headerIsSticky && headerBottom > 0 && workspaceTop < headerBottom + 8,
      headerIsSticky,
      headerPosition: headerStyle.position,
      headerBottom,
      panelTop,
      workspaceTop,
    };
  });
  // At 390 px compare both clinical media simultaneously, with full-screen
  // actions preserved and no crop of clinical image pixels.
  const mobileCompare = viewport.width === 390 ? await comparePanel.evaluate(panel => {
    const grid = panel.querySelector('.dc-c5-compare-grid');
    const cards = [...panel.querySelectorAll('.dc-c5-compare-asset')];
    if (!(grid instanceof HTMLElement) || cards.length !== 2) return { pass: false, reason: 'missing-grid' };
    const style = getComputedStyle(grid);
    const columns = style.gridTemplateColumns.split(' ').filter(Boolean).length;
    const contentFit = cards.every(card => {
      const img = card.querySelector('img');
      const preview = card.children[1];
      return preview instanceof HTMLElement &&
        preview.getBoundingClientRect().height <= 180 &&
        (!img || getComputedStyle(img).objectFit === 'contain');
    });
    const buttons = cards.every(card => !!card.querySelector('button[aria-label="Ouvrir ce média en plein écran"]'));
    return { pass: columns === 2 && contentFit && buttons, columns, contentFit, buttons };
  }) : null;
  if (mobileCompare && !mobileCompare.pass) throw new Error('C5 mobile side-by-side full-content contract: ' + JSON.stringify(mobileCompare));
  let mobileZoom = null;
  if (viewport.width === 390) {
    const labels = comparePanel.locator('.dc-c5-expand-label:visible');
    const zoomCount = await labels.count();
    const labelsReadable = zoomCount === 2 &&
      await labels.evaluateAll(elements => elements.every(element =>
        getComputedStyle(element).display !== 'none' &&
        element.getBoundingClientRect().width >= 20));
    mobileZoom = { pass: labelsReadable, count: zoomCount };
    if (!mobileZoom.pass) {
      throw new Error('C5 Zoom labels not visibly painted: ' + JSON.stringify(mobileZoom));
    }
  }
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const shot = `c5-after-compare-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: false });
  if (viewport.width === 390) {
    await comparePanel.getByRole('button', { name: 'Ouvrir ce média en plein écran' }).first().click();
    await page.getByRole('dialog', { name: 'Visionneuse média clinique' }).waitFor({
      state: 'visible', timeout: 15000,
    });
    await page.getByRole('button', { name: 'Fermer la visionneuse' }).click();
  }
  evidence.push({ viewport, shot, overflow, visualFrame, mobileCompare, mobileNavigation, mobileZoom, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();
const invalid = evidence.flatMap((row) => [
  ...(row.overflow ? [{ viewport: row.viewport, reason: 'overflow' }] : []),
  ...(row.visualFrame?.stickyOverlap ? [{ viewport: row.viewport, reason: 'sticky-overlap', visualFrame: row.visualFrame }] : []),
  ...(row.visualFrame?.workspaceOverlap ? [{ viewport: row.viewport, reason: 'workspace-sticky-overlap', visualFrame: row.visualFrame }] : []),
  ...row.pageErrors.map((error) => ({ viewport: row.viewport, reason: 'pageerror', error })),
  ...row.http5xx.map((response) => ({ viewport: row.viewport, reason: 'http5xx', ...response })),
]);
const summary = { status: evidence.length === 3 && invalid.length === 0 ? 'PASS' : 'FAIL', captures: evidence.length, expectedCaptures: 3, viewports, invalid };
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('MEDIA_C5_CERTIFICATION', JSON.stringify(summary));
if (summary.status !== 'PASS') process.exit(1);
