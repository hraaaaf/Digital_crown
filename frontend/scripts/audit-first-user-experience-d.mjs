import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');
const root = 'http://127.0.0.1:5173';
const api = 'http://127.0.0.1:8005';
const out = path.resolve('../artifacts/t2-browser/fue-d');
fs.mkdirSync(out, { recursive: true });
const first = await request.newContext({ baseURL: api });
const bootstrap = await first.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password } });
if (!bootstrap.ok()) throw new Error('Owner bootstrap login rejected: ' + bootstrap.status());
const tokens = await bootstrap.json();
const enrolled = await enrollT2Workstation(first, tokens.access_token, password);
await first.dispose();
const stationState = {
  ...enrolled,
  cookies: (enrolled.cookies || []).filter(c => !['access_token', 'refresh_token'].includes(c.name)),
};
const browser = await chromium.launch({ headless: true });
const results = [];
let passed = false;
try {
  for (const profile of [
    { name: 'mobile', width: 390, height: 844, first: 'Mobile' },
    { name: 'desktop', width: 1280, height: 900, first: 'Desktop' },
  ]) {
    const dir = path.join(out, profile.name);
    fs.mkdirSync(dir, { recursive: true });
    const ctx = await browser.newContext({
      viewport: { width: profile.width, height: profile.height },
      colorScheme: 'light',
      storageState: stationState,
    });
    const page = await ctx.newPage();
    const started = Date.now();
    const errors = { page: [], console: [], server: [] };
    const screenshots = [];
    let interactions = 0;
    const snap = async name => {
      const overflow = await page.evaluate(() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > innerWidth + 1);
      const file = name + '.png';
      await page.screenshot({ path: path.join(dir, file), fullPage: name !== '04-validation', animations: 'disabled' });
      screenshots.push({ name, file, ms: Date.now() - started, interactions, overflow });
      if (overflow) throw new Error(profile.name + ' horizontal overflow: ' + name);
    };
    page.on('pageerror', e => errors.page.push(String(e.message)));
    page.on('console', msg => { if (msg.type() === 'error') errors.console.push(msg.text()); });
    page.on('response', res => { if (res.status() >= 500) errors.server.push({ status: res.status(), pathname: new URL(res.url()).pathname }); });
    try {
      await page.goto(root + '/login', { waitUntil: 'domcontentloaded' });
      await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.getByPlaceholder('nom@cabinet.com').waitFor({ state: 'visible', timeout: 15000 });
      await snap('01-before-login');
      await page.getByPlaceholder('nom@cabinet.com').fill('t2-browser@cabinet.ma'); interactions++;
      await page.getByPlaceholder('••••••••').fill(password); interactions++;
      await page.getByRole('button', { name: 'Se connecter', exact: true }).click(); interactions++;
      await page.waitForURL(url => !['/login', '/setup'].includes(url.pathname), { timeout: 20000 });
      const state = await ctx.request.get(api + '/api/clinics/init-status');
      if (state.status() !== 200 || (await state.json()).is_initialized !== true) throw new Error('Cabinet not initialized');
      const authorized = await ctx.request.get(api + '/api/patients/?limit=1');
      if (authorized.status() !== 200) throw new Error('Patient authorization=' + authorized.status());
      await page.goto(root + '/patients', { waitUntil: 'domcontentloaded' }); interactions++;
      await page.getByRole('heading', { name: 'Dossiers Patients' }).waitFor({ timeout: 15000 });
      await snap('02-patient-entry');
      await page.getByRole('link', { name: 'Créer un dossier' }).click(); interactions++;
      await page.waitForURL('**/patients/new');
      await page.locator('input[name="nom"]').waitFor({ state: 'visible' });
      await page.evaluate(() => window.scrollTo(0, 0));
      await snap('03-form-before');
      let posts = 0;
      page.on('request', req => { if (req.method() === 'POST' && new URL(req.url()).pathname === '/api/patients/') posts++; });
      await page.getByRole('button', { name: 'Créer le dossier', exact: true }).click(); interactions++;
      await page.waitForFunction(() => document.activeElement?.getAttribute('name') === 'nom', { timeout: 12000 });
      if (posts !== 0) throw new Error('Invalid form sent create request');
      const required = await page.locator('body').innerText();
      if (!required.includes('Le nom est requis') || !required.includes('Le prénom est requis')) throw new Error('Required-field refusal not understandable');
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.locator('input[name="nom"]').scrollIntoViewIfNeeded();
      await snap('04-validation');
      const idtag = 'FUED-' + profile.name.toUpperCase() + '-' + String(Date.now()).slice(-9);
      const nom = 'FUEDTEST';
      await page.locator('input[name="nom"]').fill(nom); interactions++;
      await page.locator('input[name="prenom"]').fill(profile.first); interactions++;
      await page.locator('input[name="date_naissance"]').fill('1990-01-01'); interactions++;
      await page.locator('select[name="sexe"]').selectOption('F'); interactions++;
      await page.locator('input[name="numero_dossier"]').fill(idtag); interactions++;
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.locator('input[name="nom"]').scrollIntoViewIfNeeded();
      await snap('05-form-filled');
      const createResponse = page.waitForResponse(res => res.request().method() === 'POST' && new URL(res.url()).pathname === '/api/patients/', { timeout: 25000 });
      await page.getByRole('button', { name: 'Créer le dossier', exact: true }).click(); interactions++;
      const response = await createResponse;
      if (!response.ok()) throw new Error('Create HTTP ' + response.status());
      const created = await response.json();
      if (!Number.isInteger(created.id) || created.id <= 0) throw new Error('Create response lacks real positive ID');
      if (String(created.nom).toUpperCase() !== nom || String(created.prenom).toLowerCase() !== profile.first.toLowerCase()) throw new Error('Create ACK identity mismatch');
      const read = await ctx.request.get(api + '/api/patients/' + created.id);
      if (read.status() !== 200) throw new Error('Independent GET patient=' + read.status());
      const persisted = await read.json();
      if (persisted.id !== created.id || String(persisted.nom).toUpperCase() !== nom || String(persisted.prenom).toLowerCase() !== profile.first.toLowerCase()) throw new Error('Persisted record mismatch');
      await page.waitForURL(new RegExp('/patients/' + created.id + '(?:\\?|$)'), { timeout: 15000 });
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.getByText(nom, { exact: false }).first().waitFor({ state: 'visible', timeout: 15000 });
      await snap('06-after-reload');
      const ms = Date.now() - started;
      if (errors.page.length || errors.server.length) throw new Error('Browser/server errors ' + JSON.stringify(errors));
      results.push({ viewport: profile.name, dimensions: [profile.width, profile.height], firstValueMs: ms, interactions, createStatus: response.status(), readStatus: read.status(), patientId: created.id, screenshotCount: screenshots.length, screenshots, errors });
      await ctx.close();
    } catch (e) {
      results.push({ viewport: profile.name, failed: String(e?.stack || e), interactions, screenshots, errors });
      await ctx.close();
      throw e;
    }
  }

  // Independent adversarial permission check: restricted secretary patients=false.
  const restrictedCtx = await request.newContext({ baseURL: api });
  try {
    const auth = await restrictedCtx.post('/api/auth/login', { form: { username: 't2-restricted@cabinet.ma', password } });
    if (!auth.ok()) throw new Error('Restricted persona login status=' + auth.status());
    const restrictedToken = (await auth.json()).access_token;
    const client = await request.newContext({ baseURL: api, storageState: stationState, extraHTTPHeaders: { Authorization: 'Bearer ' + restrictedToken } });
    try {
      const data = { nom: 'FUEDDENIED', prenom: 'Unauthorized', date_naissance: '1990-01-01', sexe: 'F' };
      const read = await client.get('/api/patients/');
      const create = await client.post('/api/patients/', { data });
      const duplicate = await client.post('/api/patients/check-duplicate', { data });
      if ([read.status(), create.status(), duplicate.status()].some(code => code !== 403)) {
        throw new Error('patients=false boundary failed: ' + [read.status(), create.status(), duplicate.status()].join(','));
      }
      results.push({ viewport: 'restricted-api', listStatus: read.status(), createStatus: create.status(), duplicateStatus: duplicate.status() });
    } finally { await client.dispose(); }
  } finally { await restrictedCtx.dispose(); }

  // Security/truth negative matrix on real isolated backend, with enrolled workstation.
  const ownerAuth = await request.newContext({ baseURL: api });
  try {
    const login = await ownerAuth.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password } });
    if (!login.ok()) throw new Error('Negative matrix owner authentication failed');
    const accessToken = (await login.json()).access_token;
    const owner = await request.newContext({ baseURL: api, storageState: stationState, extraHTTPHeaders: { Authorization: 'Bearer ' + accessToken } });
    try {
      const unique = 'FUEDNEG' + Date.now();
      const payload = { nom: unique, prenom: 'Conflict', date_naissance: '1990-01-01', sexe: 'F' };
      const initial = await owner.post('/api/patients/', { data: payload });
      if (initial.status() !== 200) throw new Error('409 fixture creation=' + initial.status());
      const original = await initial.json();
      const conflict = await owner.post('/api/patients/', { data: payload });
      if (conflict.status() !== 409) throw new Error('Duplicate should return 409, got ' + conflict.status());
      const check = await owner.post('/api/patients/check-duplicate', { data: payload });
      if (check.status() !== 200 || (await check.json()).has_duplicate !== true) throw new Error('Duplicate preflight failed');
      const invalid = await owner.post('/api/patients/', { data: { nom: unique + 'BAD', prenom: 'Invalid', date_naissance: '1990-01-01', sexe: '' } });
      if (invalid.status() !== 422) throw new Error('Missing explicit sex should return 422, got ' + invalid.status());
      const after = await owner.get('/api/patients/?search=' + encodeURIComponent(unique));
      if (after.status() !== 200) throw new Error('Duplicate verification search=' + after.status());
      const patients = await after.json();
      const exact = patients.filter(x => x.nom === unique);
      if (exact.length !== 1 || exact[0].id !== original.id) throw new Error('409 produced extra patients or lost original: count=' + exact.length);
      results.push({ viewport: 'negative-api', duplicateStatus: conflict.status(), invalidStatus: invalid.status(), preflightStatus: check.status(), patientCountAfter409: exact.length });
    } finally { await owner.dispose(); }
  } finally { await ownerAuth.dispose(); }

  // Two independently authenticated dentist accounts; never expose another cabinet's patient.
  const foreignAuth = await request.newContext({ baseURL: api });
  try {
    const login = await foreignAuth.post('/api/auth/login', { form: { username: 't2-setup-390@cabinet.ma', password } });
    if (!login.ok()) throw new Error('Foreign owner authentication failed: ' + login.status());
    const token = (await login.json()).access_token;
    const foreignState = await enrollT2Workstation(foreignAuth, token, password);
    const foreign = await request.newContext({ baseURL: api, storageState: foreignState, extraHTTPHeaders: { Authorization: 'Bearer ' + token } });
    try {
      const targetId = results.find(x => x.viewport === 'mobile')?.patientId;
      if (!targetId) throw new Error('Missing target patient');
      const read = await foreign.get('/api/patients/' + targetId);
      if (![403, 404].includes(read.status())) throw new Error('Foreign cabinet read was not denied: ' + read.status());
      results.push({ viewport: 'cross-cabinet-api', foreignReadStatus: read.status() });
    } finally { await foreign.dispose(); }
  } finally { await foreignAuth.dispose(); }

  // Two requests at the same instant should not create two identical patient dossiers.
  const raceAuth = await request.newContext({ baseURL: api });
  try {
    const login = await raceAuth.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password } });
    if (!login.ok()) throw new Error('Parallel authentication failed: ' + login.status());
    const token = (await login.json()).access_token;
    const race = await request.newContext({ baseURL: api, storageState: stationState, extraHTTPHeaders: { Authorization: 'Bearer ' + token } });
    try {
      const nom = 'FUEDRACE' + Date.now();
      const identity = { nom, prenom: 'Parallel', date_naissance: '1990-01-01', sexe: 'F' };
      let a, b;
      try {
        [a, b] = await Promise.all([race.post('/api/patients/', { data: identity }), race.post('/api/patients/', { data: identity })]);
      } catch {
        throw new Error('Double-submit transport error (inspect sanitized backend logs)');
      }
      const codes = [a.status(), b.status()].sort((a, b) => a - b);
      let get;
      try { get = await race.get('/api/patients/?search=' + encodeURIComponent(nom)); }
      catch { throw new Error('Double-submit follow-up GET transport error'); }
      if (get.status() !== 200) throw new Error('Parallel read=' + get.status());
      const exactCount = (await get.json()).filter(x => x.nom === nom).length;
      if (exactCount !== 1 || codes[0] !== 200 || codes[1] !== 409) throw new Error('Double-submit violation: ' + codes.join(',') + ' stored=' + exactCount);
      results.push({ viewport: 'parallel-api', createStatuses: codes, patientCount: exactCount });

      // Two different patients created at once must both succeed, with
      // distinct generated dossier numbers and exact persisted identities.
      const tag = 'FUEDDISTINCT' + Date.now();
      const identities = [
        { nom: tag + 'A', prenom: 'Alpha', date_naissance: '1990-01-01', sexe: 'F' },
        { nom: tag + 'B', prenom: 'Beta', date_naissance: '1990-01-01', sexe: 'F' },
      ];
      let responses;
      try {
        responses = await Promise.all(identities.map(data => race.post('/api/patients/', { data })));
      } catch {
        throw new Error('Concurrent distinct-patient transport failure');
      }
      const distinctStatuses = responses.map(x => x.status());
      if (distinctStatuses.some(code => code !== 200)) {
        throw new Error('Distinct concurrent identities should both create: ' + distinctStatuses.join(','));
      }
      const saved = await Promise.all(responses.map(x => x.json()));
      if (new Set(saved.map(x => x.id)).size !== 2 || new Set(saved.map(x => x.numero_dossier)).size !== 2) {
        throw new Error('Concurrent distinct patient IDs/dossier numbers are not unique');
      }
      const independentReads = await Promise.all(saved.map(x => race.get('/api/patients/' + x.id)));
      if (independentReads.some(x => x.status() !== 200)) {
        throw new Error('Concurrent distinct patient retrieval failed');
      }
      results.push({ viewport: 'parallel-distinct-api', createStatuses: distinctStatuses, uniqueIds: 2, uniqueDossierNumbers: 2 });
    } finally { await race.dispose(); }
  } finally { await raceAuth.dispose(); }

  // Independent mobile browser negative journey: all POSTs below use synthetic identities.
  // Deliberate HTTP 503 responses are Playwright interceptions, not backend outages.
  const uxContext = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: 'light', storageState: stationState });
  const ux = await uxContext.newPage();
  const uxDir = path.join(out, 'adversarial-mobile');
  fs.mkdirSync(uxDir, { recursive: true });
  try {
    await ux.goto(root + '/login', { waitUntil: 'domcontentloaded' });
    await ux.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
    await ux.reload({ waitUntil: 'domcontentloaded' });
    await ux.getByPlaceholder('nom@cabinet.com').fill('t2-browser@cabinet.ma');
    await ux.getByPlaceholder('••••••••').fill(password);
    await ux.getByRole('button', { name: 'Se connecter', exact: true }).click();
    await ux.waitForURL(url => !['/login','/setup'].includes(url.pathname), { timeout: 20000 });
    await ux.goto(root + '/patients/new', { waitUntil: 'domcontentloaded' });
    await ux.locator('input[name="nom"]').waitFor({ state: 'visible' });

    // Real keyboard Tab travel; this does not assert full screen-reader accessibility.
    await ux.locator('input[name="nom"]').focus();
    await ux.keyboard.press('Tab');
    const nextFocus = await ux.evaluate(() => document.activeElement?.getAttribute('name'));
    if (nextFocus !== 'prenom') throw new Error('Keyboard tab progression failed, next=' + nextFocus);
    const identityFieldNames = ['nom', 'prenom', 'date_naissance', 'sexe'];
    const labelProof = await Promise.all(identityFieldNames.map(async name => {
      const field = ux.locator('[name="' + name + '"]');
      return { name, hasAssociatedLabel: await field.evaluate(el => Boolean(el.labels?.length || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby'))) };
    }));
    if (labelProof.some(x => !x.hasAssociatedLabel)) throw new Error('Required identity label inaccessible: ' + JSON.stringify(labelProof));
    const nameHasAssociatedLabel = labelProof[0].hasAssociatedLabel;
    await ux.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
    // Unlike the document-wide overflow check, this also catches text hidden by
    // a local overflow-hidden header (the previous false-negative at 200%).
    const assertHeaderNotClipped = async viewport => {
      const result = await ux.evaluate(() => {
        const heading = [...document.querySelectorAll('h2')].find(el => el.textContent?.trim() === 'Nouveau Patient');
        const header = heading?.parentElement?.parentElement;
        const description = heading?.nextElementSibling;
        if (!header || !description) return { found: false };
        const container = header.getBoundingClientRect();
        const textBounds = [heading, description].flatMap(el => {
          const range = document.createRange();
          range.selectNodeContents(el);
          return Array.from(range.getClientRects(), r => ({ left: r.left, right: r.right }));
        });
        const titleTextNode = heading.firstChild;
        const titleWordFragments = ['Nouveau', 'Patient'].map(word => {
          if (!titleTextNode || titleTextNode.nodeType !== Node.TEXT_NODE) return { word, count: -1 };
          const start = titleTextNode.textContent.indexOf(word);
          if (start < 0) return { word, count: -1 };
          const range = document.createRange();
          range.setStart(titleTextNode, start);
          range.setEnd(titleTextNode, start + word.length);
          return { word, count: range.getClientRects().length };
        });
        return {
          found: true,
          titleWordFragments,
          clipped: textBounds.some(r => r.left < container.left - 1 || r.right > container.right + 1),
          headerScrollWidth: header.scrollWidth,
          headerClientWidth: header.clientWidth,
          documentOverflow: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > innerWidth + 1,
        };
      });
      if (!result.found || result.clipped || result.documentOverflow || result.headerScrollWidth > result.headerClientWidth + 1 || result.titleWordFragments.some(w => w.count !== 1)) {
        throw new Error('200% text size clipping at ' + viewport + ': ' + JSON.stringify(result));
      }
      return result;
    };
    await ux.screenshot({ path: path.join(uxDir, '01-css-text-zoom-200pct.png'), fullPage: true, animations: 'disabled' });
    const textZoomMobile = await assertHeaderNotClipped('390x844');
    await ux.setViewportSize({ width: 1280, height: 900 });
    await ux.screenshot({ path: path.join(uxDir, '01b-css-text-zoom-200pct-desktop.png'), fullPage: true, animations: 'disabled' });
    const textZoomDesktop = await assertHeaderNotClipped('1280x900');
    await ux.setViewportSize({ width: 390, height: 844 });
    await ux.evaluate(() => { document.documentElement.style.fontSize = ''; });

    const identity = 'FUEDUI' + Date.now();
    await ux.locator('input[name="nom"]').fill(identity);
    await ux.locator('input[name="prenom"]').fill('Failclosed');
    await ux.locator('input[name="date_naissance"]').fill('1990-01-01');
    await ux.locator('select[name="sexe"]').selectOption('F');
    await ux.locator('input[name="numero_dossier"]').fill('UI' + String(Date.now()).slice(-9));
    let uiCreatePostCount = 0;
    ux.on('request', req => { if (req.method() === 'POST' && new URL(req.url()).pathname === '/api/patients/') uiCreatePostCount++; });
    const preflightPattern = '**/api/patients/check-duplicate';
    await ux.route(preflightPattern, async route => {
      await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"Synthetic preflight outage"}' });
    });
    const preflight503 = ux.waitForResponse(res => new URL(res.url()).pathname === '/api/patients/check-duplicate' && res.status() === 503, { timeout: 12000 });
    await ux.getByRole('button', { name: 'Créer le dossier', exact: true }).click();
    await preflight503;
    await ux.getByRole('alert').getByText('Vérification anti-doublon indisponible.', { exact: false }).waitFor({ state: 'visible', timeout: 12000 });
    if (uiCreatePostCount !== 0 || !ux.url().endsWith('/patients/new')) throw new Error('Preflight 503 must not create patient or navigate');
    await ux.getByText('Service temporairement indisponible (503)', { exact: true }).waitFor({ state: 'visible', timeout: 12000 });
    await ux.locator('form [role="alert"]').scrollIntoViewIfNeeded();
    await ux.screenshot({ path: path.join(uxDir, '02-preflight-503-refused.png'), fullPage: false, animations: 'disabled' });
    await ux.unroute(preflightPattern);

    // Simulate a 503 from POST only, after a real successful anti-duplicate preflight.
    const createPattern = '**/api/patients/';
    await ux.route(createPattern, async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"Synthetic create outage"}' });
      } else {
        await route.continue();
      }
    });
    const create503 = ux.waitForResponse(res => new URL(res.url()).pathname === '/api/patients/' && res.request().method() === 'POST' && res.status() === 503, { timeout: 12000 });
    await ux.getByRole('button', { name: 'Créer le dossier', exact: true }).click();
    await create503;
    await ux.getByRole('alert').getByText('Création non confirmée.', { exact: false }).waitFor({ state: 'visible', timeout: 12000 });
    if (uiCreatePostCount !== 1 || !ux.url().endsWith('/patients/new')) throw new Error('Create 503 must not claim success or navigate');
    await ux.locator('form [role="alert"]').scrollIntoViewIfNeeded();
    await ux.screenshot({ path: path.join(uxDir, '03-create-503-refused.png'), fullPage: false, animations: 'disabled' });
    await ux.unroute(createPattern);

    // Genuine double mouse-click through the rendered button with real backend.
    const button = ux.getByRole('button', { name: 'Créer le dossier', exact: true });
    await button.scrollIntoViewIfNeeded();
    const bounds = await button.boundingBox();
    if (!bounds) throw new Error('Double-click target missing');
    const postsBeforeDoubleClick = uiCreatePostCount;
    const successfulCreate = ux.waitForResponse(res => new URL(res.url()).pathname === '/api/patients/' && res.request().method() === 'POST' && res.status() === 200, { timeout: 25000 });
    await ux.mouse.dblclick(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2, { delay: 30 });
    const accepted = await successfulCreate;
    const created = await accepted.json();
    await ux.waitForURL(new RegExp('/patients/' + created.id + '(?:\\?|$)'), { timeout: 15000 });
    const independent = await uxContext.request.get(api + '/api/patients/' + created.id);
    if (independent.status() !== 200) throw new Error('Double-click patient not persisted: ' + independent.status());
    await ux.waitForTimeout(250);
    const doubleClickPosts = uiCreatePostCount - postsBeforeDoubleClick;
    if (doubleClickPosts !== 1) throw new Error('Real UI double-click emitted ' + doubleClickPosts + ' POST requests');
    const persisted = await independent.json();
    if (persisted.id !== created.id || persisted.nom !== identity) throw new Error('Real double-click persistence mismatch');
    await ux.reload({ waitUntil: 'domcontentloaded' });
    await ux.getByText(identity, { exact: false }).first().waitFor({ state: 'visible', timeout: 15000 });
    await ux.screenshot({ path: path.join(uxDir, '04-after-double-click.png'), fullPage: true, animations: 'disabled' });
    results.push({ viewport: 'adversarial-mobile-ui', simulatedPreflightStatus: 503, simulatedCreateStatus: 503, noCreateOnPreflightFailure: true, noFalseSuccessOnCreateFailure: true, doubleClickPosts, doubleClickCreateStatus: accepted.status(), independentReadStatus: independent.status(), keyboardNextFocus: nextFocus, nameHasAssociatedLabel, labelProof, cssRootFont200PercentMobile: textZoomMobile, cssRootFont200PercentDesktop: textZoomDesktop, screenshots: ['01-css-text-zoom-200pct.png','01b-css-text-zoom-200pct-desktop.png','02-preflight-503-refused.png','03-create-503-refused.png','04-after-double-click.png'] });
  } finally {
    await uxContext.close();
  }
  passed = true;
} finally {
  await browser.close();
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify({ productHead: process.env.PRODUCT_HEAD || null, passed, completedAt: new Date().toISOString(), results }, null, 2));
}
if (!passed) throw new Error('FUE-D not certified');
console.log('FUE_D_PATIENT_CREATION_PASS ' + JSON.stringify(results.map(({ viewport, firstValueMs, interactions, createStatus, readStatus }) => ({ viewport, firstValueMs, interactions, createStatus, readStatus }))));
