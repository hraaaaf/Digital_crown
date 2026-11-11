import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'ceph-j1b1-s4-visual-artifacts');
const ENTRY = path.join(FRONTEND_DIR, 'src', 'ceph-j1b1-s4-entry.tsx');
const PAGE_HTML = path.join(FRONTEND_DIR, 'ceph-j1b1-s4.html');
const PORT = 5189;
const BASE_URL = 'http://127.0.0.1:' + PORT;
const themes = ['light', 'dark'];
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '430x932', width: 430, height: 932 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
  { name: '1366x700', width: 1366, height: 700 },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { CephaloWorkspace } from './features/ortho/CephaloWorkspace';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import './index.css';

document.body.dataset.theme = new URLSearchParams(window.location.search).get('theme') === 'dark' ? 'dark' : 'light';
const fixture = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(\`
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600">
    <defs><radialGradient id="g"><stop offset="0" stop-color="#334155"/><stop offset="1" stop-color="#020617"/></radialGradient></defs>
    <rect width="1200" height="1600" fill="url(#g)"/>
    <path d="M470 220 C720 260 820 520 760 760 C710 960 570 1160 420 1340" fill="none" stroke="#94a3b8" stroke-width="18" opacity=".38"/>
    <path d="M390 520 C600 450 790 560 820 760 C760 900 620 970 460 940" fill="none" stroke="#cbd5e1" stroke-width="12" opacity=".28"/>
    <circle cx="680" cy="470" r="105" fill="none" stroke="#e2e8f0" stroke-width="10" opacity=".24"/>
  </svg>\`);

useOrthoStore.setState({
  patientId: 901,
  patientName: 'Patient Démo R1',
  analysisId: 9901,
  imageSrc: fixture,
  imgDim: { w: 1200, h: 1600 },
  local: { landmarks: [], version: 1 },
  anglesData: {
    calibration_status: 'candidate_unverified',
    calibration_candidate: {
      status: 'CANDIDATE_UNVERIFIED',
      detector_method: 'CLASSICAL_RULER_GEOMETRY_V1',
      axis_x_px: 40,
      tick_positions_y_px: [10, 35, 60, 85, 110],
      median_tick_spacing_px: 25,
      mm_per_pixel: null,
      distance_mm: null,
      clinician_validated: false,
    },
  },
  visionMetadata: {},
  isCalibrated: false,
  mmPerPixel: null,
  showCalibration: false,
  calibrationClickPoints: [],
  calibrationDistance: '',
  calibrationStep: 'selecting',
  completedSteps: new Set([1]),
  step: 1,
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/patients/901/cephalo']}>
    <div style={{height:'100vh'}}><CephaloWorkspace patientId={901} patientName="Patient Démo R1" /></div>
  </MemoryRouter>,
);
`;

const htmlSource = '<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>S4 Lexique visuel synthétique</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/ceph-j1b1-s4-entry.tsx"></script></body></html>';

function json(body, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

async function waitForServer(url, timeoutMs = 30_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 300));
  }
  throw new Error('S4_SYNTHETIC_VITE_SERVER_UNAVAILABLE');
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(ENTRY, entrySource, 'utf8');
await writeFile(PAGE_HTML, htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host','127.0.0.1','--port',String(PORT), '--strictPort'], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none', VITE_API_URL: 'http://127.0.0.1:8005' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', data => { serverLog += data.toString(); });
server.stderr.on('data', data => { serverLog += data.toString(); });

const allCaptures = [];
const blockedExternalRequests = [];

async function capture(viewport, attempt, theme) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
    locale: 'fr-FR',
    colorScheme: theme,
  });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const requests = [];
  page.on('pageerror', err => pageErrors.push(err.message));
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
    if (url.hostname === '127.0.0.1' && url.port === '8005') {
      requests.push(request.method() + ' ' + url.pathname + url.search);
      if (request.method() === 'GET' && url.pathname === '/api/patients/901') {
        return route.fulfill(json({ id:901, nom:'Démo', prenom:'R1', age:34, sexe:'M' }));
      }
      return route.fulfill(json({ detail: 'Synthetic S4: endpoint blocked' }, 418));
    }
    if (url.hostname === 'fonts.googleapis.com') {
      return route.fulfill({ status: 200, contentType:'text/css', body:'/* offline synthetic screenshot */' });
    }
    blockedExternalRequests.push({ viewport:viewport.name, url:request.url(), method:request.method() });
    return route.abort('blockedbyclient');
  });

  try {
    const response = await page.goto(BASE_URL + '/ceph-j1b1-s4.html?theme=' + theme, { waitUntil:'domcontentloaded', timeout:30_000 });
    await page.getByRole('heading', { name:'Céphalométrie' }).waitFor({ state:'visible', timeout:30_000 });
    const details = page.locator('[data-cephalo-review-lexicon-details]');
    await details.waitFor({ state:'attached', timeout:30_000 });
    const initialClosed = await details.evaluate(node => !node.open);
    if (!initialClosed) throw new Error('S4_NOT_CLOSED_BY_DEFAULT');
    await details.scrollIntoViewIfNeeded();
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    await page.screenshot({
      path: path.join(OUTPUT_DIR, theme + '-' + 'before-collapsed-' + viewport.name + '.png'),
      fullPage: false,
    });

    await details.locator('summary').click();
    await page.locator('[data-cephalo-review-lexicon]').waitFor({ state:'visible', timeout:15_000 });
    const nDetector = await page.locator('[data-cephalo-review-lexicon] [data-model-channel="true"]').count();
    const nConstruction = await page.locator('[data-cephalo-review-lexicon] [data-model-channel="false"]').count();
    const nCertified = await page.locator('[data-cephalo-review-lexicon] [data-clinical-validated="true"]').count();
    if (nDetector !== 38 || nConstruction !== 2 || nCertified !== 0) {
      throw new Error('S4_FULL_CATALOG_COUNT_OR_CLINICAL_GATE_FAILED: ' + [nDetector,nConstruction,nCertified].join(','));
    }
    const search = page.getByRole('searchbox', { name: /FR, EN, synonyme ou ID/i });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({
      path: path.join(OUTPUT_DIR, theme + '-' + 'after-expanded-' + viewport.name + '.png'),
      fullPage: false,
    });

    await search.fill('Pos');
    const nFiltered = await page.locator('[data-cephalo-review-lexicon] [data-cephalo-lexicon-id]').count();
    const proper = await page.locator('[data-cephalo-lexicon-id="Pog_soft"][data-clinical-validated="false"]').count();
    if (nFiltered !== 1 || proper !== 1) throw new Error('S4_POS_EXACT_ALIAS_OR_CLINICAL_HOLD_FAILED');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({
      path: path.join(OUTPUT_DIR, theme + '-' + 'after-pos-search-' + viewport.name + '.png'),
      fullPage: false,
    });

    // On compact phones, scroll the actual image into the manual-pointing workspace
    // before testing pointer access. Preserve the recorded first-viewport screenshot.
    if (viewport.width <= 430) {
      await page.locator('[data-r20-radiograph-stage]').evaluate(node => node.scrollIntoView({ block: 'center', inline: 'nearest' }));
      await page.screenshot({
        path: path.join(OUTPUT_DIR, theme + '-edit-ready-' + viewport.name + '.png'),
        fullPage: false,
      });
    }
    const metrics = await page.evaluate(() => {
      const doc = document.documentElement;
      const panel = document.querySelector('[data-cephalo-review-lexicon]');
      const panelRect = panel?.getBoundingClientRect();
      const stage = document.querySelector('[data-r20-radiograph-stage]');
      const stageRect = stage?.getBoundingClientRect();
      const drawerRect = document.querySelector('[data-cephalo-review-lexicon-details]')?.getBoundingClientRect();
      const overlapWidth = stageRect && drawerRect ? Math.max(0, Math.min(stageRect.right, drawerRect.right) - Math.max(stageRect.left, drawerRect.left)) : 0;
      const overlapHeight = stageRect && drawerRect ? Math.max(0, Math.min(stageRect.bottom, drawerRect.bottom) - Math.max(stageRect.top, drawerRect.top)) : 0;
      const candidates = stageRect
        ? [0.22,0.48,0.74].flatMap(xFraction => [0.22,0.48,0.74].map(yFraction => ({
          x: stageRect.left + stageRect.width * xFraction,
          y: Math.max(0,stageRect.top) + (Math.min(innerHeight,stageRect.bottom) - Math.max(0,stageRect.top)) * yFraction,
        }))).filter(p => p.x >= 1 && p.x < innerWidth - 1 && p.y >= 1 && p.y < innerHeight - 1)
        : [];
      const visibleStagePoints = candidates.filter(p => {
        const hit = document.elementFromPoint(p.x, p.y);
        return Boolean(hit?.closest('[data-r20-radiograph-stage]') && !hit.closest('[data-cephalo-review-lexicon-details]'));
      });
      const accessibleStagePoint = visibleStagePoints[0] || null;
      return {
        width: innerWidth,
        activeTheme: document.body.dataset.theme,
        backgroundToken: getComputedStyle(document.body).getPropertyValue('--bg-medical-pearl').trim(),
        cardToken: getComputedStyle(document.body).getPropertyValue('--card-bg').trim(),
        textToken: getComputedStyle(document.body).getPropertyValue('--text-main').trim(),
        documentScrollWidth: doc.scrollWidth,
        horizontalDocumentOverflow: doc.scrollWidth > innerWidth + 1,
        panelVisible: Boolean(panelRect && panelRect.width > 10 && panelRect.height > 10),
        radiographStageVisible: Boolean(stageRect && stageRect.width > 50 && stageRect.height > 50 && stageRect.top < innerHeight && stageRect.bottom > 0),
        glossaryRadiographOverlapPx2: overlapWidth * overlapHeight,
        stageHitIsNotGlossary: accessibleStagePoint !== null,
        stageHitInsideStage: accessibleStagePoint !== null,
        accessibleStagePoint,
        accessibleStagePointCount: visibleStagePoints.length,
        radiographUncoveredAboveDrawerPx: stageRect && drawerRect
          ? Math.max(0, Math.min(stageRect.bottom, drawerRect.top, innerHeight) - Math.max(stageRect.top, 0)) : 0,
        panelWithinViewportX: Boolean(panelRect && panelRect.left >= -1 && panelRect.right <= innerWidth + 1),
        clinicalBadgesPresent: document.querySelectorAll('[data-clinical-validated="true"]').length,
      };
    });

    await page.evaluate(() => {
      const stage = document.querySelector('[data-r20-radiograph-stage]');
      (window).__cephS4PointerReached = false;
      stage?.addEventListener('pointerdown', () => { (window).__cephS4PointerReached = true; }, { capture: true, once: true });
    });
    if (metrics.accessibleStagePoint) await page.mouse.click(metrics.accessibleStagePoint.x, metrics.accessibleStagePoint.y);
    const pointerReachedStage = await page.evaluate(() => (window).__cephS4PointerReached === true);
    await search.press('Escape');
    const closedOnEscape = await details.evaluate(node => !node.open);
    const focusReturned = await details.locator('summary').evaluate(node => node === document.activeElement);
    const valid = response?.status() === 200 && initialClosed && nDetector === 38
      && nConstruction === 2 && nCertified === 0 && nFiltered === 1 && proper === 1
      && metrics.activeTheme === theme && metrics.backgroundToken.length > 0
      && metrics.panelVisible && metrics.panelWithinViewportX && metrics.radiographStageVisible
      && metrics.glossaryRadiographOverlapPx2 === 0 && metrics.stageHitIsNotGlossary
      && metrics.stageHitInsideStage
      && (viewport.width > 768 || metrics.radiographUncoveredAboveDrawerPx >= 240)
      && closedOnEscape && focusReturned && pointerReachedStage
      && !metrics.horizontalDocumentOverflow
      && metrics.clinicalBadgesPresent === 0
      && pageErrors.length === 0 && consoleErrors.length === 0;
    return { viewport:viewport.name, theme, attempt, valid, httpStatus:response?.status()??null,
      initialClosed, closedOnEscape, focusReturned, pointerReachedStage, nDetector, nConstruction, nCertified, nFiltered, proper,
      metrics, pageErrors, consoleErrors, apiRequests:requests };
  } catch (error) {
    return { viewport:viewport.name, theme, attempt, valid:false,
      pageErrors:[...pageErrors, error instanceof Error ? error.message : String(error)],
      consoleErrors, apiRequests:requests };
  } finally {
    await context.close().catch(()=>{});
    await browser.close().catch(()=>{});
  }
}

try {
  await waitForServer(BASE_URL + '/ceph-j1b1-s4.html');
  for (const theme of themes) {
    for (const viewport of viewports) {
      let result = await capture(viewport,1,theme);
      if (!result.valid) result = await capture(viewport,2,theme);
      allCaptures.push(result);
    }
  }
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([
    once(server,'exit'),
    new Promise(resolve => setTimeout(resolve,3000)),
  ]).catch(()=>{});
  await rm(ENTRY,{force:true});
  await rm(PAGE_HTML,{force:true});
  await writeFile(path.join(OUTPUT_DIR,'vite.log'),serverLog,'utf8');
}

const invalid = allCaptures.filter(x=>!x.valid);
const allThemeViewportPairs = themes.flatMap(theme => viewports.map(viewport => theme + ':' + viewport.name));
const observedPairs = allCaptures.map(capture => capture.theme + ':' + capture.viewport);
const pairedCoverage = allCaptures.length === allThemeViewportPairs.length
  && new Set(observedPairs).size === allThemeViewportPairs.length
  && allThemeViewportPairs.every(pair => observedPairs.includes(pair));
const lightCardTokens = new Set(allCaptures.filter(x=>x.theme==='light').map(x=>x.metrics?.cardToken));
const darkCardTokens = new Set(allCaptures.filter(x=>x.theme==='dark').map(x=>x.metrics?.cardToken));
const distinctThemeTokens = lightCardTokens.size === 1 && darkCardTokens.size === 1
  && !lightCardTokens.has([...darkCardTokens][0]);
const report = {
  lot: 'CEPH-J1.B1-S4',
  productHead: PRODUCT_HEAD,
  themes,
  pairedCoverage,
  distinctThemeTokens,
  screenshotBeforeMeaning: 'Closed glossary on SAME candidate HEAD, not a historical baseline commit screenshot',
  screenshotAfterMeaning: 'Opened real Step1 Desktop glossary and one exact Pos search on same viewport',
  fixturePolicy: 'Real CephaloWorkspace/Step1 with synthetic SVG + mock patient ID 901 isolated and all external requests blocked',
  clinicalRelease: false,
  patientDataUsed: false,
  modelInferenceExecuted: false,
  captures: allCaptures,
  blockedExternalRequests,
  invalidCount: invalid.length,
};
await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8');
console.log(JSON.stringify(report,null,2));
if (invalid.length || blockedExternalRequests.length || !pairedCoverage || !distinctThemeTokens) process.exitCode = 1;
