import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'marketplace-p5-before-artifacts');
const APP_URL = 'http://127.0.0.1:5178/approvisionnement';

const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '430x932', width: 430, height: 932 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x800', width: 1280, height: 800 },
];

const user = {
  id: 'baseline-user',
  email: 'baseline@digitalcrown.local',
  role: 'DENTISTE',
  is_superadmin: false,
  is_licensed: true,
  license_expires_at: '2030-12-31T23:59:59Z',
  full_name: 'Dr Baseline',
  nom_complet: 'Dr Baseline',
  cabinet_name: 'Cabinet Atlas',
  permissions: { patients: true },
  employer_id: 101,
  app_metadata: {},
  user_metadata: {},
  aud: 'authenticated',
  created_at: '2026-01-01T00:00:00Z',
};

const strategyPresets = [
  {
    key: 'sent_commission_10',
    label: 'Commission sur commande envoyée',
    settlementBasis: 'SENT_TO_PARTNER',
    revenueModel: 'COMMISSION_PERCENT',
    commissionRate: 10,
    discountRate: 0,
    fixedFeeAmount: 0,
    description: 'Vous êtes rémunéré dès que la commande est envoyée au fournisseur.',
  },
  {
    key: 'confirmed_commission_10',
    label: 'Commission sur commande confirmée',
    settlementBasis: 'CONFIRMED',
    revenueModel: 'COMMISSION_PERCENT',
    commissionRate: 10,
    discountRate: 0,
    fixedFeeAmount: 0,
    description: 'Le revenu est reconnu à confirmation fournisseur.',
  },
];

const suppliers = [
  {
    id: 11,
    supplierKey: 'atlas-dental',
    name: 'Atlas Dental Supply',
    badge: 'Partenaire premium',
    description: 'Consommables et restauration pour cabinet dentaire.',
    promise: 'Livraison suivie et catalogue clinique structuré.',
    apiBaseUrl: null,
    syncMode: 'manual',
    isActive: true,
    productCount: 5,
  },
  {
    id: 12,
    supplierKey: 'medident-pro',
    name: 'Medident Pro',
    badge: 'Spécialiste endodontie',
    description: 'Instrumentation et endodontie.',
    promise: 'Références techniques sélectionnées pour les soins courants.',
    apiBaseUrl: null,
    syncMode: 'manual',
    isActive: true,
    productCount: 3,
  },
];

const products = [
  { id: 101, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-101', name: 'Composite universel nano-hybride', sku: 'CMP-NH-01', dentalCategory: 'Restauration', dentalSpecialty: 'Omnipratique', unit: 'seringue', price: 390, availability: 'AVAILABLE', shortDescription: 'Composite universel haute esthétique pour restaurations antérieures et postérieures.', longDescription: 'Composite universel conçu pour une manipulation simple et une finition clinique rapide.', benefits: ['Polissage rapide', 'Teinte universelle'], isFeatured: true, sortOrder: 1 },
  { id: 102, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-102', name: 'Gants nitrile premium', sku: 'NIT-PRO-M', dentalCategory: 'Consommables', dentalSpecialty: 'Omnipratique', unit: 'boîte', price: 78, availability: 'AVAILABLE', shortDescription: 'Gants nitrile non poudrés, boîte de 100.', longDescription: 'Protection quotidienne du cabinet avec texture digitale.', benefits: ['Sans latex', 'Texture digitale'], isFeatured: true, sortOrder: 2 },
  { id: 103, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-103', name: 'Digue dentaire 6×6', sku: 'DYG-66', dentalCategory: 'Consommables', dentalSpecialty: 'Endodontie', unit: 'boîte', price: 145, availability: 'AVAILABLE', shortDescription: 'Feuilles de digue prêtes pour isolation clinique.', longDescription: 'Élasticité homogène et contraste adapté aux procédures endodontiques.', benefits: ['Isolation', 'Contraste'], isFeatured: false, sortOrder: 3 },
  { id: 104, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-104', name: 'Ciment verre ionomère', sku: 'CVI-09', dentalCategory: 'Restauration', dentalSpecialty: 'Dentisterie pédiatrique', unit: 'kit', price: 520, availability: 'ON_REQUEST', shortDescription: 'Kit verre ionomère pour restauration et scellement.', longDescription: 'Conditionnement cabinet avec dosage simplifié.', benefits: ['Fluor', 'Dosage simple'], isFeatured: false, sortOrder: 4 },
  { id: 105, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-105', name: 'Canules d’aspiration chirurgicale', sku: 'CAN-CH-20', dentalCategory: 'Consommables', dentalSpecialty: 'Chirurgie orale', unit: 'sachet', price: 42, availability: 'AVAILABLE', shortDescription: 'Canules stériles à usage unique.', longDescription: 'Aspiration précise pour les actes chirurgicaux.', benefits: ['Stérile', 'Usage unique'], isFeatured: false, sortOrder: 5 },
  { id: 201, supplierId: 12, supplierName: 'Medident Pro', externalProductId: 'MDP-201', name: 'Limes rotatives NiTi', sku: 'ENDO-NITI', dentalCategory: 'Endodontie', dentalSpecialty: 'Endodontie', unit: 'blister', price: 295, availability: 'AVAILABLE', shortDescription: 'Séquence NiTi rotative pour préparation canalaire.', longDescription: 'Séquence simplifiée avec repérage couleur.', benefits: ['Flexibilité', 'Repérage couleur'], isFeatured: true, sortOrder: 1 },
  { id: 202, supplierId: 12, supplierName: 'Medident Pro', externalProductId: 'MDP-202', name: 'Localisateur d’apex compact', sku: 'APEX-C1', dentalCategory: 'Endodontie', dentalSpecialty: 'Endodontie', unit: 'unité', price: 2450, availability: 'ON_REQUEST', shortDescription: 'Localisateur d’apex compact pour endodontie quotidienne.', longDescription: 'Écran lisible et protocole de mesure simple.', benefits: ['Compact', 'Lecture rapide'], isFeatured: true, sortOrder: 2 },
  { id: 203, supplierId: 12, supplierName: 'Medident Pro', externalProductId: 'MDP-203', name: 'Kit instrumentation parodontale', sku: 'PARO-KIT', dentalCategory: 'Instrumentation', dentalSpecialty: 'Parodontie', unit: 'kit', price: 690, availability: 'AVAILABLE', shortDescription: 'Kit de curettes et sondes pour maintenance parodontale.', longDescription: 'Instrumentation inox organisée par indication.', benefits: ['Inox', 'Kit complet'], isFeatured: false, sortOrder: 3 },
];

const catalogMeta = {
  categories: ['Consommables', 'Restauration', 'Endodontie', 'Instrumentation'],
  specialties: ['Omnipratique', 'Endodontie', 'Dentisterie pédiatrique', 'Chirurgie orale', 'Parodontie'],
  availability: ['AVAILABLE', 'ON_REQUEST', 'DISCONTINUED'],
};

const clinicProfile = {
  nom_praticien: 'Dr Baseline',
  nom_cabinet: 'Cabinet Atlas',
  selected_theme: 'elite',
  selected_template: 'swiss',
  font_fr: 'inter',
  primary_color: '#003380',
  secondary_color: '#1e40af',
  accent_color: '#60a5fa',
  show_patient_badges: true,
  performance_mode: false,
  clinical_tips_enabled: true,
  header_lines_fr: ['Dr Baseline', 'Chirurgien Dentiste'],
  specialty_ids: [],
};

const json = (body, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

function makeToken() {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ sub: user.id, exp: Math.floor(Date.now() / 1000) + 7200 })}.baseline`;
}

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  let lastError = null;
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}: ${lastError?.message || 'timeout'}`);
}

async function installApiMocks(page) {
  await page.route(/https?:\/\/[^/]+:8005\/.*/, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname.replace(/\/$/, '');

    if (pathname === '/health') return route.fulfill(json({ status: 'ok' }));
    if (pathname === '/api/auth/me') return route.fulfill(json(user));
    if (pathname === '/api/clinics/init-status') return route.fulfill(json({ is_initialized: true }));
    if (pathname === '/api/clinics/me') return route.fulfill(json(clinicProfile));
    if (pathname === '/api/partner-orders/meta') {
      return route.fulfill(json({
        supportedStatuses: ['DRAFT', 'SENT_TO_PARTNER', 'MODIFIED_AFTER_SEND', 'CONFIRMED', 'FULFILLED', 'CANCELLED'],
        supportedSettlementBases: ['SENT_TO_PARTNER', 'CONFIRMED', 'FULFILLED'],
        supportedRevenueModels: ['COMMISSION_PERCENT', 'DISCOUNT_RESALE', 'FIXED_FEE_PER_ORDER'],
        strategyPresets,
      }));
    }
    if (pathname === '/api/partner-catalog/meta') return route.fulfill(json(catalogMeta));
    if (pathname === '/api/partner-catalog/suppliers') return route.fulfill(json(suppliers));
    if (pathname === '/api/partner-catalog/products') return route.fulfill(json(products));
    if (pathname === '/api/partner-orders' && request.method() === 'POST') {
      return route.fulfill(json({ orderNumber: 'LOT-P5-BEFORE', strategyLabel: strategyPresets[0].label }, 201));
    }

    if (request.method() === 'GET') return route.fulfill(json({}));
    return route.fulfill(json({}, 200));
  });
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });

const server = spawn(
  process.platform === 'win32' ? 'npm.cmd' : 'npm',
  ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '5178'],
  {
    cwd: FRONTEND_DIR,
    env: { ...process.env, BROWSER: 'none' },
    stdio: ['ignore', 'pipe', 'pipe'],
  },
);

let serverLog = '';
server.stdout.on('data', (chunk) => { serverLog += chunk.toString(); });
server.stderr.on('data', (chunk) => { serverLog += chunk.toString(); });

const captures = [];
let browser;

try {
  await waitForServer('http://127.0.0.1:5178');
  browser = await chromium.launch({ headless: true });

  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
      reducedMotion: 'reduce',
      locale: 'fr-FR',
    });

    await context.addInitScript(({ token, baselineUser }) => {
      localStorage.clear();
      sessionStorage.clear();
      localStorage.setItem('token', token);
      localStorage.setItem('appMode', 'prod');
      localStorage.setItem('auth-storage', JSON.stringify({
        state: { user: baselineUser, isAuthenticated: true },
        version: 0,
      }));
      localStorage.setItem('app_background_animated', 'false');
    }, { token: makeToken(), baselineUser: user });

    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));
    page.on('console', (message) => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    });

    await installApiMocks(page);
    const response = await page.goto(APP_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByText('Marketplace clinique premium').waitFor({ state: 'visible', timeout: 30000 });
    await page.waitForFunction(() => !document.body.innerText.includes('Chargement du catalogue'), null, { timeout: 30000 }).catch(() => {});

    const metrics = await page.evaluate(() => {
      const doc = document.documentElement;
      const body = document.body;
      const main = document.querySelector('main');
      const width = window.innerWidth;
      const scrollWidth = Math.max(doc.scrollWidth, body.scrollWidth);
      const h1 = document.querySelector('h1');
      return {
        innerWidth: width,
        innerHeight: window.innerHeight,
        scrollWidth,
        hasHorizontalOverflow: scrollWidth > width + 1,
        bodyScrollHeight: body.scrollHeight,
        mainClientHeight: main?.clientHeight ?? null,
        mainScrollHeight: main?.scrollHeight ?? null,
        heading: h1?.textContent?.trim() || null,
        visibleTextLength: body.innerText.length,
      };
    });

    const screenshot = `before-${viewport.name}.png`;
    await page.screenshot({ path: path.join(OUTPUT_DIR, screenshot), fullPage: false });

    captures.push({
      viewport: viewport.name,
      screenshot,
      httpStatus: response?.status() ?? null,
      pageReady: Boolean(metrics.heading?.includes('Une vraie vitrine')),
      pageErrors,
      consoleErrors,
      metrics,
    });

    await context.close();
  }
} finally {
  if (browser) await browser.close();
  server.kill('SIGTERM');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}

const report = {
  chantier: 'Digital Crown Marketplace',
  lot: 'P5 UX/UI BEFORE baseline',
  productHead: PRODUCT_HEAD,
  route: '/approvisionnement',
  captureMode: 'real React route + Vite + mocked local API boundary',
  mockScope: 'auth, clinic init/profile, Marketplace catalog/order metadata only',
  viewports: viewports.map(({ name, width, height }) => ({ name, width, height })),
  captures,
};

await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
await writeFile(
  path.join(OUTPUT_DIR, 'metadata.txt'),
  [
    `chantier=${report.chantier}`,
    `lot=${report.lot}`,
    `product_head=${PRODUCT_HEAD}`,
    `route=${report.route}`,
    `viewports=${viewports.map((item) => item.name).join(',')}`,
    'deployment=none',
  ].join('\n') + '\n',
  'utf8',
);

const invalidCaptures = captures.filter((capture) => !capture.pageReady || capture.pageErrors.length > 0);
if (invalidCaptures.length > 0) {
  console.error(JSON.stringify({ invalidCaptures }, null, 2));
  process.exitCode = 1;
} else {
  console.log(JSON.stringify(report, null, 2));
}
