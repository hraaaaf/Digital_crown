import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const beforeUrl = process.env.PC00_BEFORE_URL || 'http://127.0.0.1:5174';
const afterUrl = process.env.PC00_AFTER_URL || 'http://127.0.0.1:5175';
const outputRoot = process.env.PC00_EVIDENCE_DIR || '../artifacts/pc00-patient-companion';
const viewports = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
];

await fs.mkdir(path.join(outputRoot, 'before'), { recursive: true });
await fs.mkdir(path.join(outputRoot, 'after'), { recursive: true });

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function installRoutes(page) {
  await page.route('**/health', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ status: 'ok' }),
  }));
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/patient-companion/pair' && route.request().method() === 'POST') {
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'pc00-audit-device-token',
          context: {
            access_id: 'pc00-audit-access',
            relationship_type: 'SELF',
            patient: { display_name: 'Aya Audit', prenom: 'Aya', nom: 'Audit' },
          },
          paired_at: '2026-09-19T18:00:00Z',
          storage_policy: 'local_encrypted_device',
        }),
      });
    }
    return route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'Not authenticated' }) });
  });
}

async function capture(phase, scenario, viewport) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const runtimeErrors = [];
  page.on('pageerror', error => runtimeErrors.push(error.message));
  await installRoutes(page);

  const base = phase === 'before' ? beforeUrl : afterUrl;
  await page.goto(`${base}/companion`, { waitUntil: 'domcontentloaded' });

  if (phase === 'before') {
    await page.waitForURL(/\/login(?:\?|$)/, { timeout: 10000 }).catch(() => undefined);
  } else {
    await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
    if (scenario === 'home') {
      await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
      await page.getByText('Appairer avec le code', { exact: true }).click();
      await page.getByText('Aya Audit', { exact: true }).waitFor();
    }
  }

  const screenshot = `${scenario}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputRoot, phase, screenshot), fullPage: false });

  const snapshot = await page.evaluate(() => {
    const touchTargets = [...document.querySelectorAll('button,a,input,select')].map(element => {
      const rect = element.getBoundingClientRect();
      return { tag: element.tagName, width: Math.round(rect.width), height: Math.round(rect.height) };
    }).filter(item => item.width > 0 && item.height > 0);
    return {
      pathname: window.location.pathname,
      text: document.body.innerText,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
      touchTargets,
    };
  });

  if (snapshot.horizontalOverflow) throw new Error(`${phase}/${scenario}/${viewport.width}: horizontal overflow`);
  if (runtimeErrors.length) throw new Error(`${phase}/${scenario}/${viewport.width}: ${runtimeErrors.join(' | ')}`);

  evidence.push({ phase, scenario, viewport, screenshot, ...snapshot });
  await context.close();
}

try {
  for (const viewport of viewports) {
    for (const scenario of ['welcome', 'home']) {
      await capture('before', scenario, viewport);
      await capture('after', scenario, viewport);
    }
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence.map(item => ({
  phase: item.phase,
  scenario: item.scenario,
  viewport: item.viewport,
  screenshot: item.screenshot,
  pathname: item.pathname,
})), null, 2));
