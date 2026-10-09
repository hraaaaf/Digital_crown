import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

// Real Chromium geometry certification: DOM-visible is not necessarily
// viewport-visible, especially for absolutely positioned mobile search.
const root = path.resolve('../artifacts/v15-02-4-photo-lifecycle');
fs.mkdirSync(root, { recursive: true });
const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');
const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('Search audit authentication failed: ' + login.status());
const tokens = await login.json();
const res = await api.get('/api/patients/', { headers: { Authorization: 'Bearer ' + tokens.access_token } });
if (!res.ok()) throw new Error('Patient fixture fetch failed: ' + res.status());
const patients = await res.json();
const patient = patients.find(row => row.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('A disposable patient fixture is required');

const browser = await chromium.launch({ headless: true });
const evidence = [];
try {
  for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
    const context = await browser.newContext({ viewport });
    try {
      const page = await context.newPage();
      const pageErrors = [];
      page.on('pageerror', err => pageErrors.push(String(err)));
      await page.addInitScript(({ token, refresh }) => {
        localStorage.setItem('token', token);
        localStorage.setItem('refresh_token', refresh || '');
      }, { token: tokens.access_token, refresh: tokens.refresh_token });
      await page.goto('http://127.0.0.1:5173/dashboard', { waitUntil: 'networkidle', timeout: 90000 });
      await page.getByRole('button', { name: 'Chercher un patient' }).click();
      const input = page.getByRole('textbox', { name: 'Chercher un patient' });
      await input.fill(String(patient.nom));
      const results = page.locator('#dashboard-patient-search-results');
      await results.waitFor({ state: 'visible', timeout: 30000 });
      const avatar = results.locator('[data-patient-avatar][data-patient-id="' + patient.id + '"]').first();
      await avatar.waitFor({ state: 'visible', timeout: 30000 });

      const geometry = await page.evaluate(patientId => {
        const input = document.querySelector('input[aria-label="Chercher un patient"]');
        const results = document.querySelector('#dashboard-patient-search-results');
        const avatar = results?.querySelector('[data-patient-avatar][data-patient-id="' + patientId + '"]');
        if (!input || !results || !avatar) return { pass: false, error: 'missing search surface' };
        const rect = element => {
          const r = element.getBoundingClientRect();
          return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height };
        };
        const boxes = { input: rect(input), results: rect(results), avatar: rect(avatar) };
        const visible = r => r.width >= 20 && r.height >= 20 && r.left >= -1 && r.top >= -1
          && r.right <= window.innerWidth + 1 && r.bottom <= window.innerHeight + 1;
        const a = boxes.avatar;
        const hit = document.elementFromPoint(a.left + a.width / 2, a.top + a.height / 2);
        const unoccluded = hit === avatar || avatar.contains(hit);
        return {
          pass: Object.values(boxes).every(visible) && unoccluded,
          viewport: { width: innerWidth, height: innerHeight },
          boxes, unoccluded,
          horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 2,
        };
      }, String(patient.id));

      if (!geometry.pass || geometry.horizontalOverflow || pageErrors.length) {
        throw new Error('Dashboard search must fit the viewport: ' + JSON.stringify({ geometry, pageErrors }));
      }
      await page.screenshot({
        path: path.join(root, 'dashboard-search-' + viewport.width + 'x' + viewport.height + '.png'),
        fullPage: false,
      });
      evidence.push({ viewport, geometry, pageErrors });
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
  await api.dispose();
}
fs.writeFileSync(path.join(root, 'dashboard-search-proof.json'), JSON.stringify({
  head: process.env.EVALUATED_SHA || process.env.GITHUB_SHA || null,
  patientId: patient.id, success: true, evidence,
}, null, 2));
console.log('DASHBOARD_SEARCH_VIEWPORT_PASS', JSON.stringify({ head: process.env.EVALUATED_SHA, checks: evidence.length }));
