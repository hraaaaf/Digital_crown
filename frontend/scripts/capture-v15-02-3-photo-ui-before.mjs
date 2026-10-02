// Synchronize trigger: BEFORE proof only; no product runtime change.
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/v15-02-3-photo-ui-before');
fs.mkdirSync(outDir, { recursive: true });

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 900 },
  { width: 1280, height: 900 },
];

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error(`02.3 BEFORE login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };

const patientsResponse = await api.get('/api/patients/', { headers });
if (!patientsResponse.ok()) throw new Error(`02.3 BEFORE patients failed: ${patientsResponse.status()}`);
const patients = await patientsResponse.json();
const patient = patients.find(row => row.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('02.3 BEFORE requires a patient fixture');

const samplePng = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEAhmtCEwIngcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfcNLAgY4ynDdAAAAAElFTkSuQmCC',
  'base64',
);
const uploaded = await api.post(`/api/patients/${patient.id}/photo`, {
  headers,
  multipart: { file: { name: 'patient-profile.png', mimeType: 'image/png', buffer: samplePng } },
});
if (!uploaded.ok()) throw new Error(`02.3 BEFORE photo upload failed: ${uploaded.status()} ${await uploaded.text()}`);
const photoCheck = await api.get(`/api/patients/${patient.id}/photo`, { headers });
if (!photoCheck.ok()) throw new Error(`02.3 BEFORE canonical photo unavailable: ${photoCheck.status()}`);

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
  duration_minutes: 30,
  motif: 'Contrôle 02.3',
  description: 'Contrôle 02.3',
  status: 'EN_S_ATTENTE',
  scheduling_type: 'EXACT_TIME',
  notes: null,
  employer_id: 1,
  reminder_sent: false,
  ticket_number: null,
  created_at: appointmentStart.toISOString(),
};

const browser = await chromium.launch({ headless: true });
const evidence = [];
const json = (route, body) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

async function preparePage(context) {
  const page = await context.newPage();
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

async function metrics(page) {
  return page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
  }));
}

async function shot(page, viewport, surface, suffix = '') {
  const filename = `before-${surface}-${viewport.width}x${viewport.height}${suffix}.png`;
  await page.screenshot({ path: path.join(outDir, filename), fullPage: true });
  return { filename, metrics: await metrics(page) };
}

async function text200(page, viewport, surface) {
  await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
  await page.waitForTimeout(150);
  const result = await shot(page, viewport, surface, '-text200');
  await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
  await page.waitForTimeout(80);
  return result;
}

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport, colorScheme: 'light' });
    const { page, pageErrors } = await preparePage(context);
    const row = { viewport, surfaces: {}, pageErrors };

    await page.goto('http://127.0.0.1:5173/patients', { waitUntil: 'networkidle', timeout: 90000 });
    await page.getByText(fullName, { exact: false }).first().waitFor({ state: 'visible', timeout: 30000 });
    row.surfaces.patientList = { normal: await shot(page, viewport, 'patient-list'), text200: await text200(page, viewport, 'patient-list') };

    await page.goto('http://127.0.0.1:5173/dashboard', { waitUntil: 'networkidle', timeout: 90000 });
    await page.getByRole('button', { name: 'Chercher un patient' }).click();
    const search = page.getByRole('textbox', { name: 'Chercher un patient' });
    await search.fill(String(patient.nom));
    await page.getByText(fullName, { exact: false }).first().waitFor({ state: 'visible', timeout: 30000 });
    row.surfaces.search = { normal: await shot(page, viewport, 'search'), text200: await text200(page, viewport, 'search') };
    await page.getByRole('button', { name: 'Fermer la recherche patient' }).click();

    await page.getByText(fullName, { exact: false }).first().waitFor({ state: 'visible', timeout: 30000 });
    row.surfaces.waitingRoom = { normal: await shot(page, viewport, 'waiting-room'), text200: await text200(page, viewport, 'waiting-room') };

    await page.goto('http://127.0.0.1:5173/agenda', { waitUntil: 'networkidle', timeout: 90000 });
    await page.getByText(fullName, { exact: false }).first().waitFor({ state: 'visible', timeout: 30000 });
    row.surfaces.agenda = { normal: await shot(page, viewport, 'agenda'), text200: await text200(page, viewport, 'agenda') };

    await page.goto(`http://127.0.0.1:5173/patients/${patient.id}`, { waitUntil: 'networkidle', timeout: 90000 });
    await page.getByRole('heading', { name: fullName }).waitFor({ state: 'visible', timeout: 30000 });
    row.surfaces.dossierHeader = { normal: await shot(page, viewport, 'dossier-header'), text200: await text200(page, viewport, 'dossier-header') };

    if (pageErrors.length) throw new Error(`${viewport.width}: page errors: ${pageErrors.join(' | ')}`);
    evidence.push(row);
    await context.close();
  }
} finally {
  await browser.close();
  await api.dispose();
}

fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify({
  base: 'e6ee00a906275436c54e1263ec93097278b4c400',
  patientId: patient.id,
  canonicalPhotoStatus: photoCheck.status(),
  evidence,
}, null, 2));
console.log('V15_02_3_PHOTO_UI_BEFORE', JSON.stringify({ patientId: patient.id, canonicalPhotoStatus: photoCheck.status(), viewports: evidence.length }));