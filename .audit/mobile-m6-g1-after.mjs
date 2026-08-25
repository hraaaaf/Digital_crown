import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-g1-after-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];

const snapshot = {
  generated_at: '2026-08-25T13:00:00Z',
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
      { date: '2026-08-19', amount: 2100 }, { date: '2026-08-20', amount: 1800 },
      { date: '2026-08-21', amount: 2400 }, { date: '2026-08-22', amount: 1950 },
      { date: '2026-08-23', amount: 900 }, { date: '2026-08-24', amount: 1450 },
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

const server = await createServer({ server: { host: '127.0.0.1', port: 4193, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

const surfaceSelectors = {
  onboarding: '[data-dc-mobile-shell] [style*="var(--glass-bg)"]',
  dashboard: '[data-mobile-bottom-nav]',
  context: '[data-m4d-context] .bg-card-bg',
};

async function capture(view, viewport, targetTab = null) {
  const context = await browser.newContext({ viewport, screen: viewport, deviceScaleFactor: 1, hasTouch: true, isMobile: true, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (!path.startsWith('/api/')) return route.continue();
    if (path === '/api/mobile/snapshot') return route.fulfill(json(snapshot));
    if (path === '/api/mobile/patients') return route.fulfill(json({ data: [] }));
    if (path === '/api/lab-jobs/' || path === '/api/lab-jobs') return route.fulfill(json([]));
    if (path === '/api/mobile/resource-context') return route.fulfill(json(appointmentPayload));
    if (path === '/api/mobile/refresh-token') return route.fulfill(json({}, 401));
    return route.fulfill(json({}));
  });

  await page.goto(`http://127.0.0.1:4193/mobile-m6-g1-after.html?view=${view}`, { waitUntil: 'networkidle' });
  if (view === 'onboarding') await page.getByRole('heading', { name: 'Compagnon Mobile' }).waitFor({ state: 'visible', timeout: 10000 });
  if (view === 'dashboard') {
    await page.getByText('BENNANI Sara', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
    if (targetTab === 'finance') {
      await page.getByRole('button', { name: /Finance/i }).click();
      await page.waitForTimeout(450);
    }
  }
  if (view === 'context') await page.getByRole('heading', { name: 'Rendez-vous', exact: true }).waitFor({ state: 'visible', timeout: 10000 });

  const selector = surfaceSelectors[view];
  await page.locator(selector).first().waitFor({ state: 'visible', timeout: 5000 });
  const metrics = await page.evaluate(({ view, targetTab, selector }) => {
    const root = document.documentElement;
    const shell = document.querySelector('[data-dc-mobile-shell], [data-mobile-context], [data-m4a-context], [data-m4b-context], [data-m4c-context], [data-m4d-context]');
    const surface = document.querySelector(selector);
    if (!(shell instanceof HTMLElement) || !(surface instanceof HTMLElement)) throw new Error('M6-G1 AFTER shell/surface missing');
    const pseudo = getComputedStyle(shell, '::before');
    const surfaceStyle = getComputedStyle(surface);
    const result = {
      view,
      targetTab,
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      motifMarkerPresent: pseudo.getPropertyValue('--dc-clinical-motif-ready').trim() === '1',
      motifBackgroundImage: pseudo.backgroundImage,
      motifOpacity: pseudo.opacity,
      glassBackdrop: surfaceStyle.backdropFilter || surfaceStyle.webkitBackdropFilter,
      glassBackground: surfaceStyle.backgroundColor,
      nav: null,
    };

    if (view === 'dashboard') {
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      if (!(nav instanceof HTMLElement)) throw new Error('M6-G1 nav missing');
      const buttons = [...nav.querySelectorAll('button')];
      const current = nav.querySelector('button[aria-current="page"]');
      const pills = [...nav.querySelectorAll('[data-mobile-nav-active-pill]')];
      const pill = pills[0];
      const pillRect = pill instanceof HTMLElement ? pill.getBoundingClientRect() : null;
      const currentRect = current instanceof HTMLElement ? current.getBoundingClientRect() : null;
      result.nav = {
        height: nav.getBoundingClientRect().height,
        minButtonHeight: Math.min(...buttons.map(button => button.getBoundingClientRect().height)),
        activePillCount: pills.length,
        activePillInCurrent: current instanceof HTMLElement && pill instanceof HTMLElement && current.contains(pill),
        ariaCurrentLabel: current instanceof HTMLElement ? current.innerText.replace(/\s+/g, ' ').trim() : null,
        pillX: pillRect?.x ?? null,
        currentX: currentRect?.x ?? null,
      };
    }
    return result;
  }, { view, targetTab, selector });

  let highContrast = null;
  if (view === 'dashboard' && targetTab === 'agenda' && viewport.width === 390) {
    highContrast = await page.evaluate(() => {
      document.documentElement.dataset.theme = 'high-contrast';
      const shell = document.querySelector('[data-dc-mobile-shell]');
      const nav = document.querySelector('[data-mobile-bottom-nav]');
      if (!(shell instanceof HTMLElement) || !(nav instanceof HTMLElement)) throw new Error('High contrast probe missing');
      const pseudo = getComputedStyle(shell, '::before');
      const navStyle = getComputedStyle(nav);
      return {
        motifDisplay: pseudo.display,
        motifBackgroundImage: pseudo.backgroundImage,
        navBackdrop: navStyle.backdropFilter || navStyle.webkitBackdropFilter,
        navBoxShadow: navStyle.boxShadow,
      };
    });
    await page.evaluate(() => { document.documentElement.dataset.theme = ''; });
  }

  const suffix = view === 'dashboard' ? `-${targetTab}` : '';
  const name = `${view}${suffix}-${viewport.width}x${viewport.height}`;
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
  const record = { name, view, targetTab, ...viewport, metrics, highContrast, errors };
  captures.push(record);
  await fs.writeFile(`${output}/${name}.json`, JSON.stringify(record, null, 2));
  await context.close();
}

try {
  await capture('onboarding', { width: 390, height: 844 });
  await capture('dashboard', { width: 390, height: 844 }, 'agenda');
  await capture('dashboard', { width: 390, height: 844 }, 'finance');
  await capture('dashboard', { width: 768, height: 1024 }, 'agenda');
  await capture('dashboard', { width: 768, height: 1024 }, 'finance');
  await capture('context', { width: 390, height: 844 });
  await capture('context', { width: 768, height: 1024 });

  const dashboard = captures.filter(item => item.view === 'dashboard');
  const pair390 = dashboard.filter(item => item.width === 390);
  const pair768 = dashboard.filter(item => item.width === 768);
  const moved = pair => pair.length === 2 && Math.abs((pair[0].metrics.nav?.pillX ?? 0) - (pair[1].metrics.nav?.pillX ?? 0)) >= 30;
  const hc = captures.find(item => item.view === 'dashboard' && item.width === 390 && item.targetTab === 'agenda')?.highContrast;

  const report = {
    productHead,
    count: captures.length,
    captures,
    motifEverywhere: captures.every(item => item.metrics.motifMarkerPresent && item.metrics.motifBackgroundImage !== 'none'),
    activePillExact: dashboard.every(item => item.metrics.nav?.activePillCount === 1 && item.metrics.nav?.activePillInCurrent),
    ariaCurrentExact: dashboard.every(item => (item.metrics.nav?.ariaCurrentLabel || '').toLowerCase().includes(item.targetTab === 'agenda' ? 'agenda' : 'finance')),
    minButtonHeight: Math.min(...dashboard.map(item => item.metrics.nav?.minButtonHeight ?? 0)),
    pillMoves390: moved(pair390),
    pillMoves768: moved(pair768),
    highContrastSafe: hc?.motifDisplay === 'none' && hc?.navBackdrop === 'none' && hc?.navBoxShadow === 'none',
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (
    report.count !== 7
    || !report.motifEverywhere
    || !report.activePillExact
    || !report.ariaCurrentExact
    || report.minButtonHeight < 48
    || !report.pillMoves390
    || !report.pillMoves768
    || !report.highContrastSafe
    || !report.noHorizontalOverflow
    || !report.noUnexpectedRuntimeErrors
  ) throw new Error('M6-G1 AFTER evidence gate failed');
} finally {
  await browser.close();
  await server.close();
}
