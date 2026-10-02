import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-ordonnance-actions');
fs.mkdirSync(outDir, { recursive: true });

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('G4 ordonnance login failed');
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patientsResponse = await api.get('/api/patients', { headers });
if (!patientsResponse.ok()) throw new Error('G4 ordonnance patient list failed');
const patient = (await patientsResponse.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('G4 ordonnance fixture patient missing');

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
  const screenshot = `g4-ordonnance-${viewport.width}x${viewport.height}-${scene}.png`;
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false, animations: 'disabled' });
  return { screenshot, overflow };
}

async function selectExactAmoxicillin(page) {
  const input = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').first();
  await input.fill('AMOXICILLINE');
  const results = page.locator('[data-medication-catalog-results]');
  await results.waitFor({ state: 'visible', timeout: 30000 });
  const buttons = results.locator('button[data-presentation-id]');
  const count = await buttons.count();
  for (let i = 0; i < count; i += 1) {
    const lines = (await buttons.nth(i).innerText()).split('\n').map(v => v.trim().toUpperCase()).filter(Boolean);
    if (lines.includes('AMOXICILLINE') || lines.includes('AMOXICILLIN')) {
      await buttons.nth(i).click();
      return;
    }
  }
  throw new Error('Exact amoxicillin presentation missing');
}


async function openContextualChoice(page, label) {
  const trigger = page.getByRole('button', { name: label, exact: true }).first();
  await trigger.click();
  const menu = page.getByRole('menu').first();
  await menu.waitFor({ state: 'visible', timeout: 10000 });
  return { trigger, menu };
}

async function applyManualContextualChoice(page, label, value) {
  const { trigger, menu } = await openContextualChoice(page, label);
  await menu.getByRole('menuitem', { name: /Modifier manuellement/i }).click();
  const input = page.getByLabel('Valeur personnalisée');
  await input.fill(value);
  await page.getByRole('button', { name: 'Appliquer', exact: true }).click();
  if (!(await trigger.innerText()).includes(value)) {
    throw new Error(`Manual contextual choice not applied: ${label} -> ${value}`);
  }
}

async function selectFirstContextualOption(page, label) {
  const { trigger, menu } = await openContextualChoice(page, label);
  const options = menu.getByRole('menuitem').filter({ hasNotText: 'Modifier manuellement' });
  if (await options.count() < 1) throw new Error(`No contextual option available: ${label}`);
  await options.first().click();
  const value = (await trigger.innerText()).trim();
  if (!value || value === label) throw new Error(`Contextual choice did not update: ${label}`);
  return value;
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

  await page.route('**/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'READY',
        rule_id: 'IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN',
        rule_version: 'g4-browser-action',
        blockers: [],
        active_ingredient_code: 'AMOXICILLIN',
        total_dose_mg: 2000,
        timing_min_minutes_before: 30,
        timing_max_minutes_before: 60,
        single_dose: true,
        source_ids: ['G4_BROWSER_FIXTURE'],
      }),
    });
  });

  const url = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=ordonnance`;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.locator('[data-prescription-intelligence-studio="v1"]').waitFor({ state: 'attached', timeout: 30000 });

  const actions = [];

  // Keep the desktop hover-expanding sidebar from covering document controls in the harness.
  await page.mouse.move(viewport.width - 2, viewport.height - 2);
  await page.waitForTimeout(120);
  const typeExam = page.getByRole('button', { name: 'Type radio ou examen' }).first();
  await typeExam.click();
  await page.getByPlaceholder("DÉTAILS DE L'EXAMEN RADIOLOGIQUE...").first().waitFor({ state: 'visible' });
  const typeMedication = page.getByRole('button', { name: 'Type médicament' }).first();
  await typeMedication.click();
  await page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').first().waitFor({ state: 'visible' });
  actions.push('type-toggle');

  await page.getByRole('button', { name: /Ajouter une ligne/i }).click();
  let names = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...');
  if (await names.count() !== 2) throw new Error('Add line did not create second row');
  await names.nth(0).fill('FIRST G4');
  await names.nth(1).fill('SECOND G4');
  const moveUp = page.getByRole('button', { name: 'Monter le médicament' });
  const moveDown = page.getByRole('button', { name: 'Descendre le médicament' });
  if (viewport.width >= 1024) {
    if (await moveUp.count() !== 2 || await moveDown.count() !== 2) throw new Error('Desktop reorder controls missing');
    await moveUp.nth(1).click();
    names = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...');
    if ((await names.first().inputValue()) !== 'SECOND G4') throw new Error('Move up failed');
    await moveDown.first().click();
    names = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...');
    if ((await names.nth(1).inputValue()) !== 'SECOND G4') throw new Error('Move down failed');
  } else {
    if (await moveUp.count() !== 0 || await moveDown.count() !== 0) throw new Error('Mobile unexpectedly exposes desktop-only reorder controls');
  }
  await page.getByRole('button', { name: 'Supprimer le médicament' }).nth(1).click();
  if (await page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').count() !== 1) throw new Error('Remove row failed');
  actions.push('add-reorder-remove');

  const name = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').first();
  await name.fill('G4 MANUAL');
  await page.waitForTimeout(700);
  const { trigger: formTrigger, menu: formMenu } = await openContextualChoice(page, 'Forme');
  const formTriggerHeight = await formTrigger.evaluate(node => node.getBoundingClientRect().height);
  if (formTriggerHeight < 43.5) throw new Error('Form contextual trigger touch target below 44px');
  const openScene = await snapshot(page, viewport, 'forme-open');
  await formMenu.getByRole('menuitem', { name: /Modifier manuellement/i }).click();
  await page.getByLabel('Valeur personnalisée').fill('COMPRIMÉS');
  await page.getByRole('button', { name: 'Appliquer', exact: true }).click();
  if (!/COMPRIMÉS/.test(await formTrigger.innerText())) throw new Error('Manual form selection not applied');
  actions.push('manual-form');

  await applyManualContextualChoice(page, 'Dose', '500 MG');
  const ns = page.getByTitle('Non substituable').first();
  const nsBefore = await ns.getAttribute('aria-pressed');
  await ns.click();
  if (await ns.getAttribute('aria-pressed') === nsBefore) throw new Error('NS toggle failed');

  for (const label of ['Prise', 'Rythme', 'Durée ou limite', 'Moment ou condition']) {
    await selectFirstContextualOption(page, label);
  }
  const freePosology = page.getByLabel('Posologie en texte libre').first();
  await freePosology.fill('Saisie praticien G4');
  if (await freePosology.inputValue() !== 'Saisie praticien G4') throw new Error('Free posology edit failed');
  actions.push('dose-ns-posology');

  const indication = page.getByLabel('Indication de cette ordonnance');
  await indication.fill('Indication G4 navigateur');
  if (await indication.inputValue() !== 'Indication G4 navigateur') throw new Error('Indication edit failed');

  const legal = page.getByRole('switch', { name: 'Mentions légales (Radioprotection)' });
  const legalBefore = await legal.getAttribute('aria-checked');
  await legal.click();
  if (await legal.getAttribute('aria-checked') === legalBefore) throw new Error('Legal annotations toggle failed');
  actions.push('indication-legal');

  const contextPanel = page.locator('[data-patient-clinical-context="c2"]');
  await contextPanel.waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForFunction(() => {
    const panel = document.querySelector('[data-patient-clinical-context="c2"]');
    if (!panel) return false;
    const text = panel.textContent || '';
    return !text.includes('Chargement du contexte clinique');
  }, undefined, { timeout: 15000 });

  const loadFailure = contextPanel.getByText('Contexte non chargé. Aucune valeur n’est supposée.', { exact: true });
  if (await loadFailure.isVisible().catch(() => false)) {
    throw new Error('Clinical context failed to load in G4 Ordonnance harness');
  }

  const weightField = page.getByLabel('Poids explicite en kilogrammes');
  if (!(await weightField.isVisible().catch(() => false))) {
    const contextToggle = page.getByRole('button', { name: 'Renseigner', exact: true });
    await contextToggle.waitFor({ state: 'visible', timeout: 10000 });
    await contextToggle.click();
    await weightField.waitFor({ state: 'visible', timeout: 10000 });
  }
  await weightField.fill('70');
  await page.getByLabel('Statut des allergies médicamenteuses').selectOption('NONE_KNOWN');
  await page.getByLabel('Statut allergie pénicilline ou amoxicilline').selectOption('NONE_KNOWN');
  await page.getByLabel('Catégorie cardiaque endocardite infectieuse').selectOption('PROSTHETIC_CARDIAC_VALVE');
  await page.getByLabel('Statut du contexte rénal').selectOption('NO_KNOWN_IMPAIRMENT');
  await page.getByLabel('Statut du contexte hépatique').selectOption('NO_KNOWN_IMPAIRMENT');
  await page.getByRole('button', { name: 'Enregistrer le contexte', exact: true }).click();
  await page.getByText('Contexte enregistré', { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
  actions.push('clinical-context-save');

  const contextReduce = page.getByRole('button', { name: 'Réduire', exact: true }).first();
  if (await contextReduce.isVisible().catch(() => false)) {
    await contextReduce.click();
  } else {
    const weightField = page.getByLabel('Poids explicite en kilogrammes');
    if (await weightField.isVisible().catch(() => false)) {
      throw new Error('Clinical context stayed expanded without a visible collapse control after save');
    }
  }
  await selectExactAmoxicillin(page);
  const ie = page.locator('[data-ie-prophylaxis-rule="c2"]');
  await ie.getByRole('button', { name: 'Évaluer', exact: true }).click();
  await page.getByLabel('Date prévue du geste').fill('2026-10-01');
  await page.getByLabel('Geste avec manipulation gingivale périapicale ou perforation muqueuse').selectOption('yes');
  await page.getByLabel('Voie orale possible').selectOption('yes');
  await page.getByLabel('Prise actuelle de pénicilline ou amoxicilline').selectOption('no');
  await page.getByRole('button', { name: 'Vérifier la prophylaxie', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('[data-ie-prophylaxis-rule="c2"]')?.getAttribute('data-rule-result') === 'READY', undefined, { timeout: 10000 });
  if ((await ie.getAttribute('data-rule-result')) !== 'READY') throw new Error('IE explicit evaluation did not reach READY');
  actions.push('ie-explicit-evaluation');

  const finalScene = await snapshot(page, viewport, 'actions-final');
  if (openScene.overflow || finalScene.overflow) throw new Error('Horizontal overflow detected');
  if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);
  if (http5xx.length) throw new Error(`HTTP 5xx: ${JSON.stringify(http5xx)}`);

  evidence.push({ viewport, actions, openScene, finalScene, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();

const expectedActions = 7;
for (const row of evidence) {
  if (row.actions.length !== expectedActions) throw new Error(`Expected ${expectedActions} action groups, got ${row.actions.length}`);
}

const summary = {
  status: 'PASS',
  viewports: evidence.map(row => row.viewport),
  actionGroupsPerViewport: expectedActions,
  totalActionGroupProofs: evidence.length * expectedActions,
  evidence,
};

fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_ORDONNANCE_ACTIONS', JSON.stringify({ status: summary.status, totalActionGroupProofs: summary.totalActionGroupProofs }));
