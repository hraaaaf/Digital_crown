import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const out = path.resolve('artifacts/v15-00-2-hub-github');
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const viewports = [
  { width: 390, height: 844, label: '390x844' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
];
const report = [];
try {
  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    await context.route('**/api/clinics/me', async route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ nom_cabinet: 'Centre Dentaire Benmoussa', cabinet_type: 'CLINIQUE', logo_path: null })
    }));
    await context.route('**/api/workstation/bootstrap', async route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        workstationId: null,
        defaultExperience: null,
        stationLocked: false,
        stationEscapeAuthorized: false,
        stationEscapeExpiresAt: null,
        enrollmentRequired: false,
        authenticated: false,
        pinConfigured: false,
        canManage: false,
        canConfigurePin: false,
      })
    }));
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto('http://127.0.0.1:4195/hub', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(300);
    const meta = await page.evaluate(() => ({
      head: document.querySelector('h1')?.textContent || '',
      cards: document.querySelectorAll('[data-hub-experience]').length,
      width: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      primary: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(),
      bg: getComputedStyle(document.documentElement).getPropertyValue('--bg-medical-pearl').trim(),
      card: getComputedStyle(document.documentElement).getPropertyValue('--card-bg').trim(),
    }));
    await page.screenshot({ path: path.join(out, `hub-${vp.label}.png`), fullPage: true, animations: 'disabled' });
    report.push({ viewport: vp.label, ...meta, errors });
    await context.close();
  }
} finally { await browser.close(); }
await fs.writeFile(path.join(out, 'report.json'), JSON.stringify({ commit: process.env.GITHUB_SHA || null, report }, null, 2));
console.log(JSON.stringify(report, null, 2));

const failures = report.filter(item => item.cards !== 3 || item.scrollWidth > item.width || item.errors.length > 0);
if (failures.length > 0) {
  console.error('Hub visual proof failed closed:', JSON.stringify(failures, null, 2));
  process.exit(1);
}
