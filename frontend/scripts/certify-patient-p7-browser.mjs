import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/p7-final');
fs.mkdirSync(outDir, { recursive: true });

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password: 'T2BrowserPass123!' },
});
if (!login.ok()) throw new Error(`P7 login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };

const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error(`P7 patients failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find((row) => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('P7 fixture patient T2-0001 missing');

const ortho = await api.patch(`/api/patients/${patient.id}/ortho`, {
  headers,
  data: { is_ortho_active: true },
});
if (!ortho.ok()) throw new Error(`P7 ortho activation failed: ${ortho.status()} ${await ortho.text()}`);

const odontoUrl = `/api/patients/${patient.id}/odontogram`;
const odontoBefore = await api.get(odontoUrl, { headers });
if (!odontoBefore.ok()) throw new Error(`P7 odontogram read failed: ${odontoBefore.status()} ${await odontoBefore.text()}`);
const currentOdonto = await odontoBefore.json();
const odontoPayload = {
  dentition_type: 'ADULT',
  state: {
    '11': { M: 'CARIES', D: 'HEALTHY', O: 'HEALTHY', V: 'HEALTHY', P: 'HEALTHY' },
  },
  expected_revision: currentOdonto?.revision ?? 0,
};
const odontoSave = await api.put(odontoUrl, { headers, data: odontoPayload });
if (!odontoSave.ok()) throw new Error(`P7 odontogram save failed: ${odontoSave.status()} ${await odontoSave.text()}`);
const odontoRead = await api.get(odontoUrl, { headers });
const odontoStored = await odontoRead.json();
if (!odontoRead.ok() || odontoStored?.state?.['11']?.M !== 'CARIES') throw new Error('P7 odontogram round-trip mismatch');

const conclusionMarker = 'P7 — conclusion praticien certifiée';
const conclusionUrl = `/api/patients/${patient.id}/clinical-conclusions`;
const conclusionSave = await api.post(conclusionUrl, {
  headers,
  data: {
    conclusion_text: conclusionMarker,
    proposal_text: 'Observation structurée P7',
    proposal_source: 'P7 certification',
  },
});
if (!conclusionSave.ok()) throw new Error(`P7 conclusion save failed: ${conclusionSave.status()} ${await conclusionSave.text()}`);
const conclusions = await api.get(conclusionUrl, { headers });
const conclusionRows = await conclusions.json();
if (!conclusions.ok() || !conclusionRows.some((row) => row.conclusion_text === conclusionMarker)) throw new Error('P7 conclusion round-trip mismatch');

const masterUrl = `/api/patients/${patient.id}/master-plan`;
const masterPayload = [
  { title: 'Étape P7 certifiée', assistant: 'general', status: 'pending', date_str: 'À planifier', order_index: 0 },
];
const masterSave = await api.put(masterUrl, { headers, data: masterPayload });
if (!masterSave.ok()) throw new Error(`P7 master plan save failed: ${masterSave.status()} ${await masterSave.text()}`);
const masterRead = await api.get(masterUrl, { headers });
const masterStored = await masterRead.json();
if (!masterRead.ok() || !Array.isArray(masterStored?.steps) || !masterStored.steps.some((row) => row.title === 'Étape P7 certifiée')) throw new Error('P7 master plan round-trip mismatch');
const revisions = await api.get(`${masterUrl}/revisions`, { headers });
if (!revisions.ok() || !(await revisions.json()).length) throw new Error('P7 master plan revision missing');

const onePixelPng = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZcWQAAAAASUVORK5CYII=', 'base64');
const rvgUrl = `/api/documents/patients/${patient.id}/rvg`;
const rvgUpload = await api.post(rvgUrl, {
  headers,
  multipart: {
    file: { name: 'p7-rvg.png', mimeType: 'image/png', buffer: onePixelPng },
    radio_type: 'rvg',
    tooth_number: '11',
    note: 'P7 certification',
  },
});
if (!rvgUpload.ok()) throw new Error(`P7 RVG upload failed: ${rvgUpload.status()} ${await rvgUpload.text()}`);
const uploadedRvg = await rvgUpload.json();
const rvgList = await api.get(rvgUrl, { headers });
const rvgRows = await rvgList.json();
if (!rvgList.ok() || !rvgRows.some((row) => row.id === uploadedRvg.id)) throw new Error('P7 RVG round-trip mismatch');
const rvgBlob = await api.get(`/api/documents/${uploadedRvg.id}/download`, { headers });
if (!rvgBlob.ok()) throw new Error(`P7 RVG download failed: ${rvgBlob.status()}`);

const billing = await api.get(`/api/accounting/actes-billing/patient/${patient.id}`, { headers });
if (!billing.ok()) throw new Error(`P7 billing read failed: ${billing.status()} ${await billing.text()}`);
const acte = (await billing.json())[0];
if (!acte?.id) throw new Error('P7 fixture Acte missing');
const payment = await api.post('/api/accounting/payments', {
  headers,
  data: {
    patient_id: patient.id,
    amount: 100,
    payment_method: 'ESPECES',
    acte_id: acte.id,
    installment_id: null,
    notes: 'P7 certification',
  },
});
if (!payment.ok()) throw new Error(`P7 payment failed: ${payment.status()} ${await payment.text()}`);
const paymentBody = await payment.json();
const snapshot = await api.get(`/api/patients/${patient.id}/financial-snapshot`, { headers });
const snapshotBody = await snapshot.json();
if (!snapshot.ok() || snapshotBody.total_collected < 100 || snapshotBody.remaining_due === null) throw new Error('P7 financial round-trip mismatch');

const revisionRowsResponse = await api.get(`${masterUrl}/revisions`, { headers });
const revisionRows = await revisionRowsResponse.json();
const persistence = {
  patientId: patient.id,
  odontogramRevision: odontoStored.revision,
  conclusionPersisted: true,
  masterPlanPersisted: true,
  masterPlanRevisionCount: revisionRows.length,
  rvgDocumentId: uploadedRvg.id,
  paymentId: paymentBody.id,
  financialSnapshot: snapshotBody,
};
fs.writeFileSync(path.join(outDir, 'persistence.json'), JSON.stringify(persistence, null, 2));

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function capture(page, viewport, surface, ready) {
  await ready();
  await page.waitForTimeout(450);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const shot = `p7-${surface}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: false });
  return { shot, overflow };
}

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);
  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('response', (response) => {
    if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() });
  });

  const results = [];
  const patientUrl = `http://127.0.0.1:5173/patients/${patient.id}`;

  await page.goto(patientUrl, { waitUntil: 'networkidle', timeout: 90000 });
  results.push({ surface: 'overview', ...(await capture(page, viewport, 'overview', async () => {
    await page.getByText('Prochaine action', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    await page.getByText('Situation financière', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    if (await page.getByText(/Risque:/).count()) throw new Error('P7 opaque risk summary still visible');
    if (await page.getByText('0/0', { exact: true }).count()) throw new Error('P7 false plan 0/0 visible');
  })) });

  await page.getByRole('button', { name: 'Clinique', exact: true }).click();
  results.push({ surface: 'clinical', ...(await capture(page, viewport, 'clinical', async () => {
    for (const label of ['Espace Clinique', 'Sécurité médicale', 'Dossier clinique', 'Master Plan']) {
      await page.getByText(label, { exact: true }).first().waitFor({ state: 'visible', timeout: 30000 });
    }
    if (await page.getByText(/Radar de Vigilance/i).count()) throw new Error('P7 legacy VigilanceRadar visible');
  })) });

  await page.getByRole('button', { name: 'Imagerie', exact: true }).click();
  const rvgTab = page.getByRole('button', { name: 'RVG', exact: true });
  const panoTab = page.getByRole('button', { name: 'Panoramique', exact: true });
  const cephTab = page.getByRole('button', { name: 'Céphalométrie', exact: true });
  for (const tab of [rvgTab, panoTab, cephTab]) await tab.waitFor({ state: 'visible', timeout: 30000 });

  await rvgTab.click();
  results.push({ surface: 'imaging-rvg', ...(await capture(page, viewport, 'imaging-rvg', async () => {
    await page.getByText(/Radiographies intra-orales|RVG/i).first().waitFor({ state: 'visible', timeout: 30000 });
  })) });

  await panoTab.click();
  results.push({ surface: 'imaging-panoramic', ...(await capture(page, viewport, 'imaging-panoramic', async () => {
    await page.getByText('Repérage dentaire automatique · validation praticien', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    if (await page.getByText(/Studio Panoramique IA|Intelligence Clinique IA|Détection SOTA|Zéro-Hallucination/).count()) throw new Error('P7 legacy panoramic AI label visible');
  })) });

  await cephTab.click();
  results.push({ surface: 'imaging-cephalo', ...(await capture(page, viewport, 'imaging-cephalo', async () => {
    await page.getByText('Studio Céphalométrique', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  })) });

  await page.goto(`${patientUrl}?tab=admin&documentTab=plan`, { waitUntil: 'networkidle', timeout: 90000 });
  results.push({ surface: 'documents-create', ...(await capture(page, viewport, 'documents-create', async () => {
    await page.getByRole('button', { name: 'Créer', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    const studio = page.getByLabel('Types de documents');
    await studio.waitFor({ state: 'visible', timeout: 30000 });
    for (const label of ['Ordonnance', 'Certificat', 'Devis', 'Note Honoraires', 'Suivi Paiement', 'Document Libre']) {
      if (await studio.getByRole('button', { name: label, exact: true }).count() !== 1) throw new Error(`P7 document tab missing: ${label}`);
    }
    if (await studio.getByRole('button', { name: 'Compagnon Diagnostique', exact: true }).count()) throw new Error('P7 Compagnon still exposed in Documents');
    if (new URL(page.url()).searchParams.get('documentTab') === 'plan') throw new Error('P7 legacy documentTab=plan not normalized');
  })) });

  await page.getByRole('button', { name: 'Historique', exact: true }).click();
  results.push({ surface: 'documents-history', ...(await capture(page, viewport, 'documents-history', async () => {
    await page.getByPlaceholder("Rechercher dans l'historique...").waitFor({ state: 'visible', timeout: 30000 });
  })) });

  await page.goto(patientUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Finances', exact: true }).click();
  results.push({ surface: 'finances', ...(await capture(page, viewport, 'finances', async () => {
    for (const label of ['Facturé', 'Encaissé', 'Reste dû', 'Prochaine échéance']) {
      await page.getByText(label, { exact: true }).first().waitFor({ state: 'visible', timeout: 30000 });
    }
    if (await page.getByText('Taux Recouvrement', { exact: true }).count()) throw new Error('P7 recovery KPI visible');
  })) });

  await page.goto('http://127.0.0.1:5173/patients/new', { waitUntil: 'networkidle', timeout: 90000 });
  results.push({ surface: 'add-patient', ...(await capture(page, viewport, 'add-patient', async () => {
    await page.getByText('Nouveau Patient', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    const sex = await page.locator('select[name="sexe"]').inputValue();
    if (sex !== '') throw new Error(`P7 Add Patient implicit sex: ${sex}`);
  })) });

  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}/edit`, { waitUntil: 'networkidle', timeout: 90000 });
  results.push({ surface: 'edit-patient', ...(await capture(page, viewport, 'edit-patient', async () => {
    await page.getByText('Mise à jour', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  })) });

  evidence.push({ viewport, surfaces: results, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();

const captures = evidence.reduce((total, row) => total + row.surfaces.length, 0);
const invalid = evidence.flatMap((row) => [
  ...row.surfaces.filter((surface) => surface.overflow).map((surface) => ({ viewport: row.viewport, surface: surface.surface, reason: 'overflow' })),
  ...row.pageErrors.map((error) => ({ viewport: row.viewport, reason: 'pageerror', error })),
  ...row.http5xx.map((response) => ({ viewport: row.viewport, reason: 'http5xx', ...response })),
]);
const summary = {
  status: captures === 40 && invalid.length === 0 ? 'PASS' : 'FAIL',
  captures,
  expectedCaptures: 40,
  surfacesPerViewport: 10,
  viewports,
  invalid,
  persistence,
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('P7_FINAL_CERTIFICATION', JSON.stringify(summary));
if (summary.status !== 'PASS') process.exit(1);
