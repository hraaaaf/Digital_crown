import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-c-after-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];

const server = await createServer({ server: { host: '127.0.0.1', port: 4197, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

async function snap(page, name) {
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
}

async function capture(width, height) {
  const context = await browser.newContext({
    viewport: { width, height }, screen: { width, height }, deviceScaleFactor: 2,
    hasTouch: true, isMobile: true, serviceWorkers: 'block',
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });

  await page.goto('http://127.0.0.1:4197/mobile-m6-c-after.html', { waitUntil: 'networkidle' });
  await page.getByText('BENNANI Sara', { exact: true }).first().waitFor({ state: 'visible', timeout: 10000 });
  await page.getByRole('button', { name: /BENNANI Sara/ }).first().click();

  const signatureEntry = page.getByRole('button', { name: /Signature au Fauteuil/i });
  await signatureEntry.waitFor({ state: 'visible' });
  const entryRect = await signatureEntry.boundingBox();
  await snap(page, `signature-entry-${width}x${height}`);

  await signatureEntry.click();
  await page.getByRole('heading', { name: 'Signature au Fauteuil', exact: true }).waitFor({ state: 'visible' });
  const canvas = page.locator('canvas');
  await canvas.waitFor({ state: 'visible' });
  await page.waitForFunction(() => {
    const c = document.querySelector('canvas');
    if (!c) return false;
    const r = c.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    return Math.abs(c.width - r.width * dpr) <= 2 && Math.abs(c.height - r.height * dpr) <= 2;
  });

  const saveButton = page.getByRole('button', { name: 'Enregistrer', exact: true });
  const blankSaveDisabled = await saveButton.isDisabled();
  const saveCountBefore = await page.evaluate(() => window.__M6C_SAVE_COUNT__ || 0);
  await snap(page, `signature-blank-${width}x${height}`);

  const canvasBox = await canvas.boundingBox();
  if (!canvasBox) throw new Error('Canvas bounding box unavailable');
  await page.mouse.move(canvasBox.x + canvasBox.width * 0.16, canvasBox.y + canvasBox.height * 0.58);
  await page.mouse.down();
  for (let i = 1; i <= 12; i++) {
    const x = canvasBox.x + canvasBox.width * (0.16 + i * 0.058);
    const y = canvasBox.y + canvasBox.height * (0.56 + Math.sin(i / 2) * 0.16);
    await page.mouse.move(x, y, { steps: 2 });
  }
  await page.mouse.up();
  await page.getByText('Signature prête à enregistrer', { exact: true }).waitFor({ state: 'visible' });
  const saveEnabledAfterInk = !(await saveButton.isDisabled());
  await snap(page, `signature-drawn-${width}x${height}`);

  await saveButton.click();
  const saveCountAfter = await page.evaluate(() => window.__M6C_SAVE_COUNT__ || 0);
  const payloadIsPng = await page.evaluate(() => (window.__M6C_LAST_SIGNATURE__ || '').startsWith('data:image/png;base64,'));

  const metrics = await page.evaluate(() => {
    const root = document.documentElement;
    const canvasEl = document.querySelector('canvas');
    const canvasRect = canvasEl?.getBoundingClientRect();
    const select = document.querySelector('select');
    const selectRect = select?.getBoundingClientRect();
    const buttons = Array.from(document.querySelectorAll('button')).map(button => {
      const rect = button.getBoundingClientRect();
      return { text: (button.textContent || '').replace(/\s+/g, ' ').trim(), aria: button.getAttribute('aria-label') || '', width: rect.width, height: rect.height };
    });
    const signatureButton = buttons.find(button => /Signature au Fauteuil/i.test(button.text));
    const clearButton = buttons.find(button => button.text === 'Effacer');
    const saveButton = buttons.find(button => button.text === 'Enregistrer');
    const closeTextButton = buttons.find(button => button.text === 'Fermer');
    const closeIconButton = buttons.find(button => button.aria === 'Fermer la signature');
    return {
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      signatureEntry: signatureButton || null,
      clearButton: clearButton || null,
      saveButton: saveButton || null,
      closeTextButton: closeTextButton || null,
      closeIconButton: closeIconButton || null,
      selectHeight: selectRect?.height || 0,
      canvasCssWidth: canvasRect?.width || 0,
      canvasCssHeight: canvasRect?.height || 0,
      canvasBackingWidth: canvasEl?.width || 0,
      canvasBackingHeight: canvasEl?.height || 0,
      devicePixelRatio: window.devicePixelRatio,
      canvasScaleX: canvasRect && canvasRect.width ? (canvasEl?.width || 0) / canvasRect.width : 0,
      canvasScaleY: canvasRect && canvasRect.height ? (canvasEl?.height || 0) / canvasRect.height : 0,
    };
  });

  const relevant = [entryRect?.height || 0, metrics.clearButton?.height || 0, metrics.saveButton?.height || 0, metrics.closeTextButton?.height || 0, metrics.closeIconButton?.height || 0, metrics.closeIconButton?.width || 0, metrics.selectHeight || 0].filter(Boolean);
  captures.push({
    width, height, entryRect, blankSaveDisabled, saveEnabledAfterInk,
    blankSaveCountUnchanged: saveCountBefore === 0,
    saveCountIncrementedOnce: saveCountAfter === 1,
    payloadIsPng,
    minTouch: Math.min(...relevant), metrics, errors,
  });
  await context.close();
}

try {
  await capture(390, 844);
  await capture(430, 932);
  await capture(768, 1024);

  const report = {
    productHead,
    count: 9,
    viewports: captures,
    minRelevantTouchHeight: Math.min(...captures.map(item => item.minTouch)),
    blankSaveBlockedEveryViewport: captures.every(item => item.blankSaveDisabled && item.blankSaveCountUnchanged),
    inkEnablesSaveEveryViewport: captures.every(item => item.saveEnabledAfterInk && item.saveCountIncrementedOnce && item.payloadIsPng),
    canvasDprExact: captures.every(item => Math.abs(item.metrics.canvasScaleX - item.metrics.devicePixelRatio) <= 0.02 && Math.abs(item.metrics.canvasScaleY - item.metrics.devicePixelRatio) <= 0.02),
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };

  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.count !== 9 || report.minRelevantTouchHeight < 48 || !report.blankSaveBlockedEveryViewport || !report.inkEnablesSaveEveryViewport || !report.canvasDprExact || !report.noHorizontalOverflow || !report.noUnexpectedRuntimeErrors) {
    throw new Error('M6-C AFTER evidence gate failed');
  }
} finally {
  await browser.close();
  await server.close();
}
