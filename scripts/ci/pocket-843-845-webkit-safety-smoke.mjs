// Pocket #843/#845 first safety gate on the CURRENT product SHA.
// Local-only WebKit browser simulation (NOT an iPhone, production auth, or HTTPS pairing).
import { createRequire } from 'node:module';
const require = createRequire(new URL('../../frontend/package.json', import.meta.url));
const { webkit } = require('playwright');

const origin = 'http://127.0.0.1:5173';
const iphoneUA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';
const browser = await webkit.launch({ headless: true });
const evidence = {
  scope: 'isolated-loopback-WebKit-only',
  exactCommit: process.env.GITHUB_SHA || 'local',
  safariInstallGuard: false,
  safariOneUseClaimBlocked: false,
  installedFirstBootGuard: false,
  installedCodeRefusal: false,
  manifestMatches: false,
  realHttpsPairing: 'NOT_TESTED',
  physicalIphone: 'NOT_TESTED',
};
let ctx;
try {
  ctx = await browser.newContext({ userAgent: iphoneUA, viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true });
  await ctx.addInitScript(() => Object.defineProperty(navigator, 'standalone', {configurable: true, value: false}));
  const safari = await ctx.newPage();
  let safariClaims = 0;
  safari.on('request', request => {
    if (new URL(request.url()).pathname.includes('/api/mobile/claim-token')) safariClaims++;
  });
  await safari.route('**/api/**', route => route.fulfill({status: 401, contentType: 'application/json', body: '{"detail":"Refus de test"}'}));
  await safari.goto(origin + '/mobile/onboarding?token=synthetic-not-valid', {waitUntil: 'domcontentloaded'});
  await safari.locator('[data-dc-pocket-install-first]').waitFor({state: 'visible', timeout: 25000});
  const btn = safari.getByRole('button', {name: "Valider le code d'appairage"});
  if (!await btn.isDisabled()) throw Error('Safari must block one-use claim before installation');
  evidence.safariInstallGuard = true;
  if (safariClaims !== 0) throw Error('Safari unexpectedly consumed one-use claim');
  evidence.safariOneUseClaimBlocked = true;
  await ctx.close(); ctx = null;

  ctx = await browser.newContext({ userAgent: iphoneUA, viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true });
  await ctx.addInitScript(() => Object.defineProperty(navigator, 'standalone', {configurable: true, value: true}));
  await ctx.route('**/api/**', route => route.fulfill({status: 401, contentType:'application/json', body: '{"detail":"Refus de test"}'}));
  const installed = await ctx.newPage();
  await installed.goto(origin + '/mobile/dashboard', {waitUntil: 'domcontentloaded'});
  await installed.getByText('Compagnon Mobile', {exact: true}).waitFor({state:'visible',timeout:25000});
  if (new URL(installed.url()).pathname !== '/mobile/onboarding') throw Error('Unauthorized dashboard access');
  if (await installed.locator('[data-dc-pocket-today]').count()) throw Error('Protected dashboard visible before pairing');
  evidence.installedFirstBootGuard = true;
  const manifest = await installed.evaluate(async () => {
    const r = await fetch('/manifest.json'); return r.ok ? r.json() : null;
  });
  if (!manifest || manifest.start_url !== '/mobile/dashboard' || manifest.id !== '/' || manifest.display !== 'standalone') {
    throw Error('PWA manifest identity drift');
  }
  evidence.manifestMatches = true;

  const input = installed.getByLabel("Code d'appairage à 6 chiffres");
  await input.fill('123456');
  await installed.getByRole('button', {name: "Valider le code d'appairage"}).click();
  await installed.getByText("Échec de l'appairage").waitFor({state:'visible',timeout:12000});
  if (await installed.getByText('Appairage réussi', {exact: true}).count()) throw Error('False successful pairing after 401');
  evidence.installedCodeRefusal = true;
  console.log('POCKET_REQUAL_WEBKIT_SAFE=' + JSON.stringify(evidence));
} catch (error) {
  console.error('POCKET_REQUAL_WEBKIT_FAIL=' + JSON.stringify({ ...evidence, kind: error?.name || 'Error' }));
  process.exitCode = 1;
} finally {
  await ctx?.close().catch(() => {});
  await browser.close();
}
