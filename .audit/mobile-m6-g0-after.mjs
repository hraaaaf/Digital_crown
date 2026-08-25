import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-g0-after-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];

const snapshot = {
  generated_at: '2026-08-25T10:00:00Z',
  role: 'DENTISTE',
  is_superadmin: false,
  appointments: [
    { id: 77, patient_id: 12, time: '10:30', patient_name: 'BENNANI Sara', phone: '0612345678', motif: 'Contrôle implant 36', status: 'PLANIFIE', duration_minutes: 60 },
    { id: 78, patient_id: 13, time: '14:00', patient_name: 'EL MANSOURI Yasmine', phone: '0622334455', motif: 'Empreinte', status: 'TERMINE', duration_minutes: 45 },
  ],
  finance: {
    today_revenue: 1250,
    month_revenue: 18400,
    month_variation: 8.2,
    appointments_count: 2,
    weekly_revenue: [
      { date: '2026-08-19', amount: 2100 },
      { date: '2026-08-20', amount: 1800 },
      { date: '2026-08-21', amount: 2400 },
      { date: '2026-08-22', amount: 1950 },
      { date: '2026-08-23', amount: 900 },
      { date: '2026-08-24', amount: 1450 },
      { date: '2026-08-25', amount: 1250 },
    ],
    total_patients: 287,
    total_debt: 3400,
  },
  debtors: [],
};

const appointmentPayload = {
  type: 'appointment',
  label: 'Rendez-vous',
  appointment: {
    patient_name: 'BENNANI Sara',
    datetime_start: '2026-08-25T10:30:00',
    duration_minutes: 60,
    motif: 'Contrôle implant 36',
    status: 'CONFIRMÉ',
    scheduling_type: 'EXACT_TIME',
    notes: 'Contrôle post-opératoire',
  },
};

function json(body, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

const server = await createServer({ server: { host: '127.0.0.1', port: 4191, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

const surfaceSelectors = {
  onboarding: '[data-dc-mobile-shell] [style*="var(--glass-bg)"]',
  dashboard: '[data-dc-mobile-shell] .bg-glass-bg',
  context: '[data-m4d-context] .bg-card-bg',
};

function isTranslucentColor(value) {
  return /rgba\([^)]*,\s*0?\.\d+\)/i.test(value) || /\/\s*0?\.\d+\s*\)?$/i.test(value);
}

async function capture(view, viewport) {
  const context = await browser.newContext({ viewport, screen: viewport, deviceScaleFactor: 1, hasTouch: true, isMobile: true, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  await page.route('**/*', async route => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname;
    if (!path.startsWith('/api/')) return route.continue();
    if (path === '/api/mobile/snapshot') return route.fulfill(json(snapshot));
    if (path === '/api/mobile/patients') return route.fulfill(json({ data: [] }));
    if (path === '/api/lab-jobs/' || path === '/api/lab-jobs') return route.fulfill(json([]));
    if (path === '/api/mobile/resource-context') return route.fulfill(json(appointmentPayload));
    if (path === '/api/mobile/refresh-token') return route.fulfill(json({}, 401));
    return route.fulfill(json({}));
  });

  await page.goto(`http://127.0.0.1:4191/mobile-m6-g0-after.html?view=${view}`, { waitUntil: 'networkidle' });
  if (view === 'onboarding') await page.getByRole('heading', { name: 'Compagnon Mobile' }).waitFor({ state: 'visible', timeout: 10000 });
  if (view === 'dashboard') await page.getByText('BENNANI Sara', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  if (view === 'context') await page.getByRole('heading', { name: 'Rendez-vous', exact: true }).waitFor({ state: 'visible', timeout: 10000 });

  const selector = surfaceSelectors[view];
  await page.locator(selector).first().waitFor({ state: 'visible', timeout: 5000 });
  const metrics = await page.evaluate(({ selector }) => {
    const root = document.documentElement;
    const surface = document.querySelector(selector);
    if (!(surface instanceof HTMLElement)) throw new Error(`Glass probe missing: ${selector}`);
    const style = getComputedStyle(surface);
    const shell = surface.closest('[data-dc-mobile-shell], [data-mobile-context], [data-m4a-context], [data-m4b-context], [data-m4c-context], [data-m4d-context]');
    const shellStyle = shell instanceof HTMLElement ? getComputedStyle(shell) : null;
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      backdropFilter: style.backdropFilter || style.webkitBackdropFilter,
      boxShadow: style.boxShadow,
      shellBackgroundImage: shellStyle?.backgroundImage || 'none',
      bodyText: document.body.innerText.replace(/\s+/g, ' ').trim().slice(0, 1000),
    };
  }, { selector });
  metrics.translucent = isTranslucentColor(metrics.backgroundColor);
  metrics.glassActive = /blur\(/i.test(metrics.backdropFilter) && metrics.backdropFilter !== 'none';
  metrics.depthActive = metrics.boxShadow !== 'none';
  metrics.ambientBackground = metrics.shellBackgroundImage !== 'none';

  let highContrast = null;
  if (view === 'dashboard' && viewport.width === 390) {
    highContrast = await page.evaluate(({ selector }) => {
      document.documentElement.dataset.theme = 'high-contrast';
      const surface = document.querySelector(selector);
      const shell = document.querySelector('[data-dc-mobile-shell]');
      if (!(surface instanceof HTMLElement) || !(shell instanceof HTMLElement)) throw new Error('High contrast probe missing');
      const style = getComputedStyle(surface);
      const shellStyle = getComputedStyle(shell);
      return {
        backdropFilter: style.backdropFilter || style.webkitBackdropFilter,
        backgroundColor: style.backgroundColor,
        borderColor: style.borderColor,
        boxShadow: style.boxShadow,
        shellBackgroundImage: shellStyle.backgroundImage,
      };
    }, { selector });
  }

  const name = `${view}-${viewport.width}x${viewport.height}`;
  if (highContrast) await page.evaluate(() => { document.documentElement.dataset.theme = ''; });
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
  const record = { name, view, ...viewport, metrics, highContrast, errors };
  captures.push(record);
  await fs.writeFile(`${output}/${name}.json`, JSON.stringify(record, null, 2));
  await context.close();
}

try {
  await capture('onboarding', { width: 390, height: 844 });
  await capture('dashboard', { width: 390, height: 844 });
  await capture('dashboard', { width: 768, height: 1024 });
  await capture('context', { width: 390, height: 844 });
  await capture('context', { width: 768, height: 1024 });

  const dashboard390 = captures.find(item => item.view === 'dashboard' && item.width === 390);
  const report = {
    productHead,
    count: captures.length,
    captures,
    allGlassActive: captures.every(item => item.metrics.glassActive),
    allTranslucent: captures.every(item => item.metrics.translucent),
    allDepthActive: captures.every(item => item.metrics.depthActive),
    allAmbientBackground: captures.every(item => item.metrics.ambientBackground),
    highContrastOpaque: dashboard390?.highContrast?.backdropFilter === 'none'
      && dashboard390?.highContrast?.boxShadow === 'none'
      && dashboard390?.highContrast?.shellBackgroundImage === 'none',
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (
    report.count !== 5
    || !report.allGlassActive
    || !report.allTranslucent
    || !report.allDepthActive
    || !report.allAmbientBackground
    || !report.highContrastOpaque
    || !report.noHorizontalOverflow
    || !report.noUnexpectedRuntimeErrors
  ) throw new Error('M6-G0 AFTER glass evidence gate failed');
} finally {
  await browser.close();
  await server.close();
}
