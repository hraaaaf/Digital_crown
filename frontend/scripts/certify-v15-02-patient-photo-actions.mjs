import { chromium, request } from 'playwright';

const user=process.env.T2_USER;
const password=process.env.T2_PASSWORD;
if(!user||!password) throw new Error('T2_USER/T2_PASSWORD required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:user,password}});
if(!login.ok()) throw new Error('photo actions login failed '+login.status());
const tokens=await login.json();
const headers={Authorization:'Bearer '+tokens.access_token};
const patients=await api.get('/api/patients/',{headers});
if(!patients.ok()) throw new Error('photo actions patients failed '+patients.status());
const rows=await patients.json();
const patient=rows.find(row=>row.numero_dossier==='T2-0001')||rows[0];
if(!patient) throw new Error('photo actions requires patient fixture');

const samplePng=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAASUlEQVR42u3PQQ0AIBDAsAP/nuGNAvZoFSzZOjNnyNi7dwfgUQIeJeBRAh4l4FECHiXgUQIeJeBRAh4l4FECHiXgUQIeJeBRAh4l4FHCB30Bf4Q3zAAAAABJRU5ErkJggg==','base64');

const browser=await chromium.launch({headless:true});
const ctx=await browser.newContext({viewport:{width:430,height:932},colorScheme:'light'});
const page=await ctx.newPage();
await page.addInitScript(v=>{
  localStorage.setItem('token',v.access);
  localStorage.setItem('refresh_token',v.refresh||'');
  localStorage.setItem('appMode','prod');
},{access:tokens.access_token,refresh:tokens.refresh_token});

let postCalls=0;
let deleteCalls=0;
let failNextPost=true;
await page.route('**/api/patients/'+patient.id+'/photo',async route=>{
  const method=route.request().method();
  if(method==='POST'){
    postCalls+=1;
    if(failNextPost){
      failNextPost=false;
      return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced photo upload refusal'})});
    }
    return route.fulfill({status:201,contentType:'application/json',body:JSON.stringify({photo_url:'/api/patients/'+patient.id+'/photo'})});
  }
  if(method==='GET'){
    return route.fulfill({status:200,contentType:'image/jpeg',body:samplePng});
  }
  if(method==='DELETE'){
    deleteCalls+=1;
    return route.fulfill({status:204,body:''});
  }
  return route.continue();
});

await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'/edit',{waitUntil:'networkidle',timeout:90000});
await page.getByRole('heading',{name:'Mise à jour',exact:true}).waitFor({state:'visible',timeout:30000});

await page.getByLabel('Importer une photo du patient').setInputFiles({
  name:'patient.png',
  mimeType:'image/png',
  buffer:samplePng
});
const dialog=page.getByRole('dialog',{name:'Recadrer la photo'});
await dialog.waitFor({state:'visible',timeout:30000});
await page.getByLabel('Zoom de la photo').fill('1.5');
await page.getByLabel('Position horizontale').fill('20');
await page.getByLabel('Position verticale').fill('-10');

const save=dialog.getByRole('button',{name:/Enregistrer la photo/i});
await save.click();
await page.getByRole('alert').filter({hasText:/n’a pas pu être enregistrée/i}).waitFor({state:'visible',timeout:10000});
if(!(await dialog.isVisible())) throw new Error('crop dialog closed after refused upload');
if(postCalls!==1) throw new Error('refused upload call count mismatch '+postCalls);

await save.click();
await dialog.waitFor({state:'detached',timeout:10000});
await page.getByRole('button',{name:/Supprimer/i}).waitFor({state:'visible',timeout:10000});
if(postCalls!==2) throw new Error('upload retry call count mismatch '+postCalls);

await page.getByRole('button',{name:/Supprimer/i}).click();
await page.getByRole('button',{name:/Supprimer/i}).waitFor({state:'detached',timeout:10000});
if(deleteCalls!==1) throw new Error('delete call count mismatch '+deleteCalls);

console.log(JSON.stringify({status:'PASS',scenario:'v15-02-photo-actions',postCalls,deleteCalls,patientId:patient.id}));
await ctx.close();
await browser.close();
await api.dispose();
