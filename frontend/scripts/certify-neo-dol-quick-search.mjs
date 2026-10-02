import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/neo-n43b-procedure-safety-visual');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const auth = { Authorization: `Bearer ${tokens.access_token}` };

const patients = await api.get('/api/patients', { headers: auth });
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find(p => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2 certification patient not found');

const backendSearch = await api.get('/api/medications/neo/search?q=DOL', { headers: auth });
if (!backendSearch.ok()) throw new Error(`Backend DOL search failed: ${backendSearch.status()} ${await backendSearch.text()}`);
const backendRows = (await backendSearch.json()).slice(0, 6);

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
const page = await context.newPage();
const pageErrors = [];
page.on('pageerror', error => pageErrors.push(String(error)));

await page.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });

const workstationState = {
  workstationId: 'neo-dol-visual-proof',
  defaultExperience: 'cabinet',
  stationLocked: false,
  stationEscapeAuthorized: false,
  stationEscapeExpiresAt: null,
  enrollmentRequired: false,
  authenticated: true,
  pinConfigured: true,
  canManage: true,
  canConfigurePin: true,
};
await page.route('**/api/workstation/bootstrap', route => route.fulfill({
  status: 200, contentType: 'application/json', body: JSON.stringify(workstationState),
}));
await page.route('**/api/workstation/state', route => route.fulfill({
  status: 200, contentType: 'application/json', body: JSON.stringify(workstationState),
}));

await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=ordonnance`, {
  waitUntil: 'networkidle',
  timeout: 90000,
});
await page.locator('[data-prescription-intelligence-studio="v1"]').waitFor({ state: 'attached', timeout: 30000 });

const quick = page.locator('[data-neo-quick-access]');
await quick.waitFor({ state: 'visible', timeout: 30000 });
const input = quick.getByLabel('Ajouter un médicament ou un protocole');
await input.fill('DOL');

const results = quick.locator('div.mt-2.overflow-hidden.rounded-xl');
await results.waitFor({ state: 'visible', timeout: 30000 });
await page.waitForTimeout(500);

const renderedButtons = results.locator('button');
const renderedCount = await renderedButtons.count();
const rendered = [];
for (let i = 0; i < renderedCount; i += 1) {
  const button = renderedButtons.nth(i);
  rendered.push({
    text: (await button.innerText()).trim(),
  });
}

const backendNormalized = backendRows.map(row => ({
  presentation_id: String(row.presentation_id || ''),
  nom: String(row.nom || ''),
  dci: String(row.dci || ''),
  dosage: String(row.dosage || ''),
  unite: String(row.unite || ''),
  forme: String(row.forme || ''),
  source_id: String(row.source?.id || ''),
  source_label: String(row.source?.label || ''),
  snapshot_date: String(row.source?.snapshot_date || ''),
  marketing_verified: Boolean(row.source?.current_marketing_status_verified),
}));

const presentationTexts = rendered
  .map(item => item.text)
  .filter(Boolean);

const mismatches = [];
for (const row of backendNormalized) {
  const expectedStrength = [row.dosage, row.unite].filter(Boolean).join(' ').trim();
  const match = presentationTexts.some(text =>
    text.includes(row.nom)
    && text.includes(row.dci || 'DCI non renseignée')
    && text.includes(expectedStrength || 'dosage à préciser')
  );
  if (!match) mismatches.push(row.presentation_id || row.nom);
}

const inputValue = await input.inputValue();
if (inputValue !== 'DOL') throw new Error(`Quick input changed unexpectedly: ${inputValue}`);
if (!backendNormalized.length) throw new Error('Backend returned no DOL suggestions');
if (!renderedCount) throw new Error('Quick access rendered no suggestions for DOL');
if (mismatches.length) throw new Error(`Rendered suggestions do not match backend rows: ${mismatches.join(', ')}`);
if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);

const screenshot = 'neo-quick-search-dol-1280x900.png';
await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false });

const report = {
  status: 'PASS',
  query: inputValue,
  backendSuggestionCount: backendNormalized.length,
  backendSuggestions: backendNormalized,
  renderedSuggestionCount: renderedCount,
  renderedSuggestions: rendered,
  mismatches,
  pageErrors,
  screenshot,
};
fs.writeFileSync(path.join(outDir, 'dol-quick-search-results.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));

await browser.close();
await api.dispose();
