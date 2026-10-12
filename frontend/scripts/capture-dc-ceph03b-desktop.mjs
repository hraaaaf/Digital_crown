import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.CEPH03B_PHASE;
if (!['BEFORE', 'AFTER'].includes(phase)) throw Error('CEPH03B_PHASE must be BEFORE or AFTER');
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const root = process.cwd();
const out = path.join(root, 'dc-ceph03b-' + phase.toLowerCase() + '-desktop-artifacts');
const port = 5196;
const baseUrl = 'http://127.0.0.1:' + port;
const modes = [
  { name: 'com', landmark: 'Po', construction: 'com-frankfort', start: [30,40], dest: [65,75] },
  { name: 'all', landmark: 'N', construction: 'ricketts-n-pog', start: [130,70], dest: [145,90] },
];
const viewports = [{ name: '1280x900', width: 1280, height: 900 }, { name: '1600x1000', width: 1600, height: 1000 }];
const htmlName = 'ceph03b-desktop-visual.html';
const html = '<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body style="margin:0"><div id="root"></div><script type="module" src="/src/features/ortho/CephaloTracingLayer.visualFixture.tsx"></script></body></html>';
const blockedExternalRequests = [];
const captures = [];

await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
await writeFile(path.join(root, htmlName), html, 'utf8');

const viteBin = path.join(root, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host','127.0.0.1','--port',String(port)], { cwd: root, env: { ...process.env, BROWSER: 'none' }, stdio: ['ignore','pipe','pipe'] });
let log = '';
server.stdout.on('data', chunk => { log += chunk; });
server.stderr.on('data', chunk => { log += chunk; });

const assert = (actual, expected, description) => {
  if (actual !== expected) throw Error(description + ' expected=' + expected + ' observed=' + actual);
};
const approximate = (a,b,description) => {
  if (!Number.isFinite(a) || Math.abs(a-b) > 0.3) throw Error(description + ' expected=' + b + ' observed=' + a);
};
async function waitForServer() {
  for (let i = 0; i < 150; i++) {
    try {
      const response = await fetch(baseUrl + '/' + htmlName);
      if (response.ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve,200));
  }
  throw Error('Vite did not start');
}

async function browserCapture(viewport, mode) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, reducedMotion: 'reduce', locale: 'fr-FR' });
  const page = await context.newPage();
  const errors = [], consoleErrors = [], shots = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  await page.route('**/*', async route => {
    const u = new URL(route.request().url());
    if (u.hostname === '127.0.0.1' && u.port === String(port)) return route.continue();
    if (u.hostname === 'fonts.googleapis.com') return route.fulfill({ status: 200, contentType: 'text/css', body: '' });
    blockedExternalRequests.push({ viewport: viewport.name, mode: mode.name, url: route.request().url() });
    return route.abort('blockedbyclient');
  });
  const prefix = phase.toLowerCase() + '-' + mode.name + '-' + viewport.name + '-';
  const take = async state => {
    const name = prefix + state + '.png';
    await page.screenshot({ path: path.join(out, name), fullPage: false });
    shots.push(name);
  };
  const overlay = () => page.locator('[data-r19-construction="' + mode.construction + '"],[data-r18-construction="' + mode.construction + '"]');
  const coordinates = async () => overlay().evaluate(el => ({
    x: Number(el.getAttribute('x1')),
    y: Number(el.getAttribute('y1')),
  }));
  const screenCoords = async (svgX,svgY) => page.locator('[data-ceph03b-drag-handle="' + mode.landmark + '"]').evaluate((el,point) => {
    const svg = el.ownerSVGElement;
    if (!svg || !svg.getScreenCTM()) throw Error('SVG screen matrix unavailable');
    const p = svg.createSVGPoint();
    p.x = point.x; p.y = point.y;
    const result = p.matrixTransform(svg.getScreenCTM());
    return { x: result.x, y: result.y };
  }, { x: svgX, y: svgY });
  const commitCount = () => page.locator('[data-commit-count]').getAttribute('data-commit-count');
  try {
    const response = await page.goto(baseUrl + '/' + htmlName + '?mode=' + mode.name, { waitUntil: 'domcontentloaded', timeout: 30000 });
    assert(response?.status(), 200, 'Fixture response');
    await page.locator('[data-ceph03b-browser-fixture="' + mode.name + '"]').waitFor({ state: 'visible', timeout: 20000 });
    await overlay().waitFor({ state: 'attached', timeout: 20000 });
    await page.locator('[data-ceph03b-drag-handle="' + mode.landmark + '"]').waitFor({ state: 'attached' });
    const initial = await coordinates();
    approximate(initial.x,mode.start[0],'Initial overlay X');
    approximate(initial.y,mode.start[1],'Initial overlay Y');
    await take('initial');

    const initialScreen = await screenCoords(...mode.start);
    const finalScreen = await screenCoords(...mode.dest);
    await page.mouse.move(initialScreen.x, initialScreen.y);
    await page.mouse.down();
    await page.mouse.move(finalScreen.x, finalScreen.y, { steps: 5 });
    await page.waitForFunction(({ landmark, x, y }) => {
      const handle = document.querySelector('[data-ceph03b-drag-handle="' + landmark + '"]');
      const ring = handle?.querySelector('circle');
      if (!ring) return false;
      return Math.abs(Number(ring.getAttribute('cx')) - x) < 0.3
        && Math.abs(Number(ring.getAttribute('cy')) - y) < 0.3;
    }, { landmark: mode.landmark, x: mode.dest[0], y: mode.dest[1] }, { timeout: 5000 });
    const during = await coordinates();
    const expectLive = phase === 'AFTER' ? mode.dest : mode.start;
    approximate(during.x,expectLive[0],'During overlay X');
    approximate(during.y,expectLive[1],'During overlay Y');
    assert(await commitCount(), '0', 'No save during transient drag');
    await take('drag');

    await page.locator('[data-ceph03b-drag-handle="' + mode.landmark + '"]').dispatchEvent('pointercancel', { pointerId: 1, bubbles: true });
    await page.mouse.up();
    await page.waitForTimeout(70);
    const cancelled = await coordinates();
    approximate(cancelled.x,mode.start[0],'Canceled overlay X');
    approximate(cancelled.y,mode.start[1],'Canceled overlay Y');
    assert(await commitCount(), '0', 'No save after cancellation');
    await take('cancel');

    await page.mouse.move(initialScreen.x, initialScreen.y);
    await page.mouse.down();
    await page.mouse.move(finalScreen.x, finalScreen.y, { steps: 5 });
    await page.mouse.up();
    await page.waitForFunction(() => document.querySelector('[data-commit-count]')?.getAttribute('data-commit-count') === '1', null, { timeout: 5000 });
    const committed = await coordinates();
    approximate(committed.x,mode.dest[0],'Committed overlay X');
    approximate(committed.y,mode.dest[1],'Committed overlay Y');
    await take('commit');

    await page.locator('[data-toggle-plans]').click();
    assert(await overlay().count(), 0, 'Plan overlay is hidden when plans off');
    await page.locator('[data-toggle-plans]').click();
    assert(await overlay().count(), 1, 'Plan overlay restored');
    const afterToggle = await coordinates();
    approximate(afterToggle.x,mode.dest[0],'Overlay X after layer toggle');
    const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    assert(horizontalOverflow, false, 'No horizontal overflow');
    assert(errors.length, 0, 'No page errors');
    assert(consoleErrors.length, 0, 'No console errors');
    return { viewport: viewport.name, mode: mode.name, valid: true, initial, during, cancelled, committed, shots, errors, consoleErrors, horizontalOverflow };
  } catch (error) {
    await take('failure').catch(() => {});
    return { viewport: viewport.name, mode: mode.name, valid: false, shots, errors: [...errors, String(error)], consoleErrors };
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}
try {
  await waitForServer();
  for (const viewport of viewports) for (const mode of modes) captures.push(await browserCapture(viewport,mode));
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server,'exit'),new Promise(resolve => setTimeout(resolve,3000))]).catch(() => {});
  await writeFile(path.join(out, 'vite.log'), log, 'utf8');
}
const report = {
  lot: 'DC-CEPH03B-DESKTOP-PAIRED-OVERLAY-DRAG',
  phase, productHead,
  viewports: viewports.map(v => v.name),
  modes: modes.map(m => m.name),
  fixture: 'synthetic-only/no-patient-data',
  expectedTransientOverlay: phase === 'AFTER' ? 'FOLLOWS_POINTER' : 'BASELINE_STALE',
  captures, blockedExternalRequests,
  invalidCount: captures.filter(item => !item.valid).length,
};
await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2),'utf8');
console.log(JSON.stringify(report,null,2));
if (report.invalidCount || blockedExternalRequests.length) process.exitCode = 1;
