import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const out = path.resolve('artifacts/v15-00-3-workstation');
await fs.mkdir(out, { recursive: true });

const baseBootstrap = {
  workstationId: null,
  defaultExperience: null,
  stationLocked: false,
  stationEscapeAuthorized: false,
  stationEscapeExpiresAt: null,
  enrollmentRequired: false,
  authenticated: true,
  pinConfigured: false,
  canManage: true,
  canConfigurePin: true,
};

const scenarios = [
  {
    name: 'hub-admin',
    url: '/hub?select=1',
    bootstrap: baseBootstrap,
    state: { ...baseBootstrap, workstationId: 'ws-proof' },
    expect: '[data-workstation-admin]',
  },
  {
    name: 'hub-enroll',
    url: '/hub?select=1',
    bootstrap: {
      ...baseBootstrap,
      enrollmentRequired: true,
      workstationId: null,
    },
    state: null,
    expect: '[data-workstation-enrollment]',
  },
  {
    name: 'station-locked',
    url: '/station',
    bootstrap: {
      ...baseBootstrap,
      workstationId: 'ws-proof',
      defaultExperience: 'station',
      stationLocked: true,
      canManage: false,
      canConfigurePin: false,
    },
    state: null,
    expect: '[data-workstation-experience="station"]',
  },
  {
    name: 'station-admin',
    url: '/station',
    bootstrap: {
      ...baseBootstrap,
      workstationId: 'ws-proof',
      defaultExperience: 'station',
      stationLocked: true,
      canManage: false,
      canConfigurePin: false,
    },
    state: null,
    revealAdmin: true,
    expect: '[data-station-admin]',
  },
];

const viewports = [
  { width: 390, height: 844, label: '390x844' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
];

const browser = await chromium.launch({ headless: true });
const report = [];

try {
  for (const scenario of scenarios) {
    for (const vp of viewports) {
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

      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {
        if (message.type() === 'error') errors.push(message.text());
      });

      await page.goto(`http://127.0.0.1:4195${scenario.url}`, {
        waitUntil: 'networkidle',
        timeout: 30000,
      });
      if (scenario.revealAdmin) {
        await page.keyboard.press('Control+Alt+h');
        await page.waitForTimeout(100);
      }

      const meta = await page.evaluate(expectSelector => ({
        width: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        expectedVisible: Boolean(document.querySelector(expectSelector)),
        h1: document.querySelector('h1')?.textContent || '',
      }), scenario.expect);

      await page.screenshot({
        path: path.join(out, `${scenario.name}-${vp.label}.png`),
        fullPage: true,
        animations: 'disabled',
      });

      report.push({
        scenario: scenario.name,
        viewport: vp.label,
        ...meta,
        errors,
      });
      await context.close();
    }
  }
} finally {
  await browser.close();
}

await fs.writeFile(
  path.join(out, 'report.json'),
  JSON.stringify({ commit: process.env.GITHUB_SHA || null, report }, null, 2),
);

const failures = report.filter(item =>
  !item.expectedVisible ||
  item.scrollWidth > item.width ||
  item.errors.length > 0
);
console.log(JSON.stringify(report, null, 2));
if (failures.length > 0) {
  console.error('Workstation visual proof failed closed:', JSON.stringify(failures, null, 2));
  process.exit(1);
}
