// LOT05: test the actual authenticated React App and FastAPI backend.main in disposable T2.
// No production data, import, Alembic PostgreSQL certification, or mobile Pocket claim.
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha = process.env.EVALUATED_SHA;
const password = process.env.T2_PASSWORD;
if (!/^[a-f0-9]{40}$/.test(sha || '') || !password ||
    process.env.ENVIRONMENT !== 'test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1') {
  throw new Error('LOT05_T2_ISOLATION_AND_EXACT_SHA_REQUIRED');
}
const base = 'http://127.0.0.1:8005';
const ui = 'http://127.0.0.1:5173';
const dest = path.resolve('../artifacts/v15-05-migration-appshell-t2');
const actors = [
  { name: 'owner', email: 't2-browser@cabinet.ma', allowed: true },
  { name: 'employed-admin', email: 't2-migration-employed-admin@cabinet.ma', allowed: false },
];
const sizes = [{ width: 390, height: 844 }, { width: 1280, height: 900 }];
const report = { sha, scope: 'real App.tsx + Sidebar + LoginPage and T2 backend.main',
  notCertified: ['real import', 'SQLCipher', 'full Alembic PostgreSQL', 'native zoom', 'Pocket'],
  checks: [], failures: [], pass: false };
await fs.mkdir(dest, { recursive: true });
const setup = await request.newContext({ baseURL: base });
const browser = await chromium.launch({ headless: true });
try {
  const login = await setup.post('/api/auth/login', {
    form: { username: actors[0].email, password },
  });
  if (login.status() !== 200) throw new Error('Owner enrollment login ' + login.status());
  const token = (await login.json()).access_token;
  if (!token) throw new Error('No owner JWT in test bootstrap');
  const storage = await enrollT2Workstation(setup, token, password);
  const cookies = storage.cookies.filter(x => x.name === 'dc_workstation');
  if (cookies.length !== 1) throw new Error('Expected one real workstation cookie');
  for (const viewport of sizes) for (const actor of actors) {
    const item = { viewport: viewport.width, actor: actor.name, login: false, sidebar: null, route: null };
    const context = await browser.newContext({
      viewport, reducedMotion: 'reduce', storageState: { cookies, origins: [] },
    });
    try {
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', err => errors.push(String(err).slice(0, 220)));
      await page.goto(ui + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.locator('input[type=email]').waitFor({ state: 'visible', timeout: 45000 });
      if (!await page.evaluate(() => !localStorage.getItem('token') && !localStorage.getItem('refresh_token'))) {
        throw new Error('Fresh browser already authenticated');
      }
      await page.locator('input[type=email]').fill(actor.email);
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
      await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 60000 });
      await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({ state: 'visible', timeout: 45000 });
      item.login = await page.evaluate(() => Boolean(localStorage.getItem('token')));
      if (!item.login) throw new Error('Not a real UI login');
      item.sidebar = await page.locator('a[href="/settings/migration"]').count() > 0;
      if (item.sidebar !== actor.allowed) throw new Error('Sidebar owner mismatch');
      await page.goto(ui + '/settings/migration', { waitUntil: 'domcontentloaded', timeout: 60000 });
      if (actor.allowed) {
        await page.locator('[data-testid="migration-studio"]').waitFor({
          state: 'visible', timeout: 45000,
        });
        item.route = new URL(page.url()).pathname === '/settings/migration';
        if (!await page.getByRole('button', { name: /Examiner les correspondances/i }).isDisabled()) {
          throw new Error('Review action enabled without mapping files');
        }
        const uploadLabels = page.locator('[data-testid="migration-studio"] label').filter({
          hasText: 'Choisir un fichier JSON',
        });
        if (await uploadLabels.count() !== 2) {
          throw new Error('Two French file selectors not rendered');
        }
        const firstLabel = uploadLabels.first();
        const inputId = await firstLabel.getAttribute('for');
        if (!inputId || await page.locator('input[type="file"]').first().getAttribute('id') !== inputId) {
          throw new Error('File selector label missing accessible input association');
        }
        // Verify the real label opens the browser file chooser, without uploading data.
        const chooser = page.waitForEvent('filechooser', { timeout: 10000 });
        await firstLabel.click();
        await chooser;
        await firstLabel.scrollIntoViewIfNeeded();
        await page.screenshot({
          path: path.join(dest, actor.name + '-' + viewport.width + '-upload.png'),
          animations: 'disabled',
        });
      } else {
        await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 45000 });
        // A URL redirect alone can show PageLoader; require real dashboard before screenshot.
        await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({
          state: 'visible', timeout: 45000,
        });
        item.route = await page.locator('[data-testid="migration-studio"]').count() > 0;
      }
      if (item.route !== actor.allowed) throw new Error('Direct route owner mismatch');
      const geom = await page.evaluate(() => ({
        width: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      }));
      item.geometry = geom;
      if (geom.scrollWidth > geom.width + 1) throw new Error('Horizontal overflow');
      if (errors.length) throw new Error('Unexpected JS errors ' + errors.join(','));
      await page.screenshot({
        path: path.join(dest, actor.name + '-' + viewport.width + '.png'),
        fullPage: true, animations: 'disabled',
      });
      report.checks.push(item);
    } catch (e) {
      report.failures.push({ ...item, error: String(e).slice(0, 500) });
    } finally { await context.close(); }
  }
} finally {
  await browser.close();
  await setup.dispose();
}
report.pass = report.failures.length === 0 && report.checks.length === sizes.length * actors.length;
await fs.writeFile(path.join(dest, 'report.json'), JSON.stringify(report, null, 2));
console.log('LOT05_AUTH_APP_SHELL_T2', JSON.stringify({
  sha, pass: report.pass, checks: report.checks, failures: report.failures,
}));
if (!report.pass) throw new Error('Real authenticated app shell gate not proven');
