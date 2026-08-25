import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-b-after-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];
const uploads = [];

const patientPayload = {
  type: 'patient', label: 'Dossier patient',
  patient: { id: 12, numero_dossier: 'DC-0012', nom: 'BENNANI', prenom: 'Sara', date_naissance: '1989-04-16T00:00:00', telephone: '0612345678', assurance: 'CNSS', has_medical_alert: true, motif_consultation: 'Contrôle implant 36' },
};
const json = (body, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) });
const jpeg = Buffer.from('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABD/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/EB//xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/EB//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/EB//2Q==', 'base64');

const server = await createServer({ server: { host: '127.0.0.1', port: 4195, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

async function snap(page, name) {
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
}

async function capture(width, height) {
  const context = await browser.newContext({ viewport: { width, height }, screen: { width, height }, deviceScaleFactor: 1, hasTouch: true, isMobile: true, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith('/api/')) return route.continue();
    if (url.pathname === '/api/mobile/resource-context') return route.fulfill(json(patientPayload));
    if (url.pathname === '/api/mobile/resource-context-document-scan') {
      const raw = route.request().postDataBuffer();
      uploads.push({ width, body: raw ? raw.toString('latin1') : '' });
      return route.fulfill(json({ success: true, pages: 2, document: { id: 66, document_type: 'AUTRE', title: 'Document scanné', created_at: '2026-08-25T17:00:00' } }));
    }
    if (url.pathname === '/api/mobile/refresh-token') return route.fulfill(json({}, 401));
    return route.fulfill(json({}));
  });

  await page.goto('http://127.0.0.1:4195/mobile-m6-b-after.html', { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Dossier patient', exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  await page.getByText('BENNANI Sara', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  const action = page.locator('[data-m6b-scan-action]');
  await action.waitFor({ state: 'visible' });
  await snap(page, `patient-scan-action-${width}x${height}`);

  const input = page.locator('[data-m6b-scan-input]');
  await input.setInputFiles({ name: 'scan-page-1.jpg', mimeType: 'image/jpeg', buffer: jpeg });
  await page.locator('[data-m6b-scan-sheet]').waitFor({ state: 'visible' });
  await input.setInputFiles({ name: 'scan-page-2.jpg', mimeType: 'image/jpeg', buffer: jpeg });
  await page.getByText('2 pages prêtes', { exact: true }).waitFor({ state: 'visible' });
  await page.getByText('Page 2 sur 2', { exact: true }).waitFor({ state: 'visible' });
  await snap(page, `patient-scan-preview-${width}x${height}`);

  await page.getByRole('button', { name: 'Enregistrer le PDF · 2 pages', exact: true }).click();
  await page.locator('[data-m6b-scan-success]').waitFor({ state: 'visible' });
  await page.getByText('Document scanné enregistré', { exact: true }).waitFor({ state: 'visible' });
  await snap(page, `patient-scan-saved-${width}x${height}`);

  const metrics = await page.evaluate(() => {
    const root = document.documentElement;
    const action = document.querySelector('[data-m6b-scan-action]')?.getBoundingClientRect();
    const input = document.querySelector('[data-m6b-scan-input]');
    const controls = Array.from(document.querySelectorAll('[data-m6b-touch]')).map(el => {
      const rect = el.getBoundingClientRect();
      return { width: rect.width, height: rect.height, text: (el.textContent || '').replace(/\s+/g, ' ').trim() };
    });
    return {
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      scanActionHeight: action?.height || 0,
      cameraAccept: input?.getAttribute('accept') || '',
      cameraCapture: input?.getAttribute('capture') || '',
      controls,
    };
  });
  captures.push({ width, height, metrics, errors });
  await context.close();
}

try {
  await capture(390, 844);
  await capture(430, 932);
  await capture(768, 1024);
  const touchHeights = captures.flatMap(item => item.metrics.controls.map(control => control.height));
  const minTouch = touchHeights.length ? Math.min(...touchHeights) : 0;
  const report = {
    productHead,
    count: 9,
    viewports: captures,
    scanActionPresent: captures.every(item => item.metrics.scanActionHeight >= 44),
    cameraInputCorrect: captures.every(item => item.metrics.cameraCapture === 'environment' && /image\/jpeg/.test(item.metrics.cameraAccept) && /image\/png/.test(item.metrics.cameraAccept) && /image\/webp/.test(item.metrics.cameraAccept)),
    uploadCount: uploads.length,
    contextBoundUpload: uploads.every(item => item.body.includes('name="context_key"') && item.body.includes('M6B-Patient')),
    multiPageUpload: uploads.every(item => (item.body.match(/name="pages"/g) || []).length === 2),
    patientIdAbsent: uploads.every(item => !item.body.includes('patient_id')),
    minM6BTouchHeight: minTouch,
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.count !== 9 || !report.scanActionPresent || !report.cameraInputCorrect || report.uploadCount !== 3 || !report.contextBoundUpload || !report.multiPageUpload || !report.patientIdAbsent || report.minM6BTouchHeight < 44 || !report.noHorizontalOverflow || !report.noUnexpectedRuntimeErrors) {
    throw new Error('M6-B AFTER evidence gate failed');
  }
} finally {
  await browser.close();
  await server.close();
}
