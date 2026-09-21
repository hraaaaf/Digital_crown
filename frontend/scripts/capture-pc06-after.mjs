import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC06_AFTER_URL || 'http://127.0.0.1:5183';
const outputRoot = process.env.PC06_EVIDENCE_DIR || '../artifacts/pc06-finance-after';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA2LWhlYWQiLCJleHAiOjIwMDAwMDAwMDB9.audit';

const financePayload = {
  summary: { billed: 1800, collected: 600, remaining_due: 1200 },
  payments: [{ id: 1, amount: 600, method: 'CARTE', paid_at: '2026-09-20T10:00:00Z', source: 'acte' }],
  schedules: [{
    id: 3,
    title: 'Traitement orthodontique',
    total_amount: 1200,
    items: [
      { id: 5, label: 'Versement 1', amount: 600, due_date: '2026-10-01T00:00:00Z', paid_date: null, status: 'EN_ATTENTE' },
      { id: 6, label: 'Versement 2', amount: 600, due_date: '2026-11-01T00:00:00Z', paid_date: null, status: 'EN_ATTENTE' },
    ],
  }],
  invoices: [{
    share_id: 'share-1',
    document_id: 9,
    title: "Note d'honoraires septembre",
    amount: 1800,
    issued_at: '2026-09-01T00:00:00Z',
    download_path: '/api/patient-companion/contexts/pc06-after-access/finance/invoices/share-1/download',
  }],
  online_payment: { available: false },
};

async function installHarness(context) {
  await context.addInitScript(({ token, financePayload }) => {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
      const raw = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      if (!url.pathname.startsWith('/api/patient-companion/')) return nativeFetch(input, init);
      const method = (init.method || 'GET').toUpperCase();

      if (url.pathname === '/api/patient-companion/pair' && method === 'POST') {
        return new Response(JSON.stringify({
          access_token: token,
          context: { access_id: 'pc06-after-access', relationship_type: 'SELF', patient: { display_name: 'Aya Finance' } },
          paired_at: '2026-09-21T08:00:00Z',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/agenda') || url.pathname.endsWith('/shares') || url.pathname.endsWith('/questionnaires') || url.pathname.endsWith('/consents')) {
        return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/notifications')) {
        return new Response(JSON.stringify({
          items: [],
          preferences: { appointments: true, documents: true, questionnaires: true, consents: true },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/finance') && method === 'GET') {
        return new Response(JSON.stringify(financePayload), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 404, headers: { 'Content-Type': 'application/json' } });
    };
  }, { token, financePayload });
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
      await page.getByText('Aya Finance', { exact: true }).waitFor();
      await page.locator('[data-pc01-sync]').click();
      await page.locator('[data-pc06-finance]').waitFor();
      await page.getByText('Traitement orthodontique', { exact: true }).waitFor();
      await page.getByText("Note d'honoraires septembre", { exact: true }).waitFor();

      const controls = await page.locator('[data-pc06-finance] button').evaluateAll(nodes =>
        nodes.map(node => ({ height: node.getBoundingClientRect().height, width: node.getBoundingClientRect().width }))
      );
      if (controls.some(control => control.height < 44)) throw new Error('PC06 actionable control below 44px');

      const summaryLineCounts = await page.locator('[data-pc06-summary-value]').evaluateAll(nodes =>
        nodes.map(node => {
          const range = document.createRange();
          range.selectNodeContents(node);
          return range.getClientRects().length;
        })
      );
      if (summaryLineCounts.length !== 3 || summaryLineCounts.some(lines => lines !== 1)) {
        throw new Error(`PC06 summary amount wrapped: ${JSON.stringify(summaryLineCounts)}`);
      }

      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC06 AFTER horizontal overflow');
      if (await page.getByRole('button', { name: /payer/i }).count()) throw new Error('PC06 must not expose an online payment CTA');

      const screenshot = `${browserName}-finance-${viewport.width}x${viewport.height}.png`;
      await fs.mkdir(path.join(outputRoot, 'after'), { recursive: true });
      await page.screenshot({ path: path.join(outputRoot, 'after', screenshot), fullPage: true });
      evidence.push({
        browser: browserName,
        phase: 'after',
        viewport,
        screenshot,
        horizontalOverflow,
        financeControls: controls,
        summaryLineCounts,
      });
      await context.close();
    }
  } finally {
    await browser.close();
  }
}
await fs.writeFile(path.join(outputRoot, 'evidence.json'), JSON.stringify(evidence, null, 2));
