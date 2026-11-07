// RESTORE-03 FUE-I: real React and actual authenticated FastAPI.
 // All data are synthetic; no route interception and no frozen/apply operations.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha = process.env.FUE_HEAD || '';
const password = process.env.T2_PASSWORD;
assert.match(sha, /^[0-9a-f]{40}$/);
assert.ok(password && process.env.ENVIRONMENT === 'test' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1' &&
  process.env.DATABASE_URL === 'sqlite:///./t2-runtime-cert.db',
  'FUE lab must use only the disposable T2 database');
const apiBase = 'http://127.0.0.1:8005';
const uiBase = 'http://127.0.0.1:5173';
const output = path.resolve('../artifacts/restore03-fue-i');
await fs.mkdir(output, { recursive: true });
const report = {
  head: sha, marker: 'RESTORE03_REAL_UI_FASTAPI_FUE_I_NONDESTRUCTIVE',
  actualReact: true, actualFastAPI: true, backendMocked: false,
  routeIntercepted: false, syntheticOnly: true, database: 'T2_DISPOSABLE_SQLITE',
  frozenExe: false, fullRestoreApplied: false, deployed: false,
  clinicalGo: false, humanVisualApproval: false,
  pass: false, checks: [], screenshots: [], failure: null,
};
const check = (name, viewport = '') => report.checks.push({ name, viewport, status: 'PASS' });
const browser = await chromium.launch({ headless: true });
const setup = await request.newContext({ baseURL: apiBase });
const contexts = [];
const errors = [];
const downloadBytes = async (download) => {
  const filename = download.suggestedFilename();
  assert.ok(filename.endsWith('.db.enc'), 'Actual encrypted SQLite download required');
  const bytes = await fs.readFile(await download.path());
  assert.ok(bytes.length > 200, 'Empty encrypted backup');
  // Fernet tokens have a stable ASCII transport envelope; do not retain bytes.
  assert.ok(bytes.subarray(0, 2).toString('ascii') === 'gA');
  return bytes;
};
async function token(email) {
  const r = await setup.post('/api/auth/login', {
    form: { username: email, password },
  });
  assert.equal(r.status(), 200, 'Real JWT login for ' + email);
  const data = await r.json();
  assert.ok(data.access_token);
  return data.access_token;
}
const screenshot = async (page, name) => {
  await page.screenshot({
    path: path.join(output, name + '.png'), fullPage: true, animations: 'disabled',
  });
  report.screenshots.push(name + '.png');
};
let owner, staff;
try {
  owner = await token('t2-browser@cabinet.ma');
  const cookieState = await enrollT2Workstation(setup, owner, password);
  const cookies = cookieState.cookies.filter(x => x.name === 'dc_workstation');
  assert.equal(cookies.length, 1, 'Real workstation cookie mandatory');
  staff = await token('t2-restricted@cabinet.ma');
  const ownerApi = await request.newContext({
    baseURL: apiBase, extraHTTPHeaders: { Authorization: 'Bearer ' + owner },
    storageState: { cookies, origins: [] },
  });
  const staffApi = await request.newContext({
    baseURL: apiBase, extraHTTPHeaders: { Authorization: 'Bearer ' + staff },
  });
  contexts.push(ownerApi, staffApi);
  const patientsBeforeResponse = await ownerApi.get('/api/patients/');
  assert.equal(patientsBeforeResponse.status(), 200);
  const patientIds = list => list.map(x => [x.id, x.numero_dossier]).sort((a,b)=>a[0]-b[0]);
  const beforePatientIds = patientIds(await patientsBeforeResponse.json());
  check('real-owner-JWT-and-workstation-cookie');
  const denied = await staffApi.post('/api/admin/restore/preflight', {
    multipart: { backup: { name: 'denied.db.enc',
      mimeType: 'application/octet-stream', buffer: Buffer.from('REJECT_SYNTHETIC') } },
  });
  assert.equal(denied.status(), 403, 'Staff cannot stage a restore');
  check('staff-denied-real-HTTP-403');

  for (const viewport of [
    { width: 1440, height: 1000 }, { width: 390, height: 1000 },
  ]) {
    const label = String(viewport.width);
    const context = await browser.newContext({
      viewport, acceptDownloads: true, reducedMotion: 'reduce', serviceWorkers: 'block',
      storageState: { cookies, origins: [] },
    });
    contexts.push(context);
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', e => pageErrors.push(String(e).slice(0, 130)));
    await page.goto(uiBase + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
    await page.locator('input[type=password]').fill(password);
    await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
    await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 60000 });
    await page.goto(uiBase + '/settings', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.getByRole('heading', { name: 'Paramètres', exact: true }).waitFor({ timeout: 30000 });
    await page.getByRole('button', { name: 'Sécurité & Backup', exact: true }).click();
    await page.getByText('Restauration guidée', { exact: true }).waitFor({ state: 'visible' });
    check('real-React-settings-authenticated-' + label, label);
    await screenshot(page, label + '-before');
    const [download, exportResponse] = await Promise.all([
      page.waitForEvent('download', { timeout: 90000 }),
      page.waitForResponse(r => new URL(r.url()).pathname === '/api/admin/export-db' &&
        r.request().method() === 'GET', { timeout: 90000 }),
      page.getByRole('button', { name: 'Créer et télécharger la sauvegarde' }).click(),
    ]);
    assert.equal(exportResponse.status(), 200);
    const encrypted = await downloadBytes(download);
    check('real-UI-encrypted-backup-export-' + label, label);

    const preflightPromise = page.waitForResponse(r =>
      new URL(r.url()).pathname === '/api/admin/restore/preflight' &&
      r.request().method() === 'POST', { timeout: 120000 });
    await page.locator('input[type=file]').setInputFiles({
      name: 'FUE-SYNTHETIC-RESTORE.db.enc',
      mimeType: 'application/octet-stream',
      buffer: encrypted,
    });
    const preflightResponse = await preflightPromise;
    assert.equal(preflightResponse.status(), 200);
    const preflight = await preflightResponse.json();
    assert.equal(preflight.status, 'preflight_ready');
    assert.equal(preflight.compatible, true);
    assert.equal(preflight.restore_database, true);
    assert.equal(preflight.restore_media, false);
    assert.match(preflight.restore_id, /^[0-9a-f]{32}$/);
    await page.getByText('Préflight validé', { exact: true }).waitFor();
    await screenshot(page, label + '-preflight');
    check('real-HTTP-preflight-compatible-no-media-' + label, label);

    const preparedPromise = page.waitForResponse(r =>
      new URL(r.url()).pathname.endsWith('/restore/' + preflight.restore_id + '/prepare') &&
      r.request().method() === 'POST', { timeout: 120000 });
    await page.getByRole('button', { name: 'Préparer la restauration' }).click();
    const prepareResponse = await preparedPromise;
    assert.equal(prepareResponse.status(), 200);
    const prepared = await prepareResponse.json();
    assert.equal(prepared.status, 'prepared');
    const job = await ownerApi.get('/api/admin/restore/' + preflight.restore_id + '/status');
    assert.equal(job.status(), 200);
    assert.equal((await job.json()).status, 'prepared');
    await page.getByText('Préparation sécurisée validée.', { exact: false }).first().waitFor();
    await screenshot(page, label + '-prepared');
    check('real-prepared-rescue-snapshot-and-GET-status-' + label, label);

    const applyButton = page.getByRole('button', { name: 'Redémarrer et restaurer' });
    assert.equal(await applyButton.isDisabled(), true);
    const confirmation = page.getByPlaceholder('RESTAURER');
    await confirmation.fill('restaurer');
    assert.equal(await applyButton.isDisabled(), true, 'Wrong case must not arm apply');
    await confirmation.fill('RESTAURER');
    assert.equal(await applyButton.isEnabled(), true);
    const blockedPromise = page.waitForResponse(r =>
      new URL(r.url()).pathname.endsWith('/restore/' + preflight.restore_id + '/apply') &&
      r.request().method() === 'POST', { timeout: 30000 });
    await applyButton.click();
    const blocked = await blockedPromise;
    assert.equal(blocked.status(), 409, 'Source process MUST refuse actual apply');
    await page.getByText(/Apply hors-processus disponible uniquement/).first().waitFor();
    await screenshot(page, label + '-apply-refused');
    const stillPrepared = await ownerApi.get('/api/admin/restore/' + preflight.restore_id + '/status');
    assert.equal((await stillPrepared.json()).status, 'prepared');
    check('confirmation-gated-and-source-apply-409-no-mutation-' + label, label);

    const cancelPromise = page.waitForResponse(r =>
      new URL(r.url()).pathname.endsWith('/restore/' + preflight.restore_id) &&
      r.request().method() === 'DELETE', { timeout: 30000 });
    await page.getByRole('button', { name: 'Fermer ce préflight' }).click();
    assert.equal((await cancelPromise).status(), 200);
    const deleted = await ownerApi.get('/api/admin/restore/' + preflight.restore_id + '/status');
    assert.equal(deleted.status(), 404, 'Cancelling must remove staged job');
    check('real-cancel-cleans-staging-' + label, label);

    const invalidResponsePromise = page.waitForResponse(r =>
      new URL(r.url()).pathname === '/api/admin/restore/preflight' &&
      r.request().method() === 'POST', { timeout: 30000 });
    await page.locator('input[type=file]').setInputFiles({
      name: 'INVALID-SYNTHETIC.db.enc',
      mimeType: 'application/octet-stream',
      buffer: Buffer.from('NOT_A_DIGITAL_CROWN_ENCRYPTED_BACKUP'),
    });
    const invalidResponse = await invalidResponsePromise;
    assert.equal(invalidResponse.status(), 400, 'Invalid backup must fail closed');
    assert.equal(await page.getByRole('button', { name: 'Préparer la restauration' }).count(), 0);
    await screenshot(page, label + '-invalid-refused');
    check('invalid-backup-denied-HTTP-400-no-prepare-' + label, label);
    assert.deepEqual(pageErrors, [], 'No uncaught browser errors in real FUE');
    const overflowing = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
    assert.equal(overflowing, false, 'No full-page horizontal overflow at ' + label);
    check('page-no-overflow-no-JS-errors-' + label, label);
  }
  const afterPatientIds = patientIds(await (await ownerApi.get('/api/patients/')).json());
  assert.deepEqual(afterPatientIds, beforePatientIds, 'Synthetic patient identities must not change');
  check('patient-record-ids-preserved-before-after');
  const health = await setup.get('/health');
  assert.equal(health.status(), 200);
  assert.equal((await health.json()).db, 'ok');
  check('real-backend-healthy-after-all-FUE');
  report.pass = true;
} catch (error) {
  report.failure = { type: error?.constructor?.name || 'Error',
    code: String(error?.code || 'FUE_ASSERTION'), /* never write credentials or API response */ };
  throw error;
} finally {
  for (const c of contexts.reverse()) {
    try {
      if (typeof c.close === 'function') await c.close();
      else if (typeof c.dispose === 'function') await c.dispose();
    } catch { /* disposable T2 cleanup; report persists */ }
  }
  await setup.dispose().catch(() => {});
  await browser.close();
  await fs.writeFile(path.join(output, 'report.json'),
    JSON.stringify(report, null, 2) + '
', 'utf8');
}
if (!report.pass || report.checks.length < 19 || report.screenshots.length !== 10) {
  throw new Error('RESTORE03_FUE_INCOMPLETE');
}
console.log('RESTORE03_REAL_UI_FASTAPI_FUE_I_NONDESTRUCTIVE_PASS ' +
  report.checks.length + ' checks / ' + report.screenshots.length + ' screenshots / ' + sha);
