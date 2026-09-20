
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
  await page.getByRole('button', { name: 'Adulte', exact: true }).waitFor({ state: 'visible' });
  await plan.click();
  await page.getByRole('button', { name: 'Adulte', exact: true }).waitFor({ state: 'hidden' });
  await plan.click();
  await page.getByRole('button', { name: 'Adulte', exact: true }).waitFor({ state: 'visible' });
  await page.getByRole('button', { name: 'Enfant', exact: true }).click();
  const pediatricTeeth = [51,52,53,54,55,61,62,63,64,65,71,72,73,74,75,81,82,83,84,85];
  for (const tooth of pediatricTeeth) {
    const toothButton = page.getByRole('button', { name: new RegExp('^Dent ' + tooth + ',') });
    // SVG hit-testing is geometry-dependent in headless Chromium. Exercise the
    // same accessible product action through the keyboard contract instead.
    await toothButton.focus();
    await page.keyboard.press('Enter');
    const title = page.getByText('Dent ' + tooth, { exact: true });
    await title.waitFor({ state: 'visible', timeout: 10000 });
    const selector = title.locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    await selector.locator('button').first().click();
    await title.waitFor({ state: 'hidden', timeout: 10000 });
  }
  actions.push('all-20-pediatric-teeth-open-close');

  await page.getByRole('button', { name: /Bridge & Prothèses/i }).click();
  const quickGroups = page.getByRole('button').filter({ hasText: /^Q[1-8]$/ });
  const quickGroupNames = (await quickGroups.allTextContents()).map(x => x.trim()).filter(Boolean);
  for (const group of quickGroupNames) {
    const groupButton = page.getByRole('button', { name: group, exact: true });
    await groupButton.focus();
    await page.keyboard.press('Enter');
    await page.getByText(/dents sélectionnées/i).waitFor({ state: 'visible', timeout: 5000 });
    await page.getByRole('button', { name: 'Réinitialiser', exact: true }).click();
  }
  actions.push(quickGroupNames.length
    ? 'bridge-quick-groups-runtime-all-reset:' + quickGroupNames.join(',')
    : 'bridge-mode-opened-no-quick-groups-exposed');

  await page.getByRole('button', { name: /Soins Ciblés/i }).click();
  const adultButton = page.getByRole('button', { name: 'Adulte', exact: true });
  if (await adultButton.first().isVisible().catch(() => false)) {
    await adultButton.first().focus();
    await page.keyboard.press('Enter');
  }

  await page.getByRole('button', { name: 'Réduire Schéma', exact: true }).click();
  await page.getByRole('button', { name: 'Afficher Schéma', exact: true }).waitFor({ state: 'visible' });
  await page.getByRole('button', { name: 'Afficher Schéma', exact: true }).click();
  await page.getByRole('button', { name: 'Réduire Schéma', exact: true }).waitFor({ state: 'visible' });
  actions.push('odontogram-open-collapse-adult-pediatric');

  await page.getByRole('button', { name: /Bridge & Prothèses/i }).click();
  for (const group of ['Q1','Q2','Q3','Q4','S1','S2','S3','S4','S5','S6']) {
    await page.getByRole('button', { name: group, exact: true }).click();
    await page.getByText(/dents sélectionnées/i).waitFor({ state: 'visible', timeout: 5000 });
    await page.getByRole('button', { name: 'Réinitialiser', exact: true }).click();
    await page.getByRole('button', { name: group, exact: true }).waitFor({ state: 'visible', timeout: 5000 });
  }
  actions.push('adult-quick-groups-reset');

  const resetGroupedActScene = async () => {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
    await page.getByRole('button', { name: 'Note Honoraires', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    await page.getByRole('button', { name: /Bridge & Prothèses/i }).click();
    const adultButton = page.getByRole('button', { name: 'Adulte', exact: true });
    if (await adultButton.first().isVisible().catch(() => false)) {
      await adultButton.first().focus();
      await page.keyboard.press('Enter');
    }
    const q1 = page.getByRole('button', { name: 'Q1', exact: true });
    await q1.waitFor({ state: 'visible', timeout: 5000 });
    await q1.focus();
    await page.keyboard.press('Enter');
    await page.getByRole('button', { name: 'Bridge', exact: true }).waitFor({ state: 'visible', timeout: 5000 });
  };

  for (const act of [
    { button: 'Bridge', result: 'Bridge' },
    { button: 'Stellite', result: 'Stellite' },
    { button: 'Prothèse Adjointe (PAP)', result: 'Prothèse Adjointe (PAP)' },
    { button: /^Curetage /, result: /^Curetage / },
    { button: /^Surfaçage /, result: /^Surfaçage / },
    { button: 'Attelle de contention', result: 'Attelle de contention' },
  ]) {
    await resetGroupedActScene();
    await page.getByRole('button', { name: act.button, exact: typeof act.button === 'string' }).click();
    await page.getByText(act.result, { exact: typeof act.result === 'string' }).last().waitFor({ state: 'visible', timeout: 5000 });
  }

  await resetGroupedActScene();
  await page.getByPlaceholder('Ou saisir un autre acte...').fill('Acte groupé G4');
  await page.getByPlaceholder('Prix').fill('1200');
  await page.getByRole('button', { name: 'Appliquer', exact: true }).click();
  await page.waitForFunction(
    () => Array.from(document.querySelectorAll('input')).some(input => input.value === 'Acte groupé G4'),
    null,
    { timeout: 5000 }
  );
  actions.push('grouped-acts-custom');

  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Note Honoraires', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await page.getByRole('button', { name: /Soins Ciblés/i }).click();
  const adultButtonForTargeted = page.getByRole('button', { name: 'Adulte', exact: true });
  if (await adultButtonForTargeted.first().isVisible().catch(() => false)) {
    await adultButtonForTargeted.first().focus();
    await page.keyboard.press('Enter');
  }
  const adultTeeth = [11,12,13,14,15,16,17,18,21,22,23,24,25,26,27,28,31,32,33,34,35,36,37,38,41,42,43,44,45,46,47,48];
  for (const tooth of adultTeeth) {
    const toothButton = page.getByRole('button', { name: new RegExp('^Dent ' + tooth + ',') });
    await toothButton.focus();
    await page.keyboard.press('Enter');
    const title = page.getByText('Dent ' + tooth, { exact: true });
    await title.waitFor({ state: 'visible', timeout: 10000 });
    const selector = title.locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    await selector.locator('button').first().click();
    await title.waitFor({ state: 'hidden', timeout: 10000 });
  }
  actions.push('all-32-adult-teeth-open-close');

  const dent11Button = page.getByRole('button', { name: /Dent 11,/i });
  await dent11Button.focus();
  await page.keyboard.press('Enter');
  await page.getByText('Dent 11', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const search = page.getByPlaceholder('Rechercher un acte (Composite, Extraction, Couronne...)');
  const categoryBar = search.locator('xpath=../following-sibling::div[1]');
  const categoryButtons = categoryBar.getByRole('button');
  const categoryLabels = (await categoryButtons.allInnerTexts()).map(label => label.trim()).filter(Boolean);
  if (categoryLabels.length < 3) throw new Error('TreatmentSelector categories missing');
  for (let i = 0; i < categoryLabels.length; i++) {
    const categoryButton = categoryBar.getByRole('button').nth(i);
    await categoryButton.waitFor({ state: 'visible', timeout: 5000 });
    await categoryButton.focus();
    await page.keyboard.press('Enter');
  }

  const specialty = categoryLabels.find(label => {
    const normalized = label.toLocaleLowerCase('fr-FR');
    return !['favoris', 'tous les actes'].includes(normalized);
  });
  if (!specialty) throw new Error('No specialty category available');
  const specialtyButton = page.getByRole('button', { name: specialty, exact: true }).last();
  await specialtyButton.waitFor({ state: 'visible', timeout: 10000 });
  await specialtyButton.focus();
  await page.keyboard.press('Enter');
  const addCatalogAct = page.getByRole('button', { name: /^Ajouter un acte à / }).last();
  await addCatalogAct.waitFor({ state: 'visible', timeout: 10000 });
  await addCatalogAct.focus();
  await page.keyboard.press('Enter');
  await page.getByPlaceholder("Nom de l'acte...").fill('G4 annulé ' + viewport.width);
  await page.getByPlaceholder('Prix MAD').fill('123');
  await page.getByRole('button', { name: '✕', exact: true }).click();
  if (await page.getByPlaceholder("Nom de l'acte...").count()) throw new Error('Custom catalog act cancel failed');

  await addCatalogAct.waitFor({ state: 'visible', timeout: 5000 });
  await addCatalogAct.focus();
  await page.keyboard.press('Enter');
  const catalogActName = 'G4 Catalogue ' + viewport.width;
  await page.getByPlaceholder("Nom de l'acte...").fill(catalogActName);
  await page.getByPlaceholder('Prix MAD').fill('456');
  await page.getByRole('button', { name: 'OK', exact: true }).click();
  await page.getByText(catalogActName, { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  actions.push('treatment-selector-categories-custom-catalog-act');

  await search.fill('Composite 1 face');
  const treatmentRow = page.locator('tr').filter({ hasText: 'Composite 1 face' }).first();
  await treatmentRow.click();
  await treatmentRow.locator('input[type="number"]').fill('450');
  await page.locator('textarea').last().fill('Note G4 navigateur');
  await page.getByRole('button', { name: /Valider la Sélection/i }).click();
  await page.getByText('Composite 1 face', { exact: true }).last().waitFor({ state: 'visible', timeout: 5000 });
  actions.push('targeted-tooth-treatment');

  const dent11Title = page.getByText('Dent 11', { exact: true });
  await dent11Title.waitFor({ state: 'hidden', timeout: 5000 }).catch(async () => {
    const targetedSelector = dent11Title.locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    const closeButton = targetedSelector.locator('button').first();
    await closeButton.waitFor({ state: 'visible', timeout: 5000 });
    await closeButton.click({ force: true });
    await dent11Title.waitFor({ state: 'hidden', timeout: 10000 });
  });

  await page.getByRole('button', { name: /Soins Généraux/i }).click();
  for (const act of [
    'Détartrage & Polissage',
    'Surfaçage Radiculaire (par secteur)',
    'Bilan Parodontal Complet',
    'Blanchiment Dentaire',
    'Fluorisation',
    'Gouttière de Bruxisme',
    'Semestre ODF',
    'Consultation Standard',
    'Aéropolissage',
    'Traitement Parodontal (Séance)',
  ]) {
    await page.getByRole('button', { name: act, exact: true }).click();
  }
  await page.getByRole('button', { name: /Acte personnalisé/i }).click();
  if (!(await page.getByPlaceholder('Rechercher ou saisir un acte...').count())) throw new Error('General-care custom act did not create a line');
  actions.push('global-care-actions-and-custom');

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
  let installment = page.getByDisplayValue('Versement 1');
  await installment.fill('Échéance G4 supprimée');
  let row = installment.locator('xpath=ancestor::div[contains(@class,"grid")][1]');
  await row.locator('input[type="date"]').fill('2026-10-15');
  await row.locator('input[type="number"]').fill('500');
  await row.locator('button').click();
  if (await page.getByDisplayValue('Échéance G4 supprimée').count()) throw new Error('Treasury installment delete failed');

  await page.getByRole('button', { name: /Nouvelle Échéance/i }).click();
  installment = page.getByDisplayValue('Versement 1');
  await installment.fill('Échéance G4');
  row = installment.locator('xpath=ancestor::div[contains(@class,"grid")][1]');
  await row.locator('input[type="date"]').fill('2026-10-15');
  await row.locator('input[type="number"]').fill('500');
  actions.push('treasury-configuration-add-edit-delete');

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
  const treasuryTitle = page.getByText('Encaissement', { exact: true });
  const treasuryOverlay = treasuryTitle.locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
  await treasuryOverlay.locator('button').first().click();
  if (await page.getByText('Encaissement', { exact: true }).count()) throw new Error('Treasury top close failed');

  await page.getByRole('button', { name: /Procéder à l'Encaissement/i }).click();
  await page.getByRole('button', { name: 'Fermer', exact: true }).click();
  if (await page.getByText('Encaissement', { exact: true }).count()) throw new Error('Treasury footer close failed');
  actions.push('treasury-close-controls');

  const scene = await snapshot(page, viewport, 'final');
  if (scene.overflow) throw new Error('Horizontal overflow detected');
  if (pageErrors.length) throw new Error('Page errors: ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('HTTP 5xx: ' + JSON.stringify(http5xx));

  evidence.push({ viewport, actions, scene, treasuryConfirmPersistenceRequests: persistenceRequests, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();

const expectedActionGroups = 13;
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
