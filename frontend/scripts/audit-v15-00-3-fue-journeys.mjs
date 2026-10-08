import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

// Scoped FUE-I laboratory. Simulated server contracts are NOT backend PIN/auth proof.
const out = path.resolve('artifacts/v15-00-3-fue-journeys');
await fs.mkdir(out, { recursive: true });
const base = 'http://127.0.0.1:4195';
const viewports = [
  { label: '390x844', width: 390, height: 844 },
  { label: '768x1024', width: 768, height: 1024 },
  { label: '1280x900', width: 1280, height: 900 },
];
const initial = {
  workstationId: 'ws-fue-003',
  displayName: 'Accueil FUE',
  defaultExperience: null,
  stationLocked: false,
  stationEscapeAuthorized: false,
  stationEscapeExpiresAt: null,
  enrollmentRequired: false,
  authenticated: true,
  pinConfigured: true,
  canManage: true,
  canConfigurePin: true,
};
const fixtures = {
  'station-public': { ...initial, defaultExperience: 'station', stationLocked: true, canManage: false, canConfigurePin: false },
  'hub-mode-transition': { ...initial },
  'hub-reenrollment': { ...initial, workstationId: null, enrollmentRequired: true },
};
const phases = [];
const failures = [];
const browser = await chromium.launch({ headless: true });

const record = (phase, pass, detail = '') => {
  phases.push({ phase, pass: Boolean(pass), detail });
  if (!pass) throw new Error(phase + ': ' + detail);
};

const inspect = async (page, label, journey, viewport, issues, extra = {}) => {
  const probe = await page.evaluate(() => {
    const root = document.documentElement;
    const active = document.activeElement;
    const visible = Array.from(document.querySelectorAll('button, a, input, summary')).filter(node => {
      const rect = node.getBoundingClientRect();
      const css = getComputedStyle(node);
      return rect.width > 0 && rect.height > 0 && css.visibility !== 'hidden' && css.display !== 'none';
    });
    const smallControls = visible.filter(node => {
      const rect = node.getBoundingClientRect();
      return node.matches('button') && !node.hasAttribute('disabled') &&
        (rect.width < 44 || rect.height < 44);
    }).map(node => ({ text: node.getAttribute('aria-label') || (node.textContent || '').trim().slice(0, 40),
      width: Math.round(node.getBoundingClientRect().width),
      height: Math.round(node.getBoundingClientRect().height) }));
    return {
      url: location.pathname + location.search,
      title: document.querySelector('h1')?.textContent || '',
      width: root.clientWidth,
      scrollWidth: root.scrollWidth,
      activeTag: active?.tagName || null,
      activeName: active?.getAttribute('aria-label') || (active?.textContent || '').slice(0, 35),
      focusedVisible: Boolean(active?.matches(':focus-visible')),
      stationScreen: document.querySelector('[data-station-screen]')?.getAttribute('data-station-screen') || null,
      lang: document.querySelector('[data-station-language]')?.getAttribute('data-station-language') || null,
      dir: document.querySelector('[data-station-language]')?.getAttribute('dir') || null,
      smallControls,
      clinicalLinks: Array.from(document.querySelectorAll('a[href]')).map(a => a.getAttribute('href'))
        .filter(href => /\/(patients|agenda|accounting|dashboard|settings)(\/|$)/i.test(href || '')),
    };
  });
  const file = journey + '-' + viewport.label + '-' + label + '.png';
  await page.screenshot({ path: path.join(out, file), fullPage: true, animations: 'disabled' });
  const item = { journey, viewport: viewport.label, phase: label, file, ...probe, ...extra };
  issues.captures.push(item);
  record(journey + '/' + viewport.label + '/' + label + '/no-overflow', probe.scrollWidth <= probe.width,
    String(probe.scrollWidth) + '>' + String(probe.width));
  return item;
};

const installRoutes = async (context, state, unexpected, requests) => {
  // Default: fail closed and keep exact unexpected requests visible in JSON.
  await context.route('http://127.0.0.1:8005/api/**', route => {
    const request = route.request();
    unexpected.push(request.method() + ' ' + request.url());
    return route.fulfill({ status: 501, contentType: 'application/json',
      body: JSON.stringify({ detail: 'UNMODELLED_FUE_LAB_REQUEST' }) });
  });
  const json = (route, data, status = 200) => route.fulfill({
    status, contentType: 'application/json', body: JSON.stringify(data),
  });
  await context.route('**/api/clinics/me', route => json(route, {
    nom_cabinet: 'Centre Dentaire Benmoussa', cabinet_type: 'CLINIQUE',
  }));
  await context.route('**/api/workstation/bootstrap', route => {
    requests.push({ action: 'bootstrap-read', mode: state.value.defaultExperience,
      escapeAuthorized: state.value.stationEscapeAuthorized });
    return json(route, state.value);
  });
  await context.route('**/api/workstation/state', route => state.value.enrollmentRequired
    ? json(route, { detail: 'WORKSTATION_ENROLLMENT_REQUIRED' }, 423)
    : json(route, state.value));
  await context.route('**/api/workstation/registry', route => json(route, []));
  await context.route('**/api/workstation/patient-session/config', route => json(route, { fallbackMode: 'disabled' }));
  await context.route('**/api/workstation/mode', route => {
    const data = route.request().postDataJSON();
    requests.push({ action: 'change-mode', mode: data.mode, pinLength: String(data.ownerPin || '').length });
    if (data.ownerPin !== '2468') return json(route, { detail: 'PIN refusé' }, 403);
    state.value = { ...state.value, defaultExperience: data.mode, stationLocked: data.mode === 'station',
      stationEscapeAuthorized: false };
    return json(route, state.value);
  });
  await context.route('**/api/workstation/station/escape', route => {
    const data = route.request().postDataJSON();
    requests.push({ action: 'escape', pinLength: String(data.ownerPin || '').length });
    if (data.ownerPin !== '2468') return json(route, { detail: 'PIN refusé' }, 403);
    state.value = { ...state.value, stationEscapeAuthorized: true,
      stationEscapeExpiresAt: Math.floor(Date.now() / 1000) + 600 };
    requests.push({ action: 'escape-authorized', mode: state.value.defaultExperience,
      escapeAuthorized: state.value.stationEscapeAuthorized });
    return json(route, { expiresAt: state.value.stationEscapeExpiresAt });
  });
  await context.route('**/api/workstation/pair', route => {
    const data = route.request().postDataJSON();
    requests.push({ action: 'pair', name: data.displayName, codeLength: String(data.code || '').length });
    if (data.code !== '123456') return json(route, { detail: 'CODE_INVALID' }, 403);
    state.value = { ...initial, displayName: data.displayName, workstationId: 'ws-fue-paired' };
    return json(route, state.value);
  });
  await context.route('**/health', route => json(route, { status: 'ok' }));
  // This persona is explicitly authenticated in the synthetic workstation bootstrap.
  // A contradictory /auth/me 401 causes the real frontend auth interceptor to log out.
  await context.route('**/api/auth/me', route => json(route, {
    id: 1, nom_complet: 'Audit FUE synthétique', role: 'owner', email: 'synthetic@example.invalid',
  }));
  await context.route('**/api/clinics/init-status', route => json(route, { is_initialized: true }));
};

const run = async (journey, viewport) => {
  const state = { value: { ...fixtures[journey] } };
  const unexpected = [];
  const requests = [];
  const issues = { journey, viewport: viewport.label, captures: [], unexpected, requests, errors: [], checks: [], navigations: [] };
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, reducedMotion: 'reduce' });
  let page;
  try {
    await installRoutes(context, state, unexpected, requests);
    page = await context.newPage();
    page.on('framenavigated', frame => {
      if (frame === page.mainFrame()) issues.navigations.push(frame.url());
    });
    page.on('pageerror', e => issues.errors.push('PAGEERROR ' + e.message));
    page.on('requestfailed', r => issues.errors.push('FAILED ' + r.method() + ' ' + r.url() + ' ' + (r.failure()?.errorText || '')));
    page.on('console', m => { if (m.type() === 'error') issues.errors.push('CONSOLE ' + m.text()); });

    if (journey === 'station-public') {
      await page.goto(base + '/station', { waitUntil: 'networkidle' });
      await page.locator('[data-station-screen="home"]').waitFor();
      const before = await inspect(page, '01-before', journey, viewport, issues);
      if (viewport.width === 390) {
        await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
        await inspect(page, '01b-text-at-200-percent', journey, viewport, issues);
        await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
      }
      record(journey + '/' + viewport.label + '/no-clinical-links', before.clinicalLinks.length === 0,
        JSON.stringify(before.clinicalLinks));

      await page.keyboard.press('Tab');
      const keyboard = await page.evaluate(() => ({
        tag: document.activeElement?.tagName,
        visible: Boolean(document.activeElement?.matches(':focus-visible')),
      }));
      issues.checks.push({ keyboard });
      record(journey + '/' + viewport.label + '/keyboard-focus', keyboard.tag === 'BUTTON' && keyboard.visible,
        JSON.stringify(keyboard));
      await inspect(page, '02-keyboard-focus', journey, viewport, issues);

      await page.locator('[data-station-action="documents"]').click();
      await page.locator('[data-station-screen="documents"]').waitFor();
      record(journey + '/' + viewport.label + '/documents-building',
        await page.getByText('Cette étape est en cours de construction.').count() > 0);
      await inspect(page, '03-documents-after-click', journey, viewport, issues);
      await page.getByRole('button', { name: 'Retour à l’accueil' }).click();
      await page.locator('[data-station-screen="home"]').waitFor();
      await inspect(page, '04-back-home', journey, viewport, issues);

      await page.locator('[data-station-action="help"]').click();
      await page.locator('[data-station-screen="help"]').waitFor();
      await inspect(page, '05-help-after-click', journey, viewport, issues);
      await page.getByRole('button', { name: 'Retour à l’accueil' }).click();
      await page.getByRole('button', { name: 'العربية' }).click();
      await page.locator('[data-station-language="ar"][dir="rtl"]').waitFor();
      await inspect(page, '06-rtl-after-click', journey, viewport, issues);
      await page.getByRole('button', { name: 'English' }).click();
      await page.locator('[data-station-language="en"][dir="ltr"]').waitFor();
      await page.getByRole('button', { name: 'Français' }).click();

      await page.keyboard.press('Control+Alt+h');
      await page.locator('[data-station-admin]').waitFor();
      await inspect(page, '07-admin-before-pin', journey, viewport, issues);
      const pin = page.getByLabel('PIN propriétaire', { exact: true });
      await pin.fill('123');
      await page.getByRole('button', { name: 'Autoriser l’accès au Hub' }).click();
      record(journey + '/' + viewport.label + '/short-pin-refused',
        await page.getByRole('status').filter({ hasText: 'PIN propriétaire requis.' }).count() > 0);
      record(journey + '/' + viewport.label + '/invalid-no-server-call',
        requests.filter(r => r.action === 'escape').length === 0);
      await inspect(page, '08-invalid-pin-after-click', journey, viewport, issues);

      await page.getByRole('button', { name: 'Annuler' }).click();
      await page.locator('[data-station-screen="home"]').waitFor();
      await page.reload({ waitUntil: 'networkidle' });
      await page.locator('[data-station-screen="home"]').waitFor();
      await inspect(page, '09-cancel-reload-still-station', journey, viewport, issues);
      for (const route of ['/hub?select=1', '/control-center', '/cabinet']) {
        await page.goto(base + route, { waitUntil: 'networkidle' });
        await page.locator('[data-station-screen="home"]').waitFor({ timeout: 12000 });
        record(journey + '/' + viewport.label + '/direct-lock-' + route,
          new URL(page.url()).pathname === '/station', page.url());
      }
      await inspect(page, '10-direct-url-blocked', journey, viewport, issues);
    }

    if (journey === 'hub-mode-transition') {
      await page.goto(base + '/hub?select=1', { waitUntil: 'networkidle' });
      await page.locator('[data-workstation-admin]').waitFor();
      await inspect(page, '01-before', journey, viewport, issues);
      if (viewport.width === 390) {
        await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
        await inspect(page, '01b-text-at-200-percent', journey, viewport, issues);
        await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
      }

      const mode = page.getByRole('button', { name: "Station d'accueil", exact: true });
      await mode.focus();
      await page.keyboard.press('Enter');
      record(journey + '/' + viewport.label + '/keyboard-mode-selected',
        (await mode.getAttribute('aria-pressed')) === 'true');
      await inspect(page, '02-mode-selected-with-keyboard', journey, viewport, issues);
      await page.getByLabel('PIN propriétaire', { exact: true }).fill('123');
      await page.getByRole('button', { name: 'Appliquer ce mode' }).click();
      record(journey + '/' + viewport.label + '/invalid-pin-blocked',
        await page.getByRole('status').filter({ hasText: 'Saisissez le PIN propriétaire.' }).count() > 0);
      record(journey + '/' + viewport.label + '/mode-not-sent', requests.filter(x => x.action === 'change-mode').length === 0,
        JSON.stringify(requests.filter(x => x.action === 'change-mode')));
      await inspect(page, '03-invalid-mode-after-click', journey, viewport, issues);

      await page.getByLabel('PIN propriétaire', { exact: true }).fill('2468');
      await page.getByRole('button', { name: 'Appliquer ce mode' }).click();
      await page.locator('[data-station-screen="home"]').waitFor({ timeout: 12000 });
      record(journey + '/' + viewport.label + '/mode-change-called',
        requests.filter(x => x.action === 'change-mode' && x.mode === 'station' && x.pinLength === 4).length === 1);
      await inspect(page, '04-mode-applied-after-click', journey, viewport, issues);
      await page.reload({ waitUntil: 'networkidle' });
      await page.locator('[data-station-screen="home"]').waitFor();
      await inspect(page, '05-mode-persisted-after-reload', journey, viewport, issues);
      await page.keyboard.press('Control+Alt+h');
      await page.locator('[data-station-admin]').waitFor();
      await page.getByLabel('PIN propriétaire', { exact: true }).fill('2468');
      await page.getByRole('button', { name: 'Autoriser l’accès au Hub' }).click();
      await page.locator('[data-workstation-admin]').waitFor({ timeout: 12000 });
      record(journey + '/' + viewport.label + '/authorized-escape',
        requests.filter(x => x.action === 'escape' && x.pinLength === 4).length === 1);
      await inspect(page, '06-authorized-hub-return', journey, viewport, issues);
    }

    if (journey === 'hub-reenrollment') {
      await page.goto(base + '/hub?select=1', { waitUntil: 'networkidle' });
      await page.locator('[data-workstation-enrollment]').waitFor();
      await inspect(page, '01-before', journey, viewport, issues);
      if (viewport.width === 390) {
        await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
        await inspect(page, '01b-text-at-200-percent', journey, viewport, issues);
        await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
      }
      const pair = page.getByRole('button', { name: 'Appairer cette borne' });
      record(journey + '/' + viewport.label + '/pair-disabled-until-code',
        await pair.isDisabled());
      await page.getByLabel('Nom de cette borne').fill('Accueil FUE');
      await page.getByLabel('Code d’appairage').fill('123');
      record(journey + '/' + viewport.label + '/short-code-blocked', await pair.isDisabled());
      await inspect(page, '02-invalid-enrollment', journey, viewport, issues);
      await page.getByLabel('Code d’appairage').fill('123456');
      await pair.click();
      await page.locator('[data-workstation-admin]').waitFor({ timeout: 12000 });
      record(journey + '/' + viewport.label + '/pair-action-called',
        requests.filter(x => x.action === 'pair' && x.codeLength === 6 && x.name === 'Accueil FUE').length === 1);
      await inspect(page, '03-paired-after-click', journey, viewport, issues);
      await page.reload({ waitUntil: 'networkidle' });
      await page.locator('[data-workstation-admin]').waitFor({ timeout: 12000 });
      record(journey + '/' + viewport.label + '/no-repeat-enrollment',
        await page.locator('[data-workstation-enrollment]').count() === 0);
      await inspect(page, '04-pair-persisted-after-reload', journey, viewport, issues);
    }

    record(journey + '/' + viewport.label + '/zero-browser-errors', issues.errors.length === 0,
      JSON.stringify(issues.errors));
    record(journey + '/' + viewport.label + '/zero-unmodelled-apis', unexpected.length === 0,
      JSON.stringify(unexpected));
    if (journey === 'station-public') {
      record(journey + '/' + viewport.label + '/touch-targets-44px',
        issues.captures.filter(c => c.phase.includes('before') || c.phase.includes('admin-before'))
          .every(c => c.smallControls.length === 0),
        JSON.stringify(issues.captures.flatMap(c => c.smallControls)));
    }
    issues.outcome = 'PASS';
  } catch (error) {
    issues.outcome = 'FAIL';
    issues.failure = String(error?.stack || error);
    failures.push({ journey, viewport: viewport.label, failure: issues.failure });
    try { if (page) await page.screenshot({ path: path.join(out, journey + '-' + viewport.label + '-FAIL.png'), fullPage: true }); }
    catch { /* Preserve the original error */ }
  } finally {
    issues.unexpected = [...unexpected];
    issues.requests = [...requests];
    issues.finalUrl = page?.url() || null;
    issues.finalServerState = { mode: state.value.defaultExperience, escapeAuthorized: state.value.stationEscapeAuthorized,
      escapeExpiresAt: state.value.stationEscapeExpiresAt };
    await fs.writeFile(path.join(out, journey + '-' + viewport.label + '.json'), JSON.stringify(issues, null, 2));
    await context.close();
  }
};

try {
  for (const journey of Object.keys(fixtures)) {
    for (const viewport of viewports) await run(journey, viewport);
  }
} finally {
  await browser.close();
}
const report = {
  head: process.env.GITHUB_HEAD_SHA || process.env.GITHUB_SHA || null,
  scope: 'synthetic Workstation FUE-I; backend auth/PIN intentionally not certified',
  scenarios: Object.keys(fixtures),
  viewportCount: viewports.length,
  assertionCount: phases.length,
  passedAssertions: phases.filter(p => p.pass).length,
  failedAssertions: phases.filter(p => !p.pass).length,
  phases,
  failures,
};
await fs.writeFile(path.join(out, 'journey-matrix.json'), JSON.stringify(report, null, 2));
console.log('FUE 00.3 journeys:', JSON.stringify({
  scenarios: report.scenarios, viewportCount: report.viewportCount,
  assertions: report.assertionCount, passed: report.passedAssertions, fails: failures,
}, null, 2));
if (failures.length) process.exitCode = 1;
