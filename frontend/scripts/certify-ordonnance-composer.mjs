// Dedicated visual gate for the real DrugRow prescription composer fixture.
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const outDir = path.resolve('../artifacts/ordonnance-composer');
fs.mkdirSync(outDir, { recursive: true });

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const browser = await chromium.launch({ headless: true });
const captures = [];

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'dark' });
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));

  await page.goto('http://127.0.0.1:5173/ordonnance-composer-fixture.html', {
    waitUntil: 'networkidle',
    timeout: 60000,
  });
  await page.locator('[data-composer-visual-fixture]').waitFor({ state: 'visible', timeout: 20000 });
  const cards = page.locator('[data-ordonnance-drug-card]');
  await cards.nth(1).waitFor({ state: 'visible', timeout: 20000 });
  await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'));
  await page.waitForTimeout(180);

  const cardCount = await cards.count();
  if (cardCount !== 2) {
    throw new Error(`Expected 2 DrugRow cards at ${viewport.width}x${viewport.height}, got ${cardCount}; pageErrors=${pageErrors.join(' | ')}`);
  }

  const scenes = [];
  for (const [index, label] of [[0, 'regular'], [1, 'pain']]) {
    const card = cards.nth(index);
    await card.scrollIntoViewIfNeeded();
    await page.waitForTimeout(160);

    const metrics = await card.evaluate(el => {
      const visible = node => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
      };
      const composer = el.querySelector('[data-ordonnance-prescription-composer]');
      const controls = composer
        ? [...composer.querySelectorAll('select')].filter(visible)
        : [];
      const persistedLabel = composer
        ? [...composer.querySelectorAll('div')].find(node => node.textContent?.trim() === 'Phrase persistée')
        : null;
      const persistedValue = persistedLabel?.nextElementSibling || null;
      const rect = el.getBoundingClientRect();
      return {
        card: { width: rect.width, height: rect.height, left: rect.left, right: rect.right },
        composerVisible: Boolean(composer),
        controlCount: controls.length,
        controlMinHeight: controls.length ? Math.min(...controls.map(control => control.getBoundingClientRect().height)) : null,
        summaryVisible: Boolean(persistedValue && visible(persistedValue)),
        summaryText: persistedValue?.textContent?.trim() || '',
      };
    });

    const shot = `ordonnance-composer-${viewport.width}x${viewport.height}-${label}.png`;
    await page.screenshot({ path: path.join(outDir, shot), fullPage: false });
    scenes.push({ label, screenshot: shot, metrics });
  }

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  captures.push({ viewport, scenes, horizontalOverflow: overflow, pageErrors });
  await context.close();
}

const failures = [];
const expectedSummary = {
  regular: '1 comprimé, 3 fois par jour pendant 7 jours, après les repas.',
  pain: '1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.',
};

for (const capture of captures) {
  if (capture.horizontalOverflow) failures.push(`${capture.viewport.width}: horizontal overflow`);
  if (capture.pageErrors.length) failures.push(`${capture.viewport.width}: page errors ${capture.pageErrors.join(' | ')}`);
  for (const scene of capture.scenes) {
    if (!scene.metrics.composerVisible) failures.push(`${capture.viewport.width}-${scene.label}: composer missing`);
    if (scene.metrics.controlCount !== 4) failures.push(`${capture.viewport.width}-${scene.label}: expected 4 controls, got ${scene.metrics.controlCount}`);
    if ((scene.metrics.controlMinHeight || 0) < 43.5) failures.push(`${capture.viewport.width}-${scene.label}: control height ${scene.metrics.controlMinHeight}`);
    if (!scene.metrics.summaryVisible) failures.push(`${capture.viewport.width}-${scene.label}: persisted phrase missing`);
    if (scene.metrics.summaryText !== expectedSummary[scene.label]) {
      failures.push(`${capture.viewport.width}-${scene.label}: unexpected persisted phrase ${scene.metrics.summaryText}`);
    }
  }
}

const report = {
  status: failures.length ? 'FAIL' : 'PASS',
  viewports: viewports.map(viewport => `${viewport.width}x${viewport.height}`),
  captures,
  failures,
};

fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
await browser.close();
if (failures.length) process.exit(1);
