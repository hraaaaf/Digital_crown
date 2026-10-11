import fs from 'node:fs';
import { webkit } from 'playwright';

const proofFile = process.env.FUE_LIVE_BROWSER_CODE_FILE;
if (!proofFile || !fs.existsSync(proofFile)) throw new Error('FUE_BROWSER_PRECHECK_MISSING');
const fields = Object.fromEntries(fs.readFileSync(proofFile, 'utf8')
  .split(/\r?\n/).filter(Boolean).map(line => {
    const equal = line.indexOf('=');
    return equal < 0 ? [line, ''] : [line.slice(0, equal), line.slice(equal + 1)];
  }));
if (fields.POCKET_FUE_READY !== 'true' || !/^\d{6}$/.test(fields.POCKET_FUE_CODE ?? '')
    || !fields.POCKET_FUE_LINK?.startsWith('https://')) {
  throw new Error('FUE_BROWSER_PRECHECK_INVALID');
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
let failure = false;
try {
  // Real HTTPS Cloudflare gateway, real FastAPI code, real Safari-engine ECDH,
  // actual IndexedDB, no Playwright route mocks and no fake success injection.
  await page.goto(fields.POCKET_FUE_LINK, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.getByLabel("Code d'appairage à 6 chiffres").fill(fields.POCKET_FUE_CODE);
  await page.getByRole('button', { name: "Valider le code d'appairage" }).click();
  await page.getByText('Appairage réussi', { exact: true }).waitFor({ state: 'visible', timeout: 20000 });
  console.log('FUE_BROWSER_REAL_PAIRING_ACK=true');
  // The actual reported iPhone failure was a success page without a Dashboard.
  await page.waitForURL(/\/mobile\/dashboard\?tab=agenda/, { timeout: 15000 });
  await page.locator('[data-mobile-bottom-nav][data-pocket-glass-nav]').waitFor({ state: 'visible', timeout: 20000 });
  const targets = await page.locator('[data-mobile-bottom-nav] [data-mobile-nav-item]').count();
  if (targets !== 5) throw new Error('FUE_BROWSER_NAV_ALIGNMENT_FAILURE');
  if (await page.getByText('Déverrouiller Digital Crown', { exact: true }).count()) {
    throw new Error('FUE_BROWSER_FALSE_BIOMETRIC_GATE');
  }
  await page.screenshot({ path: '/tmp/pocket-fue-webkit-real-dashboard.png', animations: 'disabled' });
  console.log('FUE_BROWSER_REAL_AGENDA_ROUTE=true');
  console.log('FUE_BROWSER_REAL_GLASS_NAV_5=true');
} catch {
  failure = true;
  await page.screenshot({ path: '/tmp/pocket-fue-webkit-failed.png', animations: 'disabled' }).catch(() => {});
  // Never log the one-shot code, cookie, session capability, public URL or JWT.
  console.error('FUE_BROWSER_TRANSITION_FAILED');
} finally {
  await context.close();
  await browser.close();
}
if (failure) process.exitCode = 1;
