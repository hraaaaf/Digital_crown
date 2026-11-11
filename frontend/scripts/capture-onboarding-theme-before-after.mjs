// True BEFORE/AFTER from the same real OnboardingScanner component.
// GitHub-hosted, ephemeral, synthetic, network-blocked. No API/patient/credential IO.
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const frontend = path.resolve(here, '..');
const repoRoot = path.resolve(frontend, '..');
const relComponent = 'frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx';
const componentPath = path.join(repoRoot, relComponent);
const original = await fs.readFile(componentPath, 'utf8');
const baselineSha = '324afd13487acf7ff29223f077451927b54b8178';
const before = execFileSync('git', ['show', baselineSha + ':' + relComponent], {
  cwd: repoRoot, encoding: 'utf8', maxBuffer: 2 * 1024 * 1024,
});
const out = path.resolve(repoRoot, 'artifacts/theme-onboarding-before-after');
const htmlPath = path.join(frontend, 'dc-onboarding-visual-cert.html');
const entryPath = path.join(frontend, 'src', 'dc-onboarding-visual-cert.tsx');
const themes = ['elite', 'emerald', 'dark', 'high-contrast'];
const viewports = [{width: 390, height: 844}, {width: 768, height: 1024}, {width: 1280, height: 900}];
const records = [];
const pageErrors = [];
let browser;
let server;

async function capture(phase) {
  server = await createServer({
    root: frontend,
    server: { host: '127.0.0.1', port: 5199, strictPort: true },
    clearScreen: false,
    optimizeDeps: { include: ['html5-qrcode'] },
  });
  await server.listen();
  browser = await chromium.launch({ headless: true });
  try {
    for (const theme of themes) {
      for (const viewport of viewports) {
        const context = await browser.newContext({
          viewport, reducedMotion: 'reduce', serviceWorkers: 'block',
          locale: 'fr-FR', colorScheme: theme === 'dark' ? 'dark' : 'light',
        });
        await context.route('**/*', route => {
          const u = new URL(route.request().url());
          if (u.hostname !== '127.0.0.1' || u.port !== '5199') return route.abort();
          return route.continue();
        });
        const page = await context.newPage();
        page.on('pageerror', error => pageErrors.push({
          phase, theme, width: viewport.width, message: String(error.message).slice(0, 240),
        }));
        await page.goto('http://127.0.0.1:5199/dc-onboarding-visual-cert.html?theme=' + encodeURIComponent(theme), {
          waitUntil: 'domcontentloaded', timeout: 45000,
        });
        const shell = page.locator('[data-dc-mobile-shell]').first();
        await shell.waitFor({ state: 'visible', timeout: 30000 });
        await page.waitForTimeout(400); // allow React effect and CSS to settle
        const result = await shell.evaluate(element => {
          const root = document.documentElement;
          const computed = getComputedStyle(root);
          const probe = document.createElement('div');
          probe.style.backgroundColor = 'var(--bg-medical-pearl)';
          probe.style.color = 'var(--text-main)';
          document.body.appendChild(probe);
          const expectedBg = getComputedStyle(probe).backgroundColor;
          const expectedText = getComputedStyle(probe).color;
          probe.remove();
          return {
            rootTheme: root.dataset.theme || 'elite',
            bodyTheme: document.body.dataset.theme || 'elite',
            actualBackground: getComputedStyle(element).backgroundColor,
            actualText: getComputedStyle(element).color,
            expectedBackground: expectedBg,
            expectedText,
            width: window.innerWidth,
            overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          };
        });
        const filename = phase + '-' + theme + '-' + viewport.width + 'x' + viewport.height + '.png';
        await page.screenshot({ path: path.join(out, filename), animations: 'disabled', fullPage: false });
        const png = await fs.readFile(path.join(out, filename));
        if (png.toString('hex', 0, 8) !== '89504e470d0a1a0a' ||
            png.readUInt32BE(16) !== viewport.width ||
            png.readUInt32BE(20) !== viewport.height) {
          throw new Error('Invalid PNG viewport: ' + filename);
        }
        const record = {
          phase, theme, viewport, screenshot: filename, pngSha256: crypto.createHash('sha256').update(png).digest('hex'),
          ...result,
        };
        records.push(record);
        if (phase === 'after') {
          if (result.rootTheme !== theme || result.bodyTheme !== theme) {
            throw new Error('Selected runtime theme was lost: ' + JSON.stringify(record));
          }
          if (result.actualBackground !== result.expectedBackground ||
              result.actualText !== result.expectedText || result.overflow) {
            throw new Error('After semantic colors/viewport mismatch: ' + JSON.stringify(record));
          }
        }
        if (phase === 'before' && theme !== 'elite' && result.rootTheme === theme) {
          throw new Error('Historical BEFORE no longer reproduces the reset: ' + JSON.stringify(record));
        }
        await context.close();
      }
    }
  } finally {
    await browser?.close();
    browser = undefined;
    await server?.close();
    server = undefined;
  }
}

const harnessHtml = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body><div id="root"></div><script>const t=new URLSearchParams(location.search).get('theme')||'elite';const id=t==='elite'?'':t;document.documentElement.dataset.theme=id;document.body.dataset.theme=id;</script><script type="module" src="/src/dc-onboarding-visual-cert.tsx"></script></body></html>`;
const harnessTsx = [
  "import React from 'react';",
  "import {createRoot} from 'react-dom/client';",
  "import {MemoryRouter} from 'react-router-dom';",
  "import {OnboardingScanner} from './features/mobile/Onboarding/OnboardingScanner';",
  "import './index.css';",
  "import './features/mobile/mobileRuntimeTheme.css';",
  "createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/mobile/onboarding']}><OnboardingScanner /></MemoryRouter>);",
].join('\n');

try {
  await fs.mkdir(out, { recursive: true });
  await fs.writeFile(htmlPath, harnessHtml);
  await fs.writeFile(entryPath, harnessTsx);
  await fs.writeFile(componentPath, before);
  await capture('before');
  await fs.writeFile(componentPath, original);
  await capture('after');
  if (records.length !== themes.length * viewports.length * 2 || pageErrors.length) {
    throw new Error('Incomplete captures or JS exceptions ' + JSON.stringify(pageErrors));
  }
  await fs.writeFile(path.join(out, 'evidence.json'), JSON.stringify({
    baselineSha, candidateSha: execFileSync('git', ['rev-parse','HEAD'], {cwd:repoRoot,encoding:'utf8'}).trim(),
    evidence: records, pageErrors, patientData: 'NONE', deployment: 'NONE',
  }, null, 2));
  console.log('ONBOARDING_THEME_REAL_BEFORE_AFTER_PASS records=' + records.length);
} finally {
  await browser?.close().catch(() => undefined);
  await server?.close().catch(() => undefined);
  await fs.writeFile(componentPath, original);
  await fs.rm(htmlPath, {force:true});
  await fs.rm(entryPath, {force:true});
}
