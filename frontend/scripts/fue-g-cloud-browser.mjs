// FUE-G CLOUD-LAB ONLY: real Chromium UI proof layered on the green S+A+B+C(+D) API lab.
// Every browser context inherits only its own dc_workstation cookie from the Docker
// client's pairing. Never load owner auth cookies or log credentials/tokens.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium, request } from 'playwright';

const root = process.env.FUE_STATE_ROOT;
const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
if (!root || !head || !password || process.env.T2_CLOUD_LAB !== '1') {
  throw new Error('Isolated cloud-only browser preconditions missing');
}
const base = 'https://cabinet.local:5173';
const apiBase = 'https://cabinet.local:8005';
const evidence = path.resolve('../artifacts/fue-g-cloud/browser');
fs.mkdirSync(evidence, { recursive: true });
const users = {
  A: 't2-browser@cabinet.ma',
  B: 't2-browser@cabinet.ma',
  C: 't2-restricted@cabinet.ma',
  D: 't2-reception@cabinet.ma',
};
const roles = { A: 'Dentiste', B: 'Dentiste', C: 'Assistante', D: 'Accueil' };
const viewport = { width: 1280, height: 900 };
const api = await request.newContext({ baseURL: apiBase, ignoreHTTPSErrors: false });
const browser = await chromium.launch({ headless: true });
const results = [];

function workstationCookie(role) {
  const raw = fs.readFileSync(path.join(root, 'fue-g-cloud-state-' + role.toLowerCase(), 'cookies.txt'), 'utf8');
  const rows = raw.split(/\r?\n/).filter(row => row && !row.startsWith('# ') && !row.startsWith('# Netscape'));
  const station = rows.map(row => {
    const httpOnly = row.startsWith('#HttpOnly_');
    const cells = (httpOnly ? row.slice('#HttpOnly_'.length) : row).split('\t');
    if (cells.length < 7 || cells[5] !== 'dc_workstation') return null;
    return {
      name: 'dc_workstation', value: cells.slice(6).join('\t'),
      domain: 'cabinet.local', path: '/', secure: cells[3] === 'TRUE',
      httpOnly, sameSite: 'Lax',
    };
  }).filter(Boolean);
  if (station.length !== 1) throw new Error(role + ' must have exactly one station cookie');
  return station[0];
}
const sha16 = value => crypto.createHash('sha256').update(String(value)).digest('hex').slice(0, 16);
try {
  for (const role of Object.keys(users)) {
    const pair = JSON.parse(fs.readFileSync(path.join(root, 'fue-g-cloud-state-' + role.toLowerCase(), 'reports/pair.json'), 'utf8'));
    const recovered = JSON.parse(fs.readFileSync(path.join(root, 'fue-g-cloud-state-' + role.toLowerCase(), 'reports/recover.json'), 'utf8'));
    if (pair.status !== 'PASS' || recovered.status !== 'PASS' || pair.productHead !== head || pair.workstationHash !== recovered.workstationHash) {
      throw new Error(role + ' API pairing/recovery evidence mismatch');
    }
    const login = await api.post('/api/auth/login', { form: { username: users[role], password } });
    if (!login.ok()) throw new Error(role + ' browser persona authentication failed HTTP ' + login.status());
    const tokens = await login.json();
    if (!tokens.access_token) throw new Error(role + ' access token missing');
    const ctx = await browser.newContext({ viewport, colorScheme: 'light', ignoreHTTPSErrors: false });
    try {
      await ctx.addCookies([workstationCookie(role)]);
      const page = await ctx.newPage();
      await page.addInitScript(token => {
        localStorage.setItem('token', token);
        localStorage.setItem('appMode', 'prod');
      }, tokens.access_token);
      // Compare workstation identity in the real browser to the independent
      // Docker client's cookie-based, exact-HEAD pairing proof.
      await page.goto(base + '/dashboard', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.getByRole('button', { name: 'Ajout rapide' }).waitFor({ state: 'visible', timeout: 45000 });
      const identity = await page.evaluate(async url => {
        const token = localStorage.getItem('token');
        const response = await fetch(url + '/api/workstation/bootstrap', {
          credentials: 'include', headers: { Authorization: 'Bearer ' + token },
        });
        if (!response.ok) throw new Error('Browser workstation bootstrap HTTP ' + response.status);
        const data = await response.json();
        return { workstationId: data.workstationId };
      }, apiBase);
      if (!identity.workstationId || sha16(identity.workstationId) !== pair.workstationHash) {
        throw new Error(role + ' browser workstation not the paired Docker identity');
      }
      await page.screenshot({ path: path.join(evidence, role + '-before-dashboard.png'), fullPage: false });
      let restrictedRouteDenied = false;
      if (role === 'C' || role === 'D') {
        await page.goto(base + '/patients', { waitUntil: 'domcontentloaded', timeout: 90000 });
        await page.waitForURL('**/dashboard', { timeout: 20000 });
        restrictedRouteDenied = true;
        if (await page.getByRole('link', { name: 'Patients', exact: true }).count()) {
          throw new Error(role + ' restricted user sees patient navigation');
        }
      }
      await page.goto(base + '/agenda', { waitUntil: 'domcontentloaded', timeout: 90000 });
      await page.waitForURL('**/agenda', { timeout: 20000 });
      await page.getByRole('heading', { name: 'Agenda', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
      await page.locator('[data-testid="agenda-active-view"]').waitFor({ state: 'visible', timeout: 30000 });
      await page.screenshot({ path: path.join(evidence, role + '-after-agenda.png'), fullPage: false });
      results.push({
        role, persona: roles[role], status: 'PASS', workstationHash: pair.workstationHash,
        tlsBrowserVerified: true, viewport: '1280x900', before: role + '-before-dashboard.png',
        after: role + '-after-agenda.png', restrictedRouteDenied,
      });
      console.log(JSON.stringify({ role, persona: roles[role], phase: 'browser', status: 'PASS', head }));
    } finally {
      await ctx.close();
    }
  }
  if (results.length !== 4 || new Set(results.map(x => x.workstationHash)).size !== 4) {
    throw new Error('Four unique browser identities required');
  }
  fs.writeFileSync(path.join(evidence, 'report.json'), JSON.stringify({
    head, success: true, scope: 'EXPERIMENTAL Chromium same-origin TLS UI using four Docker-paired identities; NOT Windows installation or physical LAN',
    checks: results,
  }, null, 2));
  console.log('FUE_G_CLOUD_BROWSER_SUMMARY ' + JSON.stringify({ head, success: true, browsers: results.length, screenshots: 8, restrictedPosts: 2 }));
} finally {
  await browser.close();
  await api.dispose();
}
