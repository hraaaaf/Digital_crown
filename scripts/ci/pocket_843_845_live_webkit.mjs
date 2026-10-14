import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(new URL('../../frontend/package.json', import.meta.url));
const { webkit } = require('playwright');

// True HTTPS test-origin pairing, real ECDH + IndexedDB. Synthetic tenant only.
// Never print capability links, PINs, cookies, JWTs or patient-like payloads.
const proofPath = process.env.FUE_LIVE_BROWSER_CODE_FILE;
if (!proofPath || !fs.existsSync(proofPath)) throw Error('FUE_CODE_MISSING');
const fields = Object.fromEntries(fs.readFileSync(proofPath, 'utf8').split(/\r?\n/)
  .filter(Boolean).map(x => [x.slice(0, x.indexOf('=')), x.slice(x.indexOf('=') + 1)]));
if (fields.POCKET_FUE_READY !== 'true'
  || !/^\d{6}$/.test(fields.POCKET_FUE_CODE || '')
  || !fields.POCKET_FUE_LINK?.startsWith('https://')) throw Error('FUE_CODE_INVALID');
const origin = new URL(fields.POCKET_FUE_LINK).origin;

const browser = await webkit.launch({ headless: true });
const mobileDevice = {
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 3, isMobile: true, hasTouch: true, locale: 'fr-FR',
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
};
// Two independent browser contexts model Safari and iOS Home Screen storage.
// This is a WebKit simulation, NOT a physical Apple "Add to Home Screen" proof.
const safariContext = await browser.newContext({ ...mobileDevice, ignoreHTTPSErrors: true });
const context = await browser.newContext({ ...mobileDevice, ignoreHTTPSErrors: true });
await context.addInitScript(() => {
  Object.defineProperty(navigator, 'standalone', { configurable: true, value: true });
});
const page = await context.newPage();
const evidence = {
  safariClaimsBlocked: false, pwaSeparateStorage: false,
  needsPairingFirstRun: false, paired: false, todayBoot: false, fiveTabs: false,
  agendaTab: false, plusWorks: false, todayWorks: false,
  persistentRelaunch: false, pwaStandaloneManifest: false,
};
const safePath = url => {
  try { const p = new URL(url).pathname; return p.startsWith('/session/') ? '/session/[REDACTED]' : p; }
  catch { return '[invalid]'; }
};
let errors = 0;
const pageErrorDiagnostics = [];
function classifyPageError(error) {
  const msg = String(error?.message || '');
  const categories = [
    [/storage|indexeddb|quota|transaction/i, 'storage'],
    [/crypto|subtle|decrypt|encrypt|ecdh/i, 'crypto'],
    [/fetch|network|load failed|abort/i, 'network'],
    [/permission|notallowed|denied/i, 'permission'],
    [/dynamic import|module|chunk/i, 'module'],
    [/react|hook|render|hydration/i, 'react'],
    [/undefined|null|cannot read/i, 'undefined-access'],
    [/syntax|parse|json/i, 'parse'],
    [/timeout/i, 'timeout'],
  ];
  return {
    errorType: ['TypeError', 'ReferenceError', 'SyntaxError', 'SecurityError', 'Error'].includes(error?.name) ? error.name : 'other',
    category: categories.find(([pattern]) => pattern.test(msg))?.[1] || 'unknown',
    // Property names, not values or URLs, help classify minified runtime errors.
    property: msg.match(/reading ['"]([a-zA-Z_$][a-zA-Z0-9_$]{0,40})['"]/)?.[1] || null,
    // Secret-safe exception signature; no raw message, stack, token, URL or patient content.
    safeName: /^[A-Za-z][A-Za-z0-9]{0,39}$/.test(String(error?.name || '')) ? String(error.name) : 'unknown-name',
    fingerprint: createHash('sha256').update(msg).digest('hex').slice(0,16),
    messageLength: Math.min(msg.length, 10000),
    signature: [
      [/service.?worker|workbox|sw[.]js/i, 'service-worker'],
      [/not.?supported|unsupported/i, 'not-supported'],
      [/not.?allowed|operation is not allowed/i, 'not-allowed'],
      [/quota|indexeddb|database/i, 'storage'],
      [/abort|cancel|interrupted/i, 'aborted'],
      [/import|module|chunk/i, 'module'],
      [/fetch|network|load failed/i, 'network'],
      [/security|certificate|trust|ssl|tls/i, 'tls-security'],
      [/resizeobserver/i, 'resize-observer'],
    ].find(([pattern]) => pattern.test(msg))?.[1] || 'other',
    stackOrigin: /\/assets\/[^\s:]+\.js/.test(String(error?.stack || '')) ? 'built-asset' :
      /\/src\//.test(String(error?.stack || '')) ? 'source' : 'unknown',
  };
}
const visited = [];
let phase = 'initial';
const moduleRequests = [];
page.on('requestfailed', request => {
  const p = safePath(request.url());
  // Do not expose path IDs, tokens or full URLs; only asset type and failure class.
  if (moduleRequests.length < 8) moduleRequests.push({
    asset: p.startsWith('/assets/') ? 'asset' : p.startsWith('/api/') ? 'api' : 'other',
    kind: request.resourceType(),
    failure: /cancel|abort/i.test(request.failure()?.errorText || '') ? 'cancelled' : 'failed',
    phase,
  });
});
page.on('response', response => {
  const p = safePath(response.url());
  if (p.startsWith('/assets/') && response.status() >= 400 && moduleRequests.length < 8)
    moduleRequests.push({ asset: 'asset', kind: 'http', status: response.status(), phase });
});
page.on('framenavigated', frame => {
  if (frame === page.mainFrame()) visited.push(safePath(frame.url()));
});
page.on('pageerror', error => {
  errors++;
  if (pageErrorDiagnostics.length < 3) {
    const diagnostic = classifyPageError(error);
    pageErrorDiagnostics.push({
      ...diagnostic, phase,
      knownModuleLoadFailure: /importing a module script failed|failed to fetch dynamically imported module|load failed/i.test(String(error?.message || '')),
    });
  }
});

try {
  // In Safari, a one-time pairing code must be blocked so it is not consumed
  // in the WRONG storage profile before Pocket has been installed.
  if (origin !== 'https://127.0.0.1:5443') throw Error('NON_LOOPBACK_ORIGIN');
  phase = 'safari-gateway';
  const safari = await safariContext.newPage();
  await safari.goto(fields.POCKET_FUE_LINK, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await safari.getByRole('link', { name: /Continuer vers l.appairage/ }).click();
  await safari.locator('[data-dc-pocket-install-first]').waitFor({ state: 'visible', timeout: 12000 });
  if (!(await safari.getByRole('button', { name: "Valider le code d'appairage" }).isDisabled())) {
    throw Error('SAFARI_CONSUMES_ONE_USE_QR');
  }
  evidence.safariClaimsBlocked = true;
  evidence.localhostHttps = new URL(origin).protocol === 'https:';
  // An installed Pocket instance has its own IndexedDB AND cookie container;
  // the test HTTPS gateway requires each context to open its capability entry.
  await safariContext.close();
  phase = 'pwa-gateway';
  await page.goto(fields.POCKET_FUE_LINK, { waitUntil: 'domcontentloaded', timeout: 30000 });
  evidence.pwaSeparateStorage = (await page.evaluate(() => (navigator).standalone)) === true;
  phase = 'pwa-onboarding';
  await page.getByRole('link', { name: /Continuer vers l.appairage/ }).click();
  const manifest = await page.evaluate(async () => {
    const response = await fetch('/manifest.json');
    if (!response.ok) return null;
    const data = await response.json();
    return { name: data.name, id: data.id, start_url: data.start_url, display: data.display };
  });
  evidence.pwaStandaloneManifest = manifest?.display === 'standalone'
    && manifest?.start_url === '/mobile/dashboard'
    && manifest?.name === 'Digital Crown Pocket' && manifest?.id === '/';
  if (!evidence.pwaStandaloneManifest) throw Error('PWA_MANIFEST_WRONG');
  // First installed-app start without device credentials must require pairing,
  // while preserving the already-authorized synthetic HTTPS test gateway.
  phase = 'unauthenticated-dashboard';
  await page.goto(origin + '/mobile/dashboard', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.getByText('Compagnon Mobile', { exact: true }).waitFor({ state: 'visible', timeout: 20000 });
  if (new URL(page.url()).pathname !== '/mobile/onboarding') throw Error('PWA_UNPAIRED_BYPASS');
  evidence.needsPairingFirstRun = true;
  await page.getByLabel("Code d'appairage à 6 chiffres").fill(fields.POCKET_FUE_CODE);
  await page.getByRole('button', { name: "Valider le code d'appairage" }).click();
  await page.getByText('Appairage réussi', { exact: true }).waitFor({ state: 'visible', timeout: 25000 });
  phase = 'paired';
  evidence.paired = true;
  evidence.realServerPairing = true;

  try {
    await page.waitForURL(/\/mobile\/dashboard(?:\?.*)?$/, { timeout: 6500 });
  } catch {
    await page.getByRole('link', { name: 'Continuer vers Digital Crown Pocket' }).click({ noWaitAfter: true });
    await page.waitForURL(/\/mobile\/dashboard(?:\?.*)?$/, { timeout: 16000 });
  }
  await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible', timeout: 20000 });
  phase = 'dashboard';
  evidence.todayBoot = true;
  // Read ONLY the existence of the stored pairing key, never the token or master key.
  evidence.indexedDbPairingRecord = await page.evaluate(() => new Promise(resolve => {
    const request = indexedDB.open('digital-crown-zka');
    request.onerror = () => resolve(false);
    request.onsuccess = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('secure_keys')) {
        db.close();
        resolve(false);
        return;
      }
      const transaction = db.transaction('secure_keys', 'readonly');
      const lookup = transaction.objectStore('secure_keys').get('zka_credentials');
      lookup.onsuccess = () => {
        const present = lookup.result != null;
        db.close();
        resolve(present);
      };
      lookup.onerror = () => { db.close(); resolve(false); };
    };
  }));
  if (!evidence.indexedDbPairingRecord) throw Error('NO_INDEXEDDB_PAIRING_RECORD');
  const nav = page.locator('[data-mobile-bottom-nav][data-pocket-glass-nav]');
  await nav.waitFor({ state: 'visible', timeout: 8000 });
  evidence.fiveTabs = (await nav.locator('[data-mobile-nav-item]').count()) === 5;
  if (!evidence.fiveTabs) throw Error('PWA_NAV_NOT_COMPLETE');

  await nav.locator('[data-mobile-nav-item="agenda"]').click();
  await page.locator('[data-dc-pocket-agenda]').waitFor({ state: 'visible', timeout: 8000 });
  await page.getByText('6 rendez-vous · vue rapide en lecture seule').waitFor({ state: 'visible', timeout: 12000 });
  for (const treatment of ['Consultation initiale', 'Détartrage', 'Contrôle orthodontique', "Pose d'appareil orthodontique", 'Soin conservateur', 'Contrôle de suivi']) {
    await page.getByText(treatment, { exact: true }).waitFor({ state: 'visible', timeout: 8000 });
  }
  evidence.agendaHasSixDemoActs = true;
  evidence.agendaTab = true;

  await nav.locator('[data-mobile-nav-item="more"]').click();
  await page.getByRole('dialog', { name: 'Plus' }).waitFor({ state: 'visible', timeout: 8000 });
  evidence.plusWorks = true;
  await page.getByRole('button', { name: 'Fermer Plus' }).click();

  await nav.locator('[data-mobile-nav-item="today"]').click();
  await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible', timeout: 8000 });
  evidence.todayWorks = true;

  phase = 'relaunch';
  // Reopen the installed PWA's canonical start URL (same browser profile).
  // A lasting device pair must NOT show the scanner a second time.
  await page.goto(origin + '/mobile/dashboard', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible', timeout: 20000 });
  if (await page.getByText('Compagnon Mobile').count()) throw Error('PWA_REPAIRED_ON_RELAUNCH');
  evidence.persistentRelaunch = true;
  if (errors) throw Error('PWA_RUNTIME_ERRORS');
  if (!evidence.localhostHttps || !evidence.realServerPairing) throw Error('REQUIRED_GATE_NOT_SATISFIED');

  await page.screenshot({ path: '/tmp/pocket-pwa-first-launch-after-webkit.png', animations: 'disabled' });
  // No clinic payloads or codes in CI log output; statuses alone are emitted.
  console.log('FUE_POCKET_APP_LIFECYCLE=' + JSON.stringify(evidence));
} catch {
  await page.screenshot({ path: '/tmp/pocket-pwa-first-launch-failed-webkit.png', animations: 'disabled' }).catch(() => {});
  console.error('FUE_POCKET_APP_LIFECYCLE_FAILED=' + JSON.stringify({
    ...evidence, currentPath: safePath(page.url()), visited: visited.slice(-12), runtimeErrors: errors, pageErrorDiagnostics, moduleRequests,
    onboardingVisible: await page.getByText('Compagnon Mobile').count(),
    successVisible: await page.getByText('Appairage réussi', { exact: true }).count(),
  }));
  process.exitCode = 1;
} finally {
  await safariContext.close().catch(() => {});
  await context.close();
  await browser.close();
}
