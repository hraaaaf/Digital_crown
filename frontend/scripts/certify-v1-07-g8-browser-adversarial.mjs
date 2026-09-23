import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G8 login failed');
const tokens=await login.json();

const browser=await chromium.launch({headless:true});
const viewports=[{width:390,height:844},{width:1280,height:900}];
const routes=['/dashboard','/patients','/agenda','/settings','/stock'];
const proofs=[];

async function seed(page){
  await page.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:tokens.access_token,refresh:tokens.refresh_token});
}
function prove(v,a,d={}){proofs.push({viewport:v.width+'x'+v.height,action:a,status:'PASS',...d});}

for(const viewport of viewports){
  const ctx=await browser.newContext({viewport,colorScheme:'light'});
  const page=await ctx.newPage();
  await seed(page);

  // Responsive reachability / no horizontal overflow on representative surfaces.
  for(const route of routes){
    if(route==='/stock'){
      await page.route('**/api/stock/items',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{
        id:1,nom:'Gants nitrile',categorie:'CONSOMMABLE',quantite:10,seuil_alerte:5,unite:'boîte',
        prix_unitaire:30,fournisseur:'Supplier',notes:'Taille M',alerte:false
      }])}));
      await page.route('**/api/stock/alerts',r=>r.fulfill({status:200,contentType:'application/json',body:'{"count":0,"items":[]}'}));
    }
    await page.goto('http://127.0.0.1:5173'+route,{waitUntil:'networkidle',timeout:90000});
    const layout=await page.evaluate(()=>({c:document.documentElement.clientWidth,s:document.documentElement.scrollWidth}));
    if(layout.s>layout.c+2) throw new Error(route+' horizontal overflow '+layout.s+'>'+layout.c+' at '+viewport.width);
    const focusable=await page.locator('button:visible,input:visible,select:visible,textarea:visible,a[href]:visible').count();
    if(focusable===0) throw new Error(route+' exposes zero focusable controls');
    prove(viewport,'responsive-reachability',{route,focusable});
    if(route==='/stock'){
      await page.unroute('**/api/stock/items');
      await page.unroute('**/api/stock/alerts');
    }
  }

  // Error truth: forced stock read failure must not render false empty.
  await page.route('**/api/stock/items',r=>r.fulfill({status:503,contentType:'application/json',body:'{"detail":"stock unavailable"}'}));
  await page.route('**/api/stock/alerts',r=>r.fulfill({status:200,contentType:'application/json',body:'{"count":0,"items":[]}'}));
  await page.goto('http://127.0.0.1:5173/stock',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Stock indisponible',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(await page.getByText(/Aucun article\. Commencez/i).count()) throw new Error('false empty stock on read failure');
  prove(viewport,'error-vs-empty-stock');
  await page.unroute('**/api/stock/items');
  await page.unroute('**/api/stock/alerts');

  // Dialog keyboard/focus semantics + delete refusal non-mutation.
  await page.route('**/api/stock/items',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{
    id:1,nom:'Gants nitrile',categorie:'CONSOMMABLE',quantite:10,seuil_alerte:5,unite:'boîte',
    prix_unitaire:30,fournisseur:'Supplier',notes:'Taille M',alerte:false
  }])}));
  await page.route('**/api/stock/alerts',r=>r.fulfill({status:200,contentType:'application/json',body:'{"count":0,"items":[]}'}));
  await page.route('**/api/stock/items/1',async r=>{
    if(r.request().method()==='DELETE') return r.fulfill({status:503,contentType:'application/json',body:'{"detail":"Suppression refusée"}'});
    return r.continue();
  });
  await page.goto('http://127.0.0.1:5173/stock',{waitUntil:'networkidle',timeout:90000});
  const row=page.getByText('Gants nitrile',{exact:true}).locator('xpath=ancestor::tr');
  await row.getByTitle('Supprimer').click();
  const dialog=page.getByRole('dialog',{name:'Supprimer cet article ?'});
  await dialog.waitFor({state:'visible',timeout:5000});
  await page.waitForFunction(()=>!!document.activeElement?.closest('[role="dialog"]'),undefined,{timeout:5000});
  const activeInside=await page.evaluate(()=>!!document.activeElement?.closest('[role="dialog"]'));
  if(!activeInside) throw new Error('delete dialog did not own focus');
  prove(viewport,'dialog-focus-entry');

  await page.keyboard.press('Escape');
  await dialog.waitFor({state:'hidden',timeout:5000});
  prove(viewport,'dialog-escape-close');

  await row.getByTitle('Supprimer').click();
  await page.getByRole('button',{name:'Supprimer définitivement',exact:true}).click();
  await dialog.getByText('Suppression refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(!(await page.getByText('Gants nitrile',{exact:true}).count())) throw new Error('delete refusal mutated visible stock');
  prove(viewport,'destructive-refusal-non-mutation');

  // Representative single-flight mutation.
  let postCount=0;
  await page.unroute('**/api/stock/items');
  await page.route('**/api/stock/items',async r=>{
    if(r.request().method()==='GET'){
      return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{
        id:1,nom:'Gants nitrile',categorie:'CONSOMMABLE',quantite:10,seuil_alerte:5,unite:'boîte',
        prix_unitaire:30,fournisseur:'Supplier',notes:'Taille M',alerte:false
      }])});
    }
    if(r.request().method()==='POST'){
      postCount++;
      await new Promise(res=>setTimeout(res,350));
      return r.fulfill({status:201,contentType:'application/json',body:'{"id":2}'});
    }
    return r.continue();
  });
  await page.goto('http://127.0.0.1:5173/stock',{waitUntil:'networkidle',timeout:90000});
  await page.getByRole('button',{name:/Ajouter un article/i}).click();
  const modal=page.getByText('Nouvel article',{exact:true}).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
  await modal.getByPlaceholder('Ex: Gants nitrile S').fill('Masques single-flight');
  const add=modal.getByRole('button',{name:'Ajouter',exact:true});
  await add.evaluate(el=>{(el).click();(el).click();});
  await page.waitForTimeout(700);
  if(postCount!==1) throw new Error('single-flight violated: POST count='+postCount);
  prove(viewport,'critical-mutation-single-flight',{postCount});

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G8_BROWSER_ADVERSARIAL',JSON.stringify({status:'PASS',proofs}));
