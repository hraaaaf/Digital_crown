import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser');
fs.mkdirSync(outDir, { recursive: true });
const outputPath = path.join(outDir, 'output-gates.json');

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function fail(message, evidence = {}) {
  const report = { status: 'FAIL', error: message, ...evidence };
  fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
  console.error('T2_OUTPUT_RED', JSON.stringify(report));
  process.exitCode = 1;
  return report;
}

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password: 'T2BrowserPass123!' },
});
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const patients = await api.get('/api/patients', {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patientList = await patients.json();
const patient = patientList.find((candidate) => candidate.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2 certification patient not found');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });

await context.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');

  window.__t2PrintCalls = 0;
  const nativeCreateElement = Document.prototype.createElement;
  const contentWindowDescriptor = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
  Document.prototype.createElement = function patchedCreateElement(tagName, options) {
    const element = nativeCreateElement.call(this, tagName, options);
    if (String(tagName).toLowerCase() === 'iframe' && contentWindowDescriptor?.get) {
      try {
        Object.defineProperty(element, 'contentWindow', {
          configurable: true,
          get() {
            const childWindow = contentWindowDescriptor.get.call(this);
            if (childWindow && !childWindow.__t2PrintWrapped) {
              try {
                childWindow.__t2PrintWrapped = true;
                childWindow.print = () => {
                  window.__t2PrintCalls = (window.__t2PrintCalls || 0) + 1;
                };
              } catch {}
            }
            return childWindow;
          },
        });
      } catch {}
    }
    return element;
  };
}, { access: tokens.access_token, refresh: tokens.refresh_token });

const page = await context.newPage();
const basePatientUrl = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=`;

async function waitForStudio(label) {
  await page.getByText('Documents A5', { exact: true }).waitFor({ timeout: 30000 });
  await page.getByText(label, { exact: true }).first().waitFor({ timeout: 30000 });
}

async function closeOpenDialog() {
  const dialog = page.getByRole('dialog').last();
  if (await dialog.isVisible({ timeout: 1200 }).catch(() => false)) {
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
  }
}

async function generateLibreAndCapturePdf(expectedTitle, expectedContent) {
  const generateRequestPromise = page.waitForRequest((req) =>
    req.method() === 'POST' && req.url().includes('/api/documents/generate?'),
    { timeout: 30000 },
  );
  const pdfResponsePromise = page.waitForResponse((response) => {
    const contentType = response.headers()['content-type'] || '';
    return response.request().method() === 'GET' && contentType.includes('application/pdf');
  }, { timeout: 30000 });

  await page.getByRole('button', { name: 'Enregistrer', exact: true }).click();
  const generateRequest = await generateRequestPromise;
  const payload = generateRequest.postDataJSON();
  const pdfResponse = await pdfResponsePromise;
  const pdfBytes = await pdfResponse.body();

  if (payload?.data?.title !== expectedTitle || payload?.data?.content !== expectedContent) {
    throw new Error(`stale payload: expected ${expectedTitle}/${expectedContent}, got ${payload?.data?.title}/${payload?.data?.content}`);
  }
  if (!pdfResponse.ok() || !pdfBytes.subarray(0, 4).equals(Buffer.from('%PDF'))) {
    throw new Error(`invalid PDF response: status=${pdfResponse.status()} signature=${pdfBytes.subarray(0, 4).toString()}`);
  }
  return {
    title: payload.data.title,
    content: payload.data.content,
    pdfStatus: pdfResponse.status(),
    contentType: pdfResponse.headers()['content-type'],
    bytes: pdfBytes.length,
    hash: sha256(pdfBytes),
  };
}

let printEvidence = null;
let freshnessEvidence = null;

try {
  await page.goto(`${basePatientUrl}devis`, { waitUntil: 'networkidle', timeout: 90000 });
  await waitForStudio('Devis');
  await page.getByRole('button', { name: 'Actes rapides', exact: true }).click();
  await page.getByRole('button', { name: /Nouvel acte/i }).click();
  await page.getByPlaceholder('Rechercher ou saisir un acte...').last().fill('Certification impression T2');
  await page.getByPlaceholder('0.00').last().fill('321');

  const generatedForPrint = page.waitForResponse((response) =>
    response.request().method() === 'POST' && response.url().includes('/api/documents/generate?'),
    { timeout: 30000 },
  );
  await page.getByRole('button', { name: 'Imprimer', exact: true }).click();
  const warning = page.getByRole('dialog', { name: 'Attention : Impression Directe' });
  await warning.waitFor({ state: 'visible', timeout: 10000 });
  await warning.getByRole('button', { name: 'Confirmer', exact: true }).click();
  const printGenerateResponse = await generatedForPrint;
  await page.waitForFunction(() => window.__t2PrintCalls > 0, null, { timeout: 30000 });
  const printCalls = await page.evaluate(() => window.__t2PrintCalls || 0);
  printEvidence = {
    pass: printGenerateResponse.ok() && printCalls > 0,
    generateStatus: printGenerateResponse.status(),
    printCalls,
    path: 'iframe.contentWindow.print()',
  };
  await page.screenshot({ path: path.join(outDir, 't2-browser-print.png'), fullPage: true });
} catch (error) {
  printEvidence = { pass: false, error: String(error) };
  await page.screenshot({ path: path.join(outDir, 't2-browser-print-failed.png'), fullPage: true }).catch(() => {});
}

try {
  await page.goto(`${basePatientUrl}libre`, { waitUntil: 'networkidle', timeout: 90000 });
  await waitForStudio('Document Libre');
  await closeOpenDialog();

  const titleInput = page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...');
  const contentInput = page.getByPlaceholder("Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte.");

  await titleInput.fill('T2 Freshness A');
  await contentInput.fill('Version PDF A');
  const first = await generateLibreAndCapturePdf('T2 Freshness A', 'Version PDF A');

  await titleInput.fill('T2 Freshness B');
  await contentInput.fill('Version PDF B');
  await titleInput.fill('T2 Freshness C');
  await contentInput.fill('Version PDF C');
  const second = await generateLibreAndCapturePdf('T2 Freshness C', 'Version PDF C');

  freshnessEvidence = {
    pass: first.hash !== second.hash && second.title === 'T2 Freshness C' && second.content === 'Version PDF C',
    first,
    second,
    changedHash: first.hash !== second.hash,
    latestPayloadObserved: second.title === 'T2 Freshness C' && second.content === 'Version PDF C',
  };
  await page.screenshot({ path: path.join(outDir, 't2-pdf-freshness.png'), fullPage: true });
} catch (error) {
  freshnessEvidence = { pass: false, error: String(error) };
  await page.screenshot({ path: path.join(outDir, 't2-pdf-freshness-failed.png'), fullPage: true }).catch(() => {});
}

const pass = printEvidence?.pass === true && freshnessEvidence?.pass === true;
const report = {
  status: pass ? 'PASS' : 'FAIL',
  patientId: patient.id,
  print: printEvidence,
  freshness: freshnessEvidence,
};
fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));

await context.close();
await browser.close();
await api.dispose();

if (!pass) {
  fail('Browser print and/or PDF freshness certification failed', report);
  process.exit(1);
}
