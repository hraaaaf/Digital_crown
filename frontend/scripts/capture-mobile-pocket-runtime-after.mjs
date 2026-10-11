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
  await page.route('**/api/mobile/passkey/status', route => json(route, {
    state: 'disabled', credential_id: null, rp_id: 'digitalcrown.local',
    expected_origin: 'https://digitalcrown.local:8005', origin_ready: true,
    user_verification: 'required', server_gate: false,
  }));
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
}

async function seedPocketSession(page) {
  await page.goto(`${baseUrl}/landing`, { waitUntil: 'domcontentloaded' });
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
  await page.screenshot({ path: path.join(outputDir, todayScreenshot) });

  // P1: the Agenda must be a separate, authorized day list with no desktop mutations.
  await nav.getByText('Agenda', { exact: true }).click();
  await page.locator('[data-dc-pocket-agenda]').waitFor({ state: 'visible' });
  const agendaScreenshot = `runtime-${role.slug}-agenda-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, agendaScreenshot) });

  await nav.getByText('Plus', { exact: true }).click();
  const moreMenu = page.locator('[data-mobile-more-menu]');
  await moreMenu.waitFor({ state: 'visible' });
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
    return {
      role: document.querySelector('[data-dc-pocket-today]')?.getAttribute('data-dc-pocket-role'),
      dialog: dialog ? rect(dialog) : null,
      items: items.map(item => ({
        id: item.getAttribute('data-mobile-more-item'),
        text: item.textContent?.trim(),
        rect: rect(item),
      })),
    };
  });
  await fs.writeFile(path.join(outputDir, `menu-${role.slug}-${viewport.width}x${viewport.height}-${engine.name()}.json`),
    JSON.stringify(menuState, null, 2));
  await page.screenshot({ path: path.join(outputDir, `menu-before-scroll-${role.slug}-${viewport.width}x${viewport.height}-${engine.name()}.png`) });
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
  await page.screenshot({ path: path.join(outputDir, screenshot) });

  await page.goto(`${baseUrl}/mobile/dashboard?tab=frontdesk`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Patient Web', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  if (await page.locator('[data-mobile-restricted]').count()) throw new Error('P1: Frontdesk rejected an authorized Pocket role');
  await page.screenshot({ path: path.join(outputDir, `runtime-${role.slug}-frontdesk-${viewport.width}x${viewport.height}.png`) });

  await page.goto(`${baseUrl}/mobile/dashboard?tab=securite`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Téléphone connecté', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await page.screenshot({ path: path.join(outputDir, `runtime-${role.slug}-securite-${viewport.width}x${viewport.height}.png`) });

  await page.goto(`${baseUrl}/mobile/dashboard?tab=stock`, { waitUntil: 'domcontentloaded' });
  await page.locator('[data-mobile-stock]').waitFor({ state: 'visible', timeout: 30000 });
  await page.getByText('Gants nitrile', { exact: true }).waitFor({ state: 'visible' });
  if (await page.locator('[data-dc-preview-demo]').count()) throw new Error('Preview rendered for Stock deep-link');
  const stockScreenshot = `runtime-${role.slug}-stock-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, stockScreenshot) });

  await page.goto(`${baseUrl}/mobile/dashboard?tab=library`, { waitUntil: 'domcontentloaded' });
  await page.locator('[data-mobile-library]').waitFor({ state: 'visible', timeout: 30000 });
  if (role.value === 'DENTISTE') await page.getByText('Bibliothèque', { exact: true }).first().waitFor({ state: 'visible' });
  else await page.getByText('Accès réservé', { exact: true }).waitFor({ state: 'visible' });
  await page.screenshot({ path: path.join(outputDir, `runtime-${role.slug}-library-${viewport.width}x${viewport.height}.png`) });

  if (role.value === 'DENTISTE') {
    for (const [tab, marker] of [
      ['finance', '[data-mobile-finance]'],
      ['lab', '[data-mobile-lab]'],
      ['dentists', '[data-mob5a-team]'],
      ['marketplace', '[data-mobile-marketplace]'],
      ['bot', '[data-mobile-assistant]'],
    ]) {
      await page.goto(`${baseUrl}/mobile/dashboard?tab=${tab}`, { waitUntil: 'domcontentloaded' });
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
      await page.screenshot({ path: path.join(outputDir, `runtime-${role.slug}-${tab}-${viewport.width}x${viewport.height}.png`) });
    }
  } else {
    for (const tab of ['finance', 'lab', 'marketplace']) {
      await page.goto(`${baseUrl}/mobile/dashboard?tab=${tab}`, { waitUntil: 'domcontentloaded' });
      await page.locator('[data-mobile-restricted]').waitFor({ state: 'visible', timeout: 30000 });
      await page.getByText('Accès réservé', { exact: true }).waitFor({ state: 'visible' });
      await page.screenshot({ path: path.join(outputDir, `runtime-${role.slug}-${tab}-${viewport.width}x${viewport.height}.png`) });
    }
    for (const [tab, marker] of [['dentists', '[data-mob5a-team]'], ['bot', '[data-mobile-assistant]']]) {
      await page.goto(`${baseUrl}/mobile/dashboard?tab=${tab}`, { waitUntil: 'domcontentloaded' });
      await page.locator(marker).waitFor({ state: 'visible', timeout: 30000 });
      await page.screenshot({ path: path.join(outputDir, `runtime-${role.slug}-${tab}-${viewport.width}x${viewport.height}.png`) });
    }
  }

  if (runtimeErrors.length) throw new Error(`${role.value}/${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);

  return { role: role.value, viewport, path: '/mobile/dashboard', preview: false, stockRoutable: true, libraryRoutable: true, restoredModulesRoutable: true, roleGuardsVerified: true, ...geometry, runtimeErrors, todayScreenshot, agendaScreenshot, screenshot, stockScreenshot };
}

await fs.mkdir(outputDir, { recursive: true });
const browser = await engine.launch({ headless: true });
const evidence = [];
const themeEvidence = [];

try {
  for (const role of roles) {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      const runtimeErrors = [];
      page.on('pageerror', error => runtimeErrors.push(`pageerror:${error.message}`));
      page.on('console', message => {
        if (message.type() === 'error' && !message.text().toLowerCase().includes('[vite]')) {
          runtimeErrors.push(`console:${message.text()}`);
        }
      });

      const failStage = 'runtime';
      try {
        await installRoutes(page, role.value);
        await seedPocketSession(page);
        await page.goto(`${baseUrl}/mobile/dashboard`, { waitUntil: 'domcontentloaded' });
        evidence.push(await assertRuntime(page, role, viewport, runtimeErrors));
      } catch (error) {
        await captureRuntimeFailure(page, failStage, role, viewport, runtimeErrors).catch(console.error);
        throw error;
      } finally {
        await context.close();
      }
    }
  }
  // Selectable themes must come from the same paired cabinet runtime endpoint,
  // not from an injected CSS palette or the unauthenticated demo shell.
  for (const theme of themes) {
    const context = await browser.newContext({ viewport: { width: 430, height: 932 } });
    const page = await context.newPage();
    await installRoutes(page, 'DENTISTE', theme);
    await seedPocketSession(page);
    await page.goto(`${baseUrl}/mobile/dashboard`, { waitUntil: 'domcontentloaded' });
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
    await page.screenshot({ path: path.join(outputDir, `theme-${theme.id}-today-430x932.png`) });
    await page.locator('[data-mobile-bottom-nav]').getByText('Plus', { exact: true }).click();
    await page.locator('[data-mobile-more-menu]').waitFor({ state: 'visible' });
    await page.screenshot({ path: path.join(outputDir, `theme-${theme.id}-plus-430x932.png`) });
    await page.goto(`${baseUrl}/mobile/dashboard?tab=stock`, { waitUntil: 'domcontentloaded' });
    await page.getByText('Gants nitrile', { exact: true }).waitFor({ state: 'visible' });
    await page.screenshot({ path: path.join(outputDir, `theme-${theme.id}-stock-430x932.png`) });
    await page.goto(`${baseUrl}/mobile/dashboard?tab=securite`, { waitUntil: 'domcontentloaded' });
    await page.getByText('Téléphone connecté', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    await page.screenshot({ path: path.join(outputDir, `theme-${theme.id}-securite-430x932.png`) });
    themeEvidence.push(result);
    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'runtime-evidence.json'), JSON.stringify(evidence, null, 2));
await fs.writeFile(path.join(outputDir, 'theme-evidence.json'), JSON.stringify(themeEvidence, null, 2));
console.log(JSON.stringify({ engine: engine.name(), evidence, themeEvidence }, null, 2));