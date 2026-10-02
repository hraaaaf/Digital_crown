import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('targeted login failed '+login.status());
const tokens=await login.json();
const headers={Authorization:'Bearer '+tokens.access_token};
const patients=await api.get('/api/patients',{headers});
if(!patients.ok()) throw new Error('patients read failed '+patients.status());
const body=await patients.json();
const list=Array.isArray(body)?body:(body.items||body.patients||[]);
const patient=list.find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('T2 patient missing');

const browser=await chromium.launch({headless:true});
const ctx=await browser.newContext({viewport:{width:1280,height:900},colorScheme:'light'});
const page=await ctx.newPage();
await page.addInitScript(v=>{
  localStorage.setItem('token',v.access);
  localStorage.setItem('refresh_token',v.refresh||'');
  localStorage.setItem('appMode','prod');
},{access:tokens.access_token,refresh:tokens.refresh_token});

const sortPatients=[
  {...patient,id:9101,numero_dossier:'G2-ZETA',nom:'ZETA',prenom:'Zoé'},
  {...patient,id:9102,numero_dossier:'G2-ALPHA',nom:'ALPHA',prenom:'Alice'},
  patient
];
await page.route('**/api/patients/',async route=>{
  if(route.request().method()==='GET') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(sortPatients)});
  return route.continue();
});

await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
const sortSelect=page.locator('select').filter({hasText:'Plus Récents'}).first();
await sortSelect.selectOption('az');
let firstName=await page.locator('tbody tr').first().locator('td').nth(0).innerText();
if(!firstName.toUpperCase().includes('ALPHA')) throw new Error('patient A-Z sort consumer mismatch: '+firstName);
await sortSelect.selectOption('za');
firstName=await page.locator('tbody tr').first().locator('td').nth(0).innerText();
if(!firstName.toUpperCase().includes('ZETA')) throw new Error('patient Z-A sort consumer mismatch: '+firstName);

const keyboardSearch=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
await keyboardSearch.fill('T2-0001');
const keyboardRow=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first();
await keyboardRow.focus();
await keyboardRow.press('Enter');
await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'),{timeout:10000});
await page.goBack({waitUntil:'networkidle'});

await page.getByRole('button',{name:/Import CSV/i}).click();
const csvDialog=page.getByRole('dialog').filter({hasText:'Importer des patients'});
const csvFile=csvDialog.locator('input[type="file"]');
const csvImport=csvDialog.getByRole('button',{name:'Importer',exact:true});
if(!(await csvImport.isDisabled())) throw new Error('CSV import enabled without file');
await csvFile.setInputFiles({name:'patients.csv',mimeType:'text/csv',buffer:Buffer.from('nom,prenom,date_naissance\nTEST,CSV,1990-01-01')});
let csvCalls=0;
await page.route('**/api/patients/import-csv',async route=>{
  csvCalls+=1;
  return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({created:1,skipped_duplicates:1,errors:[{row:3,reason:'ligne invalide'}]})});
});
await csvImport.click();
await csvDialog.getByText(/ligne invalide/i).waitFor({state:'visible',timeout:10000});
if(csvCalls!==1) throw new Error('CSV import ACK count mismatch');
await csvDialog.getByRole('button',{name:'Fermer',exact:true}).click();
await page.unroute('**/api/patients/import-csv');

await page.getByRole('button',{name:/Import CSV/i}).click();
const csvDialogRefusal=page.getByRole('dialog').filter({hasText:'Importer des patients'});
await csvDialogRefusal.locator('input[type="file"]').setInputFiles({name:'bad.csv',mimeType:'text/csv',buffer:Buffer.from('bad')});
let csvRefusalCalls=0;
await page.route('**/api/patients/import-csv',async route=>{
  csvRefusalCalls+=1;
  return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced CSV refusal'})});
});
await csvDialogRefusal.getByRole('button',{name:'Importer',exact:true}).click();
await page.getByText('forced CSV refusal',{exact:true}).waitFor({state:'visible',timeout:10000});
if(csvRefusalCalls!==1 || !(await csvDialogRefusal.isVisible())) throw new Error('CSV refusal contract mismatch');
await csvDialogRefusal.getByRole('button',{name:'Annuler',exact:true}).click();
await page.unroute('**/api/patients/import-csv');

const deleteSearch=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
await deleteSearch.fill('T2-0001');
let deleteRow=page.locator('tbody tr').filter({hasText:/CERTIFICATION\s+T2/i}).first();
await deleteRow.waitFor({state:'visible',timeout:10000});
let deleteButton=deleteRow.getByRole('button',{name:'Supprimer définitivement'});
await deleteButton.click();
let confirmInput=page.getByPlaceholder('T2 CERTIFICATION');
await confirmInput.fill('WRONG');
let confirm=page.getByRole('button',{name:'Supprimer',exact:true});
if(!(await confirm.isDisabled())) throw new Error('patient delete enabled with wrong confirmation text');
await page.getByRole('button',{name:'Annuler',exact:true}).click();
await page.getByRole('dialog',{name:'Supprimer le dossier'}).waitFor({state:'detached',timeout:5000});
if(!(await page.getByText(/CERTIFICATION\s+T2/i).count())) throw new Error('patient disappeared after delete cancel');

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
if(!(await page.getByRole('dialog',{name:'Supprimer le dossier'}).isVisible())) throw new Error('patient delete refusal closed confirmation modal');
await page.getByRole('button',{name:'Annuler',exact:true}).click();
await page.unroute('**/api/patients/'+patient.id);

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
await page.unroute('**/api/patients/'+patient.id);

await page.reload({waitUntil:'networkidle',timeout:90000});
await page.getByPlaceholder('Rechercher par nom, prénom ou dossier...').fill('T2-0001');
await page.getByText(/CERTIFICATION\s+T2/i).first().waitFor({state:'visible',timeout:10000});

console.log(JSON.stringify({status:'PASS',scenario:'g2-patient-list-csv-delete-targeted',csvCalls,csvRefusalCalls,deleteAckCalls,patientId:patient.id}));
await ctx.close();
await browser.close();
await api.dispose();
