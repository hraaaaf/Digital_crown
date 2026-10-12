import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const phase = process.env.EVIDENCE_PHASE === 'before' ? 'before' : 'after';
const out = path.resolve(`artifacts/v15-04-5-companion-phone-${phase}`);
await fs.mkdir(out, { recursive: true });
const sha = process.env.EVALUATED_SHA || '';
const viewports = [
  { width: 390, height: 844, label: '390x844' },
  { width: 430, height: 932, label: '430x932' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
];
const scales = [
  { label: 'normal', font: null },
  { label: 'text200', font: '200%' },
];
const accessId = '00000000-0000-0000-0000-000000000101';
const sessionId = 'visual-phone-session';
const browser = await chromium.launch({ headless: true });
const report = [];
try {
  for (const viewport of viewports) {
    for (const scale of scales) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
        acceptDownloads: true,
      });
      const seen = { claims: 0, listings: 0, downloads: 0, phonePurges: 0 };
      await context.route('**/api/workstation/patient-session/claim', async route => {
        seen.claims += 1;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          headers: { 'Cache-Control': 'no-store' },
          body: JSON.stringify({ status: 'identified', sessionId }),
        });
      });
      await context.route('**/api/patient-companion/station-session/**', async route => {
        const uri = route.request().url();
        if (!uri.includes(`/station-session/${sessionId}/`) || !uri.includes(`accessId=${accessId}`)) {
          return route.fulfill({ status: 403, contentType: 'application/json', body: '{"detail":"INVALID_SCOPE"}' });
        }
        if (route.request().method() === 'POST' && uri.includes('/purge?')) {
          seen.phonePurges += 1;
          return route.fulfill({ status: 204, body: '' });
        }
        if (uri.includes('/care-sheet/')) {
          seen.downloads += 1;
          return route.fulfill({
            status: 200,
            contentType: 'application/pdf',
            headers: { 'Cache-Control': 'no-store, private' },
            body: '%PDF-1.4\\n%Synthetic phone-only document fixture\\n%%EOF\\n',
          });
        }
        seen.listings += 1;
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          headers: { 'Cache-Control': 'no-store' },
          body: JSON.stringify({ documents: [{ documentId: 42, kind: 'care_sheet' }, { documentId: 71, kind: 'presence_receipt' }] }),
        });
      });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto('http://127.0.0.1:4197/companion', { waitUntil: 'domcontentloaded', timeout: 30000 });
      // Seed only an isolated encrypted fixture vault; never use patient data.
      await page.evaluate(async ({ accessId }) => {
        const module = await import('/src/features/patient-companion/PatientCompanionStorage.ts');
        await module.PatientCompanionStorage.savePairing({
          accessToken: 'visual-only-phone-token',
          context: {
            access_id: accessId,
            relationship_type: 'SELF',
            patient: { display_name: 'Aya Audit', prenom: 'Aya', nom: 'Audit' },
          },
          pairedAt: new Date().toISOString(),
          expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
        });
      }, { accessId });
      await page.goto(
        'http://127.0.0.1:4197/companion?stationSession=opaque-visual-qr',
        { waitUntil: 'domcontentloaded', timeout: 30000 },
      );
      if (scale.font) {
        await page.evaluate(value => { document.documentElement.style.fontSize = value; }, scale.font);
      }
      await page.locator('[data-station-handoff-status]').waitFor({ timeout: 12000 });
      if (phase === 'after') {
        await page.locator('[data-pc-station-documents]').waitFor({ timeout: 12000 });
        await page.locator('[data-pc-care-sheet-download="42"]').waitFor({ timeout: 12000 });
        await page.locator('[data-pc-presence-receipt-download="71"]').waitFor({ timeout: 12000 });
        // React StrictMode in Vite dev can replay the read-only discovery
        // effect on mount. A successful phone listing is required, but up to
        // two identical GETs are expected in this synthetic development lab.
        if (seen.listings < 1 || seen.listings > 2) {
          throw new Error(`Phone discovery request count unexpected: ${seen.listings}`);
        }
      } else {
        if (await page.locator('[data-pc-station-documents]').count()) {
          throw new Error('BEFORE base unexpectedly contains the new phone document collection surface');
        }
      }
      const filename = `${phase}-companion-phone-${viewport.label}-${scale.label}.png`;
      await page.screenshot({ path: path.join(out, filename), fullPage: false });
      let componentFilename = null;
      if (phase === 'after') {
        componentFilename = `after-companion-document-card-${viewport.label}-${scale.label}.png`;
        await page.locator('[data-pc-station-documents]').screenshot({
          path: path.join(out, componentFilename),
        });
      }
      const layout = await page.evaluate(() => ({
        width: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        documentPickupVisible: Boolean(document.querySelector('[data-pc-station-documents]')),
        presenceReceiptVisible: Boolean(document.querySelector('[data-pc-presence-receipt-download="71"]')),
        phoneDownloadVisible: Boolean(document.querySelector('[data-pc-care-sheet-download="42"]')),
        rawSessionTokenInUrl: location.search.includes('stationSession'),
        text: document.body.innerText.slice(0, 1500),
        overflowCandidates: Array.from(document.querySelectorAll('body *'))
          .map(node => {
            const rect = node.getBoundingClientRect();
            return {
              tag: node.tagName.toLowerCase(),
              className: typeof node.className === 'string' ? node.className.slice(0, 180) : '',
              text: (node.textContent || '').trim().slice(0, 80),
              left: Math.round(rect.left * 10) / 10,
              right: Math.round(rect.right * 10) / 10,
              width: Math.round(rect.width * 10) / 10,
            };
          })
          .filter(node => node.right > window.innerWidth + 1 && node.left < window.innerWidth)
          .slice(0, 15),
      }));
      // BEFORE is a pinned historical revision. Capture its known accessibility
      // defect as evidence instead of demanding that the baseline be fixed.
      // AFTER must have zero horizontal overflow at every viewport and scale.
      if (phase === 'after' && layout.scrollWidth > layout.width) {
        throw new Error(`Phone horizontal overflow: ${layout.scrollWidth} > ${layout.width}; offending DOM: ${JSON.stringify(layout.overflowCandidates)}`);
      }
      if (layout.rawSessionTokenInUrl) throw new Error('Raw station QR leaked into phone URL after claim');
      if (seen.claims !== 1 || seen.downloads !== 0 || seen.phonePurges !== 0 || errors.length) {
        throw new Error(`Phone UI baseline regression: ${JSON.stringify({ seen, errors })}`);
      }
      report.push({
        phase, sha, filename, componentFilename, viewport: viewport.label, scale: scale.label,
        ...layout, overflowPx: Math.max(0, layout.scrollWidth - layout.width),
        claims: seen.claims, listings: seen.listings,
        downloads: seen.downloads, phonePurges: seen.phonePurges, errors,
        scope: 'synthetic app with encrypted local test-only pairing, mocked API responses; not physical phone',
      });
      await context.close();
    }
  }
} finally {
  await browser.close();
}
const evidence = {
  phase, sha, base: phase === 'before' ? sha : null,
  limitations: [
    'Actual Patient Companion React application and encrypted IndexedDB vault',
    'Mocked HTTPS transport API responses; true PDF SHA and deny/expiry cases validated in separate backend/TLS CI',
    'BEFORE records historic layout defects without gating them; AFTER strictly fails on any horizontal overflow',
    'Not a real camera, NFC tag, mobile device, printer, or LAN compatibility proof',
  ],
  report,
};
await fs.writeFile(path.join(out, 'evidence.json'), JSON.stringify(evidence, null, 2));
if (report.length !== 8) throw new Error('Expected 8 matched personal phone captures');
console.log(`04.5 Personal phone ${phase.toUpperCase()} screenshots: ${report.length} verified`);
