import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const beforeUrl = process.env.PC01_BEFORE_URL || 'http://127.0.0.1:5174';
const afterUrl = process.env.PC01_AFTER_URL || 'http://127.0.0.1:5175';
const outputRoot = process.env.PC01_EVIDENCE_DIR || '../artifacts/pc01-patient-wallet';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const deviceToken = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzAxLWRldmljZSIsImV4cCI6MjAwMDAwMDAwMH0.audit';

await fs.mkdir(path.join(outputRoot, 'before'), { recursive: true });
await fs.mkdir(path.join(outputRoot, 'after'), { recursive: true });

async function clearVault(page, base) {
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => new Promise((resolve, reject) => {
    const request = indexedDB.deleteDatabase('digital-crown-patient-companion');
    request.onsuccess = () => resolve(null);
    request.onerror = () => reject(request.error);
    request.onblocked = () => resolve(null);
  }));
}

async function installRoutes(page, mode = 'online') {
  await page.route('**/api/**', async route => {
    if (mode === 'offline') return route.abort('internetdisconnected');
    const url = new URL(route.request().url());
    if (url.pathname === '/api/patient-companion/pair' && route.request().method() === 'POST') {
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({
        access_token: deviceToken,
        context: { access_id: 'pc01-audit-access', relationship_type: 'SELF', patient: { display_name: 'Aya Audit' } },
        paired_at: '2026-09-19T18:00:00Z',
        storage_policy: 'local_encrypted_device',
      })});
    }
    if (url.pathname.endsWith('/appointments')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [
        { id: 11, datetime_start: '2026-09-22T09:30:00Z', duration_minutes: 30, motif: 'Contrôle orthodontique', status: 'CONFIRME' },
      ]})});
    }
    if (url.pathname.endsWith('/shares')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [
        { share_id: 'share-doc-1', resource_type: 'document', resource_id: 21, title: 'Ordonnance septembre', document_type: 'ORDONNANCE' },
        { share_id: 'share-media-1', resource_type: 'media', resource_id: 22, title: 'Radiographie de contrôle', asset_type: 'RADIOGRAPH' },
      ]})});
    }
    if (url.pathname.endsWith('/me')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ contexts: [] })});
    }
    return route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
  });
}

async function pair(page) {
  await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
  await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
  await page.getByText('Appairer avec le code', { exact: true }).click();
  await page.getByText('Aya Audit', { exact: true }).waitFor({ timeout: 10000 }).catch(async () => {
    const pageBody = await page.locator('body').innerText();
    throw new Error('PC01 pairing did not reach home. BODY=' + pageBody.slice(0, 2000));
  });
}

async function probe(page) {
  return page.evaluate(async ({ deviceToken }) => {
    const db = await new Promise((resolve, reject) => {
      const request = indexedDB.open('digital-crown-patient-companion', 1);
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
    const key = await read('device-aes-key');
    db.close();
    const webStorage = [localStorage, sessionStorage].flatMap(storage =>
      Array.from({ length: storage.length }, (_, i) => storage.getItem(storage.key(i) || '') || '')
    ).join('|');
    return {
      hasCiphertext: typeof envelope?.ciphertext === 'string' && envelope.ciphertext.length > 20,
      plaintextAppointmentLeak: JSON.stringify(envelope || {}).includes('Contrôle orthodontique'),
      plaintextDocumentLeak: JSON.stringify(envelope || {}).includes('Ordonnance septembre'),
      tokenLeak: JSON.stringify(envelope || {}).includes(deviceToken) || webStorage.includes(deviceToken),
      keyAlgorithm: key?.algorithm?.name ?? null,
      keyExtractable: key?.extractable ?? null,
    };
  }, { deviceToken });
}

async function capture(browserName, browser, phase, viewport) {
  const base = phase === 'before' ? beforeUrl : afterUrl;
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => {
    const message = error.message || '';
    const expectedHarnessNoise =
      /Importing a module script failed/i.test(message) ||
      /dev-sw\.js\?dev-sw due to access control checks/i.test(message);
    if (!expectedHarnessNoise) errors.push(message);
  });
  await installRoutes(page, 'online');
  await clearVault(page, base);
  await page.goto(`${base}/companion`, { waitUntil: 'domcontentloaded' });
  await pair(page);

  if (phase === 'after') {
    await page.locator('[data-pc01-sync]').click();
    await page.getByText('Contrôle orthodontique', { exact: true }).waitFor();
    await page.getByText('Ordonnance septembre', { exact: true }).waitFor();
  }

  const onlineShot = `${browserName}-wallet-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputRoot, phase, onlineShot), fullPage: true });

  let offline = null;
  if (phase === 'after') {
    const encrypted = await probe(page);
    await page.unroute('**/api/**');
    await installRoutes(page, 'offline');
    const requestCount = [];
    page.on('request', request => { if (request.url().includes('/api/')) requestCount.push(request.url()); });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.getByText('Contrôle orthodontique', { exact: true }).waitFor();
    const offlineShot = `${browserName}-offline-reload-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outputRoot, phase, offlineShot), fullPage: true });
    offline = {
      screenshot: offlineShot,
      text: await page.locator('body').innerText(),
      encrypted,
      apiRequestsAfterReload: requestCount.length,
    };
  }

  const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (horizontalOverflow) throw new Error(`${phase}/${browserName}/${viewport.width}: horizontal overflow`);
  if (errors.length) throw new Error(errors.join(' | '));
  evidence.push({ browser: browserName, phase, viewport, screenshot: onlineShot, horizontalOverflow, offline });
  await context.close();
}

for (const [name, type] of Object.entries(browsers)) {
  const browser = await type.launch({ headless: true });
  try {
    for (const viewport of viewports) {
      await capture(name, browser, 'before', viewport);
      await capture(name, browser, 'after', viewport);
    }
  } finally {
    await browser.close();
  }
}

await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));
