import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC07_BEFORE_URL || 'http://127.0.0.1:5184';
const outputRoot = process.env.PC07_EVIDENCE_DIR || '../artifacts/pc07-emergency-photo-before';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA3LWJlZm9yZSIsImV4cCI6MjAwMDAwMDAwMH0.audit';

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

for (const [browserName, browserType] of Object.entries(browsers)) {
  const browser = await browserType.launch({ headless: true });
  try {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport });
      await installHarness(context);
      const page = await context.newPage();
      await clearVault(page);
      await page.goto(`${baseUrl}/companion`, { waitUntil: 'domcontentloaded' });
      await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
      await page.getByText('Appairer avec le code', { exact: true }).click();
      await page.getByText('Aya Urgence', { exact: true }).waitFor();
      if (await page.locator('[data-pc07-emergency-photo]').count()) {
        throw new Error('PC07 unexpectedly present in BEFORE');
      }
      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC07 BEFORE horizontal overflow');
      const screenshot = `${browserName}-home-${viewport.width}x${viewport.height}.png`;
      await fs.mkdir(path.join(outputRoot, 'before'), { recursive: true });
      await page.screenshot({ path: path.join(outputRoot, 'before', screenshot), fullPage: true });
      evidence.push({ browser: browserName, phase: 'before', viewport, screenshot, horizontalOverflow });
      await context.close();
    }
  } finally {
    await browser.close();
  }
}
await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
