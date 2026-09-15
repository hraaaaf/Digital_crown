import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/ordonnance-fidelity-v3');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

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
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
const page = await context.newPage();
await page.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });

const url = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=ordonnance`;
await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
await page.locator('[data-prescription-intelligence-studio="v1"]').waitFor({ state: 'attached', timeout: 30000 });

const nameInput = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').first();
if (!(await nameInput.count())) throw new Error('Medication name input not found');
await nameInput.scrollIntoViewIfNeeded();
await nameInput.fill('ACIG');

const results = page.locator('[data-medication-catalog-results]');
await results.waitFor({ state: 'visible', timeout: 30000 });
await page.waitForTimeout(350);

const buttons = results.locator('button[data-presentation-id]');
const count = await buttons.count();
if (count !== 2) throw new Error(`Expected exactly 2 ACIG suggestions, got ${count}`);

const visibleTexts = [];
for (let i = 0; i < count; i += 1) {
  visibleTexts.push((await buttons.nth(i).innerText()).trim());
}
if (!visibleTexts.some(text => /ACIGAM 100 MG/i.test(text))) throw new Error('ACIGAM 100 MG suggestion missing');
if (!visibleTexts.some(text => /ACIGAM 200 MG/i.test(text))) throw new Error('ACIGAM 200 MG suggestion missing');
if ((await nameInput.inputValue()) !== 'ACIG') throw new Error('Input changed unexpectedly');

const provenanceLabel = results.getByText(
  'Référentiel documentaire Maroc · provenance par présentation · statut commercial actuel non certifié',
  { exact: true },
);
await provenanceLabel.waitFor({ state: 'visible', timeout: 10000 });

const selectedBadges = page.getByText('Présentation identifiée', { exact: true });
if (await selectedBadges.count()) throw new Error('A presentation was selected unexpectedly');

const shot = 'acig-autocomplete-proof-1280x900.png';
await page.screenshot({ path: path.join(outDir, shot), fullPage: false });
fs.writeFileSync(path.join(outDir, 'acig-autocomplete-proof.json'), JSON.stringify({
  query: 'ACIG',
  selected: false,
  suggestionCount: count,
  provenanceLabel: await provenanceLabel.innerText(),
  visibleSuggestions: visibleTexts,
  screenshot: shot,
}, null, 2));

await browser.close();
await api.dispose();
console.log(JSON.stringify({
  query: 'ACIG',
  selected: false,
  suggestionCount: count,
  provenanceLabel: await provenanceLabel.innerText(),
  visibleSuggestions: visibleTexts,
}, null, 2));
