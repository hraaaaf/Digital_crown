import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.V15_03_1_PHASE || 'before';
const out = path.resolve(`artifacts/v15-03-1-kiosk-shell-${phase}`);
await fs.mkdir(out, { recursive: true });

const bootstrap = {
  workstationId: 'ws-kiosk-proof',
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

const browser = await chromium.launch({ headless: true });
const report = [];

try {
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

      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {
        if (message.type() === 'error') errors.push(message.text());
      });

      await page.goto('http://127.0.0.1:4195/station', {
        waitUntil: 'networkidle',
        timeout: 30000,
      });
      if (scale.rootFontSize) {
        await page.evaluate(value => { document.documentElement.style.fontSize = value; }, scale.rootFontSize);
        await page.waitForTimeout(100);
      }

      const meta = await page.evaluate(() => ({
        width: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        height: document.documentElement.clientHeight,
        scrollHeight: document.documentElement.scrollHeight,
        stationVisible: Boolean(document.querySelector('[data-workstation-experience="station"]')),
        clinicalLinks: Array.from(document.querySelectorAll('a')).filter(a => /patients|agenda|accounting|dashboard|settings/i.test(a.getAttribute('href') || '')).map(a => a.getAttribute('href')),
        h1: document.querySelector('h1')?.textContent || '',
      }));

      const filename = `${phase}-station-${vp.label}-${scale.label}.png`;
      await page.screenshot({
        path: path.join(out, filename),
        fullPage: true,
        animations: 'disabled',
      });

      report.push({
        phase,
        viewport: vp.label,
        scale: scale.label,
        filename,
        ...meta,
        errors,
      });
      await context.close();
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
  item.errors.length > 0
);
console.log(JSON.stringify(evidence, null, 2));
if (failures.length > 0) {
  console.error('V1.5-03.1 visual evidence failed closed:', JSON.stringify(failures, null, 2));
  process.exit(1);
}
