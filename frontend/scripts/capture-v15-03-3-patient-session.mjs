import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.V15_03_3_PHASE || 'after';
const out = path.resolve(`artifacts/v15-03-3-patient-session-${phase}`);
await fs.mkdir(out, { recursive: true });

const bootstrap = {
  workstationId: 'ws-03-3-proof',
  displayName: 'Accueil 1',
  defaultExperience: 'station',
  stationLocked: true,
  stationEscapeAuthorized: false,
  stationEscapeExpiresAt: null,
  enrollmentRequired: false,
  authenticated: true,
  pinConfigured: true,
  canManage: false,
  canConfigurePin: false,
};

const viewports = [
  { width: 390, height: 844, label: '390x844' },
  { width: 430, height: 932, label: '430x932' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
];
const scales = [
  { label: 'normal', rootFontSize: null },
  { label: 'text200', rootFontSize: '200%' },
];

const scenarios = phase === 'before'
  ? [{ name: 'appointment', mode: 'before' }]
  : [
      { name: 'appointment', mode: 'pending' },
      { name: 'fallback', mode: 'fallback' },
      { name: 'identified', mode: 'identified' },
    ];

const onePixelPng = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
const browser = await chromium.launch({ headless: true });
const report = [];

try {
  for (const scenario of scenarios) {
    for (const vp of viewports) {
      for (const scale of scales) {
        const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
        await context.route('**/api/workstation/bootstrap', route => route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(bootstrap),
        }));
        await context.route('**/api/workstation/state', route => route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(bootstrap),
        }));
        await context.route('**/api/workstation/patient-session', route => {
          if (route.request().method() !== 'POST') return route.continue();
          return route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              sessionId: 'proof-session',
              handoffUrl: 'https://cabinet.local/companion?stationSession=opaque-proof-token',
              qrDataUrl: onePixelPng,
              nfcPayload: 'https://cabinet.local/companion?stationSession=opaque-proof-token',
              expiresAt: '2026-10-04T01:02:00',
              fallbackMode: 'phone_dob',
            }),
          });
        });
        await context.route('**/api/workstation/patient-session/proof-session', route => {
          if (route.request().method() !== 'GET') return route.continue();
          const payload = scenario.mode === 'identified'
            ? { status: 'identified', sessionId: 'proof-session', displayName: 'Aya Audit', claimedAt: '2026-10-04T01:00:10' }
            : { status: 'pending', sessionId: 'proof-session', expiresAt: '2026-10-04T01:02:00' };
          return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) });
        });
        await context.route('**/api/workstation/patient-session/proof-session/appointments/today', route => route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'none', appointments: [], staffActionRequired: false }),
        }));
        await context.route('**/api/workstation/patient-session/proof-session/purge', route => route.fulfill({ status: 204, body: '' }));
        await context.route('**/api/workstation/patient-session/proof-session/fallback', route => route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'identified', sessionId: 'proof-session', displayName: 'Aya Audit' }),
        }));

        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => {
          if (message.type() === 'error') errors.push(message.text());
        });

        await page.goto('http://127.0.0.1:4197/station', { waitUntil: 'networkidle', timeout: 30000 });
        if (scale.rootFontSize) {
          await page.evaluate(value => { document.documentElement.style.fontSize = value; }, scale.rootFontSize);
          await page.waitForTimeout(100);
        }

        await page.locator('[data-station-action="appointment"]').click();

        if (phase === 'before') {
          await page.getByText('Cette étape est en cours de construction.').waitFor({ timeout: 10000 });
        } else if (scenario.mode === 'fallback') {
          await page.locator('[data-station-patient-session]').waitFor({ timeout: 10000 });
          await page.locator('[data-station-fallback-toggle]').click();
          await page.locator('[data-station-fallback-form]').waitFor({ timeout: 10000 });
        } else if (scenario.mode === 'identified') {
          await page.locator('[data-station-arrival-bridge]').waitFor({ timeout: 10000 });
        } else {
          await page.locator('[data-station-patient-session]').waitFor({ timeout: 10000 });
        }

        const meta = await page.evaluate(() => ({
          width: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          stationVisible: Boolean(document.querySelector('[data-workstation-experience="station"]')),
          patientSessionVisible: Boolean(document.querySelector('[data-station-patient-session]')),
          fallbackVisible: Boolean(document.querySelector('[data-station-fallback-form]')),
          identifiedVisible: Boolean(document.querySelector('[data-station-arrival-bridge]')),
          cameraInputs: document.querySelectorAll('input[accept*="image"], video').length,
          clinicalLinks: Array.from(document.querySelectorAll('a'))
            .filter(a => /patients|agenda|accounting|dashboard|settings/i.test(a.getAttribute('href') || ''))
            .map(a => a.getAttribute('href')),
          bodyText: document.body.textContent || '',
        }));

        const filename = `${phase}-${scenario.name}-${vp.label}-${scale.label}.png`;
        await page.screenshot({ path: path.join(out, filename), fullPage: true, animations: 'disabled' });
        report.push({ phase, scenario: scenario.name, viewport: vp.label, scale: scale.label, filename, ...meta, errors });
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}

const evidence = {
  phase,
  head: process.env.EVALUATED_SHA || process.env.GITHUB_SHA || null,
  base: process.env.EVALUATED_BASE || null,
  report,
};
await fs.writeFile(path.join(out, 'evidence.json'), JSON.stringify(evidence, null, 2));

const failures = report.filter(item =>
  !item.stationVisible ||
  item.scrollWidth > item.width ||
  item.clinicalLinks.length > 0 ||
  item.cameraInputs > 0 ||
  item.errors.length > 0 ||
  (phase === 'after' && item.scenario === 'appointment' && !item.patientSessionVisible) ||
  (phase === 'after' && item.scenario === 'fallback' && !item.fallbackVisible) ||
  (phase === 'after' && item.scenario === 'identified' && !item.identifiedVisible)
);
console.log(JSON.stringify(evidence, null, 2));
if (failures.length > 0) {
  console.error('V1.5-03.3 visual evidence failed closed:', JSON.stringify(failures, null, 2));
  process.exit(1);
}
