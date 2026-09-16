import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'mutuelles-cnss-ui-after-artifacts');
const PORT = 5199;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const doc = {
  id: '9915104',
  name: 'Honoraires_CNSS_Apres.pdf',
  type: 'NOTE',
  date: '15/09/2026',
  url: '/documents/9915104/download',
  file_exists: true,
  clinical_data: {
    payments: [
      { acte: 'Détartrage', dent: '11,21', montant: 500, date: '2026-09-15' },
      { acte: 'Extraction', dent: '36', montant: 700, date: '2026-09-15' },
    ],
  },
  payment_status: 'EN_ATTENTE',
  is_accounted: true,
};

const preparedDraft = {
  schema_version: '1.0',
  patient_id: 915,
  organization: 'CNSS',
  honoraires_document_id: 9915104,
  lines: [
    {
      service_date: '2026-09-15',
      label: 'Détartrage',
      teeth: ['11', '21'],
      amount_mad: 500,
      mapping_status: 'EXACT',
      ngap_code: 'D',
      ngap_coefficient: 10,
      mapping_rule_id: 'fixture-detartrage',
      source: {
        honoraires_document_id: 9915104,
        honoraires_line_index: 0,
        acte_id: 501,
        source_line_uid: 'fixture-line-1',
        catalog_act_id: 101,
      },
    },
    {
      service_date: '2026-09-15',
      label: 'Extraction',
      teeth: ['36'],
      amount_mad: 700,
      mapping_status: 'EXACT',
      ngap_code: 'DC',
      ngap_coefficient: 15,
      mapping_rule_id: 'fixture-extraction',
      source: {
        honoraires_document_id: 9915104,
        honoraires_line_index: 1,
        acte_id: 502,
        source_line_uid: 'fixture-line-2',
        catalog_act_id: 102,
      },
    },
  ],
  administrative: {
    request_nature: null,
    insured_full_name: null,
    insured_registration_number: null,
    insured_national_id: null,
    insured_address: null,
    insured_quality: null,
    beneficiary_full_name: 'PATIENT CNSS',
    beneficiary_birth_date: '1990-01-01',
    beneficiary_national_id: 'AB123456',
    beneficiary_sex: 'M',
    relationship_to_insured: null,
    practitioner_full_name: 'Dr Cabinet Test',
    practitioner_inpe: 'INPE-777',
    care_type: 'SOINS',
    prior_approval_number: null,
    accident_date: null,
    accident_circumstances: null,
    attachments_count: 0,
  },
  unresolved_fields: [],
  status: 'READY_FOR_REVIEW',
  template: {
    template_version: 'CNSS-610-1-04',
    template_hash: 'fixture-template-hash',
    source_url: 'cabinet://cnss-610-1-04.pdf',
    trust: 'CABINET_VALIDATED',
  },
  reference: {
    ngap_reference_version: 'fixture-ngap',
    ngap_reference_hash: 'fixture-ngap-hash',
  },
  validated_by_practitioner_id: null,
  validated_at: null,
};

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { PatientDocuments } from './features/patients/PatientDocuments';
import { api } from './services/api';
import './index.css';

const fixture = ${JSON.stringify(doc)};
const preparedDraft = ${JSON.stringify(preparedDraft)};
const calls: Array<{ method: string; url: string; data?: unknown }> = [];
(window as any).__cnssCalls = calls;

(api as any).get = async (url: string) => {
  calls.push({ method: 'GET', url });
  if (url === '/patients/915/documents') return { data: [fixture], status: 200 };
  throw new Error('Unexpected GET in deterministic Mutuelles AFTER cert: ' + url);
};
(api as any).post = async (url: string, data?: any) => {
  calls.push({ method: 'POST', url, data });
  if (url === '/documents/insurance-submissions/prepare') {
    return { data: structuredClone(preparedDraft), status: 200 };
  }
  if (url === '/documents/insurance-submissions/validate') {
    return {
      data: {
        ...structuredClone(data),
        status: 'VALIDATED',
        validated_by_practitioner_id: 77,
        validated_at: '2026-09-15T22:30:00Z',
        unresolved_fields: [],
      },
      status: 200,
    };
  }
  if (url === '/documents/insurance-submissions/finalize') {
    return {
      data: {
        document_id: 9915999,
        is_new_version: false,
        file_hash: 'fixture-final-pdf-hash',
        original_filename: 'Feuille_soins_CNSS_915_9915104.pdf',
      },
      status: 200,
    };
  }
  throw new Error('Unexpected POST in deterministic Mutuelles AFTER cert: ' + url);
};

document.body.dataset.theme = 'light';
ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/patients/915']}>
    <Routes><Route path="/patients/:id" element={<PatientDocuments />} /></Routes>
  </MemoryRouter>,
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Mutuelles CNSS UI AFTER</title><style>html,body,#root{width:100%;min-height:100%;margin:0}body{padding:16px;box-sizing:border-box}</style></head><body><div id="root"></div><script type="module" src="/src/mutuelles-cnss-ui-after-entry.tsx"></script></body></html>`;

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
await writeFile(path.join(FRONTEND_DIR, 'src', 'mutuelles-cnss-ui-after-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'mutuelles-cnss-ui-after.html'), htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', chunk => { serverLog += chunk.toString(); });
server.stderr.on('data', chunk => { serverLog += chunk.toString(); });

const captures = [];
const blockedExternalRequests = [];

try {
  await waitForServer(BASE_URL);
  for (const viewport of viewports) {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
      reducedMotion: 'reduce',
      locale: 'fr-FR',
    });
    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
    page.on('dialog', dialog => void dialog.accept());

    await page.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
      if (url.hostname === 'fonts.googleapis.com') return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* offline visual harness */' });
      blockedExternalRequests.push({ viewport: viewport.name, url: request.url(), method: request.method() });
      return route.abort('blockedbyclient');
    });

    const response = await page.goto(`${BASE_URL}/mutuelles-cnss-ui-after.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByText(doc.name, { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-card-${viewport.name}.png`), fullPage: false });

    const actionButton = page.getByRole('button', { name: `Actions du document ${doc.name}`, exact: true });
    await actionButton.click();
    await page.locator('[data-document-action-menu]').waitFor({ state: 'visible', timeout: 10000 });
    const insuranceAction = page.locator('[data-insurance-action="prepare-cnss"]');
    const hasInsuranceAction = await insuranceAction.count() === 1;
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-menu-${viewport.name}.png`), fullPage: false });

    await insuranceAction.click();
    const review = page.locator('[data-insurance-review="cnss"]');
    await review.waitFor({ state: 'visible', timeout: 10000 });
    const reviewVisible = await review.isVisible();
    const upperInsuredControls = await page.locator('[data-cnss-field^="insured_"]').count();
    const validatedZoneControls = await page.locator('[data-cnss-section="administrative"] [data-cnss-field]').count();
    const mentionsInsuredBlank = await page.getByText(/partie supérieure réservée à l’assuré reste volontairement vierge/i).count() === 1;
    const reviewMetrics = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth),
      horizontalOverflow: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > innerWidth + 1,
    }));
    await page.screenshot({ path: path.join(OUTPUT_DIR, `after-review-${viewport.name}.png`), fullPage: false });

    const validateButton = page.locator('[data-cnss-action="validate"]');
    const finalizeButton = page.locator('[data-cnss-action="finalize"]');
    const validateInitiallyEnabled = await validateButton.isEnabled();
    await validateButton.click();
    await page.waitForFunction(() => {
      const button = document.querySelector('[data-cnss-action="finalize"]');
      return button instanceof HTMLButtonElement && !button.disabled;
    });
    const finalizeAfterValidationEnabled = await finalizeButton.isEnabled();
    await finalizeButton.click();
    await review.waitFor({ state: 'detached', timeout: 10000 });
    await page.waitForFunction(() => ((window).__cnssCalls || []).filter(call => call.method === 'GET' && call.url === '/patients/915/documents').length >= 2);

    const calls = await page.evaluate(() => (window).__cnssCalls || []);
    const postUrls = calls.filter(call => call.method === 'POST').map(call => call.url);
    const expectedPostUrls = [
      '/documents/insurance-submissions/prepare',
      '/documents/insurance-submissions/validate',
      '/documents/insurance-submissions/finalize',
    ];
    const exactPostSequence = JSON.stringify(postUrls) === JSON.stringify(expectedPostUrls);
    const metrics = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth),
      horizontalOverflow: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > innerWidth + 1,
    }));

    captures.push({
      viewport: viewport.name,
      httpStatus: response?.status() ?? null,
      pageErrors,
      consoleErrors,
      hasInsuranceAction,
      reviewVisible,
      upperInsuredControls,
      validatedZoneControls,
      mentionsInsuredBlank,
      validateInitiallyEnabled,
      finalizeAfterValidationEnabled,
      exactPostSequence,
      reviewMetrics,
      metrics,
      valid: (
        response?.status() === 200 &&
        hasInsuranceAction &&
        reviewVisible &&
        upperInsuredControls === 0 &&
        validatedZoneControls === 10 &&
        mentionsInsuredBlank &&
        validateInitiallyEnabled &&
        finalizeAfterValidationEnabled &&
        exactPostSequence &&
        !reviewMetrics.horizontalOverflow &&
        !metrics.horizontalOverflow &&
        pageErrors.length === 0 &&
        consoleErrors.length === 0
      ),
    });
    await context.close();
    await browser.close();
  }

  const report = {
    certificate: 'MUTUELLES_CNSS_UI_AFTER_V1',
    phase: 'AFTER',
    productHead: PRODUCT_HEAD,
    viewports: viewports.map(v => v.name),
    captures,
    blockedExternalRequests,
    invalidCount: captures.filter(c => !c.valid).length,
  };
  await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
  if (report.invalidCount || blockedExternalRequests.length) throw new Error(`Visual AFTER failed: ${JSON.stringify(report)}`);
} finally {
  server.kill('SIGTERM');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8').catch(() => {});
  await rm(path.join(FRONTEND_DIR, 'src', 'mutuelles-cnss-ui-after-entry.tsx'), { force: true });
  await rm(path.join(FRONTEND_DIR, 'mutuelles-cnss-ui-after.html'), { force: true });
}
