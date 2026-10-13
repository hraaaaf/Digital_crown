/** Synthetic-only production-component proof. Never contacts a cabinet API. */
import { createRequire } from 'node:module';
import { createCipheriv, randomBytes } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.POCKET_PROOF_URL || 'http://127.0.0.1:5197';
if (!['127.0.0.1', 'localhost'].includes(new URL(base).hostname)) throw Error('Only isolated loopback runtime allowed');
const out = process.env.POCKET_PROOF_DIR || '../artifacts/pocket-read-capabilities';
const after = process.env.POCKET_PROOF_PHASE === 'after';
const engine = process.env.POCKET_PROOF_ENGINE === 'webkit' ? webkit : chromium;
const scenarios = [
  { name: 'dentiste', role: 'DENTISTE', patients: true, finance: true },
  { name: 'dentiste-restreint', role: 'DENTISTE', patients: false, finance: false },
  { name: 'assistante', role: 'SECRETAIRE', patients: true, finance: false },
  { name: 'assistante-finance', role: 'SECRETAIRE', patients: true, finance: true },
].filter(item => !process.env.POCKET_PROOF_SCENARIO || item.name === process.env.POCKET_PROOF_SCENARIO);
const sizes = [{ width: 390, height: 844 }, { width: 430, height: 932 }, { width: 768, height: 1024 }, { width: 1280, height: 900 }]
  .filter(item => !process.env.POCKET_PROOF_WIDTH || item.width === Number(process.env.POCKET_PROOF_WIDTH));
if (!scenarios.length || !sizes.length) throw Error('Invalid proof scenario or viewport');
const key = 'a'.repeat(64);
function encrypt(value) {
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', Buffer.from(key, 'hex'), iv);
  const data = Buffer.concat([cipher.update(JSON.stringify(value)), cipher.final()]);
  return { payload: Buffer.concat([iv, data, cipher.getAuthTag()]).toString('base64') };
}
function policy(scenario) {
  const grants = { 'agenda.read': true, 'cabinet.patients.read': scenario.patients,
    'cabinet.clinical.read': scenario.patients && scenario.role === 'DENTISTE', 'cabinet.finance.read': scenario.finance, 'shares.read': false };
  return { version: 1, principal_kind: 'staff', capabilities: Object.fromEntries(
    Object.entries(grants).map(([action, allowed]) => [action, { allowed, scope: allowed ? 'cabinet' : null, reason: allowed ? null : 'not_authorized' }]),
  ) };
}
function snapshot(scenario, url) {
  const date = new URL(url).searchParams.get('target_date') || '2026-10-12';
  return { generated_at: '2026-10-12T08:00:00Z', role: scenario.role, appointments: [
    { id: 101, patient_id: 11, time: '09:00', date, patient_name: 'Patient fictif A', phone: null, motif: 'Contrôle', status: 'TERMINE', duration_minutes: 30 },
    { id: 102, patient_id: 12, time: '10:15', date, patient_name: 'Patient fictif B', phone: null, motif: 'Consultation', status: 'EN_ATTENTE', duration_minutes: 45 },
    { id: 103, patient_id: 13, time: '11:30', date, patient_name: 'Patient fictif C', phone: null, motif: 'Suivi', status: 'PLANIFIE', duration_minutes: 30 },
  ], finance: { today_revenue: 0, month_revenue: 0, month_variation: null, appointments_count: 3,
    weekly_revenue: [], total_patients: 3, total_debt: 0 }, debtors: [] };
}
await fs.mkdir(out, { recursive: true });
const browser = await engine.launch({ headless: true });
const evidence = [];
try {
  for (const scenario of scenarios) for (const viewport of sizes) {
    const context = await browser.newContext({ viewport, serviceWorkers: 'block', reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = [], unknown = [];
    let capabilityHits = 0;
    let currentPolicy = policy(scenario);
    let policyUnavailable = false;
    page.on('pageerror', error => errors.push(error.message));
    const json = (route, value, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(value) });
    // All API traffic is intercepted, including historical non-loopback bases.
    await page.route('**/api/**', route => {
      const request = route.request();
      const url = new URL(request.url());
      if (request.method() !== 'GET') { unknown.push(request.method() + ' ' + url.pathname); return json(route, {}, 501); }
      if (url.pathname === '/api/mobile/capabilities') { capabilityHits++; return json(route, policyUnavailable ? {} : encrypt(currentPolicy), policyUnavailable ? 503 : 200); }
      if (url.pathname === '/api/mobile/snapshot') return json(route, snapshot(scenario, request.url()));
      if (url.pathname === '/api/mobile/patients') return json(route, { data: [] });
      if (url.pathname === '/api/mobile/lab-jobs') return json(route, []);
      if (url.pathname === '/api/mobile/quick-actions/capabilities') return json(route, { can_create_appointment: true, can_create_patient: scenario.patients, can_open_clinical_context: scenario.patients && scenario.role === 'DENTISTE', can_pay: false });
      if (url.pathname === '/api/mobile/passkey/status') return json(route, { state: 'disabled', expected_origin: 'https://digitalcrown.local:8005', server_gate: false });
      if (url.pathname === '/api/clinics/mobile-theme') return json(route, { selected_theme: 'elite', primary_color: '#003380', secondary_color: '#1e40af', accent_color: '#60a5fa', font_fr: 'inter' });
      if (url.pathname === '/api/mobile/notifications') return json(route, { items: [] });
      if (url.pathname === '/api/auth/me') return json(route, {}, 401);
      unknown.push(url.pathname); return json(route, {}, 501);
    });
    await page.route('**/__pocket_session_seed', route => route.fulfill({ contentType: 'text/html', body: '<!doctype html><title>Synthetic fixture</title>' }));
    await page.goto(base + '/__pocket_session_seed');
    const jwt = Buffer.from('{}').toString('base64url') + '.' + Buffer.from(JSON.stringify({ exp: 4102444800 })).toString('base64url') + '.fixture';
    await page.evaluate(async creds => {
      await new Promise((resolve, reject) => {
        const request = indexedDB.open('digital-crown-zka', 1);
        request.onupgradeneeded = () => request.result.createObjectStore('secure_keys');
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const db = request.result, tx = db.transaction('secure_keys', 'readwrite');
          tx.objectStore('secure_keys').put(creds, 'zka_credentials');
          tx.oncomplete = () => { db.close(); resolve(); }; tx.onerror = () => reject(tx.error);
        };
      });
    }, { publicId: '0123456789abcdef', masterKey: key, access_token: jwt, refresh_token: 'synthetic-only', device_id: 'synthetic-device', api_base_url: base });
    const capture = async label => {
      await page.evaluate(() => document.fonts.ready);
      await page.waitForFunction(() => {
        const pane = document.querySelector('main > div');
        return !pane || (getComputedStyle(pane).opacity === '1' && getComputedStyle(pane).transform === 'none');
      });
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      await page.screenshot({ path: path.join(out, `${scenario.name}-${label}-${viewport.width}x${viewport.height}.png`) });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (overflow) throw Error(`${scenario.name}/${viewport.width}: horizontal overflow`);
    };
    try {
      await page.goto(base + '/mobile/dashboard');
      await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible' });
      if (after) await page.locator('[data-pocket-read-status="ready"]').waitFor();
      const patientsDisabled = await page.locator('[data-mobile-nav-item="patients"]').isDisabled();
      await capture('today');
      await page.locator('[data-mobile-nav-item="more"]').click();
      await page.locator('[data-mobile-more-menu]').waitFor();
      const financeVisible = await page.locator('[data-mobile-more-item="finance"]').count() > 0;
      await capture('plus');
      await page.getByRole('button', { name: 'Fermer Plus' }).click();
      await page.goto(base + '/mobile/dashboard?tab=finance');
      if (after) await page.locator('[data-pocket-read-status="ready"]').waitFor();
      await page.getByText(scenario.finance && after || !after && scenario.role === 'DENTISTE' ? 'Aperçu financier · lecture seule' : 'Accès réservé', { exact: true }).waitFor();
      await capture('finance');
      if (after && (patientsDisabled !== !scenario.patients || financeVisible !== scenario.finance || capabilityHits < 1)) throw Error('Permissions mismatch');
      if (after) {
        // Revoke while an already-open finance screen contains a granted snapshot.
        currentPolicy = policy({ ...scenario, patients: false, finance: false });
        await page.evaluate(() => window.dispatchEvent(new Event('focus')));
        await page.locator('[data-pocket-read-status="ready"]').waitFor();
        await page.getByText('Accès réservé', { exact: true }).waitFor();
        if (!(await page.locator('[data-mobile-nav-item="patients"]').isDisabled())) throw Error('Revoked dossiers still enabled');
        if (await page.getByText('Aperçu financier · lecture seule', { exact: true }).count()) throw Error('Revoked finance remains mounted');
        await capture('revoked');
        await page.goto(base + '/mobile/dashboard?tab=patients');
        await page.locator('[data-pocket-read-status="ready"]').waitFor();
        await page.getByText('Accès réservé', { exact: true }).waitFor();
        if (await page.getByRole('button', { name: 'Ouvrir la recherche patients' }).count()) throw Error('Denied patient search remains');
        policyUnavailable = true;
        await page.evaluate(() => window.dispatchEvent(new Event('focus')));
        await page.locator('[data-pocket-read-status="unavailable"]').waitFor();
        await page.getByText('Accès à vérifier', { exact: true }).waitFor();
        await capture('unavailable');
        policyUnavailable = false;
        await page.getByRole('button', { name: 'Réessayer' }).click();
        await page.locator('[data-pocket-read-status="ready"]').waitFor();
        await page.getByText('Accès réservé', { exact: true }).waitFor();
      }
      if (errors.length || unknown.length) throw Error(JSON.stringify({ errors, unknown }));
      evidence.push({ scenario: scenario.name, viewport, patientsDisabled, financeVisible, capabilityHits, revocationAndRetry: after, result: 'PASS' });
    } catch (error) {
      await page.screenshot({ path: path.join(out, `${scenario.name}-failure-${viewport.width}.png`) }).catch(() => undefined);
      evidence.push({ scenario: scenario.name, viewport, result: 'FAIL', error: error.message, errors, unknown });
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
await fs.writeFile(path.join(out, 'evidence.json'), JSON.stringify({ phase: after ? 'after' : 'before', engine: engine.name(), fixture: 'synthetic API, actual MobileDashboard', evidence }, null, 2));
console.log(JSON.stringify(evidence.map(({ scenario, viewport, result, error }) => ({ scenario, width: viewport.width, result, error })), null, 2));
if (evidence.some(item => item.result !== 'PASS')) process.exitCode = 1;
