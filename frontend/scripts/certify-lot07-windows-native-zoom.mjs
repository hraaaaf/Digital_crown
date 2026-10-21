// LOT07/07-C — native Windows Chromium browser zoom (NOT CSS zoom or CDP scale).
// Synthetic fixture only: real Cabinet/T2 HTTP authority remains in Linux FUE-G.
// A zoom shortcut that does not change real browser CSS viewport MUST fail closed.
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { inspectPngVisibleInk } from './lot07-07c-png-visual-proof.mjs';

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
  // Windows hosted runners do not guarantee a hardware-backed compositor.
  // Keep real headed Chromium/native shortcut, but force software rasterization
  // so screenshot pixels are observable independently of an unstable GPU.
  browser = await chromium.launch({ headless: false, args: ['--disable-gpu'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  activePage = page;
  report.navigations = [];
  report.pageErrors = [];
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) report.navigations.push(frame.url().slice(0,160));
  });
  page.on('pageerror', error => report.pageErrors.push(String(error).slice(0,300)));
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
  // Native Ctrl-plus can trigger a Chromium document navigation. A single
  // page.evaluate at that instant throws "Execution context was destroyed".
  // Retry only that transient navigation; all visual/security assertions remain.
  async function measure() {
    let lastError;
    for (let attempt = 0; attempt < 35; attempt++) {
      try {
        const result = await page.evaluate(() => ({
          devicePixelRatio: window.devicePixelRatio,
          innerWidth: window.innerWidth,
          outerWidth: window.outerWidth,
          cssBodyZoom: document.body.style.zoom,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }));
        if (result.innerWidth > 0 && result.clientWidth > 0) return result;
      } catch (err) {
        lastError = err;
        if (!/Execution context was destroyed|Cannot find context|navigation/i.test(String(err))) throw err;
      }
      await page.waitForTimeout(350);
    }
    throw new Error('Windows browser measurement never stabilized after native zoom: '+String(lastError));
  }
  assert.ok(new URL(page.url()).pathname === '/07c-windows-native-zoom.html',
    'Synthetic Windows fixture URL must remain stable before native zoom');
  const before = await measure();
  const beforePng = await page.screenshot({ path: path.join(dest, 'windows-owner-100-before.png'), fullPage: true });
  report.visualBefore = inspectPngVisibleInk(beforePng);
  assert.ok(report.visualBefore.inkPixels > 120, 'BEFORE must contain visible rendered text');
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
  await page.waitForLoadState('domcontentloaded', { timeout: 15000 });
  await page.getByTestId('command-cabinet-readonly').waitFor({ state: 'visible', timeout: 20000 });
  report.documentUrlAfterZoom = new URL(page.url()).pathname;
  assert.equal(report.documentUrlAfterZoom, '/07c-windows-native-zoom.html',
    'Browser reload must retain synthetic HTML entry rather than redirect to Cabinet login');
  report.externalHostsBlocked = [...new Set(external)];
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
  // Screen pixels, not DOM visibility, must show the actual cockpit. The first
  // Windows run #39501431409 was SUCCESS while its AFTER PNG was pure white.
  // Never accept that false-green visual evidence again.
  await page.bringToFront();
  await page.waitForTimeout(1500);
  let visualAfter;
  for (let attempt=1;attempt<=3;attempt++) {
    await page.evaluate(() => new Promise(resolve =>
      requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const png=await page.screenshot({
      path: path.join(dest, 'windows-owner-native-zoom-attempt.png'), fullPage: true,
    });
    visualAfter=inspectPngVisibleInk(png);
    report.visualAfter=visualAfter;
    report.screenshotAttempts=attempt;
    if(visualAfter.inkPixels > 120)break;
    await page.waitForTimeout(1250);
  }
  assert.ok(visualAfter.inkPixels > 120,
    'Windows 200% AFTER screenshot has no real rendered text: white frame is NOT an approval');
  assert.equal(await page.getByTestId('command-count').innerText(), '2',
    'AFTER must retain live mounted synthetic Cabinet count');

  // 07-C visual REVIEW B: at 200% the first viewport shows only the cockpit
  // heading. Prove the real appointments table is reachable with ordinary
  // scrolling and legible in the actual viewport, not just mounted in the DOM.
  const firstAppointment = page.locator('tbody tr').first().getByText('09:15', { exact: true });
  await firstAppointment.scrollIntoViewIfNeeded({ timeout: 20000 });
  await page.waitForTimeout(450);
  const appointmentBox = await firstAppointment.boundingBox();
  assert.ok(appointmentBox, 'Native 200% first appointment must be rendered');
  assert.ok(appointmentBox.x >= -2 && appointmentBox.y >= 0 &&
            appointmentBox.x + appointmentBox.width <= 720 &&
            appointmentBox.y + appointmentBox.height <= 450,
    'Native 200% first appointment must be visibly reachable by scroll: ' +
    JSON.stringify(appointmentBox));
  const rowScreenshot = await page.screenshot({
    path: path.join(dest, 'windows-owner-native-zoom-scrolled-agenda.png'),
    fullPage: false,
  });
  report.visualScrolledAgenda = inspectPngVisibleInk(rowScreenshot);
  assert.ok(report.visualScrolledAgenda.inkPixels > 120,
    'Native 200% scrolled appointment screenshot must show visible text');
  report.appointmentVisibleAtNativeZoom = true;
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
