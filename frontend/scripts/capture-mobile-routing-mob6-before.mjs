import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:5173';
const artifactDir = process.env.ARTIFACT_DIR || '../artifacts/mobile-routing-mob6-before';
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const viewports = [
  { name: '390', width: 390, height: 844 },
  { name: '430', width: 430, height: 932 },
  { name: '768', width: 768, height: 1024 },
];
const routes = ['/patients', '/agenda', '/stock'];

await fs.mkdir(artifactDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = { productHead, baseURL, routes, viewports: [] };

for (const viewport of viewports) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    userAgent: `Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1 MOB6-${viewport.name}`,
  });
  const viewportResult = { ...viewport, probes: [] };

  for (const route of routes) {
    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', err => pageErrors.push(String(err)));
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
    const response = await page.goto(`${baseURL}${route}`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(250);
    const finalPath = new URL(page.url()).pathname + new URL(page.url()).search;
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    const loginVisible = await page.locator('input[type="password"]').count() > 0;
    const onboardingVisible = await page.locator('text=/QR|appair|onboarding|scanner/i').count() > 0;
    const slug = route.slice(1).replaceAll('/', '-') || 'root';
    await page.screenshot({ path: path.join(artifactDir, `${viewport.name}-${slug}.png`), fullPage: true });
    viewportResult.probes.push({
      route,
      status: response?.status() ?? null,
      finalPath,
      loginVisible,
      onboardingVisible,
      horizontalOverflow: overflow,
      pageErrors,
      consoleErrors,
    });
    await page.close();
  }

  report.viewports.push(viewportResult);
  await context.close();
}

await browser.close();
await fs.writeFile(path.join(artifactDir, 'report.json'), JSON.stringify(report, null, 2));

const probes = report.viewports.flatMap(v => v.probes);
if (!probes.every(p => p.status === 200)) throw new Error('MOB-6 BEFORE expected HTTP 200 for all probes');
if (!probes.every(p => p.finalPath === '/login')) throw new Error(`MOB-6 BEFORE drift: expected direct desktop deep-links to land on /login, got ${JSON.stringify(probes.map(p => [p.route,p.finalPath]))}`);
if (!probes.every(p => p.loginVisible)) throw new Error('MOB-6 BEFORE drift: desktop login not visible for every probe');
if (probes.some(p => p.horizontalOverflow)) throw new Error('MOB-6 BEFORE horizontal overflow detected');
if (probes.some(p => p.pageErrors.length)) throw new Error('MOB-6 BEFORE page errors detected');

console.log(JSON.stringify(report, null, 2));
