import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-g1-before-artifacts';
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

function json(body, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

const server = await createServer({ server: { host: '127.0.0.1', port: 4192, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

async function capture(viewport, targetTab) {
  const context = await browser.newContext({ viewport, screen: viewport, deviceScaleFactor: 1, hasTouch: true, isMobile: true, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith('/api/')) return route.continue();
    if (url.pathname === '/api/mobile/snapshot') return route.fulfill(json(snapshot));
    if (url.pathname === '/api/mobile/patients') return route.fulfill(json({ data: [] }));
    if (url.pathname === '/api/lab-jobs/' || url.pathname === '/api/lab-jobs') return route.fulfill(json([]));
    if (url.pathname === '/api/mobile/refresh-token') return route.fulfill(json({}, 401));
    return route.fulfill(json({}));
  });

  await page.goto('http://127.0.0.1:4192/mobile-m6-g1-before.html', { waitUntil: 'networkidle' });
  await page.getByText('BENNANI Sara', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  if (targetTab === 'finance') {
    await page.getByRole('button', { name: /Finance/i }).click();
    await page.waitForTimeout(350);
  }

  const metrics = await page.evaluate((targetTab) => {
    const root = document.documentElement;
    const shell = document.querySelector('[data-dc-mobile-shell]');
    const nav = document.querySelector('nav');
    if (!(shell instanceof HTMLElement) || !(nav instanceof HTMLElement)) throw new Error('M6-G1 BEFORE shell/nav missing');
    const buttons = [...nav.querySelectorAll('button')].map(button => {
      const rect = button.getBoundingClientRect();
      const style = getComputedStyle(button);
      return {
        label: button.innerText.replace(/\s+/g, ' ').trim(),
        width: rect.width,
        height: rect.height,
        backgroundColor: style.backgroundColor,
        color: style.color,
        transform: style.transform,
      };
    });
    const pseudo = getComputedStyle(shell, '::before');
    return {
      targetTab,
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      navHeight: nav.getBoundingClientRect().height,
      buttons,
      minButtonHeight: Math.min(...buttons.map(item => item.height)),
      activePillPresent: !!nav.querySelector('[data-mobile-nav-active-pill]'),
      motifMarkerPresent: pseudo.getPropertyValue('--dc-clinical-motif-ready').trim() === '1',
      pseudoBackgroundImage: pseudo.backgroundImage,
      shellBackgroundImage: getComputedStyle(shell).backgroundImage,
    };
  }, targetTab);

  const name = `dashboard-${targetTab}-${viewport.width}x${viewport.height}`;
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
  const record = { name, ...viewport, targetTab, metrics, errors };
  captures.push(record);
  await fs.writeFile(`${output}/${name}.json`, JSON.stringify(record, null, 2));
  await context.close();
}

try {
  for (const viewport of [{ width: 390, height: 844 }, { width: 768, height: 1024 }]) {
    await capture(viewport, 'agenda');
    await capture(viewport, 'finance');
  }
  const report = {
    productHead,
    count: captures.length,
    captures,
    noActivePill: captures.every(item => !item.metrics.activePillPresent),
    motifNotYetImplemented: captures.every(item => !item.metrics.motifMarkerPresent),
    minButtonHeight: Math.min(...captures.map(item => item.metrics.minButtonHeight)),
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.count !== 4 || !report.noActivePill || !report.motifNotYetImplemented || !report.noHorizontalOverflow || !report.noUnexpectedRuntimeErrors) {
    throw new Error('M6-G1 BEFORE evidence gate failed');
  }
} finally {
  await browser.close();
  await server.close();
}
