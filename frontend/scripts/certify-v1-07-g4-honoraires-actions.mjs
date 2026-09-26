
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

async function inputByValue(page, value) {
  const inputs = page.locator('input');
  const count = await inputs.count();
  for (let index = 0; index < count; index += 1) {
    const candidate = inputs.nth(index);
    if ((await candidate.inputValue()) === value) return candidate;
  }
  throw new Error('Input with value "' + value + '" not found');
}

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
const captureTreasuryGuardBeforeOnly = process.env.G4_TREASURY_GUARD_BEFORE_ONLY === '1';

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

async function waitForPointerBlockingToasts(page) {
  await page.waitForFunction(() => {
    const toaster = document.querySelector('[data-rht-toaster]');
    if (!toaster) return true;
    return !Array.from(toaster.children).some((node) => {
      if (!(node instanceof HTMLElement)) return false;
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.pointerEvents !== 'none'
        && style.visibility !== 'hidden'
        && Number(style.opacity || '1') > 0
        && rect.width > 0
        && rect.height > 0;
    });
  }, null, { timeout: 10000 });
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
    const toothButton = page.getByRole('button', { name: 'Dent ' + tooth, exact: true });
    await toothButton.focus();
    await page.keyboard.press('Enter');
    if ((await toothButton.getAttribute('aria-pressed')) !== 'true') throw new Error('Pediatric tooth selection failed: ' + tooth);
    await page.keyboard.press('Enter');
    if ((await toothButton.getAttribute('aria-pressed')) !== 'false') throw new Error('Pediatric tooth deselection failed: ' + tooth);
  }
  actions.push('all-20-pediatric-teeth-toggle');

  await page.getByText('Sélection rapide', { exact: true }).click();
  for (const group of ['Maxillaire','Mandibule','Toutes']) {
    await page.getByRole('button', { name: group, exact: true }).click();
    await page.getByText(/dent\(s\) sélectionnée\(s\)/i).waitFor({ state: 'visible', timeout: 5000 });
    await page.getByRole('button', { name: 'Réinitialiser', exact: true }).click();
  }
  actions.push('pediatric-quick-selection-neutral');

  await page.getByRole('button', { name: 'Adulte', exact: true }).click();
  await page.getByRole('button', { name: 'Réduire Schéma', exact: true }).click();
  await page.getByRole('button', { name: 'Afficher Schéma', exact: true }).waitFor({ state: 'visible' });
  await page.getByRole('button', { name: 'Afficher Schéma', exact: true }).click();
  await page.getByRole('button', { name: 'Réduire Schéma', exact: true }).waitFor({ state: 'visible' });
  actions.push('odontogram-open-collapse-adult-pediatric');

  await page.getByText('Sélection rapide', { exact: true }).click();
  for (const group of ['Maxillaire','Mandibule','Toutes']) {
    await page.getByRole('button', { name: group, exact: true }).click();
    await page.getByText(/dent\(s\) sélectionnée\(s\)/i).waitFor({ state: 'visible', timeout: 5000 });
    await page.getByRole('button', { name: 'Réinitialiser', exact: true }).click();
  }
  actions.push('adult-quick-selection-neutral');

  for (const tooth of [11,12,13]) {
    const button = page.getByRole('button', { name: 'Dent ' + tooth, exact: true });
    await button.focus();
    await page.keyboard.press('Enter');
  }
  await page.getByText(/3 dent\(s\) sélectionnée\(s\)/i).waitFor({ state: 'visible', timeout: 5000 });
  const selectedSearch = page.getByPlaceholder('Rechercher un acte pour cette sélection…');
  await selectedSearch.fill('Bridge');
  const bridgeButton = page.getByRole('button', { name: /Bridge/ }).last();
  await bridgeButton.waitFor({ state: 'visible', timeout: 5000 });
  await bridgeButton.click();
  await page.getByText('Bridge 3 éléments', { exact: true }).last().waitFor({ state: 'visible', timeout: 5000 });
  actions.push('multi-tooth-search-add');

  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Note Honoraires', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  const adultTeeth = [11,12,13,14,15,16,17,18,21,22,23,24,25,26,27,28,31,32,33,34,35,36,37,38,41,42,43,44,45,46,47,48];
  for (const tooth of adultTeeth) {
    const toothButton = page.getByRole('button', { name: 'Dent ' + tooth, exact: true });
    await toothButton.focus();
    await page.keyboard.press('Enter');
    if ((await toothButton.getAttribute('aria-pressed')) !== 'true') throw new Error('Adult tooth selection failed: ' + tooth);
    await page.keyboard.press('Enter');
    if ((await toothButton.getAttribute('aria-pressed')) !== 'false') throw new Error('Adult tooth deselection failed: ' + tooth);
  }
  actions.push('all-32-adult-teeth-toggle');

  const dent11Button = page.getByRole('button', { name: 'Dent 11', exact: true });
  await dent11Button.focus();
  await page.keyboard.press('Enter');
  const singleSearch = page.getByPlaceholder('Rechercher un acte pour cette sélection…');
  await singleSearch.fill('Composite 1 face');
  const compositeButton = page.getByRole('button', { name: /Composite 1 face/ }).last();
  await compositeButton.waitFor({ state: 'visible', timeout: 5000 });
  await compositeButton.click();
  await page.getByText('Composite 1 face', { exact: true }).last().waitFor({ state: 'visible', timeout: 5000 });
  actions.push('single-tooth-search-add');

  const dent12Button = page.getByRole('button', { name: 'Dent 12', exact: true });
  await dent12Button.focus();
  await page.keyboard.press('Enter');
  if ((await dent12Button.getAttribute('aria-pressed')) !== 'true') throw new Error('Single selection state missing');
  await page.keyboard.press('Enter');
  if ((await dent12Button.getAttribute('aria-pressed')) !== 'false') throw new Error('Single deselection state missing');
  actions.push('single-tooth-natural-deselect');

  const responsiveScene = await snapshot(page, viewport, 'odontogram-selection-flow');
  if (responsiveScene.overflow) throw new Error('Odontogram selection flow overflow detected');
  actions.push('odontogram-selection-responsive');

  const actionDock = page.locator('[data-accounting-action-dock]');
  await actionDock.waitFor({ state: 'visible', timeout: 5000 });
  const dockBox = await actionDock.boundingBox();
  if (!dockBox || dockBox.y < 0 || dockBox.y + dockBox.height > viewport.height + 2) {
    throw new Error('Accounting action dock is not fully viewport-accessible');
  }
  for (const label of ['Aperçu','Enregistrer','Imprimer','À régler','Partiel','Payé','Espèces','TPE','Chèque','Virement']) {
    await actionDock.getByRole('button', { name: label, exact: true }).waitFor({ state: 'visible', timeout: 5000 });
  }
  await actionDock.getByRole('button', { name: 'Payé', exact: true }).click();
  await actionDock.getByRole('button', { name: 'TPE', exact: true }).click();
  await actionDock.getByRole('button', { name: 'Partiel', exact: true }).click();
  await actionDock.getByRole('alert').waitFor({ state: 'visible', timeout: 5000 });
  await actionDock.getByRole('button', { name: 'Compris', exact: true }).click();
  await actionDock.getByRole('button', { name: 'À régler', exact: true }).click();
  await page.screenshot({
    path: path.join(outDir, 'g4-honoraires-' + viewport.width + 'x' + viewport.height + '-accounting-action-dock.png'),
    fullPage: false,
    animations: 'disabled',
  });
  actions.push('accounting-action-dock-no-scroll');

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

  await page.getByRole('button', { name: /Échéances & options/i }).click();
  const advancedTitle = page.getByText('Encaissement', { exact: true });
  await advancedTitle.waitFor({ state: 'visible' });
  const advancedOverlay = advancedTitle.locator('xpath=ancestor::div[contains(@class,"fixed")][1]');

  const accountedLabel = advancedOverlay.getByText('Comptabiliser CA', { exact: true });
  await accountedLabel.locator('..').getByRole('button').click();
  // A prior successful catalog action may still have a transient toast over the
  // treasury status row. Do not force the click: wait until the real pointer
  // path is available, then exercise the visible control normally.
  await waitForPointerBlockingToasts(page);
  await advancedOverlay.getByRole('button', { name: 'Attente', exact: true }).click();
  await advancedOverlay.getByRole('button', { name: 'Partiel', exact: true }).click();
  await advancedOverlay.getByRole('alert').waitFor({ state: 'visible', timeout: 5000 });
  await page.screenshot({
    path: path.join(outDir, 'g4-honoraires-' + viewport.width + 'x' + viewport.height + '-treasury-partial-guard-before.png'),
    fullPage: false,
    animations: 'disabled',
  });
  if (captureTreasuryGuardBeforeOnly) {
    evidence.push({
      viewport,
      actions: [...actions, 'treasury-partial-guard-before'],
      beforeOnly: true,
      pageErrors,
      http5xx,
    });
    await context.close();
    continue;
  }
  await advancedOverlay.getByRole('button', { name: 'Compris', exact: true }).click();
  await advancedOverlay.getByRole('button', { name: 'Réglé', exact: true }).click();

  for (const mode of ['Espèces','Chèque','TPE','Virement']) {
    await advancedOverlay.getByRole('button', { name: mode, exact: true }).click();
  }

  await advancedOverlay.getByRole('button', { name: 'Unique', exact: true }).click();
  await advancedOverlay.getByRole('button', { name: /Global \/ Planifié/i }).click();
  await advancedOverlay.getByRole('button', { name: /Nouvelle Échéance/i }).click();
  let installment = await inputByValue(page, 'Versement 1');
  await installment.fill('Échéance G4 supprimée');
  let row = installment.locator('xpath=ancestor::div[contains(@class,"grid")][1]');
  await row.locator('input[type="date"]').fill('2026-10-15');
  await row.locator('input[type="number"]').fill('500');
  await row.locator('button').click();
  try {
    await inputByValue(page, 'Échéance G4 supprimée');
    throw new Error('Treasury installment delete failed');
  } catch (error) {
    if (String(error).includes('Treasury installment delete failed')) throw error;
  }

  await advancedOverlay.getByRole('button', { name: /Nouvelle Échéance/i }).click();
  installment = await inputByValue(page, 'Versement 1');
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
  const truthCopy = advancedOverlay.getByText('Ces réglages seront enregistrés avec la note lors de son enregistrement.', { exact: true });
  await truthCopy.waitFor({ state: 'visible', timeout: 5000 });
  await page.screenshot({
    path: path.join(outDir, 'g4-honoraires-' + viewport.width + 'x' + viewport.height + '-treasury-truth-after.png'),
    fullPage: false,
    animations: 'disabled',
  });
  page.on('request', requestListener);
  await advancedOverlay.getByRole('button', { name: 'Appliquer à la note', exact: true }).click();
  await page.getByText('Encaissement', { exact: true }).waitFor({ state: 'hidden', timeout: 5000 });
  page.off('request', requestListener);
  if (persistenceRequests.length) throw new Error('Treasury apply unexpectedly persisted');
  actions.push('treasury-apply-local-only-truthful');

  await page.getByRole('button', { name: /Échéances & options/i }).click();
  const treasuryTitle = page.getByText('Encaissement', { exact: true });
  const treasuryOverlay = treasuryTitle.locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
  const treasuryTopClose = treasuryOverlay.locator('button').first();
  const topCloseOwnsHit = await treasuryTopClose.evaluate((button) => {
    const rect = button.getBoundingClientRect();
    const target = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
    return target === button || Boolean(target && button.contains(target));
  });
  if (!topCloseOwnsHit) throw new Error('Treasury top close does not own hit target');
  await page.screenshot({
    path: path.join(outDir, 'g4-honoraires-' + viewport.width + 'x' + viewport.height + '-treasury-layer-after.png'),
    fullPage: false,
    animations: 'disabled',
  });
  await treasuryTopClose.click();
  await page.getByText('Encaissement', { exact: true }).waitFor({ state: 'hidden', timeout: 5000 });

  await page.getByRole('button', { name: /Échéances & options/i }).click();
  await page.getByRole('button', { name: 'Fermer', exact: true }).click();
  await page.getByText('Encaissement', { exact: true }).waitFor({ state: 'hidden', timeout: 5000 });
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

const expectedActionGroups = 14;
if (!captureTreasuryGuardBeforeOnly) {
  for (const row of evidence) {
    if (row.actions.length !== expectedActionGroups) throw new Error('Honoraires action-group count mismatch');
  }
}

const summary = captureTreasuryGuardBeforeOnly ? {
  status: 'BEFORE_CAPTURED',
  viewports: evidence.length,
  evidence,
} : {
  status: 'PASS',
  actionGroupsPerViewport: expectedActionGroups,
  totalActionGroupProofs: expectedActionGroups * evidence.length,
  treasuryConfirmPersists: false,
  evidence,
};
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_HONORAIRES_ACTIONS ' + JSON.stringify({
  status: summary.status,
  totalActionGroupProofs: summary.totalActionGroupProofs || 0,
  treasuryConfirmPersists: summary.treasuryConfirmPersists ?? false,
  viewports: summary.viewports || evidence.length,
}));