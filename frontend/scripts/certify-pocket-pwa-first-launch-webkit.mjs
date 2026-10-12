import fs from 'node:fs';
import { webkit } from 'playwright';

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
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 3, isMobile: true, hasTouch: true, locale: 'fr-FR',
});
const page = await context.newPage();
const evidence = {
  paired: false, todayBoot: false, fiveTabs: false,
  agendaTab: false, plusWorks: false, todayWorks: false,
  persistentRelaunch: false, pwaStandaloneManifest: false,
};
const safePath = url => {
  try { const p = new URL(url).pathname; return p.startsWith('/session/') ? '/session/[REDACTED]' : p; }
  catch { return '[invalid]'; }
};
let errors = 0;
const visited = [];
page.on('framenavigated', frame => {
  if (frame === page.mainFrame()) visited.push(safePath(frame.url()));
});
page.on('pageerror', () => { errors++; });

try {
  await page.goto(fields.POCKET_FUE_LINK, { waitUntil: 'domcontentloaded', timeout: 30000 });
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
  await page.getByLabel("Code d'appairage à 6 chiffres").fill(fields.POCKET_FUE_CODE);
  await page.getByRole('button', { name: "Valider le code d'appairage" }).click();
  await page.getByText('Appairage réussi', { exact: true }).waitFor({ state: 'visible', timeout: 25000 });
  evidence.paired = true;

  try {
    await page.waitForURL(/\/mobile\/dashboard(?:\?.*)?$/, { timeout: 6500 });
  } catch {
    await page.getByRole('link', { name: 'Continuer vers Digital Crown Pocket' }).click({ noWaitAfter: true });
    await page.waitForURL(/\/mobile\/dashboard(?:\?.*)?$/, { timeout: 16000 });
  }
  await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible', timeout: 20000 });
  evidence.todayBoot = true;
  const nav = page.locator('[data-mobile-bottom-nav][data-pocket-glass-nav]');
  await nav.waitFor({ state: 'visible', timeout: 8000 });
  evidence.fiveTabs = (await nav.locator('[data-mobile-nav-item]').count()) === 5;
  if (!evidence.fiveTabs) throw Error('PWA_NAV_NOT_COMPLETE');

  await nav.locator('[data-mobile-nav-item="agenda"]').click();
  await page.locator('[data-dc-pocket-agenda]').waitFor({ state: 'visible', timeout: 8000 });
  evidence.agendaTab = true;

  await nav.locator('[data-mobile-nav-item="more"]').click();
  await page.getByRole('dialog', { name: 'Plus' }).waitFor({ state: 'visible', timeout: 8000 });
  evidence.plusWorks = true;
  await page.getByRole('button', { name: 'Fermer Plus' }).click();

  await nav.locator('[data-mobile-nav-item="today"]').click();
  await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible', timeout: 8000 });
  evidence.todayWorks = true;

  // Reopen the installed PWA's canonical start URL (same browser profile).
  // A lasting device pair must NOT show the scanner a second time.
  await page.goto(origin + '/mobile/dashboard', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.locator('[data-dc-pocket-today]').waitFor({ state: 'visible', timeout: 20000 });
  if (await page.getByText('Compagnon Mobile').count()) throw Error('PWA_REPAIRED_ON_RELAUNCH');
  evidence.persistentRelaunch = true;
  if (errors) throw Error('PWA_RUNTIME_ERRORS');

  await page.screenshot({ path: '/tmp/pocket-pwa-first-launch-after-webkit.png', animations: 'disabled' });
  console.log('FUE_POCKET_APP_LIFECYCLE=' + JSON.stringify(evidence));
} catch {
  await page.screenshot({ path: '/tmp/pocket-pwa-first-launch-failed-webkit.png', animations: 'disabled' }).catch(() => {});
  console.error('FUE_POCKET_APP_LIFECYCLE_FAILED=' + JSON.stringify({
    ...evidence, currentPath: safePath(page.url()), visited: visited.slice(-12), runtimeErrors: errors,
    onboardingVisible: await page.getByText('Compagnon Mobile').count(),
    successVisible: await page.getByText('Appairage réussi', { exact: true }).count(),
  }));
  process.exitCode = 1;
} finally {
  await context.close();
  await browser.close();
}
