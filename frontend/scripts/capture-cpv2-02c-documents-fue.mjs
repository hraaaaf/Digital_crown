// CPV2-02C — FUE-I browser evidence, synthetic Pocket session only.
// Real React component, Vite app theme tokens, real browser layout; HTTP APIs stubbed.
// NOT an authenticated FastAPI / physical cabinet / FUE-G certification.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const url = process.env.CPV2_DOCS_FUE_URL || 'http://127.0.0.1:5174/mobile/demo?demo=1';
const out = process.env.CPV2_DOCS_FUE_DIR || '../artifacts/cpv2-02c-documents-fue';
const viewportMatrix = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 800 },
];
const credentials = {
  publicId: '0123456789abcdef', masterKey: 'a'.repeat(64),
  access_token: 'synthetic-fue-token-not-valid', refresh_token: 'synthetic',
  device_id: 'synthetic-cpv2-02c', api_base_url: 'http://127.0.0.1:5174',
};
const evidence = [];
await fs.mkdir(out, { recursive: true });

async function seedCredentials(page) {
  await page.evaluate(async creds => {
    await new Promise((resolve, reject) => {
      const req = indexedDB.open('digital-crown-zka', 1);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains('secure_keys')) req.result.createObjectStore('secure_keys');
      };
      req.onerror = () => reject(req.error);
      req.onsuccess = () => {
        const db = req.result;
        const tx = db.transaction('secure_keys', 'readwrite');
        tx.objectStore('secure_keys').put(creds, 'zka_credentials');
        tx.oncomplete = () => { db.close(); resolve(); };
        tx.onerror = () => reject(tx.error);
      };
    });
  }, credentials);
}

function jsonRoute(route, payload) {
  return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) });
}

async function mountRealComponent(page) {
  await page.evaluate(async () => {
    // Vite supplies the real application modules; no test copy of the component.
    const React = await import('/node_modules/.vite/deps/react.js');
    const ReactDOM = await import('/node_modules/.vite/deps/react-dom_client.js');
    const mod = await import('/src/features/mobile/Dashboard/views/MobileQuickDocumentSheet.tsx');
    const target = document.createElement('div');
    target.id = 'cpv2-02c-browser-evidence';
    document.body.appendChild(target);
    ReactDOM.createRoot(target).render(React.createElement(mod.MobileQuickDocumentSheet, {
      patient: { id: 101, name: 'Patient Fictif CPV2', medicalAlert: 'Alerte médicale fictive' },
      preview: false,
      onClose: () => {},
    }));
  });
  await page.locator('[data-mobile-quick-document]').waitFor({ state: 'visible', timeout: 12000 });
}

async function createCase(engine, viewport, options = {}) {
  const browser = await engine.launch({ headless: true });
  const context = await browser.newContext({ viewport, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const counters = { capabilityHits: 0, previewHits: 0, archiveHits: 0 };
  const allowed = options.none
    ? { can_create_prescription: false, can_create_certificate: false, can_create_devis: false, can_create_honoraires: false, can_create_free_document: false }
    : { can_create_prescription: false, can_create_certificate: !options.honoraires, can_create_devis: false, can_create_honoraires: !!options.honoraires, can_create_free_document: false };

  await page.route('**/api/mobile/quick-actions/capabilities', route => {
    counters.capabilityHits++;
    return jsonRoute(route, allowed);
  });
  await page.route('**/api/mobile/patient-cockpit/**', route => jsonRoute(route, { patient: { has_medical_alert: false } }));
  await page.route('**/api/mobile/documents/preview', route => {
    counters.previewHits++;
    if (options.invalidPdf) return jsonRoute(route, { error: 'invalid type' });
    return route.fulfill({ status: 200, contentType: 'application/pdf', body: '%PDF-1.4\n% synthetic PDF preview only\n' });
  });
  await page.route('**/api/mobile/documents/archive', route => {
    counters.archiveHits++;
    return route.fulfill({ status: 200, contentType: 'application/pdf', body: '%PDF-1.4\n% synthetic archive only\n' });
  });
  const label = engine.name() + '-' + viewport.width + 'x' + viewport.height + (options.zoom ? '-zoom200' : '') +
    (options.none ? '-deny' : options.invalidPdf ? '-invalidpdf' : options.honoraires ? '-honoraires' : '');
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await seedCredentials(page);
    if (options.zoom) {
      await page.evaluate(() => { document.documentElement.style.zoom = '200%'; });
    }
    await mountRealComponent(page);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(out, label + '-01-before.png') });

    if (options.none) {
      await page.getByText('Aucun type documentaire autorisé pour cette session.').waitFor();
      if (await page.getByRole('button', { name: /Certificat/i }).count()) throw Error('Unauthorized certificate exposed');
    } else {
      await page.getByRole('button', { name: options.honoraires ? /Honoraires/i : /Certificat/i }).first().click();
      if (options.honoraires) {
        await page.getByPlaceholder('Acte').fill('Acte fictif');
        await page.getByPlaceholder('MAD').fill('100');
      }
      await page.screenshot({ path: path.join(out, label + '-02-editor.png') });
      await page.getByRole('button', { name: /Prévisualiser/i }).click();
      if (options.invalidPdf) {
        await page.getByText('Réponse PDF invalide.').waitFor();
        if (await page.getByText(/Aperçu validé/i).count()) throw Error('Accepted invalid PDF');
      } else {
        await page.getByText(/Aperçu validé/i).waitFor();
        await page.screenshot({ path: path.join(out, label + '-03-preview.png') });
        if (options.honoraires) {
          const disabled = await page.getByRole('button', { name: /Archivage indisponible/i }).isDisabled();
          if (!disabled) throw Error('Honoraires archival button not disabled');
        } else {
          await page.getByRole('button', { name: /Archiver le document/i }).click();
          await page.getByText(/Document généré et archivé/i).waitFor();
          if (!(await page.getByRole('button', { name: /Déjà archivé/i }).isDisabled())) throw Error('Duplicate archive button enabled');
          await page.screenshot({ path: path.join(out, label + '-04-after.png') });
        }
      }
    }

    const geometry = await page.locator('[data-mobile-quick-document] section').evaluate(el => ({
      clientWidth: el.clientWidth, scrollWidth: el.scrollWidth,
      clientHeight: el.clientHeight, scrollHeight: el.scrollHeight,
      font: getComputedStyle(el).fontFamily,
      background: getComputedStyle(el).backgroundColor,
    }));
    if (geometry.scrollWidth > geometry.clientWidth + 2) throw Error('Horizontal overflow in document sheet');
    if (counters.capabilityHits !== 1) throw Error('Missing / duplicate capabilities read');
    if (options.none && (counters.previewHits || counters.archiveHits)) throw Error('Unauthorized server action');
    if (options.invalidPdf && (counters.previewHits !== 1 || counters.archiveHits)) throw Error('Invalid PDF progressed');
    if (options.honoraires && counters.archiveHits) throw Error('Unauthorized honoraires archive');
    if (!options.none && !options.invalidPdf && !options.honoraires && (counters.previewHits !== 1 || counters.archiveHits !== 1)) throw Error('Missing preview/archive action');
    if (errors.length) throw Error('JS runtime errors: ' + errors.join(' | '));
    evidence.push({ engine: engine.name(), viewport, zoom200CssSimulation: !!options.zoom, case: options.none ? 'deny' : options.invalidPdf ? 'invalid-pdf' : options.honoraires ? 'honoraires' : 'preview-archive', counts: counters, geometry, passed: true, mocks: true });
  } catch (e) {
    await page.screenshot({ path: path.join(out, label + '-FAIL.png'), fullPage: true }).catch(() => {});
    evidence.push({ engine: engine.name(), viewport, case: label, passed: false, error: String(e), counts: counters, mocks: true });
    throw e;
  } finally {
    await context.close();
    await browser.close();
  }
}

try {
  for (const engine of [chromium, webkit]) {
    for (const viewport of viewportMatrix) {
      await createCase(engine, viewport);
      await createCase(engine, viewport, { zoom: true });
    }
    await createCase(engine, viewportMatrix[0], { none: true });
    await createCase(engine, viewportMatrix[0], { invalidPdf: true });
    await createCase(engine, viewportMatrix[0], { honoraires: true });
  }
} finally {
  await fs.writeFile(path.join(out, 'fue-i-evidence.json'), JSON.stringify({
    sha: process.env.CPV2_DOCS_FUE_SHA || 'UNKNOWN',
    level: 'FUE-I synthetic browser component + mocked APIs (NOT FUE-G)',
    noProductionData: true, noDeployment: true, evidence,
  }, null, 2));
}
console.log('CPV2-02C FUE-I browser pass: ' + evidence.length + ' scenarios');
