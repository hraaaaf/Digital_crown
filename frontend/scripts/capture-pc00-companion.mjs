import { chromium, webkit } from 'playwright';
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

const browserTypes = { chromium, webkit };
const evidence = [];

async function clearPatientVault(page) {
  await page.goto('about:blank');
  await page.goto(afterUrl, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => new Promise((resolve, reject) => {
    const request = indexedDB.deleteDatabase('digital-crown-patient-companion');
    request.onsuccess = () => resolve(null);
    request.onerror = () => reject(request.error);
    request.onblocked = () => resolve(null);
  }));
}

async function installFetchHarness(context) {
  await context.addInitScript(() => {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
      const raw = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      if (!url.pathname.startsWith('/api/patient-companion/')) return nativeFetch(input, init);
      if (url.pathname === '/api/patient-companion/pair' && (init.method || 'GET').toUpperCase() === 'POST') {
        return new Response(JSON.stringify({
          access_token: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzAwLWRldmljZSIsImV4cCI6MjAwMDAwMDAwMH0.audit',
          context: {
            access_id: 'pc00-audit-access',
            relationship_type: 'SELF',
            patient: { display_name: 'Aya Audit', prenom: 'Aya', nom: 'Audit' },
          },
          paired_at: '2026-09-19T18:00:00Z',
          storage_policy: 'local_encrypted_device',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response(JSON.stringify({ detail: 'Not authenticated' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    };
  });
}

async function capture(browserName, browser, phase, scenario, viewport) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const runtimeErrors = [];
  page.on('pageerror', error => {
    const message = error.message || '';
    const expectedHarnessNoise =
      phase === 'after' &&
      (/^TypeError: Importing a module script failed\.?$/i.test(message) ||
       /dev-sw\.js\?dev-sw due to access control checks/i.test(message));
    if (!expectedHarnessNoise) runtimeErrors.push(message);
  });
  const base = phase === 'before' ? beforeUrl : afterUrl;
  if (phase === 'after') await clearPatientVault(page);
  await installFetchHarness(context);
  await page.goto(`${base}/companion`, { waitUntil: 'domcontentloaded' });

  if (phase === 'before') {
    await page.waitForURL(/\/login(?:\?|$)/, { timeout: 10000 }).catch(() => undefined);
  } else {
    await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
    if (scenario === 'home') {
      await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
      await page.getByText('Appairer avec le code', { exact: true }).click();
      await page.getByText('Aya Audit', { exact: true }).waitFor({ timeout: 10000 }).catch(async () => {
        const pageBody = await page.locator('body').innerText();
        throw new Error('PC00 pairing did not reach home. BODY=' + pageBody.slice(0, 2000));
      });
    }
  }

  const screenshot = `${browserName}-${scenario}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputRoot, phase, screenshot), fullPage: false });

  const snapshot = await page.evaluate(async ({ phase, scenario }) => {
    const touchTargets = [...document.querySelectorAll('button,a,input,select')].map(element => {
      const rect = element.getBoundingClientRect();
      return { tag: element.tagName, width: Math.round(rect.width), height: Math.round(rect.height) };
    }).filter(item => item.width > 0 && item.height > 0);

    let storageProbe = null;
    if (phase === 'after' && scenario === 'home') {
      const db = await new Promise((resolve, reject) => {
        const request = indexedDB.open('digital-crown-patient-companion');
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      const read = key => new Promise((resolve, reject) => {
        const tx = db.transaction('vault', 'readonly');
        const request = tx.objectStore('vault').get(key);
        request.onsuccess = () => resolve(request.result ?? null);
        request.onerror = () => reject(request.error);
      });
      const envelope = await read('companion-state');
      const deviceKey = await read('device-aes-key');
      db.close();
      const readStorageValues = storage => Array.from({ length: storage.length }, (_, index) => {
        const key = storage.key(index);
        return key ? storage.getItem(key) || '' : '';
      });
      const webStorage = [
        ...readStorageValues(localStorage),
        ...readStorageValues(sessionStorage),
      ].join('|');
      storageProbe = {
        envelopeVersion: envelope?.version ?? null,
        hasCiphertext: typeof envelope?.ciphertext === 'string' && envelope.ciphertext.length > 20,
        envelopeLeaksAccessToken: JSON.stringify(envelope || {}).includes('eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzAwLWRldmljZSIsImV4cCI6MjAwMDAwMDAwMH0.audit'),
        keyAlgorithm: deviceKey?.algorithm?.name ?? null,
        keyExtractable: deviceKey?.extractable ?? null,
        webStorageLeaksAccessToken: webStorage.includes('eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzAwLWRldmljZSIsImV4cCI6MjAwMDAwMDAwMH0.audit'),
        webStorageLeaksManualCode: webStorage.includes('ABCD-EFGH-JKLM'),
      };
    }

    return {
      pathname: window.location.pathname,
      text: document.body.innerText,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
      touchTargets,
      storageProbe,
    };
  }, { phase, scenario });

  if (snapshot.horizontalOverflow) throw new Error(`${phase}/${scenario}/${viewport.width}: horizontal overflow`);
  if (runtimeErrors.length) throw new Error(`${phase}/${scenario}/${viewport.width}: ${runtimeErrors.join(' | ')}`);

  evidence.push({ browser: browserName, phase, scenario, viewport, screenshot, ...snapshot });
  await context.close();
}

for (const [browserName, browserType] of Object.entries(browserTypes)) {
  const browser = await browserType.launch({ headless: true });
  try {
    for (const viewport of viewports) {
      for (const scenario of ['welcome', 'home']) {
        await capture(browserName, browser, 'before', scenario, viewport);
        await capture(browserName, browser, 'after', scenario, viewport);
      }
    }
  } finally {
    await browser.close();
  }
}

await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence.map(item => ({
  browser: item.browser,
  phase: item.phase,
  scenario: item.scenario,
  viewport: item.viewport,
  screenshot: item.screenshot,
  pathname: item.pathname,
})), null, 2));
