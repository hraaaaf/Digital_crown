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
  const dialog = page.getByRole('dialog').last();
  if (await dialog.isVisible({timeout:1000}).catch(() => false)) {
    await page.keyboard.press('Escape');
    await dialog.waitFor({state:'hidden',timeout:10000}).catch(() => {});
  }
  const title = page.getByPlaceholder('Ex: ORDONNANCE, LETTRE...');
  const content = page.getByPlaceholder("Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte.");
  await title.fill(`P6 ${viewport.width}`);
  await content.fill('Texte P6');
  await page.getByTitle('Tableau').click();
  await page.getByRole('button', {name:'A5',exact:true}).click();
  await page.getByRole('button', {name:'A4',exact:true}).click();
  await page.getByRole('button', {name:'Justifié',exact:true}).click();
  const metrics = await page.evaluate(() => {
    const d = document.documentElement;
    const vw = window.innerWidth;
    const visible = (el) => { const r=el.getBoundingClientRect(),s=getComputedStyle(el); return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0; };
    const clipped = [...document.querySelectorAll('input,textarea,button')].filter(visible).filter((el)=>{const r=el.getBoundingClientRect();return r.left<-1||r.right>vw+1;}).length;
    return { scrollWidth:d.scrollWidth, clientWidth:d.clientWidth, noOverflow:d.scrollWidth<=d.clientWidth+2, clipped };
  });
  const screenshot = `p6-${viewport.width}x${viewport.height}-editor.png`;
  await page.screenshot({path:path.join(out,screenshot),fullPage:true});
  evidence.push({viewport,metrics,errors,screenshot,pass:metrics.noOverflow&&metrics.clipped===0&&errors.length===0});
  await context.close();
}
const report = {status:evidence.every((x)=>x.pass)?'PASS':'FAIL',evidence};
fs.writeFileSync(path.join(out,'p6-editor.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
await browser.close();
await api.dispose();
if (report.status !== 'PASS') process.exit(1);
