import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-a-before-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];

const patientPayload = {
  type: 'patient',
  label: 'Dossier patient',
  patient: {
    id: 12,
    numero_dossier: 'DC-0012',
    nom: 'BENNANI',
    prenom: 'Sara',
    date_naissance: '1989-04-16T00:00:00',
    telephone: '0612345678',
    assurance: 'CNSS',
    has_medical_alert: true,
    motif_consultation: 'Contrôle implant 36',
  },
};

const json = (body, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) });
const server = await createServer({ server: { host: '127.0.0.1', port: 4193, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

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
    if (url.pathname === '/api/mobile/refresh-token') return route.fulfill(json({}, 401));
    return route.fulfill(json({}));
  });
  await page.goto('http://127.0.0.1:4193/mobile-m6-a-before.html', { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Dossier patient', exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  await page.getByText('BENNANI Sara', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });

  const metrics = await page.evaluate(() => {
    const root = document.documentElement;
    const actionLabels = Array.from(document.querySelectorAll('a,button')).map(el => (el.textContent || '').replace(/\s+/g, ' ').trim());
    const controls = Array.from(document.querySelectorAll('[data-m4a-touch]')).map(el => {
      const rect = el.getBoundingClientRect();
      return { text: (el.textContent || '').replace(/\s+/g, ' ').trim(), width: rect.width, height: rect.height };
    });
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      actionLabels,
      controls,
      hasCameraFileInput: Boolean(document.querySelector('input[type="file"][accept*="image"]')),
      hasClinicalPhotoAction: actionLabels.some(label => /photo clinique|prendre.*photo|photo/i.test(label)),
    };
  });
  const name = `patient-${width}x${height}`;
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
  const record = { name, width, height, metrics, errors };
  captures.push(record);
  await fs.writeFile(`${output}/${name}.json`, JSON.stringify(record, null, 2));
  await context.close();
}

try {
  await capture(390, 844);
  await capture(430, 932);
  await capture(768, 1024);
  const report = {
    productHead,
    count: captures.length,
    captures,
    photoActionAbsent: captures.every(item => !item.metrics.hasClinicalPhotoAction),
    cameraInputAbsent: captures.every(item => !item.metrics.hasCameraFileInput),
    existingActions: captures[0]?.metrics.actionLabels || [],
    minExistingTouchHeight: Math.min(...captures.flatMap(item => item.metrics.controls.map(control => control.height))),
    noHorizontalOverflow: captures.every(item => !item.metrics.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.count !== 3 || !report.photoActionAbsent || !report.cameraInputAbsent || !report.noHorizontalOverflow || !report.noUnexpectedRuntimeErrors) {
    throw new Error('M6-A BEFORE evidence gate failed');
  }
} finally {
  await browser.close();
  await server.close();
}
