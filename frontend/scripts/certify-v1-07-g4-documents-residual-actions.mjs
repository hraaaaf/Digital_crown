
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-documents-residual');
fs.mkdirSync(outDir, { recursive: true });

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('G4 residual login failed');
const tokens = await login.json();
const headers = { Authorization: 'Bearer ' + tokens.access_token };
const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error('G4 residual patient list failed');
const patient = (await patients.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('G4 residual fixture patient missing');

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function gotoTab(page, tab) {
  const url = 'http://127.0.0.1:5173/patients/' + patient.id + '?tab=admin&documentTab=' + tab;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
}

async function noRuntimeFailure(page, pageErrors, http5xx, viewport, scene) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const shot = 'g4-residual-' + viewport.width + 'x' + viewport.height + '-' + scene + '.png';
  await page.screenshot({ path: path.join(outDir, shot), fullPage: false, animations: 'disabled' });
  if (overflow) throw new Error('Horizontal overflow: ' + scene);
  if (pageErrors.length) throw new Error('Page errors: ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('HTTP 5xx: ' + JSON.stringify(http5xx));
  return shot;
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

  const actions = [];

  // CERTIFICAT — all three types + conditional fields.
  await gotoTab(page, 'certificat');
  await page.getByRole('button', { name: 'Arrêt de travail', exact: true }).click();
  const start = page.locator('#certificate-rest-start');
  const days = page.getByLabel('Durée du repos en jours');
  await start.fill('2026-10-01');
  await days.fill('5');
  if (await days.inputValue() !== '5') throw new Error('Certificate duration edit failed');

  await page.getByRole('button', { name: 'Présence au cabinet', exact: true }).click();
  if (await page.getByLabel('Durée du repos en jours').count()) throw new Error('Presence certificate kept work-stop duration controls');

  await page.getByRole('button', { name: 'Certificat médical', exact: true }).click();
  const freeCertificate = page.getByPlaceholder('Rédigez librement le contenu certifié par le praticien...');
  await freeCertificate.fill('Certification G4 navigateur — contenu praticien');
  if (await freeCertificate.inputValue() !== 'Certification G4 navigateur — contenu praticien') throw new Error('Free certificate content edit failed');

  const certPreview = page.getByRole('button', { name: 'Aperçu', exact: true });
  await certPreview.click();
  const certClose = page.getByRole('button', { name: 'Fermer', exact: true });
  await certClose.waitFor({ state: 'visible', timeout: 30000 });
  await certClose.click();
  actions.push('certificate-types-fields-preview');

  // DEVIS — specific phase organization + shared accounting behavior.
  await gotoTab(page, 'devis');
  await page.getByRole('button', { name: /Ligne Manuelle/i }).last().click();
  const d1 = page.getByPlaceholder('Rechercher ou saisir un acte...').last();
  const p1 = page.getByPlaceholder('0.00').last();
  await d1.fill('Extraction simple');
  await p1.fill('600');

  await page.getByRole('button', { name: /Ligne Manuelle/i }).last().click();
  const descriptions = page.getByPlaceholder('Rechercher ou saisir un acte...');
  const prices = page.getByPlaceholder('0.00');
  await descriptions.last().fill('Couronne Zircone Premium');
  await prices.last().fill('3500');

  const organize = page.getByRole('button', { name: /Organiser par phases/i });
  await organize.click();
  const phaseSeparators = page.locator('input[placeholder="Rechercher ou saisir un acte..."]:disabled');
  if (!(await phaseSeparators.count())) throw new Error('Devis phase organization produced no disabled phase separator');
  const phaseValues = await phaseSeparators.evaluateAll(nodes => nodes.map(node => node.value));
  if (!phaseValues.some(value => /^--- .+ ---$/.test(value))) throw new Error('Devis phase separator format missing');
  actions.push('devis-manual-lines-phase-sequencing');

  // SUIVI PAIEMENT — create balanced plan, save, persisted row controls.
  await gotoTab(page, 'echeancier');
  await page.getByRole('button', { name: 'Nouveau plan', exact: true }).click();
  await page.getByPlaceholder('Ex: Plan de paiement').fill('Plan G4 navigateur');

  const planRoot = page.locator('#installment-studio-container');
  const numberInputs = planRoot.locator('input[type="number"]');
  if (await numberInputs.count() < 5) throw new Error('Installment numeric controls missing');

  await numberInputs.nth(0).fill('1000');
  await numberInputs.nth(1).fill('200');
  const dateInputs = planRoot.locator('input[type="date"]');
  await dateInputs.first().fill('2026-10-01');
  await numberInputs.nth(2).fill('2');
  await page.getByRole('button', { name: /Générer le tableau des échéances/i }).click();

  await page.getByText('Total équilibré', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const savePlan = page.getByRole('button', { name: 'Enregistrer le plan', exact: true });
  if (await savePlan.isDisabled()) throw new Error('Balanced installment plan still disabled');
  await savePlan.click();
  await page.getByText(/Plan enregistré #/).waitFor({ state: 'visible', timeout: 15000 });

  const persistedRows = planRoot.locator('tbody tr');
  if (await persistedRows.count() < 1) throw new Error('No persisted installment rows after save');

  const firstRow = persistedRows.first();
  const paymentSelect = firstRow.locator('select');
  if (!(await paymentSelect.count())) throw new Error('Persisted installment payment mode missing');
  await paymentSelect.selectOption('ESPECES');

  const reminder = firstRow.locator('input[type="checkbox"]');
  if (!(await reminder.count())) throw new Error('Persisted installment reminder control missing');
  await reminder.check();
  const whatsapp = firstRow.getByTitle('Ouvrir WhatsApp avec le rappel prérempli');
  await whatsapp.waitFor({ state: 'visible', timeout: 5000 });
  await page.evaluate(() => {
    window.__g4OpenedUrls = [];
    window.open = (url) => {
      window.__g4OpenedUrls.push(String(url || ''));
      return null;
    };
  });
  await whatsapp.click();
  const openedUrls = await page.evaluate(() => window.__g4OpenedUrls || []);
  if (!openedUrls.some(urlValue => urlValue.startsWith('https://wa.me/'))) throw new Error('WhatsApp reminder action did not build wa.me URL');

  const collect = firstRow.getByRole('button', { name: 'Encaisser', exact: true });
  if (await collect.isDisabled()) throw new Error('Installment collect remained disabled after explicit payment mode');
  await collect.click();
  await firstRow.getByText('PAYÉ', { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
  actions.push('installment-generate-save-reminder-collect');

  // LIBRE — controls not already covered by P6.
  await gotoTab(page, 'libre');
  const libreTitle = 'G4 Libre résiduel ' + viewport.width;
  await page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...').fill(libreTitle);
  await page.getByPlaceholder('Ex: À qui de droit...').fill('À qui de droit');
  await page.getByPlaceholder('Ex: Rabat, le 12/05/2026').fill('Rabat, le 19/09/2026');
  const hideHeader = page.locator('#hideHeader');
  await hideHeader.check();

  for (const label of ['Gauche', 'Centre', 'Droite', 'Justifié']) {
    await page.getByRole('button', { name: label, exact: true }).click();
  }

  const editor = page.getByPlaceholder("Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte.");
  await editor.fill('Texte G4');
  await editor.selectText();
  for (const title of ['Gras', 'Italique', 'Souligné', 'Agrandir']) {
    await page.getByTitle(title).click();
    await page.waitForTimeout(25);
  }
  await page.getByTitle('Tableau').click();
  await page.waitForTimeout(25);
  const editorValue = await editor.inputValue();
  for (const marker of ['<b>', '<i>', '<u>', '<font size="16">', '| Colonne 1 |']) {
    if (!editorValue.includes(marker)) throw new Error('Libre toolbar marker missing: ' + marker);
  }
  actions.push('libre-recipient-date-header-alignment-toolbar');

  // HISTORIQUE — act on the exact Libre document created by this viewport pass.
  const archiveResponsePromise = page.waitForResponse(response =>
    response.request().method() === 'POST' && response.url().includes('/api/documents/generate?archive=true'),
    { timeout: 30000 },
  );
  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  const archiveResponse = await archiveResponsePromise;
  if (!archiveResponse.ok()) throw new Error('Libre archive request failed');

  const docsAfter = await api.get('/api/patients/' + patient.id + '/documents', { headers });
  if (!docsAfter.ok()) throw new Error('History reconciliation fetch failed');
  const generated = (await docsAfter.json()).find(doc =>
    doc.clinical_data?.title === libreTitle
  );
  if (!generated) throw new Error('New Libre archive not found by exact clinical title');

  await page.goto('http://127.0.0.1:5173/patients/' + patient.id + '?tab=archives', { waitUntil: 'networkidle', timeout: 90000 });
  const searchHistory = page.getByPlaceholder("Rechercher dans l'historique...");
  await searchHistory.fill(generated.name);

  const exactAction = page.getByRole('button', { name: 'Actions du document ' + generated.name, exact: true });
  await exactAction.waitFor({ state: 'visible', timeout: 30000 });
  let card = exactAction.locator('xpath=ancestor::div[@data-document-kind][1]');

  // Voir: real download API + browser-open path, with navigation neutralized.
  await page.evaluate(() => {
    window.__g4OpenedUrls = [];
    window.open = (url) => {
      window.__g4OpenedUrls.push(String(url || ''));
      return null;
    };
  });
  const viewResponsePromise = page.waitForResponse(response =>
    response.request().method() === 'GET' && response.url().includes('/api/documents/' + generated.id + '/download'),
    { timeout: 15000 },
  );
  await card.getByRole('button', { name: 'Voir', exact: true }).click();
  const viewResponse = await viewResponsePromise;
  if (!viewResponse.ok()) throw new Error('History view download API failed');
  const viewOpenUrls = await page.evaluate(() => window.__g4OpenedUrls || []);
  if (!viewOpenUrls.some(urlValue => urlValue.startsWith('blob:'))) throw new Error('History view did not open generated blob URL');

  // Fichier: actual browser download event.
  const browserDownload = page.waitForEvent('download', { timeout: 15000 });
  await card.getByRole('button', { name: 'Fichier', exact: true }).click();
  const download = await browserDownload;
  if (!download.suggestedFilename()) throw new Error('History file download has no filename');

  // Signature: generated canonical doc must expose practitioner signature action.
  await exactAction.click();
  let sign = card.locator('[data-document-action="sign"]');
  if (!(await sign.count())) throw new Error('Generated canonical document has no practitioner signature action');
  page.once('dialog', dialog => dialog.accept());
  await sign.click();
  await page.getByText('Signature praticien enregistrée', { exact: true }).waitFor({ state: 'visible', timeout: 15000 });

  // Edit: real action must restore a structured editable document.
  const actionAfterSign = page.getByRole('button', { name: 'Actions du document ' + generated.name, exact: true });
  await actionAfterSign.click();
  card = actionAfterSign.locator('xpath=ancestor::div[@data-document-kind][1]');
  await card.locator('[data-document-action="edit"]').click();
  await page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...').waitFor({ state: 'visible', timeout: 15000 });
  if ((await page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...').inputValue()) !== libreTitle) {
    throw new Error('History edit did not restore exact Libre title');
  }

  // Return to history, locate exact document again, then trash with explicit confirmation.
  await page.goto('http://127.0.0.1:5173/patients/' + patient.id + '?tab=archives', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByPlaceholder("Rechercher dans l'historique...").fill(generated.name);
  const actionForTrash = page.getByRole('button', { name: 'Actions du document ' + generated.name, exact: true });
  await actionForTrash.waitFor({ state: 'visible', timeout: 15000 });
  card = actionForTrash.locator('xpath=ancestor::div[@data-document-kind][1]');
  await actionForTrash.click();
  page.once('dialog', dialog => dialog.accept());
  await card.locator('[data-document-action="trash"]').click();
  await actionForTrash.waitFor({ state: 'hidden', timeout: 15000 });
  actions.push('history-search-view-download-sign-edit-trash');

  const shot = await noRuntimeFailure(page, pageErrors, http5xx, viewport, 'final');
  evidence.push({ viewport, actions, screenshot: shot, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();

const expectedActionGroups = 5;
for (const row of evidence) {
  if (row.actions.length !== expectedActionGroups) throw new Error('Residual action-group count mismatch');
}

const summary = {
  status: 'PASS',
  actionGroupsPerViewport: expectedActionGroups,
  totalActionGroupProofs: expectedActionGroups * evidence.length,
  evidence,
};
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_DOCUMENTS_RESIDUAL ' + JSON.stringify({ status: summary.status, totalActionGroupProofs: summary.totalActionGroupProofs }));
