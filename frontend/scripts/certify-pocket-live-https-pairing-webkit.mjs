import fs from 'node:fs';
import { webkit } from 'playwright';

// This only runs in a disposable synthetic GitHub Actions runner; do not emit
// the one-shot code, session URL, cookie, JWT or clinic-like payload into CI.
const proofFile = process.env.FUE_LIVE_BROWSER_CODE_FILE;
if (!proofFile || !fs.existsSync(proofFile)) throw new Error('FUE_BROWSER_CODE_FILE_MISSING');
const fields = Object.fromEntries(fs.readFileSync(proofFile, 'utf8')
  .split(/\r?\n/).filter(Boolean).map(line => {
    const equal = line.indexOf('=');
    return equal < 0 ? [line, ''] : [line.slice(0, equal), line.slice(equal + 1)];
  }));
if (fields.POCKET_FUE_READY !== 'true'
    || !/^\d{6}$/.test(fields.POCKET_FUE_CODE ?? '')
    || !fields.POCKET_FUE_LINK?.startsWith('https://')) {
  throw new Error('FUE_BROWSER_CODE_INVALID');
}

const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  isMobile: true,
  hasTouch: true,
  deviceScaleFactor: 3,
  locale: 'fr-FR',
});
const page = await context.newPage();
const evidence = { realHttps: false, pairingSuccess: false, dashboardAgenda: false, plusOpens: false, todayResponds: false };
const transitions = [];
const apiStatuses = [];
const assetStatuses = [];
const failedPaths = [];
let jsErrors = 0;
let consoleErrors = 0;
const safePath = (url) => {
  try {
    const p = new URL(url).pathname;
    return p.startsWith('/session/') ? '/session/[REDACTED]' : p;
  } catch { return '[invalid-url]'; }
};
page.on('framenavigated', frame => {
  if (frame === page.mainFrame()) transitions.push(safePath(frame.url()));
});
page.on('response', response => {
  const p = safePath(response.url());
  if (p.startsWith('/api/mobile/')) apiStatuses.push({ path: p, status: response.status() });
  if (p.startsWith('/assets/')) assetStatuses.push({ ext: p.endsWith('.js') ? 'js' : p.endsWith('.css') ? 'css' : 'other', status: response.status() });
});
page.on('requestfailed', request => {
  const p = safePath(request.url());
  failedPaths.push(p.startsWith('/assets/') ? '/assets/[REDACTED]' : p);
});
page.on('pageerror', () => { jsErrors++; });
page.on('console', entry => { if (entry.type() === 'error') consoleErrors++; });
try {
  await page.goto(fields.POCKET_FUE_LINK, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.getByRole('link', { name: /Continuer vers l.appairage/ }).click();
  await page.getByLabel("Code d'appairage à 6 chiffres").fill(fields.POCKET_FUE_CODE);
  evidence.realHttps = page.url().startsWith('https:');
  await page.getByRole('button', { name: "Valider le code d'appairage" }).click();
  await page.getByText('Appairage réussi', { exact: true }).waitFor({ state: 'visible', timeout: 20000 });
  evidence.pairingSuccess = true;
  evidence.afterClaimPath = safePath(page.url());
  evidence.secureContext = await page.evaluate(() => window.isSecureContext);
  evidence.cookiePresent = (await context.cookies()).some(cookie => cookie.name === 'pocket_fue');
  // Observe whether React auto-navigation works. If not, exercise the native
  // iPhone fallback link exactly as the owner does.
  try {
    await page.waitForURL(/\/mobile\/dashboard\?tab=agenda/, { timeout: 4000 });
  } catch {
    evidence.autoTimeoutPath = safePath(page.url());
    await page.getByRole('link', { name: 'Continuer vers Agenda' }).click({ noWaitAfter: true });
    evidence.afterClickPath = safePath(page.url());
    await page.waitForURL(/\/mobile\/dashboard\?tab=agenda/, { timeout: 15000 });
  }
  await page.locator('[data-dc-pocket-agenda]').waitFor({ state: 'visible', timeout: 20000 });
  const nav = page.locator('[data-mobile-bottom-nav][data-pocket-glass-nav]');
  await nav.waitFor({ state: 'visible' });
  const tabs = nav.locator('[data-mobile-nav-item]');
  if (await tabs.count() !== 5) throw new Error('FUE_NAV_TARGET_COUNT');
  // A client-rendered Agenda without a usable backend is not a green FUE.
  await page.getByText('Agenda non chargé. Synchronisez votre Pocket avec le cabinet.')
    .waitFor({ state: 'hidden', timeout: 12000 });
  evidence.dashboardAgenda = true;
  await nav.locator('[data-mobile-nav-item="more"]').click();
  await page.getByRole('dialog', { name: 'Plus' }).waitFor({ state: 'visible', timeout: 7000 });
  evidence.plusOpens = true;
  await page.getByRole('button', { name: 'Fermer Plus', exact: true }).click();
  await nav.locator('[data-mobile-nav-item="today"]').click();
  await page.locator('[data-mobile-nav-item="today"][aria-current="page"]').waitFor({ timeout: 7000 });
  evidence.todayResponds = true;
  await page.screenshot({ path: '/tmp/pocket-fue-webkit-real-dashboard.png', animations: 'disabled' });
  console.log('FUE_REAL_WEBKIT_RESULT=' + JSON.stringify(evidence));
} catch (error) {
  await page.screenshot({ path: '/tmp/pocket-fue-webkit-failed.png', animations: 'disabled' }).catch(() => {});
  // Only publish a controlled error category, not the URL nor credentials.
  const summary = {
    ...evidence, currentPath: safePath(page.url()),
    transitions: transitions.slice(-12),
    apiStatuses: apiStatuses.slice(-20),
    assets: { total: assetStatuses.length, jsLoaded: assetStatuses.filter(x => x.ext === 'js' && x.status === 200).length, failed: assetStatuses.filter(x => x.status >= 400).slice(-8) },
    failedPaths: failedPaths.slice(-12),
    jsErrors, consoleErrors,
    document: await page.evaluate(() => ({
      readyState: document.readyState,
      hasAppModule: !!document.querySelector('script[type="module"]'),
      hasReactRoot: !!document.getElementById('root'),
      currentPath: window.location.pathname,
      hasSessionStorage: !!window.sessionStorage,
    })).catch(() => ({ error: true })),
    stillOnSuccess: (await page.getByText('Appairage réussi', { exact: true }).count()) > 0,
    hasAgenda: (await page.locator('[data-dc-pocket-agenda]').count()) > 0,
    hasBiometricGate: (await page.getByText('Accès mobile protégé').count()) > 0,
  };
  console.error('FUE_REAL_WEBKIT_FAILURE=' + JSON.stringify(summary));
  process.exitCode = 1;
} finally {
  await context.close();
  await browser.close();
}
