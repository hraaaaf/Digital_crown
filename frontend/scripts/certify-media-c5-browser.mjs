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
  const page = await context.newPage();
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });

  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('response', (response) => {
    if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() });
  });

  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Imagerie', exact: true }).click();
  await page.getByRole('button', { name: 'Médiathèque', exact: true }).click();
  await page.getByText('Médiathèque clinique', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });

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
    const header = document.querySelector('header.sticky');
    const panel = document.querySelector('[data-testid="media-compare-panel"]');
    const workspace = document.querySelector('[data-testid="patient-media-timeline"]');
    if (!(header instanceof HTMLElement) || !(panel instanceof HTMLElement) || !(workspace instanceof HTMLElement)) {
      return { stickyOverlap: true, workspaceOverlap: true, headerBottom: null, panelTop: null, workspaceTop: null };
    }
    const headerBottom = Math.round(header.getBoundingClientRect().bottom);
    const panelTop = Math.round(panel.getBoundingClientRect().top);
    const workspaceTop = Math.round(workspace.getBoundingClientRect().top);
    return {
      stickyOverlap: panelTop < headerBottom + 8,
      workspaceOverlap: workspaceTop < headerBottom + 8,
      headerBottom,
      panelTop,
      workspaceTop,
    };
  });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const shot = `c5-after-compare-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: false });
  evidence.push({ viewport, shot, overflow, visualFrame, pageErrors, http5xx });
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
