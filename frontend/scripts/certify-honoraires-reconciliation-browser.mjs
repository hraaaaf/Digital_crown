import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/honoraires-reconciliation');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };

const suffix = Date.now().toString().slice(-6);
const patientResp = await api.post('/api/patients/', {
  headers,
  data: {
    nom: `RECONCILIATION-${suffix}`,
    prenom: 'Honoraires',
    date_naissance: '1990-01-01',
    sexe: 'M',
    telephone: '0600000000',
  },
});
if (!patientResp.ok()) throw new Error(`Patient create failed: ${patientResp.status()} ${await patientResp.text()}`);
const patient = await patientResp.json();

const gen = await api.post('/api/documents/generate', {
  headers,
  data: {
    type: 'note',
    patient_id: patient.id,
    is_accounted: true,
    payment_status: 'PAYE',
    data: {
      payments: [
        { date: '2026-09-20', acte: 'Soin A certification', dent: '-', montant: 600, mode_reglement: 'ESPECES' },
        { date: '2026-09-20', acte: 'Soin B certification', dent: '-', montant: 400, mode_reglement: 'ESPECES' },
      ],
      doc_date: '2026-09-20',
      teeth_data: [],
    },
  },
});
if (!gen.ok()) throw new Error(`Honoraires generation failed: ${gen.status()} ${await gen.text()}`);

const beforeApi = await api.get(`/api/accounting/honoraires?patient_id=${patient.id}&year=2026&month=9`, { headers });
if (!beforeApi.ok()) throw new Error(`Before accounting failed: ${beforeApi.status()}`);
const beforeJson = await beforeApi.json();
if (beforeJson.items.length !== 2) throw new Error(`Expected 2 derived Acte rows, got ${beforeJson.items.length}`);
const archiveIds = [...new Set(beforeJson.items.map((item) => item.document_archive_id))];
if (archiveIds.length !== 1 || !archiveIds[0]) throw new Error(`Missing unique document_archive_id: ${JSON.stringify(archiveIds)}`);
const archiveId = archiveIds[0];

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage();
await page.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });

await page.goto('http://127.0.0.1:5173/accounting', { waitUntil: 'networkidle', timeout: 90000 });
await page.getByText(patient.nom, { exact: false }).first().waitFor({ timeout: 30000 });
await page.screenshot({ path: path.join(outDir, 'before-delete.png'), fullPage: true });

const patientRow = page.getByText(patient.nom, { exact: false }).first().locator('tr');
await patientRow.click();
await page.getByText('Soin A certification', { exact: true }).waitFor({ timeout: 10000 });
const detailRow = page.getByText('Soin A certification', { exact: true }).locator('tr');
await detailRow.getByTitle('Supprimer').click();
await page.getByText('Supprimer cette note définitivement ?', { exact: true }).waitFor({ timeout: 10000 });
await page.getByRole('button', { name: 'Confirmer', exact: true }).click();
await page.getByText(patient.nom, { exact: false }).first().waitFor({ state: 'detached', timeout: 30000 }).catch(() => {});
await page.waitForTimeout(700);
await page.screenshot({ path: path.join(outDir, 'after-delete.png'), fullPage: true });

const afterApi = await api.get(`/api/accounting/honoraires?patient_id=${patient.id}&year=2026&month=9`, { headers });
if (!afterApi.ok()) throw new Error(`After accounting failed: ${afterApi.status()}`);
const afterJson = await afterApi.json();
if (afterJson.items.length !== 0 || afterJson.total_amount !== 0 || afterJson.total_collected !== 0) {
  throw new Error(`Accounting not cleared: ${JSON.stringify(afterJson)}`);
}

const docs = await api.get(`/api/documents?patient_id=${patient.id}&include_deleted=true`, { headers });
let archiveStatus = null;
if (docs.ok()) {
  const payload = await docs.json();
  const list = Array.isArray(payload) ? payload : (payload.documents || payload.items || []);
  archiveStatus = list.find((item) => Number(item.id) === Number(archiveId))?.status ?? null;
}

const evidence = {
  productHead: process.env.GITHUB_SHA || null,
  patientId: patient.id,
  archiveId,
  before: {
    itemCount: beforeJson.items.length,
    totalAmount: beforeJson.total_amount,
    totalCollected: beforeJson.total_collected,
    allRowsPointToArchive: beforeJson.items.every((item) => Number(item.document_archive_id) === Number(archiveId)),
  },
  after: {
    itemCount: afterJson.items.length,
    totalAmount: afterJson.total_amount,
    totalCollected: afterJson.total_collected,
    archiveStatus,
  },
  screenshots: ['before-delete.png', 'after-delete.png'],
  pass:
    beforeJson.items.length === 2 &&
    beforeJson.items.every((item) => Number(item.document_archive_id) === Number(archiveId)) &&
    afterJson.items.length === 0 &&
    afterJson.total_amount === 0 &&
    afterJson.total_collected === 0,
};
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(evidence, null, 2));
if (!evidence.pass) throw new Error('Honoraires reconciliation browser certification failed');

await browser.close();
await api.dispose();
console.log('HONORAIRES_RECONCILIATION_BROWSER_PASS', JSON.stringify(evidence));
