#!/usr/bin/env node
/**
 * Exact source component browser proof, no cabinet backend, no deployment.
 * The PDF is the backend A4 fixture created in the preceding workflow step.
 * Chromium mobile viewport is NOT a real Safari/iPhone certification.
 */
import { chromium } from 'playwright';
import { createServer } from 'vite';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const root = process.cwd();
const output = path.resolve(root, '../artifacts/cephalo-pdf-l3-human-review/browser');
const pdf = await readFile(path.resolve(root, '../artifacts/cephalo-pdf-l3-human-review/a4-modern-no-images.pdf'));
const manifest = JSON.parse(await readFile(path.resolve(root, '../artifacts/cephalo-pdf-l3-human-review/manifest.json'), 'utf8'));
const expected = manifest.documents.find(x => x.pdf === 'a4-modern-no-images.pdf')?.sha256;
const actual = crypto.createHash('sha256').update(pdf).digest('hex');
if (!expected || actual !== expected) throw new Error('Browser PDF differs from exact-SHA backend artifact');
await mkdir(output, { recursive: true });
const server = await createServer({
  server: { host: '127.0.0.1', port: 4189, strictPort: true },
  clearScreen: false,
});
await server.listen();
const browser = await chromium.launch();
const results = [];
try {
  for (const viewport of [
    { name: 'desktop-chromium', width: 1440, height: 900 },
    { name: 'mobile-chromium', width: 390, height: 844 },
  ]) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
      isMobile: viewport.width < 500,
      hasTouch: viewport.width < 500,
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', err => errors.push(err.message));
    await page.route('**/ceph-l3-preview-fixture.pdf', route => route.fulfill({
      status: 200, contentType: 'application/pdf', body: pdf,
    }));
    await page.goto('http://127.0.0.1:4189/tests/visual/ceph-l3-live-preview.html', { waitUntil: 'networkidle' });
    const dialog = page.getByRole('dialog');
    await dialog.waitFor({ timeout: 20000 });
    const frame = page.locator('iframe[title^="Aperçu PDF"]');
    await frame.waitFor({ timeout: 15000 });
    const print = page.getByRole('button', { name: 'Imprimer' });
    await print.waitFor({ state: 'visible', timeout: 15000 });
    await print.waitFor({ state: 'attached' });
    await page.waitForFunction(() => {
      const button = [...document.querySelectorAll('button')].find(x => x.textContent?.includes('Imprimer'));
      return !!button && !button.disabled;
    }, null, { timeout: 15000 });
    const download = page.getByRole('link', { name: 'Télécharger PDF' });
    await download.waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'Plein écran' }).waitFor({ state: 'visible' });
    const parity = await page.evaluate(() => {
      const iframe = document.querySelector('iframe[title^="Aperçu PDF"]');
      const anchor = document.querySelector('a[download]');
      return iframe?.getAttribute('src')?.split('#')[0] === anchor?.getAttribute('href');
    });
    if (!parity) throw new Error('Download and preview URLs differ');
    if (errors.length) throw new Error('React runtime errors: ' + errors.join('; '));
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
    if (overflow) throw new Error('Horizontal page overflow');
    const screenshot = `ceph-l3-preview-${viewport.name}-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(output, screenshot), animations: 'disabled' });
    results.push({
      viewport, screenshot, pdf_sha256: actual,
      preview_download_blob_parity: true,
      print_button_enabled: true,
      print_dialog_opened: false,
      source: 'actual LivePreview.tsx; actual backend-generated synthetic PDF',
    });
    await context.close();
  }
} finally {
  await browser.close();
  await server.close();
}
await writeFile(path.join(output, 'browser-manifest.json'),
  JSON.stringify({ sha: manifest.commit, results, caveat: 'Chromium only; print dialog and Safari not verified' }, null, 2));
console.log(JSON.stringify({ browserCaptures: results.length, sha: manifest.commit }));
