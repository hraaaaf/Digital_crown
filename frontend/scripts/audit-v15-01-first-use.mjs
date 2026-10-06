import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/fue-v15-01');
fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const productHead = process.env.PRODUCT_HEAD || 'unknown';
const profiles = [
  { label: 'tablet', width: 768, height: 1024 },
  { label: 'desktop', width: 1280, height: 900 },
];

const evidence = [];
const apiContext = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const topologyResponse = await apiContext.get('/api/health/topology');
const dbResponse = await apiContext.get('/api/health/db');
const topology = await topologyResponse.json().catch(() => null);
const db = await dbResponse.json().catch(() => null);
await apiContext.dispose();

for (const profile of profiles) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: profile.width, height: profile.height } });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const http5xx = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', err => pageErrors.push(err.message));
  page.on('response', res => { if (res.status() >= 500) http5xx.push({ status: res.status(), url: res.url() }); });

  await page.goto('http://127.0.0.1:5173/hub?select=1', { waitUntil: 'networkidle', timeout: 30000 });
  await page.screenshot({ path: path.join(outDir, profile.label + '-01-hub.png'), fullPage: true });

  const controlCard = page.locator('[data-hub-experience="control"]');
  await controlCard.waitFor({ state: 'visible', timeout: 10000 });
  await controlCard.click();
  await page.waitForURL('**/control-center', { timeout: 10000 });
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: path.join(outDir, profile.label + '-02-control-center.png'), fullPage: true });

  const bodyText = (await page.locator('body').innerText()).replace(/\s+/g, ' ').trim();
  const buttons = await page.getByRole('button').allTextContents();
  const placeholder = bodyText.includes('en cours de construction');
  const exposesTopology = /LAN|TLS|serveur|base de données|topologie|adresse|réseau/i.test(bodyText)
    && !placeholder;
  const hasActionableRemediation = buttons.some(text => /tester|vérifier|réessayer|connecter|diagnostic|copier|configurer/i.test(text));

  evidence.push({
    profile,
    url: page.url(),
    placeholder,
    exposesTopology,
    hasActionableRemediation,
    buttons,
    consoleErrors,
    pageErrors,
    http5xx,
    horizontalOverflow: await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1),
  });

  await context.close();
  await browser.close();
}

const report = {
  productHead,
  topologyHttpStatus: topologyResponse.status(),
  topology,
  dbHttpStatus: dbResponse.status(),
  db,
  profiles: evidence,
  success: topologyResponse.ok() && dbResponse.ok() && evidence.every(item =>
    !item.placeholder
    && item.exposesTopology
    && item.hasActionableRemediation
    && item.pageErrors.length === 0
    && item.http5xx.length === 0
    && !item.horizontalOverflow
  ),
};
fs.writeFileSync(path.join(outDir, 'fue-v15-01-report.json'), JSON.stringify(report, null, 2));
console.log('FUE_V15_01_REPORT ' + JSON.stringify(report));
if (!report.success) {
  console.error('FUE_V15_01_FAIL: installer first-use path is not actionable from Control Center');
  process.exit(1);
}
console.log('FUE_V15_01_PASS');
