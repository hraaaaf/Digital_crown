import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const baseUrl = process.env.MOBILE_RUNTIME_URL || 'http://127.0.0.1:5173';
const outputDir = process.env.MOBILE_RUNTIME_DIR || '../artifacts/mobile-pocket-runtime';
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];
const roles = [
  { value: 'DENTISTE', slug: 'dentiste', marker: 'practitioner', label: 'Vue praticien · priorité clinique' },
  { value: 'SECRETAIRE', slug: 'secretaire', marker: 'assistant', label: 'Vue assistante · flux cabinet' },
];
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

async function installRoutes(page, role) {
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
    selected_theme: 'elite', primary_color: '#003380', secondary_color: '#1e40af',
    accent_color: '#60a5fa', app_accent_color: null, font_fr: 'inter',
  }));
  await page.route('**/api/lab-jobs/**', route => json(route, []));
  await page.route('**/api/mobile/dentists', route => json(route, { dentists: [] }));
  await page.route('**/stock/items', route => json(route, [
    { id: 1, nom: 'Gants nitrile', categorie: 'CONSOMMABLE', quantite: 8, seuil_alerte: 10, unite: 'boîte', fournisseur: 'Demo', alerte: true },
    { id: 2, nom: 'Composite', categorie: 'MATERIAU', quantite: 20, seuil_alerte: 5, unite: 'seringue', fournisseur: null, alerte: false },
  ]));
  await page.route('**/stock/alerts', route => json(route, []));
  await page.route('**/appointments/pending', route => json(route, [
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
  }, credentials);
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
  await nav.getByText('Assistant', { exact: true }).waitFor({ state: 'visible' });
  if (await nav.getByText('Alertes', { exact: true }).count()) throw new Error('Legacy Alertes permanent nav leaked into canonical Pocket nav');
  if (geometry.navHeight !== 76) throw new Error(`${role.value}/${viewport.width}: nav height ${geometry.navHeight}`);
  if (geometry.horizontalOverflow) throw new Error(`${role.value}/${viewport.width}: overflow ${geometry.scrollWidth}>${geometry.innerWidth}`);
  await assertTouchTarget(page.locator('input[type="date"]'), 'date input');
  const todayScreenshot = `runtime-${role.slug}-today-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, todayScreenshot) });

  await nav.getByText('Plus', { exact: true }).click();
  const moreMenu = page.locator('[data-mobile-more-menu]');
  await moreMenu.waitFor({ state: 'visible' });
  await moreMenu.getByText('Salle d’attente', { exact: true }).waitFor({ state: 'visible' });
  await moreMenu.getByText('Accueil', { exact: true }).waitFor({ state: 'visible' });
  await moreMenu.getByText('Sécurité', { exact: true }).waitFor({ state: 'visible' });
  const expectedLabels = role.value === 'DENTISTE' ? expectedDentistLabels : expectedSecretaryLabels;
  for (const label of expectedLabels) {
    await moreMenu.getByText(label, { exact: true }).waitFor({ state: 'visible' });
  }
  if (role.value === 'SECRETAIRE' && await moreMenu.getByText('Bibliothèque', { exact: true }).count()) {
    throw new Error('SECRETAIRE: Bibliothèque must remain RBAC-hidden in Plus');
  }
  await assertTouchTarget(page.getByRole('button', { name: 'Fermer Plus' }), 'Plus close');

  const screenshot = `runtime-${role.slug}-plus-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, screenshot) });

  await page.goto(`${baseUrl}/mobile/dashboard?tab=stock`, { waitUntil: 'domcontentloaded' });
  await page.locator('[data-mobile-stock]').waitFor({ state: 'visible', timeout: 30000 });
  await page.getByText('Gants nitrile', { exact: true }).waitFor({ state: 'visible' });
  if (await page.locator('[data-dc-preview-demo]').count()) throw new Error('Preview rendered for Stock deep-link');
  const stockScreenshot = `runtime-${role.slug}-stock-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, stockScreenshot) });

  await page.goto(`${baseUrl}/mobile/dashboard?tab=library`, { waitUntil: 'networkidle' });
  await page.locator('[data-mobile-library]').waitFor({ state: 'visible', timeout: 30000 });
  if (role.value === 'DENTISTE') await page.getByText('Bibliothèque', { exact: true }).first().waitFor({ state: 'visible' });
  else await page.getByText('Accès réservé', { exact: true }).waitFor({ state: 'visible' });
  if (runtimeErrors.length) throw new Error(`${role.value}/${viewport.width}: runtime errors: ${runtimeErrors.join(' | ')}`);

  return { role: role.value, viewport, path: '/mobile/dashboard', preview: false, stockRoutable: true, libraryRoutable: true, ...geometry, runtimeErrors, todayScreenshot, screenshot, stockScreenshot };
}

await fs.mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const evidence = [];

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

      await installRoutes(page, role.value);
      await seedPocketSession(page);
      await page.goto(`${baseUrl}/mobile/dashboard`, { waitUntil: 'domcontentloaded' });
      evidence.push(await assertRuntime(page, role, viewport, runtimeErrors));
      await context.close();
    }
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'runtime-evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence, null, 2));