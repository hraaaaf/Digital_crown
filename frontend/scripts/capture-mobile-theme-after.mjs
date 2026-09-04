import { chromium } from 'playwright';
import fs from 'node:fs/promises';

const baseUrl = process.env.MOBILE_EVIDENCE_URL || 'http://127.0.0.1:5173/mobile/demo?demo=1';
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

function patientUrl() {
  const url = new URL(baseUrl);
  url.searchParams.set('tab', 'patients');
  return url.toString();
}

async function assertThemeContract(page) {
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
}

await fs.mkdir(outDir, { recursive: true });
const browser = await chromium.launch({ headless: true });

try {
  for (const [width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height } });
    await context.addInitScript((theme) => {
      localStorage.setItem('digitalcrown_mobile_theme', JSON.stringify(theme));
    }, fixture);

    const dashboard = await context.newPage();
    await dashboard.goto(baseUrl, { waitUntil: 'networkidle' });
    await dashboard.locator('[data-dc-mobile-shell]').waitFor();
    await dashboard.waitForTimeout(350);
    await assertThemeContract(dashboard);
    await dashboard.screenshot({
      path: `${outDir}/after-dashboard-${width}x${height}.png`,
      fullPage: false,
    });
    await dashboard.close();

    const patient = await context.newPage();
    await patient.goto(patientUrl(), { waitUntil: 'networkidle' });
    await patient.locator('[data-mobile-patient-cockpit]').waitFor();
    await patient.waitForTimeout(350);
    await assertThemeContract(patient);
    await patient.screenshot({
      path: `${outDir}/after-patient-cockpit-${width}x${height}.png`,
      fullPage: false,
    });
    await patient.close();
    await context.close();
  }
} finally {
  await browser.close();
}
