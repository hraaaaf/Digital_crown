import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-finances-actions');
fs.mkdirSync(outDir, { recursive: true });

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('finance login failed');
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };

const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error('finance patient list failed');
const patient = (await patients.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('finance fixture patient missing');

async function apiPayments() {
  const r = await api.get(`/api/accounting/payments/patient/${patient.id}`, { headers });
  if (!r.ok()) throw new Error(`payments reload failed: ${r.status()}`);
  return await r.json();
}
async function apiBilling() {
  const r = await api.get(`/api/accounting/actes-billing/patient/${patient.id}`, { headers });
  if (!r.ok()) throw new Error(`billing reload failed: ${r.status()}`);
  return await r.json();
}

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);
  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('response', response => {
    if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() });
  });

  const baselinePayments = await apiPayments();

  try {
    await page.goto('http://127.0.0.1:5173/dashboard', { waitUntil: 'networkidle', timeout: 90000 });
    const patientsLink = page.getByRole('link', { name: 'Patients', exact: true }).first();
    if (!(await patientsLink.isVisible().catch(() => false))) {
      const menuButton = page.getByRole('button', { name: /menu|navigation/i }).first();
      if (await menuButton.isVisible().catch(() => false)) await menuButton.click();
    }
    await patientsLink.waitFor({ state: 'visible', timeout: 15000 });
    await patientsLink.click();
    await page.waitForURL(url => url.pathname === '/patients', { timeout: 15000 });

    const patientSearch = page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
    await patientSearch.fill('T2-0001');
    const patientRow = page.getByRole('button').filter({ hasText: 'T2-0001' }).first();
    await patientRow.waitFor({ state: 'visible', timeout: 15000 });
    await patientRow.click();
    await page.waitForURL(url => url.pathname === `/patients/${patient.id}`, { timeout: 15000 });

    const financeTab = page.getByRole('button', { name: /^(Finances|Finance)$/i }).first();
    await financeTab.waitFor({ state: 'visible', timeout: 15000 });
    await financeTab.click();
    await page.waitForURL(url => url.pathname === `/patients/${patient.id}` && url.searchParams.get('tab') === 'finances', { timeout: 15000 });
    await page.getByText('Facturé', { exact: true }).first().waitFor({ state: 'visible', timeout: 30000 });

    await page.screenshot({
      path: path.join(outDir, `g4-finances-${viewport.width}x${viewport.height}-bureau-entry.png`),
      fullPage: false,
      animations: 'disabled',
    });
  } catch (error) {
    const shot = `g4-finances-${viewport.width}x${viewport.height}-bureau-error.png`;
    await page.screenshot({ path: path.join(outDir, shot), fullPage: false, animations: 'disabled' }).catch(() => {});
    const visibleText = await page.locator('body').innerText().catch(() => '');
    fs.writeFileSync(
      path.join(outDir, `g4-finances-${viewport.width}x${viewport.height}-bureau-error.json`),
      JSON.stringify({ viewport, url: page.url(), error: String(error), visibleText: visibleText.slice(0, 2500), pageErrors, http5xx, shot }, null, 2),
    );
    throw error;
  }

  const quickOpen = page.getByRole('button', { name: /Enregistrer un paiement/i });
  await quickOpen.click();
  const quickDialog = page.getByRole('dialog', { name: 'Saisir un Paiement' });
  await quickDialog.waitFor({ state: 'visible', timeout: 10000 });
  const quickSubmit = quickDialog.getByRole('button', { name: 'Encaisser', exact: true });
  if (!(await quickSubmit.isDisabled())) throw new Error('quick payment submit enabled without amount/method');
  await quickDialog.getByPlaceholder('0.00').fill('123.45');
  await quickDialog.getByRole('button', { name: 'Carte', exact: true }).click();
  await quickDialog.getByPlaceholder(/Acompte traitement ortho/i).fill('G4 quickpay browser proof');
  if (await quickSubmit.isDisabled()) throw new Error('quick payment submit stayed disabled after explicit inputs');
  const quickRespPromise = page.waitForResponse(r => r.url().includes('/api/accounting/payments') && r.request().method() === 'POST', { timeout: 15000 });
  await quickSubmit.click();
  const quickResp = await quickRespPromise;
  if (!quickResp.ok()) throw new Error(`quick payment persistence failed: ${quickResp.status()}`);
  await quickDialog.waitFor({ state: 'detached', timeout: 10000 });

  const afterQuick = await apiPayments();
  if (afterQuick.length !== baselinePayments.length + 1) throw new Error('quick payment count did not increment exactly once');
  const quickPersisted = afterQuick.find(p => Math.abs(Number(p.amount) - 123.45) < 0.005 && p.payment_method === 'CARTE' && p.notes === 'G4 quickpay browser proof');
  if (!quickPersisted) throw new Error('quick payment exact persisted row missing');

  await page.reload({ waitUntil: 'networkidle' });
  await page.getByText('Actes & Paiements', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  let billing = await apiBilling();
  const unpaid = billing.find(a => Number(a.remaining_due) > 200);
  if (!unpaid) throw new Error('no unpaid billing act available for finance action proof');

  const row = page.getByText(unpaid.libelle, { exact: true }).locator('xpath=ancestor::tr[1]');
  await row.getByRole('button', { name: 'Payer', exact: true }).click();
  await page.getByText('Paiement acte', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const amountInput = page.locator('input[type="number"]').last();
  await amountInput.fill('111');
  await page.getByRole('button', { name: 'Virement', exact: true }).last().click();
  const acteSubmit = page.getByRole('button', { name: 'Encaisser', exact: true }).last();
  const acteRespPromise = page.waitForResponse(r => r.url().includes('/api/accounting/payments') && r.request().method() === 'POST', { timeout: 15000 });
  await acteSubmit.click();
  const acteResp = await acteRespPromise;
  if (!acteResp.ok()) throw new Error(`act-specific payment failed: ${acteResp.status()}`);
  const actePayment = await acteResp.json();
  if (Number(actePayment.acte_id) !== Number(unpaid.id) || Math.abs(Number(actePayment.amount) - 111) >= 0.005 || actePayment.payment_method !== 'VIREMENT') {
    throw new Error('act-specific payment response mismatch');
  }

  await page.reload({ waitUntil: 'networkidle' });
  billing = await apiBilling();
  const updated = billing.find(a => Number(a.id) === Number(unpaid.id));
  if (!updated) throw new Error('paid act disappeared from billing');
  const expectedRemaining = Number(unpaid.remaining_due) - 111;
  if (Math.abs(Number(updated.remaining_due) - expectedRemaining) >= 0.01) throw new Error('act remaining due did not persist exact partial payment');

  const updatedRow = page.getByText(unpaid.libelle, { exact: true }).locator('xpath=ancestor::tr[1]');
  await updatedRow.getByRole('button', { name: 'Plan', exact: true }).click();
  const planDialog = page.getByRole('dialog').filter({ hasText: "Plan d'échéances" });
  await planDialog.waitFor({ state: 'visible', timeout: 10000 });
  const createPlan = planDialog.getByRole('button', { name: 'Créer le plan', exact: true });
  if (!(await createPlan.isDisabled())) throw new Error('installment create enabled before amounts');

  const remainder = Number(updated.remaining_due);
  const firstAmount = Math.floor((remainder / 2) * 100) / 100;
  const secondAmount = Math.round((remainder - firstAmount) * 100) / 100;
  await planDialog.getByLabel('Montant du versement 1').fill(String(firstAmount));
  await planDialog.getByLabel('Montant du versement 2').fill(String(secondAmount));
  if (await createPlan.isDisabled()) throw new Error('installment create stayed disabled after exact coverage');
  const planRespPromise = page.waitForResponse(r => r.url().includes('/api/installments/') && r.request().method() === 'POST', { timeout: 15000 });
  await createPlan.click();
  const planResp = await planRespPromise;
  if (!planResp.ok()) throw new Error(`installment plan persistence failed: ${planResp.status()}`);
  const planBody = await planResp.json();
  if (Number(planBody.acte_id) !== Number(unpaid.id) || Math.abs(Number(planBody.total_amount) - remainder) >= 0.01 || planBody.installments?.length !== 2) {
    throw new Error('installment plan persisted payload mismatch');
  }

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const shot = `g4-finances-${viewport.width}x${viewport.height}-final.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: false, animations: 'disabled' });
  if (overflow) throw new Error('finance horizontal overflow');
  if (pageErrors.length) throw new Error('finance page errors: ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('finance HTTP5xx: ' + JSON.stringify(http5xx));

  evidence.push({
    viewport,
    quickPaymentId: quickPersisted.id,
    actId: unpaid.id,
    actPaymentId: actePayment.id,
    installmentPlanId: planBody.id,
    remainder,
    shot,
  });
  await context.close();
}

await browser.close();
await api.dispose();
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify({ status: 'PASS', evidence }, null, 2));
console.log('G4_FINANCES_ACTIONS ' + JSON.stringify({ status: 'PASS', viewports: evidence.length }));
