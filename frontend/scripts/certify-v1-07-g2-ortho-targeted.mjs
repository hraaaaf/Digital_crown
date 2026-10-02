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

await page.route('**/api/patients/'+patient.id,async route=>{
  if(route.request().method()==='GET') return route.fulfill({
    status:200,
    contentType:'application/json',
    body:JSON.stringify({...patient,dossier:{...(patient.dossier||{}),is_ortho_active:false}})
  });
  return route.continue();
});

let patchCalls=0;
let failNext=true;
await page.route('**/api/patients/'+patient.id+'/ortho',async route=>{
  if(route.request().method()==='PATCH'){
    patchCalls+=1;
    if(failNext){
      failNext=false;
      return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced ortho refusal'})});
    }
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({is_ortho_active:true})});
  }
  return route.continue();
});

await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'?tab=radiology&radioTab=cephalo',{waitUntil:'networkidle',timeout:90000});
const activate=page.getByRole('button',{name:/Activer le Suivi Orthodontique/i});
await activate.waitFor({state:'visible',timeout:10000});
await page.getByText('Module Céphalométrique Verrouillé',{exact:true}).waitFor({state:'visible',timeout:10000});

const refused=page.waitForResponse(res=>new URL(res.url()).pathname==='/api/patients/'+patient.id+'/ortho'&&res.request().method()==='PATCH'&&res.status()===503);
await activate.click();
await refused;
await page.getByText('Module Céphalométrique Verrouillé',{exact:true}).waitFor({state:'visible',timeout:10000});

const accepted=page.waitForResponse(res=>new URL(res.url()).pathname==='/api/patients/'+patient.id+'/ortho'&&res.request().method()==='PATCH'&&res.status()===200);
await activate.click();
await accepted;
await page.waitForFunction(()=>!document.body.innerText.includes('Module Céphalométrique Verrouillé'),undefined,{timeout:10000});
if(patchCalls!==2) throw new Error('ortho patch count mismatch '+patchCalls);

console.log(JSON.stringify({status:'PASS',scenario:'g2-ortho-cephalo-targeted',patchCalls,patientId:patient.id}));
await ctx.close();
await browser.close();
await api.dispose();
