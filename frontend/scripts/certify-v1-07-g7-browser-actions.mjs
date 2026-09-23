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

  // STOCK — read truth, search/category, CRUD/quantity success + refusal + non-mutation.
  let stockItems=[{
    id:1,nom:'Gants nitrile',categorie:'CONSOMMABLE',quantite:10,seuil_alerte:5,unite:'boîte',
    prix_unitaire:30,fournisseur:'Supplier',notes:'Taille M',alerte:false
  }];
  let nextStockId=2;
  let readFailuresRemaining=1;
  let failNextCreate=false,failNextPatch=false,failNextDelete=false;
  let createCalls=0,patchCalls=0,deleteCalls=0;

  await page.route('**/api/stock/items',async route=>{
    const req=route.request();
    if(req.method()==='GET'){
      if(readFailuresRemaining>0){
        readFailuresRemaining-=1;
        return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Stock indisponible'})});
      }
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(stockItems)});
    }
    if(req.method()==='POST'){
      createCalls+=1;
      if(failNextCreate){
        failNextCreate=false;
        return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Article refusé'})});
      }
      const body=req.postDataJSON();
      const created={id:nextStockId++,...body,alerte:Number(body.quantite)<=Number(body.seuil_alerte)};
      stockItems=[...stockItems,created];
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(created)});
    }
    return route.continue();
  });
  await page.route('**/api/stock/items/*',async route=>{
    const req=route.request();
    const id=Number(new URL(req.url()).pathname.split('/').pop());
    if(req.method()==='PATCH'){
      patchCalls+=1;
      if(failNextPatch){
        failNextPatch=false;
        return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Mutation stock refusée'})});
      }
      const body=req.postDataJSON();
      stockItems=stockItems.map(item=>item.id===id?{...item,...body,alerte:Number(body.quantite??item.quantite)<=Number(body.seuil_alerte??item.seuil_alerte)}:item);
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(stockItems.find(item=>item.id===id))});
    }
    if(req.method()==='DELETE'){
      deleteCalls+=1;
      if(failNextDelete){
        failNextDelete=false;
        return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Suppression refusée'})});
      }
      stockItems=stockItems.filter(item=>item.id!==id);
      return route.fulfill({status:200,contentType:'application/json',body:'{}'});
    }
    return route.continue();
  });
  await page.route('**/api/stock/alerts',route=>{
    const alertItems=stockItems.filter(item=>Number(item.quantite)<=Number(item.seuil_alerte));
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({count:alertItems.length,items:alertItems})});
  });

  await page.goto('http://127.0.0.1:5173/stock',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Stock indisponible',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(await page.getByText('Aucun article. Commencez par en ajouter un.',{exact:true}).count()) throw new Error('stock read failure rendered false empty state');
  await page.getByRole('button',{name:'Réessayer',exact:true}).click();
  await page.getByText('Gants nitrile',{exact:true}).waitFor({state:'visible',timeout:10000});
  prove(viewport,'stock-read-failure-retry');

  const search=page.getByPlaceholder('Rechercher…');
  await search.fill('absent');
  await page.getByText('Aucun résultat pour cette recherche.',{exact:true}).waitFor({state:'visible',timeout:5000});
  await search.fill('');
  await page.getByRole('button',{name:'Matériaux',exact:true}).click();
  await page.getByText('Aucun résultat pour cette recherche.',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:'Tous',exact:true}).click();
  await page.getByText('Gants nitrile',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'stock-search-category-filter-restore');

  // Quantity ACK then refusal preserves persisted/UI state.
  await page.getByRole('button',{name:'Augmenter la quantité de Gants nitrile',exact:true}).click();
  await page.waitForFunction(()=>document.body.innerText.includes('11 boîte'));
  if(stockItems.find(i=>i.id===1)?.quantite!==11) throw new Error('stock quantity ACK not persisted in fixture');
  prove(viewport,'stock-quantity-success',{patchCalls});

  failNextPatch=true;
  await page.getByRole('button',{name:'Augmenter la quantité de Gants nitrile',exact:true}).click();
  await page.getByText('Mutation stock refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(stockItems.find(i=>i.id===1)?.quantite!==11) throw new Error('stock quantity refusal mutated state');
  await page.getByText(/11 boîte/).waitFor({state:'visible',timeout:5000});
  prove(viewport,'stock-quantity-refusal-non-mutation',{patchCalls});

  // Add success.
  await page.getByRole('button',{name:/Ajouter un article/i}).click();
  let stockDialog=page.getByRole('dialog',{name:'Nouvel article'});
  await stockDialog.getByPlaceholder('Ex: Gants nitrile S').fill('Masques FFP2');
  await stockDialog.locator('select').selectOption('MATERIAU');
  await stockDialog.locator('input[type="number"]').nth(0).fill('7');
  await stockDialog.locator('input[type="number"]').nth(1).fill('3');
  await stockDialog.getByRole('button',{name:'Ajouter',exact:true}).click();
  await stockDialog.waitFor({state:'detached',timeout:10000});
  await page.getByText('Masques FFP2',{exact:true}).waitFor({state:'visible',timeout:10000});
  const createdStock=stockItems.find(i=>i.nom==='Masques FFP2');
  if(!createdStock || createCalls<1) throw new Error('stock add ACK mismatch');
  prove(viewport,'stock-add-success',{id:createdStock.id});

  // Add refusal keeps modal and does not append item.
  failNextCreate=true;
  const stockCountBeforeRefusedAdd=stockItems.length;
  await page.getByRole('button',{name:/Ajouter un article/i}).click();
  stockDialog=page.getByRole('dialog',{name:'Nouvel article'});
  await stockDialog.getByPlaceholder('Ex: Gants nitrile S').fill('Article refusé browser');
  await stockDialog.getByRole('button',{name:'Ajouter',exact:true}).click();
  await stockDialog.getByText('Article refusé',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(!(await stockDialog.isVisible()) || stockItems.length!==stockCountBeforeRefusedAdd) throw new Error('stock add refusal contract mismatch');
  prove(viewport,'stock-add-refusal-preserves-modal');
  await stockDialog.getByRole('button',{name:'Annuler',exact:true}).click();

  // Edit success then refusal/non-mutation.
  let createdRow=page.getByText('Masques FFP2',{exact:true}).locator('xpath=ancestor::tr');
  await createdRow.hover();
  await createdRow.getByTitle('Modifier').click();
  stockDialog=page.getByRole('dialog',{name:'Modifier l’article'});
  const stockName=stockDialog.getByPlaceholder('Ex: Gants nitrile S');
  await stockName.fill('Masques FFP3');
  await stockDialog.getByRole('button',{name:'Mettre à jour',exact:true}).click();
  await stockDialog.waitFor({state:'detached',timeout:10000});
  await page.getByText('Masques FFP3',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(stockItems.find(i=>i.id===createdStock.id)?.nom!=='Masques FFP3') throw new Error('stock edit ACK mismatch');
  prove(viewport,'stock-edit-success');

  createdRow=page.getByText('Masques FFP3',{exact:true}).locator('xpath=ancestor::tr');
  await createdRow.hover();
  await createdRow.getByTitle('Modifier').click();
  stockDialog=page.getByRole('dialog',{name:'Modifier l’article'});
  failNextPatch=true;
  await stockDialog.getByPlaceholder('Ex: Gants nitrile S').fill('Masques SHOULD NOT SAVE');
  await stockDialog.getByRole('button',{name:'Mettre à jour',exact:true}).click();
  await stockDialog.getByText('Mutation stock refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(stockItems.find(i=>i.id===createdStock.id)?.nom!=='Masques FFP3') throw new Error('stock edit refusal mutated state');
  prove(viewport,'stock-edit-refusal-non-mutation');
  await stockDialog.getByRole('button',{name:'Annuler',exact:true}).click();

  // Delete cancel, refusal, then ACK removal.
  createdRow=page.getByText('Masques FFP3',{exact:true}).locator('xpath=ancestor::tr');
  await createdRow.hover();
  await createdRow.getByTitle('Supprimer').click();
  let deleteDialog=page.getByRole('dialog',{name:'Supprimer cet article ?'});
  await deleteDialog.getByRole('button',{name:'Annuler',exact:true}).click();
  if(!stockItems.some(i=>i.id===createdStock.id)) throw new Error('stock delete cancel mutated state');
  prove(viewport,'stock-delete-cancel-non-mutation');

  createdRow=page.getByText('Masques FFP3',{exact:true}).locator('xpath=ancestor::tr');
  await createdRow.hover();
  await createdRow.getByTitle('Supprimer').click();
  deleteDialog=page.getByRole('dialog',{name:'Supprimer cet article ?'});
  failNextDelete=true;
  await deleteDialog.getByRole('button',{name:'Supprimer définitivement',exact:true}).click();
  await deleteDialog.getByText('Suppression refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(!stockItems.some(i=>i.id===createdStock.id)) throw new Error('stock delete refusal mutated state');
  prove(viewport,'stock-delete-refusal-non-mutation',{deleteCalls});
  await deleteDialog.getByRole('button',{name:'Annuler',exact:true}).click();

  createdRow=page.getByText('Masques FFP3',{exact:true}).locator('xpath=ancestor::tr');
  await createdRow.hover();
  await createdRow.getByTitle('Supprimer').click();
  deleteDialog=page.getByRole('dialog',{name:'Supprimer cet article ?'});
  await deleteDialog.getByRole('button',{name:'Supprimer définitivement',exact:true}).click();
  await deleteDialog.waitFor({state:'detached',timeout:10000});
  await page.getByText('Masques FFP3',{exact:true}).waitFor({state:'detached',timeout:10000});
  if(stockItems.some(i=>i.id===createdStock.id)) throw new Error('stock delete ACK did not remove item');
  prove(viewport,'stock-delete-success',{deleteCalls});

  await page.unroute('**/api/stock/items');
  await page.unroute('**/api/stock/items/*');
  await page.unroute('**/api/stock/alerts');

  // MARKETPLACE — catalog truth, cart persistence, checkout close/refusal/success.
  const strategy={
    key:'sent_commission_10',
    label:'Commission sur commande envoyée',
    settlementBasis:'SENT_TO_PARTNER',
    revenueModel:'COMMISSION_PERCENT',
    commissionRate:10,
    discountRate:0,
    fixedFeeAmount:0,
    description:'Browser certification'
  };
  const marketProduct={
    id:101,supplierId:11,supplierName:'Atlas Dental',externalProductId:'P-101',
    name:'Composite universel',sku:'CMP-101',dentalCategory:'Restauration',dentalSpecialty:'Omnipratique',
    unit:'seringue',price:390,availability:'AVAILABLE',shortDescription:'Composite',longDescription:'Composite',
    benefits:[],isFeatured:true,sortOrder:1
  };
  let catalogReads=0,orderCalls=0,failNextOrder=true;
  await page.route('**/api/partner-orders/meta',route=>route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify({strategyPresets:[strategy]})
  }));
  await page.route('**/api/partner-catalog/meta',route=>route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify({
      categories:['Restauration'],specialties:['Omnipratique'],availability:['AVAILABLE','DISCONTINUED']
    })
  }));
  await page.route('**/api/partner-catalog/suppliers',route=>route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify([{
      id:11,supplierKey:'atlas',name:'Atlas Dental',isActive:true,productCount:1
    }])
  }));
  await page.route('**/api/partner-catalog/products',route=>{
    catalogReads+=1;
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([marketProduct])});
  });
  await page.route('**/api/partner-orders',async route=>{
    if(route.request().method()!=='POST') return route.continue();
    orderCalls+=1;
    const body=route.request().postDataJSON();
    if(body.lines?.length!==1 || Number(body.lines[0]?.quantity)!==1 || body.lines[0]?.sku!=='CMP-101'){
      throw new Error('marketplace order payload mismatch');
    }
    if(!body.customer?.fullName || !body.customer?.clinic || !body.customer?.phone || !body.customer?.email || !body.customer?.city){
      throw new Error('marketplace customer payload incomplete');
    }
    if(failNextOrder){
      failNextOrder=false;
      return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Brouillon refusé'})});
    }
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({orderNumber:'CMD-G7-1'})});
  });

  await page.goto('http://127.0.0.1:5173/approvisionnement',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Composite universel',{exact:true}).waitFor({state:'visible',timeout:10000});
  const marketSearch=page.getByPlaceholder('Nom, référence ou SKU…');
  await marketSearch.fill('CMP');
  await page.getByText('Composite universel',{exact:true}).waitFor({state:'visible',timeout:5000});
  await marketSearch.fill('zzzz-no-match');
  if(await page.getByText('Composite universel',{exact:true}).count()) throw new Error('marketplace search did not filter product');
  await marketSearch.fill('CMP');
  await page.getByRole('button',{name:'Disponibles',exact:true}).click();
  if((await page.getByRole('button',{name:'Disponibles',exact:true}).getAttribute('aria-pressed'))!=='true') throw new Error('marketplace availability filter state mismatch');
  await page.getByRole('button',{name:'Restauration',exact:true}).click();
  if((await page.getByRole('button',{name:'Restauration',exact:true}).getAttribute('aria-pressed'))!=='true') throw new Error('marketplace category filter state mismatch');
  await page.getByText('Composite universel',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'marketplace-search-availability-category');

  const readsBeforeRefresh=catalogReads;
  const catalogRefresh=page.waitForResponse(
    r=>r.request().method()==='GET' && r.url().includes('/api/partner-catalog/products'),
    {timeout:10000},
  );
  await page.getByRole('button',{name:'Actualiser',exact:true}).click();
  const catalogRefreshAck=await catalogRefresh;
  if(!catalogRefreshAck.ok() || catalogReads<=readsBeforeRefresh) throw new Error('marketplace Actualiser did not reread catalog');
  prove(viewport,'marketplace-explicit-refresh',{catalogReads});

  const plus=page.getByRole('button',{name:'Ajouter une unité de Composite universel',exact:true});
  const minus=page.getByRole('button',{name:'Retirer une unité de Composite universel',exact:true});
  await plus.click();
  await plus.click();
  await page.getByRole('button',{name:/Ouvrir le panier, 2 unités/i}).first().waitFor({state:'visible',timeout:5000});
  await minus.click();
  await page.getByRole('button',{name:/Ouvrir le panier, 1 unité/i}).first().waitFor({state:'visible',timeout:5000});
  prove(viewport,'marketplace-cart-plus-minus');

  await page.reload({waitUntil:'networkidle',timeout:90000});
  await page.getByRole('button',{name:/Ouvrir le panier, 1 unité/i}).first().waitFor({state:'visible',timeout:10000});
  prove(viewport,'marketplace-cart-reload-persistence');

  let cart=page.getByRole('button',{name:/Ouvrir le panier, 1 unité/i}).first();
  await cart.click();
  let checkout=page.getByRole('dialog',{name:/Préparer le brouillon/i});
  await checkout.waitFor({state:'visible',timeout:5000});
  await checkout.getByRole('button',{name:'Fermer',exact:true}).click();
  await checkout.waitFor({state:'detached',timeout:5000});
  await page.getByRole('button',{name:/Ouvrir le panier, 1 unité/i}).first().waitFor({state:'visible',timeout:5000});
  prove(viewport,'marketplace-checkout-close-preserves-cart');

  cart=page.getByRole('button',{name:/Ouvrir le panier, 1 unité/i}).first();
  await cart.click();
  checkout=page.getByRole('dialog',{name:/Préparer le brouillon/i});
  await checkout.getByLabel('Nom complet').fill('Dr G7 Browser');
  await checkout.getByLabel('Cabinet').fill('Cabinet G7');
  await checkout.getByLabel('Email').fill('g7@example.com');
  await checkout.getByLabel('Téléphone').fill('0611111111');
  await checkout.getByLabel('Ville').fill('Rabat');
  const save=checkout.getByRole('button',{name:'Enregistrer le brouillon',exact:true});
  await save.click();
  await checkout.getByText('Brouillon refusé',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(orderCalls!==1 || !(await checkout.isVisible())) throw new Error('marketplace refusal contract mismatch');
  await page.getByRole('button',{name:/Ouvrir le panier, 1 unité/i}).first().waitFor({state:'visible',timeout:5000});
  prove(viewport,'marketplace-draft-refusal-preserves-checkout',{orderCalls});

  await save.click();
  await checkout.waitFor({state:'detached',timeout:10000});
  if(orderCalls!==2) throw new Error('marketplace draft success ACK count mismatch');
  const emptyCartButton=page.getByRole('button',{name:/Ouvrir le panier, 0 unité/i}).first();
  await emptyCartButton.waitFor({state:'visible',timeout:5000});
  if(!(await emptyCartButton.isDisabled())) throw new Error('marketplace cart not emptied/disabled after draft ACK');
  prove(viewport,'marketplace-draft-success-clears-cart',{orderCalls});

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
      if(!favs.includes('detartrage-surfacage')) throw new Error('library favorite did not persist');

      await page.reload({waitUntil:'networkidle',timeout:90000});
      const detReloaded=page.getByText('Détartrage',{exact:true}).first();
      await detReloaded.waitFor({state:'visible',timeout:5000});
      const cardReloaded=detReloaded.locator('xpath=ancestor::button[1]');
      const starReloaded=cardReloaded.locator('span').filter({hasText:/^[☆★]$/}).first();
      await starReloaded.waitFor({state:'visible',timeout:5000});
      if((await starReloaded.innerText()).trim()!=='★') throw new Error('library favorite UI did not survive reload');
      const favsReloaded=await page.evaluate(()=>JSON.parse(localStorage.getItem('dc_favs')||'[]'));
      if(!favsReloaded.includes('detartrage-surfacage')) throw new Error('library favorite storage lost after reload');
      prove(viewport,'library-favorite-reload-persistence');

      await cardReloaded.click();
    } else {
      await card.click();
    }
    await page.waitForURL('**/bibliotheque/detartrage-surfacage');
    prove(viewport,'library-deeplink-navigation');
  }

  // SCIENCE HUB — search + category + safe external link + back navigation.
  await page.goto('http://127.0.0.1:5173/science-hub',{waitUntil:'networkidle',timeout:90000});
  const sciSearch=page.getByPlaceholder('Rechercher un article...');
  if(await sciSearch.count()){
    await sciSearch.fill('zzzz-no-match');
    await page.getByText('Aucun article ne correspond à votre recherche.',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'science-hub-no-result-truth');
    await sciSearch.fill('');
  }

  const endoCategory=page.getByRole('button',{name:'ENDODONTIE',exact:true});
  await endoCategory.click();
  const cards=page.getByTestId('science-article-card');
  const cardCount=await cards.count();
  if(cardCount!==4) throw new Error('science category expected 4 ENDODONTIE cards, got '+cardCount);
  for(let i=0;i<cardCount;i++){
    if((await cards.nth(i).getAttribute('data-category'))!=='ENDODONTIE') {
      throw new Error('science category filter leaked another category');
    }
  }
  prove(viewport,'science-hub-category-filter',{category:'ENDODONTIE',count:cardCount});

  const study=page.getByRole('link',{name:/Consulter l'étude complète/i}).first();
  if(await study.count()){
    const target=await study.getAttribute('target');
    const rel=await study.getAttribute('rel')||'';
    if(target!=='_blank'||!rel.includes('noopener')||!rel.includes('noreferrer')) throw new Error('unsafe science external link');
    prove(viewport,'science-hub-safe-external-link');
  }

  const returnButton=page.getByRole('button',{name:'Retour',exact:true});
  await returnButton.click();
  await page.waitForURL('**/bibliotheque/detartrage-surfacage',{timeout:10000});
  prove(viewport,'science-hub-back-navigation');

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G7_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
