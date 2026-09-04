import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.MOBILE_EVIDENCE_URL || 'http://127.0.0.1:5173/mobile/demo?demo=1&quick=1';
const outputDir = process.env.MOBILE_EVIDENCE_DIR || '../artifacts/mobile-quick-action-hub-after';
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
      if (message.type() === 'error') runtimeErrors.push(`console:${message.text()}`);
    });

    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.locator('[data-dc-mobile-shell]').waitFor({ state: 'visible' });
    await page.locator('[data-mobile-quick-action-hub]').waitFor({ state: 'visible' });

    const result = await page.evaluate(() => {
      const oldFab = document.querySelector('button[aria-label="Ajouter un rendez-vous"]');
      const promotedFab = document.querySelector('button[aria-expanded="true"]');
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      const hub = document.querySelector('[data-mobile-quick-action-hub]');
      if (!(promotedFab instanceof HTMLElement)) throw new Error('Promoted MOB-3 FAB missing');
      if (!(nav instanceof HTMLElement)) throw new Error('Mobile bottom nav missing');
      if (!(hub instanceof HTMLElement)) throw new Error('Quick Action Hub missing');

      const oldStyle = oldFab instanceof HTMLElement ? getComputedStyle(oldFab) : null;
      const newStyle = getComputedStyle(promotedFab);
      const fabBox = promotedFab.getBoundingClientRect();
      const navBox = nav.getBoundingClientRect();
      const dialog = hub.querySelector('[role="dialog"]');
      const dialogBox = dialog instanceof HTMLElement ? dialog.getBoundingClientRect() : null;
      const labels = Array.from(hub.querySelectorAll('button')).map(button => button.textContent?.trim()).filter(Boolean);

      return {
        oldFabPresent: Boolean(oldFab),
        oldFabVisibility: oldStyle?.visibility || null,
        oldFabPointerEvents: oldStyle?.pointerEvents || null,
        promotedFabVisible: newStyle.visibility !== 'hidden' && newStyle.display !== 'none' && fabBox.width > 0 && fabBox.height > 0,
        fabBox: { x: fabBox.x, y: fabBox.y, width: fabBox.width, height: fabBox.height },
        navBox: { x: navBox.x, y: navBox.y, width: navBox.width, height: navBox.height },
        dialogBox: dialogBox ? { x: dialogBox.x, y: dialogBox.y, width: dialogBox.width, height: dialogBox.height } : null,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        actions: labels,
      };
    });

    if (!result.promotedFabVisible) throw new Error(`${viewport.width}: promoted FAB is not visible`);
    if (result.fabBox.width !== 56 || result.fabBox.height !== 56) {
      throw new Error(`${viewport.width}: FAB size ${result.fabBox.width}x${result.fabBox.height}, expected 56x56`);
    }
    if (result.oldFabPresent && (result.oldFabVisibility !== 'hidden' || result.oldFabPointerEvents !== 'none')) {
      throw new Error(`${viewport.width}: legacy Agenda FAB is still interactive/visible`);
    }
    if (result.horizontalOverflow) {
      throw new Error(`${viewport.width}: horizontal overflow ${result.scrollWidth}>${result.innerWidth}`);
    }
    for (const expected of ['Nouveau RDV', 'Nouveau patient', 'Photo clinique', 'Scanner document', 'Encaisser rapidement']) {
      if (!result.actions.some(label => label?.includes(expected))) {
        throw new Error(`${viewport.width}: missing action ${expected}`);
      }
    }
    if (runtimeErrors.length) throw new Error(`${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);

    const name = `after-quick-hub-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outputDir, name) });
    evidence.push({ viewport, ...result, runtimeErrors, screenshot: name });
    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'runtime-evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));
