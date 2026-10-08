import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

// V1.5-01.3 error-only FUE-I: deterministic browser fault injection.
// BEFORE uses the previous certified 01.2 HEAD; AFTER tests the new HEAD.
// No external IP is contacted and no real server or patient data is used.
const phase = process.env.V15_01_3_PHASE || 'after';
const assertAfter = phase === 'after';
const directory = path.resolve('artifacts/fue-v15-01-3-' + phase);
fs.rmSync(directory, { recursive: true, force: true });
fs.mkdirSync(directory, { recursive: true });

const base = 'http://127.0.0.1:8005';
const profiles = [
  { name: '390x844', width: 390, height: 844 },
  { name: '430x932', width: 430, height: 932 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];
const scenarios = ['missing-server', 'service-503', 'database-503', 'wrong-lan', 'enrollment-423', 'station-423'];
const healthyTopology = {
  topologyRole: 'server',
  bindHost: '127.0.0.1',
  port: 8005,
  lanExposed: false,
  tlsEnabled: false,
  tlsReady: false,
  connectionUrl: null,
  remediation: 'LAN_DISABLED_LOOPBACK_ONLY',
};
const bootstrap = {
  authenticated: false,
  workstationId: null,
  enrollmentRequired: false,
  defaultExperience: null,
  stationLocked: false,
  stationEscapeAuthorized: false,
};
const report = { phase, head: process.env.PRODUCT_HEAD || null, cases: [], success: false, scope: '01.3 network-error experience / mocked service faults, no real LAN TLS' };
const browser = await chromium.launch({ headless: true });
const respond = (route, status, body) => route.fulfill({
  status,
  contentType: 'application/json',
  headers: { 'Cache-Control': 'no-store' },
  body: JSON.stringify(body),
});
try {
  for (const profile of profiles) {
    for (const scenario of scenarios) {
      const record = { profile: profile.name, scenario, screenshots: [], errors: [], failures: [], externalRequests: [] };
      report.cases.push(record);
      const context = await browser.newContext({
        viewport: { width: profile.width, height: profile.height },
        storageState: { cookies: [], origins: [] },
      });
      let currentMode = scenario;
      const page = await context.newPage();
      page.setDefaultTimeout(12000);
      page.on('pageerror', error => record.errors.push(error.message));
      page.on('request', req => {
        if (/^https?:\/\/(?:192\.168\.1\.20|example\.com)(?::|\/)/.test(req.url())) {
          record.externalRequests.push(req.url());
        }
      });
      const capture = async label => {
        const filename = profile.name + '-' + scenario + '-' + label + '.png';
        await page.screenshot({ path: path.join(directory, filename), fullPage: true, animations: 'disabled' });
        record.screenshots.push({
          file: filename,
          diagnosis: await page.locator('[data-control-center-remediation]').getAttribute('data-control-center-diagnosis'),
          message: (await page.locator('[data-control-center-remediation]').innerText()).replace(/\s+/g, ' ').trim(),
          backend: await page.locator('[data-control-center-backend]').innerText(),
          database: await page.locator('[data-control-center-db]').innerText(),
          horizontalOverflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1),
        });
      };
      try {
        // All API calls are intercepted. Unexpected traffic fails closed.
        await context.route('**/api/**', route => respond(route, 501, { detail: 'UNMODELLED_01_3_API' }));
        await context.route('**/api/workstation/bootstrap', route => respond(route, 200, bootstrap));
        await context.route('**/api/health/topology', async route => {
          if (currentMode === 'missing-server') return route.abort('failed');
          if (currentMode === 'service-503') return respond(route, 503, { detail: 'SERVICE_UNAVAILABLE' });
          return respond(route, 200, healthyTopology);
        });
        await context.route('**/api/health/db', route => {
          if (currentMode === 'missing-server') return route.abort('failed');
          if (currentMode === 'service-503' || currentMode === 'database-503') return respond(route, 503, { detail: 'SERVICE_UNAVAILABLE' });
          return respond(route, 200, { status: 'ok' });
        });
        await context.route('**/api/clinics/me', route => {
          if (currentMode === 'missing-server') return route.abort('failed');
          if (currentMode === 'enrollment-423') return respond(route, 423, { detail: 'WORKSTATION_IDENTITY_REQUIRED' });
          if (currentMode === 'station-423') return respond(route, 423, { detail: 'WORKSTATION_STATION_LOCKED' });
          return respond(route, 401, { detail: 'AUTH_REQUIRED' });
        });
        await page.goto(base + '/control-center', { waitUntil: 'domcontentloaded' });
        const target = page.locator('[data-control-center-target]');
        await target.waitFor({ state: 'visible' });
        if (scenario === 'wrong-lan') {
          await target.fill('http://192.168.1.20:8005');
          await page.locator('[data-control-center-probe]').click();
          await page.getByRole('alert').filter({ hasText: 'HTTPS est obligatoire' }).waitFor();
          await capture('01-insecure-lan-before');
          await target.fill('https://example.com:8005');
          await page.locator('[data-control-center-probe]').click();
          await page.getByRole('alert').filter({ hasText: 'adresse locale du cabinet' }).waitFor();
          await capture('02-public-host-rejected');
          await target.fill('https://192.168.1.20:8005');
          await page.locator('[data-control-center-probe]').click();
          await page.getByText('Aucune requête n’est envoyée à une origine distante', { exact: false }).waitFor();
          if (assertAfter) await page.locator('[data-control-center-diagnosis="handoff"]').waitFor();
          await capture('03-explicit-handoff-only');
          if (record.externalRequests.length) throw new Error('External probe leaked before explicit navigation');
          await target.fill(base);
          await page.locator('[data-control-center-probe]').click();
          await page.locator('[data-control-center-backend]').filter({ hasText: 'Joignable' }).waitFor();
          await page.locator('[data-control-center-db]').filter({ hasText: 'Disponible' }).waitFor();
          await capture('04-after-correction');
        } else {
          if (assertAfter) {
            const kind = scenario === 'missing-server' ? 'network'
              : scenario === 'service-503' ? 'service'
                : scenario === 'database-503' ? 'database'
                  : scenario === 'enrollment-423' ? 'enrollment' : 'station-lock';
            await page.locator('[data-control-center-diagnosis="' + kind + '"]').waitFor();
          } else {
            // Legacy BEFORE has no machine-readable diagnosis state; the route
            // failures have resolved when the retry button is available.
            await page.waitForTimeout(950);
          }
          await capture('01-failure');
          if (assertAfter) {
            const message = record.screenshots[0].message;
            if (!message.includes('relancez le diagnostic')) throw new Error('No actionable next step for ' + scenario);
            if (scenario === 'missing-server' && message.includes('Ouvrez cette adresse')) throw new Error('Wrong-origin advice on a same-origin network outage');
            if (scenario === 'service-503' && !message.includes('HTTP 503')) throw new Error('HTTP service outage misclassified');
            if (scenario === 'database-503' && !message.includes('PostgreSQL')) throw new Error('DB failure lacks PostgreSQL next step');
            if (scenario === 'enrollment-423' && !message.includes('appairée')) throw new Error('Identity refusal lacks pairing action');
            if (scenario === 'station-423' && !message.includes('PIN')) throw new Error('Station lock incorrectly treated as enrollment');
          }
          currentMode = 'healthy';
          await page.locator('[data-control-center-probe]').click();
          await page.locator('[data-control-center-backend]').filter({ hasText: 'Joignable' }).waitFor();
          await page.locator('[data-control-center-db]').filter({ hasText: 'Disponible' }).waitFor();
          await capture('02-recovered');
        }
        if (record.errors.length) throw new Error('Unhandled page errors: ' + record.errors.length);
        if (record.screenshots.some(step => step.horizontalOverflow)) throw new Error('Horizontal overflow');
        record.result = 'PASS';
      } catch (error) {
        record.result = 'FAIL';
        record.failures.push(String(error?.message || error).slice(0, 1400));
        await page.screenshot({ path: path.join(directory, profile.name + '-' + scenario + '-FAIL.png'), fullPage: true }).catch(() => {});
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
report.success = report.cases.every(test => test.result === 'PASS');
fs.writeFileSync(path.join(directory, 'report.json'), JSON.stringify(report, null, 2));
console.log('V15_01_3_FUE_SUMMARY ' + JSON.stringify({
  phase: report.phase,
  head: report.head,
  success: report.success,
  pass: report.cases.filter(test => test.result === 'PASS').length,
  total: report.cases.length,
  failures: report.cases.filter(test => test.result !== 'PASS').map(test => ({ profile: test.profile, scenario: test.scenario, failures: test.failures })),
}));
if (!report.success) process.exitCode = 1;
