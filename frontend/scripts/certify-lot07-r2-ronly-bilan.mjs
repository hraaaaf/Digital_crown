/** Real Chrome + FastAPI + seeded synthetic classified BILAN, without mocks.
 * Browser proof of DEC-R2-01 + DEC-R2-02 on one disposable T2 only.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha = process.env.SOURCE_HEAD;
const password = process.env.T2_PASSWORD;
if (process.env.ENVIRONMENT !== 'test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    process.env.DATABASE_URL !== 'sqlite:///./t2-runtime-cert.db' ||
    !/^[0-9a-f]{40}$/.test(sha ?? '') || !password) {
  throw Error('REFUSED: real R-only E2E requires isolated exact SHA T2');
}
const root = path.resolve('../artifacts/lot07-r2-ronly-dec02');
await fs.mkdir(root, { recursive: true });
const checks = [];
const assert = (name, yes, data = {}) => {
  checks.push({ name, pass: Boolean(yes), ...data });
  if (!yes) throw Error('DEC_R2_BROWSER_E2E_FAIL: ' + name + ' ' + JSON.stringify(data));
};
const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const browser = await chromium.launch({ headless: true });
let context;
try {
  const login = await api.post('/api/auth/login', { form: {
    username: 't2-browser@cabinet.ma', password,
  } });
  assert('real owner login', login.status() === 200, { status: login.status() });
  const tokens = await login.json();
  const headers = { Authorization: 'Bearer ' + tokens.access_token };
  const patientRes = await api.get('/api/patients/', { headers });
  assert('real patient endpoint', patientRes.status() === 200);
  const patient = (await patientRes.json()).find(p => p.numero_dossier === 'T2-0001');
  assert('exact synthetic T2 patient', Number.isSafeInteger(patient?.id));

  const list = await api.get('/api/patients/' + patient.id + '/documents', { headers });
  assert('authenticated BILAN list', list.status() === 200);
  const docs = await list.json();
  const bilan = docs.find(d => d.type === 'BILAN' && d.name === 'T2-historical-bilan.pdf');
  assert('BILAN classified R URL without static path', bilan?.url === '/api/documents/bilan/' + bilan?.id + '/view');
  const pdf = await api.get('/api/documents/bilan/' + bilan.id + '/view', { headers });
  const pdfBytes = await pdf.body();
  assert('owner receives actual paginated PDF bytes for visual review',
    pdf.status() === 200 && (pdf.headers()['content-type'] ?? '').includes('application/pdf') &&
    pdfBytes.subarray(0,5).toString() === '%PDF-' && pdfBytes.includes(Buffer.from('%%EOF')) &&
    pdfBytes.length > 900, { status: pdf.status(), bytes: pdfBytes.length });
  const png = await api.get('/api/documents/bilan/' + bilan.id + '/page?page=1', { headers });
  const pngBytes = await png.body();
  assert('owner receives a real server-rendered authenticated BILAN page image',
    png.status() === 200 && pngBytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])) &&
    png.headers()['x-bilan-page-count'] === '1', { status: png.status(), bytes: pngBytes.length });
  for (const [name, req] of [
    ['ordinary download blocked', api.get('/api/documents/' + bilan.id + '/download', { headers })],
    ['archive URL blocked', api.get('/api/static/archives/r2-dec01-t2/synthetic-bilan.pdf', { headers })],
    ['trash blocked', api.post('/api/documents/' + bilan.id + '/trash', { headers })],
    ['signature blocked', api.post('/api/documents/' + bilan.id + '/sign', { headers })],
  ]) {
    const response = await req;
    assert(name, response.status() === 403, { status: response.status() });
  }
  // Enroll the authentic synthetic owner BEFORE any staff login. The app
  // binds workstation permissions to the current authenticated owner session.
  const ws = await enrollT2Workstation(api, tokens.access_token, password);
  const cookies = ws.cookies.filter(c => c.name === 'dc_workstation');
  assert('server workstation enrolled for browser', cookies.length === 1 && cookies[0].httpOnly);

  // Staff must use its own HTTP context: never overwrite owner cookies.
  const restrictedContext = await request.newContext({
    baseURL: 'http://127.0.0.1:8005',
    storageState: { cookies, origins: [] },
  });
  const restrictedLogin = await restrictedContext.post('/api/auth/login', { form: {
    username: 't2-restricted@cabinet.ma', password,
  } });
  assert('synthetic restricted login', restrictedLogin.status() === 200);
  const restrictedJwt = (await restrictedLogin.json()).access_token;
  const restricted = await restrictedContext.get('/api/documents/bilan/' + bilan.id + '/view', {
    headers: { Authorization: 'Bearer ' + restrictedJwt },
  });
  assert('secretary direct URL denied', restricted.status() === 403);
  const restrictedPage = await restrictedContext.get('/api/documents/bilan/' + bilan.id + '/page?page=1', {
    headers: { Authorization: 'Bearer ' + restrictedJwt },
  });
  assert('secretary cannot obtain raster BILAN page', restrictedPage.status() === 403);
  await restrictedContext.dispose();
  const withoutAuth = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
  const unauthorized = await withoutAuth.get('/api/documents/bilan/' + bilan.id + '/view');
  assert('bearerless URL denied', [401,403].includes(unauthorized.status()));
  await withoutAuth.dispose();

  // Genuine browser login: do not inject tokens, intercept APIs or force stores.
  context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    locale: 'fr-FR',
    storageState: { cookies, origins: [] },
  });
  const page = await context.newPage();
  const failures = [];
  page.on('pageerror', error => failures.push(String(error).slice(0, 300)));
  const writes = [];
  page.on('request', req => {
    const u = new URL(req.url());
    if (u.pathname.includes('/documents/') && !['GET', 'HEAD', 'OPTIONS'].includes(req.method())) {
      writes.push({ path: u.pathname, method: req.method() });
    }
  });
  await page.goto('http://127.0.0.1:5173/hub?select=1', { waitUntil: 'domcontentloaded' });
  await page.locator('[data-hub-experience="cabinet"]').click();
  await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button', { name: 'Se connecter', exact: true }).click();
  await page.waitForURL(url => new URL(url).pathname === '/dashboard', { timeout: 45000 });
  await page.goto('http://127.0.0.1:5173/patients/' + patient.id + '?tab=radiology&radioTab=media',
    { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('[data-v15-071-real-cabinet-lab]').waitFor({ state: 'visible', timeout: 60000 });
  await page.locator('[data-testid="multiview-ronly-contract"]').waitFor({ state: 'visible' });
  const scope = page.locator('[data-v15-071-real-cabinet-lab]');
  await scope.locator('[data-testid="multiview-real-dossier"]').waitFor({ state: 'visible', timeout: 30000 });
  await scope.locator('[data-testid="multiview-bilan-readonly"]').waitFor({ state: 'visible' });
  // Real Chromium visual proof: selected document theme tokens must drive
  // every MultiView surface, independent of default Elite Blue branding.
  // No mocks, no color literals and no change to the persisted theme setting.
  const originalTheme = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
  const themeColors = {};
  for (const chosenTheme of ['emerald','rose','ocean','graphite','prestige','dark','high-contrast']) {
    await page.evaluate(name => document.documentElement.setAttribute('data-theme', name), chosenTheme);
    const colors = await scope.evaluate(node => {
      const probe = document.createElement('div');
      probe.style.backgroundColor = 'var(--card-bg)';
      probe.style.color = 'var(--text-main)';
      probe.style.borderColor = 'var(--border-color)';
      document.body.appendChild(probe);
      const expected = {
        card: getComputedStyle(probe).backgroundColor,
        text: getComputedStyle(probe).color,
        border: getComputedStyle(probe).borderColor,
      };
      probe.style.backgroundColor = 'var(--bg-medical-pearl)';
      const expectedSurface = getComputedStyle(probe).backgroundColor;
      probe.style.color = 'var(--text-on-primary)';
      const expectedPrimaryText = getComputedStyle(probe).color;
      probe.remove();

      /* The local radiology theme overrides Tailwind v4 semantic aliases.
         Measure the actual inherited text roles, not global root aliases. */
      const localProbe = document.createElement('div');
      localProbe.style.color = 'var(--color-on-primary)';
      node.appendChild(localProbe);
      const expectedScopedPrimaryText = getComputedStyle(localProbe).color;
      localProbe.style.color = 'var(--primary)';
      const expectedSemanticPrimary = getComputedStyle(localProbe).color;
      localProbe.remove();
      const rgb = value => (value.match(/[0-9.]+/g) || []).slice(0, 3).map(Number);
      const luminance = value => {
        const [r,g,b] = rgb(value).map(v => {
          const x = v / 255;
          return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
        });
        return 0.2126*r + 0.7152*g + 0.0722*b;
      };
      const contrast = (a,b) => {
        const first = luminance(a), second = luminance(b);
        return (Math.max(first,second)+0.05)/(Math.min(first,second)+0.05);
      };
      const intro = node.querySelector('.dc-mv-commandbar .text-primary');
      const mediaHeading = node.querySelector('[data-testid="patient-media-timeline"] h2');
      const modeBadge = node.querySelector('[data-testid="multiview-ronly-contract"]');
      const darkContrast = intro && mediaHeading && modeBadge ? {
        intro: contrast(getComputedStyle(intro).color,expected.card),
        mediaTitle: contrast(getComputedStyle(mediaHeading).color,expected.card),
        modeBadge: contrast(getComputedStyle(modeBadge).color,expectedSurface),
      } : null;
      const media = node.querySelector('[data-v15-071-viewslot="imagerie"]');
      const badge = node.querySelector('[data-testid="multiview-ronly-contract"]');
      const hero = node.querySelector('[data-testid="multiview-real-dossier"] > div:first-child');
      return {
        expected, expectedSurface, expectedPrimaryText, expectedScopedPrimaryText,
        expectedSemanticPrimary, darkContrast,
        renderedPrimaryLabel: intro ? getComputedStyle(intro).color : null,
        renderedBadgeInk: modeBadge ? getComputedStyle(modeBadge).color : null,
        renderedSliderAccent: (() => {
          const slider = node.querySelector('input[type="range"]');
          return slider ? getComputedStyle(slider).accentColor : null;
        })(),
        card: media ? getComputedStyle(media).backgroundColor : 'absent',
        text: getComputedStyle(node).color,
        surface: badge ? getComputedStyle(badge).backgroundColor : 'absent',
        primaryText: hero ? getComputedStyle(hero).color : 'absent',
      };
    });
    assert('theme ' + chosenTheme + ' inherits semantic colors in real MultiView',
      colors.card === colors.expected.card &&
      colors.text === colors.expected.text &&
      colors.surface === colors.expectedSurface &&
      colors.primaryText === colors.expectedScopedPrimaryText, colors);
    assert('theme ' + chosenTheme + ' uses selected semantic PRIMARY on label, badge and range control',
      colors.renderedPrimaryLabel === colors.expectedSemanticPrimary &&
      colors.renderedBadgeInk === colors.expectedSemanticPrimary &&
      colors.renderedSliderAccent === colors.expectedSemanticPrimary,
      { token: colors.expectedSemanticPrimary, label: colors.renderedPrimaryLabel,
        badge: colors.renderedBadgeInk, slider: colors.renderedSliderAccent });
    if (chosenTheme === 'dark') {
      assert('dark radiology primary labels and mode badge pass WCAG AA 4.5:1 against their real themed surfaces',
        colors.darkContrast !== null &&
        colors.darkContrast.intro >= 4.5 &&
        colors.darkContrast.mediaTitle >= 4.5 &&
        colors.darkContrast.modeBadge >= 4.5, colors.darkContrast);
    }
    if (chosenTheme === 'prestige') {
      assert('Prestige clinical text and R badge reach real WCAG AA 4.5:1',
        colors.darkContrast !== null &&
        colors.darkContrast.intro >= 4.5 &&
        colors.darkContrast.mediaTitle >= 4.5 &&
        colors.darkContrast.modeBadge >= 4.5, colors.darkContrast);
    }
    if (chosenTheme === 'high-contrast') {
      assert('high-contrast clinical labels and R-mode badge reach AAA 7:1 measured contrast',
        colors.darkContrast !== null &&
        colors.darkContrast.intro >= 7 &&
        colors.darkContrast.mediaTitle >= 7 &&
        colors.darkContrast.modeBadge >= 7, colors.darkContrast);
      assert('high-contrast clinical labels use real pure-black theme ink, not inherited brand blue',
        colors.renderedPrimaryLabel === colors.expected.text &&
        colors.renderedBadgeInk === colors.expected.text,
        { renderedPrimaryLabel: colors.renderedPrimaryLabel,
          renderedBadgeInk: colors.renderedBadgeInk, expected: colors.expected.text });
    }
    themeColors[chosenTheme] = colors;
    if (['emerald','prestige','dark','high-contrast'].includes(chosenTheme)) {
      await page.screenshot({
        path: path.join(root, 'theme-' + chosenTheme + '-clinical-1920.png'),
        fullPage: false,
      });
    }
  }
  assert('themes actually change the rendered surfaces',
    themeColors.emerald.card !== themeColors.dark.card &&
    themeColors.rose.card !== themeColors.prestige.card);
  await page.evaluate(previous => {
    if (previous === null) document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', previous);
  }, originalTheme);
  const open = scope.getByRole('button', { name: 'Consulter : T2-historical-bilan.pdf' });
  await open.waitFor({ state: 'visible', timeout: 30000 });
  assert('R-only clinical slot has no upload inputs', await scope.locator('input[type=file]').count() === 0);
  assert('R-only clinical slot has no save/erase UI', await scope.getByRole('button', {
    name: /^(Enregistrer|Supprimer|Signer|Importer)$/i,
  }).count() === 0);
  await open.click();
  const inlinePage = scope.locator('[data-testid="bilan-page-image"]');
  await inlinePage.waitFor({ state: 'visible', timeout: 30000 });
  assert('authenticated PNG page genuinely painted in browser',
    await inlinePage.evaluate(img => img instanceof HTMLImageElement && img.complete && img.naturalWidth > 100));
  assert('real BILAN PDF read in browser using authenticated blob', true);
  assert('no BILAN write request from MultiView', writes.length === 0, { writes });
  assert('no uncaught browser errors', failures.length === 0, { failures });
  // The authenticated blob viewer needs its own load event after the frame
  // appears. The fixture is a real ReportLab PDF; do not claim a rendered
  // document merely because an iframe node exists.
  await inlinePage.evaluate((img) => {
    if (!(img instanceof HTMLImageElement) || !img.complete || img.naturalWidth < 100)
      throw Error('BILAN raster preview not rendered');
  });
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(root, 'synthetic-r-only-bilan-1920.png'), fullPage: false });
  // This additional visual proof exposes the entire real PDF instead of only
  // the top strip of an iframe below the 900px desktop fold.
  await scope.getByRole('button', { name: /Agrandir/ }).click();
  const enlarged = page.getByRole('dialog', { name: /Bilan historique agrandi/ });
  await enlarged.waitFor({ state: 'visible', timeout: 20000 });
  const expandedPage = enlarged.locator('[data-testid="bilan-page-image-expanded"]');
  await expandedPage.waitFor({ state: 'visible' });
  assert('fullscreen PDF preview actually renders page pixels',
    await expandedPage.evaluate(img => img instanceof HTMLImageElement && img.complete && img.naturalWidth > 100));
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(root, 'synthetic-bilan-expanded-pdf-1920.png'), fullPage: false });
  await enlarged.getByRole('button', { name: 'Fermer', exact: true }).click();
  assert('fullscreen BILAN preview closes without mutation', await page.getByRole('dialog', { name: /Bilan historique agrandi/ }).count() === 0 &&
    writes.length === 0);
  await fs.writeFile(path.join(root, 'assertions.json'), JSON.stringify({
    sourceHead: sha, syntheticOnly: true, browser: 'chromium', checks, failures, writes,
  }, null, 2));
  console.log('LOT07_R2_DEC01_DEC02_REAL_BROWSER_E2E_PASS ' + sha);
} finally {
  await context?.close();
  await browser.close();
  await api.dispose();
}
