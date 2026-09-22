import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-ui-truth-after');
fs.mkdirSync(outDir, { recursive: true });

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2 credentials required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('AFTER login failed');
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patients = await api.get('/api/patients', { headers });
const patient = (await patients.json()).find(x => x.numero_dossier === 'T2-0001');
if (!patient) throw new Error('AFTER patient missing');

const png = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEANmpCD8ongcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfUJxAYTIfIvQAAAAAElFTkSuQmCC',
  'base64'
);
const browser = await chromium.launch({ headless: true });
const evidence = [];

for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await page.addInitScript(({ a, r }) => {
    localStorage.setItem('token', a);
    localStorage.setItem('refresh_token', r || '');
    localStorage.setItem('appMode', 'prod');
  }, { a: tokens.access_token, r: tokens.refresh_token });

  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', e => pageErrors.push(String(e)));
  page.on('response', r => { if (r.status() >= 500) http5xx.push({ url: r.url(), status: r.status() }); });

  const base = `http://127.0.0.1:5173/patients/${patient.id}`;

  const seeded = await api.post(`/api/ia/upload-panoramic?patient_id=${patient.id}`, {
    headers,
    multipart: { file: { name: `g4-ui-after-${viewport.width}x${viewport.height}.png`, mimeType: 'image/png', buffer: png } }
  });
  if (!seeded.ok()) throw new Error(`AFTER panoramic seed failed for ${viewport.width}x${viewport.height}: ${seeded.status()}`);
  const seededAnalysis = await seeded.json();

  await page.goto(base + '?tab=admin&documentTab=echeancier', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Nouveau plan', exact: true }).click();
  const fieldAfter = async (labelText) => {
    return page.getByText(labelText, { exact: true }).locator('..').locator('input');
  };
  await (await fieldAfter('Montant Total Prévu (MAD)')).fill('1000');
  await (await fieldAfter('Avance (MAD)')).fill('200');
  await (await fieldAfter('Nbre Mensualités')).fill('2');
  await page.getByRole('button', { name: /Générer le tableau des échéances/i }).click();
  await page.locator('input[value="Mensualité 1"]').waitFor({ state: 'visible', timeout: 10000 });
  await page.getByRole('button', { name: 'Enregistrer le plan', exact: true }).waitFor({ state: 'visible' });
  await page.getByRole('button', { name: 'Générer PDF', exact: true }).waitFor({ state: 'visible' });
  if (await page.getByRole('button', { name: 'Enregistrer', exact: true }).count()) throw new Error('echeancier still exposes ambiguous footer Enregistrer');
  const echeancierShot = `after-echeancier-footer-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, echeancierShot), animations: 'disabled', fullPage: false });

  await page.goto(base + '?tab=radiology&radioTab=panoramic', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Historique', exact: true }).click();
  const history = page.locator('[data-m4b-history]');
  await history.waitFor({ state: 'visible', timeout: 15000 });
  await page.getByText('Corbeille récupérable', { exact: true }).waitFor({ state: 'visible' });
  await page.getByRole('button', { name: "Mettre l'examen panoramique à la corbeille", exact: true }).first().waitFor({ state: 'visible' });
  const trashShot = `after-panoramic-trash-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, trashShot), animations: 'disabled', fullPage: false });

  const seededDate = new Date(seededAnalysis.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  const seededRow = history.getByText(`Examen du ${seededDate}`, { exact: true }).locator('xpath=ancestor::div[contains(@class,"group")][1]').first();
  await seededRow.waitFor({ state: 'visible', timeout: 10000 });
  await seededRow.click();
  await page.getByText('Revue structurée', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  await page.getByText('Revue structurée', { exact: true }).click();

  const domainSelects = page.locator('select[aria-label^="Revue structurée — "]');
  if (await domainSelects.count() !== 8) throw new Error('structured review does not expose 8 domains');
  for (let i = 0; i < 8; i += 1) {
    if (await domainSelects.nth(i).inputValue() !== 'not_assessed') throw new Error('structured domain default is not not_assessed');
  }

  const question = `Question G4 AFTER ${viewport.width}`;
  const abnormalNote = `Observation G4 AFTER ${viewport.width}`;
  const answer = `Réponse G4 AFTER ${viewport.width}`;
  await page.locator('input[placeholder="Optionnelle"]').fill(question);
  await page.getByLabel("Qualité de l'examen panoramique").selectOption('diagnostic');
  await domainSelects.nth(0).selectOption('normal');
  await domainSelects.nth(1).selectOption('abnormal');
  await page.getByLabel(/Note — Restaurations/).fill(abnormalNote);
  await page.locator('textarea[placeholder="Optionnelle"]').fill(answer);

  const genP = page.waitForRequest(r => r.url().endsWith('/api/ia/generate-panoramic-report') && r.method() === 'POST', { timeout: 20000 });
  const respP = page.waitForResponse(r => r.url().endsWith('/api/ia/generate-panoramic-report') && r.request().method() === 'POST', { timeout: 20000 });
  await page.getByRole('button', { name: /VALIDER ET GÉNÉRER/i }).click();
  const genReq = await genP;
  const payload = genReq.postDataJSON();
  const genResp = await respP;
  if (!genResp.ok()) throw new Error(`structured report generation failed: ${genResp.status()}`);
  if (payload?.report_context?.dental_anomalies?.status !== 'normal') throw new Error('explicit normal domain missing from payload');
  if (payload?.report_context?.restorations?.status !== 'abnormal') throw new Error('explicit abnormal domain missing from payload');
  if (payload?.report_context?.restorations?.note !== abnormalNote) throw new Error('abnormal note not preserved in payload');
  if (payload?.report_context?.caries?.status !== 'not_assessed') throw new Error('untouched domain lost not_assessed state');

  const report = await genResp.json();
  if (!report?.report_narrative?.includes(question)) throw new Error('clinical question missing from generated report');
  if (!report?.report_narrative?.includes(abnormalNote)) throw new Error('abnormal note missing from generated report');
  if (!report?.report_narrative?.includes(answer)) throw new Error('clinical answer missing from generated report');

  const list = await api.get(`/api/ia/patients/${patient.id}/panoramic-analyses`, { headers });
  if (!list.ok()) throw new Error('structured persistence reload failed');
  const persisted = (await list.json()).find(x => x?.detections_data?.report_context?.clinical_question === question);
  if (!persisted) throw new Error('structured report context was not persisted');
  if (persisted.detections_data.report_context.restorations.note !== abnormalNote) throw new Error('persisted abnormal note changed');

  const structuredShot = `g4-panoramic-structured-report-after-${viewport.width}x${viewport.height}.png`;
  await page.getByRole('button', { name: 'Constatations', exact: true }).click();
  await page.getByText('Revue structurée', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  await page.screenshot({ path: path.join(outDir, structuredShot), animations: 'disabled', fullPage: false });

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  if (overflow) throw new Error('AFTER horizontal overflow');
  if (pageErrors.length) throw new Error('AFTER page errors: ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('AFTER HTTP5xx: ' + JSON.stringify(http5xx));

  evidence.push({ viewport, echeancierShot, trashShot, structuredShot, structuredDomains: 8 });
  await context.close();
}

await browser.close();
await api.dispose();
const summary = { status: 'PASS', phase: 'AFTER', evidence };
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_UI_TRUTH_AFTER ' + JSON.stringify(summary));
