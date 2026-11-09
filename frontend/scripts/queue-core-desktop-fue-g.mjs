/**
 * Digital Crown LOT08.2-B Browser FUE-G / LAB, synthetic data ONLY.
 *
 * Requires two independently started, loopback-only local processes:
 *   DIGITALCROWN_QUEUE_FUE_RUN=1 python -m queue_core.tests.desktop_lab_fue_server
 *   VITE_QUEUE_CORE_LAB_PREVIEW=true ... vite --host 127.0.0.1 --port 5173
 * Uses NO clinical DB, no actual patient identities, no production credentials.
 * Fails closed if root marker does not match. Screenshots outside git.
 */
import { chromium } from 'playwright-core';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const serverRoot = process.env.QUEUE_LAB_FUE_ROOT;
const evidence = process.env.QUEUE_LAB_EVIDENCE;
const marker = 'DIGITALCROWN_QUEUE_FUE_SYNTHETIC_ONLY_V1';
if (!serverRoot || !evidence || !path.isAbsolute(serverRoot) || !path.isAbsolute(evidence) ||
  path.basename(serverRoot).indexOf('dc-queue-fue-') !== 0 ||
  !existsSync(path.join(serverRoot, '.queue-fue-marker')) ||
  readFileSync(path.join(serverRoot, '.queue-fue-marker'), 'utf8').trim() !== marker ||
  !process.env.DIGITALCROWN_QUEUE_FUE_RUN || process.env.DIGITALCROWN_QUEUE_FUE_RUN !== '1') {
  throw new Error('FUE_SYNTHETIC_LAB_GUARD');
}

const executablePaths = [
  process.env.PLAYWRIGHT_CHROMIUM_PATH,
  'C:\\Users\\lenovo\\AppData\\Local\\ms-playwright\\chromium-1200\\chrome-win64\\chrome.exe',
  'C:\\Users\\lenovo\\AppData\\Local\\ms-playwright\\chromium-1200\\chrome-win\\chrome.exe',
].filter(Boolean);
const executablePath = executablePaths.find(x => existsSync(x));
if (!executablePath) throw new Error('CHROMIUM_EXECUTABLE_NOT_FOUND');

mkdirSync(evidence, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true, args: ['--no-first-run'] });
const start = performance.now();
const testResults = [];
const screenshotResults = [];
const errors = [];
const pass = (name, actual, expected) => {
  if (actual !== expected) throw new Error(name + ': expected ' + JSON.stringify(expected) + ' got ' + JSON.stringify(actual));
  testResults.push({ name, status: 'PASS' });
};
async function screenshot(page, title, width, height) {
  await page.setViewportSize({ width, height });
  await page.waitForTimeout(150);
  const filename = path.join(evidence, title + '-' + width + 'x' + height + '.png');
  const bytes = await page.screenshot({ path: filename, fullPage: true });
  const xOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
  if (xOverflow) throw new Error('HORIZONTAL_OVERFLOW_' + width);
  screenshotResults.push({ filename, sha256: createHash('sha256').update(bytes).digest('hex'), width, height });
}
async function login(page, username) {
  await page.getByRole('textbox', { name: 'Identifiant opérateur' }).fill(username);
  await page.getByLabel('Mot de passe').fill('SyntheticStaffPassword!!2026');
  const sessionReply = page.waitForResponse(
    r => r.url().endsWith('/v1/operators/session') && r.request().method() === 'POST',
    { timeout: 12000 },
  );
  await page.getByRole('button', { name: 'Se connecter' }).click();
  const response = await sessionReply;
  pass('login-status-' + username, response.status(), 200);
  const result = await response.json();
  await page.getByTestId('visit-V1').waitFor({ state: 'visible', timeout: 10000 });
  pass('login-browser-' + username, await page.getByText('Opérateur : ' + username).count(), 1);
  return result.token;
}
const base = 'http://127.0.0.1:5173/queue-core-fue.html';
try {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
  const page = await ctx.newPage();
  page.on('pageerror', err => errors.push('PAGE_ERROR:' + err.message));
  page.on('response', response => {
    if (response.status() >= 400) {
      const target = new URL(response.url());
      const expectedRevocation = response.status() === 401 &&
        target.pathname === '/api/queue-core-lab/v1/queues/Q1/snapshot';
      if (!expectedRevocation) errors.push('HTTP_' + response.status() + ':' + target.pathname);
    }
  });
  page.on('console', message => {
    if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) {
      errors.push('CONSOLE:' + message.text());
    }
  });
  await page.goto(base, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.getByTestId('queue-core-lab').waitFor({ timeout: 15000 });
  pass('page-visible-lab', await page.getByRole('heading', { name: 'Salle d’attente — laboratoire' }).count(), 1);
  pass('no-patient-identity', await page.getByText('Données synthétiques uniquement.', { exact: false }).count(), 1);
  await screenshot(page, 'before-login', 390, 844);
  await screenshot(page, 'before-login', 768, 1024);
  await screenshot(page, 'before-login', 1280, 900);

  await login(page, 'reception1');
  pass('initial-status', await page.getByTestId('status-V1').innerText(), 'PLANNED');
  await screenshot(page, 'reception-planned', 390, 844);
  await page.getByRole('button', { name: 'Enregistrer arrivée V1' }).click();
  await page.getByTestId('status-V1').getByText('WAITING').waitFor({ timeout: 10000 });
  pass('real-visit-checkin', await page.getByTestId('status-V1').innerText(), 'WAITING');
  pass('reception-hides-unauthorized-call', await page.getByRole('button', { name: 'Appeler V1' }).count(), 0);
  await page.getByRole('button', { name: 'Écouter SSE' }).click();
  await page.getByTestId('stream-status').getByText('SSE connecté').waitFor({ timeout: 12000 });
  await page.getByText('V1 ·', { exact: false }).first().waitFor({ timeout: 12000 });
  pass('sse-event-visible', (await page.getByRole('list', { name: 'Journal SSE' }).locator('li').count()) >= 2, true);
  await screenshot(page, 'reception-after-sse', 768, 1024);
  await page.getByRole('button', { name: 'Arrêter SSE' }).click();
  await page.getByRole('button', { name: 'Se déconnecter' }).click();
  await page.getByRole('button', { name: 'Se connecter' }).waitFor({ state: 'visible', timeout: 10000 });

  const staffToken = await login(page, 'chairman1');
  pass('staff-initial-waiting', await page.getByTestId('status-V1').innerText(), 'WAITING');
  pass('staff-hides-reception-checkin', await page.getByRole('button', { name: 'Enregistrer arrivée V2' }).count(), 0);
  await page.getByRole('button', { name: 'Appeler V1' }).click();
  await page.getByTestId('status-V1').getByText('CALLED').waitFor({ timeout: 12000 });
  pass('real-call', await page.getByTestId('status-V1').innerText(), 'CALLED');
  await page.getByRole('button', { name: 'Installer au fauteuil V1' }).click();
  await page.getByTestId('status-V1').getByText('CHAIR').waitFor({ timeout: 12000 });
  pass('real-chair', await page.getByTestId('status-V1').innerText(), 'CHAIR');
  await page.getByRole('button', { name: 'Terminer V1' }).click();
  await page.getByTestId('status-V1').getByText('DONE').waitFor({ timeout: 12000 });
  pass('real-done', await page.getByTestId('status-V1').innerText(), 'DONE');
  await screenshot(page, 'staff-after-done', 1280, 900);

  // Real browser connects an authenticated SSE GET. External local-admin
  // fixture revocation occurs while the staff browser session stays open.
  await page.getByRole('button', { name: 'Écouter SSE' }).click();
  await page.getByTestId('stream-status').getByText('SSE connecté').waitFor({ timeout: 12000 });
  await page.getByText('V1 ·', { exact: false }).first().waitFor({ timeout: 12000 });
  writeFileSync(path.join(serverRoot, 'REVOKE_STAFF_SYNTHETIC'), 'revoke\n');
  await page.waitForFunction(() => {
    return document.body.textContent?.includes('Flux SSE fermé') ||
      document.body.textContent?.includes('Flux SSE interrompu');
  }, null, { timeout: 12000 });
  pass('sse-closes-after-revocation', await page.getByTestId('queue-status').innerText(), 'Flux SSE fermé : reconnexion obligatoire');
  await page.getByRole('button', { name: 'Se connecter' }).waitFor({ timeout: 12000 });
  pass('revocation-hides-queue-immediately', await page.getByTestId('visit-V1').count(), 0);
  pass('revocation-clears-browser-session', await page.getByText('Flux SSE fermé : reconnexion obligatoire').count(), 1);
  const deniedStatus = await page.evaluate(async (token) => {
    const response = await fetch('http://127.0.0.1:18987/api/queue-core-lab/v1/queues/Q1/snapshot', {
      headers: { Authorization: 'Bearer ' + token }, cache: 'no-store', credentials: 'omit',
    });
    return response.status;
  }, staffToken);
  pass('revoked-next-request-401', deniedStatus, 401);
  await screenshot(page, 'revoked-session', 390, 844);
  if (errors.length) throw new Error('BROWSER_ERRORS:' + errors.join('|'));
  const durationS = Math.round((performance.now() - start) / 1000);
  const result = { status: 'PASS', durationS, checks: testResults, screenshots: screenshotResults, browserErrors: errors, clinicalData: 'NONE', install: 'NONE' };
  const target = path.join(evidence, 'fue-g-results.json');
  writeFileSync(target, JSON.stringify(result, null, 2));
  console.log('FUE_G_LAB_PASS ' + testResults.length + ' checks ' + screenshotResults.length + ' screenshots ' + durationS + 's');
  console.log('EVIDENCE ' + target);
  await ctx.close();
} catch (err) {
  console.error('FUE_G_LAB_FAIL', String(err));
  writeFileSync(path.join(evidence, 'fue-g-failure.txt'), String(err));
  process.exitCode = 1;
} finally {
  await browser.close();
}
