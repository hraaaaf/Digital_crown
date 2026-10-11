// Evidence-only station UX probe. Mocked API: never label as patient/real-hardware E2E.
import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.FUE_PHASE || 'after';
const out = path.resolve(`artifacts/fue-v15-04-3-${phase}`);
await fs.mkdir(out, { recursive: true });
const base = process.env.FUE_BASE_URL || 'http://127.0.0.1:4197';
const sha = process.env.FUE_EVALUATED_SHA || null;
const viewports = [
  { width: 390, height: 844 }, { width: 430, height: 932 },
  { width: 768, height: 1024 }, { width: 1280, height: 900 },
];
const locales = [
  { code: 'fr', button: 'Français', underConstruction: 'Cette étape est en cours de construction.' },
  { code: 'ar', button: 'العربية', underConstruction: 'هذه الخطوة قيد الإنشاء.' },
  { code: 'en', button: 'English', underConstruction: 'This step is under construction.' },
];
const bootstrap = {
  workstationId: 'fue043-workstation', displayName: 'Station LAB',
  defaultExperience: 'station', stationLocked: true,
  stationEscapeAuthorized: false, stationEscapeExpiresAt: null,
  enrollmentRequired: false, authenticated: true,
  pinConfigured: true, canManage: false, canConfigurePin: false,
};
const browser = await chromium.launch({ headless: true });
const rows = [];
try {
  for (const viewport of viewports) {
    for (const locale of locales) {
      const context = await browser.newContext({ viewport });
      await context.route('**/api/workstation/bootstrap*', route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(bootstrap),
      }));
      await context.route('**/api/workstation/state*', route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify(bootstrap),
      }));
      await context.route('**/api/workstation/patient-session/config*', route => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify({ fallbackMode: 'disabled' }),
      }));
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', err => errors.push(err.message));
      await page.goto(`${base}/station`, { waitUntil: 'networkidle', timeout: 30_000 });
      await page.locator('[data-workstation-experience="station"]').waitFor();
      await page.getByRole('button', { name: locale.button, exact: true }).click();
      for (const action of ['documents', 'help']) {
        const actionButton = page.locator(`[data-station-action="${action}"]`);
        await actionButton.click();
        await page.locator(`[data-station-screen="${action}"]`).waitFor();
        const actual = await page.evaluate(() => ({
          innerWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          buttons: Array.from(document.querySelectorAll('button')).map(button => button.textContent?.trim()).filter(Boolean),
          text: document.body.innerText,
          heading: document.querySelector('h1')?.textContent || '',
          language: document.querySelector('[data-workstation-experience="station"]')?.getAttribute('lang'),
        }));
        const name = `${phase}-${action}-${locale.code}-${viewport.width}x${viewport.height}.png`;
        await page.screenshot({ path: path.join(out, name), fullPage: true, animations: 'disabled' });
        const row = {
          phase, action, locale: locale.code, viewport: `${viewport.width}x${viewport.height}`,
          screenshot: name, heading: actual.heading,
          overflow: actual.scrollWidth > actual.innerWidth,
          underConstruction: actual.text.includes(locale.underConstruction),
          buttonCount: actual.buttons.length, languageCorrect: actual.language === locale.code,
          errors: [...errors],
        };
        rows.push(row);
        const nav = page.locator('[data-station-screen]').getAttribute('data-station-screen');
        if (await nav !== action) throw Error(`Screen switch failed: ${action}`);
        await page.getByRole('button', { name: locale.code === 'fr' ? 'Retour à l’accueil' : locale.code === 'en' ? 'Back to welcome' : 'العودة إلى الاستقبال' }).click();
        await page.locator('[data-station-screen="home"]').waitFor();
      }
      await context.close();
    }
  }
} finally { await browser.close(); }
const report = {
  phase, sha, simulator: true,
  semantics: 'UI lab browser mock; NOT patient physical experience and NOT care-sheet retrieval E2E',
  rows, failed: rows.filter(row => row.overflow || row.errors.length || !row.languageCorrect),
  observations: {
    documentRetrievalUiReady: !rows.some(row => row.action === 'documents' && row.underConstruction),
    note: 'Documents currently indicates en cours de construction; this is a truthful product gap, not masked by check success.',
  },
};
await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ phase, count: rows.length, failures: report.failed.length, documentRetrievalUiReady: report.observations.documentRetrievalUiReady }));
if (report.failed.length || !rows.length) process.exitCode = 1;
