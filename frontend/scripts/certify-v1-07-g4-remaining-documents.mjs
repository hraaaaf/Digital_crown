import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-remaining-documents');
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
  const screenshot = `g4-docs-${viewport.width}x${viewport.height}-${scene}.png`;
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false, animations: 'disabled' });
  return { screenshot, overflow };
}

async function fieldAfter(page, label) {
  const node = page.getByText(label, { exact: true }).first();
  const parent = node.locator('..');
  return parent.locator('input,select').first();
}

async function exerciseStudioHeader(page) {
  const author = page.getByLabel('Auteur clinique du document');
  if (!(await author.isDisabled())) {
    const options = await author.locator('option').evaluateAll(nodes => nodes.map(node => ({ value: node.value, text: node.textContent || '' })).filter(row => row.value));
    if (options.length) {
      await author.selectOption(options[0].value);
      if (await author.inputValue() !== options[0].value) throw new Error('author selection failed');
    }
  }
  const date = page.getByLabel("Date d'émission");
  await date.fill('2026-09-19');
  if (await date.inputValue() !== '2026-09-19') throw new Error('document date edit failed');
}

async function closeResidualPreview(page) {
  const overlay = page.locator('.document-studio-live-preview').last();
  if (!(await overlay.count()) || !(await overlay.isVisible())) return;
  const close = overlay.getByRole('button', { name: 'Fermer', exact: true });
  await close.waitFor({ state: 'visible', timeout: 5000 });
  await close.click();
  await overlay.waitFor({ state: 'hidden', timeout: 5000 });
}

async function exercisePreview(page) {
  const previewButton = page.getByRole('button', { name: 'Aperçu', exact: true });
  if (!(await previewButton.count())) {
    const closeToggle = page.getByRole('button', { name: 'Fermer', exact: true });
    if (await closeToggle.count()) {
      await closeToggle.last().click();
      await page.waitForTimeout(100);
    }
  }
  await previewButton.waitFor({ state: 'visible', timeout: 5000 });
  await previewButton.click();
  const desktopInline = await page.evaluate(() => window.matchMedia('(min-width: 1280px)').matches);
  const previewRoot = desktopInline
    ? page.locator('aside[data-ordonnance-desktop-preview="inline"]').last()
    : page.locator('.document-studio-live-preview').last();
  await previewRoot.waitFor({ state: 'visible', timeout: 15000 });
  const previewSurface = desktopInline
    ? previewRoot.getByRole('region', { name: /Aperçu PDF/ })
    : previewRoot.getByRole('dialog');
  await previewSurface.waitFor({ state: 'visible', timeout: 5000 });
  const refresh = previewSurface.getByRole('button', { name: 'Actualiser', exact: true });
  if (await refresh.count()) await refresh.click();
  await previewSurface.getByRole('button', { name: 'Fermer', exact: true }).click();
  await previewRoot.waitFor({ state: 'hidden', timeout: 5000 });
}

for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);
  const pageErrors = [];
  const ignoredPageErrors = [];
  const http5xx = [];
  page.on('pageerror', error => {
    const message = String(error);
    if (message.includes("Failed to read the 'localStorage' property from 'Window': Access is denied for this document.")) {
      ignoredPageErrors.push(message);
      return;
    }
    pageErrors.push(message);
  });
  page.on('response', response => { if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() }); });
  const base = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=`;
  const actions = [];

  await page.goto(base + 'certificat', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Certificat', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await closeResidualPreview(page);
  await exerciseStudioHeader(page);
  await page.getByRole('button', { name: /Arrêt de travail/i }).click();
  await page.getByLabel('Début du repos').fill('2026-10-02');
  await page.getByLabel('Durée du repos en jours').fill('4');
  if (await page.getByLabel('Durée du repos en jours').inputValue() !== '4') throw new Error('certificate duration failed');
  await page.getByRole('button', { name: /Présence au cabinet/i }).click();
  if (await page.getByLabel('Durée du repos en jours').count()) throw new Error('presence certificate still exposes duration');
  await page.getByRole('button', { name: /Certificat médical/i }).click();
  const freeCertificate = page.getByLabel(/Contenu du certificat médical/i);
  await freeCertificate.fill(`Contenu certifié G4 navigateur ${viewport.width}x${viewport.height}`);
  if (await freeCertificate.inputValue() !== `Contenu certifié G4 navigateur ${viewport.width}x${viewport.height}`) throw new Error('free certificate content failed');
  actions.push('certificate-types-fields');
  await exercisePreview(page);
  actions.push('certificate-preview-refresh-close');
  let responsePromise = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('certificate save failed');
  await freeCertificate.fill(`Contenu certifié G4 navigateur impression ${viewport.width}x${viewport.height}`);
  responsePromise = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Préparer impression', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('certificate prepare print failed');
  actions.push('certificate-save-prepare-print');
  const certScene = await snap(page, viewport, 'certificate');

  await page.goto(base + 'echeancier', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Suivi Paiement', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await exerciseStudioHeader(page);
  await page.getByRole('button', { name: 'Nouveau plan', exact: true }).click();
  const title = page.getByPlaceholder('Ex: Plan de paiement');
  await title.fill('Plan G4 navigateur');
  await (await fieldAfter(page, 'Montant Total Prévu (MAD)')).fill('1000');
  await (await fieldAfter(page, 'Avance (MAD)')).fill('200');
  await (await fieldAfter(page, 'Date Avance')).fill('2026-10-03');
  await (await fieldAfter(page, 'Nbre Mensualités')).fill('2');
  await page.getByRole('button', { name: /Générer le tableau des échéances/i }).click();
  await page.locator('input[value="Avance Initiale"]').waitFor({ state: 'visible', timeout: 5000 });
  await page.locator('input[value="Mensualité 1"]').waitFor({ state: 'visible', timeout: 5000 });
  await page.locator('input[value="Mensualité 2"]').waitFor({ state: 'visible', timeout: 5000 });
  await page.getByText('Total équilibré', { exact: true }).waitFor({ state: 'visible', timeout: 5000 });
  actions.push('installment-generate');

  await page.getByRole('button', { name: /Ajouter manuellement/i }).click();
  const manualRow = page.locator('input[value="Nouveau versement"]');
  await manualRow.waitFor({ state: 'visible' });
  await page.getByRole('button', { name: /Supprimer Nouveau versement/i }).click();
  if (await page.locator('input[value="Nouveau versement"]').count()) throw new Error('manual installment deletion failed');
  actions.push('installment-manual-add-remove');

  const save = page.getByRole('button', { name: 'Enregistrer le plan', exact: true });
  await save.waitFor({ state: 'visible' });
  if (await save.isDisabled()) throw new Error('balanced plan save remained disabled');
  await save.click();
  await page.getByText(/Plan enregistré #/).waitFor({ state: 'visible', timeout: 15000 });
  actions.push('installment-save');

  const installmentRoot = page.locator('#installment-studio-container:visible').last();
  await installmentRoot.waitFor({ state: 'visible', timeout: 5000 });
  const firstMethod = installmentRoot.locator('select[aria-label^="Mode de règlement"]').first();
  await firstMethod.selectOption('CARTE');
  const collect = installmentRoot.getByRole('button', { name: 'Encaisser', exact: true }).first();
  const collectDebug = await installmentRoot.evaluate((node) => ({
    dataPlan: node.getAttribute('data-plan-data'),
    collectButtons: Array.from(node.querySelectorAll('button')).filter(button => (button.textContent || '').trim() === 'Encaisser').map(button => ({
      disabled: button.disabled,
      text: (button.textContent || '').trim(),
    })),
    paymentMethods: Array.from(node.querySelectorAll('select[aria-label^="Mode de règlement"]')).map(select => ({
      label: select.getAttribute('aria-label'),
      value: select.value,
    })),
  }));
  console.log('G4_INSTALLMENT_PRECOLLECT ' + JSON.stringify({
    viewport: `${viewport.width}x${viewport.height}`,
    collectDebug,
  }));
  if (await collect.isDisabled()) throw new Error('collect remained disabled after method selection');
  await collect.evaluate((button) => {
    window.__g4CollectDomClicks = 0;
    button.addEventListener('click', () => { window.__g4CollectDomClicks += 1; }, { once: false });
  });
  const collectPutPromise = page.waitForResponse(response =>
    /\/api\/installments\/\d+$/.test(new URL(response.url()).pathname) &&
    response.request().method() === 'PUT',
    { timeout: 10000 }
  );
  await collect.click();
  let collectPutResponse;
  try {
    collectPutResponse = await collectPutPromise;
  } catch (error) {
    console.log('G4_INSTALLMENT_CLICK_DIAG ' + JSON.stringify({
      viewport: `${viewport.width}x${viewport.height}`,
      domClicks: await page.evaluate(() => window.__g4CollectDomClicks || 0),
      buttonVisible: await collect.isVisible(),
      buttonEnabled: await collect.isEnabled(),
      methodValue: await firstMethod.inputValue(),
      planData: await installmentRoot.getAttribute('data-plan-data'),
    }));
    throw error;
  }
  const collectPutBody = await collectPutResponse.json();
  const collectReloadResponse = await api.get(`/api/installments/patient/${patient.id}`, { headers });
  if (!collectReloadResponse.ok()) throw new Error('installment reload verification failed');
  const collectReloadBody = await collectReloadResponse.json();
  const reloadedPlan = Array.isArray(collectReloadBody)
    ? collectReloadBody.find(plan => Number(plan.id) === Number(collectPutBody.plan_id))
    : null;
  console.log('G4_INSTALLMENT_COLLECT_ACK ' + JSON.stringify({
    viewport: `${viewport.width}x${viewport.height}`,
    putStatus: collectPutResponse.status(),
    putBody: {
      id: collectPutBody.id,
      plan_id: collectPutBody.plan_id,
      status: collectPutBody.status,
    },
    reloadStatus: collectReloadResponse.status(),
    reloadedPlan: reloadedPlan ? {
      id: reloadedPlan.id,
      installmentStatuses: (reloadedPlan.installments || []).map(item => ({ id: item.id, status: item.status })),
    } : null,
  }));
  await page.getByText('PAYÉ', { exact: true }).first().waitFor({ state: 'visible', timeout: 10000 });
  actions.push('installment-collect');

  const reminder = page.locator('input[aria-label^="Activer rappel WhatsApp"]').last();
  await reminder.check();
  const wa = page.getByTitle('Ouvrir WhatsApp avec le rappel prérempli');
  await page.evaluate(() => {
    window.__g4OpenedUrl = null;
    window.open = (url) => { window.__g4OpenedUrl = String(url || ''); return null; };
  });
  await wa.click();
  const openedUrl = await page.evaluate(() => window.__g4OpenedUrl);
  if (!openedUrl || !openedUrl.startsWith('https://wa.me/')) throw new Error('WhatsApp reminder URL not produced');
  actions.push('installment-reminder');
  await exercisePreview(page);
  actions.push('installment-preview');
  const generatePdf = page.getByRole('button', { name: 'Générer PDF', exact: true });
  await generatePdf.click({ trial: true, timeout: 30000 });
  responsePromise = page.waitForResponse(response => response.url().includes('/api/installments/generate-preview') && response.request().method() === 'POST', { timeout: 30000 });
  await generatePdf.click();
  const installmentGenerateResponse = await responsePromise;
  if (!installmentGenerateResponse.ok()) throw new Error('installment footer generation failed');
  actions.push('installment-footer-generer-pdf-is-preview-only');
  await page.getByRole('button', { name: 'Imprimer', exact: true }).click();
  const warning = page.getByRole('dialog', { name: 'Attention : Impression Directe' });
  await warning.waitFor({ state: 'visible', timeout: 5000 });
  await warning.getByRole('button', { name: 'Annuler', exact: true }).click();
  await page.getByRole('button', { name: 'Imprimer', exact: true }).click();
  await warning.waitFor({ state: 'visible', timeout: 5000 });
  responsePromise = page.waitForResponse(response => response.url().includes('/api/installments/generate-preview') && response.request().method() === 'POST', { timeout: 30000 });
  await warning.getByRole('button', { name: 'Confirmer', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('installment print confirmation failed');
  actions.push('installment-save-print');
  const installmentScene = await snap(page, viewport, 'installment');

  await page.goto(base + 'libre', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Document Libre', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await closeResidualPreview(page);
  await exerciseStudioHeader(page);
  await page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...').fill(`Lettre G4 ${viewport.width}x${viewport.height}`);
  await page.getByPlaceholder('Ex: À qui de droit...').fill('À qui de droit');
  await page.getByPlaceholder('Ex: Rabat, le 12/05/2026').fill('Rabat, le 19/09/2026');
  await page.getByLabel(/Masquer l'en-tête patient/i).check();
  for (const name of ['A5','A4','Gauche','Centre','Droite','Justifié']) await page.getByRole('button', { name, exact: true }).click();
  const content = page.getByPlaceholder("Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte.");
  await content.fill(`Texte G4 ${viewport.width}x${viewport.height}`);
  for (const [titleName, token] of [['Gras','<b>'],['Italique','<i>'],['Souligné','<u>'],['Agrandir','<font size="16">']]) {
    await content.evaluate(el => { el.selectionStart = 0; el.selectionEnd = el.value.length; });
    await page.getByTitle(titleName).click();
    await page.waitForTimeout(30);
    if (!(await content.inputValue()).includes(token)) throw new Error('libre format failed: ' + titleName);
  }
  await page.getByRole('button',{name:'Tableau',exact:true}).click();
  if (!(await content.inputValue()).includes('| Colonne 1 |')) throw new Error('libre table insertion failed');
  actions.push('libre-residual-controls');
  await exercisePreview(page);
  actions.push('libre-preview-refresh-close');
  responsePromise = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('libre save failed');
  await content.fill((await content.inputValue()) + ' impression');
  responsePromise = page.waitForResponse(response => response.url().includes('/api/documents/generate') && response.request().method() === 'POST', { timeout: 30000 });
  await page.getByRole('button', { name: 'Préparer impression', exact: true }).click();
  if (!(await responsePromise).ok()) throw new Error('libre prepare print failed');
  actions.push('libre-save-prepare-print');
  const libreScene = await snap(page, viewport, 'libre');

  if ([certScene, installmentScene, libreScene].some(row => row.overflow)) throw new Error('horizontal overflow detected');
  if (pageErrors.length) throw new Error('page errors: ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('HTTP5xx: ' + JSON.stringify(http5xx));

  evidence.push({ viewport, actions, certScene, installmentScene, libreScene, pageErrors, ignoredPageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();
const summary = { status: 'PASS', evidence };
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_REMAINING_DOCUMENTS ' + JSON.stringify({ status: summary.status, viewports: evidence.length }));