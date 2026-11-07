/**
 * CPV2-02C FUE-G browser: real React -> actual FastAPI -> disposable local DB.
 * No mocked HTTP endpoint. Only fault injection: deliberately lose ONE real
 * archive HTTP response *after* route.fetch has committed at FastAPI.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

if (process.env.GITHUB_ACTIONS !== 'true'
  || process.env.CPV2_02C_REAL_BROWSER_LAB !== '1'
  || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== 'true'
  || process.env.ENVIRONMENT !== 'test') {
  throw Error('Real browser lab requires CI-only isolated runtime attestation');
}
const sha = process.env.CPV2_REAL_BROWSER_SHA;
const creds = JSON.parse(fs.readFileSync(process.env.CPV2_REAL_BROWSER_CREDS_FILE, 'utf8'));
const out = path.resolve(process.env.CPV2_REAL_BROWSER_OUTPUT);
const origin = 'http://127.0.0.1:5174';
const backend = 'http://127.0.0.1:8005';
assert.match(sha, /^[0-9a-f]{40}$/);
assert.equal(creds.api_base_url, backend);
assert.equal(creds.masterKey, '22'.repeat(32));
assert.equal(creds.patients.length, 2);
fs.mkdirSync(out, { recursive: true });

const api = await request.newContext({ baseURL: backend });
const browser = await chromium.launch({ headless: true });
const proof = { sourceHead: sha, level: 'REAL Chromium->FastAPI->isolated SQL',
  mocks: false, networkFaultInjection: true, documents: [], screenshots: [], allPassed: false };

async function setCreds(page) {
  // Genuine MobileStorage IndexedDB access. No service worker, no mocked hook.
  await page.evaluate(async (saved) => {
    await new Promise((resolve, reject) => {
      const req = indexedDB.open('digital-crown-zka', 1);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains('secure_keys')) {
          req.result.createObjectStore('secure_keys');
        }
      };
      req.onerror = () => reject(req.error);
      req.onsuccess = () => {
        const db = req.result;
        const tx = db.transaction('secure_keys', 'readwrite');
        tx.objectStore('secure_keys').put(saved, 'zka_credentials');
        tx.oncomplete = () => { db.close(); resolve(); };
        tx.onerror = () => reject(tx.error);
      };
    });
  }, creds);
}

async function mount(page, patientId) {
  await page.evaluate(async (id) => {
    const React = await import('/node_modules/.vite/deps/react.js');
    const ReactDOM = await import('/node_modules/.vite/deps/react-dom_client.js');
    const ui = await import('/src/features/mobile/Dashboard/views/MobileQuickDocumentSheet.tsx');
    const root = document.createElement('div');
    root.id = 'real-cpv2-02c-root';
    document.body.appendChild(root);
    (ReactDOM.default ?? ReactDOM).createRoot(root).render(
      (React.default ?? React).createElement(ui.MobileQuickDocumentSheet, {
        patient: { id, name: 'Patient fictif ' + id },
        preview: false,
        onClose: () => {},
      }),
    );
  }, patientId);
  await page.locator('[data-mobile-quick-document]').waitFor({ state: 'visible' });
}

async function runPatient(patientId, loseResponse) {
  const context = await browser.newContext({
    viewport: { width: 430, height: 932 }, serviceWorkers: 'block',
  });
  const page = await context.newPage();
  const javascriptErrors = [];
  const posts = [];
  const reads = [];
  let actualArchiveId = null;
  page.on('pageerror', (e) => javascriptErrors.push(e.message));
  page.on('request', (req) => {
    const url = new URL(req.url());
    if (url.origin !== backend) return;
    if (url.pathname === '/api/mobile/documents/archive' && req.method() === 'POST') {
      posts.push({
        key: req.headers()['idempotency-key'],
        body: req.postDataJSON(),
      });
    }
    if (url.pathname.startsWith('/api/mobile/documents/archive/receipt/') && req.method() === 'GET') {
      reads.push(url.pathname);
    }
  });
  if (loseResponse) {
    await page.route('**/api/mobile/documents/archive', async (route) => {
      if (route.request().method() !== 'POST') return route.continue();
      // This forwards the *real* request and tests a post-commit network loss.
      const upstream = await route.fetch();
      assert.equal(upstream.status(), 200, 'Backend did not archive before loss');
      actualArchiveId = upstream.headers()['x-document-id'];
      assert.match(actualArchiveId ?? '', /^[0-9]+$/);
      await route.abort('failed');
    });
  }

  try {
    await page.goto(origin + '/mobile/demo?demo=1', { waitUntil: 'domcontentloaded' });
    await setCreds(page);
    await mount(page, patientId);
    await page.getByRole('button', { name: /Certificat/i }).first().click();
    await page.getByRole('button', { name: /Prévisualiser/i }).click();
    await page.getByText(/Aperçu validé/i).waitFor({ timeout: 50000 });
    const previewResponse = page.locator('[data-mobile-quick-document]');
    assert.equal(await previewResponse.count(), 1);
    await page.getByRole('button', { name: /Archiver le document/i }).click();

    if (loseResponse) {
      await page.getByText(/Archivage non confirmé/i).waitFor({ timeout: 50000 });
      assert.equal(await page.getByRole('button', { name: /Archiver le document/i }).isDisabled(), true);
      // A page reload must recover the opaque intent; no repeated archive POST.
      await page.reload({ waitUntil: 'domcontentloaded' });
      await mount(page, patientId);
      await page.getByText(/Archivage non confirmé/i).waitFor({ timeout: 50000 });
      await page.getByRole('button', { name: /Vérifier le reçu/i }).click();
      await page.getByText(/Archive retrouvée et confirmée/i).waitFor({ timeout: 50000 });
      assert.equal(reads.length, 1, 'Expected GET-only receipt recovery');
    } else {
      await page.getByText(/Document archivé et reçu confirmé/i).waitFor({ timeout: 50000 });
    }
    assert.equal(posts.length, 1, 'Exactly one clinical POST per intent');
    const { key, body } = posts[0];
    assert.match(key, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    const token = creds.access_token;
    const receipt = await api.get('/api/mobile/documents/archive/receipt/' + key, {
      headers: { Authorization: 'Bearer ' + token },
    });
    assert.equal(receipt.status(), 200);
    assert.match(receipt.headers()['content-type'] || '', /application\/pdf/);
    const documentId = receipt.headers()['x-document-id'];
    assert.match(documentId || '', /^[0-9]+$/);
    if (loseResponse) assert.equal(actualArchiveId, documentId);
    assert.ok((await receipt.body()).length > 1000, 'Real PDF bytes required');

    // Browser never creates the second archive. Identical API replay is
    // explicitly verified and returns the SAME document number and PDF.
    const replay = await api.post('/api/mobile/documents/archive', {
      headers: { Authorization: 'Bearer ' + token, 'Idempotency-Key': key },
      data: body,
    });
    assert.equal(replay.status(), 200);
    assert.equal(replay.headers()['x-document-id'], documentId);
    assert.equal(replay.headers()['x-idempotent-replay'], 'true');
    const changed = { ...body, data: { ...body.data, reason: 'Autre certificat fictif' } };
    const collision = await api.post('/api/mobile/documents/archive', {
      headers: { Authorization: 'Bearer ' + token, 'Idempotency-Key': key },
      data: changed,
    });
    assert.equal(collision.status(), 409, 'Idempotency UUID reused for new clinical content');

    const name = loseResponse ? '02-lost-response-recovered.png' : '01-real-archive.png';
    await page.screenshot({ path: path.join(out, name), fullPage: true });
    proof.screenshots.push(name);
    assert.deepEqual(javascriptErrors, [], 'Browser JavaScript errors');
    proof.documents.push({
      patientId, intentKey: key, documentId: Number(documentId),
      actualRequestsToBackend: 1, receiptGetsInBrowser: reads.length,
      lostResponse: loseResponse, safeRecovery: true,
      replayStatus: replay.status(), collisionStatus: collision.status(),
    });
  } finally {
    await context.close();
  }
}

try {
  const denied = await api.get('/api/mobile/documents/archive/ready');
  assert.ok([401, 422].includes(denied.status()), 'Anonymous read must be denied');
  await runPatient(creds.patients[0], false);
  await runPatient(creds.patients[1], true);
  proof.allPassed = true;
} finally {
  fs.writeFileSync(path.join(out, 'evidence.json'), JSON.stringify(proof, null, 2));
  await api.dispose();
  await browser.close();
}
