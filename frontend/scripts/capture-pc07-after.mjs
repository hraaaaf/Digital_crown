import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC07_AFTER_URL || 'http://127.0.0.1:5185';
const outputRoot = process.env.PC07_EVIDENCE_DIR || '../artifacts/pc07-emergency-photo-after';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA3LWFmdGVyIiwiZXhwIjoyMDAwMDAwMDAwfQ.audit';
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAATElEQVR4nO3PQQ0AIBDAsAP/nuGNAvZoFSzZOjNnyNi2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bdu2bf8F3gAB0EAB1hWfFgAAAABJRU5ErkJggg==', 'base64');

const cabinetSigning = {
  kty: 'EC', crv: 'P-256',
  x: 'ooF2PvMFbREFvvigvOWXERDaJr8FA7yxdgSqyLHasas',
  y: 'LSKBcZtWeiPKVaRkqAleLK9OgUWrnkESUSZESNYBzLw',
  kid: '0211a9af-b74c-45f9-8145-6edb869fc389', use: 'sig',
};
const cabinetEncryption = {
  kty: 'EC', crv: 'P-256',
  x: 'c_D97Il2E2m8QmmFRoZNiQTPFP4hB4iEucbbAWMlnfU',
  y: '9bhsEba_-W4JglHSxkqrKJqlOOWmB4KVQt6WrxpcsfQ',
  kid: 'c5c56d83-be92-41d4-87f5-9e56551f371a', use: 'enc',
};

async function installHarness(context) {
  await context.addInitScript(({ token, cabinetSigning, cabinetEncryption }) => {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
      const raw = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      if (!url.pathname.startsWith('/api/patient-companion/')) return nativeFetch(input, init);
      const method = (init.method || 'GET').toUpperCase();
      if (url.pathname === '/api/patient-companion/pair' && method === 'POST') {
        const request = JSON.parse(String(init.body || '{}'));
        const remote = request.remote_keys;
        return new Response(JSON.stringify({
          access_token: token,
          context: { access_id: '6ca78b1a-2a5b-4a85-8d71-6f997833c1f5', relationship_type: 'SELF', patient: { display_name: 'Aya Urgence' } },
          paired_at: '2026-09-21T09:00:00Z',
          remote_transport: remote ? {
            status: 'enrolled',
            protocol_version: 'dc-pc-remote-v1',
            keyset_id: 'pc07-visual-keyset',
            patient_signing_kid: remote.signing_kid,
            patient_encryption_kid: remote.encryption_kid,
            cabinet: {
              signing: { kid: cabinetSigning.kid, public_jwk: cabinetSigning },
              encryption: { kid: cabinetEncryption.kid, public_jwk: cabinetEncryption },
            },
          } : undefined,
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    };
  }, { token, cabinetSigning, cabinetEncryption });
}

async function clearVault(page) {
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => new Promise(resolve => {
    const request = indexedDB.deleteDatabase('digital-crown-patient-companion');
    request.onsuccess = () => resolve(null);
    request.onerror = () => resolve(null);
    request.onblocked = () => resolve(null);
  }));
}

async function pair(page) {
  await page.goto(`${baseUrl}/companion`, { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
  await page.getByText('Appairer avec le code', { exact: true }).click();
  await page.getByText('Aya Urgence', { exact: true }).waitFor();
  await page.locator('[data-pc07-emergency-photo]').waitFor();
}

async function forcePending(page) {
  await page.evaluate(async () => {
    const db = await new Promise((resolve, reject) => {
      const req = indexedDB.open('digital-crown-patient-companion', 2);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    const read = key => new Promise((resolve, reject) => {
      const tx = db.transaction('vault', 'readonly');
      const req = tx.objectStore('vault').get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    const key = await read('device-aes-key');
    const envelope = await read('companion-state');
    const decode = value => {
      const raw = atob(value);
      const out = new Uint8Array(raw.length);
      for (let i = 0; i < raw.length; i += 1) out[i] = raw.charCodeAt(i);
      return out;
    };
    const encode = bytes => {
      let raw = '';
      for (const b of bytes) raw += String.fromCharCode(b);
      return btoa(raw);
    };
    const clear = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: decode(envelope.iv) }, key, decode(envelope.ciphertext));
    const state = JSON.parse(new TextDecoder().decode(clear));
    const accessId = state.activeAccessId;
    const queue = state.cache[accessId]?.emergencyPhotos || [];
    if (!queue.length) throw new Error('PC07 visual queue missing');
    queue[0].state = 'remote_pending_ack';
    queue[0].updatedAt = new Date().toISOString();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(JSON.stringify(state)));
    const next = { version: 1, iv: encode(iv), ciphertext: encode(new Uint8Array(encrypted)) };
    await new Promise((resolve, reject) => {
      const tx = db.transaction('vault', 'readwrite');
      tx.objectStore('vault').put(next, 'companion-state');
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
    db.close();
  });
}

for (const [browserName, browserType] of Object.entries(browsers)) {
  const browser = await browserType.launch({ headless: true });
  try {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport });
      await installHarness(context);
      const page = await context.newPage();
      await clearVault(page);
      await pair(page);

      const section = page.locator('[data-pc07-emergency-photo]');
      const controls = await section.locator('button').evaluateAll(nodes => nodes.map(node => ({
        height: node.getBoundingClientRect().height,
        width: node.getBoundingClientRect().width,
      })));
      if (controls.some(control => control.height < 44)) throw new Error('PC07 control below 44px');
      let horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC07 idle horizontal overflow');

      await fs.mkdir(path.join(outputRoot, 'after'), { recursive: true });
      const idleShot = `${browserName}-idle-${viewport.width}x${viewport.height}.png`;
      await page.screenshot({ path: path.join(outputRoot, 'after', idleShot), fullPage: true });
      evidence.push({ browser: browserName, phase: 'idle', viewport, screenshot: idleShot, horizontalOverflow, controls });

      await section.locator('input[type=file]').setInputFiles({ name: 'emergency.png', mimeType: 'image/png', buffer: png });
      await page.getByText('Envoyer au cabinet', { exact: true }).waitFor();
      horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC07 preview horizontal overflow');
      const previewShot = `${browserName}-preview-${viewport.width}x${viewport.height}.png`;
      await page.screenshot({ path: path.join(outputRoot, 'after', previewShot), fullPage: true });
      evidence.push({ browser: browserName, phase: 'preview', viewport, screenshot: previewShot, horizontalOverflow });

      await forcePending(page);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.getByText('Reprendre l’envoi', { exact: true }).waitFor();
      if (await page.getByText('Photo reçue par le cabinet.', { exact: true }).count()) {
        throw new Error('PC07 pending state must not claim receipt');
      }
      horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC07 pending horizontal overflow');
      const pendingShot = `${browserName}-pending-${viewport.width}x${viewport.height}.png`;
      await page.screenshot({ path: path.join(outputRoot, 'after', pendingShot), fullPage: true });
      evidence.push({ browser: browserName, phase: 'pending', viewport, screenshot: pendingShot, horizontalOverflow });
      await context.close();
    }
  } finally {
    await browser.close();
  }
}
await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
