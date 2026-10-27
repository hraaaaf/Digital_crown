/**
 * Synthetic browser evidence for G3. ZERO real backend, storage or patient.
 * Playwright intercepts all G3 requests and provides explicit fake receipts.
 * Chromium responsive layouts and CSS 200% text scaling are NOT native
 * Windows NVDA / browser zoom / PostgreSQL clinical FUE certification.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const SHA = process.env.G3_SOURCE_HEAD || '';
const DIRECTORY = path.resolve('..', 'artifacts/cb03-g3-synthetic-visual');
const ID = 'd4a97731-cdcb-4b9c-94d3-f1d21c242a21';
const PATIENT = { id: 21, nom: 'Benali', prenom: 'Salma', numero_dossier: 'S-21' };
fs.mkdirSync(DIRECTORY, { recursive: true });

const browser = await chromium.launch({ headless: true });
const results = [];
try {
  for (const width of [390, 430, 1280, 1600]) {
    const context = await browser.newContext({
      viewport: { width, height: 900 },
      deviceScaleFactor: 1,
      locale: 'fr-FR',
    });
    const page = await context.newPage();
    const errors = [];
    let prepared = 0, confirmed = 0;
    page.on('pageerror', e => errors.push(e.message));

    await page.route('**/api/bot/guided/**', async route => {
      const request = route.request();
      const origin = 'http://127.0.0.1:5173';
      const headers = {
        'access-control-allow-origin': origin,
        'access-control-allow-credentials': 'true',
        'access-control-allow-methods': 'GET,POST,OPTIONS',
        'access-control-allow-headers': 'authorization,content-type',
        'content-type': 'application/json',
      };
      if (request.method() === 'OPTIONS') {
        await route.fulfill({ status: 204, headers });
        return;
      }
      let payload;
      if (request.method() === 'POST' && request.url().endsWith('/prepare-appointment')) {
        prepared++;
        const data = request.postDataJSON();
        if (data.utterance !== 'Prépare un RDV demain 10h pour Mme Benali contrôle'
            || data.praticien_id !== 9 || data.duration_minutes !== 30) {
          throw new Error('Unexpected preparation payload');
        }
        payload = {
          status: 'prepared', executable: false, preparation_id: ID,
          expires_at: '2026-11-01T12:30:00',
          summary: {
            patient: PATIENT, praticien_id: 9, resource_id: null,
            datetime_start: '2026-11-07T10:00:00',
            duration_minutes: 30, motif: 'CONTROLE',
          },
        };
      } else if (request.method() === 'POST' && request.url().endsWith('/confirm')) {
        confirmed++;
        const data = request.postDataJSON();
        if (data.preparation_id !== ID || data.confirm !== true ||
            Object.keys(data).length !== 2) {
          throw new Error('Unsafe confirmation body');
        }
        payload = {
          preparation_id: ID, status: 'executed', action_type: 'CREATE_APPOINTMENT',
          result: { appointment_id: 81, status: 'CREATED' },
        };
      } else {
        throw new Error('Unexpected endpoint or method: ' + request.method() + ' ' + request.url());
      }
      await route.fulfill({ status: 200, headers, body: JSON.stringify(payload) });
    });
    await page.goto('http://127.0.0.1:5173/cb03-g3-visual-lab.html', {
      waitUntil: 'networkidle',
    });

    const panel = page.getByRole('region', { name: 'CB-03 G3 — actions guidées' });
    await panel.waitFor();
    const confirm = page.getByRole('button', { name: 'Confirmer explicitement cette action' });
    if (await confirm.count()) throw new Error('Confirmation visible before server preparation');
    if (prepared !== 0 || confirmed !== 0) throw new Error('Unexpected auto POST on mount');

    await page.screenshot({ path: path.join(DIRECTORY, 'g3-' + width + '-start.png'), fullPage: true });
    await page.getByRole('textbox', { name: 'Votre demande en français' })
      .fill('Prépare un RDV demain 10h pour Mme Benali contrôle');
    await page.getByRole('button', { name: /Vérifier et préparer/ }).click();
    await page.getByText('Salma Benali · Dossier S-21').waitFor();
    if (await confirm.isEnabled()) throw new Error('Confirm enabled without explicit acknowledgement');
    if (prepared !== 1 || confirmed !== 0) throw new Error('Unexpected write before confirmation');

    await page.screenshot({ path: path.join(DIRECTORY, 'g3-' + width + '-prepared.png'), fullPage: true });
    await page.getByRole('checkbox', { name: /J’ai vérifié le patient/ }).check();
    if (!(await confirm.isEnabled())) throw new Error('Explicit confirm not enabled after checkbox');
    await confirm.click();
    await page.getByText(/Action exécutée et vérifiée/).waitFor();
    if (confirmed !== 1 || prepared !== 1) throw new Error('Duplicate or missing confirmation');
    if (await confirm.count()) throw new Error('Confirm resurrected after execution');
    await page.screenshot({ path: path.join(DIRECTORY, 'g3-' + width + '-executed.png'), fullPage: true });

    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > window.innerWidth + 2
    );
    if (overflow) throw new Error('Horizontal overflow at viewport width ' + width);

    if (width === 390) {
      // CSS font scaling is a separate source/synthetic stress test, NOT
      // native browser zoom and NOT Windows/NVDA FUE evidence.
      await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
      await page.screenshot({
        path: path.join(DIRECTORY, 'g3-390-text-200pct.png'), fullPage: true,
      });
      const textOverflow = await page.evaluate(() =>
        document.documentElement.scrollWidth > window.innerWidth + 2
      );
      if (textOverflow) throw new Error('Horizontal overflow at 200% CSS text scaling');
    }
    if (errors.length) throw new Error('Browser errors: ' + errors.join(' | '));
    results.push({ viewport: width, prepared, confirmed, horizontalOverflow: false,
      screenshots: 3 + (width === 390 ? 1 : 0) });
    await context.close();
  }
} finally {
  await browser.close();
}
const evidence = { source_head: SHA, type: 'synthetic-mocked-browser-only',
  real_backend: false, clinical_write: false, native_zoom: false,
  nvda: false, results };
fs.writeFileSync(path.join(DIRECTORY, 'evidence.json'),
  JSON.stringify(evidence, null, 2) + '\n');
console.log('CB03_G3_SYNTHETIC_VISUAL_PASS', JSON.stringify(evidence));
