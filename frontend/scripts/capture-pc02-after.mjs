import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const afterUrl = process.env.PC02_AFTER_URL || 'http://127.0.0.1:5175';
const phases = ['after'];
const outputRoot = process.env.PC02_EVIDENCE_DIR || '../artifacts/pc02-agenda-after';
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

async function installFetchHarness(context) {
  await context.addInitScript(({ deviceToken }) => {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
      const raw = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      if (!url.pathname.startsWith('/api/patient-companion/')) return nativeFetch(input, init);

      const afterReloadKey = 'pc02-api-calls-after-reload';
      if (sessionStorage.getItem('pc02-offline-reload') === '1') {
        const count = Number(sessionStorage.getItem(afterReloadKey) || '0') + 1;
        sessionStorage.setItem(afterReloadKey, String(count));
        throw new TypeError('Failed to fetch');
      }

      if (url.pathname === '/api/patient-companion/pair' && (init.method || 'GET').toUpperCase() === 'POST') {
        return new Response(JSON.stringify({
          access_token: deviceToken,
          context: { access_id: 'pc02-audit-access', relationship_type: 'SELF', patient: { display_name: 'Aya Audit' } },
          paired_at: '2026-09-19T18:00:00Z',
          storage_policy: 'local_encrypted_device',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/agenda/practitioners')) {
        return new Response(JSON.stringify({ items: [
          { practitioner_ref: '6f36c8eb-e0ae-4702-9bc7-34d436965ade', display_name: 'Dr Aya Audit' },
        ]}), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/agenda/slots')) {
        return new Response(JSON.stringify({ items: [
          { slot_ref: 'e3ed0d13-d446-4478-a2a7-bf62407f373d', datetime_start: '2026-09-23T10:00:00Z', duration_minutes: 30, expires_at: '2026-09-23T09:15:00Z' },
          { slot_ref: '3e642013-b5f8-4168-bbf7-b80a4615f940', datetime_start: '2026-09-23T10:30:00Z', duration_minutes: 30, expires_at: '2026-09-23T09:15:00Z' },
        ]}), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/agenda')) {
        return new Response(JSON.stringify({ items: [
          { appointment_ref: '8fd11a5e-4a63-4d8a-bca8-2d4b6ef3a901', datetime_start: '2026-09-22T09:30:00Z', duration_minutes: 30, motif: 'Contrôle orthodontique', status: 'CONFIRME' },
        ]}), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/shares')) {
        return new Response(JSON.stringify({ items: [
          { share_id: 'share-doc-1', resource_type: 'document', title: 'Ordonnance septembre', document_type: 'ORDONNANCE' },
          { share_id: 'share-media-1', resource_type: 'media', title: 'Radiographie de contrôle', asset_type: 'RADIOGRAPH' },
        ]}), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/me')) {
        return new Response(JSON.stringify({ contexts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 404, headers: { 'Content-Type': 'application/json' } });
    };
  }, { deviceToken });
}

async function pair(page) {
  await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
  await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
  await page.getByText('Appairer avec le code', { exact: true }).click();
  await page.getByText('Aya Audit', { exact: true }).waitFor({ timeout: 10000 }).catch(async () => {
    const pageBody = await page.locator('body').innerText();
    throw new Error('PC02 pairing did not reach home. BODY=' + pageBody.slice(0, 2000));
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
  const base = afterUrl;
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
  await installFetchHarness(context);
  await clearVault(page, base);
  await page.goto(`${base}/companion`, { waitUntil: 'domcontentloaded' });
  await pair(page);

  if (true) {
    await page.locator('[data-pc01-sync]').click();
    await page.getByText('Contrôle orthodontique', { exact: true }).waitFor();
    await page.getByText('Ordonnance septembre', { exact: true }).waitFor();
  }

  await page.locator('[data-pc02-agenda]').waitFor();
  await page.locator('[data-pc02-book]').click();
  await page.locator('[data-pc02-booking-panel]').waitFor();
  await page.getByRole('button', { name: 'Voir les créneaux' }).click();
  await page.getByText('10:00', { exact: true }).waitFor();
  const controls = await page.locator('[data-pc02-booking-panel] button, [data-pc02-booking-panel] select, [data-pc02-booking-panel] input').evaluateAll(nodes =>
    nodes.map(node => ({ width: node.getBoundingClientRect().width, height: node.getBoundingClientRect().height }))
  );
  if (controls.some(control => control.height < 48)) {
    throw new Error(`${phase}/${browserName}/${viewport.width}: agenda control below 48px`);
  }
  const onlineShot = `${browserName}-agenda-picker-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputRoot, phase, onlineShot), fullPage: true });

  let offline = null;
  if (false) {
    const encrypted = await probe(page);
    await page.evaluate(() => {
      sessionStorage.setItem('pc02-api-calls-after-reload', '0');
      sessionStorage.setItem('pc02-offline-reload', '1');
    });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.getByText('Contrôle orthodontique', { exact: true }).waitFor();
    const offlineShot = `${browserName}-offline-reload-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outputRoot, phase, offlineShot), fullPage: true });
    offline = {
      screenshot: offlineShot,
      text: await page.locator('body').innerText(),
      encrypted,
      apiRequestsAfterReload: Number(await page.evaluate(() => sessionStorage.getItem('pc02-api-calls-after-reload') || '0')),
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
      for (const phase of phases) await capture(name, browser, phase, viewport);
    }
  } finally {
    await browser.close();
  }
}

await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));
