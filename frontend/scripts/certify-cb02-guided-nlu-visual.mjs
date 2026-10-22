/** CB-02 B: real browser screenshots of the NEW guided panel, isolated synthetic T2.
 * Same-view BEFORE/AFTER, real FastAPI response, no native NVDA certification.
 * Neither CI flags nor a screenshot are permission to activate a clinic.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.CROWN_BOT_GUIDED_NLU_ENABLED !== 'true'
    || process.env.VITE_CROWN_BOT_GUIDED_NLU_ENABLED !== 'true') {
  throw Error('REFUSED: isolated and explicitly ephemeral CB-02 experiment required');
}
const appOrigin = process.env.CB02_VISUAL_APP_URL || 'http://127.0.0.1:5173';
const apiOrigin = process.env.CB02_VISUAL_API_URL || 'http://127.0.0.1:8005';
for (const candidate of [appOrigin, apiOrigin]) {
  const u = new URL(candidate);
  if (u.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(u.hostname)
      || u.username || u.password || u.search || u.hash || !['', '/'].includes(u.pathname)) {
    throw Error('REFUSED: only ephemeral localhost runner services allowed');
  }
}
const user = process.env.T2_USER, pass = process.env.T2_PASSWORD;
const head = process.env.CB02_SOURCE_HEAD;
if (!user?.startsWith('t2-') || !pass || !/^[a-f0-9]{40}$/.test(head)) {
  throw Error('REFUSED: synthetic identity and SHA required');
}
const out = path.resolve('../artifacts/cb02-guided-nlu-visual');
fs.mkdirSync(out, { recursive: true });
const http = await request.newContext({ baseURL: apiOrigin });
const auth = await http.post('/api/auth/login', {
  form: { username: user, password: pass },
});
if (!auth.ok()) throw Error('REFUSED: synthetic login failed ' + auth.status());
const token = await auth.json();
const browser = await chromium.launch({ headless: true });
const report = [];
try {
  for (const width of [390, 430, 1280, 1600]) {
    const viewport = { width, height: width < 500 ? 844 : 900 };
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    const errors = [], writes = [];
    page.on('pageerror', err => errors.push(String(err)));
    page.on('request', req => {
      const u = new URL(req.url());
      if (u.origin === apiOrigin && req.method() !== 'GET'
          && (/^\/api\/bot\/execute\b/.test(u.pathname)
              || /^\/api\/appointments\b/.test(u.pathname)
              || /^\/api\/patients\b/.test(u.pathname))) {
        writes.push(req.method() + ' ' + u.pathname);
      }
    });
    await page.addInitScript(({ access, refresh }) => {
      localStorage.setItem('token', access);
      localStorage.setItem('refresh_token', refresh || '');
      localStorage.setItem('appMode', 'prod');
    }, { access: token.access_token, refresh: token.refresh_token });
    await page.goto(appOrigin + '/dashboard', { waitUntil: 'domcontentloaded', timeout: 90000 });
    const opener = page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
    await opener.waitFor({ state: 'visible', timeout: 30000 });
    await opener.click();
    const guided = page.getByRole('region', { name: 'Français guidé Crown Bot CB-02' });
    await guided.waitFor({ state: 'visible', timeout: 20000 });
    await guided.scrollIntoViewIfNeeded();
    const before = 'cb02-before-' + width + '.png';
    await page.screenshot({ path: path.join(out, before) });

    const input = guided.getByRole('textbox', { name: 'Votre demande en français' });
    await input.fill('Mon agenda demain');
    const response = page.waitForResponse(r => new URL(r.url()).pathname === '/api/bot/guided/preview'
      && r.request().method() === 'POST', { timeout: 30000 });
    await guided.getByRole('button', { name: 'Comprendre la demande' }).click();
    const httpResponse = await response;
    if (httpResponse.status() !== 200) throw Error('CB02 server status ' + httpResponse.status());
    const result = await httpResponse.json();
    if (result.status !== 'requires_server_authorization' || result.intent !== 'AGENDA_READ'
        || result.proposal !== null || result.executable !== false
        || !/^\d{4}-\d{2}-\d{2}$/.test(result.fields?.date?.value || '')) {
      throw Error('CB02 real server contract NOT met: ' + JSON.stringify(result));
    }
    await guided.getByText('Syntaxe comprise ; contrôles serveur obligatoires.').waitFor({
      state: 'visible', timeout: 10000,
    });
    await guided.scrollIntoViewIfNeeded();
    const after = 'cb02-after-' + width + '.png';
    await page.screenshot({ path: path.join(out, after) });

    const bounds = await page.evaluate(() => {
      const root = document.querySelector('[aria-label="Français guidé Crown Bot CB-02"]');
      const frame = root?.getBoundingClientRect();
      return {
        rootVisible: Boolean(root && frame && frame.width > 0 && frame.height > 0),
        rootBounds: frame ? { x: frame.x, y: frame.y, width: frame.width, height: frame.height } : null,
        documentOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
        panelOverflow: Boolean(root && root.scrollWidth > root.clientWidth + 2),
      };
    });
    if (!bounds.rootVisible || bounds.documentOverflow || bounds.panelOverflow
        || !bounds.rootBounds || bounds.rootBounds.width > width + 2) {
      throw Error('CB02 responsive bounds FAIL at ' + width + ': ' + JSON.stringify(bounds));
    }
    if (writes.length || errors.length) throw Error('CB02 writes/browser errors at ' + width
      + ': ' + JSON.stringify({ writes, errors }));
    report.push({ width, before, after, result: 'PASS', bounds,
      syntheticApiContract: 'AGENDA_READ requires_server_authorization', clinicalWrites: 0 });
    await context.close();
  }
  fs.writeFileSync(path.join(out, 'summary.json'), JSON.stringify({
    sourceHead: head,
    result: 'PASS',
    scope: 'NEW CB-02 guided UI 390/430/1280/1600 Chromium headless + localhost FastAPI',
    limits: 'NOT Windows native zoom 200%; NOT NVDA; NOT human clinic usability',
    report,
  }, null, 2));
  console.log('CB02_GUIDED_VISUAL_NEW_UI: PASS', JSON.stringify(report));
} finally {
  await browser.close();
  await http.dispose();
}
