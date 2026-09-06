import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const mode = process.env.MOBILE_EVIDENCE_MODE || 'after';
const baseUrl = process.env.MOBILE_EVIDENCE_URL || 'http://127.0.0.1:5173/mobile/demo?demo=1&tab=library';
const outputDir = process.env.MOBILE_EVIDENCE_DIR || '../artifacts/mobile-library-mob5e';
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];

if (!['before', 'after'].includes(mode)) throw new Error(`Unsupported mode: ${mode}`);

await fs.mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const evidence = [];

async function geometry(page, currentMode) {
  return page.evaluate(modeName => {
    const nav = document.querySelector('[data-mobile-bottom-nav]');
    if (!(nav instanceof HTMLElement)) throw new Error('MOB-5E canonical nav missing');
    const target = modeName === 'before'
      ? document.querySelector('[data-mobile-more-menu]')
      : document.querySelector('[data-mobile-library]');
    if (!(target instanceof HTMLElement)) throw new Error(`MOB-5E ${modeName} target missing`);
    return {
      navButtons: nav.querySelectorAll(':scope > div > button, :scope > div > div > button').length,
      navHeight: nav.getBoundingClientRect().height,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    };
  }, currentMode);
}

function assertGeometry(viewport, current) {
  if (current.navButtons !== 5) throw new Error(`${viewport.width}: canonical nav changed (${current.navButtons})`);
  if (current.navHeight !== 76) throw new Error(`${viewport.width}: nav height ${current.navHeight}`);
  if (current.horizontalOverflow) throw new Error(`${viewport.width}: overflow ${current.scrollWidth}>${current.innerWidth}`);
}

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
      if (await page.getByText('Bibliothèque', { exact: true }).count()) {
        throw new Error(`${viewport.width}: Bibliothèque already present in BEFORE`);
      }
      const beforeGeometry = await geometry(page, mode);
      assertGeometry(viewport, beforeGeometry);
      const screenshot = `before-plus-${viewport.width}x${viewport.height}.png`;
      await page.screenshot({ path: path.join(outputDir, screenshot) });
      if (runtimeErrors.length) throw new Error(`${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);
      evidence.push({ mode, viewport, ...beforeGeometry, runtimeErrors, screenshot });
    } else {
      await page.locator('[data-mobile-library]').waitFor({ state: 'visible' });
      await page.getByRole('heading', { name: 'Bibliothèque' }).waitFor({ state: 'visible' });
      await page.getByText('50 protocoles', { exact: true }).waitFor({ state: 'visible' });

      const listGeometry = await geometry(page, mode);
      assertGeometry(viewport, listGeometry);
      const listScreenshot = `after-library-list-${viewport.width}x${viewport.height}.png`;
      await page.screenshot({ path: path.join(outputDir, listScreenshot) });

      const search = page.getByPlaceholder('Rechercher un acte, code, discipline…');
      await search.fill('Extraction molaire');
      await page.getByText('1 résultat', { exact: true }).waitFor({ state: 'visible' });
      await page.getByText('Extraction molaire', { exact: true }).click();
      await page.locator('[data-mobile-library-detail]').waitFor({ state: 'visible' });
      await page.getByText('Radio panoramique confirmée', { exact: true }).waitFor({ state: 'visible' });

      const detailGeometry = await geometry(page, mode);
      assertGeometry(viewport, detailGeometry);
      const detailScreenshot = `after-library-detail-${viewport.width}x${viewport.height}.png`;
      await page.screenshot({ path: path.join(outputDir, detailScreenshot) });

      if (runtimeErrors.length) throw new Error(`${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);
      evidence.push({
        mode,
        viewport,
        list: listGeometry,
        detail: detailGeometry,
        runtimeErrors,
        screenshots: [listScreenshot, detailScreenshot],
      });
    }

    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, `${mode}-runtime-evidence.json`), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));