import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const phase = process.argv[2];
const commitSha = process.argv[3];
if (!['before', 'after'].includes(phase) || !commitSha) throw new Error('usage: node mobile-m6-i-capture.mjs <before|after> <sha>');

const PORT = phase === 'before' ? 4181 : 4182;
const baseUrl = `http://127.0.0.1:${PORT}`;
const outDir = path.resolve('mobile-m6-i-artifacts');
await mkdir(outDir, { recursive: true });

const isWindows = process.platform === 'win32';
const vite = spawn(isWindows ? 'npx.cmd' : 'npx', ['vite', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], {
  stdio: ['ignore', 'pipe', 'pipe'],
  env: { ...process.env, BROWSER: 'none' },
  detached: !isWindows,
});
let viteLog = '';
vite.stdout.on('data', chunk => { viteLog += chunk.toString(); });
vite.stderr.on('data', chunk => { viteLog += chunk.toString(); });

async function stopVite() {
  if (vite.exitCode !== null) return;
  if (isWindows) {
    await new Promise(resolve => {
      const killer = spawn('taskkill', ['/pid', String(vite.pid), '/t', '/f'], { stdio: 'ignore' });
      killer.once('exit', resolve);
      killer.once('error', resolve);
    });
  } else if (vite.pid) {
    try { process.kill(-vite.pid, 'SIGTERM'); } catch {}
    await Promise.race([
      new Promise(resolve => vite.once('exit', resolve)),
      new Promise(resolve => setTimeout(resolve, 2000)),
    ]);
    if (vite.exitCode === null) {
      try { process.kill(-vite.pid, 'SIGKILL'); } catch {}
    }
  }
  vite.stdout?.destroy();
  vite.stderr?.destroy();
  vite.unref();
}

async function waitForVite() {
  let lastError;
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      const res = await fetch(`${baseUrl}/mobile-m6-i-visual.html`);
      if (res.ok) return;
    } catch (error) { lastError = error; }
    await new Promise(resolve => setTimeout(resolve, 125));
  }
  throw new Error(`Vite readiness failed: ${lastError || viteLog}`);
}

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];

const captures = [];
let browser;
try {
  await waitForVite();
  browser = await chromium.launch({ headless: true });
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(`pageerror:${error.message}`));
    page.on('console', msg => { if (msg.type() === 'error') errors.push(`console:${msg.text()}`); });
    await page.goto(`${baseUrl}/mobile-m6-i-visual.html`, { waitUntil: 'networkidle' });
    await page.getByText('Sécurité', { exact: true }).waitFor();

    const metrics = await page.evaluate(() => {
      const biometric = document.querySelector('[data-m6i-biometric]');
      const activate = document.querySelector('[data-m6i-activate]');
      const rect = activate?.getBoundingClientRect();
      return {
        hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        biometricVisible: !!biometric,
        glassReflectionCount: document.querySelectorAll('[data-m6i-glass-reflection]').length,
        activationHeight: rect?.height ?? 0,
      };
    });

    const baseName = `${phase}-security-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outDir, baseName), fullPage: false });
    captures.push({ phase, kind: 'security', viewport, file: baseName, errors, metrics });

    // BEFORE already has the required same-viewport security capture. For AFTER,
    // take a second viewport capture centered on the new card using a fresh DOM
    // lookup inside the page. This avoids holding a Locator across React remounts.
    if (phase === 'after') {
      const centered = await page.evaluate(() => {
        const element = document.querySelector('[data-m6i-biometric]');
        if (!element) return false;
        element.scrollIntoView({ block: 'center', inline: 'nearest' });
        return true;
      });
      if (centered) {
        await page.waitForFunction(() => {
          const element = document.querySelector('[data-m6i-biometric]');
          if (!element) return false;
          const rect = element.getBoundingClientRect();
          return rect.bottom > 0 && rect.top < window.innerHeight;
        });
        const contextName = `${phase}-context-${viewport.width}x${viewport.height}.png`;
        await page.screenshot({ path: path.join(outDir, contextName), fullPage: false });
        captures.push({ phase, kind: 'context', viewport, file: contextName, errors: [...errors], metrics });
      }
    }
    await context.close();
  }

  if (phase === 'after') {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(`pageerror:${error.message}`));
      page.on('console', msg => { if (msg.type() === 'error') errors.push(`console:${msg.text()}`); });
      await page.goto(`${baseUrl}/mobile-m6-i-lock.html`, { waitUntil: 'networkidle' });
      await page.getByText('Déverrouiller Digital Crown', { exact: true }).waitFor();
      const metrics = await page.evaluate(() => {
        const unlock = [...document.querySelectorAll('button')].find(button => button.textContent?.includes('Déverrouiller'));
        const rect = unlock?.getBoundingClientRect();
        return {
          hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          protectedContentVisible: !!document.querySelector('[data-protected-secret]'),
          unlockHeight: rect?.height ?? 0,
        };
      });
      const file = `after-lock-${viewport.width}x${viewport.height}.png`;
      await page.screenshot({ path: path.join(outDir, file), fullPage: false });
      captures.push({ phase, kind: 'lock', viewport, file, errors, metrics });
      await context.close();
    }
  }
} finally {
  if (browser) await browser.close();
  await stopVite();
}

const reportPath = path.join(outDir, 'report.json');
let report = { baseHead: null, productHead: null, captures: [] };
try { report = JSON.parse(await readFile(reportPath, 'utf8')); } catch {}
if (phase === 'before') report.baseHead = commitSha;
else report.productHead = commitSha;
report.captures = [...(report.captures || []).filter(item => item.phase !== phase), ...captures];
await writeFile(reportPath, JSON.stringify(report, null, 2));
