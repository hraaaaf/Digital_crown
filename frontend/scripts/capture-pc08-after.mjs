import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC08_AFTER_URL || 'http://127.0.0.1:5182';
const outputRoot = process.env.PC08_AFTER_DIR || '../artifacts/pc08-after';
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA4LWFmdGVyIiwiZXhwIjoyMDAwMDAwMDAwfQ.audit';
const evidence = [];

async function harness(context) {
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
          context: { access_id: '11111111-1111-4111-8111-111111111111', relationship_type: 'SELF', patient: { display_name: 'Aya Companion' } },
          paired_at: '2026-09-22T09:00:00Z',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.pathname.endsWith('/notifications')) return new Response(JSON.stringify({ items: [], preferences: { appointments: true, documents: true, questionnaires: true, consents: true } }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      if (url.pathname.endsWith('/agenda') || url.pathname.endsWith('/shares') || url.pathname.endsWith('/questionnaires') || url.pathname.endsWith('/consents')) return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      return new Response('{}', { status: 404, headers: { 'Content-Type': 'application/json' } });
    };
  }, { token });
}

for (const [browserName, browserType] of Object.entries({ chromium, webkit })) {
  const browser = await browserType.launch({ headless: true });
  try {
    for (const viewport of [{ width: 360, height: 800 }, { width: 390, height: 844 }]) {
      const context = await browser.newContext({ viewport, colorScheme: 'light' });
      const page = await context.newPage();
      const pageErrors = [];
      const consoleErrors = [];
      page.on('pageerror', error => pageErrors.push(String(error)));
      page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
      await harness(context);
      await page.goto(`${baseUrl}/companion`, { waitUntil: 'domcontentloaded' });
      await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
      await page.getByText('Appairer avec le code', { exact: true }).click();
      const section = page.locator('[data-pc08-secure-messaging]');
      await section.waitFor();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      if (overflow || pageErrors.length || consoleErrors.length) throw new Error(JSON.stringify({ overflow, pageErrors, consoleErrors }));
      const shot = `${browserName}-patient-after-${viewport.width}x${viewport.height}.png`;
      await fs.mkdir(outputRoot, { recursive: true });
      await section.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(outputRoot, shot), fullPage: true });
      evidence.push({ browserName, viewport, shot, overflow, pageErrors, consoleErrors });
      await context.close();
    }
  } finally { await browser.close(); }
}
await fs.writeFile(path.join(outputRoot, 'report.json'), JSON.stringify(evidence, null, 2));
