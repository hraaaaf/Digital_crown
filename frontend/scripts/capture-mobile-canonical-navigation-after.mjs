import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.MOBILE_EVIDENCE_URL || 'http://127.0.0.1:5173/mobile/demo?demo=1';
const outputDir = process.env.MOBILE_EVIDENCE_DIR || '../artifacts/mobile-canonical-navigation-after';
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];

function near(actual, expected, tolerance = 1) {
  return Math.abs(actual - expected) <= tolerance;
}

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
    await nav.waitFor({ state: 'visible' });

    const geometry = await page.evaluate(() => {
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      const quick = document.querySelector('button[aria-label="Ouvrir les actions rapides"]');
      const legacyFab = document.querySelector('button[aria-label="Ajouter un rendez-vous"]');
      if (!(nav instanceof HTMLElement)) throw new Error('MOB-4 nav missing');
      if (!(quick instanceof HTMLElement)) throw new Error('MOB-4 central quick action missing');
      const navBox = nav.getBoundingClientRect();
      const quickBox = quick.getBoundingClientRect();
      const legacyStyle = legacyFab instanceof HTMLElement ? getComputedStyle(legacyFab) : null;
      return {
        navBox: { x: navBox.x, y: navBox.y, width: navBox.width, height: navBox.height },
        quickBox: { x: quickBox.x, y: quickBox.y, width: quickBox.width, height: quickBox.height },
        navText: nav.textContent || '',
        navButtons: nav.querySelectorAll('button').length,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        legacyFabPresent: Boolean(legacyFab),
        legacyFabVisibility: legacyStyle?.visibility || null,
        legacyFabPointerEvents: legacyStyle?.pointerEvents || null,
      };
    });

    if (geometry.navButtons !== 5) throw new Error(`${viewport.width}: expected 5 permanent nav buttons, got ${geometry.navButtons}`);
    for (const label of ['Aujourd’hui', 'Patients', 'Assistant', 'Plus']) {
      if (!geometry.navText.includes(label)) throw new Error(`${viewport.width}: missing canonical nav label ${label}`);
    }
    for (const legacy of ['Finance', 'Envois Labo', 'Sécurité']) {
      if (geometry.navText.includes(legacy)) throw new Error(`${viewport.width}: legacy permanent nav label still present: ${legacy}`);
    }
    if (geometry.navBox.height !== 76) throw new Error(`${viewport.width}: nav height ${geometry.navBox.height}, expected 76`);
    if (geometry.quickBox.width !== 60 || geometry.quickBox.height !== 60) {
      throw new Error(`${viewport.width}: central action ${geometry.quickBox.width}x${geometry.quickBox.height}, expected 60x60`);
    }
    const expectedNavWidth = Math.min(viewport.width - 24, 720);
    const expectedNavX = (viewport.width - expectedNavWidth) / 2;
    if (!near(geometry.navBox.width, expectedNavWidth) || !near(geometry.navBox.x, expectedNavX)) {
      throw new Error(`${viewport.width}: nav geometry diverges ${JSON.stringify(geometry.navBox)}`);
    }
    const quickCenter = geometry.quickBox.x + geometry.quickBox.width / 2;
    if (!near(quickCenter, viewport.width / 2)) {
      throw new Error(`${viewport.width}: central action is not centered (${quickCenter})`);
    }
    if (geometry.legacyFabPresent && (geometry.legacyFabVisibility !== 'hidden' || geometry.legacyFabPointerEvents !== 'none')) {
      throw new Error(`${viewport.width}: legacy Agenda FAB remains visible/interactable`);
    }
    if (geometry.horizontalOverflow) throw new Error(`${viewport.width}: overflow ${geometry.scrollWidth}>${geometry.innerWidth}`);

    await page.getByRole('button', { name: 'Ouvrir les actions rapides' }).click();
    await page.locator('[data-mobile-quick-action-hub]').waitFor({ state: 'visible' });
    for (const action of ['Nouveau RDV', 'Nouveau patient', 'Photo clinique', 'Scanner document', 'Encaisser rapidement']) {
      await page.getByText(action, { exact: true }).waitFor({ state: 'visible' });
    }
    await page.getByRole('button', { name: 'Fermer les actions rapides' }).click();
    await page.locator('[data-mobile-quick-action-hub]').waitFor({ state: 'detached' });

    await nav.getByText('Plus', { exact: true }).click();
    await page.locator('[data-mobile-more-menu]').waitFor({ state: 'visible' });
    for (const destination of ['Finance', 'Envois Labo', 'Sécurité']) {
      await page.getByText(destination, { exact: true }).waitFor({ state: 'visible' });
    }
    await page.getByText('Finance', { exact: true }).click();
    await page.locator('[data-mobile-more-menu]').waitFor({ state: 'detached' });
    const plusCurrent = await nav.getByText('Plus', { exact: true }).locator('..').getAttribute('aria-current');
    if (plusCurrent !== 'page') throw new Error(`${viewport.width}: Plus is not active for a secondary tab`);

    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.locator('[data-mobile-bottom-nav]').waitFor({ state: 'visible' });
    if (runtimeErrors.length) throw new Error(`${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);

    const screenshot = `after-canonical-nav-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outputDir, screenshot) });
    evidence.push({ viewport, ...geometry, runtimeErrors, screenshot });
    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'runtime-evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));
