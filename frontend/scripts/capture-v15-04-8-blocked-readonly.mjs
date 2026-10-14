/** Browser screenshots for REAL UI component in an isolated synthetic fixture.
 * Not a full Settings before/after and never physical-device certification.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const outDir = path.resolve('artifacts/v15-04-8-blocked-readonly');
fs.mkdirSync(outDir, { recursive: true });
const base = process.env.VISUAL_BASE_URL || 'http://127.0.0.1:4198';
const head = process.env.GITHUB_SHA_SOURCE || 'unknown';
const browser = await chromium.launch({ headless: true });
const report = [];
try {
  for (const viewport of [
    { width: 360, height: 780 },
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1280, height: 800 },
  ]) {
    for (const zoom of [100, 200]) {
      const context = await browser.newContext({viewport, deviceScaleFactor: 1});
      const page = await context.newPage();
      const forbiddenRequests = [];
      const pageErrors = [];
      page.on('pageerror', error => pageErrors.push(String(error)));
      page.on('console', message => {
        if (message.type() === 'error') pageErrors.push(message.text());
      });
      page.on('request', request => {
        if (/\/print-jobs|\/print-request|\/documents\/.*\.pdf/i.test(request.url())) {
          forbiddenRequests.push(request.url());
        }
      });
      const response = await page.goto(base + '/visual-lab/blocked-jobs.html', {
        waitUntil: 'networkidle', timeout: 45000,
      });
      try {
        await page.locator('[data-print-job-status="uncertain"]').first().waitFor({ timeout: 30000 });
      } catch (error) {
        const diagnosis = {
          viewport, zoom, responseStatus: response?.status() ?? null,
          currentUrl: page.url(),
          bodyExcerpt: (await page.locator('body').innerText().catch(() => '')).slice(0, 1200),
          pageErrors, forbiddenRequests,
          message: String(error),
        };
        fs.writeFileSync(path.join(outDir, `failure-${viewport.width}-text${zoom}.json`),
          JSON.stringify(diagnosis, null, 2) + '\n');
        await page.screenshot({
          path: path.join(outDir, `failure-${viewport.width}-text${zoom}.png`),
          fullPage: true,
        }).catch(() => {});
        throw new Error('BLOCKED_READONLY_RENDER_DIAGNOSTIC ' + JSON.stringify(diagnosis));
      }
      if (pageErrors.length) throw new Error('BLOCKED_READONLY_PAGE_ERRORS ' + JSON.stringify(pageErrors));
      if (zoom === 200) await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
      const measured = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        width: document.documentElement.clientWidth,
        cards: document.querySelectorAll('[data-print-job-status="uncertain"]').length,
        forbiddenControls: [...document.querySelectorAll('button')].filter(
          button => !button.textContent?.includes('Actualiser les états'),
        ).length + document.querySelectorAll('a,form,iframe,object,embed').length,
      }));
      if (measured.cards !== 2 || measured.forbiddenControls !== 0
          || measured.scrollWidth > measured.width || forbiddenRequests.length) {
        throw new Error(JSON.stringify({viewport,zoom,measured,forbiddenRequests}));
      }
      const filename = `${viewport.width}x${viewport.height}-text${zoom}.png`;
      await page.screenshot({path: path.join(outDir,filename),fullPage: true});
      report.push({viewport,zoom,filename,...measured,forbiddenRequests:forbiddenRequests.length});
      await context.close();
    }
  }
} finally { await browser.close(); }
fs.writeFileSync(path.join(outDir,'evidence.json'),JSON.stringify({
  sourceSha:head,
  captureType:'COMPONENT_ONLY_NOT_FULL_SETTINGS_BEFORE_AFTER',
  realDeviceTested:false,
  printerActivated:false,
  report,
},null,2)+'\n');
console.log('BLOCKED_READONLY_BROWSER_PASS cases='+report.length+' no_print_controls=1 no_horizontal_overflow=1 synthetic_only=1');
