import { chromium } from 'playwright';
import fs from 'node:fs/promises';

const url = process.env.MOBILE_EVIDENCE_URL || 'http://127.0.0.1:5173/mobile/demo?demo=1';
const outDir = process.env.MOBILE_EVIDENCE_DIR || '../artifacts/mobile-theme-after';
const fixture = {
  selected_theme: 'elite',
  primary_color: '#003380',
  secondary_color: '#1e40af',
  accent_color: '#60a5fa',
  app_accent_color: null,
  font_fr: 'inter',
};
const viewports = [
  [390, 844],
  [430, 932],
  [768, 1024],
];

await fs.mkdir(outDir, { recursive: true });
const browser = await chromium.launch({ headless: true });

try {
  for (const [width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height } });
    await context.addInitScript((theme) => {
      localStorage.setItem('digitalcrown_mobile_theme', JSON.stringify(theme));
    }, fixture);
    const page = await context.newPage();
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.locator('[data-dc-mobile-shell]').waitFor();
    await page.waitForTimeout(400);

    const contract = await page.evaluate(() => ({
      theme: document.documentElement.dataset.theme,
      primary: document.documentElement.style.getPropertyValue('--primary').trim(),
      font: document.documentElement.style.getPropertyValue('--app-font-family').trim(),
      shellFont: getComputedStyle(document.querySelector('[data-dc-mobile-shell]')).fontFamily,
    }));

    if (contract.theme !== '') throw new Error(`Elite theme must use empty data-theme, got ${contract.theme}`);
    if (contract.primary.toLowerCase() !== '#003380') throw new Error(`Unexpected primary: ${contract.primary}`);
    if (!contract.font.includes('Inter')) throw new Error(`Runtime font token is not Inter: ${contract.font}`);
    if (!contract.shellFont.includes('Inter')) throw new Error(`Mobile shell does not consume runtime font: ${contract.shellFont}`);

    await page.screenshot({
      path: `${outDir}/after-${width}x${height}.png`,
      fullPage: false,
    });
    await context.close();
  }
} finally {
  await browser.close();
}
