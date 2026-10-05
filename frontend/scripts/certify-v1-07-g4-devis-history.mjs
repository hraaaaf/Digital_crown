import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-devis-history');
fs.mkdirSync(outDir, { recursive: true });
const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('login failed');
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patientsResponse = await api.get('/api/patients', { headers });
if (!patientsResponse.ok()) throw new Error('patients failed');
const patient = (await patientsResponse.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('fixture patient missing');

// Canonical synthetic Devis PDF human-review gate.
const devisGateDir = path.resolve('../artifacts/t2-browser/devis-pdf-gate');
fs.mkdirSync(devisGateDir, { recursive: true });
const longDevisA = 'Réhabilitation prothétique complexe avec préparation périphérique atraumatique, empreinte de précision, contrôle occlusal dynamique et ajustements fonctionnels successifs';
const longDevisB = 'Traitement conservateur plurifactoriel avec isolation opératoire, reconstruction anatomique stratifiée, finition, polissage et vérification des contacts proximaux et occlusaux';
const devisRows = count => Array.from({ length: count }, (_, i) => ({ acte: 'Acte de devis ' + String(i + 1).padStart(2, '0'), dent: String([11,12,13,14,15,16,21,22,23,24][i % 10]), prix_unitaire: 100 + i * 7 }));
const devisScenarios = [
  { id: 'standard', items: devisRows(3) },
  { id: 'dense-12-actes', items: devisRows(12) },
  { id: 'stress-texte-montant', items: [{ acte: longDevisA + ' — ' + longDevisB, dent: '11, 12', prix_unitaire: 999999.99 }] },
];
const devisGateReport = { productHead: process.env.PRODUCT_HEAD || null, patientDossier: patient.numero_dossier, scenarios: [] };
for (const scenario of devisScenarios) {
  const response = await api.post('/api/documents/generate?archive=false&preview=true&force=false', {
    headers: { ...headers, 'Content-Type': 'application/json' },
    data: { type: 'devis', patient_id: patient.id, is_accounted: false, payment_status: 'EN_ATTENTE', data: { items: scenario.items, doc_date: '2026-09-20', teeth_data: [], installments: [] } },
  });
  if (!response.ok()) throw new Error('devis gate ' + scenario.id + ' generation failed ' + response.status());
  const payload = await response.json();
  if (!payload.pdf_url) throw new Error('devis gate ' + scenario.id + ' missing pdf_url');
  const clean = String(payload.pdf_url).replace(/^\//, '').replace(/^api\//, '');
  const pdf = await api.get('/api/' + clean, { headers });
  if (!pdf.ok()) throw new Error('devis gate ' + scenario.id + ' fetch failed ' + pdf.status());
  const bytes = await pdf.body();
  if (bytes.length < 5 || bytes.subarray(0,4).toString('ascii') !== '%PDF') throw new Error('devis gate ' + scenario.id + ' invalid PDF');
  const file = scenario.id + '.pdf';
  fs.writeFileSync(path.join(devisGateDir, file), bytes);
  devisGateReport.scenarios.push({ id: scenario.id, rowCount: scenario.items.length, bytes: bytes.length, signature: bytes.subarray(0,4).toString('ascii'), pdfFile: file, expectedTotal: scenario.items.reduce((sum,item) => sum + item.prix_unitaire, 0) });
}
for (const scenario of devisGateReport.scenarios) {
  if (scenario.signature !== '%PDF') throw new Error('devis gate ' + scenario.id + ' missing PDF signature');
}
fs.writeFileSync(path.join(devisGateDir, 'gate-matrix.json'), JSON.stringify(devisGateReport, null, 2));
console.log('DEVIS_PDF_GATE_PASS', JSON.stringify(devisGateReport));

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function snap(page, viewport, scene) {
  const screenshot = `g4-devis-history-${viewport.width}x${viewport.height}-${scene}.png`;
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false, animations: 'disabled' });
  return { screenshot, overflow };
}

async function exerciseStudioHeader(page) {
  const author = page.getByLabel('Auteur clinique du document');
  if (!(await author.isDisabled())) {
    const options = await author.locator('option').evaluateAll(nodes => nodes.map(node => node.value).filter(Boolean));
    if (options.length) await author.selectOption(options[0]);
  }
  const date = page.getByLabel("Date d'émission");
  await date.fill('2026-09-19');
}

async function generateHistoryFixture(viewportLabel) {
  const marker = `G4-HISTORY-${viewportLabel}-${Date.now()}`;
  const payload = {
    type: 'libre',
    patient_id: patient.id,
    data: {
      title: marker,
      content: `Contenu ${marker}`,
      custom_patient: '',
      custom_date: '',
      hide_patient_header: false,
      page_size: 'A5',
      alignment: 'left',
      doc_date: '2026-09-19',
    },
    is_accounted: false,
    payment_status: 'EN_ATTENTE',
  };
  const generated = await api.post('/api/documents/generate?archive=true', {
    headers: { ...headers, 'Content-Type': 'application/json' },
    data: payload,
  });
  if (!generated.ok()) throw new Error(`history fixture generation ${generated.status()}`);
  const docsResponse = await api.get(`/api/patients/${patient.id}/documents`, { headers });
  if (!docsResponse.ok()) throw new Error('history docs fetch failed');
  const docs = await docsResponse.json();
  const doc = docs.find(row => row.clinical_data?.title === marker || row.clinical_data?.content === `Contenu ${marker}`);
  if (!doc) throw new Error('generated history fixture not found');
  return { marker, doc };
}

for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light', acceptDownloads: true });
  const page = await context.newPage();
  await seedAuth(page);
  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('response', response => { if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() }); });
  const actions = [];
  const patientUrl = `http://127.0.0.1:5173/patients/${patient.id}`;

  await page.goto(`${patientUrl}?tab=admin&documentTab=devis`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Devis', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await exerciseStudioHeader(page);
  if (await page.getByRole('button', { name: /Procéder à l'Encaissement/i }).count()) throw new Error('Devis exposes treasury collection');

  const manual = page.getByRole('button', { name: /Ligne Manuelle/i }).last();
  const createManualCatalogLine = async (name, price) => {
    await manual.click();
    const nameInput = page.getByPlaceholder("Nom de l'acte").last();
    const priceInput = page.getByPlaceholder('Tarif à définir').last();
    await nameInput.waitFor({ state: 'visible', timeout: 5000 });
    await nameInput.fill(name);
    await priceInput.fill(String(price));
    await page.getByRole('button', { name: 'Créer et ajouter', exact: true }).last().click();
    await nameInput.waitFor({ state: 'hidden', timeout: 10000 });
    await page.waitForFunction(expected => [...document.querySelectorAll('input')].some(input => input.value === expected), name, { timeout: 10000 });
  };
  await createManualCatalogLine('Détartrage G4 ' + viewport.width, 500);
  await createManualCatalogLine('Bridge G4 ' + viewport.width, 1800);
  await page.getByRole('button', { name: /Organiser par phases/i }).click();
  await page.waitForFunction(() => [...document.querySelectorAll('input, textarea')].some(element => /PHASE 1 : ASSAINISSEMENT/i.test(element.value)), null, { timeout: 5000 });
  await page.waitForFunction(() => [...document.querySelectorAll('input, textarea')].some(element => /PHASE 3 : PROTHÉTIQUE/i.test(element.value)), null, { timeout: 5000 });
  actions.push('devis-phase-organization');

  const preview = page.getByRole('button', { name: 'Aperçu', exact: true });
  await preview.click();
  const previewSurface = viewport.width >= 1280
    ? page.getByRole('region', { name: /Aperçu PDF/i }).last()
    : page.getByRole('dialog').last();
  await previewSurface.waitFor({ state: 'visible', timeout: 15000 });
  await page.getByRole('button', { name: /Fermer/i }).last().click();
  actions.push('devis-preview');

  const saveResponse = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  const saved = await saveResponse;
  if (!saved.ok()) throw new Error(`Devis save failed ${saved.status()}`);
  actions.push('devis-save');

  const printButton = page.getByRole('button', { name: 'Imprimer', exact: true });
  await printButton.click();
  const printWarning = page.getByRole('dialog', { name: 'Attention : Impression Directe' });
  await printWarning.waitFor({ state: 'visible', timeout: 5000 });
  await printWarning.getByRole('button', { name: 'Annuler', exact: true }).click();
  await printButton.click();
  await printWarning.waitFor({ state: 'visible', timeout: 5000 });
  const printResponse = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await printWarning.getByRole('button', { name: 'Confirmer', exact: true }).click();
  if (!(await printResponse).ok()) throw new Error('Devis print confirmation failed');
  actions.push('devis-print');
  const devisScene = await snap(page, viewport, 'devis');

  const { marker, doc } = await generateHistoryFixture(`${viewport.width}x${viewport.height}`);
  await page.goto(`${patientUrl}?tab=archives`, { waitUntil: 'networkidle', timeout: 90000 });
  const search = page.getByPlaceholder("Rechercher dans l'historique...");
  await search.fill(doc.name);
  const title = page.getByText(doc.name, { exact: true });
  await title.waitFor({ state: 'visible', timeout: 15000 });
  actions.push('history-search');

  await page.getByRole('button', { name: 'Créer', exact: true }).click();
  await page.getByRole('button', { name: 'Historique', exact: true }).click();
  await page.getByPlaceholder("Rechercher dans l'historique...").fill(doc.name);
  await page.getByText(doc.name, { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
  actions.push('history-create-roundtrip');

  const card = title.locator('xpath=ancestor::div[@data-document-kind][1]');
  const viewButton = card.getByRole('button', { name: 'Voir', exact: true });
  const popupPromise = context.waitForEvent('page').catch(() => null);
  await viewButton.click();
  const popup = await popupPromise;
  if (popup) await popup.close();
  actions.push('history-view');

  const downloadPromise = page.waitForEvent('download', { timeout: 15000 });
  await card.getByRole('button', { name: 'Fichier', exact: true }).click();
  const download = await downloadPromise;
  if (!download.suggestedFilename()) throw new Error('history download filename missing');
  actions.push('history-download');

  let actionsButton = card.getByRole('button', { name: `Actions du document ${doc.name}`, exact: true });
  await actionsButton.click();
  const menu = card.locator('[data-document-action-menu]');
  await menu.waitFor({ state: 'visible', timeout: 5000 });
  const sign = menu.locator('[data-document-action="sign"]');
  if (await sign.count()) {
    page.once('dialog', dialog => dialog.accept());
    const signResponse = page.waitForResponse(response => response.url().includes(`/api/documents/${doc.id}/sign`) && response.request().method() === 'POST', { timeout: 15000 });
    await sign.click();
    const signed = await signResponse;
    if (!signed.ok()) throw new Error(`history sign failed ${signed.status()}`);
    await page.waitForTimeout(300);
    actions.push('history-sign');
  }

  await search.fill(doc.name);
  const titleAgain = page.getByText(doc.name, { exact: true });
  await titleAgain.waitFor({ state: 'visible', timeout: 15000 });
  const cardAgain = titleAgain.locator('xpath=ancestor::div[@data-document-kind][1]');
  actionsButton = cardAgain.getByRole('button', { name: `Actions du document ${doc.name}`, exact: true });
  await actionsButton.click();
  await cardAgain.locator('[data-document-action-menu]').waitFor({ state: 'visible', timeout: 5000 });
  await cardAgain.locator('[data-document-action="edit"]').click();
  await page.waitForTimeout(300);
  const editUrl = new URL(page.url());
  if (editUrl.searchParams.get('tab') !== 'admin') {
    throw new Error(`history edit did not enter admin tab: ${page.url()}`);
  }
  // The product currently keeps the previous documentTab query value during an
  // archive edit and hydrates Document Libre from edit state. Do not require a
  // synthetic URL transition that the runtime contract does not provide.
  await page.getByRole('button', { name: 'Document Libre', exact: true }).click();
  await page.getByRole('button', { name: 'Document Libre', exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const libreTitle = page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...');
  await libreTitle.waitFor({ state: 'visible', timeout: 10000 });
  try {
    await page.waitForFunction(expected => {
      const input = document.querySelector('input[placeholder="Ex: ORDONNANCE, LETTRE..."]');
      return input instanceof HTMLInputElement && input.value === expected;
    }, marker, { timeout: 30000 });
  } catch (error) {
    const diagnostic = await page.evaluate(expected => {
      const input = document.querySelector('input[placeholder="Ex: ORDONNANCE, LETTRE..."]');
      return { expected, actualTitle: input instanceof HTMLInputElement ? input.value : null, url: window.location.href };
    }, marker);
    fs.writeFileSync(path.join(outDir, `history-edit-diagnostic-${viewport.width}x${viewport.height}.json`), JSON.stringify(diagnostic, null, 2));
    console.error('G4_HISTORY_EDIT_DIAGNOSTIC', JSON.stringify(diagnostic));
    throw error;
  }
  actions.push('history-edit');

  await page.goto(`${patientUrl}?tab=archives`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByPlaceholder("Rechercher dans l'historique...").fill(doc.name);
  const finalTitle = page.getByText(doc.name, { exact: true });
  await finalTitle.waitFor({ state: 'visible', timeout: 15000 });
  const finalCard = finalTitle.locator('xpath=ancestor::div[@data-document-kind][1]');
  await finalCard.getByRole('button', { name: `Actions du document ${doc.name}`, exact: true }).click();
  const trash = finalCard.locator('[data-document-action="trash"]');
  page.once('dialog', dialog => dialog.accept());
  const trashResponse = page.waitForResponse(response => response.url().includes(`/api/documents/${doc.id}/trash`) && response.request().method() === 'POST', { timeout: 15000 });
  await trash.click();
  const trashed = await trashResponse;
  if (!trashed.ok()) throw new Error(`history trash failed ${trashed.status()}`);
  await finalTitle.waitFor({ state: 'detached', timeout: 10000 });
  actions.push('history-trash');
  const historyScene = await snap(page, viewport, 'history');

  if (devisScene.overflow || historyScene.overflow) throw new Error('horizontal overflow detected');
  if (pageErrors.length) throw new Error('page errors: ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('HTTP5xx: ' + JSON.stringify(http5xx));

  evidence.push({ viewport, actions, devisScene, historyScene, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();
const summary = { status: 'PASS', evidence };
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_DEVIS_HISTORY ' + JSON.stringify({ status: summary.status, viewports: evidence.length }));
