import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'mobile-marketplace-mob5g-artifacts');
const PORT = 5182;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const mobileViewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '430x932', width: 430, height: 932 },
  { name: '768x1024', width: 768, height: 1024 },
];
const desktopViewport = { name: '1280x800', width: 1280, height: 800 };

const user = {
  id: 'baseline-user', email: 'baseline@digitalcrown.local', role: 'DENTISTE', is_superadmin: false,
  is_licensed: true, license_expires_at: '2030-12-31T23:59:59Z', full_name: 'Dr Baseline',
  nom_complet: 'Dr Baseline', cabinet_name: 'Cabinet Atlas', permissions: { patients: true },
  employer_id: 101, app_metadata: {}, user_metadata: {}, aud: 'authenticated', created_at: '2026-01-01T00:00:00Z',
};

const strategyPresets = [{
  key: 'sent_commission_10', label: 'Commission sur commande envoyée', settlementBasis: 'SENT_TO_PARTNER',
  revenueModel: 'COMMISSION_PERCENT', commissionRate: 10, discountRate: 0, fixedFeeAmount: 0,
  description: 'Test certification.',
}];
const suppliers = [{ id: 11, supplierKey: 'atlas-dental', name: 'Atlas Dental Supply', badge: 'Partenaire', description: 'Catalogue test.', promise: 'Test.', apiBaseUrl: null, syncMode: 'manual', isActive: true, productCount: 4 }];
const products = [
  { id: 101, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-101', name: 'Composite universel nano-hybride', sku: 'CMP-NH-01', dentalCategory: 'Restauration', dentalSpecialty: 'Omnipratique', unit: 'seringue', price: 390, availability: 'AVAILABLE', shortDescription: 'Composite universel.', longDescription: 'Composite universel.', benefits: [], isFeatured: true, sortOrder: 1 },
  { id: 102, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-102', name: 'Limes rotatives NiTi', sku: 'ENDO-NITI', dentalCategory: 'Endodontie', dentalSpecialty: 'Endodontie', unit: 'blister', price: 295, availability: 'AVAILABLE', shortDescription: 'Limes NiTi.', longDescription: 'Limes NiTi.', benefits: [], isFeatured: true, sortOrder: 2 },
  { id: 103, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-103', name: 'Gants nitrile premium', sku: 'NIT-PRO-M', dentalCategory: 'Consommables', dentalSpecialty: 'Omnipratique', unit: 'boîte', price: 78, availability: 'AVAILABLE', shortDescription: 'Gants nitrile.', longDescription: 'Gants nitrile.', benefits: [], isFeatured: false, sortOrder: 3 },
  { id: 104, supplierId: 11, supplierName: 'Atlas Dental Supply', externalProductId: 'ATL-104', name: 'Ciment verre ionomère', sku: 'CVI-09', dentalCategory: 'Restauration', dentalSpecialty: 'Omnipratique', unit: 'kit', price: 520, availability: 'ON_REQUEST', shortDescription: 'CVI.', longDescription: 'CVI.', benefits: [], isFeatured: false, sortOrder: 4 },
];
const catalogMeta = { categories: ['Consommables', 'Restauration', 'Endodontie'], specialties: ['Omnipratique', 'Endodontie'], availability: ['AVAILABLE', 'ON_REQUEST', 'DISCONTINUED'] };
const clinicProfile = { nom_praticien: 'Dr Baseline', nom_cabinet: 'Cabinet Atlas', selected_theme: 'elite', selected_template: 'swiss', font_fr: 'inter', primary_color: '#003380', secondary_color: '#1e40af', accent_color: '#60a5fa', show_patient_badges: true, performance_mode: false, clinical_tips_enabled: true, header_lines_fr: ['Dr Baseline'], specialty_ids: [] };
const json = (body, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) });
const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64');
const token = `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ sub: user.id, exp: Math.floor(Date.now() / 1000) + 7200 })}.mob5g`;

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try { const response = await fetch(url); if (response.ok) return; } catch {}
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

async function installDesktopMocks(page, orderPosts) {
  await page.route(/https?:\/\/[^/]+:8005\/.*/, async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname.replace(/\/$/, '');
    if (pathname === '/health') return route.fulfill(json({ status: 'ok' }));
    if (pathname === '/api/auth/me') return route.fulfill(json(user));
    if (pathname === '/api/clinics/init-status') return route.fulfill(json({ is_initialized: true }));
    if (pathname === '/api/clinics/me') return route.fulfill(json(clinicProfile));
    if (pathname === '/api/partner-orders/meta') return route.fulfill(json({ supportedStatuses: ['DRAFT'], strategyPresets }));
    if (pathname === '/api/partner-catalog/meta') return route.fulfill(json(catalogMeta));
    if (pathname === '/api/partner-catalog/suppliers') return route.fulfill(json(suppliers));
    if (pathname === '/api/partner-catalog/products') return route.fulfill(json(products));
    if (pathname === '/api/partner-orders' && request.method() === 'POST') {
      orderPosts.push(request.postDataJSON());
      return route.fulfill(json({ orderNumber: 'CMD-MOB5G-CERT', strategyLabel: strategyPresets[0].label }, 201));
    }
    return route.fulfill(json({}));
  });
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], { cwd: FRONTEND_DIR, env: { ...process.env, BROWSER: 'none' }, stdio: ['ignore', 'pipe', 'pipe'] });
let serverLog = '';
server.stdout.on('data', (chunk) => { serverLog += chunk.toString(); });
server.stderr.on('data', (chunk) => { serverLog += chunk.toString(); });
let browser;
const mobile = [];
let desktop = null;

try {
  await waitForServer(BASE_URL);
  browser = await chromium.launch({ headless: true });

  for (const viewport of mobileViewports) {
    const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1, reducedMotion: 'reduce', locale: 'fr-FR' });
    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });

    const response = await page.goto(`${BASE_URL}/mobile/demo?demo=1&tab=marketplace`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.locator('[data-mobile-marketplace]').waitFor({ state: 'visible', timeout: 30000 });
    await page.getByRole('searchbox', { name: 'Rechercher par nom ou SKU' }).waitFor({ state: 'visible' });
    const metrics = await page.evaluate(() => {
      const doc = document.documentElement;
      const body = document.body;
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      const search = document.querySelector('#mobile-marketplace-search');
      const firstProduct = document.querySelector('[data-mobile-marketplace-product]');
      return {
        innerWidth: innerWidth,
        scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
        horizontalOverflow: Math.max(doc.scrollWidth, body.scrollWidth) > innerWidth + 1,
        navButtons: nav?.querySelectorAll(':scope > div > button, :scope > div > div > button').length ?? 0,
        navHeight: nav ? Math.round(nav.getBoundingClientRect().height) : null,
        searchInFirstViewport: Boolean(search && search.getBoundingClientRect().top < innerHeight),
        firstProductInFirstViewport: Boolean(firstProduct && firstProduct.getBoundingClientRect().top < innerHeight),
      };
    });

    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-mobile-${viewport.name}.png`), fullPage: false });
    await page.getByRole('button', { name: 'Ajouter une unité de Composite universel nano-hybride' }).click();
    await page.getByRole('button', { name: 'Ouvrir le panier, 1 unité' }).click();
    const dialog = page.locator('[data-mobile-marketplace-checkout]');
    await dialog.waitFor({ state: 'visible' });
    const prefill = {
      fullName: await page.getByLabel('Nom complet').inputValue(),
      clinic: await page.getByLabel('Cabinet').inputValue(),
      email: await page.getByLabel('Email').inputValue(),
      phone: await page.getByLabel('Téléphone').inputValue(),
      city: await page.getByLabel('Ville').inputValue(),
    };
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-mobile-checkout-${viewport.name}.png`), fullPage: false });

    mobile.push({ viewport: viewport.name, httpStatus: response?.status() ?? null, pageErrors, consoleErrors, metrics, prefill });
    await context.close();
  }

  const context = await browser.newContext({ viewport: { width: desktopViewport.width, height: desktopViewport.height }, deviceScaleFactor: 1, reducedMotion: 'reduce', locale: 'fr-FR' });
  await context.addInitScript(({ authToken, baselineUser }) => {
    localStorage.clear();
    sessionStorage.clear();
    localStorage.setItem('token', authToken);
    localStorage.setItem('appMode', 'prod');
    localStorage.setItem('auth-storage', JSON.stringify({ state: { user: baselineUser, isAuthenticated: true }, version: 0 }));
    localStorage.setItem('app_background_animated', 'false');
  }, { authToken: token, baselineUser: user });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const orderPosts = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  await installDesktopMocks(page, orderPosts);
  const response = await page.goto(`${BASE_URL}/approvisionnement`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.locator('[data-marketplace-desktop]').waitFor({ state: 'visible', timeout: 30000 });
  await page.locator('[data-marketplace-product="101"]').waitFor({ state: 'visible', timeout: 30000 });
  await page.screenshot({ path: path.join(OUTPUT_DIR, 'after-desktop-1280x800.png'), fullPage: false });

  const metrics = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    const search = document.querySelector('#marketplace-search');
    const firstProduct = document.querySelector('[data-marketplace-product]');
    return {
      innerWidth,
      scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
      horizontalOverflow: Math.max(doc.scrollWidth, body.scrollWidth) > innerWidth + 1,
      searchInFirstViewport: Boolean(search && search.getBoundingClientRect().top < innerHeight),
      firstProductInFirstViewport: Boolean(firstProduct && firstProduct.getBoundingClientRect().top < innerHeight),
      permanentCheckoutForm: Boolean(document.querySelector('[data-marketplace-checkout]')),
      draftDisclosureVisible: body.innerText.includes('Le fournisseur ne reçoit rien à cette étape.'),
    };
  });

  const urlBefore = page.url();
  await page.getByRole('button', { name: 'Ajouter une unité de Composite universel nano-hybride' }).click();
  await page.getByRole('button', { name: 'Préparer le DRAFT' }).click();
  await page.locator('[data-marketplace-checkout]').waitFor({ state: 'visible' });
  const prefill = {
    fullName: await page.getByLabel('Nom complet').inputValue(),
    clinic: await page.getByLabel('Cabinet').inputValue(),
    email: await page.getByLabel('Email').inputValue(),
  };
  await page.screenshot({ path: path.join(OUTPUT_DIR, 'after-desktop-checkout-1280x800.png'), fullPage: false });
  await page.getByLabel('Téléphone').fill('0600000000');
  await page.getByLabel('Ville').fill('Rabat');
  await page.getByRole('button', { name: 'Enregistrer le brouillon' }).click();
  await page.waitForTimeout(250);
  const posted = orderPosts[0];
  desktop = {
    viewport: desktopViewport.name,
    httpStatus: response?.status() ?? null,
    pageErrors,
    consoleErrors,
    metrics,
    prefill,
    checkout: {
      postCount: orderPosts.length,
      sameUrlAfterSubmit: page.url() === urlBefore,
      productId: posted?.lines?.[0]?.productId ?? null,
      quantity: posted?.lines?.[0]?.quantity ?? null,
      total: posted?.estimatedTotal ?? null,
      customer: posted?.customer ?? null,
    },
  };
  await context.close();
} finally {
  if (browser) await browser.close();
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise((resolve) => setTimeout(resolve, 3000))]).catch(() => {});
  if (server.exitCode === null && !server.killed) server.kill('SIGKILL');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}

const expectedPrefill = { fullName: 'Dr Baseline', clinic: 'Cabinet Atlas', email: 'baseline@digitalcrown.local' };
const mobileInvalid = mobile.filter((item) =>
  item.httpStatus !== 200 || item.pageErrors.length || item.consoleErrors.length || item.metrics.horizontalOverflow ||
  item.metrics.navButtons !== 5 || item.metrics.navHeight !== 76 || !item.metrics.searchInFirstViewport || !item.metrics.firstProductInFirstViewport ||
  item.prefill.fullName !== expectedPrefill.fullName || item.prefill.clinic !== expectedPrefill.clinic || item.prefill.email !== expectedPrefill.email
);
const desktopInvalid = !desktop || desktop.httpStatus !== 200 || desktop.pageErrors.length || desktop.consoleErrors.length || desktop.metrics.horizontalOverflow ||
  !desktop.metrics.searchInFirstViewport || !desktop.metrics.firstProductInFirstViewport || desktop.metrics.permanentCheckoutForm || !desktop.metrics.draftDisclosureVisible ||
  desktop.prefill.fullName !== expectedPrefill.fullName || desktop.prefill.clinic !== expectedPrefill.clinic || desktop.prefill.email !== expectedPrefill.email ||
  desktop.checkout.postCount !== 1 || !desktop.checkout.sameUrlAfterSubmit || String(desktop.checkout.productId) !== '101' || desktop.checkout.quantity !== 1 || desktop.checkout.total !== 390 ||
  desktop.checkout.customer?.fullName !== expectedPrefill.fullName || desktop.checkout.customer?.clinic !== expectedPrefill.clinic || desktop.checkout.customer?.email !== expectedPrefill.email ||
  desktop.checkout.customer?.phone !== '0600000000' || desktop.checkout.customer?.city !== 'Rabat';

const report = {
  chantier: 'Digital Crown Mobile',
  lot: 'MOB-5G Marketplace AFTER',
  productHead: PRODUCT_HEAD,
  baselineBefore: '062eadf1afc6ffc241be8420313e065a35f7d95b',
  beforeArtifactId: 9992935589,
  mobile,
  desktop,
  mobileInvalidCount: mobileInvalid.length,
  desktopInvalid: Boolean(desktopInvalid),
  deployment: 'none',
};
await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
await writeFile(path.join(OUTPUT_DIR, 'metadata.txt'), `product_head=${PRODUCT_HEAD}\nbaseline_before=062eadf1afc6ffc241be8420313e065a35f7d95b\nbefore_artifact=9992935589\ndeployment=none\n`, 'utf8');

if (mobileInvalid.length || desktopInvalid) {
  console.error(JSON.stringify({ mobileInvalid, desktop }, null, 2));
  process.exitCode = 1;
} else {
  console.log(JSON.stringify(report, null, 2));
}
