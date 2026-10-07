import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD required');

const baseURL = 'http://127.0.0.1:5173';
const apiURL = 'http://127.0.0.1:8005';
const outDir = path.resolve('../artifacts/t2-browser/first-user-experience-b');
fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const personas = [
  {
    id: 'secondary-dentist',
    email: 't2-secondary@cabinet.ma',
    expectedRole: 'DENTISTE',
    allowedPatients: true,
    firstRoute: '/patients',
    firstValue: /CERTIFICATION|Patients/i,
  },
  {
    id: 'restricted-secretary',
    email: 't2-restricted@cabinet.ma',
    expectedRole: 'SECRETAIRE',
    allowedPatients: false,
    firstRoute: '/agenda',
    firstValue: /Agenda/i,
  },
];

const viewports = [
  { id: 'mobile', width: 390, height: 844 },
  { id: 'desktop', width: 1280, height: 900 },
];

const bootstrap = await request.newContext({ baseURL: apiURL });
const ownerLogin = await bootstrap.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!ownerLogin.ok()) throw new Error('FUE-B owner bootstrap login failed: ' + ownerLogin.status());
const ownerTokens = await ownerLogin.json();
const enrolled = await enrollT2Workstation(bootstrap, ownerTokens.access_token, password);
await bootstrap.dispose();

const stationStorage = {
  ...enrolled,
  cookies: (enrolled.cookies || []).filter(cookie => !['access_token', 'refresh_token'].includes(cookie.name)),
};

const browser = await chromium.launch({ headless: true });
const report = {
  productHead: process.env.PRODUCT_HEAD || null,
  fueType: 'B',
  scenario: 'new user joins an already configured cabinet',
  startedAt: new Date().toISOString(),
  runs: [],
};

for (const persona of personas) {
  for (const viewport of viewports) {
    const label = persona.id + '-' + viewport.id;
    const dir = path.join(outDir, label);
    fs.mkdirSync(dir, { recursive: true });
    const ctx = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      colorScheme: 'light',
      storageState: stationStorage,
    });
    const page = await ctx.newPage();
    const started = Date.now();
    let interactions = 0;
    const consoleErrors = [];
    const pageErrors = [];
    const http5xx = [];
    const initStatusErrors = [];
    const checkpoints = [];

    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push({ tMs: Date.now() - started, text: msg.text() });
    });
    page.on('pageerror', err => pageErrors.push({ tMs: Date.now() - started, message: String(err?.message || err) }));
    page.on('response', res => {
      const item = { tMs: Date.now() - started, status: res.status(), url: res.url() };
      if (res.status() >= 500) http5xx.push(item);
      if (res.url().includes('/api/clinics/init-status') && res.status() >= 400) initStatusErrors.push(item);
    });

    async function checkpoint(id, title) {
      await page.waitForTimeout(150);
      const overflow = await page.evaluate(() => ({
        viewportWidth: window.innerWidth,
        bodyWidth: document.body.scrollWidth,
        htmlWidth: document.documentElement.scrollWidth,
        horizontal: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > window.innerWidth + 1,
      }));
      const filename = String(checkpoints.length + 1).padStart(2, '0') + '-' + id + '.png';
      await page.screenshot({ path: path.join(dir, filename), fullPage: true, animations: 'disabled' });
      checkpoints.push({
        id,
        title,
        path: new URL(page.url()).pathname,
        tMs: Date.now() - started,
        interactions,
        overflow,
        screenshot: path.join(label, filename),
      });
    }

    await page.goto(baseURL + '/login', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 90000 });
    await checkpoint('before-login', 'BEFORE — première connexion');

    await page.getByPlaceholder('nom@cabinet.com').fill(persona.email);
    interactions += 1;
    await page.getByPlaceholder('••••••••').fill(password);
    interactions += 1;
    await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
    interactions += 1;

    await page.waitForFunction(() => !['/login', '/setup'].includes(window.location.pathname), null, { timeout: 20000 });
    await page.waitForTimeout(700);
    const landingPath = new URL(page.url()).pathname;
    if (landingPath === '/setup') throw new Error(label + ': employee was sent through institutional setup');
    await checkpoint('after-first-login', 'AFTER — arrivée cabinet existant');

    const read = async (url) => {
      const response = await ctx.request.get(apiURL + url, { failOnStatusCode: false });
      let body = null;
      try { body = await response.json(); } catch {}
      return { status: response.status(), body };
    };
    const [me, init, clinic, patients, accounting] = await Promise.all([
      read('/api/auth/me'),
      read('/api/clinics/init-status'),
      read('/api/admin/cabinet/me'),
      read('/api/patients/'),
      read('/api/accounting/treasury-hub'),
    ]);
    const state = { me, init, clinic, patients, accounting };

    if (state.me.status !== 200) throw new Error(label + ': /api/auth/me=' + state.me.status);
    if (state.me.body?.role !== persona.expectedRole) {
      throw new Error(label + ': wrong role ' + JSON.stringify(state.me.body?.role));
    }
    if (!state.me.body?.employer_id) {
      throw new Error(label + ': employee is not attached to an existing cabinet owner');
    }
    if (state.init.status !== 200 || state.init.body?.is_initialized !== true) {
      throw new Error(label + ': cabinet init state is not already configured ' + JSON.stringify(state.init));
    }
    if (state.clinic.status !== 200 || state.clinic.body?.nom_cabinet !== 'Cabinet T2 Certification') {
      throw new Error(label + ': wrong cabinet identity ' + JSON.stringify(state.clinic));
    }
    const patientsAllowed = state.patients.status >= 200 && state.patients.status < 300;
    if (patientsAllowed !== persona.allowedPatients) {
      throw new Error(label + ': patients permission mismatch ' + JSON.stringify(state.patients.status));
    }
    if (!persona.allowedPatients && state.patients.status !== 403) {
      throw new Error(label + ': restricted patients access did not fail closed with 403');
    }
    if (state.accounting.status !== 403) {
      throw new Error(label + ': accounting=false did not fail closed with 403; got ' + state.accounting.status);
    }

    const landingText = await page.locator('body').innerText();
    const roleVisible = persona.expectedRole === 'SECRETAIRE'
      ? /secr[eé]taire/i.test(landingText)
      : /dentiste|praticien/i.test(landingText);
    const clinicVisible = /Cabinet T2 Certification/i.test(landingText);
    if (!roleVisible) {
      throw new Error(label + ': role/context is not understandable on first arrival');
    }
    if (!clinicVisible) {
      throw new Error(label + ': cabinet identity is not visible on first arrival');
    }

    await page.goto(baseURL + persona.firstRoute, { waitUntil: 'domcontentloaded', timeout: 30000 });
    interactions += 1;
    await page.waitForTimeout(700);
    const firstValueText = await page.locator('body').innerText();
    if (!persona.firstValue.test(firstValueText)) {
      throw new Error(label + ': first useful route did not expose expected business value at ' + persona.firstRoute);
    }
    const firstValueMs = Date.now() - started;
    await checkpoint('first-business-action', 'FIRST VALUE — première action métier observable');

    const overflowCount = checkpoints.filter(item => item.overflow.horizontal).length;
    if (overflowCount > 0) throw new Error(label + ': horizontal overflow observed');
    if (http5xx.length) throw new Error(label + ': HTTP 5xx observed ' + JSON.stringify(http5xx));
    if (pageErrors.length) throw new Error(label + ': page errors observed ' + JSON.stringify(pageErrors));
    if (consoleErrors.length) throw new Error(label + ': console errors observed ' + JSON.stringify(consoleErrors));
    if (initStatusErrors.length) throw new Error(label + ': init-status errors observed ' + JSON.stringify(initStatusErrors));

    report.runs.push({
      label,
      persona: persona.id,
      viewport,
      landingPath,
      role: state.me.body?.role,
      clinic: state.clinic.body?.nom_cabinet,
      initialized: state.init.body?.is_initialized,
      permissionEvidence: {
        patientsStatus: state.patients.status,
        expectedAllowed: persona.allowedPatients,
        accountingStatus: state.accounting.status,
        expectedAccountingAllowed: false,
      },
      comprehensionEvidence: { roleVisible, clinicVisible },
      firstRoute: persona.firstRoute,
      firstValueMs,
      interactions,
      checkpoints,
      consoleErrors,
      pageErrors,
      http5xx,
      initStatusErrors,
    });

    await ctx.close();
  }
}

await browser.close();
report.completedAt = new Date().toISOString();
fs.writeFileSync(path.join(outDir, 'fue-b-report.json'), JSON.stringify(report, null, 2));
console.log('FIRST_USER_EXPERIENCE_B_AUDIT_PASS ' + JSON.stringify({
  productHead: report.productHead,
  runs: report.runs.map(run => ({
    label: run.label,
    landingPath: run.landingPath,
    role: run.role,
    clinic: run.clinic,
    patientsStatus: run.permissionEvidence.patientsStatus,
    accountingStatus: run.permissionEvidence.accountingStatus,
    roleVisible: run.comprehensionEvidence.roleVisible,
    clinicVisible: run.comprehensionEvidence.clinicVisible,
    firstValueMs: run.firstValueMs,
    interactions: run.interactions,
  })),
}));
