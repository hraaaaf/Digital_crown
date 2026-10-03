import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.V15_03_2_PHASE || 'after';
const out = path.resolve(`artifacts/v15-03-2-station-identity-${phase}`);
await fs.mkdir(out, { recursive: true });

const baseBootstrap = {
  workstationId: 'ws-proof-identity-0001',
  displayName: phase === 'after' ? 'Accueil 1' : null,
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

const scenarios = [
  {
    name: 'hub-admin',
    url: '/hub?select=1',
    bootstrap: baseBootstrap,
    state: baseBootstrap,
    expect: phase === 'after' ? '[data-workstation-identity]' : '[data-workstation-admin]',
  },
  {
    name: 'hub-enroll',
    url: '/hub?select=1',
    bootstrap: { ...baseBootstrap, workstationId: null, displayName: null, enrollmentRequired: true },
    state: null,
    expect: '[data-workstation-enrollment]',
  },
];

const registry = [
  {
    workstationId: 'ws-proof-identity-0001',
    displayName: 'Accueil 1',
    defaultExperience: 'station',
    revoked: false,
    createdAt: '2026-10-03T10:00:00',
    updatedAt: '2026-10-03T10:00:00',
  },
  {
    workstationId: 'ws-proof-identity-0002',
    displayName: 'Borne entrée',
    defaultExperience: 'station',
    revoked: false,
    createdAt: '2026-10-03T10:05:00',
    updatedAt: '2026-10-03T10:05:00',
  },
];

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

const browser = await chromium.launch({ headless: true });
const report = [];

try {
  for (const scenario of scenarios) {
    for (const vp of viewports) {
      for (const scale of scales) {
        const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
        await context.route('**/api/clinics/me', route => route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ nom_cabinet: 'Centre Dentaire Benmoussa', cabinet_type: 'CLINIQUE' }),
        }));
        await context.route('**/api/workstation/bootstrap', route => route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(scenario.bootstrap),
        }));
        await context.route('**/api/workstation/state', route => route.fulfill({
          status: scenario.state ? 200 : 423,
          contentType: 'application/json',
          body: JSON.stringify(scenario.state ?? { detail: 'WORKSTATION_ENROLLMENT_REQUIRED' }),
        }));
        await context.route('**/api/workstation/registry', route => route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(registry),
        }));

        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => {
          if (message.type() === 'error') errors.push(message.text());
        });

        await page.goto(`http://127.0.0.1:4196${scenario.url}`, { waitUntil: 'networkidle', timeout: 30000 });
        if (scale.rootFontSize) {
          await page.evaluate(value => { document.documentElement.style.fontSize = value; }, scale.rootFontSize);
          await page.waitForTimeout(100);
        }

        const meta = await page.evaluate(expectSelector => ({
          width: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          expectedVisible: Boolean(document.querySelector(expectSelector)),
          identityVisible: Boolean(document.querySelector('[data-workstation-identity]')),
          enrollmentVisible: Boolean(document.querySelector('[data-workstation-enrollment]')),
          h1: document.querySelector('h1')?.textContent || '',
        }), scenario.expect);

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
  !item.expectedVisible ||
  item.scrollWidth > item.width ||
  item.errors.length > 0
);
console.log(JSON.stringify(evidence, null, 2));
if (failures.length > 0) {
  console.error('V1.5-03.2 station identity visual evidence failed closed:', JSON.stringify(failures, null, 2));
  process.exit(1);
}
