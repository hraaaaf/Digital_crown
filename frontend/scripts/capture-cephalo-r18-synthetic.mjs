import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'cephalo-r18-synthetic-artifacts');
const PORT = 5198;
const BASE_URL = `http://127.0.0.1:${PORT}`;

const syntheticLandmarks = [
  { id: 'S', x: 500, y: 250 },
  { id: 'N', x: 600, y: 300 },
  { id: 'A', x: 640, y: 500 },
  { id: 'B', x: 620, y: 650 },
  { id: 'Po', x: 450, y: 350 },
  { id: 'Or', x: 650, y: 360 },
  { id: 'Go', x: 450, y: 800 },
  { id: 'Me', x: 650, y: 900 },
  { id: 'U1_incisal', x: 650, y: 700 },
  { id: 'U1_apex', x: 620, y: 560 },
  { id: 'L1_incisal', x: 630, y: 690 },
  { id: 'L1_apex', x: 590, y: 790 },
  { id: 'Prn', x: 760, y: 480 },
  { id: 'Ls_soft', x: 735, y: 620 },
  { id: 'Li_soft', x: 730, y: 690 },
  { id: 'Pog_soft', x: 700, y: 820 },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Step3Clinical } from './features/ortho/components/Step3Clinical';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import { computeStep3Data } from './features/ortho/cephaloUtils';
import { getCephaloPalette } from './features/ortho/cephaloTheme';
import './index.css';

const landmarks = ${JSON.stringify(syntheticLandmarks)};
const base = useOrthoStore.getState().etape3Data;
const calculated = computeStep3Data(landmarks, 34, 'M', 0.1, null);

useOrthoStore.setState({
  patientId: 915,
  patientName: 'Patient Synthétique R18',
  analysisId: 9918,
  local: { landmarks, version: 1 },
  isCalibrated: true,
  mmPerPixel: 0.1,
  etape3Data: {
    ...base,
    ...calculated,
    selectedAnalysis: 'COM',
    dentaire: { ...base.dentaire, ...(calculated.dentaire || {}) },
    osseuse: { ...base.osseuse, ...(calculated.osseuse || {}) },
    esthetique: { ...base.esthetique, ...(calculated.esthetique || {}) },
  },
});

document.body.dataset.theme = 'default';

function App() {
  const P = getCephaloPalette();
  return (
    <main style={{ minHeight: '100vh', background: P.bg, padding: '24px' }}>
      <div style={{ maxWidth: '1120px', margin: '0 auto' }}>
        <Step3Clinical P={P} />
      </div>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Cephalo R18 synthetic capture</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-r18-synthetic-entry.tsx"></script></body></html>`;

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'cephalo-r18-synthetic-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'cephalo-r18-synthetic.html'), htmlSource, 'utf8');
await writeFile(path.join(OUTPUT_DIR, 'synthetic-landmarks.json'), JSON.stringify({
  fixture: 'CEPHALO_R18_SYNTHETIC_V1',
  disclaimer: 'Synthetic geometry for runtime/UI validation only. Not a clinical patient and not a normative reference.',
  age: 34,
  sex: 'M',
  mmPerPixel: 0.1,
  landmarks: syntheticLandmarks,
}, null, 2), 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', chunk => { serverLog += chunk.toString(); });
server.stderr.on('data', chunk => { serverLog += chunk.toString(); });

const pageErrors = [];
const consoleErrors = [];
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1400 },
  deviceScaleFactor: 2,
  reducedMotion: 'reduce',
  locale: 'fr-FR',
});
const page = await context.newPage();
page.on('pageerror', error => pageErrors.push(error.message));
page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });

function metricReader(labels) {
  return page.evaluate((wanted) => {
    const values = {};
    const spans = Array.from(document.querySelectorAll('span'));
    for (const label of wanted) {
      const labelEl = spans.find(node => (node.textContent || '').trim() === label);
      if (!labelEl) {
        values[label] = null;
        continue;
      }
      const card = labelEl.parentElement?.parentElement;
      const input = card?.querySelector('input');
      if (input) {
        values[label] = input.value;
        continue;
      }
      const valueEl = Array.from(card?.querySelectorAll('div') || []).find(node => {
        const cls = node.getAttribute('class') || '';
        return cls.includes('text-base') && cls.includes('font-black');
      });
      values[label] = valueEl ? (valueEl.textContent || '').trim() : null;
    }
    return values;
  }, labels);
}

async function ensureSectionOpen(sectionName, proofLabel) {
  if (await page.getByText(proofLabel, { exact: true }).count()) {
    const proof = page.getByText(proofLabel, { exact: true }).first();
    if (await proof.isVisible()) return;
  }
  await page.getByRole('button', { name: sectionName }).click();
  await page.getByText(proofLabel, { exact: true }).first().waitFor({ state: 'visible' });
}

const modes = [
  {
    key: 'com',
    button: 'McNamara (COM)',
    required: ['Surplomb', 'Recouvrement', '1 / Mandibulaire (IMPA)', '1 / Francfort', 'Inter Incisif (1/1)', 'Angle de Tweed', 'A′B′', 'Situation Point A', 'Situation Point B', 'Profondeur Faciale'],
    sections: [['Analyse Osseuse', 'A′B′']],
  },
  {
    key: 'steiner',
    button: 'STEINER',
    required: ['1 / NA (°)', '1 / NA (mm)', '1 / NB (°)', '1 / NB (mm)', 'Inter-Incisif', 'SNA', 'SNB', 'ANB', 'Ligne E / Ls', 'Ligne E / Li'],
    sections: [['Analyse Osseuse', 'SNA'], ['Analyse Esthétique (Ricketts)', 'Ligne E / Ls']],
  },
  {
    key: 'tweed',
    button: 'TWEED',
    required: ['IMPA', 'FMIA', 'Angle de Tweed', 'Ligne E / Ls', 'Ligne E / Li'],
    sections: [['Analyse Osseuse', 'Angle de Tweed'], ['Analyse Esthétique (Ricketts)', 'Ligne E / Ls']],
  },
];

const report = {
  lot: 'CEPHALO-R18-SYNTHETIC-RUNTIME-CAPTURE',
  productHead: PRODUCT_HEAD,
  fixture: 'CEPHALO_R18_SYNTHETIC_V1',
  disclaimer: 'Synthetic geometry for runtime/UI validation only. No clinical or normative validity claimed.',
  viewport: '1440x1400@2x',
  analyses: [],
  pageErrors,
  consoleErrors,
};

try {
  await waitForServer(`${BASE_URL}/cephalo-r18-synthetic.html`);
  await page.goto(`${BASE_URL}/cephalo-r18-synthetic.html`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.getByRole('button', { name: 'McNamara (COM)' }).waitFor({ state: 'visible', timeout: 30000 });

  for (const mode of modes) {
    await page.getByRole('button', { name: mode.button }).click();
    await page.waitForTimeout(150);
    for (const [sectionName, proofLabel] of mode.sections) {
      await ensureSectionOpen(sectionName, proofLabel);
    }
    const values = await metricReader(mode.required);
    const missing = Object.entries(values).filter(([, value]) => value === null || value === '' || value === '-').map(([label]) => label);
    if (missing.length) throw new Error(`${mode.key}: calculated values missing for ${missing.join(', ')}`);
    const filename = `analysis-${mode.key}-1440x1400@2x.png`;
    await page.screenshot({ path: path.join(OUTPUT_DIR, filename), fullPage: true });
    report.analyses.push({ mode: mode.key.toUpperCase(), uiLabel: mode.button, screenshot: filename, values, valid: true });
  }

  if (pageErrors.length || consoleErrors.length) {
    throw new Error(`Browser errors: page=${JSON.stringify(pageErrors)} console=${JSON.stringify(consoleErrors)}`);
  }
  await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
} catch (error) {
  report.failure = String(error?.stack || error);
  await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
  throw error;
} finally {
  await browser.close();
  server.kill('SIGTERM');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
  await rm(path.join(FRONTEND_DIR, 'src', 'cephalo-r18-synthetic-entry.tsx'), { force: true });
  await rm(path.join(FRONTEND_DIR, 'cephalo-r18-synthetic.html'), { force: true });
}
