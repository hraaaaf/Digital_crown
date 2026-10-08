import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD required');

const baseURL = 'http://127.0.0.1:5173';
const outDir = path.resolve('../artifacts/t2-browser/first-user-experience');
fs.mkdirSync(outDir, { recursive: true });

const profiles = [
  { label: 'mobile', email: 't2-setup-390@cabinet.ma', viewport: { width: 390, height: 844 } },
  { label: 'desktop', email: 't2-setup-1280@cabinet.ma', viewport: { width: 1280, height: 900 } },
];

const browser = await chromium.launch({ headless: true });
const report = {
  productHead: process.env.PRODUCT_HEAD || null,
  startedAt: new Date().toISOString(),
  protocol: 'docs/audits/FIRST_USER_EXPERIENCE_PROMPT.md',
  profiles: [],
};

for (const profile of profiles) {
  fs.mkdirSync(path.join(outDir, profile.label), { recursive: true });
  const ctx = await browser.newContext({ viewport: profile.viewport, colorScheme: 'light' });
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
    const tMs = Date.now() - started;
    if (res.status() >= 500) http5xx.push({ tMs, status: res.status(), url: res.url() });
    if (res.url().includes('/api/clinics/init-status') && res.status() >= 400) {
      initStatusErrors.push({ tMs, status: res.status(), url: res.url() });
    }
  });

  async function checkpoint(id, title) {
    await page.waitForTimeout(120);
    const overflow = await page.evaluate(() => ({
      viewportWidth: window.innerWidth,
      bodyWidth: document.body.scrollWidth,
      htmlWidth: document.documentElement.scrollWidth,
      horizontal: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > window.innerWidth + 1,
    }));
    const filename = `${String(checkpoints.length + 1).padStart(2, '0')}-${id}.png`;
    await page.screenshot({ path: path.join(outDir, profile.label, filename), fullPage: true });
    checkpoints.push({
      id,
      title,
      path: page.url().replace(baseURL, ''),
      url: page.url(),
      tMs: Date.now() - started,
      interactions,
      overflow,
      screenshot: path.join(profile.label, filename),
    });
  }

  async function click(locator) {
    await locator.click();
    interactions += 1;
  }
  async function fill(locator, value) {
    await locator.fill(value);
    interactions += 1;
  }

  await page.goto(baseURL + '/login', { waitUntil: 'networkidle', timeout: 90000 });
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.reload({ waitUntil: 'networkidle', timeout: 90000 });
  await checkpoint('A-login-empty', 'Login vierge');

  await fill(page.getByPlaceholder('nom@cabinet.com'), profile.email);
  await fill(page.getByPlaceholder('••••••••'), password);
  await click(page.getByRole('button', { name: 'Se connecter', exact: true }));
  await page.waitForURL('**/setup', { timeout: 20000 });
  await page.locator('[data-flow-step="1"]').waitFor({ state: 'visible', timeout: 20000 });
  await checkpoint('B-setup-entry', 'Redirection Première configuration');

  await checkpoint('C-step1-identity-before', 'Setup 1 — Identité BEFORE');
  await click(page.getByRole('button', { name: /Continuer/i }));
  if ((await page.locator('[data-flow-step="1"]').count()) !== 1) throw new Error(profile.label + ': setup advanced despite missing identity');
  await checkpoint('C-step1-validation', 'Setup 1 — Validation requise');

  const suffix = profile.label === 'mobile' ? 'Mobile' : 'Desktop';
  await fill(page.getByPlaceholder(/Cabinet Dentaire|Centre Dentaire/), 'Cabinet FUE ' + suffix);
  await fill(page.getByPlaceholder('Étage, Résidence, Rue, Ville...'), 'Casablanca — Audit FUE');
  await fill(page.getByPlaceholder('Dr. Jean Dupont'), 'Dr FUE ' + suffix);
  await checkpoint('C-step1-identity-filled', 'Setup 1 — Identité AFTER');
  await click(page.getByRole('button', { name: /Continuer/i }));

  const setupSteps = [
    ['D-step2-specialties', 'Setup 2 — Spécialités', 2],
    ['E-step3-contacts', 'Setup 3 — Coordonnées', 3],
    ['F-step4-qr', 'Setup 4 — QR / partage', 4],
    ['G-step5-design', 'Setup 5 — Design documentaire', 5],
    ['H-step6-theme', 'Setup 6 — Thème / identité', 6],
    ['I-step7-confirmation', 'Setup 7 — Confirmation', 7],
  ];

  for (const [id, title, step] of setupSteps) {
    await page.locator('[data-flow-step="' + step + '"]').waitFor({ state: 'visible', timeout: 10000 });
    await checkpoint(id, title);
    if (step < 7) await click(page.getByRole('button', { name: /Continuer/i }));
  }

  const setupCompleteBefore = Date.now() - started;
  await click(page.getByRole('button', { name: /Finaliser l.Installation/i }));
  await page.waitForURL('**/dashboard', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  await page.locator('[data-tour="quick-action-new-patient"]').waitFor({ state: 'visible', timeout: 10000 });
  const postSetupInitErrors = initStatusErrors.filter(item => item.tMs >= setupCompleteBefore);
  if (new URL(page.url()).pathname !== '/dashboard') {
    throw new Error(profile.label + ': setup handoff did not remain stable on dashboard: ' + page.url());
  }
  if (postSetupInitErrors.length > 0) {
    throw new Error(profile.label + ': setup handoff produced init-status errors: ' + JSON.stringify(postSetupInitErrors));
  }
  const setupCompleteMs = Date.now() - started;
  await checkpoint('J-dashboard-first-arrival', 'Dashboard après configuration');

  const quick = page.getByRole('button', { name: 'Ajout rapide' });
  await quick.waitFor({ state: 'visible', timeout: 15000 });
  await checkpoint('K-discover-new-patient', 'Découverte action Nouveau Patient');
  await click(quick);
  const newPatient = page.getByRole('menuitem', { name: /Nouveau Patient/i });
  await newPatient.waitFor({ state: 'visible', timeout: 5000 });
  await checkpoint('K-new-patient-menu', 'Menu Ajout rapide ouvert');
  await click(newPatient);
  await page.waitForURL('**/patients/new', { timeout: 10000 });
  // URL navigation can finish before the lazy-loaded patient form mounts on mobile.
  // Require actual visible content before taking the BEFORE evidence screenshot.
  await page.getByRole('heading', { name: 'Nouveau Patient' }).waitFor({ state: 'visible', timeout: 15000 });
  await page.locator('input[name="nom"]').waitFor({ state: 'visible', timeout: 15000 });
  await page.locator('input[name="prenom"]').waitFor({ state: 'visible', timeout: 15000 });
  await checkpoint('L-patient-form-empty', 'Création premier patient BEFORE');

  const dossier = 'FUE-' + (profile.label === 'mobile' ? '390' : '1280');
  await fill(page.locator('input[name="nom"]'), 'FIRSTUSE');
  await fill(page.locator('input[name="prenom"]'), suffix);
  await fill(page.locator('input[name="numero_dossier"]'), dossier);
  await page.getByText(/Numéro disponible/i).waitFor({ state: 'visible', timeout: 10000 });
  await fill(page.locator('input[name="date_naissance"]'), '1990-01-01');
  await page.locator('select[name="sexe"]').selectOption('F');
  interactions += 1;
  await checkpoint('L-patient-form-filled', 'Création premier patient AFTER saisie');

  await click(page.getByRole('button', { name: 'Créer le dossier', exact: true }));
  await page.waitForURL(/\/patients\/\d+(?:\?|$)/, { timeout: 20000 });
  await page.waitForFunction(
    ({ nom, prenom }) => {
      const text = document.body?.innerText || '';
      return text.includes(nom) && text.includes(prenom);
    },
    { nom: 'FIRSTUSE', prenom: suffix },
    { timeout: 15000 }
  );
  const firstValueMs = Date.now() - started;
  await checkpoint('M-first-value-patient-record', 'FIRST VALUE — Dossier patient visible');

  const firstValueText = await page.locator('body').innerText();
  if (!/FIRSTUSE/i.test(firstValueText) || !new RegExp(suffix, 'i').test(firstValueText)) {
    throw new Error(profile.label + ': created patient identity not visible on dossier after explicit render wait');
  }

  report.profiles.push({
    label: profile.label,
    viewport: profile.viewport,
    setupCompleteBeforeMs: setupCompleteBefore,
    setupCompleteMs,
    firstValueMs,
    interactions,
    checkpointCount: checkpoints.length,
    checkpoints,
    consoleErrors,
    pageErrors,
    http5xx,
    initStatusErrors,
  });

  await ctx.close();
}

await browser.close();
report.completedAt = new Date().toISOString();
fs.writeFileSync(path.join(outDir, 'fue-report.json'), JSON.stringify(report, null, 2));
console.log('FIRST_USER_EXPERIENCE_AUDIT_PASS ' + JSON.stringify({
  productHead: report.productHead,
  profiles: report.profiles.map(p => ({
    label: p.label,
    viewport: p.viewport,
    setupCompleteMs: p.setupCompleteMs,
    firstValueMs: p.firstValueMs,
    interactions: p.interactions,
    checkpoints: p.checkpointCount,
    http5xx: p.http5xx.length,
    consoleErrors: p.consoleErrors.length,
    pageErrors: p.pageErrors.length,
    initStatusErrors: p.initStatusErrors.length,
  })),
}));
