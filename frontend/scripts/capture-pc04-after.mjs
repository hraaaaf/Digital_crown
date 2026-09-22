import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC04_AFTER_URL || 'http://127.0.0.1:5179';
const outputRoot = process.env.PC04_EVIDENCE_DIR || '../artifacts/pc04-consent-after';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA0LWhlYWQiLCJleHAiOjIwMDAwMDAwMDB9.audit';

async function installHarness(context) {
  await context.addInitScript(({ token }) => {
    window.open = () => null;
    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
      const raw = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      if (!url.pathname.startsWith('/api/patient-companion/')) return nativeFetch(input, init);
      const method = (init.method || 'GET').toUpperCase();
      if (url.pathname === '/api/patient-companion/pair' && method === 'POST') {
        return new Response(JSON.stringify({
          access_token: token,
          context: { access_id: 'pc04-after-access', relationship_type: 'SELF', patient: { display_name: 'Aya Audit' } },
          paired_at: '2026-09-20T19:00:00Z',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/agenda') || url.pathname.endsWith('/shares') || url.pathname.endsWith('/questionnaires')) {
        return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/consents') && method === 'GET') {
        return new Response(JSON.stringify({ items: [{
          consent_id: '11111111-1111-4111-8111-111111111111',
          share_id: '22222222-2222-4222-8222-222222222222',
          title: 'Consentement éclairé — traitement',
          document_type: 'DOCUMENT_LIBRE',
          document_version: 3,
          state: 'PENDING',
          created_at: '2026-09-20T19:00:00Z',
          qualified_electronic_signature: false,
        }] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.includes('/consents/') && url.pathname.endsWith('/document') && method === 'GET') {
        return new Response('%PDF-1.4\nPC04 visual fixture\n%%EOF', {
          status: 200,
          headers: { 'Content-Type': 'application/pdf' },
        });
      }
      return new Response('{}', { status: 404, headers: { 'Content-Type': 'application/json' } });
    };
  }, { token });
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
      await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
      await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
      await page.getByText('Appairer avec le code', { exact: true }).click();
      await page.getByText('Aya Audit', { exact: true }).waitFor();
      await page.locator('[data-pc01-sync]').click();
      await page.locator('[data-pc04-consent-vault]').waitFor();
      await page.getByText('Consentement éclairé — traitement', { exact: true }).waitFor();
      await page.getByText('Lire le document', { exact: true }).click();
      await page.locator('[data-pc04-signature]').waitFor();

      const buttons = await page.locator('[data-pc04-signature] button').evaluateAll(nodes =>
        nodes.map(node => ({ height: node.getBoundingClientRect().height, width: node.getBoundingClientRect().width }))
      );
      if (buttons.some(control => control.height < 48)) throw new Error('PC04 signature control below 48px');
      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC04 AFTER horizontal overflow');

      const screenshot = `${browserName}-consent-signature-${viewport.width}x${viewport.height}.png`;
      await fs.mkdir(path.join(outputRoot, 'after'), { recursive: true });
      await page.screenshot({ path: path.join(outputRoot, 'after', screenshot), fullPage: true });
      evidence.push({ browser: browserName, phase: 'after', viewport, screenshot, horizontalOverflow });
      await context.close();
    }
  } finally {
    await browser.close();
  }
}
await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
