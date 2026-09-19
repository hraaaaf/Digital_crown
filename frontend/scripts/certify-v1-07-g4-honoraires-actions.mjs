
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-honoraires-actions');
fs.mkdirSync(outDir, { recursive: true });

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('G4 honoraires login failed');
const tokens = await login.json();
const headers = { Authorization: 'Bearer ' + tokens.access_token };
const patientsResponse = await api.get('/api/patients', { headers });
if (!patientsResponse.ok()) throw new Error('G4 honoraires patient list failed');
const patient = (await patientsResponse.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('G4 honoraires fixture patient missing');

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function snapshot(page, viewport, scene) {
  const screenshot = 'g4-honoraires-' + viewport.width + 'x' + viewport.height + '-' + scene + '.png';
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false, animations: 'disabled' });
  return { screenshot, overflow };
}

for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);

  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('response', response => {
    if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() });
  });

  const url = 'http://127.0.0.1:5173/patients/' + patient.id + '?tab=admin&documentTab=honoraires';
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Note Honoraires', exact: true }).waitFor({ state: 'visible', timeout: 30000 });

  const actions = [];

  const plan = page.getByRole('button', { name: /Plan de soins/i });
  await plan.click();
  await page.getByRole('button', { name: 'Adulte', exact: true }).waitFor({ state: 'visible' });
  await page.getByRole('button', { name: 'Enfant', exact: true }).click();
  await page.getByRole('button', { name: 'Adulte', exact: true }).click();
  actions.push('odontogram-open-adult-pediatric');

  await page.getByRole('button', { name: /Bridge & Prothèses/i }).click();
  for (const group of ['Q1','Q2','Q3','Q4','S1','S2','S3','S4','S5','S6']) {
    await page.getByRole('button', { name: group, exact: true }).click();
    await page.getByText(/dents sélectionnées/i).waitFor({ state: 'visible', timeout: 5000 });
  }
  await page.getByRole('button', { name: 'Réinitialiser', exact: true }).click();
  actions.push('adult-quick-groups-reset');

  for (const act of ['Bridge', 'Stellite', 'Prothèse Adjointe (PAP)', 'Attelle de contention']) {
    await page.getByRole('button', { name: 'Q1', exact: true }).click();
    await page.getByRole('button', { name: act, exact: true }).click();
    await page.getByText(act, { exact: true }).last().waitFor({ state: 'visible', timeout: 5000 });
  }
  await page.getByRole('button', { name: 'Q1', exact: true }).click();
  await page.getByPlaceholder('Ou saisir un autre acte...').fill('Acte groupé G4');
  await page.getByPlaceholder('Prix').fill('1200');
  await page.getByRole('button', { name: 'Appliquer', exact: true }).click();
  await page.getByText('Acte groupé G4', { exact: true }).waitFor({ state: 'visible', timeout: 5000 });
  actions.push('grouped-acts-custom');

  await page.getByRole('button', { name: /Soins Ciblés/i }).click();
  await page.getByRole('button', { name: /Dent 11,/i }).click();
  await page.getByText('Dent 11', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const search = page.getByPlaceholder('Rechercher un acte (Composite, Extraction, Couronne...)');
  await search.fill('Composite 1 face');
  const treatmentRow = page.locator('tr').filter({ hasText: 'Composite 1 face' }).first();
  await treatmentRow.click();
  await treatmentRow.locator('input[type="number"]').fill('450');
  await page.locator('textarea').last().fill('Note G4 navigateur');
  await page.getByRole('button', { name: /Valider la Sélection/i }).click();
  await page.getByText('Composite 1 face', { exact: true }).last().waitFor({ state: 'visible', timeout: 5000 });
  actions.push('targeted-tooth-treatment');

  await page.getByRole('button', { name: /Soins Généraux/i }).click();
  for (const act of ['Détartrage & Polissage','Bilan Parodontal Complet','Blanchiment Dentaire','Fluorisation','Gouttière de Bruxisme','Semestre ODF','Consultation Standard','Aéropolissage']) {
    await page.getByRole('button', { name: act, exact: false }).first().click();
  }
  actions.push('global-care-actions');

  await page.getByRole('button', { name: /Ligne Manuelle/i }).last().click();
  const descriptions = page.getByPlaceholder('Rechercher ou saisir un acte...');
  const prices = page.getByPlaceholder('0.00');
  await descriptions.last().fill('G4 Honoraires manuel');
  await prices.last().fill('321');
  await page.getByRole('button', { name: 'Monter G4 Honoraires manuel' }).click();
  await page.getByRole('button', { name: 'Descendre G4 Honoraires manuel' }).click();
  await page.getByRole('button', { name: 'Supprimer G4 Honoraires manuel' }).click();
  if (await page.getByText('G4 Honoraires manuel', { exact: true }).count()) throw new Error('Manual honorarium line removal failed');
  actions.push('manual-line-order-delete');

  await page.getByRole('button', { name: /Procéder à l'Encaissement/i }).click();
  await page.getByText('Encaissement', { exact: true }).waitFor({ state: 'visible' });

  const accountedLabel = page.getByText('Comptabiliser CA', { exact: true });
  await accountedLabel.locator('..').getByRole('button').click();
  await page.getByRole('button', { name: 'Attente', exact: true }).click();
  await page.getByRole('button', { name: 'Partiel', exact: true }).click();
  await page.getByRole('alert').waitFor({ state: 'visible', timeout: 5000 });
  await page.getByRole('button', { name: 'Compris', exact: true }).click();
  await page.getByRole('button', { name: 'Réglé', exact: true }).click();

  for (const mode of ['Cash','Chèque','TPE','Virement']) {
    await page.getByRole('button', { name: mode, exact: true }).click();
  }

  await page.getByRole('button', { name: 'Unique', exact: true }).click();
  await page.getByRole('button', { name: /Global \/ Planifié/i }).click();
  await page.getByRole('button', { name: /Nouvelle Échéance/i }).click();
  const installment = page.getByDisplayValue('Versement 1');
  await installment.fill('Échéance G4');
  const row = installment.locator('xpath=ancestor::div[contains(@class,"grid")][1]');
  await row.locator('input[type="date"]').fill('2026-10-15');
  await row.locator('input[type="number"]').fill('500');
  actions.push('treasury-configuration');

  const persistenceRequests = [];
  const requestListener = req => {
    const urlValue = req.url();
    if (/payments|documents\/generate|installments/.test(urlValue)) persistenceRequests.push(urlValue);
  };
  page.on('request', requestListener);
  await page.getByRole('button', { name: "Confirmer l'Encaissement", exact: true }).click();
  await page.waitForTimeout(250);
  page.off('request', requestListener);
  if (await page.getByText('Encaissement', { exact: true }).count()) throw new Error('Treasury confirm did not close modal');
  if (persistenceRequests.length) throw new Error('Treasury confirm unexpectedly persisted');
  actions.push('treasury-confirm-local-only');

  await page.getByRole('button', { name: /Procéder à l'Encaissement/i }).click();
  await page.getByRole('button', { name: 'Fermer', exact: true }).click();
  if (await page.getByText('Encaissement', { exact: true }).count()) throw new Error('Treasury close failed');
  actions.push('treasury-close');

  const scene = await snapshot(page, viewport, 'final');
  if (scene.overflow) throw new Error('Horizontal overflow detected');
  if (pageErrors.length) throw new Error('Page errors: ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('HTTP 5xx: ' + JSON.stringify(http5xx));

  evidence.push({ viewport, actions, scene, treasuryConfirmPersistenceRequests: persistenceRequests, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();

const expectedActionGroups = 9;
for (const row of evidence) {
  if (row.actions.length !== expectedActionGroups) throw new Error('Honoraires action-group count mismatch');
}

const summary = {
  status: 'PASS',
  actionGroupsPerViewport: expectedActionGroups,
  totalActionGroupProofs: expectedActionGroups * evidence.length,
  treasuryConfirmPersists: false,
  evidence,
};
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_HONORAIRES_ACTIONS ' + JSON.stringify({
  status: summary.status,
  totalActionGroupProofs: summary.totalActionGroupProofs,
  treasuryConfirmPersists: summary.treasuryConfirmPersists,
}));
