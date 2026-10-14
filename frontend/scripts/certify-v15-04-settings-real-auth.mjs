// V1.5-04: real backend and real browser Login UI, no auth/HTTP mocks.
// The BEFORE frontend uses the immutable master baseline; the isolated API stays
// on the tested AFTER backend in both phases. Never claim two physical devices.
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const phase = process.env.SETTINGS_REAL_PHASE;
const head = process.env.PRODUCT_HEAD;
const base = process.env.BASE_HEAD;
const password = process.env.T2_PASSWORD;
const ownerPin = process.env.T2_OWNER_PIN;
const owner = process.env.T2_USER;
const branchPhase = phase === 'before' || phase === 'after';
if (!branchPhase || !/^[0-9a-f]{40}$/.test(head || '')
  || !/^[0-9a-f]{40}$/.test(base || '') || !password || !owner
  || !/^\d{6}$/.test(ownerPin || '')) {
  throw new Error('Exact HEADs, phase, and isolated credentials required');
}
if (process.env.ENVIRONMENT !== 'test' || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1') {
  throw new Error('Never run real-auth Settings certification outside isolated test');
}

const apiBase = 'http://127.0.0.1:8005';
const uiBase = 'http://127.0.0.1:5173';
const output = path.resolve('../artifacts/v15-04-settings-real-auth/' + phase);
await fs.mkdir(output, { recursive: true });
const viewports = [
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];
const roles = [
  { name: 'owner', email: owner, expectedAccess: 200 },
  { name: 'delegated', email: 't2-delegated-admin@cabinet.ma', expectedAccess: 403 },
];
const evidence = {
  phase, baseHead: base, productHead: head,
  actualFrontendHead: phase === 'before' ? base : head,
  backendHead: head,
  protocol: 'Live FastAPI + real Vite Settings + browser Login, isolated T2 only',
  realCabinetAuthentication: true,
  syntheticApiAuth: false,
  beforeAfterFrontendVersionsAreDifferent: true,
  physicalPass: false,
  samples: [], failures: [],
};
const browser = await chromium.launch({ headless: true });
try {
  for (const role of roles) {
    for (const vp of viewports) {
      const record = {
        role: role.name, viewport: vp, phase, shots: [], jsErrors: [],
        backendErrors: [], monitorRequests: [], checks: {},
      };
      let context;
      const api = await request.newContext({ baseURL: apiBase });
      try {
        // Real workstation creation uses the owner account, not fabricated cookies.
        const ownerLogin = await api.post('/api/auth/login', {
          form: { username: owner, password },
        });
        if (ownerLogin.status() !== 200) throw new Error('Owner login failed: ' + ownerLogin.status());
        const ownerToken = (await ownerLogin.json()).access_token;
        const enrollment = await enrollT2Workstation(api, ownerToken, password);
        const workstationCookies = enrollment.cookies.filter(cookie => cookie.name === 'dc_workstation');
        if (workstationCookies.length !== 1) throw new Error('Missing real enrolled workstation cookie');

        // Enrolment creates a workstation in unselected (hub) mode. This
        // owner-only endpoint requires a real Cabinet-mode workstation, so
        // exercise the actual privileged PIN and mode APIs; never forge mode
        // state, database records, auth responses or cookies in the harness.
        const ownerHeaders = { Authorization: 'Bearer ' + ownerToken };
        const pinSetup = await api.post('/api/workstation/owner-pin', {
          data: { accountPassword: password, newPin: ownerPin },
          headers: ownerHeaders,
        });
        if (pinSetup.status() !== 200) {
          throw new Error('Real owner PIN setup failed: HTTP ' + pinSetup.status());
        }
        const modeSelection = await api.post('/api/workstation/mode', {
          data: { mode: 'cabinet', ownerPin },
          headers: ownerHeaders,
        });
        if (modeSelection.status() !== 200) {
          throw new Error('Real Cabinet workstation mode selection failed: HTTP ' + modeSelection.status());
        }
        const serverMode = await modeSelection.json();
        if (serverMode.defaultExperience !== 'cabinet') {
          throw new Error('Real Cabinet workstation mode was not acknowledged by server');
        }
        record.checks.realCabinetMode = true;

        // Backend owner/delegated decisions are verified with genuine credentials.
        const roleLogin = await api.post('/api/auth/login', {
          form: { username: role.email, password },
        });
        if (roleLogin.status() !== 200) throw new Error('Role login failed: ' + role.name + ' ' + roleLogin.status());
        const roleToken = (await roleLogin.json()).access_token;
        const backendStatus = await api.get('/api/admin/station-print-config/blocked-jobs', {
          headers: { Authorization: 'Bearer ' + roleToken },
        });
        // API request context already owns legitimate workstation cookie.
        record.checks.realBackendOwnerBoundaryStatus = backendStatus.status();
        if (backendStatus.status() !== role.expectedAccess) {
          throw new Error('Backend owner boundary mismatch for ' + role.name + ': ' + backendStatus.status());
        }
        if (role.name === 'owner') {
          const body = await backendStatus.json();
          if (body.printingAvailable !== false || body.retrySupported !== false
            || !Array.isArray(body.jobs)) throw new Error('Owner monitor exposed unsafe capability');
        }
        record.checks.realWorkstationCookie = true;

        context = await browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          reducedMotion: 'reduce',
          storageState: { cookies: workstationCookies, origins: [] },
        });
        const page = await context.newPage();
        page.on('pageerror', err => record.jsErrors.push(err.message));
        page.on('response', response => {
          const url = new URL(response.url());
          if (url.pathname === '/api/admin/station-print-config/blocked-jobs') {
            record.monitorRequests.push({
              status: response.status(),
              cache: response.headers()['cache-control'] || '',
            });
          }
          if (response.status() >= 500) {
            record.backendErrors.push({ status: response.status(), path: url.pathname });
          }
        });
        await page.goto(uiBase + '/login', { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.locator('input[type=email]').fill(role.email);
        await page.locator('input[type=password]').fill(password);
        await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
        await page.waitForURL(url => url.pathname === '/dashboard', { timeout: 60000 });
        record.checks.realBrowserLogin = true;
        await page.goto(uiBase + '/settings', { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.getByRole('heading', { name: 'Paramètres', exact: true }).waitFor({ timeout: 35000 });
        await page.getByRole('button', { name: 'Sécurité & Backup', exact: true }).click();
        await page.getByRole('heading', { name: 'Sécurité & Souveraineté', exact: true }).waitFor({ timeout: 35000 });
        record.checks.realSettingsNavigation = true;

        const monitor = page.getByTestId('blocked-print-jobs-read-only');
        if (phase === 'after' && role.name === 'owner') {
          await monitor.waitFor({ state: 'visible', timeout: 20000 });
          await page.getByText(/Aucune impression bloquée répertoriée|impression\(s\) à vérifier/).first()
            .waitFor({ timeout: 20000 });
          if (!record.monitorRequests.some(x => x.status === 200 && x.cache.includes('no-store'))) {
            throw new Error('Owner monitor not served by actual backend with no-store');
          }
          if (await page.getByRole('button', { name: /réimprimer|imprimer maintenant/i }).count()) {
            throw new Error('Unsafe print or retry CTA on owner read-only panel');
          }
        } else {
          if (await monitor.count()) throw new Error('Restricted/baseline monitor leaked to ' + role.name);
          if (record.monitorRequests.length) throw new Error('Delegated or baseline frontend fetched owner-only monitor');
        }

        for (const zoom of [100, 200]) {
          await page.evaluate(z => { document.documentElement.style.fontSize = z + '%'; }, zoom);
          await page.waitForTimeout(150);
          const overflow = await page.evaluate(() => ({
            scrollWidth: document.documentElement.scrollWidth,
            viewportWidth: document.documentElement.clientWidth,
          }));
          if (overflow.scrollWidth > overflow.viewportWidth + 1) {
            throw new Error('Horizontal overflow ' + role.name + ' at ' + vp.width + 'px/' + zoom + '%');
          }
          const label = role.name + '-' + vp.width + 'x' + vp.height + '-text' + zoom;
          const filename = label + '.png';
          await page.evaluate(() => window.scrollTo(0, 0));
          await page.screenshot({ path: path.join(output, filename), fullPage: false, animations: 'disabled' });
          record.shots.push(filename);
          if (phase === 'after' && role.name === 'owner') {
            await monitor.scrollIntoViewIfNeeded();
            const detail = label + '-owner-monitor.png';
            await page.screenshot({ path: path.join(output, detail), fullPage: false, animations: 'disabled' });
            record.shots.push(detail);
          }
        }
        if (record.jsErrors.length || record.backendErrors.length) {
          throw new Error('Unexpected browser/server errors: ' + JSON.stringify({
            jsErrors: record.jsErrors, backendErrors: record.backendErrors,
          }));
        }
        record.checks.roleBoundary = true;
        record.complete = true;
        evidence.samples.push(record);
      } catch (err) {
        record.complete = false;
        record.error = String(err);
        evidence.samples.push(record);
        evidence.failures.push({ role: role.name, viewport: vp, reason: String(err) });
        if (context?.pages()[0]) {
          await context.pages()[0].screenshot({
            path: path.join(output, 'FAIL-' + role.name + '-' + vp.width + '.png'),
            fullPage: false,
          }).catch(() => {});
        }
      } finally {
        await context?.close();
        await api.dispose();
      }
    }
  }
} finally {
  await browser.close();
  evidence.complete = evidence.samples.length === 6 && evidence.failures.length === 0
    && evidence.samples.every(s => s.complete && s.shots.length >= 2);
  await fs.writeFile(path.join(output, 'evidence.json'), JSON.stringify(evidence, null, 2));
}
if (!evidence.complete) throw new Error('Real-auth Settings certification failed: ' + JSON.stringify(evidence.failures));
console.log('REAL_AUTH_SETTINGS_' + phase.toUpperCase() + '_PASS 6 role/viewport samples');
