import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

// V1.5-00.4 is a synthetic Hub/Dispatcher contract and interactive UX gate.
// It cannot certify actual backend authentication, PIN semantics or clinical data.
const out = path.resolve('artifacts/v15-00-4-fue');
await fs.mkdir(out, { recursive: true });
const base = 'http://127.0.0.1:4195';
const viewports = [
  { width: 390, height: 844, label: '390x844' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
];
const bootstrap = {
  workstationId: null, defaultExperience: null, stationLocked: false,
  stationEscapeAuthorized: false, stationEscapeExpiresAt: null,
  enrollmentRequired: false, authenticated: false, pinConfigured: false,
  canManage: false, canConfigurePin: false,
};
const profile = { id: 1, nom_complet: 'FUE synthétique', email: 'fue@example.invalid', role: 'owner' };
const paths = {
  'fresh-routing': { state: bootstrap },
  'offline-recovery': { state: null },
  'locked-station': {
    state: { ...bootstrap, workstationId: 'station-004', defaultExperience: 'station',
      stationLocked: true, authenticated: true, pinConfigured: true },
  },
  'remembered-control': {
    state: { ...bootstrap, workstationId: 'control-004', defaultExperience: 'control_center',
      authenticated: true, pinConfigured: true },
  },
};
const browser = await chromium.launch({ headless: true });
const matrix = [];

const expect = (checks, name, pass, evidence = null) => {
  checks.push({ name, pass: Boolean(pass), evidence });
  if (!pass) throw new Error(name + ': ' + JSON.stringify(evidence));
};
const response = (route, value, status = 200) => route.fulfill({
  status, contentType: 'application/json', body: JSON.stringify(value),
});
const install = async (context, item, audit) => {
  // Every request to the cabinet backend must be explicitly modelled.
  await context.route('http://127.0.0.1:8005/api/**', route => {
    audit.unexpected.push(route.request().method() + ' ' + route.request().url());
    return response(route, { detail: 'FUE_004_UNMODELLED_API' }, 501);
  });
  await context.route('**/api/workstation/bootstrap', route =>
    item.state ? response(route, item.state) : response(route, { detail: 'offline-proof' }, 503));
  await context.route('**/api/workstation/state', route =>
    item.state ? response(route, item.state) : response(route, { detail: 'offline-proof' }, 503));
  await context.route('**/api/clinics/me', route => item.state
    ? response(route, { nom_cabinet: 'Clinique FUE', cabinet_type: 'CLINIQUE' })
    : response(route, { detail: 'offline-proof' }, 503));
  await context.route('**/api/auth/me', route => item.state?.authenticated
    ? response(route, profile) : response(route, { detail: 'Unauthenticated' }, 401));
  await context.route('**/api/clinics/init-status', route => response(route, { is_initialized: true }));
  await context.route('**/health', route => response(route, { status: 'ok' }));
  await context.route('**/api/health/topology', route => item.state
    ? response(route, {
      status: 'ok', topologyRole: 'single', bindHost: '127.0.0.1',
      port: 8005, lanExposed: false, tlsReady: false, connectionUrl: null,
    })
    : response(route, { detail: 'offline-proof' }, 503));
  await context.route('**/api/health/db', route => item.state
    ? response(route, { status: 'ok' })
    : response(route, { detail: 'offline-proof' }, 503));
};

const capture = async (page, audit, phase) => {
  const snapshot = await page.evaluate(() => {
    const root = document.documentElement;
    const controls = Array.from(document.querySelectorAll('button,a,input,summary')).filter(el => {
      const r = el.getBoundingClientRect();
      const st = getComputedStyle(el);
      return r.width > 0 && r.height > 0 && st.display !== 'none' && st.visibility !== 'hidden';
    });
    return {
      url: location.pathname + location.search,
      h1: document.querySelector('h1')?.textContent || null,
      width: root.clientWidth, scrollWidth: root.scrollWidth,
      hubCardIds: Array.from(document.querySelectorAll('[data-hub-experience]')).map(el => el.getAttribute('data-hub-experience')),
      clinicalLinks: Array.from(document.querySelectorAll('a[href]')).map(el => el.getAttribute('href')).filter(p =>
        /^\/(patients|agenda|accounting|dashboard|settings)(\/|$)/i.test(p || '')),
      offscreenControls: controls.filter(el => {
        const r = el.getBoundingClientRect();
        return r.left < -1 || r.right > root.clientWidth + 1;
      }).map(el => el.getAttribute('aria-label') || (el.textContent || '').trim().slice(0, 50)),
      activeTag: document.activeElement?.tagName,
      focusVisible: Boolean(document.activeElement?.matches(':focus-visible')),
      clinicalContent: Boolean(document.querySelector('[data-patient-chart], [data-clinical-dashboard]')),
    };
  });
  const name = audit.journey + '-' + audit.viewport + '-' + phase + '.png';
  await page.screenshot({ path: path.join(out, name), fullPage: true, animations: 'disabled' });
  audit.captures.push({ phase, name, ...snapshot });
  expect(audit.checks, phase + ': no horizontal overflow', snapshot.scrollWidth <= snapshot.width, snapshot);
  if (phase.endsWith('-zoom200')) expect(audit.checks,
    phase + ': interactive elements remain onscreen', snapshot.offscreenControls.length === 0, snapshot.offscreenControls);
  return snapshot;
};

async function run(journey, viewport) {
  const item = paths[journey];
  const audit = {
    journey, viewport: viewport.label, checks: [], captures: [],
    api: [], unexpected: [], remoteRequests: [], externalFonts: [], expectedOfflineLogs: [], expectedNavigationAborts: [], errors: [], outcome: 'PENDING',
  };
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, reducedMotion: 'reduce' });
  let page = null;
  try {
    await install(context, item, audit);
    page = await context.newPage();
    page.on('pageerror', e => audit.errors.push(e.message));
    page.on('requestfailed', r => {
      const reason = r.failure()?.errorText || 'UNKNOWN';
      // A navigation can legitimately cancel read-only topology probes. Do
      // not hide DNS/connectivity/TLS failures or aborted non-probe operations.
      const expectedNavigationAbort = reason === 'net::ERR_ABORTED'
        && r.method() === 'GET'
        && /^http:\/\/127\.0\.0\.1:8005\/api\/(?:health\/(?:topology|db)|clinics\/me)(?:\?|$)/.test(r.url());
      if (expectedNavigationAbort) {
        audit.expectedNavigationAborts.push({ method: 'GET', route: new URL(r.url()).pathname, reason });
      } else {
        audit.errors.push('requestfail ' + r.method() + ' ' + r.url() + ' ' + reason);
      }
    });
    page.on('request', r => {
      if (/^https?:\/\//.test(r.url()) &&
          !/^http:\/\/127\.0\.0\.1:(?:4195|8005)\//.test(r.url())) {
        const url = new URL(r.url());
        const fontStylesheet = url.hostname === 'fonts.googleapis.com' && r.resourceType() === 'stylesheet';
        const fontFile = url.hostname === 'fonts.gstatic.com' && r.resourceType() === 'font';
        const headers = r.headers();
        if (fontStylesheet || fontFile) {
          audit.externalFonts.push({ url: r.url(), resourceType: r.resourceType(),
            credentialed: Boolean(headers.authorization || headers.cookie) });
          if (headers.authorization || headers.cookie) audit.remoteRequests.push('CREDENTIALED_EXTERNAL_FONT ' + r.url());
        } else audit.remoteRequests.push(r.method() + ' ' + r.resourceType() + ' ' + r.url());
      }
      if (r.url().startsWith('http://127.0.0.1:8005/api/')) audit.api.push({
        method: r.method(), url: new URL(r.url()).pathname,
      });
    });
    // HTTP 401 / 503 below are deliberate negative test inputs, not console contract failures.
    page.on('console', m => {
      if (m.type() !== 'error') return;
      const message = m.text();
      // Expected adapter diagnostic only when the explicit offline 503 fixture is active.
      if (journey === 'offline-recovery' &&
          (message === 'Path: /workstation/bootstrap' ||
           message === 'Details: offline-proof')) {
        // This is the exact deliberate 503 fixture, not an arbitrary failure.
        audit.expectedOfflineLogs.push(message);
        return;
      }
      if (/^Failed to load resource: the server responded with a status of (?:401|503)/.test(message)) {
        audit.expectedOfflineLogs.push(message);
        return;
      }
      audit.errors.push('console ' + message);
    });

    if (journey === 'fresh-routing') {
      await page.goto(base + '/hub', { waitUntil: 'networkidle' });
      await page.locator('[data-v15-hub]').waitFor();
      let before = await capture(page, audit, '01-first-hub');
      expect(audit.checks, 'three PC destinations only',
        JSON.stringify(before.hubCardIds) === JSON.stringify(['cabinet', 'station', 'control']), before.hubCardIds);
      expect(audit.checks, 'no clinical links in Hub', before.clinicalLinks.length === 0, before.clinicalLinks);
      expect(audit.checks, 'no clinical data fetched by Hub',
        audit.api.every(x => !/^\/api\/(?:patients|agenda|accounting|dashboard|consultations)/.test(x.url)), audit.api);
      if (viewport.width === 390) {
        await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
        await capture(page, audit, '01b-hub-zoom200');
        await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
      }
      await page.locator('[data-hub-experience="control"]').focus();
      await page.keyboard.press('Enter');
      await page.locator('[data-control-center-topology]').waitFor();
      await capture(page, audit, '02-control-after-keyboard');
      expect(audit.checks, 'control center navigation through keyboard',
        new URL(page.url()).pathname === '/control-center', page.url());
      await page.locator('[data-control-center-open]').click();
      await page.locator('[data-v15-hub]').waitFor({ timeout: 15000 });
      await capture(page, audit, '03-back-from-control');
      await page.locator('[data-hub-experience="station"]').click();
      await page.waitForURL('**/hub?select=1', { timeout: 15000 });
      await capture(page, audit, '04-unpaired-station-refused');
      expect(audit.checks, 'unpaired Station entry rejected',
        await page.locator('[data-workstation-experience="station"]').count() === 0);
      await page.locator('[data-hub-experience="cabinet"]').click();
      await page.waitForURL('**/login', { timeout: 15000 });
      await capture(page, audit, '05-cabinet-login-boundary');
      expect(audit.checks, 'anonymous Cabinet routes to login', new URL(page.url()).pathname === '/login');
      await page.goto(base + '/dashboard', { waitUntil: 'networkidle' });
      await page.waitForURL('**/login', { timeout: 15000 });
      expect(audit.checks, 'anonymous direct dashboard refused', new URL(page.url()).pathname === '/login');
      // A PC Hub is a dispatcher, never a substitute route to Mobile/Companion.
      expect(audit.checks, 'PC Hub excludes Mobile/Companion',
        !before.hubCardIds.includes('mobile') && !before.hubCardIds.includes('companion'));
    }

    if (journey === 'offline-recovery') {
      await page.goto(base + '/hub?select=1', { waitUntil: 'networkidle' });
      await page.locator('[data-hub-offline]').waitFor({ timeout: 15000 });
      await capture(page, audit, '01-offline-hub');
      expect(audit.checks, 'offline Hub shows no contradictory generic server toast',
        (await page.getByText('Erreur Serveur (500)', { exact: true }).count()) === 0);
      await page.locator('[data-hub-experience="control"]').click();
      await page.locator('[data-control-center-topology]').waitFor({ timeout: 15000 });
      await capture(page, audit, '02-offline-control-reachable');
      expect(audit.checks, 'offline Control Center shows no generic server toast',
        (await page.getByText('Erreur Serveur (500)', { exact: true }).count()) === 0);
      expect(audit.checks, 'offline Control Center remains reachable',
        new URL(page.url()).pathname === '/control-center');
      expect(audit.checks, 'offline status does not claim healthy backend',
        !((await page.locator('[data-control-center-backend]').textContent()) || '').includes('Joignable'));
      const field = page.locator('[data-control-center-target]');
      await field.fill('http://192.168.1.5:8005');
      await page.locator('[data-control-center-probe]').click();
      await page.getByRole('alert').filter({ hasText: 'HTTPS' }).waitFor();
      await capture(page, audit, '03-reject-insecure-lan-target');
      await field.fill('https://192.168.1.5:8005');
      await page.locator('[data-control-center-probe]').click();
      await page.getByText(/Aucune requête n’est envoyée à une origine distante/).first().waitFor();
      await capture(page, audit, '04-remote-target-no-probe');
      expect(audit.checks, 'no unapproved remote API requests before explicit navigation',
        audit.remoteRequests.length === 0, audit.remoteRequests);
      await page.getByRole('button', { name: 'Retour au Hub' }).click();
      await page.locator('[data-hub-offline]').waitFor({ timeout: 15000 });
      await capture(page, audit, '05-offline-return-to-hub');
      await page.goto(base + '/dashboard', { waitUntil: 'networkidle' });
      await page.waitForURL('**/login', { timeout: 15000 });
      expect(audit.checks, 'clinical dashboard not exposed offline anonymously',
        new URL(page.url()).pathname === '/login');
    }

    if (journey === 'locked-station') {
      await page.goto(base + '/hub', { waitUntil: 'networkidle' });
      await page.locator('[data-workstation-experience="station"]').waitFor({ timeout: 15000 });
      await capture(page, audit, '01-remembered-station');
      expect(audit.checks, 'remembered Station auto-dispatch', new URL(page.url()).pathname === '/station');
      for (const [name, candidate] of [['hub-select', '/hub?select=1'], ['control', '/control-center']]) {
        await page.goto(base + candidate, { waitUntil: 'networkidle' });
        await page.locator('[data-workstation-experience="station"]').waitFor({ timeout: 15000 });
        expect(audit.checks, 'locked Station blocks direct ' + name,
          new URL(page.url()).pathname === '/station', page.url());
        await capture(page, audit, '02-refused-' + name);
      }
      await page.reload({ waitUntil: 'networkidle' });
      expect(audit.checks, 'Station persists after reload', new URL(page.url()).pathname === '/station', page.url());
      await capture(page, audit, '03-station-reload');
    }

    if (journey === 'remembered-control') {
      await page.goto(base + '/hub', { waitUntil: 'networkidle' });
      await page.locator('[data-control-center-topology]').waitFor({ timeout: 15000 });
      await capture(page, audit, '01-dispatched-control');
      expect(audit.checks, 'remembered control auto-dispatch', new URL(page.url()).pathname === '/control-center');
      await page.reload({ waitUntil: 'networkidle' });
      await page.locator('[data-control-center-topology]').waitFor();
      await capture(page, audit, '02-control-reload');
      await page.goto(base + '/hub?select=1', { waitUntil: 'networkidle' });
      await page.locator('[data-v15-hub]').waitFor();
      const after = await capture(page, audit, '03-explicit-hub-selection');
      expect(audit.checks, 'explicit Hub selection not overridden',
        new URL(page.url()).pathname === '/hub' && after.hubCardIds.length === 3, page.url());
    }

    expect(audit.checks, 'zero unmodelled backend API calls', audit.unexpected.length === 0, audit.unexpected);
    expect(audit.checks, 'zero unapproved external API calls or credentials in font requests', audit.remoteRequests.length === 0, audit.remoteRequests);
    expect(audit.checks, 'zero unhandled browser failures', audit.errors.length === 0, audit.errors);
    audit.outcome = 'PASS';
  } catch (e) {
    audit.outcome = 'FAIL';
    audit.failure = String(e?.stack || e);
    if (page) {
      audit.lastUrl = page.url();
      try { await page.screenshot({ path: path.join(out, journey + '-' + viewport.label + '-FAIL.png'), fullPage: true }); }
      catch { /* Preserve original failure */ }
    }
  } finally {
    await fs.writeFile(path.join(out, journey + '-' + viewport.label + '.json'), JSON.stringify(audit, null, 2));
    await context.close();
  }
  return audit;
}

const reports = [];
try {
  for (const journey of Object.keys(paths)) reports.push(...await Promise.all(viewports.map(v => run(journey, v))));
} finally {
  await browser.close();
}
const summary = {
  head: process.env.GITHUB_HEAD_SHA || process.env.GITHUB_SHA || null,
  scope: 'synthetic Hub/Dispatcher FUE-I, no real backend PIN/auth/clinical verification',
  runs: reports.length,
  passed: reports.filter(x => x.outcome === 'PASS').length,
  failed: reports.filter(x => x.outcome === 'FAIL').map(x => ({
    journey: x.journey, viewport: x.viewport, reason: x.failure, lastUrl: x.lastUrl,
  })),
  assertions: reports.reduce((n, r) => n + r.checks.length, 0),
  passedAssertions: reports.reduce((n, r) => n + r.checks.filter(c => c.pass).length, 0),
  captures: reports.reduce((n, r) => n + r.captures.length, 0),
};
await fs.writeFile(path.join(out, 'certification-matrix.json'), JSON.stringify(summary, null, 2));
console.log('V1.5-00.4 FUE matrix', JSON.stringify(summary, null, 2));
if (summary.failed.length) process.exitCode = 1;
