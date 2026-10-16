/** Crown Bot ZERO-LLM opt-in preview: genuine responsive interaction smoke.

Uses synthetic, isolated T2 workstation only. Captures the same viewport before
and after entering preview (interaction state, NOT a diff to a prior release).
No executable confirmation, booking or real patient data is ever submitted.
*/
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const appUrl = process.env.CROWN_BOT_VISUAL_APP_URL || 'http://127.0.0.1:5173';
const apiUrl = process.env.CROWN_BOT_VISUAL_API_URL || 'http://127.0.0.1:8005';
const user = process.env.T2_USER;
const pass = process.env.T2_PASSWORD;
if (!user || !pass) throw new Error('Synthetic T2 staff credentials required');

const output = path.resolve('../artifacts/crown-bot-zero-llm-preview');
fs.mkdirSync(output, { recursive: true });
const contextApi = await request.newContext({ baseURL: apiUrl });
const login = await contextApi.post('/api/auth/login', {
  form: { username: user, password: pass },
});
if (!login.ok()) throw new Error(`Synthetic login failed: ${login.status()}`);
const tokens = await login.json();
const browser = await chromium.launch({ headless: true });
const evidence = [];

try {
  for (const width of [390, 430, 1280]) {
    const viewport = { width, height: width < 500 ? 844 : 900 };
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    const errors = [];
    const writes = [];
    page.on('pageerror', error => errors.push(String(error)));
    page.on('request', req => {
      if (/\/api\/(bot\/execute|appointments\/?)/.test(req.url())
        && req.method() !== 'GET') writes.push(req.url());
    });
    await page.addInitScript(({ access, refresh }) => {
      localStorage.setItem('token', access);
      localStorage.setItem('refresh_token', refresh || '');
      localStorage.setItem('appMode', 'prod');
    }, { access: tokens.access_token, refresh: tokens.refresh_token });
    await page.goto(`${appUrl}/dashboard`, {
      waitUntil: 'domcontentloaded', timeout: 90000,
    });
    const opener = page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
    await opener.waitFor({ state: 'visible', timeout: 30000 });
    await opener.click();
    const overlay = page.locator('[data-ux1-c-crownbot-overlay]');
    await overlay.waitFor({ state: 'visible', timeout: 15000 });
    const before = `crownbot-before-${width}.png`;
    await page.screenshot({ path: path.join(output, before) });

    await page.getByRole('button', { name: 'Chat', exact: true }).click();
    const preview = page.getByRole('region', { name: 'Simulation ZERO-LLM Crown Bot' });
    await preview.waitFor({ state: 'visible' });
    await preview.getByRole('button', { name: '/patient' }).click();
    await preview.getByText('Patient : saisissez un identifiant, un nom/prénom exact ou un numéro de dossier', { exact: false }).waitFor({
      state: 'visible', timeout: 15000,
    });
    const after = `crownbot-after-${width}.png`;
    await page.screenshot({ path: path.join(output, after) });
    const geometry = await page.evaluate(() => {
      const preview = document.querySelector('[aria-label="Simulation ZERO-LLM Crown Bot"]');
      const rect = preview?.getBoundingClientRect();
      return {
        documentOverflow: document.documentElement.scrollWidth
          > document.documentElement.clientWidth + 2,
        previewOverflow: Boolean(preview && preview.scrollWidth > preview.clientWidth + 2),
        previewBounds: rect ? { x: rect.x, y: rect.y, width: rect.width, height: rect.height } : null,
      };
    });
    if (geometry.documentOverflow || geometry.previewOverflow
      || !geometry.previewBounds
      || geometry.previewBounds.x < -1
      || geometry.previewBounds.x + geometry.previewBounds.width > width + 1) {
      throw new Error(`Responsive overflow at ${width}: ${JSON.stringify(geometry)}`);
    }
    if (writes.length) throw new Error(`A read-only preview made clinical writes: ${writes.join(',')}`);
    if (errors.length) throw new Error(`Browser errors at ${width}: ${errors.join(';')}`);
    evidence.push({ width, before, after, geometry, writes, errors });
    await context.close();
  }
  fs.writeFileSync(path.join(output, 'summary.json'), JSON.stringify({
    result: 'PASS', kind: 'same-viewport before/after interaction (not historical release diff)',
    head: process.env.GITHUB_SHA || null, evidence,
  }, null, 2));
  console.log('CROWN_BOT_ZERO_LLM_PREVIEW_VISUAL: PASS', JSON.stringify(evidence));
} finally {
  await browser.close();
  await contextApi.dispose();
}
