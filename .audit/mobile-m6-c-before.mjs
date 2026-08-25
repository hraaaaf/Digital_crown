import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-c-before-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];

const server = await createServer({ server: { host: '127.0.0.1', port: 4196, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

async function snap(page, name) {
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
}

async function capture(width, height) {
  const context = await browser.newContext({
    viewport: { width, height },
    screen: { width, height },
    deviceScaleFactor: 1,
    hasTouch: true,
    isMobile: true,
    serviceWorkers: 'block',
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });

  await page.goto('http://127.0.0.1:4196/mobile-m6-c-before.html', { waitUntil: 'networkidle' });
  await page.getByText('BENNANI Sara', { exact: true }).first().waitFor({ state: 'visible', timeout: 10000 });

  const appointmentButton = page.getByRole('button', { name: /BENNANI Sara/ }).first();
  await appointmentButton.click();
  const signatureEntry = page.getByRole('button', { name: /Signature au Fauteuil/i });
  await signatureEntry.waitFor({ state: 'visible' });
  await snap(page, `signature-entry-${width}x${height}`);
  const entryRect = await signatureEntry.boundingBox();

  await signatureEntry.click();
  await page.getByRole('heading', { name: 'Signature au Fauteuil', exact: true }).waitFor({ state: 'visible' });
  const canvas = page.locator('canvas');
  await canvas.waitFor({ state: 'visible' });
  await snap(page, `signature-blank-${width}x${height}`);

  const beforeCount = await page.evaluate(() => window.__M6C_BLANK_SAVE_COUNT__ || 0);
  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  const afterCount = await page.evaluate(() => window.__M6C_BLANK_SAVE_COUNT__ || 0);
  const blankPayloadLength = await page.evaluate(() => (window.__M6C_LAST_SIGNATURE__ || '').length);

  const canvasBox = await canvas.boundingBox();
  if (!canvasBox) throw new Error('Canvas bounding box unavailable');
  await page.mouse.move(canvasBox.x + canvasBox.width * 0.18, canvasBox.y + canvasBox.height * 0.55);
  await page.mouse.down();
  for (let i = 1; i <= 10; i++) {
    const x = canvasBox.x + canvasBox.width * (0.18 + i * 0.064);
    const y = canvasBox.y + canvasBox.height * (0.55 + Math.sin(i / 2) * 0.18);
    await page.mouse.move(x, y, { steps: 2 });
  }
  await page.mouse.up();
  await snap(page, `signature-drawn-${width}x${height}`);

  const metrics = await page.evaluate(() => {
    const root = document.documentElement;
    const canvasEl = document.querySelector('canvas');
    const canvasRect = canvasEl?.getBoundingClientRect();
    const select = document.querySelector('select');
    const selectRect = select?.getBoundingClientRect();
    const buttons = Array.from(document.querySelectorAll('button')).map(button => {
      const rect = button.getBoundingClientRect();
      return {
        text: (button.textContent || '').replace(/\s+/g, ' ').trim(),
        width: rect.width,
        height: rect.height,
      };
    });
    const signatureButton = buttons.find(button => /Signature au Fauteuil/i.test(button.text));
    const clearButton = buttons.find(button => button.text === 'Effacer');
    const saveButton = buttons.find(button => button.text === 'Enregistrer');
    const closeTextButton = buttons.find(button => button.text === 'Fermer');
    const iconOnlyButtons = buttons.filter(button => button.text === '');
    return {
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      signatureEntry: signatureButton || null,
      clearButton: clearButton || null,
      saveButton: saveButton || null,
      closeTextButton: closeTextButton || null,
      smallestIconOnlyButton: iconOnlyButtons.sort((a, b) => a.height - b.height)[0] || null,
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

  captures.push({
    width,
    height,
    entryRect,
    blankSaveAccepted: afterCount === beforeCount + 1,
    blankPayloadLength,
    metrics,
    errors,
  });
  await context.close();
}

try {
  await capture(390, 844);
  await capture(430, 932);
  await capture(768, 1024);

  const relevantHeights = captures.flatMap(item => [
    item.entryRect?.height || 0,
    item.metrics.clearButton?.height || 0,
    item.metrics.saveButton?.height || 0,
    item.metrics.closeTextButton?.height || 0,
    item.metrics.selectHeight || 0,
    item.metrics.smallestIconOnlyButton?.height || 0,
  ]).filter(Boolean);

  const report = {
    productHead,
    count: 9,
    viewports: captures,
    blankSaveAcceptedEveryViewport: captures.every(item => item.blankSaveAccepted),
    canvasBackingFixed300x180: captures.every(item => item.metrics.canvasBackingWidth === 300 && item.metrics.canvasBackingHeight === 180),
    canvasCssBackingMismatch: captures.some(item => Math.abs(item.metrics.canvasScaleX - 1) > 0.02 || Math.abs(item.metrics.canvasScaleY - 1) > 0.02),
    minRelevantTouchHeight: relevantHeights.length ? Math.min(...relevantHeights) : 0,
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };

  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.count !== 9 || !report.noHorizontalOverflow || !report.noUnexpectedRuntimeErrors) {
    throw new Error('M6-C BEFORE evidence integrity failed');
  }
} finally {
  await browser.close();
  await server.close();
}
