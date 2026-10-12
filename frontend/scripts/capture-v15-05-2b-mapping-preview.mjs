import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const out = path.resolve('artifacts/v15-05-2b-mapping');
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const viewports = [
  { label: '390x844', width: 390, height: 844 },
  { label: '1280x900', width: 1280, height: 900 },
];
const results = [];
try {
  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();
    const errors = [];
    const blockedFontRequests = [];
    const unexpectedNetworkRequests = [];
    page.on('pageerror', err => errors.push(err.message));
    // Existing global CSS imports public Google Fonts; intercept them rather than
    // treating a stylesheet fetch as a backend PHI upload. Block ALL nonlocal
    // requests, and fail if any endpoint other than known font hosts is attempted.
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.hostname === '127.0.0.1' && !url.pathname.startsWith('/api/')) {
        return route.continue();
      }
      if (['fonts.googleapis.com', 'fonts.gstatic.com'].includes(url.hostname)) {
        blockedFontRequests.push(url.hostname);
        return route.abort();
      }
      unexpectedNetworkRequests.push(url.origin + url.pathname.slice(0, 160));
      return route.abort();
    });
    await page.goto('http://127.0.0.1:4195/migration-preview.html?filled=0', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Mapping Studio' }).waitFor();
    const before = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      steps: document.querySelectorAll('[aria-current="step"]').length,
      noPatientData: !document.body.textContent?.includes('PATIENT IDENTIFIABLE'),
    }));
    await page.screenshot({ path: path.join(out, 'BEFORE-'+vp.label+'.png'),
      fullPage: true, animations: 'disabled' });

    await page.goto('http://127.0.0.1:4195/migration-preview.html?filled=1', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /Examiner les correspondances/ }).click();
    await page.getByRole('combobox', { name: 'Destination table patients' }).selectOption('patients');
    await page.getByRole('combobox', { name: 'Colonne patients.id' }).selectOption('id');
    await page.getByRole('combobox', { name: 'Colonne patients.name' }).selectOption('name');
    await page.getByRole('combobox', { name: 'Colonne patients.password_hash' }).selectOption('__unmapped__');
    await page.getByRole('combobox', { name: 'Destination table old_documents' }).selectOption('__unmapped__');
    await page.getByRole('combobox', { name: 'Colonne old_documents.legacy_ref' }).selectOption('__unmapped__');
    await page.getByRole('button', { name: 'Vérifier' }).click();
    const importButton = page.getByRole('button', { name: 'Importer — indisponible' });
    const importDisabled = await importButton.isDisabled();
    const after = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      summary: !!document.querySelector('[aria-label="Synthèse de préparation"]'),
      steps: document.querySelectorAll('[aria-current="step"]').length,
    }));
    await page.screenshot({ path: path.join(out, 'AFTER-'+vp.label+'.png'),
      fullPage: true, animations: 'disabled' });
    const result = { viewport: vp.label, before, after, importDisabled, blockedFontRequests, unexpectedNetworkRequests, errors };
    results.push(result);
    if (!importDisabled || unexpectedNetworkRequests.length > 0 || errors.length > 0 ||
      before.scrollWidth > before.width + 1 || after.scrollWidth > after.width + 1 ||
      !after.summary || before.steps !== 1 || after.steps !== 1 || !before.noPatientData) {
      throw new Error('Visual proof failed closed: '+JSON.stringify(result));
    }
    await context.close();
  }
} finally {
  await browser.close();
}
await fs.writeFile(path.join(out, 'report.json'), JSON.stringify({
  prHead: process.env.GITHUB_SHA || null, fixture: 'synthetic-only',
  note: 'Harness captures are NOT live authenticated staff runtime proof',
  results,
}, null, 2));
console.log(JSON.stringify(results, null, 2));
