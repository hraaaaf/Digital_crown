import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC05_AFTER_URL || 'http://127.0.0.1:5181';
const outputRoot = process.env.PC05_EVIDENCE_DIR || '../artifacts/pc05-notifications-after';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA1LWhlYWQiLCJleHAiOjIwMDAwMDAwMDB9.audit';

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
          context: { access_id: 'pc05-after-access', relationship_type: 'SELF', patient: { display_name: 'Aya Audit' } },
          paired_at: '2026-09-20T20:00:00Z',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/agenda')) {
        return new Response(JSON.stringify({ items: [{
          appointment_ref: 'appointment-audit',
          datetime_start: '2026-09-22T10:00:00',
          duration_minutes: 30,
          motif: '',
          status: 'CONFIRMÉ',
          scheduling_type: 'EXACT_TIME',
        }] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/shares') || url.pathname.endsWith('/questionnaires') || url.pathname.endsWith('/consents')) {
        return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/notifications') && method === 'GET') {
        return new Response(JSON.stringify({
          preferences: { appointments: true, documents: true, questionnaires: true, consents: true },
          items: [
            {
              notification_id: 'notification-consent',
              category: 'consents',
              kind: 'CONSENT_PENDING',
              title: 'Signature en attente',
              message: 'Consentement éclairé — traitement',
              created_at: '2026-09-20T19:00:00Z',
              due_at: '2026-09-23T18:00:00Z',
              priority: 'action',
            },
            {
              notification_id: 'notification-appointment',
              category: 'appointments',
              kind: 'APPOINTMENT_REMINDER',
              title: 'Rendez-vous à venir',
              message: 'Un rendez-vous est prévu prochainement avec votre cabinet.',
              created_at: '2026-09-20T19:00:00Z',
              due_at: '2026-09-22T10:00:00Z',
              priority: 'reminder',
            },
          ],
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
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
      await page.locator('[data-pc05-notifications]').waitFor();
      await page.getByText('Signature en attente', { exact: true }).waitFor();
      await page.getByText('Rendez-vous à venir', { exact: true }).waitFor();
      await page.getByLabel('Régler les notifications').click();
      await page.locator('[data-pc05-settings]').waitFor();

      const controls = await page.locator('[data-pc05-notifications] button').evaluateAll(nodes =>
        nodes.map(node => ({ height: node.getBoundingClientRect().height, width: node.getBoundingClientRect().width }))
      );
      if (controls.some(control => control.height < 44)) throw new Error('PC05 actionable control below 44px');
      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (horizontalOverflow) throw new Error('PC05 AFTER horizontal overflow');

      const screenshot = `${browserName}-notifications-${viewport.width}x${viewport.height}.png`;
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
