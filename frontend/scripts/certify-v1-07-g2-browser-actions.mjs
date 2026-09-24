import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G2 browser login failed');
const tokens=await login.json();
const restrictedApi=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const restrictedLogin=await restrictedApi.post('/api/auth/login',{form:{username:'t2-restricted@cabinet.ma',password}});
if(!restrictedLogin.ok()) throw new Error('G2 restricted login failed');
const restrictedTokens=await restrictedLogin.json();
const headers={Authorization:'Bearer '+tokens.access_token};
const patients=await api.get('/api/patients',{headers});
if(!patients.ok()) throw new Error('G2 patients fixture read failed '+patients.status()+': '+await patients.text());
const patientsBody=await patients.json();
const patientList=Array.isArray(patientsBody)?patientsBody:(Array.isArray(patientsBody?.items)?patientsBody.items:(Array.isArray(patientsBody?.patients)?patientsBody.patients:[]));
const patient=patientList.find(x=>x.numero_dossier==='T2-0001');
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


 let dashboardAppointment={
   id:701,
   start_time:'2026-09-23T10:00:00',
   status:'PRÉVU',
   description:'Certification Dashboard',
   patient:{nom:'DASHBOARD',prenom:'Browser'}
 };
 let appointmentPutCalls=0;
 await page.route('**/api/appointments/**',async route=>{
   const req=route.request();
   const url=new URL(req.url());
   if(req.method()==='GET' && url.pathname==='/api/appointments/'){
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([dashboardAppointment])});
   }
   if(req.method()==='PUT' && url.pathname==='/api/appointments/701'){
     appointmentPutCalls+=1;
     const body=req.postDataJSON();
     dashboardAppointment={...dashboardAppointment,status:body.status};
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(dashboardAppointment)});
   }
   return route.continue();
 });

 let dashboardAlerts=[
   {id:21,patient_id:patient.id,nom:'DASH',prenom:'Snooze',type:'FOLLOWUP',title:'Alerte snooze',message:'',action:'Rappeler',priority:1},
   {id:22,patient_id:patient.id,nom:'DASH',prenom:'Read',type:'FOLLOWUP',title:'Alerte read',message:'',action:'Contrôler',priority:2},
   {id:23,patient_id:patient.id,nom:'DASH',prenom:'Navigate',type:'FOLLOWUP',title:'Alerte navigate',message:'',action:'Ouvrir dossier',priority:1}
 ];
 let snoozeCalls=0,readCalls=0;
 await page.route('**/api/intelligence/alerts/**',async route=>{
   const req=route.request();
   const url=new URL(req.url());
   if(req.method()==='GET' && url.pathname==='/api/intelligence/alerts/today'){
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({total:dashboardAlerts.length,alerts:dashboardAlerts})});
   }
   let match=url.pathname.match(/^\/api\/intelligence\/alerts\/(\d+)\/snooze$/);
   if(req.method()==='PATCH' && match){
     snoozeCalls+=1;
     dashboardAlerts=dashboardAlerts.filter(a=>a.id!==Number(match[1]));
     return route.fulfill({status:200,contentType:'application/json',body:'{}'});
   }
   match=url.pathname.match(/^\/api\/intelligence\/alerts\/(\d+)\/read$/);
   if(req.method()==='PATCH' && match){
     readCalls+=1;
     dashboardAlerts=dashboardAlerts.filter(a=>a.id!==Number(match[1]));
     return route.fulfill({status:200,contentType:'application/json',body:'{}'});
   }
   return route.continue();
 });

 const bridgeOptions={
   expires_in:300,
   targets:[{
     id:77,name:'Dr Mobile Browser',email:'mobile@example.com',role:'DENTISTE',is_current_user:true,
     destinations:[{id:'dashboard',label:'Tableau de bord'},{id:'agenda',label:'Agenda'}]
   }]
 };
 let pairingCalls=0,revokeCalls=0,failNextRevoke=true;
 await page.route('**/api/mobile/bridge-options',route=>route.fulfill({
   status:200,contentType:'application/json',body:JSON.stringify(bridgeOptions)
 }));
 await page.route('**/api/mobile/bridge-pairing',async route=>{
   pairingCalls+=1;
   const body=route.request().postDataJSON();
   if(body.target_user_id!==77 || body.destination!=='dashboard') throw new Error('mobile pairing payload mismatch');
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
     qr_code:'data:image/png;base64,iVBORw0KGgo=',
     token_code:'G2MOB1',
     expires_in:300,
     target_user_id:77,
     target_user_name:'Dr Mobile Browser',
     target_role:'DENTISTE',
     destination:'dashboard',
     destination_label:'Tableau de bord',
     contains_patient_data:false
   })});
 });
 await page.route('**/api/admin/revoke-mobile',async route=>{
   revokeCalls+=1;
   if(failNextRevoke){
     failNextRevoke=false;
     return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced mobile revoke refusal'})});
   }
   return route.fulfill({status:200,contentType:'application/json',body:'{}'});
 });

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

 // Waiting room: each click must persist to the fixture, refetch and drive the next UI state.
 const arrived=page.getByRole('button',{name:'Marquer Arrivé',exact:true});
 await arrived.waitFor({state:'visible',timeout:10000});
 await arrived.click();
 await page.getByRole('button',{name:'Installer au Fauteuil',exact:true}).waitFor({state:'visible',timeout:10000});
 if(dashboardAppointment.status!=='EN_S_ATTENTE' || appointmentPutCalls!==1) throw new Error('waiting-room arrival ACK mismatch');
 pass(viewport,'dashboard-waiting-arrived',{appointmentPutCalls});

 await page.getByRole('button',{name:'Installer au Fauteuil',exact:true}).click();
 await page.getByRole('button',{name:'Terminer la Séance',exact:true}).waitFor({state:'visible',timeout:10000});
 if(dashboardAppointment.status!=='EN_FAUTEUIL' || appointmentPutCalls!==2) throw new Error('waiting-room chair ACK mismatch');
 pass(viewport,'dashboard-waiting-chair',{appointmentPutCalls});

 await page.getByRole('button',{name:'Terminer la Séance',exact:true}).click();
 await page.getByText(/Patient Sortant : DASHBOARD Browser/i).waitFor({state:'visible',timeout:10000});
 if(dashboardAppointment.status!=='TERMINÉ' || appointmentPutCalls!==3) throw new Error('waiting-room completion ACK mismatch');
 pass(viewport,'dashboard-waiting-complete-ghost-action',{appointmentPutCalls});

 for(const label of ['Encaisser les soins du jour',"Remettre l'ordonnance",'Fixer le RDV de contrôle']){
   const checkbox=page.getByLabel(label,{exact:true});
   await checkbox.check();
 }
 await page.getByText('Action terminée !',{exact:true}).waitFor({state:'visible',timeout:5000});
 await page.getByText(/Patient Sortant : DASHBOARD Browser/i).waitFor({state:'detached',timeout:3000});
 pass(viewport,'dashboard-ghost-checklist-completion');

 // Alerts: ACK removes only the targeted alert; navigation opens the patient dossier.
 const snoozeRow=page.getByText(/DASH Snooze/i).locator('xpath=ancestor::div[.//button[@aria-label="Reporter cette alerte de 24h"]][1]');
 await snoozeRow.getByRole('button',{name:'Reporter cette alerte de 24h'}).click();
 await page.getByText(/DASH Snooze/i).waitFor({state:'detached',timeout:10000});
 if(snoozeCalls!==1 || dashboardAlerts.some(a=>a.id===21)) throw new Error('alert snooze ACK mismatch');
 pass(viewport,'dashboard-alert-snooze',{snoozeCalls});

 const readRow=page.getByText(/DASH Read/i).locator('xpath=ancestor::div[.//button[@aria-label="Marquer cette alerte comme lue"]][1]');
 await readRow.getByRole('button',{name:'Marquer cette alerte comme lue'}).click();
 await page.getByText(/DASH Read/i).waitFor({state:'detached',timeout:10000});
 if(readCalls!==1 || dashboardAlerts.some(a=>a.id===22)) throw new Error('alert mark-read ACK mismatch');
 pass(viewport,'dashboard-alert-mark-read',{readCalls});

 // Mobile security: real modal focus, pairing, refusal, success, Escape close + focus restoration.
 const mobileOpen=page.getByRole('button',{name:'Appairer le téléphone mobile',exact:true});
 if(await mobileOpen.count()){
   await mobileOpen.click();
   const dialog=page.getByRole('dialog',{name:'Sécurité mobile'});
   await dialog.waitFor({state:'visible',timeout:10000});
   const closeMobile=dialog.getByRole('button',{name:'Fermer la fenêtre de sécurité mobile'});
   await page.waitForFunction(()=>document.activeElement?.getAttribute('aria-label')==='Fermer la fenêtre de sécurité mobile');
   pass(viewport,'dashboard-mobile-dialog-focus');

   const target=dialog.getByLabel('Utilisateur mobile cible');
   const destination=dialog.getByLabel('Destination mobile');
   await target.selectOption('77');
   await destination.selectOption('dashboard');
   await dialog.getByRole('button',{name:/Générer le QR de connexion/i}).click();
   await dialog.getByText('G2MOB1',{exact:true}).waitFor({state:'visible',timeout:10000});
   if(pairingCalls!==1) throw new Error('mobile pairing ACK count mismatch');
   pass(viewport,'dashboard-mobile-pairing',{pairingCalls});

   page.once('dialog',d=>d.accept());
   await dialog.getByRole('button',{name:/Révoquer tous les accès mobiles/i}).click();
   await dialog.getByText('forced mobile revoke refusal',{exact:true}).waitFor({state:'visible',timeout:10000});
   if(revokeCalls!==1) throw new Error('mobile revoke refusal count mismatch');
   if(!(await dialog.getByText('G2MOB1',{exact:true}).count())) throw new Error('mobile pairing disappeared after refused revoke');
   pass(viewport,'dashboard-mobile-revoke-refusal-non-mutation');

   page.once('dialog',d=>d.accept());
   await dialog.getByRole('button',{name:/Révoquer tous les accès mobiles/i}).click();
   await dialog.getByText(/Tous les téléphones ont été déconnectés/i).waitFor({state:'visible',timeout:10000});
   if(revokeCalls!==2) throw new Error('mobile revoke ACK count mismatch');
   await dialog.getByText('G2MOB1',{exact:true}).waitFor({state:'detached',timeout:5000});
   pass(viewport,'dashboard-mobile-revoke-ack',{revokeCalls});

   await page.keyboard.press('Escape');
   await dialog.waitFor({state:'detached',timeout:5000});
   await page.waitForFunction(()=>document.activeElement?.getAttribute('aria-label')==='Appairer le téléphone mobile');
   pass(viewport,'dashboard-mobile-escape-focus-restore');
 }

 // Alert navigation is checked last because it intentionally leaves the Dashboard.
 const navigateAlert=page.getByText(/DASH Navigate/i);
 await navigateAlert.click();
 await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'),{timeout:10000});
 pass(viewport,'dashboard-alert-patient-navigation',{patientId:patient.id});
 await page.goBack({waitUntil:'networkidle'});

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
 const dossierPrecheck=await api.get('/api/patients/check-dossier/G2-BROWSER-NEW',{headers});
 if(!dossierPrecheck.ok()) throw new Error('dossier availability precheck HTTP '+dossierPrecheck.status());
 const dossierPrecheckBody=await dossierPrecheck.json();
 if(dossierPrecheckBody.exists!==false) throw new Error('dossier availability precheck expected exists=false');
 const browserDossierProbe=await page.evaluate(async()=>{
   const token=localStorage.getItem('token');
   const response=await fetch('http://127.0.0.1:8005/api/patients/check-dossier/G2-BROWSER-NEW',{
     headers:{Authorization:'Bearer '+token}
   });
   const body=await response.json().catch(()=>null);
   return {status:response.status,body};
 });
 if(browserDossierProbe.status!==200 || browserDossierProbe.body?.exists!==false){
   throw new Error('browser dossier availability probe mismatch '+JSON.stringify(browserDossierProbe));
 }
 await page.waitForFunction(
   ()=>((document.querySelector('input[name="numero_dossier"]')?.value||'').trim().length>=2),
   null,
   {timeout:10000}
 );
 const initialDossierValue=await dossierInput.inputValue();
 if(!initialDossierValue) throw new Error('initial auto dossier number missing before replacement');
 await dossierInput.fill('');
 await dossierInput.pressSequentially('G2-BROWSER-NEW',{delay:20});
 if((await dossierInput.inputValue())!=='G2-BROWSER-NEW') throw new Error('dossier sequential input mismatch after initial auto-number settled');
 await page.getByText(/Numéro disponible/i).waitFor({state:'visible',timeout:10000});
 await page.waitForFunction(
   ()=>document.querySelector('input[name="numero_dossier"]')?.classList.contains('border-emerald-400')===true,
   null,
   {timeout:10000}
 );
 const availabilityTruth=page.locator('p.text-emerald-600').filter({hasText:'Numéro disponible'});
 if(await availabilityTruth.count()!==1) throw new Error('dossier availability visible truth missing after backend ACK');
 if((await dossierInput.inputValue())!=='G2-BROWSER-NEW') throw new Error('dossier input value drifted after backend availability check');
 const dossierPostcheck=await api.get('/api/patients/check-dossier/G2-BROWSER-NEW',{headers});
 if(!dossierPostcheck.ok()) throw new Error('dossier availability postcheck HTTP '+dossierPostcheck.status());
 const dossierPostcheckBody=await dossierPostcheck.json();
 if(dossierPostcheckBody.exists!==false) throw new Error('dossier availability postcheck expected exists=false before create');
 await birthInput.fill('1990-01-01');
 await sexInput.selectOption('F');
 await page.route('**/api/patients/check-duplicate*',route=>route.fulfill({
   status:503,contentType:'application/json',body:JSON.stringify({detail:'forced duplicate-check outage'})
 }));
 await page.getByRole('button',{name:'Créer le dossier',exact:true}).click();
 await page.getByText(/Vérification anti-doublon indisponible/i).waitFor({state:'visible',timeout:10000});
 if(!page.url().includes('/patients/new')) throw new Error('create form navigated after duplicate-check refusal');
 pass(viewport,'patient-create-duplicate-check-refusal-non-mutation');
 await page.unroute('**/api/patients/check-duplicate*');

 let createCalls=0;
 const createdId=9099;
 await page.route('**/api/patients/check-duplicate*',route=>route.fulfill({
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
 await page.unroute('**/api/patients/check-duplicate*');
 await page.unroute('**/api/patients/');
 await page.unroute('**/api/patients/'+createdId);

 // Duplicate detection: opening existing dossier must not create a patient.
 await page.goto('http://127.0.0.1:5173/patients/new?nom=DUPLICATE&prenom=Case',{waitUntil:'networkidle',timeout:90000});
 let duplicateCreateCalls=0;
 await page.route('**/api/patients/check-duplicate*',route=>route.fulfill({
   status:200,contentType:'application/json',body:JSON.stringify({
     has_duplicate:true,
     existing_patient:{
       id:patient.id,nom:patient.nom,prenom:patient.prenom,date_naissance:patient.date_naissance,created_at:'2026-01-01'
     }
   })
 }));
 await page.route('**/api/patients/**',async route=>{
   if(route.request().method()==='POST'){
     duplicateCreateCalls+=1;
     return route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({detail:'unexpected create'})});
   }
   return route.continue();
 });
 await page.locator('input[name="numero_dossier"]').fill('G2-DUP-OPEN');
 await page.locator('input[name="date_naissance"]').fill('1990-01-01');
 await page.locator('select[name="sexe"]').selectOption('F');
 await page.getByRole('button',{name:'Créer le dossier',exact:true}).click();
 await page.getByText('Patient similaire trouvé',{exact:true}).waitFor({state:'visible',timeout:10000});
 if(duplicateCreateCalls!==0) throw new Error('duplicate detection created before explicit choice');
 await page.getByRole('button',{name:/Ouvrir le dossier existant/i}).click();
 await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'),{timeout:10000});
 if(duplicateCreateCalls!==0) throw new Error('open existing duplicate triggered create');
 pass(viewport,'patient-duplicate-open-existing-non-mutation');
 await page.unroute('**/api/patients/**');
 await page.unroute('**/api/patients/check-duplicate*');

 // Explicit force-create is the only duplicate path allowed to mutate.
 await page.goto('http://127.0.0.1:5173/patients/new?nom=FORCE&prenom=Case',{waitUntil:'networkidle',timeout:90000});
 await page.route('**/api/patients/check-duplicate*',route=>route.fulfill({
   status:200,contentType:'application/json',body:JSON.stringify({
     has_duplicate:true,
     existing_patient:{id:patient.id,nom:patient.nom,prenom:patient.prenom,date_naissance:patient.date_naissance,created_at:'2026-01-01'}
   })
 }));
 const forceCreatedId=9199;
 let forceCreateCalls=0;
 await page.route('**/api/patients/?force_create=true',async route=>{
   if(route.request().method()==='POST'){
     forceCreateCalls+=1;
     const body=route.request().postDataJSON();
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:forceCreatedId,...body})});
   }
   return route.continue();
 });
 await page.route('**/api/patients/'+forceCreatedId,async route=>{
   if(route.request().method()==='GET'){
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
       id:forceCreatedId,numero_dossier:'G2-DUP-FORCE',nom:'FORCE',prenom:'Case',
       date_naissance:'1990-01-01',sexe:'F',telephone:'',assurance:'AUCUNE',is_ortho_active:false
     })});
   }
   return route.continue();
 });
 await page.locator('input[name="numero_dossier"]').fill('G2-DUP-FORCE');
 await page.locator('input[name="date_naissance"]').fill('1990-01-01');
 await page.locator('select[name="sexe"]').selectOption('F');
 await page.getByRole('button',{name:'Créer le dossier',exact:true}).click();
 await page.getByText('Patient similaire trouvé',{exact:true}).waitFor({state:'visible',timeout:10000});
 if(forceCreateCalls!==0) throw new Error('force-create mutated before explicit confirmation');
 await page.getByRole('button',{name:/Créer quand même/i}).click();
 await page.waitForURL(new RegExp('/patients/'+forceCreatedId+'(?:\\?|$)'),{timeout:10000});
 if(forceCreateCalls!==1) throw new Error('explicit force-create ACK mismatch');
 pass(viewport,'patient-duplicate-explicit-force-create',{forceCreateCalls});
 await page.unroute('**/api/patients/'+forceCreatedId);
 await page.unroute('**/api/patients/?force_create=true');
 await page.unroute('**/api/patients/check-duplicate*');

 // Cancel from create form is navigation-only and must not call create.
 await page.goto('http://127.0.0.1:5173/patients/new',{waitUntil:'networkidle',timeout:90000});
 let cancelCreateCalls=0;
 await page.route('**/api/patients/**',async route=>{
   if(route.request().method()==='POST') cancelCreateCalls+=1;
   return route.continue();
 });
 await page.getByRole('button',{name:'Annuler',exact:true}).click();
 await page.waitForURL('**/patients',{timeout:10000});
 if(cancelCreateCalls!==0) throw new Error('patient create cancel triggered mutation');
 pass(viewport,'patient-create-cancel-non-mutation');
 await page.unroute('**/api/patients/**');

 let editReadCalls=0;
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='GET'){
     editReadCalls+=1;
     if(editReadCalls===1) return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced edit read failure'})});
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(patient)});
   }
   return route.continue();
 });
 await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'/edit',{waitUntil:'networkidle',timeout:90000});
 await page.getByText('Impossible de charger le patient',{exact:true}).waitFor({state:'visible',timeout:10000});
 if(await page.locator('form').count()) throw new Error('edit form exposed defaults after read failure');
 await page.getByRole('button',{name:/Réessayer/i}).click();
 await page.getByDisplayValue(patient.nom,{exact:true}).waitFor({state:'visible',timeout:10000});
 if(editReadCalls!==2) throw new Error('edit read retry count mismatch');
 pass(viewport,'patient-edit-read-failure-retry',{editReadCalls});
 await page.unroute('**/api/patients/'+patient.id);
 const editNameLabel=page.locator('label').filter({hasText:/^Nom$/}).first();
 const editNameInput=editNameLabel.locator('..').locator('input').first();
 await editNameInput.waitFor({state:'visible',timeout:10000});
 const originalName=await editNameInput.inputValue();

 let conflictEditCalls=0;
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='PUT'){
     conflictEditCalls+=1;
     return route.fulfill({
       status:409,
       contentType:'application/json',
       body:JSON.stringify({detail:{message:'Conflit avec un patient existant.'}})
     });
   }
   return route.continue();
 });
 let conflictDialog='';
 page.once('dialog',async dialog=>{ conflictDialog=dialog.message(); await dialog.accept(); });
 await editNameInput.fill('G2 CONFLICT');
 await page.getByRole('button',{name:/Valider les modifications/i}).click();
 await page.waitForTimeout(200);
 if(conflictEditCalls!==1 || !/Conflit avec un patient existant/i.test(conflictDialog)) throw new Error('patient edit 409 conflict not surfaced');
 if(!page.url().includes('/edit')) throw new Error('patient edit conflict navigated away');
 pass(viewport,'patient-edit-conflict-non-navigation',{conflictEditCalls});
 await page.unroute('**/api/patients/'+patient.id);

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

 let dossierReadCalls=0;
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='GET'){
     dossierReadCalls+=1;
     if(dossierReadCalls===1) return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced dossier read failure'})});
     return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(patient)});
   }
   return route.continue();
 });
 await page.goto('http://127.0.0.1:5173/patients/'+patient.id,{waitUntil:'networkidle',timeout:90000});
 await page.getByText('Impossible de charger le dossier',{exact:true}).waitFor({state:'visible',timeout:10000});
 await page.getByRole('button',{name:/Réessayer/i}).click();
 await page.locator('main[data-flow-patient-surface]').waitFor({state:'visible',timeout:10000});
 if(dossierReadCalls!==2) throw new Error('patient dossier retry count mismatch');
 pass(viewport,'patient-dossier-read-failure-retry',{dossierReadCalls});
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

 // Patient List sort + keyboard activation on a deterministic browser-only list.
 const sortPatients=[
   {...patient,id:9101,numero_dossier:'G2-ZETA',nom:'ZETA',prenom:'Zoé'},
   {...patient,id:9102,numero_dossier:'G2-ALPHA',nom:'ALPHA',prenom:'Alice'},
   patient
 ];
 await page.route('**/api/patients/',async route=>{
   if(route.request().method()==='GET') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(sortPatients)});
   return route.continue();
 });
 await page.reload({waitUntil:'networkidle',timeout:90000});
 const sortSelect=page.locator('select').filter({hasText:'Plus Récents'}).first();
 await sortSelect.selectOption('az');
 let firstName=await page.locator('tbody tr').first().locator('td').nth(1).innerText();
 if(!firstName.toUpperCase().includes('ALPHA')) throw new Error('patient A-Z sort consumer mismatch: '+firstName);
 await sortSelect.selectOption('za');
 firstName=await page.locator('tbody tr').first().locator('td').nth(1).innerText();
 if(!firstName.toUpperCase().includes('ZETA')) throw new Error('patient Z-A sort consumer mismatch: '+firstName);
 pass(viewport,'patient-list-sort-consumer');

 const keyboardSearch=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
 await keyboardSearch.fill('T2-0001');
 const keyboardRow=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first();
 await keyboardRow.focus();
 await keyboardRow.press('Enter');
 await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'),{timeout:10000});
 pass(viewport,'patient-list-keyboard-navigation');
 await page.goBack({waitUntil:'networkidle'});

 // CSV import: successful multipart result and refusal with modal retained.
 await page.getByRole('button',{name:/Import CSV/i}).click();
 const csvDialog=page.getByRole('dialog').filter({hasText:'Importer des patients'});
 const csvFile=csvDialog.locator('input[type="file"]');
 const csvImport=csvDialog.getByRole('button',{name:'Importer',exact:true});
 if(!(await csvImport.isDisabled())) throw new Error('CSV import enabled without file');
 await csvFile.setInputFiles({name:'patients.csv',mimeType:'text/csv',buffer:Buffer.from('nom,prenom,date_naissance\nTEST,CSV,1990-01-01')});
 let csvCalls=0;
 await page.route('**/api/patients/import-csv',async route=>{
   csvCalls+=1;
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
     created:1,skipped_duplicates:1,errors:[{row:3,reason:'ligne invalide'}]
   })});
 });
 await csvImport.click();
 await csvDialog.getByText('1',{exact:true}).first().waitFor({state:'visible',timeout:10000});
 if(csvCalls!==1) throw new Error('CSV import ACK count mismatch');
 await csvDialog.getByText('ligne invalide',{exact:true}).waitFor({state:'visible',timeout:5000});
 pass(viewport,'patient-csv-import-result',{csvCalls});
 await csvDialog.getByRole('button',{name:'Fermer',exact:true}).click();
 await page.unroute('**/api/patients/import-csv');

 await page.getByRole('button',{name:/Import CSV/i}).click();
 const csvDialogRefusal=page.getByRole('dialog').filter({hasText:'Importer des patients'});
 const csvFileRefusal=csvDialogRefusal.locator('input[type="file"]');
 await csvFileRefusal.setInputFiles({name:'bad.csv',mimeType:'text/csv',buffer:Buffer.from('bad')});
 let csvRefusalCalls=0;
 await page.route('**/api/patients/import-csv',async route=>{
   csvRefusalCalls+=1;
   return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced CSV refusal'})});
 });
 await csvDialogRefusal.getByRole('button',{name:'Importer',exact:true}).click();
 await page.getByText('forced CSV refusal',{exact:true}).waitFor({state:'visible',timeout:10000});
 if(csvRefusalCalls!==1 || !(await csvDialogRefusal.isVisible())) throw new Error('CSV refusal contract mismatch');
 pass(viewport,'patient-csv-import-refusal-non-close',{csvRefusalCalls});
 await csvDialogRefusal.getByRole('button',{name:'Annuler',exact:true}).click();
 await page.unroute('**/api/patients/import-csv');

 await deleteSearch.fill('T2-0001');
 let deleteRow=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first();
 await deleteRow.waitFor({state:'visible',timeout:10000});

 // Wrong confirmation is blocked; cancel closes without mutation.
 let deleteButton=deleteRow.getByRole('button',{name:'Supprimer définitivement'});
 await deleteButton.click();
 let confirmInput=page.getByPlaceholder('T2 CERTIFICATION');
 await confirmInput.fill('WRONG');
 let confirm=page.getByRole('button',{name:'Supprimer',exact:true});
 if(!(await confirm.isDisabled())) throw new Error('patient delete enabled with wrong confirmation text');
 await page.getByRole('button',{name:'Annuler',exact:true}).click();
 await page.getByRole('dialog',{name:'Supprimer le dossier'}).waitFor({state:'detached',timeout:5000});
 if(!(await page.getByText(/CERTIFICATION\s+T2/i).count())) throw new Error('patient disappeared after delete cancel');
 pass(viewport,'patient-delete-wrong-confirm-and-cancel');

 // Backend refusal must preserve the row.
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='DELETE') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced delete refusal"}'});
   return route.continue();
 });
 deleteRow=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first();
 await deleteRow.getByRole('button',{name:'Supprimer définitivement'}).click();
 confirmInput=page.getByPlaceholder('T2 CERTIFICATION');
 await confirmInput.fill('T2 CERTIFICATION');
 confirm=page.getByRole('button',{name:'Supprimer',exact:true});
 await confirm.click();
 await page.waitForTimeout(300);
 if(!(await page.getByText(/CERTIFICATION\s+T2/i).count())) throw new Error('patient disappeared after refused delete');
 pass(viewport,'patient-delete-refusal-non-mutation');
 await page.unroute('**/api/patients/'+patient.id);

 // ACK removes from client/cache; hard reload proves real backend fixture was never mutated.
 let deleteAckCalls=0;
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='DELETE'){
     deleteAckCalls+=1;
     return route.fulfill({status:200,contentType:'application/json',body:'{}'});
   }
   return route.continue();
 });
 deleteButton=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first().getByRole('button',{name:'Supprimer définitivement'});
 await deleteButton.click();
 confirmInput=page.getByPlaceholder('T2 CERTIFICATION');
 await confirmInput.fill('T2 CERTIFICATION');
 await page.getByRole('button',{name:'Supprimer',exact:true}).click();
 await page.getByText(/CERTIFICATION\s+T2/i).waitFor({state:'detached',timeout:10000});
 if(deleteAckCalls!==1) throw new Error('patient delete ACK count mismatch');
 pass(viewport,'patient-delete-ack-local-removal',{deleteAckCalls});
 await page.unroute('**/api/patients/'+patient.id);

 await page.reload({waitUntil:'networkidle',timeout:90000});
 await page.getByPlaceholder('Rechercher par nom, prénom ou dossier...').fill('T2-0001');
 await page.getByText(/CERTIFICATION\s+T2/i).first().waitFor({state:'visible',timeout:10000});
 pass(viewport,'patient-delete-fixture-real-data-untouched');
 await page.unroute('**/api/patients/');
 await page.unroute('**/api/appointments/**');
 await page.unroute('**/api/intelligence/alerts/**');
 await page.unroute('**/api/mobile/bridge-options');
 await page.unroute('**/api/mobile/bridge-pairing');
 await page.unroute('**/api/admin/revoke-mobile');
 await ctx.close();

 // Restricted employee session — prove UI permission boundaries and direct-route fail-closed behavior.
 const restrictedCtx=await browser.newContext({viewport,colorScheme:'light'});
 const restrictedPage=await restrictedCtx.newPage();
 await restrictedPage.addInitScript(v=>{
   localStorage.setItem('token',v.access);
   localStorage.setItem('refresh_token',v.refresh||'');
   localStorage.setItem('appMode','prod');
 },{access:restrictedTokens.access_token,refresh:restrictedTokens.refresh_token});
 await restrictedPage.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
 await restrictedPage.getByText(/Bonjour, T2 Restricted Secretary/i).waitFor({state:'visible',timeout:10000});

 if(await restrictedPage.getByRole('button',{name:'Chercher un patient'}).count()) throw new Error('restricted user sees patient search');
 if(await restrictedPage.getByRole('button',{name:'Appairer le téléphone mobile'}).count()) throw new Error('restricted user sees mobile admin control');
 if(await restrictedPage.getByRole('button',{name:/Pilotage du cabinet/i}).count()) throw new Error('restricted user sees accounting management panel');
 if(await restrictedPage.getByRole('link',{name:'Patients',exact:true}).count()) throw new Error('restricted user sees Patients navigation');
 if(await restrictedPage.getByTitle('Réglages').count()) throw new Error('restricted user sees Settings entry');
 pass(viewport,'dashboard-restricted-hidden-controls');

 const restrictedQuick=restrictedPage.getByRole('button',{name:'Ajout rapide'});
 await restrictedQuick.click();
 if(await restrictedPage.getByRole('menuitem',{name:/Nouveau Patient/i}).count()) throw new Error('restricted user sees New Patient quick action');
 await restrictedPage.getByRole('menuitem',{name:/Nouveau RDV/i}).waitFor({state:'visible',timeout:5000});
 pass(viewport,'dashboard-restricted-agenda-only-quick-action');

 await restrictedPage.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
 await restrictedPage.waitForURL('**/dashboard',{timeout:10000});
 if(await restrictedPage.getByRole('button',{name:/Import CSV/i}).count()) throw new Error('restricted direct patients route exposed patient controls');
 pass(viewport,'patients-direct-route-permission-guard');

 await restrictedPage.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
 await restrictedPage.waitForURL('**/dashboard',{timeout:10000});
 if(await restrictedPage.getByText(/Performance & Assistance|Mon Équipe|Sécurité & Backup/i).count()) throw new Error('restricted direct settings route exposed settings controls');
 pass(viewport,'settings-direct-route-permission-guard');

 await restrictedPage.goto('http://127.0.0.1:5173/accounting',{waitUntil:'networkidle',timeout:90000});
 await restrictedPage.waitForURL('**/dashboard',{timeout:10000});
 pass(viewport,'accounting-direct-route-permission-guard');

 await restrictedPage.goto('http://127.0.0.1:5173/approvisionnement',{waitUntil:'networkidle',timeout:90000});
 await restrictedPage.waitForURL('**/dashboard',{timeout:10000});
 pass(viewport,'procurement-direct-route-permission-guard');

 await restrictedPage.goto('http://127.0.0.1:5173/super-admin',{waitUntil:'networkidle',timeout:90000});
 await restrictedPage.waitForURL('**/dashboard',{timeout:10000});
 if(await restrictedPage.getByText(/Gestion Globale des Licences/i).count()) throw new Error('restricted direct super-admin route exposed privileged UI');
 pass(viewport,'superadmin-direct-route-permission-guard');

 await restrictedPage.goto('http://127.0.0.1:5173/agenda',{waitUntil:'networkidle',timeout:90000});
 await restrictedPage.waitForURL('**/agenda',{timeout:10000});
 proveAgenda: {
   const url=new URL(restrictedPage.url());
   if(url.pathname!=='/agenda') throw new Error('agenda permission positive path failed');
 }
 pass(viewport,'agenda-positive-permission-route');

 await restrictedPage.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
 const restrictedAttention=restrictedPage.getByRole('button',{name:'Ouvrir le centre d’attention',exact:true});
 if(await restrictedAttention.count()){
   await restrictedAttention.click();
   if(await restrictedPage.getByRole('link',{name:'Trésorerie',exact:true}).count()) throw new Error('restricted user sees treasury shortcut');
   pass(viewport,'dashboard-restricted-treasury-shortcut-hidden');
 }
 await restrictedCtx.close();
}

await browser.close();
await api.dispose();
console.log('G2_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
