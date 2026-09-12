import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'cephalo-r15-after-artifacts');
const PORT = 5196;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const r15Snapshot = {
  contract_version: 'R15_CLINICAL_STUDIO_VIEW_V1',
  patient_id: 915,
  analysis_id: 9915,
  evidence_graph_present: true,
  active_runtime_chain_verified: true,
  blocking_gate_count: 7,
  blocking_gates: [
    'diagnostic_rule_registry_empty',
    'r11_authoritative_snapshot_not_persisted',
    'r11_not_authoritative',
    'r12_authoritative_snapshot_not_persisted',
    'therapeutic_rule_registry_empty',
    'r13_authoritative_snapshot_not_persisted',
    'r14_authoritative_snapshot_not_persisted',
  ],
  clinical_validation_available: false,
  clinical_validation_reason: 'Aucune validation clinique R14 sans snapshot autoritaire persistant et preuve praticien backend.',
  stages: [
    {
      stage_id: 'R11', title: 'Diagnostic scientifique', presentation_state: 'BLOCKED', authoritative_status: null,
      summary: "Aucun diagnostic n'est promu depuis les mesures sans règle source-lockée et snapshot R11 autoritaire.",
      blocking_gates: ['diagnostic_rule_registry_empty', 'r11_authoritative_snapshot_not_persisted'],
      missing_data_refs: [], contradictions: [], contraindications: [],
      provenance: [
        { label: 'Analyse céphalométrique', value: '9915' },
        { label: 'Chaîne active', value: 'vérifiée' },
        { label: 'Mesures typées actives', value: '4' },
        { label: 'Règles diagnostiques actives', value: '0' },
      ],
      clinician_action: { available: false, audit_required: true, label: 'Validation praticien', reason: "Action indisponible tant qu'un snapshot clinique autoritaire et sa preuve traçable ne sont pas résolus par le backend." },
    },
    {
      stage_id: 'R12', title: 'Problem list & objectifs', presentation_state: 'BLOCKED', authoritative_status: null,
      summary: "Les problèmes et objectifs ne peuvent dériver que d'éléments R11 explicitement validés.",
      blocking_gates: ['r11_not_authoritative', 'r12_authoritative_snapshot_not_persisted'],
      missing_data_refs: [], contradictions: [], contraindications: [],
      provenance: [{ label: 'Autorité amont', value: 'R11 requis' }],
      clinician_action: { available: false, audit_required: true, label: 'Validation praticien', reason: "Action indisponible tant qu'un snapshot clinique autoritaire et sa preuve traçable ne sont pas résolus par le backend." },
    },
    {
      stage_id: 'R13', title: 'Options thérapeutiques', presentation_state: 'BLOCKED', authoritative_status: null,
      summary: "Évaluable n'est jamais une prescription. Aucune option n'est auto-sélectionnée.",
      blocking_gates: ['r12_not_authoritative', 'therapeutic_rule_registry_empty', 'r13_authoritative_snapshot_not_persisted'],
      missing_data_refs: [], contradictions: [], contraindications: [],
      provenance: [{ label: "Règles d'option actives", value: '0' }, { label: 'Règles de critère actives', value: '0' }],
      clinician_action: { available: false, audit_required: true, label: 'Validation praticien', reason: "Action indisponible tant qu'un snapshot clinique autoritaire et sa preuve traçable ne sont pas résolus par le backend." },
    },
    {
      stage_id: 'R14', title: 'Validation clinique finale', presentation_state: 'BLOCKED', authoritative_status: null,
      summary: 'Une validation finale exige une option R13 sélectionnée et une preuve praticien résolue, horodatée et traçable.',
      blocking_gates: ['r13_no_clinician_selected_option', 'r14_authoritative_snapshot_not_persisted'],
      missing_data_refs: [], contradictions: [], contraindications: [],
      provenance: [{ label: 'Autorité amont', value: 'R13 sélection praticien requise' }],
      clinician_action: { available: false, audit_required: true, label: 'Validation praticien', reason: "Action indisponible tant qu'un snapshot clinique autoritaire et sa preuve traçable ne sont pas résolus par le backend." },
    },
  ],
};

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { CephaloWorkspace } from './features/ortho/CephaloWorkspace';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import './index.css';

document.body.dataset.theme = 'dark';
const fixture = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(\`
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600">
    <rect width="1200" height="1600" fill="#020617"/>
    <path d="M470 220 C720 260 820 520 760 760 C710 960 570 1160 420 1340" fill="none" stroke="#94a3b8" stroke-width="18" opacity=".38"/>
    <path d="M390 520 C600 450 790 560 820 760 C760 900 620 970 460 940" fill="none" stroke="#cbd5e1" stroke-width="12" opacity=".28"/>
  </svg>\`);

useOrthoStore.setState({
  patientId: 915,
  patientName: 'Patient Démo R15',
  analysisId: 9915,
  imageSrc: fixture,
  imgDim: { w: 1200, h: 1600 },
  local: { landmarks: [], version: 1 },
  anglesData: { calibration_status: 'validated', SNA: 82, SNB: 80, ANB: 2, FMA: 25, IMPA: 90 },
  visionMetadata: {},
  isCalibrated: true,
  mmPerPixel: 0.1,
  showCalibration: false,
  calibrationClickPoints: [],
  calibrationDistance: '',
  calibrationStep: 'selecting',
  completedSteps: new Set([1, 2]),
  step: 3,
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/patients/915/cephalo']}>
    <div style={{minHeight:'100vh'}}><CephaloWorkspace patientId={915} patientName="Patient Démo R15" /></div>
  </MemoryRouter>,
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Cephalo R15 AFTER</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-r15-after-entry.tsx"></script></body></html>`;
const json = (body, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) });

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try { const response = await fetch(url); if (response.ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'cephalo-r15-after-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'cephalo-r15-after.html'), htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none', VITE_API_URL: 'http://127.0.0.1:8005' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', chunk => { serverLog += chunk.toString(); });
server.stderr.on('data', chunk => { serverLog += chunk.toString(); });

const captures = [];
const blockedExternalRequests = [];

async function metrics(page, viewportName, scene) {
  return page.evaluate(({ viewportName, scene }) => {
    const body = document.body;
    const doc = document.documentElement;
    const text = (body.textContent || '').toLowerCase();
    const header = Array.from(document.querySelectorAll('h2')).find(node => node.textContent?.includes('Studio Céphalométrique'))?.parentElement?.parentElement;
    const rect = header?.getBoundingClientRect();
    return {
      viewport: viewportName,
      scene,
      innerWidth,
      scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
      horizontalDocumentOverflow: Math.max(doc.scrollWidth, body.scrollWidth) > innerWidth + 1,
      headerClipped: Boolean(rect && (rect.left < -1 || rect.right > innerWidth + 1)),
      hasWorkspaceHeading: text.includes('studio céphalométrique'),
      hasScientificChain: text.includes('chaîne clinique scientifique'),
      hasR11Surface: text.includes('r11'),
      hasR12Surface: text.includes('r12'),
      hasR13Surface: text.includes('r13'),
      hasR14Surface: text.includes('r14'),
      hasMissingSurface: text.includes('données manquantes'),
      hasContradictionSurface: text.includes('contradictions'),
      hasContraindicationSurface: text.includes('contre-indications'),
      hasPractitionerAction: text.includes('action praticien'),
      hasNoFakeValidation: text.includes('aucune validation disponible'),
      hasNonAuthoritativeNotes: text.includes('notes praticien non autoritaires'),
      hasDocumentSeparation: text.includes('actions documentaires') && text.includes('ne valide jamais r14'),
      hasArchiveAction: text.includes('archiver le bilan'),
      hasLegacyDiagnostic: text.includes('diagnostic / résumé diagnostique'),
      hasLegacyTreatmentDecision: text.includes('plan thérapeutique') && text.includes('décision praticien'),
      hasLegacyTreatmentPanel: text.includes('plan de traitement') && text.includes('praticien'),
      hasLegacyArchiveAction: text.includes('valider & archiver'),
      bodyHeight: body.scrollHeight,
    };
  }, { viewportName, scene });
}

function studioContract(m) {
  return m.hasWorkspaceHeading && m.hasScientificChain && m.hasR11Surface && m.hasR12Surface && m.hasR13Surface && m.hasR14Surface &&
    m.hasMissingSurface && m.hasContradictionSurface && m.hasContraindicationSurface && m.hasPractitionerAction && m.hasNoFakeValidation &&
    !m.horizontalDocumentOverflow && !m.headerClipped && !m.hasLegacyDiagnostic && !m.hasLegacyTreatmentDecision && !m.hasLegacyTreatmentPanel && !m.hasLegacyArchiveAction;
}

async function captureAttempt(viewport, attempt) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1, reducedMotion: 'reduce', locale: 'fr-FR' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const apiRequests = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });

  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
    if (url.hostname === '127.0.0.1' && url.port === '8005') {
      apiRequests.push(`${request.method()} ${url.pathname}${url.search}`);
      if (request.method() === 'GET' && url.pathname === '/api/patients/915') return route.fulfill(json({ id: 915, nom: 'Démo', prenom: 'R15', age: 34, sexe: 'M' }));
      if (request.method() === 'GET' && url.pathname === '/api/patients/915/cephalo-clinical-studio') return route.fulfill(json(r15Snapshot));
      if (request.method() === 'GET' && url.pathname === '/api/patients/915/cephalo-validation') return route.fulfill(json({ is_valid: true, fatals: [], warnings: [] }));
      if (request.method() === 'PUT' && url.pathname === '/api/ia/analyses/9915') return route.fulfill(json({ id: 9915, status: 'saved' }));
      return route.fulfill(json({ detail: 'Endpoint neutralisé dans le AFTER visuel R15' }, 418));
    }
    if (url.hostname === 'fonts.googleapis.com') return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* offline visual harness */' });
    blockedExternalRequests.push({ viewport: viewport.name, attempt, url: request.url(), method: request.method() });
    return route.abort('blockedbyclient');
  });

  try {
    const response = await page.goto(`${BASE_URL}/cephalo-r15-after.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByRole('heading', { name: 'Studio Céphalométrique' }).waitFor({ state: 'visible', timeout: 30000 });
    await page.getByText('Chaîne clinique scientifique').waitFor({ state: 'visible', timeout: 30000 });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    await page.waitForTimeout(350);

    const step3Top = await metrics(page, viewport.name, 'step3-top');
    if (!studioContract(step3Top) || !step3Top.hasNonAuthoritativeNotes) throw new Error(`Step3 AFTER contract failed ${JSON.stringify(step3Top)}`);
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-step3-top-${viewport.name}.png`), fullPage: false });

    const note = page.getByText(/Note diagnostique praticien/i).first();
    await note.waitFor({ state: 'visible', timeout: 10000 });
    await note.scrollIntoViewIfNeeded();
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-step3-decision-${viewport.name}.png`), fullPage: false });

    await page.getByRole('button', { name: /Documents & stratégie/i }).click();
    await page.getByText('Chaîne clinique scientifique').waitFor({ state: 'visible', timeout: 15000 });
    await page.waitForTimeout(250);
    const step4Top = await metrics(page, viewport.name, 'step4-top');
    if (!studioContract(step4Top) || !step4Top.hasDocumentSeparation || !step4Top.hasArchiveAction) throw new Error(`Step4 AFTER contract failed ${JSON.stringify(step4Top)}`);
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-step4-top-${viewport.name}.png`), fullPage: false });

    const archive = page.getByRole('button', { name: /Archiver le bilan/i }).first();
    await archive.waitFor({ state: 'visible', timeout: 10000 });
    await archive.scrollIntoViewIfNeeded();
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-step4-action-${viewport.name}.png`), fullPage: false });

    return {
      viewport: viewport.name,
      attempt,
      httpStatus: response?.status() ?? null,
      pageErrors,
      consoleErrors,
      apiRequests,
      step3Top,
      step4Top,
      valid: response?.status() === 200 && pageErrors.length === 0 && consoleErrors.length === 0 && studioContract(step3Top) && studioContract(step4Top),
    };
  } catch (error) {
    return { viewport: viewport.name, attempt, httpStatus: null, pageErrors: [...pageErrors, error instanceof Error ? error.message : String(error)], consoleErrors, apiRequests, valid: false };
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

try {
  await waitForServer(`${BASE_URL}/cephalo-r15-after.html`);
  for (const viewport of viewports) {
    const attempts = [await captureAttempt(viewport, 1)];
    if (!attempts[0].valid) attempts.push(await captureAttempt(viewport, 2));
    const finalAttempt = attempts.at(-1);
    captures.push({ ...finalAttempt, attempts: attempts.map(({ attempt, valid, httpStatus, pageErrors, consoleErrors }) => ({ attempt, valid, httpStatus, pageErrors, consoleErrors })), recoveredTransientRender: attempts.length === 2 && !attempts[0].valid && attempts[1].valid });
  }
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  if (server.exitCode === null && !server.killed) server.kill('SIGKILL');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}

const invalid = captures.filter(item => !item.valid);
const report = {
  lot: 'CEPHALO-R15', phase: 'AFTER', productHead: PRODUCT_HEAD,
  viewports: viewports.map(item => item.name),
  fixturePolicy: 'Real production R15 CephaloWorkspace with isolated deterministic patient/clinical snapshot. Snapshot is fail-closed and contains no invented clinical conclusion.',
  capturePolicy: 'Fresh Chromium process per viewport/attempt. One retry only for transient render failure. Final attempt must satisfy scientific-state visibility, semantic-separation, layout and console gates.',
  captures, blockedExternalRequests, invalidCount: invalid.length,
};
await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
if (invalid.length > 0 || blockedExternalRequests.length > 0) process.exitCode = 1;
