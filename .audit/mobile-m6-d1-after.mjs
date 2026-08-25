import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-d1-after-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];
const server = await createServer({ server: { host: '127.0.0.1', port: 4199, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

const initialAlerts = [
  { id: 71, patient_id: 12, patient_name: 'Patient Test', type: 'OVERDUE_PAYMENT', title: 'Paiement à surveiller', message: 'Une action administrative est recommandée.', priority: 1, created_at: '2026-08-25T18:00:00' },
  { id: 72, patient_id: null, patient_name: null, type: 'STOCK_GANTS', title: 'Stock à anticiper', message: 'Le seuil de vigilance du cabinet est atteint.', priority: 2, created_at: '2026-08-25T17:30:00' },
];

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function capture(width, height) {
  const context = await browser.newContext({ viewport: { width, height }, screen: { width, height }, deviceScaleFactor: 2, hasTouch: true, isMobile: true, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  const mutations = [];
  let serverAlerts = initialAlerts.map(alert => ({ ...alert }));
  let getCount = 0;
  let staleOpenRequestSeen = false;
  let releaseStaleGet;
  const staleGate = new Promise(resolve => { releaseStaleGet = resolve; });

  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });

  await page.route('**/api/mobile/notifications**', async route => {
    const request = route.request();
    const url = new URL(request.url());

    if (request.method() === 'GET' && url.pathname === '/api/mobile/notifications') {
      getCount += 1;
      if (getCount === 2) {
        const staleSnapshot = initialAlerts.map(alert => ({ ...alert }));
        staleOpenRequestSeen = true;
        await staleGate;
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ total: staleSnapshot.length, alerts: staleSnapshot }) });
        return;
      }
      const snapshot = serverAlerts.map(alert => ({ ...alert }));
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ total: snapshot.length, alerts: snapshot }) });
      return;
    }

    const mutationMatch = url.pathname.match(/^\/api\/mobile\/notifications\/(\d+)\/(read|snooze)$/);
    if (request.method() === 'PATCH' && mutationMatch) {
      const id = Number(mutationMatch[1]);
      const action = mutationMatch[2];
      mutations.push(url.pathname);
      serverAlerts = serverAlerts.filter(alert => alert.id !== id);
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok', action, snoozed_until: action === 'snooze' ? '2026-08-26T20:20:00' : null }) });
      return;
    }

    await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'Audit route not mocked' }) });
  });

  await page.goto('http://127.0.0.1:4199/mobile-m6-d1-after.html', { waitUntil: 'networkidle' });
  await page.getByText('Agenda du jour', { exact: true }).waitFor({ state: 'visible' });
  const bell = page.getByRole('button', { name: /^Notifications/i });
  await bell.waitFor({ state: 'visible' });
  await page.getByText('2 RDV aujourd\'hui', { exact: true }).waitFor({ state: 'visible' });

  const bellBox = await bell.boundingBox();
  await bell.click();
  const dialog = page.getByRole('dialog', { name: 'Notifications' });
  await dialog.waitFor({ state: 'visible' });
  await page.getByText('2 non lues', { exact: true }).waitFor({ state: 'visible' });
  const closeBox = await page.getByRole('button', { name: 'Fermer', exact: true }).boundingBox();
  const read = page.getByRole('button', { name: 'Lu', exact: true }).first();
  const snooze = page.getByRole('button', { name: '+ 24 h', exact: true }).first();
  const readBox = await read.boundingBox();
  const snoozeBox = await snooze.boundingBox();
  const rootMetrics = await page.evaluate(() => ({ hasHorizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1 }));

  await page.screenshot({ path: `${output}/dashboard-notifications-after-${width}x${height}.png`, fullPage: false, animations: 'disabled' });

  await read.click();
  for (let i = 0; i < 20 && !mutations.some(path => path.endsWith('/71/read')); i += 1) await delay(50);
  await delay(150);
  const afterReadText = await page.locator('body').innerText();
  await page.screenshot({ path: `${output}/dashboard-notifications-after-read-${width}x${height}.png`, fullPage: false, animations: 'disabled' });
  await fs.writeFile(`${output}/debug-after-read-${width}x${height}.json`, JSON.stringify({ productHead, mutations, serverAlerts, getCount, staleOpenRequestSeen, errors, afterReadText }, null, 2));
  await page.getByText('1 non lue', { exact: true }).waitFor({ state: 'visible', timeout: 5000 });

  releaseStaleGet();
  await delay(250);
  await page.getByText('1 non lue', { exact: true }).waitFor({ state: 'visible', timeout: 2000 });

  await page.getByRole('button', { name: '+ 24 h', exact: true }).click();
  await page.getByText('Rien à traiter', { exact: true }).waitFor({ state: 'visible', timeout: 5000 });

  const boxes = [bellBox, closeBox, readBox, snoozeBox];
  const minTargets48 = boxes.every(box => box && box.width >= 48 && box.height >= 48);
  const readMutation = mutations.some(path => path.endsWith('/71/read'));
  const snoozeMutation = mutations.some(path => path.endsWith('/72/snooze'));
  const serverTruthEmpty = serverAlerts.length === 0;
  captures.push({ width, height, minTargets48, readMutation, snoozeMutation, staleOpenRequestSeen, serverTruthEmpty, hasHorizontalOverflow: rootMetrics.hasHorizontalOverflow, errors });
  await context.close();
}

try {
  await capture(390, 844);
  await capture(430, 932);
  await capture(768, 1024);
  const report = {
    productHead,
    count: captures.length,
    captures,
    allTargetsAtLeast48: captures.every(item => item.minTargets48),
    allReadMutationsObserved: captures.every(item => item.readMutation),
    allSnoozeMutationsObserved: captures.every(item => item.snoozeMutation),
    staleRaceExercisedEverywhere: captures.every(item => item.staleOpenRequestSeen),
    serverTruthEmptyAfterActions: captures.every(item => item.serverTruthEmpty),
    noHorizontalOverflow: captures.every(item => !item.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (
    report.count !== 3 ||
    !report.allTargetsAtLeast48 ||
    !report.allReadMutationsObserved ||
    !report.allSnoozeMutationsObserved ||
    !report.staleRaceExercisedEverywhere ||
    !report.serverTruthEmptyAfterActions ||
    !report.noHorizontalOverflow ||
    !report.noUnexpectedRuntimeErrors
  ) {
    throw new Error('M6-D1 AFTER evidence gate failed');
  }
} finally {
  await browser.close();
  await server.close();
}
