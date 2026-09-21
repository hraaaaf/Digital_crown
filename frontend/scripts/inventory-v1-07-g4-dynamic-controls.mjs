import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-dynamic-inventory');
fs.mkdirSync(outDir, { recursive: true });
const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('dynamic inventory login failed');
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patientsResponse = await api.get('/api/patients', { headers });
if (!patientsResponse.ok()) throw new Error('dynamic inventory patient list failed');
const patient = (await patientsResponse.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('dynamic inventory fixture missing');

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function inventory(page, viewport, state) {
  await page.waitForTimeout(120);
  const controls = await page.evaluate(() => {
    const selector = [
      'button','input','select','textarea','a[href]','summary','[contenteditable="true"]',
      '[role="button"]','[role="switch"]','[role="tab"]','[role="checkbox"]','[role="radio"]',
      '[role="menuitem"]','[role="menuitemradio"]','[role="option"]','[role="slider"]','[role="combobox"]',
      '[tabindex]:not([tabindex="-1"])'
    ].join(',');
    const visible = el => {
      const style = getComputedStyle(el); const rect = el.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity || 1) > 0 && rect.width > 0 && rect.height > 0;
    };
    const labelFor = el => {
      const aria = el.getAttribute('aria-label')?.trim(); if (aria) return aria;
      const by = el.getAttribute('aria-labelledby');
      if (by) { const text = by.split(/\s+/).map(id => document.getElementById(id)?.textContent?.trim() || '').filter(Boolean).join(' '); if (text) return text; }
      if (el.id) { const linked = document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.textContent?.trim(); if (linked) return linked; }
      const wrapped = el.closest('label')?.textContent?.trim(); if (wrapped) return wrapped;
      const text = el.textContent?.replace(/\s+/g,' ').trim(); if (text) return text;
      return el.getAttribute('title')?.trim() || el.getAttribute('placeholder')?.trim() || el.getAttribute('name')?.trim() || el.getAttribute('data-tour')?.trim() || '';
    };
    return [...new Set([...document.querySelectorAll(selector)].filter(visible))].map(el => ({
      tag: el.tagName.toLowerCase(), role: el.getAttribute('role') || '', type: el.getAttribute('type') || '',
      label: labelFor(el).slice(0,240), dataTour: el.getAttribute('data-tour') || '',
      disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true')
    }));
  });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const screenshot = `g4-dynamic-${viewport.width}x${viewport.height}-${state.replace(/[^a-z0-9]+/gi,'-').toLowerCase()}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false, animations: 'disabled' });
  evidence.push({ viewport, state, url: page.url(), controls, overflow, screenshot });
}

async function selectExactAmoxicillin(page) {
  const input = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').first();
  await input.fill('AMOXICILLINE');
  const results = page.locator('[data-medication-catalog-results]');
  await results.waitFor({ state: 'visible', timeout: 30000 });
  const buttons = results.locator('button[data-presentation-id]');
  for (let i = 0; i < await buttons.count(); i += 1) {
    const lines = (await buttons.nth(i).innerText()).split('\n').map(v => v.trim().toUpperCase()).filter(Boolean);
    if (lines.includes('AMOXICILLINE') || lines.includes('AMOXICILLIN')) { await buttons.nth(i).click(); return; }
  }
  throw new Error('amoxicillin presentation missing');
}

for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);
  const base = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=`;

  await page.goto(base + 'ordonnance', { waitUntil: 'networkidle', timeout: 90000 });
  const manualDrug = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').first();
  await manualDrug.fill('G4 MANUAL');
  await page.waitForTimeout(650);
  await manualDrug.press('Escape');
  const formTrigger = page.locator('button[title="Choisir la forme manuellement"]:visible').first();
  await formTrigger.waitFor({ state: 'visible', timeout: 10000 });
  if (await formTrigger.isDisabled()) throw new Error('manual form trigger unexpectedly disabled');
  await formTrigger.dispatchEvent('click');
  await page.locator('[data-g4-manual-form-picker]').waitFor({ state: 'visible', timeout: 10000 });
  await inventory(page, viewport, 'ordonnance-form-picker');
  await page.keyboard.press('Escape');

  await page.getByRole('button', { name: 'Renseigner', exact: true }).click();
  await page.getByLabel('Poids explicite en kilogrammes').waitFor({ state: 'visible' });
  await inventory(page, viewport, 'ordonnance-clinical-context');
  await page.getByRole('button', { name: 'Réduire', exact: true }).first().click();

  await selectExactAmoxicillin(page);
  const ie = page.locator('[data-ie-prophylaxis-rule="c2"]');
  await ie.getByRole('button', { name: 'Évaluer', exact: true }).click();
  await page.getByLabel('Date prévue du geste').waitFor({ state: 'visible' });
  await inventory(page, viewport, 'ordonnance-ie-expanded');

  await page.getByRole('button', { name: /Ajouter une ligne/i }).click();
  await inventory(page, viewport, 'ordonnance-two-lines');

  await page.goto(base + 'certificat', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: /Arrêt de travail/i }).click();
  await page.getByLabel('Durée du repos en jours').waitFor({ state: 'visible' });
  await inventory(page, viewport, 'certificate-work-stop');
  await page.getByRole('button', { name: /Certificat médical/i }).click();
  await page.getByLabel(/Contenu du certificat médical/i).waitFor({ state: 'visible' });
  await inventory(page, viewport, 'certificate-free');

  await page.goto(base + 'echeancier', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Nouveau plan', exact: true }).click();
  const amountLabel = page.getByText('Montant Total Prévu (MAD)', { exact: true }).first();
  await amountLabel.locator('..').locator('input').fill('1000');
  await page.getByText('Avance (MAD)', { exact: true }).locator('..').locator('input').fill('200');
  await page.getByText('Nbre Mensualités', { exact: true }).locator('..').locator('input').fill('2');
  await page.getByRole('button', { name: /Générer le tableau des échéances/i }).click();
  await page.getByDisplayValue('Mensualité 1').waitFor({ state: 'visible' });
  await inventory(page, viewport, 'installment-generated-draft');

  await page.goto(base + 'honoraires', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: /Bridge & Prothèses/i }).click();
  await page.getByRole('button', { name: 'Q1', exact: true }).waitFor({ state: 'visible' });
  await inventory(page, viewport, 'honoraires-group-mode');
  await page.getByRole('button', { name: 'Q1', exact: true }).click();
  await page.getByRole('button', { name: 'Bridge', exact: true }).waitFor({ state: 'visible' });
  await inventory(page, viewport, 'honoraires-group-selected');

  await page.getByRole('button', { name: /Soins Ciblés/i }).click();
  const dent11 = page.getByRole('button', { name: /Dent 11,/i });
  // The odontogram is SVG-backed; Chromium pointer hit-testing can land on an
  // inner shape instead of the accessible tooth control. Exercise the same
  // real browser action through the keyboard contract used by the deep probe.
  await dent11.focus();
  await page.keyboard.press('Enter');
  await page.getByText('Dent 11', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  await inventory(page, viewport, 'honoraires-treatment-selector');
  const toothTitle = page.getByText('Dent 11', { exact: true });
  const selector = toothTitle.locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
  await selector.locator('button').first().click();

  await page.getByRole('button', { name: /Procéder à l'Encaissement/i }).click();
  await page.getByText('Encaissement', { exact: true }).waitFor({ state: 'visible' });
  await inventory(page, viewport, 'honoraires-treasury');
  await page.getByRole('button', { name: /Global \/ Planifié/i }).click();
  await page.getByRole('button', { name: /Nouvelle Échéance/i }).click();
  await page.getByDisplayValue('Versement 1').waitFor({ state: 'visible' });
  await inventory(page, viewport, 'honoraires-treasury-installment');
  await page.getByRole('button', { name: 'Fermer', exact: true }).click();

  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=archives`, { waitUntil: 'networkidle', timeout: 90000 });
  const actionButtons = page.locator('button[aria-label^="Actions du document "]');
  if (await actionButtons.count()) {
    await actionButtons.first().click();
    await page.locator('[data-document-action-menu]').first().waitFor({ state: 'visible', timeout: 10000 });
    await inventory(page, viewport, 'history-action-menu');
  }

  await context.close();
}

await browser.close();
await api.dispose();

const dynamicSignatures = new Map();
for (const row of evidence) {
  for (const control of row.controls) {
    const key = [control.tag, control.role, control.type, control.label, control.dataTour].join('|');
    if (!dynamicSignatures.has(key)) dynamicSignatures.set(key, { ...control, states: [] });
    dynamicSignatures.get(key).states.push(row.state);
  }
}
const semantic = [...dynamicSignatures.values()].map(row => ({ ...row, states: [...new Set(row.states)].sort() }))
  .sort((a,b) => a.label.localeCompare(b.label) || a.tag.localeCompare(b.tag));
const failures = evidence.filter(row => row.overflow).map(row => ({ state: row.state, viewport: row.viewport, reason: 'overflow' }));
const summary = {
  status: failures.length ? 'FAIL' : 'PASS',
  stateRuns: evidence.length,
  semanticControlsObserved: semantic.length,
  failures,
};
fs.writeFileSync(path.join(outDir, 'dynamic-inventory.json'), JSON.stringify({ summary, semantic, evidence }, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_DYNAMIC_INVENTORY ' + JSON.stringify(summary));
if (failures.length) process.exit(1);
