import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/v1-07-g4-browser-inventory');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

const viewports = [
  { width: 390, height: 844 },
  { width: 1280, height: 900 },
];

const documentTabs = [
  ['ordonnance', 'Ordonnance'],
  ['certificat', 'Certificat'],
  ['devis', 'Devis'],
  ['honoraires', 'Note Honoraires'],
  ['echeancier', 'Suivi Paiement'],
  ['libre', 'Document Libre'],
];

const assistants = [
  'Examen clinique complet',
  'Parodontologie',
  'Endodontie',
  'Prothèse & esthétique',
  'Chirurgie orale',
  'Pédodontie',
  'Orthodontie (ODF)',
  'Occlusodontie & ATM',
  'Médecine buccale',
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error(`G4 inventory login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };

const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error(`G4 inventory patients failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find((row) => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('G4 inventory fixture patient T2-0001 missing');

await api.patch(`/api/patients/${patient.id}/ortho`, {
  headers,
  data: { is_ortho_active: true },
});

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

function safeSlug(value) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

async function inventorySurface(page, viewport, surface) {
  await page.waitForTimeout(250);
  const controls = await page.evaluate(() => {
    const selectors = [
      'button',
      'input',
      'select',
      'textarea',
      'a[href]',
      'summary',
      '[contenteditable="true"]',
      '[role="button"]',
      '[role="switch"]',
      '[role="tab"]',
      '[role="checkbox"]',
      '[role="radio"]',
      '[role="menuitem"]',
      '[role="option"]',
      '[role="slider"]',
      '[role="combobox"]',
      '[tabindex]:not([tabindex="-1"])',
    ].join(',');

    const visible = (el) => {
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.display !== 'none'
        && style.visibility !== 'hidden'
        && Number(style.opacity || 1) > 0
        && rect.width > 0
        && rect.height > 0;
    };

    const labelFor = (el) => {
      const aria = el.getAttribute('aria-label')?.trim();
      if (aria) return aria;
      const labelledBy = el.getAttribute('aria-labelledby');
      if (labelledBy) {
        const text = labelledBy.split(/\s+/).map((id) => document.getElementById(id)?.textContent?.trim() || '').filter(Boolean).join(' ');
        if (text) return text;
      }
      if (el.id) {
        const linked = document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.textContent?.trim();
        if (linked) return linked;
      }
      const wrapped = el.closest('label')?.textContent?.trim();
      if (wrapped) return wrapped;
      const text = el.textContent?.replace(/\s+/g, ' ').trim();
      if (text) return text;
      return el.getAttribute('title')?.trim()
        || el.getAttribute('placeholder')?.trim()
        || el.getAttribute('name')?.trim()
        || el.getAttribute('data-tour')?.trim()
        || '';
    };

    const nodes = [...document.querySelectorAll(selectors)].filter(visible);
    const unique = [...new Set(nodes)];
    return unique.map((el, index) => ({
      index,
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      type: el.getAttribute('type') || '',
      label: labelFor(el).slice(0, 240),
      ariaLabel: el.getAttribute('aria-label') || '',
      title: el.getAttribute('title') || '',
      placeholder: el.getAttribute('placeholder') || '',
      name: el.getAttribute('name') || '',
      dataTour: el.getAttribute('data-tour') || '',
      disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true'),
      checked: 'checked' in el ? Boolean(el.checked) : null,
      value: 'value' in el ? String(el.value ?? '').slice(0, 120) : '',
      href: el.getAttribute('href') || '',
    }));
  });

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  const shot = `g4-inventory-${safeSlug(surface)}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: true, animations: 'disabled' });
  return { surface, url: page.url(), controls, controlCount: controls.length, overflow, screenshot: shot };
}

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);

  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('response', (response) => {
    if (response.status() >= 500) http5xx.push({ url: response.url(), status: response.status() });
  });

  const patientUrl = `http://127.0.0.1:5173/patients/${patient.id}`;
  const surfaces = [];

  await page.goto(patientUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Prochaine action', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  surfaces.push(await inventorySurface(page, viewport, 'overview'));

  await page.goto(`${patientUrl}?tab=clinical`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Espace Clinique', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  surfaces.push(await inventorySurface(page, viewport, 'clinical-odontogram'));

  const examsButton = page.getByRole('button', { name: 'Examens', exact: true });
  if (await examsButton.count()) {
    await examsButton.click();
    await page.getByText('Examens structurés', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    surfaces.push(await inventorySurface(page, viewport, 'clinical-exams'));

    for (const assistant of assistants) {
      const launcher = page.getByRole('button').filter({ hasText: assistant }).first();
      await launcher.waitFor({ state: 'visible', timeout: 15000 });
      await launcher.click();
      await page.getByText(`Examen · ${assistant}`, { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
      surfaces.push(await inventorySurface(page, viewport, `assistant-${assistant}`));
      const cancel = page.getByRole('button', { name: 'Annuler', exact: true }).last();
      if (await cancel.count()) {
        await cancel.click();
      } else {
        await page.goto(`${patientUrl}?tab=clinical`, { waitUntil: 'networkidle', timeout: 90000 });
        await page.getByRole('button', { name: 'Examens', exact: true }).click();
      }
      await page.waitForTimeout(120);
    }
  }

  for (const radioTab of ['media', 'rvg', 'panoramic', 'cephalo']) {
    await page.goto(`${patientUrl}?tab=radiology&radioTab=${radioTab}`, { waitUntil: 'networkidle', timeout: 90000 });
    await page.getByRole('button', { name: 'Imagerie', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    surfaces.push(await inventorySurface(page, viewport, `imaging-${radioTab}`));
  }

  for (const [slug, label] of documentTabs) {
    await page.goto(`${patientUrl}?tab=admin&documentTab=${slug}`, { waitUntil: 'networkidle', timeout: 90000 });
    const studio = page.getByLabel('Types de documents');
    await studio.waitFor({ state: 'visible', timeout: 30000 });
    await studio.getByRole('button', { name: label, exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    surfaces.push(await inventorySurface(page, viewport, `documents-${slug}`));

    if (slug === 'devis' || slug === 'honoraires') {
      const plan = page.getByTestId('document-plan-of-care');
      await plan.waitFor({ state: 'visible', timeout: 30000 });

      const continueButton = page.getByRole('button', { name: /Continuer vers les prestations/i });
      if (!(await continueButton.count())) {
        await plan.getByRole('button').filter({ hasText: 'Plan de soins' }).first().click();
        await continueButton.waitFor({ state: 'visible', timeout: 10000 });
      }

      const groupMode = page.getByRole('button', { name: 'Bridge & Prothèses', exact: true });
      const individualMode = page.getByRole('button', { name: 'Soins Ciblés (1 Dent)', exact: true });
      const tooth11 = page.getByRole('button', { name: /^Dent 11(?:,|$)/ }).first();

      await groupMode.click();
      await tooth11.waitFor({ state: 'visible', timeout: 30000 });
      if (await tooth11.getAttribute('aria-pressed') === 'true') {
        await tooth11.focus();
        await tooth11.press('Enter');
      }
      await individualMode.click();
      await page.waitForTimeout(200);

      await plan.screenshot({
        path: path.join(outDir, `g4-plan-${slug}-schema-open-${viewport.width}x${viewport.height}.png`),
        animations: 'disabled',
      });

      await groupMode.click();
      await tooth11.focus();
      await tooth11.press('Enter');
      await page.waitForFunction(
        () => [...document.querySelectorAll('[role="button"][aria-label^="Dent 11"]')]
          .some((el) => el.getAttribute('aria-pressed') === 'true'),
        null,
        { timeout: 10000 },
      );
      await page.waitForTimeout(200);

      await plan.screenshot({
        path: path.join(outDir, `g4-plan-${slug}-tooth-11-selected-${viewport.width}x${viewport.height}.png`),
        animations: 'disabled',
      });
    }
  }

  await page.goto(`${patientUrl}?tab=archives`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByPlaceholder("Rechercher dans l'historique...").waitFor({ state: 'visible', timeout: 30000 });
  surfaces.push(await inventorySurface(page, viewport, 'documents-history'));

  await page.goto(`${patientUrl}?tab=finances`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Facturé', { exact: true }).first().waitFor({ state: 'visible', timeout: 30000 });
  surfaces.push(await inventorySurface(page, viewport, 'finances'));

  evidence.push({ viewport, surfaces, pageErrors, http5xx });
  await context.close();
}

await browser.close();
await api.dispose();

const allRows = evidence.flatMap((entry) => entry.surfaces.map((surface) => ({
  viewport: `${entry.viewport.width}x${entry.viewport.height}`,
  surface: surface.surface,
  controlCount: surface.controlCount,
  overflow: surface.overflow,
  screenshot: surface.screenshot,
  controls: surface.controls,
})));

const failures = evidence.flatMap((entry) => [
  ...entry.pageErrors.map((error) => ({ viewport: entry.viewport, reason: 'pageerror', error })),
  ...entry.http5xx.map((response) => ({ viewport: entry.viewport, reason: 'http5xx', ...response })),
  ...entry.surfaces.filter((surface) => surface.overflow).map((surface) => ({ viewport: entry.viewport, surface: surface.surface, reason: 'overflow' })),
  ...entry.surfaces.filter((surface) => surface.controlCount === 0).map((surface) => ({ viewport: entry.viewport, surface: surface.surface, reason: 'zero-controls' })),
]);

const uniqueSignatures = new Map();
for (const row of allRows) {
  for (const control of row.controls) {
    const signature = [row.surface, control.tag, control.role, control.type, control.label, control.dataTour].join('|');
    if (!uniqueSignatures.has(signature)) {
      uniqueSignatures.set(signature, {
        surface: row.surface,
        tag: control.tag,
        role: control.role,
        type: control.type,
        label: control.label,
        dataTour: control.dataTour,
        disabled: control.disabled,
      });
    }
  }
}

const inventory = [...uniqueSignatures.values()].sort((a, b) =>
  a.surface.localeCompare(b.surface) || a.label.localeCompare(b.label)
);

const markdown = [
  '# V1-07 G4 browser control inventory',
  '',
  `Patient fixture: T2-0001 (id ${patient.id})`,
  `Generated controls: ${inventory.length} unique surface/control signatures`,
  `Viewports: ${viewports.map((v) => `${v.width}x${v.height}`).join(', ')}`,
  '',
  '| Surface | Tag/role | Label | State |',
  '| --- | --- | --- | --- |',
  ...inventory.map((row) => `| ${row.surface} | ${row.tag}${row.role ? ` / ${row.role}` : ''}${row.type ? ` / ${row.type}` : ''} | ${(row.label || '(sans libellé)').replace(/\|/g, '\\\\|').replace(/\n/g, ' ')} | ${row.disabled ? 'disabled' : 'enabled'} |`),
  '',
  'This artifact is an enumeration baseline, not G4 certification. Each enabled mutation/control must still be mapped to a Playwright action and an observable expected result/refusal.',
  '',
].join('\n');

const summary = {
  status: failures.length ? 'FAIL' : 'PASS',
  patientId: patient.id,
  viewports,
  surfaceRuns: allRows.length,
  uniqueControlSignatures: inventory.length,
  failures,
};

fs.writeFileSync(path.join(outDir, 'inventory.json'), JSON.stringify({ summary, inventory, evidence }, null, 2));
fs.writeFileSync(path.join(outDir, 'inventory.md'), markdown);
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));

console.log('G4_BROWSER_INVENTORY', JSON.stringify(summary));
if (failures.length) process.exit(1);
