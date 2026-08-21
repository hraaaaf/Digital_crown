import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const mode = process.env.CATALOG_CERT_MODE || 'after';
const outDir = path.resolve(process.env.CATALOG_CERT_OUT || '../artifacts/catalog-connected/after');
fs.mkdirSync(outDir, { recursive: true });
const viewports = [1440, 768, 390, 360, 320].map((width) => ({ width, height: 1200 }));

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password: 'T2BrowserPass123!' } });
if (!login.ok()) throw new Error(`login failed ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error(`patients failed ${patients.status()}`);
const patient = (await patients.json()).find((row) => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('fixture patient T2-0001 missing');

let certAct = null;
if (mode === 'after') {
  let catalogResponse = await api.get('/api/catalog/specialties', { headers });
  if (!catalogResponse.ok()) throw new Error(`catalog read failed ${catalogResponse.status()} ${await catalogResponse.text()}`);
  const catalog = await catalogResponse.json();
  let specialty = catalog.find((row) => row.name === 'Certification Catalogue');
  if (!specialty) {
    const created = await api.post('/api/catalog/specialties', { headers, data: { name: 'Certification Catalogue', color: '#64748B' } });
    if (!created.ok()) throw new Error(`specialty create failed ${created.status()} ${await created.text()}`);
    specialty = await created.json();
  }
  certAct = (specialty.acts || []).find((row) => row.code === 'CERT-CONNECT-001');
  if (!certAct) {
    const created = await api.post(`/api/catalog/specialties/${specialty.id}/acts`, {
      headers,
      data: { name: 'Détartrage catalogue certifié', code: 'CERT-CONNECT-001', base_price: 500, color: '#0F766E', is_active: true },
    });
    if (!created.ok()) throw new Error(`act create failed ${created.status()} ${await created.text()}`);
    certAct = await created.json();
  } else {
    const reset = await api.put(`/api/catalog/acts/${certAct.id}`, { headers, data: { name: 'Détartrage catalogue certifié', base_price: 500, is_active: true } });
    if (!reset.ok()) throw new Error(`act reset failed ${reset.status()} ${await reset.text()}`);
  }

  const masterUrl = `/api/patients/${patient.id}/master-plan`;
  const assistant = 'Catalogue cabinet · Certification Catalogue · CERT-CONNECT-001 · 500 DH · Tarif capturé';
  const payload = [{
    title: 'Détartrage catalogue certifié', assistant, status: 'pending', date_str: 'À planifier', order_index: 0,
    catalog_snapshot: { act_id: certAct.id, code: 'CERT-CONNECT-001', name: 'Détartrage catalogue certifié', price: 500 },
  }];
  const saved = await api.put(masterUrl, { headers, data: payload });
  if (!saved.ok()) throw new Error(`master snapshot save failed ${saved.status()} ${await saved.text()}`);
  let plan = await saved.json();
  if (plan?.steps?.[0]?.catalog_snapshot?.price !== 500) throw new Error('snapshot price not persisted');

  const mutate = await api.put(`/api/catalog/acts/${certAct.id}`, { headers, data: { base_price: 650, is_active: false } });
  if (!mutate.ok()) throw new Error(`catalog mutation failed ${mutate.status()} ${await mutate.text()}`);
  const reread = await api.get(masterUrl, { headers });
  plan = await reread.json();
  if (!reread.ok() || plan?.steps?.[0]?.catalog_snapshot?.price !== 500) throw new Error('historical snapshot followed catalog mutation');

  payload[0].status = 'done';
  payload[0].date_str = 'Fait le 21/08/2026';
  const statusUpdate = await api.put(masterUrl, { headers, data: payload });
  if (!statusUpdate.ok()) throw new Error(`historical status update while disabled failed ${statusUpdate.status()} ${await statusUpdate.text()}`);
  const statusPlan = await statusUpdate.json();
  if (statusPlan?.steps?.[0]?.catalog_snapshot?.price !== 500 || statusPlan?.steps?.[0]?.status !== 'done') {
    throw new Error('historical snapshot/status round-trip mismatch');
  }
  const reactivate = await api.put(`/api/catalog/acts/${certAct.id}`, { headers, data: { base_price: 650, is_active: true } });
  if (!reactivate.ok()) throw new Error(`catalog reactivate failed ${reactivate.status()} ${await reactivate.text()}`);
  fs.writeFileSync(path.join(outDir, 'snapshot-proof.json'), JSON.stringify({ actId: certAct.id, originalSnapshotPrice: 500, catalogPriceAfter: 650, historyUpdateWhileActDisabled: true, planSnapshotPriceAfter: 500, status: 'done' }, null, 2));
}

const browser = await chromium.launch({ headless: true });
const evidence = [];
for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('response', (response) => { if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() }); });
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });

  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=clinical`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Espace Clinique', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  if (mode === 'after') {
    await page.getByText('Ajouter un acte au plan', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    await page.getByText('Tarif figé', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    const search = page.getByPlaceholder('Rechercher nom, code ou spécialité…');
    await search.fill('CERT-CONNECT-001');
    await page.getByRole('button', { name: /Détartrage catalogue certifié/ }).click();
    if (await page.getByLabel('Nom retenu').inputValue() !== 'Détartrage catalogue certifié') throw new Error('selected name not prefilled');
    if (await page.getByLabel('Tarif DH').inputValue() !== '650') throw new Error('current catalog price not prefilled');
  }
  await page.waitForTimeout(300);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const shot = `${mode}-clinical-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: true });
  evidence.push({ viewport, shot, overflow, pageErrors, http5xx });
  await context.close();
}
await browser.close();
await api.dispose();

const invalid = evidence.flatMap((row) => [
  ...(row.overflow ? [{ viewport: row.viewport, reason: 'overflow' }] : []),
  ...row.pageErrors.map((error) => ({ viewport: row.viewport, reason: `pageerror:${error}` })),
  ...row.http5xx.map((item) => ({ viewport: row.viewport, reason: `http5xx:${item.status}:${item.url}` })),
]);
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify({ mode, evidence, invalid }, null, 2));
if (invalid.length) throw new Error(`catalog connected visual evidence invalid: ${JSON.stringify(invalid)}`);
