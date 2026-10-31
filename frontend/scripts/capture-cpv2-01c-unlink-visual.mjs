import { createRequire } from 'node:module';
import { createCipheriv, randomBytes } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const engine = process.env.MOBILE_RUNTIME_ENGINE === 'webkit' ? webkit : chromium;

const baseUrl = process.env.MOBILE_RUNTIME_URL || 'http://127.0.0.1:5173';
const outputDir = process.env.MOBILE_RUNTIME_DIR || '../artifacts/mobile-pocket-runtime';
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 800 },
];
const roles = [
  { value: 'DENTISTE', slug: 'dentiste', marker: 'practitioner', label: 'Vue praticien · priorité clinique' },
  { value: 'SECRETAIRE', slug: 'secretaire', marker: 'assistant', label: 'Vue assistante · flux cabinet' },
];
const themes = [
  { id: 'emerald', muted: '#065f46', primary: '#059669', secondary: '#065f46', accent: '#10b981', foreground: 'rgb(2, 6, 23)' },
  { id: 'rose', muted: '#9d174d', primary: '#db2777', secondary: '#9d174d', accent: '#f472b6', foreground: 'rgb(255, 255, 255)' },
  { id: 'prestige', muted: '#94a3b8', primary: '#3b82f6', secondary: '#2563eb', accent: '#60a5fa', foreground: 'rgb(2, 6, 23)' },
  { id: 'ocean', muted: '#0369a1', primary: '#0284c7', secondary: '#0369a1', accent: '#38bdf8', foreground: 'rgb(2, 6, 23)' },
  { id: 'graphite', muted: '#475569', primary: '#475569', secondary: '#334155', accent: '#94a3b8', foreground: 'rgb(255, 255, 255)' },
  { id: 'dark', muted: '#94a3b8', primary: '#4f46e5', secondary: '#3730a3', accent: '#6366f1', foreground: 'rgb(255, 255, 255)' },
  { id: 'high-contrast', muted: '#111111', primary: '#000000', secondary: '#000000', accent: '#000000', foreground: 'rgb(255, 255, 255)' },
];
// CSS custom properties preserve authored tokens, and production CSS minifiers
// may shorten #111111 to #111. Compare actual RGB hex semantics, not spelling.
function canonicalHexColor(value) {
  const hex = String(value ?? '').trim().toLowerCase();
  if (/^#[0-9a-f]{3}$/.test(hex)) {
    return '#' + [...hex.slice(1)].map(channel => channel + channel).join('');
  }
  if (/^#[0-9a-f]{6}$/.test(hex)) return hex;
  return null; // No silent acceptance for invalid colors or unknown formats.
}
if (canonicalHexColor('#111') !== canonicalHexColor('#111111')
  || canonicalHexColor('#112') === canonicalHexColor('#111111')
  || canonicalHexColor('') !== null) {
  throw new Error('Pocket color normalization guard failed');
}

// Independent runtime WCAG oracle; do not reuse the app's ink algorithm.
function rgbForRatio(value) {
  const input = String(value ?? '').trim().toLowerCase();
  const hex = canonicalHexColor(input === 'white' ? '#ffffff' : input === 'black' ? '#000000' : input);
  if (hex) return [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
  const match = input.match(/^rgba?\(([^)]+)\)$/);
  if (!match) return null;
  const parts = match[1].split(/[,\s/]+/).filter(Boolean).map(Number);
  if (parts.length !== 3 && parts.length !== 4) return null;
  if (!parts.every(Number.isFinite) || parts.slice(0, 3).some(c => c < 0 || c > 255)
    || (parts.length === 4 && parts[3] < 0.999)) return null;
  return parts.slice(0, 3);
}
function contrastRatio(a, b) {
  const lhs = rgbForRatio(a), rhs = rgbForRatio(b);
  if (!lhs || !rhs) return null;
  const luminance = rgb => rgb.map(c => {
    const v = c / 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  }).reduce((s, c, i) => s + c * [0.2126, 0.7152, 0.0722][i], 0);
  const x = luminance(lhs), y = luminance(rhs);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

const expectedDentistLabels = ['Notifications', 'Stock', 'Bibliothèque', 'Approvisionnement', 'Trésorerie', 'Envois Labo', 'Équipe'];
const expectedSecretaryLabels = ['Notifications', 'Stock', 'Équipe'];
const credentials = {
  publicId: '0123456789abcdef',
  masterKey: 'a'.repeat(64),
  access_token: fakeJwt(),
  refresh_token: 'runtime-proof-refresh',
  device_id: 'runtime-proof-device',
  api_base_url: 'http://127.0.0.1:8005',
};

function fakeJwt() {
  const header = Buffer.from(JSON.stringify({ alg: 'none', typ: 'JWT' })).toString('base64url');
  const payload = Buffer.from(JSON.stringify({ exp: 4102444800 })).toString('base64url');
  return `${header}.${payload}.proof`;
}

function snapshotFor(role, requestUrl) {
  const targetDate = new URL(requestUrl).searchParams.get('target_date') || new Date().toISOString().slice(0, 10);
  return {
    generated_at: new Date().toISOString(),
    role,
    is_superadmin: false,
    appointments: [
      { id: 101, patient_id: 11, time: '09:00', date: targetDate, patient_name: 'Nadia El Mansouri', phone: '+212600000011', motif: 'Contrôle', status: 'TERMINE', duration_minutes: 30 },
      { id: 102, patient_id: 12, time: '10:15', date: targetDate, patient_name: 'Youssef Amrani', phone: '+212600000012', motif: 'Endodontie 16', status: 'EN_ATTENTE', duration_minutes: 45 },
      { id: 103, patient_id: 13, time: '11:30', date: targetDate, patient_name: 'Salma Idrissi', phone: null, motif: 'Consultation', status: 'PLANIFIE', duration_minutes: 30 },
    ],
    finance: {
      today_revenue: 0, month_revenue: 0, month_variation: null,
      appointments_count: 3, weekly_revenue: [], total_patients: 3, total_debt: 0,
    },
    debtors: [],
  };
}

const json = (route, payload, status = 200) => route.fulfill({
  status,
  contentType: 'application/json',
  body: JSON.stringify(payload),
});

// Explicit synthetic read policy for the two historical default-profile cases.
// Keep the product's mandatory encrypted contract; never bypass its read guard.
function encryptedReadFixture(role) {
  const grants = {
    'agenda.read': true,
    'cabinet.patients.read': true,
    'cabinet.clinical.read': role === 'DENTISTE',
    'cabinet.finance.read': role === 'DENTISTE',
    'shares.read': false,
  };
  const contract = { version: 1, principal_kind: 'staff', capabilities: Object.fromEntries(
    Object.entries(grants).map(([action, allowed]) => [action, { allowed, scope: allowed ? 'cabinet' : null, reason: allowed ? null : 'not_authorized' }]),
  ) };
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', Buffer.from(credentials.masterKey, 'hex'), iv);
  const data = Buffer.concat([cipher.update(JSON.stringify(contract)), cipher.final()]);
  return { payload: Buffer.concat([iv, data, cipher.getAuthTag()]).toString('base64') };
}

async function installRoutes(page, role, selectedTheme = { id: 'elite', primary: '#003380', secondary: '#1e40af', accent: '#60a5fa' }) {
  const routeEvidence = { passkeyStatusHits: 0, readCapabilityHits: 0 };
  await page.route('**/api/mobile/capabilities', route => {
    routeEvidence.readCapabilityHits += 1;
    return json(route, encryptedReadFixture(role));
  });
  await page.route('**/api/mobile/passkey/status', route => {
    routeEvidence.passkeyStatusHits += 1;
    return json(route, {
    state: 'disabled', credential_id: null, rp_id: 'digitalcrown.local',
    expected_origin: 'https://digitalcrown.local:8005', origin_ready: true,
    user_verification: 'required', server_gate: false,
    });
  });
  await page.route('**/api/mobile/snapshot**', route => json(route, snapshotFor(role, route.request().url())));
  await page.route('**/api/mobile/patients', route => json(route, {
    data: [
      { id: 11, name: 'Nadia El Mansouri', phone: '+212600000011' },
      { id: 12, name: 'Youssef Amrani', phone: '+212600000012' },
      { id: 13, name: 'Salma Idrissi', phone: null },
    ],
  }));
  await page.route('**/api/mobile/quick-actions/capabilities', route => json(route, {
    can_create_appointment: true,
    can_create_patient: role === 'SECRETAIRE',
    can_open_clinical_context: role === 'DENTISTE',
    can_pay: false,
  }));
  await page.route('**/api/clinics/mobile-theme', route => json(route, {
    selected_theme: selectedTheme.id, primary_color: selectedTheme.primary, secondary_color: selectedTheme.secondary,
    accent_color: selectedTheme.accent, app_accent_color: null, font_fr: 'inter',
  }));
  await page.route('**/api/mobile/lab-jobs**', route => json(route, []));
  await page.route('**/api/mobile/dentists', route => json(route, { dentists: [] }));
  await page.route('**/api/mobile/stock/items**', route => json(route, [
    { id: 1, nom: 'Gants nitrile', categorie: 'CONSOMMABLE', quantite: 8, seuil_alerte: 10, unite: 'boîte', fournisseur: 'Demo', alerte: true },
    { id: 2, nom: 'Composite', categorie: 'MATERIAU', quantite: 20, seuil_alerte: 5, unite: 'seringue', fournisseur: null, alerte: false },
  ]));
  await page.route('**/api/mobile/partner-orders/meta', route => json(route, {
    strategyPresets: [{ key: 'draft', label: 'Brouillon', settlementBasis: 'SENT_TO_PARTNER', revenueModel: 'COMMISSION', commissionRate: 0, discountRate: 0, fixedFeeAmount: 0 }],
  }));
  await page.route('**/api/mobile/partner-catalog/meta', route => json(route, { categories: [], specialties: [], availability: [] }));
  await page.route('**/api/mobile/partner-catalog/suppliers', route => json(route, []));
  await page.route('**/api/mobile/partner-catalog/products', route => json(route, []));
  await page.route('**/stock/alerts', route => json(route, []));
  await page.route('**/api/mobile/frontdesk/pending', route => json(route, [
    {
      id: 701, patient_name: 'Patient Web', phone: '+212600000099',
      datetime_start: new Date(Date.now() + 3600000).toISOString(),
      duration_minutes: 30, motif: 'Demande web', status: 'EN_ATTENTE_DEMANDE',
      source: 'WEB', expires_at: null, created_at: new Date().toISOString(),
    },
  ]));
  return routeEvidence;
}

async function seedPocketSession(page) {
  // The previous seed used /landing, which boots real production JS via
  // main.tsx -> import('./App.tsx'). Immediately navigating to Pocket while
  // that unrelated lazy import is in flight can abort a module in WebKit and
  // raise "Importing a module script failed" in the *next* page.
  // Seed on the same origin using an intentionally script-free document.
  // Actual Pocket still gets one unmodified, production-built hard navigation.
  await page.route('**/__pocket_session_seed', route => route.fulfill({
    status: 200,
    contentType: 'text/html; charset=utf-8',
    body: '<!doctype html><html><head><title>Pocket session seed</title></head><body>Session seed</body></html>',
  }));
  await page.goto(`${baseUrl}/__pocket_session_seed`, { waitUntil: 'load' });
  const seedState = await page.evaluate(() => ({
    origin: location.origin,
    scripts: document.scripts.length,
  }));
  if (seedState.origin !== new URL(baseUrl).origin || seedState.scripts !== 0) {
    throw new Error('Pocket session seed must be same-origin and script-free');
  }
  const runtimeCredentials = { ...credentials, api_base_url: baseUrl };
  await page.evaluate(async (creds) => {
    await new Promise((resolve, reject) => {
      const request = indexedDB.open('digital-crown-zka', 1);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains('secure_keys')) request.result.createObjectStore('secure_keys');
      };
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('secure_keys', 'readwrite');
        tx.objectStore('secure_keys').put(creds, 'zka_credentials');
        tx.oncomplete = () => { db.close(); resolve(); };
        tx.onerror = () => reject(tx.error);
      };
    });
  }, runtimeCredentials);
}

async function captureRuntimeFailure(page, stage, role, viewport, errors) {
  // Diagnostics are strictly synthetic. Never serialize tokens, IDB values or headers.
  const label = `failure-${engine.name()}-${role.slug}-${viewport.width}x${viewport.height}-${stage}`;
  const diagnostic = { stage, engine: engine.name(), role: role.value, viewport, pageUrlPath: null,
    readyState: null, locationPath: null, shellCount: null, onboardingCount: null,
    textPreview: null, indexedDbNames: null, credentialKeyPresent: null, errors };
  try {
    const url = new URL(page.url());
    diagnostic.pageUrlPath = url.pathname;
    Object.assign(diagnostic, await page.evaluate(async () => {
      let indexedDbNames = null;
      let credentialKeyPresent = null;
      try {
        const dbs = await indexedDB.databases();
        indexedDbNames = dbs.map(db => db.name);
        const request = indexedDB.open('digital-crown-zka', 1);
        credentialKeyPresent = await new Promise(resolve => {
          request.onerror = () => resolve(false);
          request.onsuccess = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('secure_keys')) { db.close(); resolve(false); return; }
            const tx = db.transaction('secure_keys', 'readonly');
            const get = tx.objectStore('secure_keys').get('zka_credentials');
            get.onerror = () => resolve(false);
            get.onsuccess = () => resolve(Boolean(get.result?.publicId && get.result?.device_id));
            tx.oncomplete = () => db.close();
          };
        });
      } catch { indexedDbNames = ['unavailable']; credentialKeyPresent = false; }
      return {
        readyState: document.readyState,
        locationPath: location.pathname,
        shellCount: document.querySelectorAll('[data-dc-mobile-shell]').length,
        onboardingCount: document.querySelectorAll('[data-mobile-onboarding]').length,
        textPreview: document.body?.innerText?.slice(0, 500) ?? null,
        indexedDbNames,
        credentialKeyPresent,
      };
    }));
  } catch (error) { diagnostic.inspectError = error instanceof Error ? error.message : String(error); }
  try { await page.screenshot({ path: path.join(outputDir, label + '.png'), timeout: 7000 }); }
  catch (error) { diagnostic.screenshotError = error instanceof Error ? error.message : String(error); }
  await fs.writeFile(path.join(outputDir, label + '.json'), JSON.stringify(diagnostic, null, 2));
  console.error('Pocket WebKit failure diagnostics:', JSON.stringify(diagnostic));
}

// Screen capture is visual evidence, not an arbitrary animation frame.
// Framer Motion reveals the active Pocket tab from opacity 0 -> 1; WebKit
// previously captured Today's card while it was still near-transparent.
async function captureStableScreenshot(page, options) {
  const layerState = await page.waitForFunction(() => {
    const shell = document.querySelector('[data-dc-mobile-shell]');
    const layer = shell?.querySelector('main > div');
    if (!(layer instanceof HTMLElement)) return false;
    const opacity = Number.parseFloat(getComputedStyle(layer).opacity);
    return Number.isFinite(opacity) && opacity >= 0.999 ? { opacity } : false;
  }, null, { timeout: 15000 });
  const state = await layerState.jsonValue();
  if (!state || state.opacity < 0.999) throw new Error('Pocket screenshot layer not fully opaque');
  await page.screenshot({ ...options, animations: 'disabled' });
}

// Perform one genuine hard-load of Pocket per fresh browser context, then
// move between its tabs through React Router history. Repeated page.goto()
// unmounted the real SPA 12 times within seconds and caused WebKit to report
// aborted dynamic module imports after the next page had already rendered.
// This preserves route-resolution and RBAC checks on each ?tab= URL. Errors
// and missing route views still fail the run; no catch/retry is introduced.
async function navigatePocketDeepLink(page, tab = null) {
  const suffix = tab ? `?tab=${tab}` : '';
  const path = `/mobile/dashboard${suffix}`;
  if (!tab || !(await page.locator('[data-dc-mobile-shell]').count())) {
    const response = await page.goto(`${baseUrl}${path}`, {
      waitUntil: 'networkidle', timeout: 30000,
    });
    if (!response?.ok()) throw new Error(`Pocket deep-link HTTP ${response?.status() ?? 'missing'}: ${tab || 'today'}`);
    return;
  }
  await page.evaluate(nextPath => {
    window.history.pushState(window.history.state, '', nextPath);
    window.dispatchEvent(new PopStateEvent('popstate', { state: window.history.state }));
  }, path);
  await page.waitForURL(url => url.pathname === '/mobile/dashboard'
    && url.searchParams.get('tab') === tab, { timeout: 10000 });
}


async function visualMain() {
  const visualReport = {
    sourceHead: process.env.CPV2_SOURCE_HEAD || 'unverified',
    engine: engine.name(),
    evidenceKind: 'production-built real Pocket UI with synthetic paired API fixtures',
    realCabinetPaired: false,
    captures: [],
  };
  await fs.mkdir(outputDir, { recursive: true });
  const browser = await engine.launch({ headless: true });
  const captureWidths = engine.name() === 'webkit'
    ? [{ width: 390, height: 844 }, { width: 430, height: 932 }]
    : [{ width: 390, height: 844 }, { width: 430, height: 932 }, { width: 768, height: 1024 }, { width: 1280, height: 800 }];
  try {
    for (const viewport of captureWidths) {
      const context = await browser.newContext({ viewport, serviceWorkers: 'block', reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await installRoutes(page, 'DENTISTE');
      await seedPocketSession(page);
      await navigatePocketDeepLink(page, 'securite');
      await page.getByText('Téléphone connecté', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
      await page.locator('[data-pocket-read-status="ready"]').waitFor({ state: 'visible', timeout: 25000 });
      const unlink = page.getByRole('button', { name: 'Délier ce téléphone' });
      await unlink.scrollIntoViewIfNeeded();
      await unlink.waitFor({ state: 'visible' });
      const prefix = `pocket-unlink-${engine.name()}-${viewport.width}`;
      await page.screenshot({ path: path.join(outputDir, `${prefix}-button.png`), animations: 'disabled' });
      await unlink.click();
      const confirm = page.getByRole('button', { name: 'Confirmer', exact: true });
      await confirm.waitFor({ state: 'visible' });
      await page.getByText(/Cela supprimera l’accès enregistré sur ce téléphone/).waitFor({ state: 'visible' });
      await confirm.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(outputDir, `${prefix}-confirmation.png`), animations: 'disabled' });
      await page.route('**/api/mobile/revoke-device', route => json(route, { detail: 'isolated on-prem backend unavailable' }, 503));
      await confirm.click();
      await page.waitForURL(url => url.pathname === '/mobile/onboarding' &&
        url.searchParams.get('revocation') === 'pending', { timeout: 25000 });
      const pending = page.locator('[data-mobile-revocation-pending]');
      await pending.waitFor({ state: 'visible', timeout: 15000 });
      if (!(await pending.innerText()).includes("La révocation auprès de l’ancien cabinet n’a pas pu être confirmée")) {
        throw new Error('No visible unconfirmed remote revocation warning after local unlink');
      }
      const cleared = await page.evaluate(async () => {
        const get = async key => new Promise(resolve => {
          const open = indexedDB.open('digital-crown-zka', 1);
          open.onerror = () => resolve('DB_ERROR');
          open.onsuccess = () => {
            const db = open.result;
            if (!db.objectStoreNames.contains('secure_keys')) { db.close(); return resolve(null); }
            const tx = db.transaction('secure_keys', 'readonly');
            const req = tx.objectStore('secure_keys').get(key);
            req.onsuccess = () => resolve(req.result === undefined ? null : 'STILL_PRESENT');
            req.onerror = () => resolve('READ_ERROR');
            tx.oncomplete = () => db.close();
          };
        });
        return {
          credentials: await get('zka_credentials'),
          snapshot: await get('zka_last_snapshot'),
          queue: await get('zka_action_queue_v2'),
        };
      });
      if (Object.values(cleared).some(v => v !== null)) throw new Error('Local unpair retained records: '+JSON.stringify(cleared));
      await page.screenshot({ path: path.join(outputDir, `${prefix}-revocation-pending.png`), animations: 'disabled' });
      if (errors.length) throw new Error('Runtime errors: '+JSON.stringify(errors));
      visualReport.captures.push({ viewport, prefix, scenarios: ['button','confirmation','revocation-pending'], localRecordsCleared: true,
        browserErrors: 0, realBackend: false });
      await context.close();
    }
  } finally {
    await fs.writeFile(path.join(outputDir,'unlink-visual-report.json'),JSON.stringify(visualReport,null,2));
    await browser.close();
  }
  console.log(JSON.stringify(visualReport,null,2));
}
await visualMain();
