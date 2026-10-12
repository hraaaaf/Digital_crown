import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';

const base = process.env.V15_05_2B_PROOF_URL || 'http://127.0.0.1:4198/mapping-studio-proof.html';
const out = path.resolve('artifacts/v15-05-2b-mapping-studio');
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const results = [];
const sizes = [
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];
try {
  for (const viewport of sizes) {
    const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = [];
    const outgoing = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('request', request => {
      if (/\/api\/|\/auth\/|\/patients\//i.test(request.url())) outgoing.push('UNEXPECTED_API_REQUEST');
    });
    await page.goto(base, { waitUntil: 'networkidle', timeout: 60000 });
    await page.getByTestId('mapping-source-step').waitFor();
    await page.screenshot({
      path: path.join(out, 'after-inventory-' + viewport.width + 'x' + viewport.height + '.png'),
      fullPage: true, animations: 'disabled',
    });
    await page.getByRole('button', { name: /Choisir les correspondances/i }).click();
    await page.getByTestId('mapping-decisions-step').waitFor();
    await page.screenshot({
      path: path.join(out, 'after-decisions-' + viewport.width + 'x' + viewport.height + '.png'),
      fullPage: true, animations: 'disabled',
    });
    const boxes = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      bodyWidth: document.body.scrollWidth,
      tableChoices: document.querySelectorAll('select[id^="table-choice-"]').length,
      columnChoices: document.querySelectorAll('select[id^="column-choice-"]').length,
      tablesNeedingDecision: Array.from(document.querySelectorAll('select[id^="table-choice-"]'))
        .every(select => select.value === ''),
      importButtonPresent: !!document.querySelector('[data-testid="migration-import-disabled"]'),
    }));
    const row = { viewport: viewport.width + 'x' + viewport.height, ...boxes, errors, outgoing };
    results.push(row);
    await context.close();
  }
} finally {
  await browser.close();
}
await fs.writeFile(path.join(out, 'report.json'), JSON.stringify({
  proof_sha: process.env.GITHUB_SHA || 'not-bound',
  after: results,
  before: 'Route /migration-sql absent from parent #853; no honest UI BEFORE screenshot exists.',
  source: 'Synthetic-only Vite dev entrypoint, CSP connect-src none',
}, null, 2));
console.log(JSON.stringify(results, null, 2));
if (results.some(r =>
  r.documentWidth > r.viewportWidth
  || r.bodyWidth > r.viewportWidth
  || r.tableChoices !== 3
  || r.columnChoices !== 8
  || !r.tablesNeedingDecision
  || r.importButtonPresent
  || r.errors.length > 0
  || r.outgoing.length > 0
)) {
  throw new Error('05.2-B responsive browser proof failed closed');
}
