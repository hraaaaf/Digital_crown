import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');
const out = path.resolve('../artifacts/t2-browser');
fs.mkdirSync(out, { recursive: true });

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error(`login ${login.status()}`);
const tokens = await login.json();
const patients = await api.get('/api/patients', { headers: { Authorization: `Bearer ${tokens.access_token}` } });
const patient = (await patients.json()).find((p) => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('certification patient missing');

const browser = await chromium.launch({ headless: true });
const evidence = [];
for (const viewport of [{width:390,height:844},{width:768,height:1024},{width:1280,height:900}]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await page.addInitScript(({access,refresh}) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=libre`, { waitUntil:'networkidle', timeout:90000 });
  await page.getByText('Document Libre', { exact:true }).first().waitFor({ timeout:30000 });
  const initialDialog = page.getByRole('dialog').last();
  if (await initialDialog.isVisible({timeout:1000}).catch(() => false)) {
    await page.keyboard.press('Escape');
    await initialDialog.waitFor({state:'hidden',timeout:10000}).catch(() => {});
  }
  const title = page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...');
  const content = page.getByPlaceholder("Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte.");
  const table = page.getByRole('button', { name: 'Tableau', exact: true }).first();
  const a5 = page.getByRole('button', {name:'A5',exact:true});
  const a4 = page.getByRole('button', {name:'A4',exact:true});
  const justified = page.getByRole('button', {name:'Justifié',exact:true});
  await title.fill(`P6 ${viewport.width}`);
  await content.fill('Texte P6');
  // On narrow viewports the editor toolbar is horizontally scrollable; make each
  // control actionable before clicking instead of relying on Playwright's click
  // auto-scroll, which cannot scroll nested toolbar overflow reliably.
  for (const control of [table, a5, a4, justified]) {
    await control.scrollIntoViewIfNeeded();
    await control.click();
  }
  await content.scrollIntoViewIfNeeded();
  const metrics = await page.evaluate(() => {
    const d = document.documentElement;
    return { scrollWidth:d.scrollWidth, clientWidth:d.clientWidth, noOverflow:d.scrollWidth<=d.clientWidth+2 };
  });
  const controls = {};
  for (const [name, locator] of Object.entries({title,content,table,a5,a4,justified})) {
    await locator.scrollIntoViewIfNeeded();
    const box = await locator.boundingBox();
    controls[name] = box ? {left:box.x,right:box.x+box.width,withinViewport:box.x>=-1&&box.x+box.width<=viewport.width+1} : null;
  }
  const clipped = Object.entries(controls).filter(([,box]) => !box || !box.withinViewport).map(([name]) => name);
  await content.scrollIntoViewIfNeeded();
  const editorScreenshot = `p6-${viewport.width}x${viewport.height}-editor.png`;
  await page.screenshot({path:path.join(out,editorScreenshot)});

  const inlinePreview = page.locator('[data-ordonnance-desktop-preview="inline"]').last();
  const inlineVisible = viewport.width >= 1280
    && await inlinePreview.isVisible({timeout:1500}).catch(() => false);

  let previewEvidence;
  let previewPass = false;
  const previewScreenshot = `p6-${viewport.width}x${viewport.height}-preview.png`;

  if (inlineVisible) {
    const previewRegion = inlinePreview.getByRole('region', {name:/Aperçu PDF/i}).last();
    await previewRegion.waitFor({state:'visible',timeout:10000});
    const inlineBox = await inlinePreview.boundingBox();
    const previewBox = await previewRegion.boundingBox();
    const previewLayout = {
      inlineWithinViewport: Boolean(
        inlineBox &&
        inlineBox.x >= -1 &&
        inlineBox.y >= -1 &&
        inlineBox.x + inlineBox.width <= viewport.width + 1 &&
        inlineBox.y + inlineBox.height <= viewport.height + 120
      ),
      inlineWidthStable: Boolean(inlineBox && inlineBox.width >= 270 && inlineBox.width <= 290),
      editorRemainsVisible: Boolean(await content.isVisible()),
      noHorizontalOverflow: metrics.noOverflow,
    };
    await page.screenshot({path:path.join(out,previewScreenshot)});
    const closeButton = inlinePreview.getByRole('button', {name:/Fermer/i}).first();
    await closeButton.click();
    await inlinePreview.waitFor({state:'hidden',timeout:10000});
    previewPass = Object.values(previewLayout).every(Boolean);
    previewEvidence = {
      mode:'inline',
      inlineBox,
      previewBox,
      layout:previewLayout,
      dismissed:true,
      dismissalMode:'close-button',
    };
  } else {
    const previewButton = page.getByRole('button', {name:'Aperçu',exact:true});
    await previewButton.scrollIntoViewIfNeeded();
    await previewButton.click();
    const previewDialog = page.getByRole('dialog', {name:'Document Libre'}).last();
    await previewDialog.waitFor({state:'visible',timeout:30000});
    const overlay = page.locator('.document-studio-live-preview');
    const overlayBox = await overlay.boundingBox();
    const previewBox = await previewDialog.boundingBox();
    const previewLayout = {
      overlayCoversViewport: Boolean(
        overlayBox &&
        overlayBox.x <= 1 &&
        overlayBox.y <= 1 &&
        overlayBox.width >= viewport.width - 2 &&
        overlayBox.height >= viewport.height - 2
      ),
      dialogWithinViewport: Boolean(
        previewBox &&
        previewBox.x >= -1 &&
        previewBox.y >= -1 &&
        previewBox.x + previewBox.width <= viewport.width + 1 &&
        previewBox.y + previewBox.height <= viewport.height + 1
      ),
      compactOverlayWidth: viewport.width < 1024
        ? Boolean(previewBox && previewBox.width >= viewport.width * 0.9)
        : true,
      desktopCentered: viewport.width >= 1024
        ? Boolean(
            previewBox &&
            Math.abs((previewBox.x + previewBox.width / 2) - viewport.width / 2) <= 4 &&
            previewBox.width <= 1026
          )
        : true,
    };
    await page.screenshot({path:path.join(out,previewScreenshot)});
    await page.keyboard.press('Escape');
    await previewDialog.waitFor({state:'hidden',timeout:10000});
    previewPass = Object.values(previewLayout).every(Boolean);
    previewEvidence = {
      mode:'modal',
      overlayBox,
      previewBox,
      layout:previewLayout,
      dismissed:true,
      dismissalMode:'escape',
    };
  }

  evidence.push({
    viewport,
    metrics:{...metrics,clipped:clipped.length},
    controls,
    preview:previewEvidence,
    errors,
    screenshots:{editor:editorScreenshot,preview:previewScreenshot},
    pass:metrics.noOverflow&&clipped.length===0&&previewPass&&errors.length===0,
  });
  await context.close();
}
const report = {status:evidence.every((x)=>x.pass)?'PASS':'FAIL',evidence};
fs.writeFileSync(path.join(out,'p6-editor.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
await browser.close();
await api.dispose();
if (report.status !== 'PASS') process.exit(1);