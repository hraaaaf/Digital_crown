import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/v15-02-3-photo-ui-after');
fs.mkdirSync(outDir, { recursive: true });

const viewports = [
  { label: 'mobile', width: 390, height: 844 },
  { label: 'desktop', width: 1280, height: 900 },
];

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error(`02.3 AFTER login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };

const patientsResponse = await api.get('/api/patients/', { headers });
if (!patientsResponse.ok()) throw new Error(`02.3 AFTER patients failed: ${patientsResponse.status()}`);
const patients = await patientsResponse.json();
const patient = patients.find(row => row.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('02.3 AFTER requires a patient fixture');

// Distinct high-contrast synthetic portraits (no patient photos): ensure visual proof is legible at avatar size.
const sampleA = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAIAAABt+uBvAAABsElEQVR42u3a0U0DQQyE4YtFB3RCBYhukKgAiSdaQKKbiF54pgcqSHS3a3vWvn9fI8XjT3OrRMnl9/1p49w+BgFAAAEEEEAAAQQQB6CB87BCiMe371sv/X29arNdVN/F7qAshSUAGqARMqUCTdJImKyijvu76YEi9skxCn/EEtYIfdysuk70FD4o6oDS7tHQWdZAJ3Si9dCJm8sdlA6kqk/QdBqUC6StT0QGGgQQQGWAVriA3JPQIIAAAggggAACCKD5I/8dPSIJDQIIoEpAK1xDvhloUDqQtkTu02mQAkhVooi5ViirZKKVS5w8iztICpRTotApGf9y/bw+x735x8tPaPgooFCUTCx/IAlNHJMnkJwmgskHaCkaXyZrrOOSzRrruCS03jrzOa29zmRaO4POTGY7ic5wcjuPzlh+vs27AlWvz8AWNMgPqEd9ju5Cg5yAOtXn0EY0CCCA9ED9LqD9e9EggAACCCCAAAIIoDsn+h8UqrNnLxoEEEBLAPW7hnZuRIP8gDqVaP8uNMgVqEeJDm1Bg7yBqpfoaH5LmFFXZ/wRq2g0ltmS59XS2bbtH1pkla0CIqybAAAAAElFTkSuQmCC',
  'base64',
);
const sampleB = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAIAAABt+uBvAAABqklEQVR42u3a21HDQAyFYUfZEkIVNJCmeKIOHugqDVBFamCSCtZjr3VZyf++EqKjb453YJLL7et34fSPQAAQQAABBBBAAAHEAWjgtBlCPL//ej/6+Pk8KdAKSu9lIVhtWpreLzoztRQ0gUySS8fo3eKBLPbxMWoZaTwfN8mr4zOFPxTjgNzuUdNZUkDHdKLU0LGbyx3kDhRVH6PpNMgXKLY+FhloEEAApQGa4QJST0KDAAIIIIAAAggggI6f8M/RLZLQIIAAygQ0wzWkm4EGuQPFlkh9Og2KAIoqkcVcSZQ1ZKKkS+w8izsoFMinRKZTmkP6y/3f7v1fj6tpfisgU5TeIAuslpemN1qXqdWgsWNqlWgsmKSkjmI2KayjklBq6xzPKeV1DqaVM+gcySwn0RlOLufRGcvPf/OqQNnrM7AFDdIDqlGfvbvQICWgSvXZtRENAgigeKB6F9D2vWgQQAABBBBAAAEE0Mqx/gZF1NmyFw0CCKApgOpdQxs3okF6QJVKtH0XGqQKVKNEu7agQdpA2Uu0N784zMirM/6IZTQayyzO83LpLMvyBq1wmGfbuBplAAAAAElFTkSuQmCC',
  'base64',
);

const fullName = `${String(patient.nom || '').toUpperCase()} ${patient.prenom || ''}`.trim();
const today = new Date();
const appointmentStart = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 10, 0, 0);
const appointment = {
  id: 9023,
  patient_id: patient.id,
  patient_name: fullName,
  patient: { id: patient.id, nom: patient.nom, prenom: patient.prenom, photo_url: `/api/patients/${patient.id}/photo` },
  praticien_id: 1,
  resource_id: null,
  datetime_start: appointmentStart.toISOString(),
  start_time: appointmentStart.toISOString(),
  time: '10:00',
  duration_minutes: 30,
  motif: 'Contrôle 02.3',
  description: 'Contrôle 02.3',
  status: 'EN_ATTENTE',
  scheduling_type: 'EXACT_TIME',
  notes: null,
  employer_id: 1,
  reminder_sent: false,
  ticket_number: 23,
  created_at: appointmentStart.toISOString(),
};

const json = (route, body) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
async function resetNoPhoto() {
  const res = await api.delete(`/api/patients/${patient.id}/photo`, { headers });
  if (![200, 204, 404].includes(res.status())) throw new Error(`reset photo failed: ${res.status()} ${await res.text()}`);
}

async function photoHash() {
  const res = await api.get(`/api/patients/${patient.id}/photo`, { headers });
  if (!res.ok()) throw new Error(`canonical photo unavailable: ${res.status()}`);
  return crypto.createHash('sha256').update(await res.body()).digest('hex');
}

async function preparePage(context) {
  const page = await context.newPage();
  await page.addInitScript(({ access, refresh, mobileAccess }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    if (mobileAccess) localStorage.setItem('dc_mobile_cert_token', mobileAccess);
  }, {
    access: tokens.access_token,
    refresh: tokens.refresh_token,
    mobileAccess: process.env.T2_MOBILE_ACCESS_TOKEN || '',
  });
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  await page.route('**/api/appointments/pending', route => json(route, []));
  await page.route('**/api/appointments/multi-practitioner**', route => json(route, [appointment]));
  await page.route('**/api/appointments/**', route => {
    if (route.request().method() === 'GET') return json(route, [appointment]);
    return route.continue();
  });
  return { page, pageErrors };
}

async function uploadViaUi(page, buffer, name) {
  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}/edit`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.locator('[data-patient-photo-editor]').waitFor({ state: 'visible', timeout: 30000 });
  await page.getByLabel('Importer une photo du patient').setInputFiles({ name, mimeType: 'image/png', buffer });
  const dialog = page.getByRole('dialog', { name: 'Recadrer la photo' });
  await dialog.waitFor({ state: 'visible', timeout: 30000 });
  await dialog.getByRole('button', { name: 'Enregistrer la photo' }).click();
  await dialog.waitFor({ state: 'detached', timeout: 30000 });
  await page.getByRole('button', { name: 'Supprimer', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
}

async function removeViaUi(page) {
  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}/edit`, { waitUntil: 'networkidle', timeout: 90000 });
  const button = page.getByRole('button', { name: 'Supprimer', exact: true });
  await button.waitFor({ state: 'visible', timeout: 30000 });
  await button.click();
  await button.waitFor({ state: 'detached', timeout: 30000 });
  await page.getByLabel('Initiales du patient').waitFor({ state: 'visible', timeout: 30000 });
}

async function assertAvatarState(page, state) {
  const selector = `[data-patient-avatar][data-patient-id="${patient.id}"]:visible`;
  const avatar = page.locator(selector).first();
  await avatar.waitFor({ state: 'visible', timeout: 30000 });
  try {
    await page.waitForFunction(
      ({ id, expected }) => Array.from(document.querySelectorAll(`[data-patient-avatar][data-patient-id="${id}"]`)).some(node => {
        const element = node instanceof HTMLElement ? node : null;
        if (!element) return false;
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        const visible = style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
        return visible && element.getAttribute('data-photo-state') === expected;
      }),
      { id: String(patient.id), expected: state },
      { timeout: 30000 },
    );
  } catch (error) {
    const diagnostic = await page.evaluate(async ({ id }) => {
      const nodes = Array.from(document.querySelectorAll(`[data-patient-avatar][data-patient-id="${id}"]`)).map(node => ({
        photoState: node.getAttribute('data-photo-state'),
        ariaLabel: node.getAttribute('aria-label'),
      }));
      const authState = document.querySelector('[data-g3-browser-cert]')?.getAttribute('data-auth-state') || null;
      const token = localStorage.getItem('token');
      let directPhotoStatus = null;
      if (token) {
        try {
          const response = await fetch(`http://127.0.0.1:8005/api/patients/${id}/photo`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          directPhotoStatus = response.status;
        } catch {
          directPhotoStatus = -1;
        }
      }
      return { authState, hasLocalToken: Boolean(token), nodes, directPhotoStatus };
    }, { id: String(patient.id) });
    console.error('PHOTO_AVATAR_DIAGNOSTIC', JSON.stringify({ expected: state, ...diagnostic }));
    throw error;
  }
}

async function assertSurfaces(page, expectedState, viewportLabel, phase) {
  const shots = [];
  await page.goto('http://127.0.0.1:5173/patients', { waitUntil: 'networkidle', timeout: 90000 });
  const patientEntry = page.locator('[role="button"]').filter({ hasText: fullName }).first();
  await patientEntry.waitFor({ state: 'visible', timeout: 30000 });
  const listAvatar = patientEntry.locator(`[data-patient-avatar][data-patient-id="${patient.id}"]`).first();
  await listAvatar.waitFor({ state: 'visible', timeout: 30000 });
  await page.waitForFunction(
    ({ id, expected }) => Array.from(document.querySelectorAll(`[role="button"] [data-patient-avatar][data-patient-id="${id}"]`)).some(node => {
      const element = node instanceof HTMLElement ? node : null;
      if (!element) return false;
      const rect = element.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && element.getAttribute('data-photo-state') === expected;
    }),
    { id: String(patient.id), expected: expectedState },
    { timeout: 30000 },
  );
  // Do not certify a photo hidden by the PatientSummaryHoverCard: moving
  // the pointer away ends its delayed hover, then ensure the actual avatar
  // is inside the viewport and is the topmost hit-tested visual target.
  await listAvatar.scrollIntoViewIfNeeded();
  await page.mouse.move(2, 2);
  await page.getByText('Repères du dossier', { exact: true }).waitFor({ state: 'hidden', timeout: 10000 });
  await page.waitForFunction(id => {
    const avatar = document.querySelector(`[role="button"] [data-patient-avatar][data-patient-id="${id}"]`);
    if (!(avatar instanceof HTMLElement)) return false;
    const rect = avatar.getBoundingClientRect();
    if (rect.width < 20 || rect.height < 20 || rect.top < 0 || rect.bottom > innerHeight) return false;
    const foreground = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
    return foreground === avatar || avatar.contains(foreground);
  }, String(patient.id), { timeout: 10000 });
  shots.push(await snap(page, `${phase}-patient-list-${viewportLabel}.png`));

  await page.goto('http://127.0.0.1:5173/dashboard', { waitUntil: 'networkidle', timeout: 90000 });
  const searchButton = page.getByRole('button', { name: 'Chercher un patient' });
  if (await searchButton.count()) {
    await searchButton.click();
    const search = page.getByRole('textbox', { name: 'Chercher un patient' });
    await search.fill(String(patient.nom));
    const searchResults = page.locator('#dashboard-patient-search-results');
    await searchResults.waitFor({ state: 'visible', timeout: 30000 });
    await searchResults.getByText(fullName, { exact: false }).first().waitFor({ state: 'visible', timeout: 30000 });
    const searchAvatar = searchResults.locator(`[data-patient-avatar][data-patient-id="${patient.id}"]`).first();
    await searchAvatar.waitFor({ state: 'visible', timeout: 30000 });
    await page.waitForFunction(
      ({ id, expected }) => document.querySelector(`#dashboard-patient-search-results [data-patient-avatar][data-patient-id="${id}"]`)?.getAttribute('data-photo-state') === expected,
      { id: String(patient.id), expected: expectedState },
      { timeout: 30000 },
    );
    shots.push(await snap(page, `${phase}-search-${viewportLabel}.png`));
    const close = page.getByRole('button', { name: 'Fermer la recherche patient' });
    if (await close.count()) await close.click();
  }

  const waitingUrl = `http://127.0.0.1:5173/mobile/g3-cert?demo=1&tab=waiting-room&patientId=${patient.id}&patientName=${encodeURIComponent(fullName)}&ticket=23`;
  await page.goto(waitingUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.locator('[data-mob5i-waiting-room]').waitFor({ state: 'visible', timeout: 30000 });
  await page.getByText(fullName, { exact: false }).first().waitFor({ state: 'visible', timeout: 30000 });
  await assertAvatarState(page, expectedState);
  shots.push(await snap(page, `${phase}-waiting-room-${viewportLabel}.png`));

  await page.goto('http://127.0.0.1:5173/agenda', { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Mois', exact: true }).click();
  const monthView = page.getByTestId('agenda-month-view');
  await monthView.waitFor({ state: 'visible', timeout: 30000 });
  const monthAppointment = monthView.locator('[data-m4d-month-appointment]').filter({ hasText: fullName }).first();
  await monthAppointment.waitFor({ state: 'visible', timeout: 30000 });
  const agendaAvatar = monthAppointment.locator(`[data-patient-avatar][data-patient-id="${patient.id}"]`).first();
  await agendaAvatar.waitFor({ state: 'visible', timeout: 30000 });
  await page.waitForFunction(
    ({ id, expected }) => document.querySelector(`[data-testid="agenda-month-view"] [data-m4d-month-appointment] [data-patient-avatar][data-patient-id="${id}"]`)?.getAttribute('data-photo-state') === expected,
    { id: String(patient.id), expected: expectedState },
    { timeout: 30000 },
  );
  // A DOM-only state assertion is not a visual certificate: month cells can
  // sit below the fold on phones. Scroll the actual appointment into view,
  // then require the avatar centre to be unobscured inside the viewport.
  await agendaAvatar.scrollIntoViewIfNeeded();
  await page.mouse.move(2, 2);
  await page.waitForFunction(id => {
    const avatar = document.querySelector(
      `[data-testid="agenda-month-view"] [data-m4d-month-appointment] [data-patient-avatar][data-patient-id="${id}"]`,
    );
    if (!(avatar instanceof HTMLElement)) return false;
    const rect = avatar.getBoundingClientRect();
    if (rect.width < 12 || rect.height < 12 || rect.left < 0 || rect.top < 0 ||
        rect.right > innerWidth || rect.bottom > innerHeight) return false;
    const foreground = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
    return foreground === avatar || avatar.contains(foreground);
  }, String(patient.id), { timeout: 10000 });
  shots.push(await snap(page, `${phase}-agenda-${viewportLabel}.png`, { viewportOnly: true }));

  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('heading', { name: fullName }).waitFor({ state: 'visible', timeout: 30000 });
  const dossierHeader = page.locator('header').filter({ hasText: fullName }).first();
  await dossierHeader.waitFor({ state: 'visible', timeout: 30000 });
  const dossierAvatar = dossierHeader.locator(`[data-patient-avatar][data-patient-id="${patient.id}"]`).first();
  await dossierAvatar.waitFor({ state: 'visible', timeout: 30000 });
  await page.waitForFunction(
    ({ id, expected }) => document.querySelector(`header [data-patient-avatar][data-patient-id="${id}"]`)?.getAttribute('data-photo-state') === expected,
    { id: String(patient.id), expected: expectedState },
    { timeout: 30000 },
  );
  shots.push(await snap(page, `${phase}-dossier-${viewportLabel}.png`));
  return shots;
}

async function snap(page, filename, { viewportOnly = false } = {}) {
  const m = await page.evaluate(() => ({
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  if (m.horizontalOverflow) throw new Error(`${filename}: horizontal overflow ${m.scrollWidth}>${m.innerWidth}`);
  await page.screenshot({ path: path.join(outDir, filename), fullPage: !viewportOnly });
  return { filename, ...m };
}

const browser = await chromium.launch({ headless: true });
const evidence = [];
try {
  for (const viewport of viewports) {
    await resetNoPhoto();
    const context = await browser.newContext({ viewport, colorScheme: 'light' });
    const { page, pageErrors } = await preparePage(context);

    const initial = await assertSurfaces(page, 'initials', viewport.label, 'initial');
    await uploadViaUi(page, sampleA, 'patient-a.png');
    const firstHash = await photoHash();
    const added = await assertSurfaces(page, 'photo', viewport.label, 'added');

    await uploadViaUi(page, sampleB, 'patient-b.png');
    const secondHash = await photoHash();
    if (secondHash === firstHash) throw new Error(`${viewport.label}: replacement did not change canonical photo hash`);
    const replaced = await assertSurfaces(page, 'photo', viewport.label, 'replaced');

    await removeViaUi(page);
    const deleted = await assertSurfaces(page, 'initials', viewport.label, 'deleted');

    if (pageErrors.length) throw new Error(`${viewport.label}: page errors: ${pageErrors.join(' | ')}`);
    evidence.push({ viewport, firstHash, secondHash, initial, added, replaced, deleted, pageErrors });
    await context.close();
  }
} finally {
  await resetNoPhoto();
  await browser.close();
  await api.dispose();
}

fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify({
  productHead: process.env.EVALUATED_SHA || process.env.GITHUB_HEAD_SHA || process.env.GITHUB_SHA || null,
  patientId: patient.id,
  phases: ['initials', 'added', 'replaced', 'deleted'],
  surfaces: ['patient-list', 'search', 'waiting-room', 'agenda', 'dossier'],
  evidence,
  success: true,
}, null, 2));
console.log('V15_02_3_PHOTO_UI_AFTER_PASS', JSON.stringify({ patientId: patient.id, viewports: evidence.length, success: true }));
