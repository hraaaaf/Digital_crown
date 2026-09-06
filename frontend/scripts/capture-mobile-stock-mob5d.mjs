import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const mode = process.env.MOBILE_EVIDENCE_MODE || 'after';
const baseUrl = process.env.MOBILE_EVIDENCE_URL || 'http://127.0.0.1:5173/mobile/demo?demo=1&tab=stock';
const outputDir = process.env.MOBILE_EVIDENCE_DIR || '../artifacts/mobile-stock-mob5d';
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];

if (!['before', 'after'].includes(mode)) throw new Error(`Unsupported mode: ${mode}`);

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

    if (mode === 'before') {
      await page.getByText('Plus', { exact: true }).click();
      await page.locator('[data-mobile-more-menu]').waitFor({ state: 'visible' });
      if (await page.getByText('Stock', { exact: true }).count()) throw new Error(`${viewport.width}: Stock already present in BEFORE`);
    } else {
      await page.locator('[data-mobile-stock]').waitFor({ state: 'visible' });
      await page.getByRole('heading', { name: 'Stock' }).waitFor({ state: 'visible' });
      await page.getByText('Gants nitrile M', { exact: true }).waitFor({ state: 'visible' });
      await page.getByText('Composite universel', { exact: true }).waitFor({ state: 'visible' });
    }

    const geometry = await page.evaluate(currentMode => {
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      if (!(nav instanceof HTMLElement)) throw new Error('MOB-5D canonical nav missing');
      const target = currentMode === 'before'
        ? document.querySelector('[data-mobile-more-menu]')
        : document.querySelector('[data-mobile-stock]');
      if (!(target instanceof HTMLElement)) throw new Error(`MOB-5D ${currentMode} target missing`);
      return {
        navButtons: nav.querySelectorAll(':scope > div > button, :scope > div > div > button').length,
        navHeight: nav.getBoundingClientRect().height,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      };
    }, mode);

    if (geometry.navButtons !== 5) throw new Error(`${viewport.width}: canonical nav changed (${geometry.navButtons})`);
    if (geometry.navHeight !== 76) throw new Error(`${viewport.width}: nav height ${geometry.navHeight}`);
    if (geometry.horizontalOverflow) throw new Error(`${viewport.width}: overflow ${geometry.scrollWidth}>${geometry.innerWidth}`);
    if (runtimeErrors.length) throw new Error(`${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);

    const screenshot = `${mode}-${mode === 'before' ? 'plus' : 'stock'}-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outputDir, screenshot) });
    evidence.push({ mode, viewport, ...geometry, runtimeErrors, screenshot });
    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, `${mode}-runtime-evidence.json`), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));