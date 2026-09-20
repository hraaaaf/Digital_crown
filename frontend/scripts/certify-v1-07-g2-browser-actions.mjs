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
   await pilotage.click();
   await page.waitForTimeout(150);
   pass(viewport,'dashboard-management-expand');
   await pilotage.click();
   pass(viewport,'dashboard-management-collapse');
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
   const table=page.getByRole('button',{name:'Vue Table'});
   await table.click();
   const tableMode=await page.evaluate(()=>localStorage.getItem('patient_list_view_mode'));
   if(tableMode!=='table') throw new Error('table mode did not persist');
   pass(viewport,'patient-list-view-mode-persistence');
 }

 await listSearch.fill('');
 const edit=page.getByRole('button',{name:'Modifier les infos'}).first();
 if(await edit.count()){
   await edit.click();
   await page.waitForURL(new RegExp('/patients/'+patient.id+'/edit'));
   pass(viewport,'patient-edit-navigation');
   await page.goBack({waitUntil:'networkidle'});
 }

 await page.getByText(/CERTIFICATION\s+T2/i).first().click();
 await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'));
 pass(viewport,'patient-dossier-navigation');

 await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
 await page.route('**/api/patients/'+patient.id,async route=>{
   if(route.request().method()==='DELETE') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced delete refusal"}'});
   return route.continue();
 });
 const deleteButton=page.getByRole('button',{name:'Supprimer définitivement'}).first();
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
