import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m4-final-before-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];
const network = [];
const server = await createServer({ server: { host: '127.0.0.1', port: 4188, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

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
    notes: 'RDV M4 final',
  },
};

function json(body, status = 200) {
  return {
    status,
    contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': '*' },
    body: JSON.stringify(body),
  };
}

async function setup(viewport, mode) {
  const context = await browser.newContext({ viewport, screen: viewport, deviceScaleFactor: 1, hasTouch: true, isMobile: viewport.width <= 768, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  await page.route('**/*', async route => {
    const req = route.request();
    const url = new URL(req.url());
    if (!url.pathname.startsWith('/api/')) return route.continue();
    network.push(`${mode} ${req.method()} ${url.pathname}`);
    if (url.pathname === '/api/mobile/resource-context') {
      if (mode === 'offline') return route.abort('connectionrefused');
      if (mode === 'deleted') return route.fulfill(json({ detail: 'Rendez-vous supprimé ou indisponible.' }, 404));
      return route.fulfill(json(appointmentPayload));
    }
    if (url.pathname === '/api/mobile/refresh-token') return route.fulfill(json({}, 401));
    return route.fulfill(json({}));
  });
  return { context, page, errors };
}

async function metrics(page) {
  return page.evaluate(() => {
    const root = document.documentElement;
    const bodyText = document.body.innerText.replace(/\s+/g, ' ').trim();
    const buttons = [...document.querySelectorAll('button')].filter(el => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    }).map(el => {
      const rect = el.getBoundingClientRect();
      return { text: (el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 100), width: Math.round(rect.width), height: Math.round(rect.height) };
    });
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      bodyText,
      rawNetworkErrorVisible: /failed to fetch|networkerror|err_connection/i.test(bodyText),
      locationProbe: document.querySelector('[data-location-probe]')?.textContent || '',
      buttonsBelow44: buttons.filter(button => button.width < 44 || button.height < 44),
    };
  });
}

async function capture(page, errors, mode, viewport, suffix = '') {
  const measured = await metrics(page);
  const name = `${mode}${suffix}-${viewport.width}x${viewport.height}`;
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
  const record = { name, mode, ...viewport, metrics: measured, errors: [...errors] };
  captures.push(record);
  await fs.writeFile(`${output}/${name}.json`, JSON.stringify(record, null, 2));
  return record;
}

async function openError(mode, viewport) {
  const { context, page, errors } = await setup(viewport, mode);
  await page.goto(`http://127.0.0.1:4188/mobile-m4-final-before.html?mode=${mode}`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Contexte indisponible', exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const record = await capture(page, errors, mode, viewport);
  await context.close();
  return record;
}

async function openReadyReturn(viewport) {
  const { context, page, errors } = await setup(viewport, 'ready');
  await page.goto('http://127.0.0.1:4188/mobile-m4-final-before.html?mode=ready', { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Rendez-vous', exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const before = await capture(page, errors, 'ready', viewport);
  await page.getByRole('button', { name: 'Retour', exact: true }).first().click();
  await page.locator('[data-location-probe]').filter({ hasText: '/mobile/dashboard?tab=agenda' }).waitFor({ state: 'attached', timeout: 5000 });
  const afterMetrics = await metrics(page);
  before.returnRoute = afterMetrics.locationProbe;
  await fs.writeFile(`${output}/${before.name}.json`, JSON.stringify(before, null, 2));
  await context.close();
  return before;
}

try {
  const mobile = { width: 390, height: 844 };
  const tablet = { width: 768, height: 1024 };
  const unpaired = await openError('unpaired', mobile);
  const revoked = await openError('revoked', mobile);
  const deleted = await openError('deleted', mobile);
  const offlineMobile = await openError('offline', mobile);
  const offlineTablet = await openError('offline', tablet);
  const ready = await openReadyReturn(mobile);

  const report = {
    productHead,
    count: captures.length,
    captures,
    unpairedExplicit: /aucun contexte/i.test(unpaired.metrics.bodyText),
    revocationExplicit: /permission agenda révoquée/i.test(revoked.metrics.bodyText),
    deletedExplicit: /rendez-vous supprimé ou indisponible/i.test(deleted.metrics.bodyText),
    backendOfflineStateVisible: /contexte indisponible/i.test(offlineMobile.metrics.bodyText) && /contexte indisponible/i.test(offlineTablet.metrics.bodyText),
    backendOfflineRawTechnical: offlineMobile.metrics.rawNetworkErrorVisible || offlineTablet.metrics.rawNetworkErrorVisible,
    returnToAgenda: ready.returnRoute === '/mobile/dashboard?tab=agenda',
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.filter(item => !['deleted', 'offline'].includes(item.mode)).every(item => item.errors.length === 0),
    network,
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.count !== 6 || !report.unpairedExplicit || !report.revocationExplicit || !report.deletedExplicit || !report.backendOfflineStateVisible || !report.returnToAgenda || !report.noHorizontalOverflow || !report.noUnexpectedRuntimeErrors) {
    throw new Error('M4 final BEFORE evidence gate failed.');
  }
} finally {
  await browser.close();
  await server.close();
}
