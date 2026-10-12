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
    let apiCalls = 0;
    page.on('pageerror', err => errors.push(err.message));
    page.on('request', req => { if (/\/api\/|https?:\/\/(?!127\.0\.0\.1)/i.test(req.url())) apiCalls++; });
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
    const result = { viewport: vp.label, before, after, importDisabled, apiCalls, errors };
    results.push(result);
    if (!importDisabled || apiCalls > 0 || errors.length > 0 ||
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
