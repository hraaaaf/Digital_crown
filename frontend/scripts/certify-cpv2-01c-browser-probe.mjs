// CPV2-01C: browser FUE-I only. Uses REAL hook/storage, MOCKED theme HTTP.
// No real cabinet, pairing QR, live patient data or physical PWA validation.
import { spawn } from 'node:child_process';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const root = process.cwd();
const origin = 'http://127.0.0.1:5173';
const destination = path.resolve(root, '../artifacts/cpv2-01c-browser-probe');
const SHA = process.env.EVALUATED_SHA || 'unknown';
const A = { id: 'aaaaaaaaaaaaaaaa', token: 'synthetic-token_A', selected_theme: 'rose', primary_color: '#ba2277', font_fr: 'playfair' };
const B = { id: 'bbbbbbbbbbbbbbbb', token: 'synthetic-token_B', selected_theme: 'graphite', primary_color: '#225588', font_fr: 'inter' };
const viewports = [[390, 844], [430, 932], [768, 1024], [1280, 800]];
const report = { sha: SHA, source: 'real browser + production MobileStorage/useMobileRuntimeTheme', mockedThemeHttp: true,
  twoRealCabinetServers: false, physicalPwa: false, assertions: [], images: [], pass: false };
await fs.mkdir(destination, { recursive: true });
const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '5173', '--strictPort'],
  { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
let serverLogs = '';
server.stdout.on('data', d => { serverLogs += d.toString(); });
server.stderr.on('data', d => { serverLogs += d.toString(); });
let browser;

async function ready() {
  for (let n = 0; n < 90; n++) {
    try {
      const response = await fetch(origin + '/cpv2-01c-browser-probe.html');
      if (response.ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('Vite browser probe server unavailable: ' + serverLogs.slice(-800));
}

async function observe(page, expected) {
  await page.waitForFunction(arg =>
    document.documentElement.dataset.theme === arg.theme &&
    document.body.dataset.theme === arg.theme &&
    document.documentElement.style.getPropertyValue('--primary').trim() === arg.primary &&
    document.documentElement.style.getPropertyValue('--app-font-family').includes(arg.font),
    { theme: expected.selected_theme, primary: expected.primary_color, font: expected.font_fr === 'playfair' ? 'Playfair' : 'Inter' },
    { timeout: 12000 });
  const data = await page.evaluate(() => {
    const element = document.querySelector('[data-test-theme-swatch]');
    return { theme: document.documentElement.dataset.theme,
      primary: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(),
      swatch: getComputedStyle(element).backgroundColor,
      font: getComputedStyle(document.querySelector('[data-cpv2-browser-probe]')).fontFamily };
  });
  assert.equal(data.primary, expected.primary_color);
  assert.ok(data.swatch && data.font);
  return data;
}

async function call(page, method, ...args) {
  return page.evaluate(async x => window.__cpv2Lab[x.method](...x.args), { method, args });
}

try {
  await ready();
  browser = await chromium.launch({ headless: true });
  for (const [width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    let holdA = false;
    let releaseA = null;
    let offlineMode = false;
    let delayedASeen = false;
    let holdB = false;
    let releaseB = null;
    let delayedBSeen = false;
    await page.route('**/api/clinics/mobile-theme', async route => {
      const method = route.request().method();
      const headers = { 'access-control-allow-origin': '*',
        'access-control-allow-headers': 'authorization, content-type',
        'access-control-allow-methods': 'GET,OPTIONS',
        'content-type': 'application/json' };
      if (method === 'OPTIONS') return route.fulfill({ status: 204, headers });
      const auth = route.request().headers()['authorization'] || '';
      if (holdA && auth.includes(A.token)) {
        holdA = false;
        delayedASeen = true;
        await new Promise(resolve => { releaseA = resolve; });
      }
      if (holdB && auth.includes(B.token)) {
        holdB = false;
        delayedBSeen = true;
        await new Promise(resolve => { releaseB = resolve; });
      }
      if (offlineMode) return route.abort('internetdisconnected');
      const clinic = auth.includes(A.token) ? A : auth.includes(B.token) ? B : null;
      if (!clinic) return route.fulfill({ status: 401, headers, body: '{"detail":"unknown synthetic token"}' });
      return route.fulfill({ status: 200, headers, body: JSON.stringify({
        selected_theme: clinic.selected_theme,
        primary_color: clinic.primary_color,
        font_fr: clinic.font_fr,
      }) });
    });
    await page.goto(origin + '/cpv2-01c-browser-probe.html', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-cpv2-browser-probe]').waitFor();
    await page.waitForFunction(() => Boolean(window.__cpv2Lab));

    // Exact same IndexedDB/browser profile and real storage for both paired scopes.
    await call(page, 'pair', A.id, A.token);
    await observe(page, A);
    await call(page, 'saveSnapshot', 'patient-synthetic-A');
    assert.deepEqual(await call(page, 'readSnapshot'), { marker: 'patient-synthetic-A' });
    await call(page, 'pair', B.id, B.token);
    await observe(page, B);
    assert.equal(await call(page, 'readSnapshot'), null, 'A snapshot leaked into B');
    await call(page, 'saveSnapshot', 'patient-synthetic-B');
    await call(page, 'pair', A.id, A.token);
    await observe(page, A);
    assert.equal(await call(page, 'readSnapshot'), null, 'B snapshot leaked back into A');

    // A delayed theme response cannot overwrite B without triggering React cleanup.
    // The active credentials are changed silently on the SAME mounted hook.
    holdA = true;
    await call(page, 'refresh');
    for (let n = 0; n < 100 && !delayedASeen; n++) {
      await new Promise(resolve => setTimeout(resolve, 30));
    }
    assert.ok(delayedASeen && releaseA, 'A request was not held for stale-response challenge');
    await call(page, 'switchSilently', B.id, B.token);
    await call(page, 'neutralize');
    releaseA();
    await page.waitForTimeout(300);
    const stale = await page.evaluate(() => ({
      theme: document.documentElement.dataset.theme,
      primary: document.documentElement.style.getPropertyValue('--primary').trim(),
    }));
    assert.deepEqual(stale, { theme: '', primary: '' }, 'Stale tenant A theme painted B after silent switch');
    await call(page, 'refresh');
    await observe(page, B);

    // Simulate failed theme HTTP while the JavaScript runtime remains loaded.
    // A previously cached A theme may only be used when identity A is active.
    offlineMode = true;
    await call(page, 'switchSilently', A.id, A.token);
    await call(page, 'neutralize');
    await call(page, 'refresh');
    await observe(page, A);
    await call(page, 'switchSilently', B.id, B.token);
    await call(page, 'neutralize');
    await call(page, 'refresh');
    await observe(page, B);
    assert.equal(await call(page, 'readSnapshot'), null);
    // Reconnect with a deliberately held B response: assert the old
    // offline palette cannot be mistaken for a completed network refresh.
    offlineMode = false;
    holdB = true;
    await call(page, 'refresh');
    for (let n = 0; n < 100 && !delayedBSeen; n++) {
      await new Promise(resolve => setTimeout(resolve, 30));
    }
    assert.ok(delayedBSeen && releaseB, 'Reconnected B request was not held');
    const beforeResponse = await page.evaluate(() => ({
      theme: document.documentElement.dataset.theme,
      primary: document.documentElement.style.getPropertyValue('--primary').trim(),
    }));
    assert.deepEqual(beforeResponse, { theme: '', primary: '' },
      'A previous B palette must not mask an unfinished reconnect refresh');
    releaseB();
    await observe(page, B);

    // Viewports and zoom verify this probe only, not the complete patient cockpit.
    const beforeZoom = await page.evaluate(() => ({
      width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth }));
    assert.equal(beforeZoom.width, width);
    assert.ok(beforeZoom.scrollWidth <= width + 2, 'Probe overflow at width ' + width);
    await page.evaluate(() => { document.documentElement.style.zoom = '2'; });
    assert.equal(await page.locator('[data-test-theme-swatch]').isVisible(), true);
    const shot = 'browser-scope-B-' + width + 'x' + height + '.png';
    await page.screenshot({ path: path.join(destination, shot), fullPage: false });
    report.images.push(shot);
    assert.deepEqual(errors, []);
    report.assertions.push({ viewport: width + 'x' + height, pairedTransitions: 'A-B-A', sentinels: 'isolated',
      delayedAResponse: 'ignored', offlineCache: 'per-tenant', zoom200: 'probe visible',
      computedThemeB: B.selected_theme, primaryB: B.primary_color, runtimeErrors: 0 });
    await context.close();
  }
  report.pass = true;
} finally {
  await fs.writeFile(path.join(destination, 'report.json'), JSON.stringify(report, null, 2));
  if (browser) await browser.close();
  server.kill('SIGTERM');
}
if (!report.pass) process.exitCode = 1;
