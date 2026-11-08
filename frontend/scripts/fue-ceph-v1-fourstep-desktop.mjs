/** 
 * Céphalo V1 cross-step FUE-I: real Cabinet browser / disposable synthetic T2.
 * This is a diagnostic exploratory test, NOT ten certified §74 FUE, clinical
 * validation, signature, or permission to archive unsigned official reports.
 * A failing assertion is a useful product finding and must not be suppressed.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
const fixture = JSON.parse(process.env.P2TER_STUDIES || '{}');
const assert = (condition, message) => { if (!condition) throw Error(message); };
assert(process.env.ENVIRONMENT === 'test' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1' &&
  /^[a-f0-9]{40}$/.test(head || '') && password &&
  [fixture.patient_id, fixture.older_id, fixture.latest_id].every(Number.isSafeInteger),
  'Cross-step test requires immutable HEAD, JWT and synthetic disposable T2 DB');
const root = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
const out = path.resolve('../artifacts/ceph-v1-fourstep-fue');
await fs.mkdir(out, { recursive: true });
const report = {
  head, classification: 'EXPERIMENTAL_FUE_I_CROSSSTEP', fixture: 'synthetic T2 only',
  purpose: 'Find the first real UI/API/SQLite seam that breaks Step1→2→3→4→reopen',
  excluded: ['real patient', 'clinical validity', 'non-synthetic modality import',
    'independent clinical sign-off', 'signed archive', 'certified full §74 10/10',
    'production install', 'DICOM/TWAIN/hot folder', 'mobile/PWA'],
  clinical_release: false, official_archival_allowed: false,
  viewport: '1280x900', checks: [], screenshots: [], errors: [],
  complete: false, outcome: 'NOT_RUN',
};
const browser = await chromium.launch({ headless: true });
const api = await request.newContext({ baseURL: backend });
let context, page;
async function shot(label) {
  if (!page) return;
  const file = label + '.png';
  await page.screenshot({
    path: path.join(out, file), fullPage: false, animations: 'disabled'
  });
  report.screenshots.push(file);
}
async function check(id, fn) {
  try {
    const evidence = await fn();
    report.checks.push({ id, status: 'PASS', evidence: evidence ?? null });
    console.log('CEPH_FOURSTEP_PASS', id);
    return evidence;
  } catch (err) {
    const message = String(err);
    report.checks.push({ id, status: 'FAIL', error: message });
    report.errors.push(id + ': ' + message);
    await shot('failure-' + id.toLowerCase()).catch(() => undefined);
    console.log('CEPH_FOURSTEP_FAIL', id, message);
    throw err;
  }
}
const select = async (study) => {
  await page.getByRole('button', { name: 'Historique', exact: true }).click();
  await page.locator('[data-cephalo-history-analysis-id="' + study + '"]')
    .waitFor({ state: 'visible', timeout: 30000 });
  await page.locator('[data-cephalo-history-analysis-id="' + study + '"]').click();
  await page.locator('[data-cephalo-selected-analysis-id="' + study + '"]')
    .waitFor({ state: 'visible', timeout: 30000 });
};
const field = (label) => page.getByText(label, { exact: true })
  .locator('xpath=../..').locator('input[type="number"]');
const step = (label) => page.getByRole('button', { name: label, exact: true }).click();
try {
  const login = await api.post('/api/auth/login', {
    form: { username: 't2-browser@cabinet.ma', password }
  });
  assert(login.status() === 200, 'Disposable T2 JWT bootstrap failed: ' + login.status());
  const token = (await login.json()).access_token;
  const enrolled = await enrollT2Workstation(api, token, password);
  const cookies = enrolled.cookies.filter(c => c.name === 'dc_workstation');
  assert(cookies.length === 1, 'T2 local workstation cookie missing');
  context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    acceptDownloads: true, reducedMotion: 'reduce',
    storageState: { cookies, origins: [] }
  });
  page = await context.newPage();
  page.on('pageerror', err => report.errors.push('REACT_ERROR: ' + err.message));

  await check('LOGIN_REAL_CABINET', async () => {
    await page.goto(root + '/hub?select=1', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('[data-hub-experience="cabinet"]').click();
    await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
    await page.locator('input[type=password]').fill(password);
    await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
    await page.waitForURL(u => new URL(u).pathname === '/dashboard', { timeout: 45000 });
    assert(await page.evaluate(() => Boolean(localStorage.getItem('token'))), 'No real browser JWT');
    await page.goto(root + '/patients/' + fixture.patient_id + '?tab=radiology&radioTab=cephalo',
      { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('[data-ortho-workspace-title]').waitFor({ state: 'visible', timeout: 35000 });
    return { browser_jwt: true, patient_id: fixture.patient_id };
  });
  await check('STEP1_EXPLICIT_SOURCE_STUDY', async () => {
    await select(fixture.older_id);
    await shot('01-real-study');
    return { selected_id: fixture.older_id, two_studies_fixture: true };
  });
  await check('STEP2_DDM_MANUAL_NO_FICTITIOUS_REAL_DDM', async () => {
    await step('Passer aux moulages');
    await page.getByText('DDM Maxillaire', { exact: true }).waitFor({ state: 'visible' });
    assert(await page.getByText('DDM Réelle Totale', { exact: true }).count() === 0,
      'Nonvalidated clinical-to-cephalo angle→mm conversion displayed as DDM réelle');
    await field('DDM Maxillaire').fill('2.4');
    await field('DDM Mandibulaire').fill('-1.2');
    assert((await field('DDM Maxillaire').inputValue()) === '2.4', 'Maxillary DDM UI lost');
    assert((await field('DDM Mandibulaire').inputValue()) === '-1.2', 'Mandibular DDM UI lost');
    assert(await page.getByText('DDM Réelle Totale', { exact: true }).count() === 0,
      'Unapproved angle→mm correction should fail closed with nonzero DDM inputs');
    await shot('02-moulages-ddm');
    return { maxillary: 2.4, mandibular: -1.2, real_ddm: 'UNAVAILABLE' };
  });
  await check('STEP3_PROVENANCE_AND_UNVERIFIED_DIAGNOSIS', async () => {
    await step('Passer à la synthèse');
    const com = page.getByRole('button', { name: 'COM Digital Crown', exact: true });
    const steiner = page.getByRole('button', { name: 'Steiner complet (1953 + 1959)', exact: true });
    assert(await com.count() > 0 && await steiner.count() > 0,
      'V1 two-protocol clinician selection missing');
    const note = page.getByPlaceholder(/^Note diagnostique libre/);
    await note.fill('SYNTHETIC_STEP3_NOTE_A_ONLY_UNVERIFIED');
    assert((await note.inputValue()).includes('UNVERIFIED'), 'Clinician editable note missing');
    await shot('03-diagnostic-unverified');
    return { protocols: ['COM', 'STEINER_1953_1959'], clinical_confirmation: false };
  });
  await check('STEP4_DOCUMENT_DRAFT_NOT_THERAPY_DECISION', async () => {
    await step('Préparer les documents et la stratégie');
    const clinical = page.locator('textarea[placeholder^="Saisie libre"]');
    await clinical.waitFor({ state: 'visible' });
    await clinical.fill('SYNTHETIC_STEP4_PLAN_A_ONLY_UNVERIFIED');
    assert(await page.getByRole('button', { name: 'Archivage suspendu' }).isDisabled(),
      'Unsigned A4 archive control must be disabled');
    assert(await page.getByRole('button', { name: 'Brouillon PDF' }).isEnabled(),
      'PDF draft must remain available');
    const hold = await page.getByTestId('unsigned-cephalo-archive-hold').innerText();
    assert(/brouillon non signé/i.test(hold), 'Unsigned status not explained');
    await shot('04-documents-plan-draft');
    return { clinical_confirmation: false, signed: false, archive_ui: 'DISABLED' };
  });
  const pdfEvidence = await check('A4_SAME_STUDY_REVISION_UNSIGNED_PDF', async () => {
    const waiter = page.waitForResponse(r => {
      const url = new URL(r.url());
      return url.pathname === '/api/patients/' + fixture.patient_id + '/pdf' &&
        r.request().method() === 'POST' && r.request().postDataJSON()?.archive === false;
    }, { timeout: 70000 });
    await page.getByRole('button', { name: 'Brouillon PDF' }).click();
    const response = await waiter;
    const submitted = response.request().postDataJSON();
    assert(response.status() === 200, 'Draft PDF HTTP ' + response.status());
    assert(submitted.analysis_id === fixture.older_id &&
      Number.isSafeInteger(submitted.expected_revision) &&
      submitted.expected_revision > 0 && submitted.archive === false,
      'Wrong study/revision/archive payload from Step4');
    assert(response.headers()['x-cephalo-analysis-id'] === String(fixture.older_id),
      'Wrong response X-Cephalo-Analysis-ID');
    assert(response.headers()['x-cephalo-revision'] === String(submitted.expected_revision),
      'Wrong response revision');
    const bytes = await response.body();
    assert(bytes.subarray(0, 4).toString('latin1') === '%PDF', 'Invalid PDF bytes');
    await fs.writeFile(path.join(out, 'fourstep-unsigned-draft.pdf'), bytes);
    await shot('05-draft-available');
    return { revision: submitted.expected_revision, bytes: bytes.length };
  });
  await check('OFFICIAL_ARCHIVE_DIRECT_HTTP_FAIL_CLOSED', async () => {
    const denied = await api.post('/api/patients/' + fixture.patient_id + '/pdf', {
      headers: { Authorization: 'Bearer ' + token },
      data: {
        analysis_id: fixture.older_id,
        expected_revision: pdfEvidence.revision,
        archive: true
      }
    });
    assert(denied.status() === 409, 'Unsigned official A4 returned ' + denied.status());
    return { http_status: denied.status(), archive_created: false };
  });
  await check('SAVE_CLINICAL_NOTES_WITHOUT_SIGNATURE', async () => {
    const waiter = page.waitForResponse(r => {
      const url = new URL(r.url());
      return url.pathname === '/api/ia/analyses/' + fixture.older_id &&
        r.request().method() === 'PUT';
    }, { timeout: 45000 });
    await page.getByRole('button', { name: 'Sauvegarder l’analyse céphalométrique' }).click();
    const response = await waiter;
    assert(response.status() === 200, 'Save clinical notes HTTP ' + response.status());
    return { notes_unverified: true, save_http: response.status() };
  });
  await check('SECOND_STUDY_HAS_NO_OLDER_CLINICAL_INPUTS', async () => {
    await select(fixture.latest_id);
    await step('Passer aux moulages');
    assert((await field('DDM Maxillaire').inputValue()) === '', 'A maxillary DDM leaked to B');
    assert((await field('DDM Mandibulaire').inputValue()) === '', 'A mandibular DDM leaked to B');
    await step('Passer à la synthèse');
    assert(!(await page.getByPlaceholder(/^Note diagnostique libre/).inputValue())
      .includes('SYNTHETIC_STEP3_NOTE_A_ONLY_UNVERIFIED'), 'A diagnosis text leaked to B');
    await step('Préparer les documents et la stratégie');
    assert(!(await page.locator('textarea[placeholder^="Saisie libre"]').inputValue())
      .includes('SYNTHETIC_STEP4_PLAN_A_ONLY_UNVERIFIED'), 'A plan text leaked to B');
    await shot('06-other-study-isolated');
    return { older_id: fixture.older_id, latest_id: fixture.latest_id, leak: false };
  });
  await check('REOPEN_ORIGINAL_STUDY_PERSISTED_VALUES', async () => {
    await select(fixture.older_id);
    await step('Passer aux moulages');
    assert((await field('DDM Maxillaire').inputValue()) === '2.4',
      'DDM maxilllary did not persist through SQLite study reopen');
    assert((await field('DDM Mandibulaire').inputValue()) === '-1.2',
      'DDM mandibular did not persist through SQLite study reopen');
    await step('Passer à la synthèse');
    assert((await page.getByPlaceholder(/^Note diagnostique libre/).inputValue())
      .includes('SYNTHETIC_STEP3_NOTE_A_ONLY_UNVERIFIED'),
      'Unverified diagnostic note did not persist through study reopen');
    await step('Préparer les documents et la stratégie');
    assert((await page.locator('textarea[placeholder^="Saisie libre"]').inputValue())
      .includes('SYNTHETIC_STEP4_PLAN_A_ONLY_UNVERIFIED'),
      'Unverified plan note did not persist through study reopen');
    await shot('07-original-reopened');
    return { persisted: true, still_unverified: true, official_archive: false };
  });
  assert(report.errors.filter(x => x.startsWith('REACT_ERROR:')).length === 0,
    'React errors: ' + JSON.stringify(report.errors));
  report.complete = true;
  report.outcome = 'CROSSSTEP_EXPERIMENTAL_AUTOMATED_SCOPE_PASS';
} catch (error) {
  report.outcome = 'CROSSSTEP_EXPERIMENTAL_BLOCKED';
  report.errors.push('RUN_STOPPED: ' + String(error));
} finally {
  await context?.close().catch(() => undefined);
  await api.dispose();
  await browser.close();
  await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
}
console.log('CEPH_V1_FOURSTEP_FUE_RESULT', JSON.stringify({
  head, outcome: report.outcome, check_count: report.checks.length,
  failures: report.checks.filter(x => x.status === 'FAIL'),
  screenshots: report.screenshots.length
}));
assert(report.complete && report.outcome === 'CROSSSTEP_EXPERIMENTAL_AUTOMATED_SCOPE_PASS',
  'Four-step FUE did not pass. Read artifact report.json: ' + report.errors.join(' | '));
