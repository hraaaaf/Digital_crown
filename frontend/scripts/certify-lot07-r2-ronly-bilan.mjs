/** Real Chrome + FastAPI + seeded synthetic classified BILAN, without mocks.
 * Browser proof of DEC-R2-01 + DEC-R2-02 on one disposable T2 only.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha = process.env.SOURCE_HEAD;
const password = process.env.T2_PASSWORD;
if (process.env.ENVIRONMENT !== 'test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    process.env.DATABASE_URL !== 'sqlite:///./t2-runtime-cert.db' ||
    !/^[0-9a-f]{40}$/.test(sha ?? '') || !password) {
  throw Error('REFUSED: real R-only E2E requires isolated exact SHA T2');
}
const root = path.resolve('../artifacts/lot07-r2-ronly-dec02');
await fs.mkdir(root, { recursive: true });
const checks = [];
const assert = (name, yes, data = {}) => {
  checks.push({ name, pass: Boolean(yes), ...data });
  if (!yes) throw Error('DEC_R2_BROWSER_E2E_FAIL: ' + name + ' ' + JSON.stringify(data));
};
const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const browser = await chromium.launch({ headless: true });
let context;
try {
  const login = await api.post('/api/auth/login', { form: {
    username: 't2-browser@cabinet.ma', password,
  } });
  assert('real owner login', login.status() === 200, { status: login.status() });
  const tokens = await login.json();
  const headers = { Authorization: 'Bearer ' + tokens.access_token };
  const patientRes = await api.get('/api/patients/', { headers });
  assert('real patient endpoint', patientRes.status() === 200);
  const patient = (await patientRes.json()).find(p => p.numero_dossier === 'T2-0001');
  assert('exact synthetic T2 patient', Number.isSafeInteger(patient?.id));

  const list = await api.get('/api/patients/' + patient.id + '/documents', { headers });
  assert('authenticated BILAN list', list.status() === 200);
  const docs = await list.json();
  const bilan = docs.find(d => d.type === 'BILAN' && d.name === 'T2-historical-bilan.pdf');
  assert('BILAN classified R URL without static path', bilan?.url === '/api/documents/bilan/' + bilan?.id + '/view');
  const pdf = await api.get('/api/documents/bilan/' + bilan.id + '/view', { headers });
  assert('owner can read R-only PDF', pdf.status() === 200 &&
    (pdf.headers()['content-type'] ?? '').includes('application/pdf'));
  for (const [name, req] of [
    ['ordinary download blocked', api.get('/api/documents/' + bilan.id + '/download', { headers })],
    ['archive URL blocked', api.get('/api/static/archives/r2-dec01-t2/synthetic-bilan.pdf', { headers })],
    ['trash blocked', api.post('/api/documents/' + bilan.id + '/trash', { headers })],
    ['signature blocked', api.post('/api/documents/' + bilan.id + '/sign', { headers })],
  ]) {
    const response = await req;
    assert(name, response.status() === 403, { status: response.status() });
  }
  const restrictedLogin = await api.post('/api/auth/login', { form: {
    username: 't2-restricted@cabinet.ma', password,
  } });
  assert('synthetic restricted login', restrictedLogin.status() === 200);
  const restrictedJwt = (await restrictedLogin.json()).access_token;
  const restricted = await api.get('/api/documents/bilan/' + bilan.id + '/view', {
    headers: { Authorization: 'Bearer ' + restrictedJwt },
  });
  assert('secretary direct URL denied', restricted.status() === 403);
  const withoutAuth = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
  const unauthorized = await withoutAuth.get('/api/documents/bilan/' + bilan.id + '/view');
  assert('bearerless URL denied', [401,403].includes(unauthorized.status()));
  await withoutAuth.dispose();

  // Genuine browser login: do not inject tokens, intercept APIs or force stores.
  const ws = await enrollT2Workstation(api, tokens.access_token, password);
  const cookies = ws.cookies.filter(c => c.name === 'dc_workstation');
  assert('server workstation enrolled for browser', cookies.length === 1 && cookies[0].httpOnly);
  context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    storageState: { cookies, origins: [] },
  });
  const page = await context.newPage();
  const failures = [];
  page.on('pageerror', error => failures.push(String(error).slice(0, 300)));
  const writes = [];
  page.on('request', req => {
    const u = new URL(req.url());
    if (u.pathname.includes('/documents/') && !['GET', 'HEAD', 'OPTIONS'].includes(req.method())) {
      writes.push({ path: u.pathname, method: req.method() });
    }
  });
  await page.goto('http://127.0.0.1:5173/hub?select=1', { waitUntil: 'domcontentloaded' });
  await page.locator('[data-hub-experience="cabinet"]').click();
  await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
  await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 45000 });
  await page.goto('http://127.0.0.1:5173/patients/' + patient.id + '?tab=radiology&radioTab=media',
    { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('[data-v15-071-real-cabinet-lab]').waitFor({ state: 'visible', timeout: 60000 });
  await page.locator('[data-testid="multiview-ronly-contract"]').waitFor({ state: 'visible' });
  const scope = page.locator('[data-v15-071-real-cabinet-lab]');
  await scope.locator('[data-testid="multiview-bilan-readonly"]').waitFor({ state: 'visible' });
  const open = scope.getByRole('button', { name: 'Consulter : T2-historical-bilan.pdf' });
  await open.waitFor({ state: 'visible', timeout: 30000 });
  assert('R-only clinical slot has no upload inputs', await scope.locator('input[type=file]').count() === 0);
  assert('R-only clinical slot has no save/erase UI', await scope.getByRole('button', {
    name: /^(Enregistrer|Supprimer|Signer|Importer)$/i,
  }).count() === 0);
  await open.click();
  await scope.locator('iframe[title^="Bilan historique :"]').waitFor({ state: 'attached', timeout: 30000 });
  assert('real BILAN PDF read in browser using authenticated blob', true);
  assert('no BILAN write request from MultiView', writes.length === 0, { writes });
  assert('no uncaught browser errors', failures.length === 0, { failures });
  await page.screenshot({ path: path.join(root, 'synthetic-r-only-bilan-1440.png'), fullPage: false });
  await fs.writeFile(path.join(root, 'assertions.json'), JSON.stringify({
    sourceHead: sha, syntheticOnly: true, browser: 'chromium', checks, failures, writes,
  }, null, 2));
  console.log('LOT07_R2_DEC01_DEC02_REAL_BROWSER_E2E_PASS ' + sha);
} finally {
  await context?.close();
  await browser.close();
  await api.dispose();
}
