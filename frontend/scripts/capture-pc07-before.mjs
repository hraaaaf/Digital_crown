import { chromium, webkit } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.PC07_BEFORE_URL || 'http://127.0.0.1:5182';
const outputRoot = process.env.PC07_EVIDENCE_DIR || '../artifacts/pc07-emergency-photo-before';
const viewports = [{ width: 360, height: 800 }, { width: 390, height: 844 }];
const browsers = { chromium, webkit };
const evidence = [];
const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYzA3LWJhc2UiLCJleHAiOjIwMDAwMDAwMDB9.audit';

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
          context: {
            access_id: '11111111-1111-4111-8111-111111111111',
            relationship_type: 'SELF',
            patient: { display_name: 'Aya Urgence' },
          },
          paired_at: '2026-09-21T09:00:00Z',
        }), { status: 201, headers: { 'Content-Type': 'application/json' } });
      }

      if (
        url.pathname.endsWith('/agenda')
        || url.pathname.endsWith('/shares')
        || url.pathname.endsWith('/questionnaires')
        || url.pathname.endsWith('/consents')
      ) {
        return new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      if (url.pathname.endsWith('/notifications')) {
        return new Response(JSON.stringify({
          items: [],
          preferences: { appointments: true, documents: true, questionnaires: true, consents: true },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      return new Response('{}', { status: 404, headers: { 'Content-Type': 'application/json' } });
    };
  }, { token });
}

for (const [browserName, browserType] of Object.entries(browsers)) {
  const browser = await browserType.launch({ headless: true });
  try {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      await installHarness(context);
      await page.goto(`${baseUrl}/companion`, { waitUntil: 'domcontentloaded' });
      await page.getByText('Appairer ce téléphone', { exact: true }).waitFor();
      await page.getByLabel('Code manuel').fill('ABCD-EFGH-JKLM');
      await page.getByText('Appairer avec le code', { exact: true }).click();
      await page.locator('[data-pc00-cabinet-link]').waitFor();
      if (await page.locator('[data-pc07-emergency-photo]').count()) throw new Error('PC07 unexpectedly present in BEFORE');
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
