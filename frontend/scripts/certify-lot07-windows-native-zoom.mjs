// LOT07/07-C — native Windows Chromium browser zoom (NOT CSS zoom or CDP scale).
// Synthetic fixture only: real Cabinet/T2 HTTP authority remains in Linux FUE-G.
// A zoom shortcut that does not change real browser CSS viewport MUST fail closed.
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';

assert.equal(process.platform, 'win32', 'This lab requires a real Windows runner');
const sha = process.env.EVALUATED_SHA;
assert.match(sha || '', /^[0-9a-f]{40}$/);
const dest = path.resolve('../artifacts/lot07-07c-windows-native-zoom');
await fs.mkdir(dest, { recursive: true });
const report = {
  sha, platform: process.platform, browser: 'Chromium headed',
  surface: 'SYNTHETIC_COMMAND_IN_REAL_MAINLAYOUT', realCabinetBackend: false,
  nativeBrowserZoom200: false, cssZoomUsed: false, pass: false, failure: null,
};
let browser;
let activePage;
try {
  browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  activePage = page;
  const external = [];
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.hostname === '127.0.0.1' || url.hostname === 'localhost' || url.protocol === 'data:') {
      return route.continue();
    }
    external.push(url.hostname);
    return route.abort();
  });
  await page.goto('http://127.0.0.1:5173/07c-windows-native-zoom.html', { waitUntil: 'domcontentloaded' });
  await page.getByTestId('command-cabinet-readonly').waitFor({ state: 'visible', timeout: 40000 });
  assert.equal(await page.locator('[data-ux1-c-crownbot-floating]').count(), 0,
    'Real MainLayout must suppress floating CrownBot on Command route');
  assert.equal((await page.getByTestId('command-count').innerText()).trim(), '2');
  assert.ok((await page.locator('tbody').innerText()).includes('09:15'));
  const measure = () => page.evaluate(() => ({
    devicePixelRatio: window.devicePixelRatio,
    innerWidth: window.innerWidth,
    outerWidth: window.outerWidth,
    cssBodyZoom: document.body.style.zoom,
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  assert.ok(new URL(page.url()).pathname === '/07c-windows-native-zoom.html',
    'Synthetic Windows fixture URL must remain stable before native zoom');
  const before = await measure();
  await page.screenshot({ path: path.join(dest, 'windows-owner-100-before.png'), fullPage: true });
  // Attempt the actual Chrome browser-zoom keyboard accelerator. Never use
  // CSS zoom, Emulation.setPageScaleFactor or devicePixelRatio override.
  await page.bringToFront();
  for (let i = 0; i < 5; i++) {
    await page.keyboard.press('Control+Shift+Equal');
    await page.waitForTimeout(180);
  }
  let after = await measure();
  // Some Windows Chrome builds do not consume CDP keyboard accelerators.
  // Fallback to Windows' own SendKeys to the foreground headed browser.
  if (after.devicePixelRatio < before.devicePixelRatio * 1.95) {
    for (let i = 0; i < 5; i++) {
      execFileSync('powershell.exe', ['-NoProfile', '-Command',
        'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("^{ADD}")'],
        { stdio: 'pipe', timeout: 15000 });
      await page.waitForTimeout(180);
    }
    after = await measure();
    report.keyboardMethod = 'Windows SendKeys native accelerator fallback';
  } else {
    report.keyboardMethod = 'Chromium Control+Shift+Equal';
  }
  report.before = before;
  report.after = after;
  report.documentUrlAfterZoom = new URL(page.url()).pathname;
  assert.equal(report.documentUrlAfterZoom, '/07c-windows-native-zoom.html',
    'Browser reload must retain synthetic HTML entry rather than redirect to Cabinet login');
  report.externalHostsBlocked = [...new Set(external)];
  await page.screenshot({ path: path.join(dest, 'windows-owner-native-zoom-attempt.png'), fullPage: true });
  assert.equal(after.cssBodyZoom, '', 'No CSS zoom permitted');
  assert.ok(after.devicePixelRatio / before.devicePixelRatio >= 1.95 &&
            after.devicePixelRatio / before.devicePixelRatio <= 2.06,
    'Browser zoom must be genuinely 200%; measured DPR '+before.devicePixelRatio+' -> '+after.devicePixelRatio);
  assert.ok(after.innerWidth < before.innerWidth * 0.60,
    'Actual browser CSS viewport should contract at native 200% zoom');
  assert.ok(after.scrollWidth <= after.clientWidth + 2,
    'Native Windows zoom must not overflow outer document horizontally');
  assert.equal(await page.locator('[data-ux1-c-crownbot-floating]').count(), 0);
  assert.equal((await page.getByTestId('command-count').innerText()).trim(), '2');
  const compact = page.getByRole('region', { name: 'Agenda compact' });
  assert.ok(await compact.isVisible(), 'Read-only agenda remains visible at 200% browser zoom');
  report.nativeBrowserZoom200 = true;
  report.pass = true;
} catch (e) {
  report.failure = String(e?.stack || e).slice(0,2200);
  if (activePage) {
    try { await activePage.screenshot({ path: path.join(dest, 'windows-failure-viewport.png'), fullPage: true }); }
    catch { /* report.json still preserves the failure */ }
  }
} finally {
  await browser?.close();
  await fs.writeFile(path.join(dest, 'report.json'), JSON.stringify(report, null, 2));
}
console.log('LOT07_07C_WINDOWS_NATIVE_BROWSER_ZOOM', JSON.stringify(report));
if (!report.pass) process.exitCode = 1;
