import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC03_AFTER_URL || 'http://127.0.0.1:5177';
const outputRoot = process.env.PC03_EVIDENCE_DIR || '../artifacts/pc03-questionnaires-after';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzAzLWRldmljZSIsImV4cCI6MjAwMDAwMDAwMH0.audit';

async function installHarness(context) {
  await context.addInitScript(({ token }) => {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
      const raw = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      if (!url.pathname.startsWith('/api/patient-companion/')) return nativeFetch(input, init);
      const method = (init.method || 'GET').toUpperCase();
      if (url.pathname === '/api/patient-companion/pair' && method === 'POST') {
        return new Response(JSON.stringify({
          access_token: token,
          context: { access_id: 'pc03-audit-access', relationship_type: 'SELF', patient: { display_name: 'Aya Audit' } },
          paired_at: '2026-09-20T18:00:00Z',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/agenda')) {
        return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/shares')) {
        return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/questionnaires') && method === 'GET') {
        return new Response(JSON.stringify({ items: [{
          assignment_id: '36b861d2-e90e-4d4f-b6f4-c0c76b267219',
          questionnaire_id: '551cfa7a-5836-4d71-a6cf-ccebe864c752',
          title: 'Questionnaire médical du cabinet',
          version: 2,
          state: 'ASSIGNED',
          assigned_at: '2026-09-20T18:00:00Z',
          questions: [
            { id: 'q1', label: 'Question oui/non de démonstration', type: 'yes_no', required: true, options: [] },
            { id: 'q2', label: 'Choix de démonstration', type: 'single_choice', required: false, options: ['Option A', 'Option B'] },
            { id: 'q3', label: 'Information complémentaire', type: 'short_text', required: false, options: [] },
          ],
        }] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.includes('/questionnaires/') && url.pathname.endsWith('/submit') && method === 'POST') {
        return new Response(JSON.stringify({
          submission_id: '5b5d82c6-4b0d-4e12-a125-0b4f0a73d71e',
          status: 'PENDING_REVIEW',
          clinical_record_updated: false,
          submitted_at: '2026-09-20T18:10:00Z',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/me')) {
        return new Response(JSON.stringify({ contexts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
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

async function pair(page) {
  await page.goto(`${baseUrl}/companion`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
  await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
  await page.getByText('Appairer avec le code', { exact: true }).click();
  await page.getByText('Aya Audit', { exact: true }).waitFor();
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
      await page.locator('[data-pc01-sync]').click();
      await page.locator('[data-pc03-questionnaires]').waitFor();
      await page.getByText('Questionnaire médical du cabinet', { exact: true }).waitFor();
      await page.getByText('Remplir', { exact: true }).click();
      await page.locator('[data-pc03-form]').waitFor();
      const controls = await page.locator('[data-pc03-form] button, [data-pc03-form] select, [data-pc03-form] textarea').evaluateAll(nodes =>
        nodes.map(node => ({ height: node.getBoundingClientRect().height, width: node.getBoundingClientRect().width }))
      );
      if (controls.some(control => control.height < 48)) throw new Error('PC03 control below 48px');
      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC03 horizontal overflow');
      const screenshot = `${browserName}-questionnaire-form-${viewport.width}x${viewport.height}.png`;
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
