import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.MOBILE_EVIDENCE_URL || 'http://127.0.0.1:5173/mobile/demo?demo=1';
const outputDir = process.env.MOBILE_EVIDENCE_DIR || '../artifacts/mobile-frontdesk-mob5b-after';
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];

await fs.mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const evidence = [];

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    const runtimeErrors = [];
    page.on('pageerror', error => runtimeErrors.push(`pageerror:${error.message}`));
    page.on('console', message => {
      if (message.type() === 'error' && !message.text().toLowerCase().includes('[vite]')) {
        runtimeErrors.push(`console:${message.text()}`);
      }
    });

    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.locator('[data-dc-mobile-shell]').waitFor({ state: 'visible' });
    const nav = page.locator('[data-mobile-bottom-nav]');
    await nav.getByText('Plus', { exact: true }).click();
    await page.locator('[data-mobile-more-menu]').waitFor({ state: 'visible' });
    await page.getByText('Frontdesk', { exact: true }).click();
    await page.locator('[data-mobile-frontdesk]').waitFor({ state: 'visible' });
    await page.getByRole('heading', { name: 'Frontdesk' }).waitFor({ state: 'visible' });

    const geometry = await page.evaluate(() => {
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      const frontdesk = document.querySelector('[data-mobile-frontdesk]');
      if (!(nav instanceof HTMLElement) || !(frontdesk instanceof HTMLElement)) throw new Error('MOB-5B shell missing');
      return {
        navButtons: nav.querySelectorAll('button').length,
        navHeight: nav.getBoundingClientRect().height,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      };
    });

    if (geometry.navButtons !== 5) throw new Error(`${viewport.width}: canonical nav changed (${geometry.navButtons})`);
    if (geometry.navHeight !== 76) throw new Error(`${viewport.width}: nav height ${geometry.navHeight}`);
    if (geometry.horizontalOverflow) throw new Error(`${viewport.width}: overflow ${geometry.scrollWidth}>${geometry.innerWidth}`);
    if (runtimeErrors.length) throw new Error(`${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);

    const screenshot = `after-frontdesk-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outputDir, screenshot) });
    evidence.push({ viewport, ...geometry, runtimeErrors, screenshot });
    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'runtime-evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));
