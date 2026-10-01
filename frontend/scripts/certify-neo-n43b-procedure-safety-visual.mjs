import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/neo-n43b-procedure-safety-visual');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const auth = { Authorization: `Bearer ${tokens.access_token}` };

const patients = await api.get('/api/patients', { headers: auth });
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patientList = await patients.json();
const patient = patientList.find((p) => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2 certification patient not found');

const hiddenContext = {
  anticoagulant_status: 'NONE_REPORTED',
  anticoagulants: null,
  antiplatelet_status: 'NONE_REPORTED',
  antiplatelets: null,
  antithrombotic_classes: null,
  antithrombotic_combination_status: 'NO',
  warfarin_inr: null,
  warfarin_inr_checked_at: null,
  warfarin_inr_current: null,
  lmwh_dose_class: 'UNKNOWN',

  mronj_medication_status: 'PRESENT',
  mronj_agents: ['Zoledronate'],
  mronj_agent_class: 'BISPHOSPHONATE',
  mronj_indication: 'MALIGNANCY',
  mronj_route: 'PARENTERAL',
  mronj_duration_months: 18,
  mronj_concurrent_risk_therapy: ['CHEMOTHERAPY'],
  active_oral_infection_or_inflammation: 'UNKNOWN',
  suspected_or_known_mronj: 'NO',

  procedure_date: '2026-10-01',
  procedure_bleeding_risk: 'HIGHER_POSTOP_BLEEDING_RISK',
  procedure_osseous_risk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  procedure_is_implant: true,
  ie_procedure_qualifies: null,
  oral_route_possible: null,
  currently_taking_penicillin_or_amoxicillin: null,
};

const saved = await api.put(`/api/patients/${patient.id}/procedure-safety-context`, {
  headers: auth,
  data: hiddenContext,
});
if (!saved.ok()) throw new Error(`Procedure safety context seed failed: ${saved.status()} ${await saved.text()}`);

const alertProbe = await api.get(`/api/prescriptions/clinical-rules/procedure-safety/alert/${patient.id}`, {
  headers: auth,
});
if (!alertProbe.ok()) throw new Error(`Alert probe failed: ${alertProbe.status()} ${await alertProbe.text()}`);
const alertData = await alertProbe.json();
if (alertData.alert_key !== 'SPECIALIST_REVIEW_RECOMMENDED') {
  throw new Error(`Unexpected alert probe: ${JSON.stringify(alertData)}`);
}

const browser = await chromium.launch({ headless: true });
const captures = [];
const viewports = [
  { width: 390, height: 844 },
  { width: 1280, height: 900 },
];

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();

  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });

  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));

  const url = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=ordonnance`;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });

  const studio = page.locator('[data-prescription-intelligence-studio="v1"]');
  await studio.waitFor({ state: 'attached', timeout: 30000 });

  const notice = page.locator('[data-procedure-safety-notice="subtle"]');
  await notice.waitFor({ state: 'visible', timeout: 30000 });
  await page.waitForTimeout(300);

  const visibleText = await notice.innerText();
  if (visibleText.trim() !== 'Avis spécialisé recommandé.') {
    throw new Error(`Unexpected visible notice copy: ${visibleText}`);
  }

  const bodyText = await page.locator('body').innerText();
  const forbidden = ['MRONJ', 'CTX', 'Zoledronate', 'bisphosphonate', 'denosumab', 'drug holiday'];
  const leaked = forbidden.filter(term => bodyText.toLowerCase().includes(term.toLowerCase()));
  if (leaked.length) throw new Error(`Hidden MRONJ terminology leaked to practitioner UI: ${leaked.join(', ')}`);

  const metrics = await notice.evaluate(el => {
    const r = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return {
      top: r.top,
      left: r.left,
      width: r.width,
      height: r.height,
      fontSize: style.fontSize,
      color: style.color,
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
    };
  });

  const screenshot = `neo-n43b-mronj-alert-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false });

  captures.push({ viewport, screenshot, visibleText, metrics, pageErrors });
  await context.close();
}

const failures = [];
for (const capture of captures) {
  if (capture.pageErrors.length) failures.push(`${capture.viewport.width}: page errors ${capture.pageErrors.join(' | ')}`);
  if (capture.metrics.horizontalOverflow) failures.push(`${capture.viewport.width}: horizontal overflow`);
  if (capture.metrics.height > 48) failures.push(`${capture.viewport.width}: notice too tall for subtle surface (${capture.metrics.height}px)`);
}

const report = {
  status: failures.length ? 'FAIL' : 'PASS',
  head: process.env.GITHUB_SHA || null,
  patientId: patient.id,
  seededScenario: 'MRONJ_MALIGNANCY_IMPLANT_REVIEW',
  backendAlert: alertData,
  captures,
  failures,
};
fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify(report, null, 2));

await browser.close();
await api.dispose();

console.log(JSON.stringify(report, null, 2));
if (failures.length) process.exit(1);
