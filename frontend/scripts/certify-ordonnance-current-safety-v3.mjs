/**
 * LOT07 R2 — current Ordonnance clinical boundary, four-viewport real browser.
 * Historical C2 interactive panels deliberately DO NOT mount in the current
 * clinician-facing Ordonnance. Their clinical fail-closed rule remains tested
 * separately through backend/tests/test_prescription_c2_ie_evaluation_endpoint.py.
 * No mocking clinical READY states, no simulated authenticated workstation.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

if (process.env.ENVIRONMENT !== 'test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    process.env.DATABASE_URL !== 'sqlite:///./ordonnance-fidelity-v3.db' ||
    !/^[0-9a-f]{40}$/.test(process.env.PRODUCT_HEAD || '')) {
  throw new Error('REFUSED: current Ordonnance safety visual only on disposable T2 database');
}
const password = process.env.T2_PASSWORD;
if (!password) throw new Error('REFUSED: missing ephemeral T2 credential');
const outDir = path.resolve('../artifacts/ordonnance-fidelity-v3');
fs.mkdirSync(outDir, { recursive: true });

const urlBase = 'http://127.0.0.1:5173';
const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error('Synthetic owner authentication failed: HTTP ' + login.status());
const auth = await login.json();
const workstationState = await enrollT2Workstation(api, auth.access_token, password);
const cookies = workstationState.cookies.filter(c => c.name === 'dc_workstation');
if (cookies.length !== 1 || cookies[0].httpOnly !== true) {
  throw new Error('REFUSED: normal HTTP-only workstation enrollment not proven');
}
const headers = { Authorization: 'Bearer ' + auth.access_token };
const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error('Enrolled T2 patient list refused: HTTP ' + patients.status());
const patient = (await patients.json()).find(p => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2-0001 synthetic patient not found');

const alertResponse = await api.get('/api/prescriptions/clinical-rules/procedure-safety/alert/' + patient.id, { headers });
if (!alertResponse.ok()) throw new Error('Real safety alert probe HTTP ' + alertResponse.status());
const alert = await alertResponse.json();
if (alert.read_only !== true) throw new Error('Safety alert must be read-only');
const COPY = {
  CONTEXT_REQUIRED: 'Contexte clinique à compléter.',
  CLINICAL_REVIEW_RECOMMENDED: 'Vérification clinique conseillée avant validation.',
  PRESCRIBER_REVIEW_RECOMMENDED: 'Avis prescripteur recommandé.',
  SPECIALIST_REVIEW_RECOMMENDED: 'Avis spécialisé recommandé.',
  SAFETY_CHECK_UNAVAILABLE: 'Vérification clinique momentanément indisponible.',
};
if (alert.alert_key != null && !Object.hasOwn(COPY, alert.alert_key)) {
  throw new Error('Unexpected clinical alert key: fail-closed');
}
const expectedMessage = alert.alert_key ? COPY[alert.alert_key] : null;
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];
const captures = [];
const failures = [];
const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport, colorScheme: 'light', reducedMotion: 'reduce',
      storageState: { cookies, origins: [] },
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(String(error)));
    await page.addInitScript(({ access, refresh }) => {
      localStorage.setItem('token', access);
      localStorage.setItem('refresh_token', refresh || '');
      localStorage.setItem('appMode', 'prod');
    }, { access: auth.access_token, refresh: auth.refresh_token });
    try {
      await page.goto(urlBase + '/patients/' + patient.id + '?tab=admin&documentTab=ordonnance', {
        waitUntil: 'domcontentloaded', timeout: 90000,
      });
      const studio = page.locator('[data-prescription-intelligence-studio="v1"]');
      await studio.waitFor({ state: 'visible', timeout: 45000 });
      const drug = studio.locator('[data-ordonnance-drug-card]').first();
      await drug.waitFor({ state: 'visible', timeout: 30000 });
      const blockedStatus = await studio.getAttribute('data-clinical-rule-status');
      const safetyState = await studio.getAttribute('data-safety-status');
      const safetyMechanics = await studio.getAttribute('data-safety-mechanics');
      if (blockedStatus !== 'blocked' || safetyState !== 'blocked' ||
          safetyMechanics !== 'background-only') {
        failures.push(viewport.width + ': active clinical automation is not fail-closed');
      }

      // The current clinical policy forbids resurrecting the legacy edit panels
      // in this surface. Their underlying server rule is independently tested.
      for (const selector of ['[data-patient-clinical-context]', '[data-ie-prophylaxis-rule="c2"]']) {
        if (await studio.locator(selector).count()) {
          failures.push(viewport.width + ': obsolete autonomous clinical panel mounted: ' + selector);
        }
      }
      const notice = studio.locator('[data-procedure-safety-notice="subtle"]');
      if (expectedMessage) {
        await notice.waitFor({ state: 'visible', timeout: 20000 });
        const actual = (await notice.innerText()).trim();
        if (actual !== expectedMessage) failures.push(viewport.width + ': unexpected generic alert text');
      } else if (await notice.count()) {
        failures.push(viewport.width + ': READY/null safety state should remain silent');
      }
      const indication = studio.getByRole('textbox', { name: 'Indication de cette ordonnance' });
      if (!(await indication.isVisible())) failures.push(viewport.width + ': document indication missing');
      const addLine = studio.getByRole('button', { name: /ajouter une ligne/i });
      if (!(await addLine.isVisible())) failures.push(viewport.width + ': add-line action missing');

      // Validate minimum primary touch controls, no horizontal overflow,
      // and absence of internal safety or pharmacology terminology in UI.
      const metrics = await studio.evaluate(el => {
        const rect = node => node.getBoundingClientRect();
        const visible = node => {
          const r = rect(node), s = getComputedStyle(node);
          return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
        };
        const buttons = [...el.querySelectorAll('button')].filter(visible);
        const primary = buttons.filter(node =>
          /ajouter une ligne|type médicament|type radio ou examen/i.test(
            [node.textContent || '', node.getAttribute('aria-label') || ''].join(' '),
          )
        );
        return {
          studioWidth: rect(el).width,
          primaryTouchMin: primary.length ? Math.min(...primary.map(n => rect(n).height)) : null,
          primaryTouchCount: primary.length,
          documentOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
        };
      });
      if (metrics.primaryTouchCount < 3 || (metrics.primaryTouchMin ?? 0) < 43.5) {
        failures.push(viewport.width + ': primary touch target contract failed');
      }
      if (metrics.documentOverflow) failures.push(viewport.width + ': horizontal overflow');
      if (metrics.studioWidth < 270) failures.push(viewport.width + ': editor below minimum usable width');

      const clinicianText = (await studio.innerText()).toLowerCase();
      const forbidden = ['mronj', 'ctx', 'zoledronate', 'bisphosphonate', 'drug holiday',
        'règle de dose v1 certifiée', 'suggestion clinique indisponible'];
      if (forbidden.some(term => clinicianText.includes(term))) {
        failures.push(viewport.width + ': private / obsolete pharmacology wording surfaced');
      }

      // Preserve the existing real desktop preview certification: preview
      // must open as an inline split, never a squeezed offscreen drawer.
      let preview = null;
      if (viewport.width >= 1280) {
        const previewButton = page.getByRole('button', { name: /aperçu/i }).first();
        await previewButton.waitFor({ state: 'visible', timeout: 20000 });
        await previewButton.click();
        const aside = page.locator('[data-ordonnance-desktop-preview="inline"]');
        await aside.waitFor({ state: 'visible', timeout: 30000 });
        preview = await aside.evaluate(el => {
          const r = el.getBoundingClientRect();
          return { width: r.width, left: r.left, right: r.right, viewport: window.innerWidth };
        });
        if (preview.width < 270 || preview.right > viewport.width + 2) {
          failures.push(viewport.width + ': desktop preview unusable');
        }
      }
      if (pageErrors.length) failures.push(viewport.width + ': JS runtime error count ' + pageErrors.length);
      const shot = 'ordonnance-current-safety-' + viewport.width + 'x' + viewport.height + '.png';
      await page.screenshot({
        path: path.join(outDir, shot), fullPage: false,
        animations: 'disabled', caret: 'hide', timeout: 90000,
      });
      captures.push({ viewport, screenshot: shot, metrics, preview,
        alertKey: alert.alert_key || null, expectedMessage, pageErrorCount: pageErrors.length });
      console.log('R2_CURRENT_FIDELITY_VIEWPORT_PASS', viewport.width, viewport.height);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
  await api.dispose();
}

const report = {
  head: process.env.PRODUCT_HEAD,
  contract: 'NEO_N4_3B_READ_ONLY_GENERIC_ALERT_AND_SEPARATE_C2',
  syntheticOnly: true, status: failures.length ? 'FAIL' : 'PASS',
  viewports: viewports.map(v => v.width + 'x' + v.height),
  captures, failures,
};
fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify(report, null, 2));
console.log('R2_ORDONNANCE_CURRENT_SAFETY_VISUAL', JSON.stringify(report));
if (failures.length) process.exit(1);
