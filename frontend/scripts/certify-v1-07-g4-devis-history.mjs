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
  await manual.click();
  let descriptions = page.getByPlaceholder('Rechercher ou saisir un acte...');
  let prices = page.getByPlaceholder('0.00');
  await descriptions.last().fill('Détartrage G4 ' + viewport.width);
  await prices.last().fill('500');
  await manual.click();
  descriptions = page.getByPlaceholder('Rechercher ou saisir un acte...');
  prices = page.getByPlaceholder('0.00');
  await descriptions.last().fill('Bridge G4 ' + viewport.width);
  await prices.last().fill('1800');
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
  await page.waitForURL(url => new URL(url).searchParams.get('tab') === 'admin', { timeout: 10000 });
  await page.getByRole('button', { name: 'Document Libre', exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const libreTitle = page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...');
  await libreTitle.waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForFunction(expected => {
    const input = document.querySelector('input[placeholder="Ex: ORDONNANCE, LETTRE..."]');
    return input instanceof HTMLInputElement && input.value === expected;
  }, marker, { timeout: 10000 });
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
