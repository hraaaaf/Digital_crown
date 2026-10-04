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

const ordonnanceGateDir = path.resolve('../artifacts/t2-browser/ordonnance-pdf-gate');
fs.mkdirSync(ordonnanceGateDir, { recursive: true });

const med = (i, overrides = {}) => ({
  nom: 'MEDICAMENT TEST ' + String(i).padStart(2, '0'),
  dosage: 'DOSAGE TEST',
  forme: 'COMPRIME',
  posologie: 'Instruction synthétique de mise en page ' + String(i).padStart(2, '0'),
  type: 'MEDICAMENT',
  quantite: 1,
  quantite_explicit: true,
  ...overrides,
});
const longInstruction = 'Instruction synthétique volontairement longue pour éprouver le retour à la ligne, la lisibilité typographique, les espacements verticaux et la stabilité de la composition sans introduire de recommandation clinique réelle.';
const ordonnanceScenarios = [
  {
    id: 'standard',
    medications: [
      med(1, { nom: 'MEDICAMENT TEST ALPHA', dosage: 'DOSAGE A', forme: 'COMPRIME', posologie: 'Instruction synthétique courte A.' }),
      med(2, { nom: 'MEDICAMENT TEST BETA', dosage: 'DOSAGE B', forme: 'GELULE', posologie: 'Instruction synthétique courte B.' }),
    ],
  },
  {
    id: 'dense-8-lignes',
    medications: Array.from({ length: 8 }, (_, i) => med(i + 1, {
      posologie: 'Instruction synthétique dense ' + String(i + 1).padStart(2, '0') + ' — matin / midi / soir — durée test.',
    })),
  },
  {
    id: 'stress-texte-long',
    medications: [
      med(1, { nom: 'MEDICAMENT TEST AU NOM VOLONTAIREMENT TRES LONG POUR VALIDATION VISUELLE', dosage: 'DOSAGE TEST LONG', forme: 'FORME TEST LONGUE', posologie: longInstruction, quantite: 12 }),
      med(2, { nom: 'MEDICAMENT TEST COMPLEMENTAIRE LONG', dosage: 'DOSAGE B', forme: 'COMPRIME', posologie: longInstruction }),
      { nom: 'EXAMEN RADIO TEST COMPLEXE', dosage: '', forme: '', posologie: longInstruction, type: 'EXAMEN', quantite: null, quantite_explicit: false },
    ],
  },
];
const ordonnanceGateReport = {
  productHead: process.env.PRODUCT_HEAD || null,
  patientDossier: patient.numero_dossier,
  scenarios: [],
};
for (const scenario of ordonnanceScenarios) {
  const response = await api.post('/api/documents/generate?archive=false&preview=true&force=false', {
    headers: { ...headers, 'Content-Type': 'application/json' },
    data: {
      type: 'ordonnance',
      patient_id: patient.id,
      is_accounted: false,
      payment_status: 'EN_ATTENTE',
      data: {
        medications: scenario.medications,
        doc_date: '2026-09-20',
        show_legal_annotations: true,
      },
    },
  });
  if (!response.ok()) throw new Error('ordonnance gate ' + scenario.id + ' generation failed ' + response.status() + ' ' + await response.text());
  const payload = await response.json();
  if (!payload.pdf_url) throw new Error('ordonnance gate ' + scenario.id + ' missing pdf_url');
  const clean = String(payload.pdf_url).replace(/^\//, '').replace(/^api\//, '');
  const pdf = await api.get('/api/' + clean, { headers });
  if (!pdf.ok()) throw new Error('ordonnance gate ' + scenario.id + ' fetch failed ' + pdf.status());
  const bytes = await pdf.body();
  if (bytes.length < 5 || bytes.subarray(0,4).toString('ascii') !== '%PDF') throw new Error('ordonnance gate ' + scenario.id + ' invalid PDF');
  const file = scenario.id + '.pdf';
  fs.writeFileSync(path.join(ordonnanceGateDir, file), bytes);
  ordonnanceGateReport.scenarios.push({
    id: scenario.id,
    medicationCount: scenario.medications.length,
    bytes: bytes.length,
    signature: bytes.subarray(0,4).toString('ascii'),
    pdfFile: file,
  });
}
fs.writeFileSync(path.join(ordonnanceGateDir, 'gate-matrix.json'), JSON.stringify(ordonnanceGateReport, null, 2));
console.log('ORDONNANCE_PDF_GATE_PASS', JSON.stringify(ordonnanceGateReport));

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

  let procedureSafetyRequests = 0;
  await page.route('**/api/prescriptions/clinical-rules/procedure-safety/alert/**', async route => {
    if (route.request().method() !== 'GET') return route.continue();
    procedureSafetyRequests += 1;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'BLOCKED',
        alert_key: 'CONTEXT_REQUIRED',
        read_only: true,
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

  await selectExactAmoxicillin(page);
  const safetyNotice = page.locator('[data-procedure-safety-notice="subtle"]');
  await safetyNotice.waitFor({ state: 'visible', timeout: 10000 });
  if (await safetyNotice.getAttribute('data-alert-key') !== 'CONTEXT_REQUIRED') {
    throw new Error('Procedure safety notice did not expose CONTEXT_REQUIRED');
  }
  if (procedureSafetyRequests < 1) throw new Error('Procedure safety read-only endpoint was not queried');
  actions.push('procedure-safety-readonly');

  const finalScene = await snapshot(page, viewport, 'actions-final');
  if (openScene.overflow || finalScene.overflow) throw new Error('Horizontal overflow detected');
  if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);
  if (http5xx.length) throw new Error(`HTTP 5xx: ${JSON.stringify(http5xx)}`);

  evidence.push({ viewport, actions, openScene, finalScene, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();

const expectedActions = 6;
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
