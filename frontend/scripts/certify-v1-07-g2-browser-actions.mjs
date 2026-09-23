import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G2 browser login failed');
const tokens=await login.json();
const headers={Authorization:'Bearer '+tokens.access_token};
const patients=await api.get('/api/patients',{headers});
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('T2 patient missing');

const browser=await chromium.launch({headless:true});
const viewports=[{width:390,height:844},{width:1280,height:900}];
const proofs=[];

async function seed(page){
 await page.addInitScript(v=>{localStorage.setItem('token',v.access);localStorage.setItem('refresh_token',v.refresh||'');localStorage.setItem('appMode','prod');},{access:tokens.access_token,refresh:tokens.refresh_token});
}
function pass(viewport,action,detail={}){proofs.push({viewport:viewport.width+'x'+viewport.height,action,status:'PASS',...detail});}

for(const viewport of viewports){
 const ctx=await browser.newContext({viewport,colorScheme:'light'});
 const page=await ctx.newPage();
 await seed(page);

 await page.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});

 const pilotage=page.getByRole('button',{name:/Pilotage du cabinet/i});
 if(await pilotage.count()){
   const panelId=await pilotage.getAttribute('aria-controls');
   if(!panelId) throw new Error('management panel aria-controls missing');

   await pilotage.click();
   await page.waitForFunction(id=>{
     const button=document.querySelector('[aria-controls="'+id+'"]');
     const panel=document.getElementById(id);
     return button?.getAttribute('aria-expanded')==='true' && !!panel;
   },panelId);
   await page.locator('#'+panelId).waitFor({state:'visible',timeout:5000});
   pass(viewport,'dashboard-management-expand',{panelId});

   await pilotage.click();
   await page.waitForFunction(id=>{
     const button=document.querySelector('[aria-controls="'+id+'"]');
     const panel=document.getElementById(id);
     return button?.getAttribute('aria-expanded')==='false' && !panel;
   },panelId);
   pass(viewport,'dashboard-management-collapse',{panelId});
 }

 const quick=page.getByRole('button',{name:'Ajout rapide'});
 if(await quick.count()){
   await quick.click();
   const create=page.getByRole('menuitem',{name:/Nouveau Patient/i});
   await create.waitFor({state:'visible',timeout:5000});
   await create.click();
   await page.waitForURL('**/patients/new');
   pass(viewport,'dashboard-quick-create-navigation');
   await page.goBack({waitUntil:'networkidle'});
 }

 const searchButton=page.getByRole('button',{name:'Chercher un patient'});
 if(await searchButton.count()) await searchButton.click();
 const dashSearch=page.getByRole('textbox',{name:'Chercher un patient'});
 if(await dashSearch.count()){
   await dashSearch.fill('CERTIFICATION');
   const result=page.getByText(/CERTIFICATION\s+T2/i).first();
   await result.waitFor({state:'visible',timeout:10000});
   await result.click();
   await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'));
   pass(viewport,'dashboard-patient-search-navigation',{patientId:patient.id});
 }

 await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
 const listSearch=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
 await listSearch.waitFor({state:'visible',timeout:15000});
 await listSearch.fill('T2-0001');
 await page.getByText(/CERTIFICATION\s+T2/i).first().waitFor({state:'visible',timeout:10000});
 pass(viewport,'patient-list-search-by-dossier');

 const grid=page.getByRole('button',{name:'Vue Grille'});
 if(await grid.count()){
   await grid.click();
   const mode=await page.evaluate(()=>localStorage.getItem('patient_list_view_mode'));
   if(mode!=='grid') throw new Error('grid mode did not persist');
   if(await page.locator('table').count()) throw new Error('table still rendered in grid mode');
   await page.locator('div[role="button"]').filter({hasText:/CERTIFICATION\s+T2/i}).first().waitFor({state:'visible',timeout:5000});

   await page.reload({waitUntil:'networkidle',timeout:90000});
   if((await page.evaluate(()=>localStorage.getItem('patient_list_view_mode')))!=='grid') throw new Error('grid mode lost after reload');
   if(await page.locator('table').count()) throw new Error('table rendered after grid reload');
   await page.locator('div[role="button"]').filter({hasText:/CERTIFICATION\s+T2/i}).first().waitFor({state:'visible',timeout:5000});

   const table=page.getByRole('button',{name:'Vue Table'});
   await table.click();
   const tableMode=await page.evaluate(()=>localStorage.getItem('patient_list_view_mode'));
   if(tableMode!=='table') throw new Error('table mode did not persist');
   await page.locator('table').waitFor({state:'visible',timeout:5000});
   await page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first().waitFor({state:'visible',timeout:5000});

   await page.reload({waitUntil:'networkidle',timeout:90000});
   if((await page.evaluate(()=>localStorage.getItem('patient_list_view_mode')))!=='table') throw new Error('table mode lost after reload');
   await page.locator('table').waitFor({state:'visible',timeout:5000});
   pass(viewport,'patient-list-view-mode-consumer-persistence');
 }

 // No-result create CTA -> exact query handoff -> visible AddPatientForm prefill.
 const searchAfterReload=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
 await searchAfterReload.fill('G2ABSENT nour');
 await page.getByText('Aucun patient trouvé',{exact:true}).waitFor({state:'visible',timeout:5000});
 await page.getByRole('button',{name:'Ajouter ce patient',exact:true}).click();
 await page.waitForURL(/\/patients\/new\?nom=G2ABSENT&prenom=nour/,{timeout:10000});
 const nomInput=page.locator('input[name="nom"]');
 const prenomInput=page.locator('input[name="prenom"]');
 await nomInput.waitFor({state:'visible',timeout:5000});
 if((await nomInput.inputValue())!=='G2ABSENT') throw new Error('absent-search nom prefill lost');
 if((await prenomInput.inputValue())!=='nour') throw new Error('absent-search prenom prefill lost');
 await page.getByText(/Patient "G2ABSENT nour" introuvable/i).waitFor({state:'visible',timeout:5000});
 pass(viewport,'patient-no-result-add-prefill-handoff');

 // Add patient — duplicate-check refusal must fail closed; successful ACK navigates to the created dossier.
 const dossierInput=page.locator('input[name="numero_dossier"]');
 const birthInput=page.locator('input[name="date_naissance"]');
 const sexInput=page.locator('select[name="sexe"]');
 await dossierInput.fill('G2-BROWSER-NEW');
 await birthInput.fill('1990-01-01');
 await sexInput.selectOption('F');

 await page.route('**/api/patients/check-dossier/*',route=>route.fulfill({
   status:200,contentType:'application/json',body:JSON.stringify({available:true})
 }));
 await page.route('**/api/patients/check-duplicate',route=>route.fulfill({
   status:503,contentType:'application/json',body:JSON.stringify({detail:'forced duplicate-check outage'})
 }));
 await page.getByRole('button',{name:'Créer le dossier',exact:true}).click();
 await page.getByText(/Vérification anti-doublon indisponible/i).waitFor({state:'visible',timeout:10000});
 if(!page.url().includes('/patients/new')) throw new Error('create form navigated after duplicate-check refusal');
 pass(viewport,'patient-create-duplicate-check-refusal-non-mutation');
 await page.unroute('**/api/patients/check-duplicate');

 let createCalls=0;
 const createdId=9099;
 await page.route('**/api/patients/check-duplicate',route=>route.fulfill({
   status:200,contentType:'application/json',body:JSON.stringify({has_duplicate:false})
 }));
 await page.route('**/api/patients/',async route=>{
   if(route.request().method()==='POST'){
     createCalls+=1;
     const body=route.request().postDataJSON();
     if(body.nom!=='G2ABSENT' || body.prenom!=='nour') throw new Error('create payload lost search-prefill identity');
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:createdId,...body})});
   }
   return route.continue();
 });
 await page.route('**/api/patients/'+createdId,async route=>{
   if(route.request().method()==='GET'){
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
       id:createdId,numero_dossier:'G2-BROWSER-NEW',nom:'G2ABSENT',prenom:'nour',
       date_naissance:'1990-01-01',sexe:'F',telephone:'',assurance:'AUCUNE',is_ortho_active:false
     })});
   }
   return route.continue();
 });
 await page.getByRole('button',{name:'Créer le dossier',exact:true}).click();
 await page.waitForURL(new RegExp('/patients/'+createdId+'(?:\\?|$)'),{timeout:10000});
 if(createCalls!==1) throw new Error('patient create ACK count mismatch');
 pass(viewport,'patient-create-success-ack-navigation',{createdId,createCalls});
 await page.unroute('**/api/patients/check-dossier/*');
 await page.unroute('**/api/patients/check-duplicate');
 await page.unroute('**/api/patients/');
 await page.unroute('**/api/patients/'+createdId);

 await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'/edit',{waitUntil:'networkidle',timeout:90000});
 const editNameLabel=page.locator('label').filter({hasText:/^Nom$/}).first();
 const editNameInput=editNameLabel.locator('..').locator('input').first();
 await editNameInput.waitFor({state:'visible',timeout:10000});
 const originalName=await editNameInput.inputValue();

 let refusedEditCalls=0;
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='PUT'){
     refusedEditCalls+=1;
     return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced edit refusal'})});
   }
   return route.continue();
 });
 await editNameInput.fill('G2 REFUSED');
 await page.getByRole('button',{name:/Valider les modifications/i}).click();
 await page.waitForTimeout(300);
 if(refusedEditCalls!==1) throw new Error('patient edit refusal request count mismatch');
 if(!page.url().includes('/edit')) throw new Error('patient edit navigated after refused save');
 pass(viewport,'patient-edit-refusal-non-navigation',{refusedEditCalls});
 await page.unroute('**/api/patients/'+patient.id);

 let acceptedEditCalls=0;
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='PUT'){
     acceptedEditCalls+=1;
     const body=route.request().postDataJSON();
     if(body.nom!=='G2 ACCEPTED') throw new Error('patient edit ACK payload mismatch');
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...patient,nom:'G2 ACCEPTED'})});
   }
   return route.continue();
 });
 await editNameInput.fill('G2 ACCEPTED');
 await page.getByRole('button',{name:/Valider les modifications/i}).click();
 await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'),{timeout:10000});
 if(acceptedEditCalls!==1) throw new Error('patient edit ACK count mismatch');
 pass(viewport,'patient-edit-success-ack-navigation',{acceptedEditCalls});
 await page.unroute('**/api/patients/'+patient.id);

 await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
 const listSearchAfterPrefill=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
 await listSearchAfterPrefill.fill('T2-0001');

 const patientRow=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first();
 await patientRow.waitFor({state:'visible',timeout:10000});
 const edit=patientRow.getByRole('button',{name:'Modifier les infos'});
 if(await edit.count()){
   await Promise.all([
     page.waitForURL(new RegExp('/patients/'+patient.id+'/edit')),
     edit.click(),
   ]);
   pass(viewport,'patient-edit-navigation');
   await page.goBack({waitUntil:'networkidle'});
 }

 await page.getByText(/CERTIFICATION\s+T2/i).first().click();
 await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'));
 pass(viewport,'patient-dossier-navigation');

 // Dossier tabs must drive both URL state and the real rendered surface.
 for(const [label,tab] of [['Vue d’ensemble','tracking'],['Clinique','clinical'],['Imagerie','radiology'],['Document','admin'],['Companion','companion'],['Finances','finances']]){
   const tabButton=page.getByRole('button',{name:label,exact:true}).first();
   if(await tabButton.count()){
     await tabButton.click();
     await page.waitForFunction(expected=>document.querySelector('main[data-flow-patient-surface]')?.getAttribute('data-flow-patient-surface')===expected,tab);
     const url=new URL(page.url());
     if((url.searchParams.get('tab')||'tracking')!==tab) throw new Error('patient dossier tab URL mismatch '+label);
     pass(viewport,'patient-dossier-tab-'+tab);
   }
 }

 // Documents create/history are distinct real consumers.
 const documentTab=page.getByRole('button',{name:'Document',exact:true}).first();
 if(await documentTab.count()){
   await documentTab.click();
   await page.waitForFunction(()=>document.querySelector('main[data-flow-patient-surface]')?.getAttribute('data-flow-patient-surface')==='admin');
   const history=page.getByRole('button',{name:'Historique',exact:true});
   await history.click();
   await page.waitForFunction(()=>document.querySelector('main[data-flow-patient-surface]')?.getAttribute('data-flow-patient-surface')==='archives');
   if(new URL(page.url()).searchParams.get('tab')!=='archives') throw new Error('documents history URL mismatch');
   await page.getByRole('button',{name:'Créer',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('main[data-flow-patient-surface]')?.getAttribute('data-flow-patient-surface')==='admin');
   pass(viewport,'patient-documents-create-history-roundtrip');
 }

 // Quick edit -> real route.
 await page.getByRole('button',{name:'Modifier',exact:true}).click();
 await page.waitForURL(new RegExp('/patients/'+patient.id+'/edit'));
 pass(viewport,'patient-dossier-quick-edit-navigation');
 await page.goBack({waitUntil:'networkidle'});

 // Quick RDV -> Agenda plus router state must carry the current patient.
 const rdv=page.getByRole('button',{name:'RDV',exact:true});
 if(await rdv.count()){
   await rdv.click();
   await page.waitForURL('**/agenda');
   const navState=await page.evaluate(()=>history.state?.usr||null);
   if(Number(navState?.prefillPatientId)!==Number(patient.id)) throw new Error('RDV navigation lost patient prefill state');
   pass(viewport,'patient-dossier-quick-rdv-prefill',{patientId:patient.id});
   await page.goBack({waitUntil:'networkidle'});
 }

 // Ortho activation: deterministic false fixture, refusal keeps module locked, ACK unlocks cephalo.
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='GET') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...patient,is_ortho_active:false})});
   return route.continue();
 });
 let orthoPatchCalls=0;
 let failNextOrtho=true;
 await page.route('**/api/patients/'+patient.id+'/ortho',async route=>{
   if(route.request().method()==='PATCH'){
     orthoPatchCalls+=1;
     if(failNextOrtho){
       failNextOrtho=false;
       return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced ortho refusal'})});
     }
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({is_ortho_active:true})});
   }
   return route.continue();
 });
 await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'?tab=radiology&radioTab=cephalo',{waitUntil:'networkidle',timeout:90000});
 const activateOrtho=page.getByRole('button',{name:/Activer le Suivi Orthodontique/i});
 if(await activateOrtho.count()){
   await activateOrtho.click();
   await page.waitForTimeout(250);
   if(!(await page.getByText('Module Céphalométrique Verrouillé',{exact:true}).count())) throw new Error('cephalo unlocked after refused ortho activation');
   pass(viewport,'patient-ortho-activation-refusal-non-mutation');

   await activateOrtho.click();
   await page.waitForFunction(()=>!document.body.innerText.includes('Module Céphalométrique Verrouillé'),undefined,{timeout:10000});
   if(orthoPatchCalls!==2) throw new Error('ortho activation ACK count mismatch');
   pass(viewport,'patient-ortho-activation-ack',{orthoPatchCalls});
 }
 await page.unroute('**/api/patients/'+patient.id+'/ortho');
 await page.unroute('**/api/patients/'+patient.id);

 await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
 const deleteSearch=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
 await deleteSearch.fill('T2-0001');
 const deleteRow=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first();
 await deleteRow.waitFor({state:'visible',timeout:10000});
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='DELETE') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced delete refusal"}'});
   return route.continue();
 });
 const deleteButton=deleteRow.getByRole('button',{name:'Supprimer définitivement'});
 if(await deleteButton.count()){
   await deleteButton.click();
   const confirmInput=page.getByPlaceholder('T2 CERTIFICATION');
   await confirmInput.fill('T2 CERTIFICATION');
   const confirm=page.getByRole('button',{name:'Supprimer',exact:true});
   await confirm.click();
   await page.waitForTimeout(400);
   if(!(await page.getByText(/CERTIFICATION\s+T2/i).count())) throw new Error('patient disappeared after refused delete');
   pass(viewport,'patient-delete-refusal-non-mutation');
 }
 await page.unroute('**/api/patients/'+patient.id);
 await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G2_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
