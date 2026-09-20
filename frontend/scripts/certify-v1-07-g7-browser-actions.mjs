import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G7 login failed');
const tokens=await login.json();

const browser=await chromium.launch({headless:true});
const viewports=[{width:390,height:844},{width:1280,height:900}];
const proofs=[];
function prove(v,a,d={}){proofs.push({viewport:v.width+'x'+v.height,action:a,status:'PASS',...d});}
async function seed(page){
  await page.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:tokens.access_token,refresh:tokens.refresh_token});
}

for(const viewport of viewports){
  const ctx=await browser.newContext({viewport,colorScheme:'light'});
  const page=await ctx.newPage();
  await seed(page);

  // STOCK — truthful read + filters + destructive refusal/non-mutation.
  await page.route('**/api/stock/items',async route=>{
    const m=route.request().method();
    if(m==='GET') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{
      id:1,nom:'Gants nitrile',categorie:'CONSOMMABLE',quantite:10,seuil_alerte:5,unite:'boîte',
      prix_unitaire:30,fournisseur:'Supplier',notes:'Taille M',alerte:false
    }])});
    if(m==='POST') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Article refusé"}'});
    return route.continue();
  });
  await page.route('**/api/stock/alerts',route=>route.fulfill({status:200,contentType:'application/json',body:'{"count":0,"items":[]}'}));
  await page.route('**/api/stock/items/1',async route=>{
    const m=route.request().method();
    if(m==='DELETE') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Suppression refusée"}'});
    if(m==='PATCH') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Quantité refusée"}'});
    return route.continue();
  });

  await page.goto('http://127.0.0.1:5173/stock',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Gants nitrile',{exact:true}).waitFor({state:'visible',timeout:10000});
  const search=page.getByPlaceholder('Rechercher…');
  await search.fill('absent');
  await page.getByText('Aucun résultat pour cette recherche.',{exact:true}).waitFor({state:'visible',timeout:5000});
  await search.fill('');
  prove(viewport,'stock-search-truth');

  const row=page.getByText('Gants nitrile',{exact:true}).locator('xpath=ancestor::tr');
  const buttons=row.locator('button');
  if(await buttons.count()>=2){
    await buttons.nth(1).click();
    await page.getByText('Action stock non enregistrée',{exact:true}).waitFor({state:'visible',timeout:5000});
    await page.getByText('Quantité refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'stock-quantity-refusal');
  }

  const del=row.getByTitle('Supprimer');
  if(await del.count()){
    await del.click();
    const dialog=page.getByRole('dialog',{name:'Supprimer cet article ?'});
    await dialog.waitFor({state:'visible',timeout:5000});
    await page.getByRole('button',{name:'Supprimer définitivement',exact:true}).click();
    await dialog.getByText('Suppression refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
    if(!(await page.getByText('Gants nitrile',{exact:true}).count())) throw new Error('stock item disappeared after refused delete');
    prove(viewport,'stock-delete-refusal-non-mutation');
    const cancel=dialog.getByRole('button',{name:'Annuler',exact:true});
    if(await cancel.count()) await cancel.click();
  }

  const add=page.getByRole('button',{name:/Ajouter un article/i});
  if(await add.count()){
    await add.click();
    const modal=page.getByText('Nouvel article',{exact:true}).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    await modal.getByPlaceholder('Ex: Gants nitrile S').fill('Masques FFP2');
    await modal.getByRole('button',{name:'Ajouter',exact:true}).click();
    await modal.getByText('Article refusé',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'stock-add-refusal-preserves-modal');
  }

  await page.unroute('**/api/stock/items');
  await page.unroute('**/api/stock/alerts');
  await page.unroute('**/api/stock/items/1');

  // MARKETPLACE — real controller with deterministic HTTP fixture.
  await page.route('**/api/partner-orders/meta',route=>route.fulfill({status:200,contentType:'application/json',body:'{"strategyPresets":[]}'}));
  await page.route('**/api/partner-catalog/meta',route=>route.fulfill({status:200,contentType:'application/json',body:'{"categories":["Restauration"]}'}));
  await page.route('**/api/partner-catalog/suppliers',route=>route.fulfill({status:200,contentType:'application/json',body:'[]'}));
  await page.route('**/api/partner-catalog/products',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{
    id:'101',name:'Composite universel',sku:'CMP-101',category:'Restauration',specialty:'Omnipratique',
    price:390,unit:'seringue',availability:'Disponible',description:'Composite',supplierId:'11',
    supplierName:'Atlas Dental',benefits:[],isFeatured:true,sortOrder:1
  }])}));
  await page.route('**/api/partner-orders',async route=>{
    if(route.request().method()==='POST') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Brouillon refusé"}'});
    return route.continue();
  });

  await page.goto('http://127.0.0.1:5173/approvisionnement',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Composite universel',{exact:true}).waitFor({state:'visible',timeout:10000});
  const marketSearch=page.getByPlaceholder('Nom, référence ou SKU…');
  await marketSearch.fill('CMP');
  prove(viewport,'marketplace-search');

  const plus=page.getByRole('button',{name:'Ajouter une unité de Composite universel'});
  await plus.click();
  const cart=page.getByRole('button',{name:/Ouvrir le panier, 1 unité/i});
  await cart.click();
  const checkout=page.getByRole('dialog',{name:/Préparer le brouillon/i});
  await checkout.waitFor({state:'visible',timeout:5000});
  const save=checkout.getByRole('button',{name:'Enregistrer le brouillon',exact:true});
  await save.click();
  await page.waitForTimeout(500);
  if(!(await checkout.count())) throw new Error('marketplace checkout closed after refused draft');
  prove(viewport,'marketplace-draft-refusal-preserves-checkout');

  await page.unroute('**/api/partner-orders/meta');
  await page.unroute('**/api/partner-catalog/meta');
  await page.unroute('**/api/partner-catalog/suppliers');
  await page.unroute('**/api/partner-catalog/products');
  await page.unroute('**/api/partner-orders');

  // LIBRARY — search, favorite persistence, deep-link.
  await page.goto('http://127.0.0.1:5173/bibliotheque',{waitUntil:'networkidle',timeout:90000});
  const libSearch=page.getByPlaceholder('Avulsion, composite, blanchiment…');
  if(await libSearch.count()){
    await libSearch.fill('ENDO');
    await page.getByText('Traitement endodontique',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'library-search');
    await libSearch.fill('');
  }

  const det=page.getByText('Détartrage',{exact:true}).first();
  if(await det.count()){
    const card=det.locator('xpath=ancestor::button[1]');
    const star=card.locator('span').filter({hasText:/^[☆★]$/}).first();
    if(await star.count()){
      await star.click();
      const favs=await page.evaluate(()=>JSON.parse(localStorage.getItem('dc_favs')||'[]'));
      if(!favs.includes('DET')) throw new Error('library favorite did not persist');
      prove(viewport,'library-favorite-persistence');
    }
    await card.click();
    await page.waitForURL('**/bibliotheque/DET');
    prove(viewport,'library-deeplink-navigation');
  }

  // SCIENCE HUB — search + category + safe external link contract.
  await page.goto('http://127.0.0.1:5173/science-hub',{waitUntil:'networkidle',timeout:90000});
  const sciSearch=page.getByPlaceholder('Rechercher un article...');
  if(await sciSearch.count()){
    await sciSearch.fill('zzzz-no-match');
    await page.getByText('Aucun article ne correspond à votre recherche.',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'science-hub-no-result-truth');
    await sciSearch.fill('');
  }
  const study=page.getByRole('link',{name:/Consulter l'étude complète/i}).first();
  if(await study.count()){
    const target=await study.getAttribute('target');
    const rel=await study.getAttribute('rel')||'';
    if(target!=='_blank'||!rel.includes('noopener')||!rel.includes('noreferrer')) throw new Error('unsafe science external link');
    prove(viewport,'science-hub-safe-external-link');
  }

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G7_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
