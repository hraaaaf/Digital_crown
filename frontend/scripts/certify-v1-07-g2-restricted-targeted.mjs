import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const restrictedApi=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const restrictedLogin=await restrictedApi.post('/api/auth/login',{form:{username:'t2-restricted@cabinet.ma',password}});
if(!restrictedLogin.ok()) throw new Error('restricted login failed '+restrictedLogin.status());
const restrictedTokens=await restrictedLogin.json();

const browser=await chromium.launch({headless:true});
const ctx=await browser.newContext({viewport:{width:1280,height:900},colorScheme:'light'});
await ctx.clearCookies({name:'access_token'});
await ctx.clearCookies({name:'refresh_token'});
const page=await ctx.newPage();

await page.addInitScript(v=>{
  localStorage.setItem('token',v.access);
  localStorage.setItem('refresh_token',v.refresh||'');
  localStorage.setItem('appMode','prod');
},{access:restrictedTokens.access_token,refresh:restrictedTokens.refresh_token});

await page.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
await page.getByRole('button',{name:'Ajout rapide'}).waitFor({state:'visible',timeout:10000});

if(await page.getByRole('button',{name:'Chercher un patient'}).count()) throw new Error('restricted user sees patient search');
if(await page.getByRole('button',{name:'Appairer le téléphone mobile'}).count()) throw new Error('restricted user sees mobile admin control');
if(await page.getByRole('button',{name:/Pilotage du cabinet/i}).count()) throw new Error('restricted user sees accounting management panel');
if(await page.getByRole('link',{name:'Patients',exact:true}).count()) throw new Error('restricted user sees Patients navigation');
if(await page.getByTitle('Réglages').count()) throw new Error('restricted user sees Settings entry');

await page.getByRole('button',{name:'Ajout rapide'}).click();
if(await page.getByRole('menuitem',{name:/Nouveau Patient/i}).count()) throw new Error('restricted user sees New Patient quick action');
await page.getByRole('menuitem',{name:/Nouveau RDV/i}).waitFor({state:'visible',timeout:5000});

await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
await page.waitForURL('**/dashboard',{timeout:10000});
if(await page.getByRole('button',{name:/Import CSV/i}).count()) throw new Error('restricted direct patients route exposed patient controls');

await page.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
await page.waitForURL('**/dashboard',{timeout:10000});
if(await page.getByText(/Performance & Assistance|Mon Équipe|Sécurité & Backup/i).count()) throw new Error('restricted direct settings route exposed settings controls');

await page.goto('http://127.0.0.1:5173/accounting',{waitUntil:'networkidle',timeout:90000});
await page.waitForURL('**/dashboard',{timeout:10000});

await page.goto('http://127.0.0.1:5173/approvisionnement',{waitUntil:'networkidle',timeout:90000});
await page.waitForURL('**/dashboard',{timeout:10000});

await page.goto('http://127.0.0.1:5173/super-admin',{waitUntil:'networkidle',timeout:90000});
await page.waitForURL('**/dashboard',{timeout:10000});
if(await page.getByText(/Gestion Globale des Licences/i).count()) throw new Error('restricted direct super-admin route exposed privileged UI');

await page.goto('http://127.0.0.1:5173/agenda',{waitUntil:'networkidle',timeout:90000});
await page.waitForURL('**/agenda',{timeout:10000});
if(new URL(page.url()).pathname!=='/agenda') throw new Error('agenda permission positive path failed');

await page.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
const attention=page.getByRole('button',{name:'Ouvrir le centre d’attention',exact:true});
if(await attention.count()){
  await attention.click();
  if(await page.getByRole('link',{name:'Trésorerie',exact:true}).count()) throw new Error('restricted user sees treasury shortcut');
}

console.log(JSON.stringify({status:'PASS',scenario:'g2-restricted-permissions-targeted'}));
await ctx.close();
await browser.close();
await restrictedApi.dispose();
