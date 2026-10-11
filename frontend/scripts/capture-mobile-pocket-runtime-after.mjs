import { createRequire } from 'node:module';
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

async function installRoutes(page, role, selectedTheme = { id: 'elite', primary: '#003380', secondary: '#1e40af', accent: '#60a5fa' }) {
  const routeEvidence = { passkeyStatusHits: 0 };
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

async function assertTouchTarget(locator, label) {
  const box = await locator.boundingBox();
  if (!box || box.width < 44 || box.height < 44) {
    throw new Error(`${label}: touch target below 44px (${box?.width}x${box?.height})`);
  }
}

async function assertRuntime(page, role, viewport, runtimeErrors) {
  await page.locator('[data-dc-mobile-shell]').waitFor({ state: 'visible', timeout: 30000 });
  if (await page.locator('[data-dc-preview-demo]').count()) throw new Error('Preview marker present in runtime proof');
  const today = page.locator('[data-dc-pocket-today]');
  await today.waitFor({ state: 'visible' });
  const roleMarker = await today.getAttribute('data-dc-pocket-role');
  if (roleMarker !== role.marker) throw new Error(`${role.value}: role marker ${roleMarker}`);
  await page.getByText(role.label, { exact: true }).waitFor({ state: 'visible' });

  const nav = page.locator('[data-mobile-bottom-nav]');
  await nav.waitFor({ state: 'visible' });
  const geometry = await page.evaluate(() => {
    const nav = document.querySelector('[data-mobile-bottom-nav]');
    if (!(nav instanceof HTMLElement)) throw new Error('Canonical nav missing');
    return {
      navButtons: nav.querySelectorAll('button').length,
      navHeight: nav.getBoundingClientRect().height,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    };
  });
  if (geometry.navButtons !== 5) throw new Error(`${role.value}/${viewport.width}: nav buttons ${geometry.navButtons}`);
  await nav.getByText('Agenda', { exact: true }).waitFor({ state: 'visible' });
  await nav.getByText('Patients', { exact: true }).waitFor({ state: 'visible' });
  if (await nav.getByText('Assistant', { exact: true }).count()) throw new Error('P1: unfinished assistant still pinned to the primary nav');
  if (await nav.getByText('Alertes', { exact: true }).count()) throw new Error('Legacy Alertes permanent nav leaked into canonical Pocket nav');
  if (geometry.navHeight !== 76) throw new Error(`${role.value}/${viewport.width}: nav height ${geometry.navHeight}`);
  if (geometry.horizontalOverflow) throw new Error(`${role.value}/${viewport.width}: overflow ${geometry.scrollWidth}>${geometry.innerWidth}`);
  await assertTouchTarget(page.locator('input[type="date"]'), 'date input');
  const todayScreenshot = `runtime-${role.slug}-today-${viewport.width}x${viewport.height}.png`;
  await captureStableScreenshot(page, { path: path.join(outputDir, todayScreenshot) });

  // P1: the Agenda must be a separate, authorized day list with no desktop mutations.
  await nav.getByText('Agenda', { exact: true }).click();
  await page.locator('[data-dc-pocket-agenda]').waitFor({ state: 'visible' });
  const agendaScreenshot = `runtime-${role.slug}-agenda-${viewport.width}x${viewport.height}.png`;
  await captureStableScreenshot(page, { path: path.join(outputDir, agendaScreenshot) });

  await nav.getByText('Plus', { exact: true }).click();
  const moreMenu = page.locator('[data-mobile-more-menu]');
  await moreMenu.waitFor({ state: 'visible' });
  // The nav is visually above the dialog: Safari must not be able to reach it
  // by touch, hardware keyboard or accessibility navigation while modal.
  if (!(await nav.evaluate(element => element.inert && element.hasAttribute('inert')))) {
    throw new Error('Pocket Plus modal left background navigation interactive');
  }
  // Inspect initial menu geometry before moving the scroll position: WebKit
  // differs from Chromium when a focused overflow container opens in a portal.
  const menuState = await page.evaluate(() => {
    const menu = document.querySelector('[data-mobile-more-menu]');
    const dialog = menu?.querySelector('[role="dialog"]');
    const items = [...(menu?.querySelectorAll('[data-mobile-more-item]') ?? [])];
    const rect = (element) => {
      const b = element.getBoundingClientRect();
      return { top: b.top, bottom: b.bottom, height: b.height };
    };
    const css = dialog ? getComputedStyle(dialog) : null;
    const ancestorOpacity = [];
    for (let parent = dialog; parent && parent !== document.body; parent = parent.parentElement) {
      const style = getComputedStyle(parent);
      ancestorOpacity.push({ tag: parent.tagName, opacity: style.opacity, filter: style.filter, backdropFilter: style.backdropFilter });
    }
    const nav = document.querySelector('[data-mobile-bottom-nav]');
    return {
      role: document.querySelector('[data-dc-pocket-today]')?.getAttribute('data-dc-pocket-role'),
      dialog: dialog ? rect(dialog) : null,
      dialogBackground: css?.backgroundColor ?? null,
      dialogOpacity: css?.opacity ?? null,
      cardToken: css?.getPropertyValue('--card-bg').trim() ?? null,
      ancestorOpacity,
      navBackground: nav ? getComputedStyle(nav).backgroundColor : null,
      items: items.map(item => ({
        id: item.getAttribute('data-mobile-more-item'),
        text: item.textContent?.trim(),
        rect: rect(item),
      })),
    };
  });
  await fs.writeFile(path.join(outputDir, `menu-${role.slug}-${viewport.width}x${viewport.height}-${engine.name()}.json`),
    JSON.stringify(menuState, null, 2));
  // A visual smoke test cannot pass merely because the dialog has "bg-card":
  // Safari must resolve the actual drawn surface and every ancestor to opaque.
  const isOpaqueColor = value => {
    if (!value || value === 'transparent') return false;
    // WebKit may serialize resolved CSS Color 4 as color(srgb r g b / a).
    // Fail closed on unknown formats or opacity < 1, rather than requiring
    // only rgb()/rgba() and misclassifying an opaque Safari surface.
    const rgb = value.match(/^rgba?\(([^)]*)\)$/);
    const srgb = value.match(/^color\(srgb\s+([^)]*)\)$/);
    if (!rgb && !srgb) return false;
    const channels = (rgb?.[1] ?? srgb?.[1] ?? '').split(/[,\s/]+/).filter(Boolean);
    return (channels.length === 3 || channels.length === 4)
      && channels.slice(0, 3).every(channel => Number.isFinite(Number(channel)))
      && (channels.length === 3 || Number(channels[3]) >= 0.999);
  };
  if (!isOpaqueColor(menuState.dialogBackground)
    || !isOpaqueColor(menuState.navBackground)
    || menuState.ancestorOpacity.some(entry => Number(entry.opacity) < 0.999 || entry.filter !== 'none')) {
    throw new Error(`Pocket Safari Plus must be opaque: ${JSON.stringify(menuState)}`);
  }
  await captureStableScreenshot(page, { path: path.join(outputDir, `menu-before-scroll-${role.slug}-${viewport.width}x${viewport.height}-${engine.name()}.png`) });
  // Plus contains an intentionally scrollable secondary-action list. A menu
  // item can be in the DOM but outside the visible scrollport on WebKit.
  // Exercise the user's actual scrollable menu, then assert rendered labels.
  async function assertMoreItem(id, label) {
    const item = moreMenu.locator(`[data-mobile-more-item="${id}"]`);
    await item.waitFor({ state: 'attached', timeout: 15000 });
    await item.scrollIntoViewIfNeeded({ timeout: 15000 });
    await item.waitFor({ state: 'visible', timeout: 15000 });
    await item.getByText(label, { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
  }
  await assertMoreItem('waiting-room', 'Salle d’attente');
  await assertMoreItem('frontdesk', 'Accueil');
  await assertMoreItem('securite', 'Sécurité');
  await moreMenu.getByRole('button', { name: 'Assistant' }).scrollIntoViewIfNeeded();
  await moreMenu.getByRole('button', { name: 'Assistant' }).waitFor({ state: 'visible' });
  const labelIds = new Map([
    ['Notifications', 'notifications'], ['Stock', 'stock'], ['Bibliothèque', 'library'],
    ['Approvisionnement', 'marketplace'], ['Trésorerie', 'finance'],
    ['Envois Labo', 'lab'], ['Équipe', 'dentists'],
  ]);
  const expectedLabels = role.value === 'DENTISTE' ? expectedDentistLabels : expectedSecretaryLabels;
  for (const label of expectedLabels) {
    await assertMoreItem(labelIds.get(label), label);
  }
  await moreMenu.locator('[data-mobile-more-item="waiting-room"]').scrollIntoViewIfNeeded();
  if (role.value === 'SECRETAIRE' && await moreMenu.getByText('Bibliothèque', { exact: true }).count()) {
    throw new Error('SECRETAIRE: Bibliothèque must remain RBAC-hidden in Plus');
  }
  await assertTouchTarget(page.getByRole('button', { name: 'Fermer Plus' }), 'Plus close');

  const screenshot = `runtime-${role.slug}-plus-${viewport.width}x${viewport.height}.png`;
  await captureStableScreenshot(page, { path: path.join(outputDir, screenshot) });
  // A user would dismiss the overlay before following another route.
  // Hard reloading hid this persistent React state in the previous harness.
  await page.getByRole('button', { name: 'Fermer Plus' }).click();
  await moreMenu.waitFor({ state: 'detached' });
  if (await nav.evaluate(element => element.inert || element.hasAttribute('inert'))) {
    throw new Error('Pocket nav stayed inert after dismissing Plus');
  }

  await navigatePocketDeepLink(page, 'frontdesk');
  await page.getByText('Patient Web', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  if (await page.locator('[data-mobile-restricted]').count()) throw new Error('P1: Frontdesk rejected an authorized Pocket role');
  await captureStableScreenshot(page, { path: path.join(outputDir, `runtime-${role.slug}-frontdesk-${viewport.width}x${viewport.height}.png`) });

  await navigatePocketDeepLink(page, 'securite');
  await page.getByText('Téléphone connecté', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await captureStableScreenshot(page, { path: path.join(outputDir, `runtime-${role.slug}-securite-${viewport.width}x${viewport.height}.png`) });

  await navigatePocketDeepLink(page, 'stock');
  await page.locator('[data-mobile-stock]').waitFor({ state: 'visible', timeout: 30000 });
  await page.getByText('Gants nitrile', { exact: true }).waitFor({ state: 'visible' });
  if (await page.locator('[data-dc-preview-demo]').count()) throw new Error('Preview rendered for Stock deep-link');
  const stockScreenshot = `runtime-${role.slug}-stock-${viewport.width}x${viewport.height}.png`;
  await captureStableScreenshot(page, { path: path.join(outputDir, stockScreenshot) });

  await navigatePocketDeepLink(page, 'library');
  await page.locator('[data-mobile-library]').waitFor({ state: 'visible', timeout: 30000 });
  if (role.value === 'DENTISTE') await page.getByText('Bibliothèque', { exact: true }).first().waitFor({ state: 'visible' });
  else await page.getByText('Accès réservé', { exact: true }).waitFor({ state: 'visible' });
  await captureStableScreenshot(page, { path: path.join(outputDir, `runtime-${role.slug}-library-${viewport.width}x${viewport.height}.png`) });

  if (role.value === 'DENTISTE') {
    for (const [tab, marker] of [
      ['finance', '[data-mobile-finance]'],
      ['lab', '[data-mobile-lab]'],
      ['dentists', '[data-mob5a-team]'],
      ['marketplace', '[data-mobile-marketplace]'],
      ['bot', '[data-mobile-assistant]'],
    ]) {
      await navigatePocketDeepLink(page, tab);
      if (tab === 'lab') {
        // An empty LabView is a valid practitioner runtime state. Its root has zero
        // geometry when there are no jobs, so Playwright does not classify it as
        // "visible" even though the canonical Labo component is mounted.
        await page.locator(marker).waitFor({ state: 'attached', timeout: 30000 });
        if (await page.locator('[data-mobile-restricted]').count()) {
          throw new Error('DENTISTE: Labo deep-link resolved to the restricted role guard');
        }
      } else {
        await page.locator(marker).waitFor({ state: 'visible', timeout: 30000 });
      }
      await captureStableScreenshot(page, { path: path.join(outputDir, `runtime-${role.slug}-${tab}-${viewport.width}x${viewport.height}.png`) });
    }
  } else {
    for (const tab of ['finance', 'lab', 'marketplace']) {
      await navigatePocketDeepLink(page, tab);
      await page.locator('[data-mobile-restricted]').waitFor({ state: 'visible', timeout: 30000 });
      await page.getByText('Accès réservé', { exact: true }).waitFor({ state: 'visible' });
      await captureStableScreenshot(page, { path: path.join(outputDir, `runtime-${role.slug}-${tab}-${viewport.width}x${viewport.height}.png`) });
    }
    for (const [tab, marker] of [['dentists', '[data-mob5a-team]'], ['bot', '[data-mobile-assistant]']]) {
      await navigatePocketDeepLink(page, tab);
      await page.locator(marker).waitFor({ state: 'visible', timeout: 30000 });
      await captureStableScreenshot(page, { path: path.join(outputDir, `runtime-${role.slug}-${tab}-${viewport.width}x${viewport.height}.png`) });
    }
  }

  if (runtimeErrors.length) throw new Error(`${role.value}/${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);

  return { role: role.value, viewport, path: '/mobile/dashboard', preview: false, stockRoutable: true, libraryRoutable: true, restoredModulesRoutable: true, roleGuardsVerified: true, ...geometry, runtimeErrors, todayScreenshot, agendaScreenshot, screenshot, stockScreenshot };
}

await fs.mkdir(outputDir, { recursive: true });
// Screenshot fixtures intercept paired-mobile API responses through page.route.
// In WebKit, production Workbox can own these requests before page.route sees them,
// causing a *real* biometric origin guard against an unmocked response. Isolate
// route-fixture UI evidence from the service-worker/offline lifecycle contract;
// never disable biometrics in product code or change its fail-closed decision.
const screenshotContextOptions = viewport => ({ viewport, serviceWorkers: 'block' });
const browser = await engine.launch({ headless: true });
const evidence = [];
const themeEvidence = [];

try {
  for (const role of roles) {
    for (const viewport of viewports) {
      const context = await browser.newContext(screenshotContextOptions(viewport));
      const page = await context.newPage();
      const runtimeErrors = [];
      const assetFailures = [];
      const recordAssetFailure = (requestUrl, reason) => {
        try {
          const url = new URL(requestUrl);
          if (url.origin !== new URL(baseUrl).origin || !/^\/assets\/.*\.(js|css)$/.test(url.pathname)) return;
          assetFailures.push({ path: url.pathname, reason: String(reason).slice(0, 160) });
        } catch { /* Invalid diagnostic URL; never log opaque credentials. */ }
      };
      page.on('requestfailed', request => recordAssetFailure(request.url(), request.failure()?.errorText ?? 'requestfailed'));
      page.on('response', response => {
        if (response.status() >= 400) recordAssetFailure(response.url(), `HTTP ${response.status()}`);
      });
      page.on('pageerror', error => runtimeErrors.push(`pageerror:${error.message}`));
      page.on('console', message => {
        if (message.type() === 'error' && !message.text().toLowerCase().includes('[vite]')) {
          runtimeErrors.push(`console:${message.text()}`);
        }
      });

      const failStage = 'runtime';
      try {
        const routes = await installRoutes(page, role.value);
        await seedPocketSession(page);
        await navigatePocketDeepLink(page);
        const certified = await assertRuntime(page, role, viewport, runtimeErrors);
        if (assetFailures.length) {
          throw new Error(`Pocket production assets failed: ${JSON.stringify(assetFailures)}`);
        }
        if (routes.passkeyStatusHits < 1) throw new Error('Pocket passkey/status fixture not observed: certification cannot assert paired UI');
        evidence.push({ ...certified, passkeyStatusHits: routes.passkeyStatusHits, serviceWorkers: 'blocked-for-route-fixtures' });
      } catch (error) {
        await captureRuntimeFailure(page, failStage, role, viewport, [
          ...runtimeErrors, ...assetFailures.map(failure => `asset:${failure.path}:${failure.reason}`),
        ]).catch(console.error);
        throw error;
      } finally {
        await context.close();
      }
    }
  }
  // Selectable themes must come from the same paired cabinet runtime endpoint,
  // not from an injected CSS palette or the unauthenticated demo shell.
  for (const theme of themes) {
    const context = await browser.newContext(screenshotContextOptions({ width: 430, height: 932 }));
    const page = await context.newPage();
    const routes = await installRoutes(page, 'DENTISTE', theme);
    await seedPocketSession(page);
    await navigatePocketDeepLink(page);
    await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible', timeout: 30000 });
    await page.waitForFunction(({ id, primary }) => {
      const computed = getComputedStyle(document.documentElement);
      return document.documentElement.dataset.theme === id
        && computed.getPropertyValue('--primary').trim().toLowerCase() === primary.toLowerCase();
    }, { id: theme.id, primary: theme.primary }, { timeout: 20000 });
    // Theme data can arrive before the mobile capability guard has resolved.
    // A disabled + button is not a valid on-primary contrast oracle.
    await page.waitForFunction(() => {
      const action = document.querySelector('[data-mobile-bottom-nav] button[aria-label="Ouvrir les actions rapides"]');
      return action instanceof HTMLButtonElement && !action.disabled;
    }, null, { timeout: 20000 });
    // Global .bg-primary color transitions can briefly expose an intermediate
    // RGB even after the backend capability has enabled the button. Certify the
    // final on-primary foreground, never a transitional animation frame.
    await page.waitForFunction(({ foreground }) => {
      const action = document.querySelector('[data-mobile-bottom-nav] button[aria-label="Ouvrir les actions rapides"]');
      return action instanceof HTMLButtonElement
        && !action.disabled
        && getComputedStyle(action).color === foreground;
    }, { foreground: theme.foreground }, { timeout: 15000 });

    const result = await page.evaluate(() => {
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      const primaryAction = nav?.querySelector('button[aria-label="Ouvrir les actions rapides"]');
      const computed = getComputedStyle(document.documentElement);
      return {
        id: document.documentElement.dataset.theme,
        primary: computed.getPropertyValue('--primary').trim(),
        primaryInk: computed.getPropertyValue('--primary-ink').trim(),
        cardSurface: computed.getPropertyValue('--card-bg').trim(),
        canvasSurface: computed.getPropertyValue('--bg-medical-pearl').trim(),
        activeNavInk: nav?.querySelector('button[aria-current="page"]')
          ? getComputedStyle(nav.querySelector('button[aria-current="page"]')).color
          : null,
        textMuted: computed.getPropertyValue('--text-muted').trim(),
        textOnPrimary: computed.getPropertyValue('--text-on-primary').trim(),
        background: computed.getPropertyValue('--bg-medical-pearl').trim(),
        primaryActionText: primaryAction ? getComputedStyle(primaryAction).color : null,
        primaryActionDisabled: primaryAction instanceof HTMLButtonElement ? primaryAction.disabled : null,
        primaryActionClass: primaryAction?.getAttribute('class') ?? null,
        navBackground: nav ? getComputedStyle(nav).backgroundColor : null,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
        preview: Boolean(document.querySelector('[data-dc-preview-demo]')),
      };
    });
    if (result.preview || result.horizontalOverflow || result.primaryActionDisabled !== false
      || result.primaryActionText !== theme.foreground
      || !result.primaryInk || canonicalHexColor(result.textMuted) !== canonicalHexColor(theme.muted)) {
      throw new Error(`Pocket theme ${theme.id}: invalid mobile runtime inheritance: ${JSON.stringify(result)}`);
    }
    await captureStableScreenshot(page, { path: path.join(outputDir, `theme-${theme.id}-today-430x932.png`) });
    await page.locator('[data-mobile-bottom-nav]').getByText('Plus', { exact: true }).click();
    await page.locator('[data-mobile-more-menu]').waitFor({ state: 'visible' });
    if (!(await page.locator('[data-mobile-bottom-nav]').evaluate(element => element.inert && element.hasAttribute('inert')))) {
      throw new Error(`Pocket theme ${theme.id}: Plus left background nav interactive`);
    }
    await captureStableScreenshot(page, { path: path.join(outputDir, `theme-${theme.id}-plus-430x932.png`) });
    await page.getByRole('button', { name: 'Fermer Plus' }).click();
    await page.locator('[data-mobile-more-menu]').waitFor({ state: 'detached' });
    await navigatePocketDeepLink(page, 'stock');
    await page.getByText('Gants nitrile', { exact: true }).waitFor({ state: 'visible' });
    await captureStableScreenshot(page, { path: path.join(outputDir, `theme-${theme.id}-stock-430x932.png`) });
    await navigatePocketDeepLink(page, 'securite');
    await page.getByText('Téléphone connecté', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    await captureStableScreenshot(page, { path: path.join(outputDir, `theme-${theme.id}-securite-430x932.png`) });
    if (routes.passkeyStatusHits < 1) throw new Error(`Pocket ${theme.id}: passkey/status fixture not observed`);
    themeEvidence.push({ ...result, passkeyStatusHits: routes.passkeyStatusHits, serviceWorkers: 'blocked-for-route-fixtures' });
    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'runtime-evidence.json'), JSON.stringify(evidence, null, 2));
await fs.writeFile(path.join(outputDir, 'theme-evidence.json'), JSON.stringify(themeEvidence, null, 2));
console.log(JSON.stringify({ engine: engine.name(), evidence, themeEvidence }, null, 2));