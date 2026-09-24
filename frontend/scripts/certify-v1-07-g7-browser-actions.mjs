import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G7 login failed');
const tokens=await login.json();
const superEmail=process.env.T2_SUPERADMIN_EMAIL;
if(!superEmail) throw new Error('T2_SUPERADMIN_EMAIL required for G7 partner admin');
const superApi=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const superLogin=await superApi.post('/api/auth/login',{form:{username:superEmail,password}});
if(!superLogin.ok()) throw new Error('G7 superadmin login failed');
const superTokens=await superLogin.json();
const superMe=await superApi.get('/api/auth/me',{headers:{Authorization:'Bearer '+superTokens.access_token}});
if(!superMe.ok()) throw new Error('G7 superadmin /auth/me failed');
const superUser=await superMe.json();

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
  let failStockReads=true;
  let failNextCreate=false,failNextPatch=false,failNextDelete=false;
  let createCalls=0,patchCalls=0,deleteCalls=0;

  await page.route('**/api/stock/items',async route=>{
    const req=route.request();
    if(req.method()==='GET'){
      if(failStockReads){
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
  await page.getByText('Stock indisponible',{exact:true}).waitFor({state:'visible',timeout:15000});
  if(await page.getByText('Aucun article. Commencez par en ajouter un.',{exact:true}).count()) throw new Error('stock read failure rendered false empty state');
  failStockReads=false;
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

  // PARTNER ADMIN — privileged browser context, mutable supplier/product/order truth.
  const adminCtx=await browser.newContext({viewport,colorScheme:'light'});
  const adminPage=await adminCtx.newPage();
  await adminPage.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
    localStorage.setItem('auth-storage',JSON.stringify({state:{user:v.user,isAuthenticated:true},version:0}));
  },{access:superTokens.access_token,refresh:superTokens.refresh_token,user:superUser});

  let adminSuppliers=[{
    id:11,supplierKey:'atlas',name:'Atlas Dental',badge:'Local',description:'Supplier',promise:'24h',
    apiBaseUrl:null,syncMode:'manual',isActive:true,productCount:1
  }];
  let adminProducts=[{
    id:101,supplierId:11,supplierName:'Atlas Dental',externalProductId:'P101',
    name:'Composite universel',sku:'CMP-101',dentalCategory:'Restauration',dentalSpecialty:'Omnipratique',
    unit:'seringue',price:390,availability:'AVAILABLE',shortDescription:'Composite test',
    longDescription:'Long',benefits:['Facile'],isFeatured:true,sortOrder:1
  }];
  let adminOrders=[{
    id:55,orderNumber:'CMD-055',partnerName:'Atlas Dental',strategyLabel:'Commission',
    status:'DRAFT',estimatedTotal:780,currentTotal:780,recognizedRevenueAmount:0,
    partnerReference:null,statusNote:null
  }];
  const adminMeta={
    categories:['Restauration'],specialties:['Omnipratique'],availability:['AVAILABLE','ON_REQUEST']
  };
  const ordersMeta={supportedStatuses:['DRAFT','CONFIRMED','FULFILLED','CANCELLED']};
  let nextSupplierId=20,nextProductId=200;
  let supplierCreateCalls=0,productCreateCalls=0,reconcileCalls=0;
  let failNextSupplier=false,failNextReconcile=true;
  let adminReadCount=0;

  await adminPage.route('**/api/partner-catalog/**',async route=>{
    const req=route.request();
    const url=new URL(req.url());
    const path=url.pathname;
    const json=(status,body)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
    if(req.method()==='GET'){
      adminReadCount+=1;
      if(path==='/api/partner-catalog/meta') return json(200,adminMeta);
      if(path==='/api/partner-catalog/suppliers') return json(200,adminSuppliers);
      if(path==='/api/partner-catalog/products') return json(200,adminProducts);
    }
    if(req.method()==='POST' && path==='/api/partner-catalog/suppliers'){
      supplierCreateCalls+=1;
      if(failNextSupplier){
        failNextSupplier=false;
        return json(409,{detail:'Clé fournisseur déjà utilisée'});
      }
      const body=req.postDataJSON();
      const created={id:nextSupplierId++,...body,productCount:0};
      adminSuppliers=[...adminSuppliers,created];
      return json(200,created);
    }
    if(req.method()==='POST' && path==='/api/partner-catalog/products'){
      productCreateCalls+=1;
      const body=req.postDataJSON();
      const supplier=adminSuppliers.find(x=>x.id===Number(body.supplierId));
      const created={id:nextProductId++,...body,supplierName:supplier?.name||null};
      adminProducts=[...adminProducts,created];
      return json(200,created);
    }
    return json(500,{detail:'unexpected partner-admin catalog request '+req.method()+' '+path});
  });

  await adminPage.route(/\/api\/partner-orders(?:\/meta|\/\d+)?(?:\?.*)?$/,async route=>{
    const req=route.request();
    const url=new URL(req.url());
    const path=url.pathname;
    const json=(status,body)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
    if(req.method()==='GET'){
      adminReadCount+=1;
      if(path==='/api/partner-orders/meta') return json(200,ordersMeta);
      if(path==='/api/partner-orders') return json(200,adminOrders);
    }
    const match=path.match(/^\/api\/partner-orders\/(\d+)$/);
    if(req.method()==='PATCH' && match){
      reconcileCalls+=1;
      if(failNextReconcile){
        failNextReconcile=false;
        return json(409,{detail:'Transition de statut refusée'});
      }
      const id=Number(match[1]);
      const body=req.postDataJSON();
      adminOrders=adminOrders.map(order=>order.id===id?{
        ...order,
        status:body.status,
        currentTotal:body.currentTotal,
        partnerReference:body.partnerReference,
        statusNote:body.note,
      }:order);
      return json(200,adminOrders.find(order=>order.id===id));
    }
    return json(500,{detail:'unexpected partner-admin order request '+req.method()+' '+path});
  });

  await adminPage.goto('http://127.0.0.1:5173/approvisionnement/admin',{waitUntil:'networkidle',timeout:90000});
  if(!adminPage.url().includes('/approvisionnement/admin')) throw new Error('partner admin redirected despite superadmin fixture');
  const atlasOption=adminPage.locator('option',{hasText:'Atlas Dental'}).first();
  if(!(await atlasOption.count())) throw new Error('Atlas Dental supplier option missing from canonical admin data');
  await adminPage.getByText('CMD-055',{exact:true}).waitFor({state:'visible',timeout:10000});
  prove(viewport,'partner-admin-canonical-load');

  // Supplier ACK -> refetch -> visible.
  let supplierSection=adminPage.getByText('Ajouter un fournisseur',{exact:true}).locator('xpath=ancestor::section[1]');
  let supplierInputs=supplierSection.locator('input[type="text"]');
  await supplierInputs.nth(0).fill('medix');
  await supplierInputs.nth(1).fill('Medix Dental');
  await supplierSection.getByRole('button',{name:'Ajouter fournisseur',exact:true}).click();
  await adminPage.getByText('Fournisseur partenaire ajouté.',{exact:true}).waitFor({state:'visible',timeout:10000});
  const medixOption=adminPage.locator('option',{hasText:'Medix Dental'}).first();
  if(!(await medixOption.count())) throw new Error('Medix Dental supplier option missing after ACK/refetch');
  if(supplierCreateCalls!==1 || !adminSuppliers.some(x=>x.supplierKey==='medix')) throw new Error('partner supplier ACK/refetch mismatch');
  prove(viewport,'partner-admin-supplier-create',{supplierCreateCalls});

  // Supplier refusal -> no false append.
  supplierSection=adminPage.getByText('Ajouter un fournisseur',{exact:true}).locator('xpath=ancestor::section[1]');
  supplierInputs=supplierSection.locator('input[type="text"]');
  await supplierInputs.nth(0).fill('atlas-duplicate');
  await supplierInputs.nth(1).fill('Duplicate Supplier');
  failNextSupplier=true;
  const suppliersBeforeRefusal=adminSuppliers.length;
  await supplierSection.getByRole('button',{name:'Ajouter fournisseur',exact:true}).click();
  await adminPage.getByText('Clé fournisseur déjà utilisée',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(adminSuppliers.length!==suppliersBeforeRefusal) throw new Error('partner supplier refusal mutated fixture');
  prove(viewport,'partner-admin-supplier-refusal-non-mutation');

  // Product create with normalized numeric/benefit data -> refetch -> visible.
  const productSection=adminPage.getByText('Ajouter un produit',{exact:true}).locator('xpath=ancestor::section[1]');
  const productSelects=productSection.locator('select');
  const productText=productSection.locator('input[type="text"]');
  const productNumbers=productSection.locator('input[type="number"]');
  const productAreas=productSection.locator('textarea');
  await productSelects.nth(0).selectOption('11');
  await productText.nth(0).fill('EXT-9');
  await productText.nth(1).fill('Gants premium');
  await productText.nth(2).fill('GLV-9');
  await productSelects.nth(1).selectOption('Restauration');
  await productSelects.nth(2).selectOption('Omnipratique');
  await productText.nth(3).fill('boite');
  await productNumbers.nth(0).fill('125.5');
  await productSelects.nth(3).selectOption('AVAILABLE');
  await productNumbers.nth(1).fill('4');
  await productAreas.nth(0).fill('Court');
  await productAreas.nth(1).fill('Longue');
  await productAreas.nth(2).fill('Sans latex\nConfort');
  const featured=productSection.locator('input[type="checkbox"]').last();
  if(!(await featured.isChecked())) await featured.check();
  await productSection.getByRole('button',{name:'Ajouter produit',exact:true}).click();
  await adminPage.getByText('Produit partenaire ajouté.',{exact:true}).waitFor({state:'visible',timeout:10000});
  await adminPage.getByText('Gants premium',{exact:true}).first().waitFor({state:'visible',timeout:10000});
  const addedProduct=adminProducts.find(x=>x.sku==='GLV-9');
  if(productCreateCalls!==1 || !addedProduct || Number(addedProduct.price)!==125.5 || Number(addedProduct.sortOrder)!==4){
    throw new Error('partner product create normalization mismatch');
  }
  if(JSON.stringify(addedProduct.benefits)!==JSON.stringify(['Sans latex','Confort'])) throw new Error('partner product benefits normalization mismatch');
  prove(viewport,'partner-admin-product-create',{productCreateCalls});

  // Catalog filter is local/non-mutating.
  const catalogSection=adminPage.getByText('Catalogue fournisseur',{exact:true}).locator('xpath=ancestor::section[1]');
  const catalogSearch=catalogSection.locator('input[type="text"]').first();
  await catalogSearch.fill('zzzz-absent');
  await catalogSection.getByText('Aucun produit ne correspond aux filtres',{exact:true}).waitFor({state:'visible',timeout:5000});
  await catalogSearch.fill('GLV-9');
  await catalogSection.getByText('Gants premium',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'partner-admin-catalog-filter');

  // Reconciliation refusal preserves truth; second ACK persists/refetches.
  let orderCard=adminPage.getByText('CMD-055',{exact:true}).locator('xpath=ancestor::div[contains(@class,"border")][1]');
  const orderSelect=orderCard.locator('select').first();
  const orderNumber=orderCard.locator('input[type="number"]').first();
  const orderTexts=orderCard.locator('input[type="text"]');
  const orderNote=orderTexts.nth(1);
  await orderSelect.selectOption('CONFIRMED');
  await orderNumber.fill('750');
  await orderTexts.nth(0).fill('REF-77');
  await orderNote.fill('Confirmé par fournisseur');
  await orderCard.getByRole('button',{name:'Enregistrer les modifications',exact:true}).click();
  await adminPage.getByText('Transition de statut refusée',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(reconcileCalls!==1 || adminOrders[0].status!=='DRAFT' || Number(adminOrders[0].currentTotal)!==780) throw new Error('partner reconciliation refusal mutated truth');
  prove(viewport,'partner-admin-reconcile-refusal-non-mutation',{reconcileCalls});

  orderCard=adminPage.getByText('CMD-055',{exact:true}).locator('xpath=ancestor::div[contains(@class,"border")][1]');
  await orderCard.getByRole('button',{name:'Enregistrer les modifications',exact:true}).click();
  await adminPage.getByText(/Commande CMD-055 mise à jour/i).waitFor({state:'visible',timeout:10000});
  if(reconcileCalls!==2 || adminOrders[0].status!=='CONFIRMED' || Number(adminOrders[0].currentTotal)!==750 || adminOrders[0].partnerReference!=='REF-77'){
    throw new Error('partner reconciliation ACK/refetch mismatch');
  }
  prove(viewport,'partner-admin-reconcile-success',{reconcileCalls});

  // Explicit reload -> actual canonical reads.
  const readsBeforeAdminReload=adminReadCount;
  const reloadButton=adminPage.getByRole('button',{name:'Recharger',exact:true}).first();
  await reloadButton.click();
  await adminPage.waitForResponse(r=>r.request().method()==='GET' && r.url().includes('/api/partner-catalog/products'),{timeout:10000}).catch(()=>null);
  await adminPage.waitForTimeout(100);
  if(adminReadCount<=readsBeforeAdminReload) throw new Error('partner admin Recharger did not refetch canonical truth');
  prove(viewport,'partner-admin-explicit-reload',{adminReadCount});

  await adminPage.unroute('**/api/partner-catalog/**');
  await adminPage.unroute('**/api/partner-orders**');
  await adminCtx.close();

  // PARTNER DETAIL PAGES — supplier filters/deeplink/retry + product cart/discontinued/not-found truth.
  const detailSupplier={
    id:11,supplierKey:'atlas',name:'Atlas Dental',badge:'Local',description:'Fournisseur test',
    promise:'24h',apiBaseUrl:null,syncMode:'manual',isActive:true,productCount:2
  };
  const detailProducts=[
    {
      id:101,supplierId:11,supplierName:'Atlas Dental',externalProductId:'P101',
      name:'Composite universel',sku:'CMP-101',dentalCategory:'Restauration',dentalSpecialty:'Omnipratique',
      unit:'seringue',price:390,availability:'AVAILABLE',shortDescription:'Composite test',
      longDescription:'Composite premium',benefits:['Facile'],isFeatured:true,sortOrder:1
    },
    {
      id:102,supplierId:11,supplierName:'Atlas Dental',externalProductId:'P102',
      name:'Produit arrêté',sku:'OLD-102',dentalCategory:'Endodontie',dentalSpecialty:'Endodontie',
      unit:'boîte',price:120,availability:'DISCONTINUED',shortDescription:'Ancien produit',
      longDescription:'Ancien produit',benefits:[],isFeatured:false,sortOrder:2
    }
  ];
  let detailCatalogReads=0;
  let failSupplierReads=1;
  await page.route('**/api/partner-catalog/meta',route=>{
    detailCatalogReads+=1;
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
      categories:['Restauration','Endodontie'],specialties:['Omnipratique','Endodontie'],availability:['AVAILABLE','DISCONTINUED']
    })});
  });
  await page.route('**/api/partner-catalog/suppliers',route=>{
    detailCatalogReads+=1;
    if(failSupplierReads>0){
      failSupplierReads-=1;
      return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'supplier read failure'})});
    }
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([detailSupplier])});
  });
  await page.route('**/api/partner-catalog/products',route=>{
    detailCatalogReads+=1;
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(detailProducts)});
  });
  await page.route('**/api/partner-catalog/products/*',route=>{
    detailCatalogReads+=1;
    const id=Number(new URL(route.request().url()).pathname.split('/').pop());
    const item=detailProducts.find(x=>x.id===id);
    if(!item) return route.fulfill({status:404,contentType:'application/json',body:JSON.stringify({detail:'not found'})});
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(item)});
  });
  await page.route('**/api/partner-catalog/suppliers/*',route=>{
    detailCatalogReads+=1;
    const id=Number(new URL(route.request().url()).pathname.split('/').pop());
    if(id!==11) return route.fulfill({status:404,contentType:'application/json',body:JSON.stringify({detail:'not found'})});
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(detailSupplier)});
  });

  // Supplier page must fail closed without stale cache, then retry, filter, reload and deep-link.
  await page.evaluate(()=>{ for(const key of Object.keys(localStorage)){ if(key.startsWith('digitalcrown_partner_marketplace_cache_v1')) localStorage.removeItem(key); } });
  await page.goto('http://127.0.0.1:5173/approvisionnement/partenaire/11',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Impossible de charger le catalogue de ce fournisseur',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(await page.getByRole('link',{name:/Composite universel/i}).count()) throw new Error('supplier page exposed cached product during first read failure');
  await page.getByRole('button',{name:'Réessayer',exact:true}).click();
  await page.getByRole('link',{name:/Composite universel/i}).waitFor({state:'visible',timeout:10000});
  prove(viewport,'partner-supplier-read-failure-retry');

  const supplierReadsBeforeReload=detailCatalogReads;
  const supplierReloadPromise=page.waitForResponse(
    r=>r.request().method()==='GET' && r.url().includes('/api/partner-catalog/products'),
    {timeout:10000}
  );
  await page.getByRole('button',{name:'Recharger',exact:true}).click();
  const supplierReloadAck=await supplierReloadPromise;
  if(!supplierReloadAck.ok() || detailCatalogReads<=supplierReadsBeforeReload) throw new Error('supplier Recharger did not refetch');
  prove(viewport,'partner-supplier-explicit-reload',{detailCatalogReads});

  await page.getByRole('button',{name:'Endodontie',exact:true}).first().click();
  await page.getByRole('link',{name:/Produit arrêté/i}).waitFor({state:'visible',timeout:5000});
  if(await page.getByRole('link',{name:/Composite universel/i}).count()) throw new Error('supplier category filter leaked product');
  await page.getByRole('button',{name:'Omnipratique',exact:true}).click();
  await page.getByText(/Aucun produit ne correspond/i).waitFor({state:'visible',timeout:5000});
  prove(viewport,'partner-supplier-category-specialty-filter');

  await page.getByRole('button',{name:'Toutes',exact:true}).first().click();
  await page.getByRole('button',{name:'Toutes',exact:true}).last().click();
  const productLink=page.getByRole('link',{name:/Composite universel/i});
  const productHref=await productLink.getAttribute('href');
  if(productHref!=='/approvisionnement/produits/101') throw new Error('supplier product deep-link mismatch '+productHref);
  await productLink.click();
  await page.waitForURL('**/approvisionnement/produits/101',{timeout:10000});
  await page.getByRole('heading',{name:'Composite universel',level:1}).waitFor({state:'visible',timeout:10000});
  prove(viewport,'partner-supplier-product-deeplink');

  // Product page: canonical links + cart +/- persistence across reload.
  const backLink=page.getByRole('link',{name:/Retour catalogue/i});
  if((await backLink.getAttribute('href'))!=='/approvisionnement') throw new Error('product back link mismatch');
  const supplierLink=page.getByRole('link',{name:/Voir fournisseur/i});
  if((await supplierLink.getAttribute('href'))!=='/approvisionnement/partenaire/11') throw new Error('product supplier link mismatch');

  const productPlus=page.getByRole('button',{name:'Ajouter une unité de Composite universel',exact:true});
  const productMinus=page.getByRole('button',{name:'Retirer une unité de Composite universel',exact:true});
  await productPlus.click();
  await productPlus.click();
  await page.getByRole('link',{name:/2 dans le panier/i}).waitFor({state:'visible',timeout:5000});
  await productMinus.click();
  await page.getByRole('link',{name:/1 dans le panier/i}).waitFor({state:'visible',timeout:5000});
  await page.reload({waitUntil:'networkidle',timeout:90000});
  await page.getByRole('link',{name:/1 dans le panier/i}).waitFor({state:'visible',timeout:10000});
  prove(viewport,'partner-product-cart-reload-persistence');

  // Discontinued product must not expose ordering controls.
  await page.goto('http://127.0.0.1:5173/approvisionnement/produits/102',{waitUntil:'networkidle',timeout:90000});
  await page.getByRole('heading',{name:'Produit arrêté',level:1}).waitFor({state:'visible',timeout:10000});
  await page.getByText(/ne peut plus être commandé/i).waitFor({state:'visible',timeout:5000});
  if(await page.getByRole('button',{name:/Ajouter une unité/i}).count()) throw new Error('discontinued product exposes add quantity');
  if(await page.getByText('Retourner à la commande partenaire',{exact:true}).count()) throw new Error('discontinued product exposes order return action');
  prove(viewport,'partner-product-discontinued-order-lock');

  // Missing product truth -> explicit state -> return catalogue.
  await page.goto('http://127.0.0.1:5173/approvisionnement/produits/999',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Produit introuvable.',{exact:true}).waitFor({state:'visible',timeout:10000});
  await page.getByRole('button',{name:'Revenir au catalogue',exact:true}).click();
  await page.waitForURL('**/approvisionnement',{timeout:10000});
  prove(viewport,'partner-product-not-found-return');

  await page.unroute('**/api/partner-catalog/meta');
  await page.unroute('**/api/partner-catalog/suppliers');
  await page.unroute('**/api/partner-catalog/products');
  await page.unroute('**/api/partner-catalog/products/*');
  await page.unroute('**/api/partner-catalog/suppliers/*');

  // LIBRARY — search/reset, favorite filter, view/sort consumer, deep-link, recents, nav, print, soin mode, command palette.
  await page.goto('http://127.0.0.1:5173/bibliotheque',{waitUntil:'networkidle',timeout:90000});
  const libSearch=page.getByPlaceholder('Avulsion, composite, blanchiment…');
  await libSearch.waitFor({state:'visible',timeout:10000});

  await libSearch.fill('ENDO');
  await page.getByText('Traitement endodontique',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'library-search-match');

  await libSearch.fill('zzzz-no-match');
  await page.getByText('Aucun protocole trouvé',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:/Réinitialiser les filtres/i}).click();
  await page.getByText('Détartrage',{exact:true}).first().waitFor({state:'visible',timeout:5000});
  if((await libSearch.inputValue())!=='') throw new Error('library reset did not clear search');
  prove(viewport,'library-no-result-reset');

  const protocolList=page.getByTestId('library-protocol-list');
  const order=async()=>protocolList.locator('[data-protocol-code]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-protocol-code')));
  const alphaOrder=await order();

  await page.getByTitle('Vue liste').click();
  if((await protocolList.getAttribute('data-library-view'))!=='list') throw new Error('library list view consumer mismatch');
  await page.getByTitle('Vue grille').click();
  if((await protocolList.getAttribute('data-library-view'))!=='grid') throw new Error('library grid view consumer mismatch');
  prove(viewport,'library-grid-list-consumer');

  await page.getByRole('button',{name:'Difficulté',exact:true}).click();
  if((await protocolList.getAttribute('data-library-sort'))!=='difficulty') throw new Error('library difficulty sort state mismatch');
  const difficultyOrder=await order();
  if(JSON.stringify(difficultyOrder)===JSON.stringify(alphaOrder)) throw new Error('library difficulty sort did not alter rendered order');
  await page.getByRole('button',{name:'Discipline',exact:true}).click();
  if((await protocolList.getAttribute('data-library-sort'))!=='category') throw new Error('library category sort state mismatch');
  const categoryOrder=await order();
  if(JSON.stringify(categoryOrder)===JSON.stringify(difficultyOrder)) throw new Error('library category sort did not alter rendered order');
  prove(viewport,'library-sort-consumer');

  // Return alpha before stable target selection.
  await page.getByRole('button',{name:'A→Z',exact:true}).click();
  const detCard=page.locator('[data-protocol-code="detartrage-surfacage"]').first();
  await detCard.waitFor({state:'visible',timeout:5000});
  const detStar=detCard.locator('span').filter({hasText:/^[☆★]$/}).first();
  await detStar.click();
  let favs=await page.evaluate(()=>JSON.parse(localStorage.getItem('dc_favs')||'[]'));
  if(!favs.includes('detartrage-surfacage')) throw new Error('library favorite did not persist');

  await page.reload({waitUntil:'networkidle',timeout:90000});
  favs=await page.evaluate(()=>JSON.parse(localStorage.getItem('dc_favs')||'[]'));
  if(!favs.includes('detartrage-surfacage')) throw new Error('library favorite storage lost after reload');
  if(viewport.width>=768){
    await page.getByRole('button',{name:/Favoris/i}).click();
    const favProtocolList=page.getByTestId('library-protocol-list');
    const favCodes=await favProtocolList.locator('[data-protocol-code]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-protocol-code')));
    if(favCodes.length!==1 || favCodes[0]!=='detartrage-surfacage') throw new Error('library favorites filter mismatch');
    await page.getByRole('button',{name:/Tous/i}).first().click();
  }
  prove(viewport,'library-favorite-filter-reload-persistence',{filterChecked:viewport.width>=768});

  // Open protocol: recents + route.
  await page.locator('[data-protocol-code="detartrage-surfacage"]').first().click();
  await page.waitForURL('**/bibliotheque/detartrage-surfacage',{timeout:10000});
  let recents=await page.evaluate(()=>JSON.parse(localStorage.getItem('dc_recents')||'[]'));
  if(recents[0]!=='detartrage-surfacage') throw new Error('library recent history not recorded');
  prove(viewport,'library-deeplink-and-recent');

  const initialProtocolUrl=page.url();
  await page.getByTitle('Suivant (→)').click();
  await page.waitForFunction(url=>location.href!==url,initialProtocolUrl);
  const nextUrl=page.url();
  if(nextUrl===initialProtocolUrl) throw new Error('library next did not navigate');
  await page.getByTitle('Précédent (←)').click();
  await page.waitForURL('**/bibliotheque/detartrage-surfacage',{timeout:5000});
  prove(viewport,'library-next-previous-roundtrip');

  // Print action.
  await page.evaluate(()=>{ window.__g7PrintCount=0; window.print=()=>{window.__g7PrintCount+=1;}; });
  await page.getByTitle('Imprimer (P)').click();
  const printCount=await page.evaluate(()=>window.__g7PrintCount||0);
  if(printCount!==1) throw new Error('library print action not invoked');
  prove(viewport,'library-print-action',{printCount});

  // Immersive care mode opens and explicitly returns.
  await page.getByRole('button',{name:/Ouvrir en mode Soin/i}).click();
  await page.getByText('Mode Soin Actif',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:/Retour Bibliothèque/i}).click();
  await page.getByText('Mode Soin Actif',{exact:true}).waitFor({state:'detached',timeout:5000});
  prove(viewport,'library-soin-mode-open-close');

  // Close detail then command palette via button and keyboard.
  const closeProtocolButton=page.getByTitle('Fermer (Esc)');
  await closeProtocolButton.click();
  await closeProtocolButton.waitFor({state:'detached',timeout:5000});
  await page.waitForFunction(()=>location.pathname==='/bibliotheque',null,{timeout:5000});
  if(new URL(page.url()).pathname!=='/bibliotheque') throw new Error('library close did not return to root');
  await page.getByRole('button',{name:/Rechercher/i}).first().click();
  let cmd=page.getByPlaceholder('Rechercher un protocole ou une spécialité...');
  await cmd.waitFor({state:'visible',timeout:5000});
  await cmd.fill('endodontique');
  await cmd.press('Enter');
  await page.waitForURL(/\/bibliotheque\/.+/, {timeout:10000});
  if(page.url().endsWith('/bibliotheque')) throw new Error('library command palette did not open protocol');
  prove(viewport,'library-command-palette-open-result');

  await page.keyboard.press('Escape');
  await page.waitForFunction(()=>location.pathname==='/bibliotheque',null,{timeout:5000});
  if(new URL(page.url()).pathname!=='/bibliotheque') throw new Error('library Escape did not return to root');
  await page.keyboard.press('Control+K');
  cmd=page.getByPlaceholder('Rechercher un protocole ou une spécialité...');
  await cmd.waitFor({state:'visible',timeout:5000});
  await cmd.fill('zzzz-no-match');
  await page.getByText('Aucun protocole ne correspond à votre recherche.',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.keyboard.press('Escape');
  await cmd.waitFor({state:'detached',timeout:5000});
  prove(viewport,'library-command-palette-keyboard-escape');

  // Recent history remains visible and explicit clear mutates only local history.
  await page.getByText('Récemment consultés',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:'Effacer',exact:true}).click();
  recents=await page.evaluate(()=>JSON.parse(localStorage.getItem('dc_recents')||'[]'));
  if(recents.length!==0) throw new Error('library recent clear did not persist');
  prove(viewport,'library-recent-clear');

  // SCIENCE HUB — title/author search, category truth, safe external link, back navigation.
  await page.goto('http://127.0.0.1:5173/science-hub',{waitUntil:'networkidle',timeout:90000});
  const sciSearch=page.getByPlaceholder('Rechercher un article...');
  await sciSearch.waitFor({state:'visible',timeout:10000});

  await sciSearch.fill('Ultrasonic');
  await page.getByText('Ultrasonic vs Sonic Activation of Sodium Hypochlorite',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(await page.getByText('Root Resorption in Clear Aligner Therapy vs Fixed Appliances',{exact:true}).count()) throw new Error('science title search leaked unrelated article');
  prove(viewport,'science-hub-title-search');

  await sciSearch.fill('Zanza');
  await page.getByText('Bioceramic Sealers in Endodontics: Clinical Success Rates',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'science-hub-author-search');
  await sciSearch.fill('');

  const endoCategory=page.getByRole('button',{name:'ENDODONTIE',exact:true});
  await endoCategory.click();
  const cards=page.getByTestId('science-article-card');
  const cardCount=await cards.count();
  if(cardCount<1) throw new Error('science ENDODONTIE filter returned no cards');
  for(let i=0;i<cardCount;i++){
    if((await cards.nth(i).getAttribute('data-category'))!=='ENDODONTIE') throw new Error('science category filter leaked another category');
  }
  prove(viewport,'science-hub-category-filter',{category:'ENDODONTIE',count:cardCount});

  await sciSearch.fill('zzzz-no-match');
  await page.getByText('Aucun article ne correspond à votre recherche.',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'science-hub-no-result-truth');
  await sciSearch.fill('');

  const study=page.getByRole('link',{name:/Consulter l'étude complète/i}).first();
  if(await study.count()){
    const href=await study.getAttribute('href');
    const target=await study.getAttribute('target');
    const rel=await study.getAttribute('rel')||'';
    if(!href?.startsWith('https://pubmed.ncbi.nlm.nih.gov/') || target!=='_blank' || !rel.includes('noopener') || !rel.includes('noreferrer')){
      throw new Error('science external link contract mismatch');
    }
    prove(viewport,'science-hub-safe-external-link',{href});
  }

  const returnButton=page.getByRole('button',{name:'Retour',exact:true});
  await returnButton.click();
  await page.waitForURL('**/bibliotheque',{timeout:10000});
  prove(viewport,'science-hub-back-navigation');

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G7_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
