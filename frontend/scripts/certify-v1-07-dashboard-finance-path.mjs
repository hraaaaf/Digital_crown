import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir=path.resolve('../artifacts/t2-browser/dashboard-finance-path');
fs.mkdirSync(outDir,{recursive:true});
const user=process.env.T2_USER,password=process.env.T2_PASSWORD;
if(!user||!password) throw new Error('T2 credentials required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:user,password}});
if(!login.ok()) throw new Error('login failed');
const tokens=await login.json(),headers={Authorization:`Bearer ${tokens.access_token}`};
const patients=await api.get('/api/patients',{headers});
if(!patients.ok()) throw new Error('patients failed');
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('fixture patient missing');

const browser=await chromium.launch({headless:true});
const evidence=[];
for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
  const context=await browser.newContext({viewport,colorScheme:'light'});
  const page=await context.newPage();
  await page.addInitScript(({access,refresh})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('refresh_token',refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:tokens.access_token,refresh:tokens.refresh_token});

  const pageErrors=[],responses=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('response',r=>{
    if(r.status()>=400) responses.push({status:r.status(),method:r.request().method(),url:r.url()});
  });

  await page.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
  await page.getByRole('button',{name:'Chercher un patient',exact:true}).click();
  const search=page.getByRole('textbox',{name:'Chercher un patient',exact:true});
  await search.fill('T2-0001');
  const result=page.getByRole('button',{name:/CERTIFICATION T2/i}).first();
  await result.waitFor({state:'visible',timeout:30000});
  await result.click();
  await page.waitForURL(new RegExp('/patients/'+patient.id+'(?:\\?|$)'),{timeout:30000});
  const finances=page.getByRole('button',{name:'Finances',exact:true});
  await finances.waitFor({state:'visible',timeout:30000});
  await finances.click();

  let outcome='finance-visible';
  try{
    for(const label of ['Facturé','Encaissé','Reste dû','Prochaine échéance']){
      await page.getByText(label,{exact:true}).first().waitFor({state:'visible',timeout:15000});
    }
  }catch{
    outcome='finance-error-or-timeout';
  }

  const shot=`dashboard-to-finances-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({path:path.join(outDir,shot),fullPage:false,animations:'disabled'});
  evidence.push({viewport,outcome,url:page.url(),pageErrors,httpErrors:responses,shot});
  await context.close();
}
await browser.close();
await api.dispose();
const summary={status:evidence.every(x=>x.outcome==='finance-visible'&&x.pageErrors.length===0&&x.httpErrors.every(r=>r.status<500))?'PASS':'FAIL',evidence};
fs.writeFileSync(path.join(outDir,'summary.json'),JSON.stringify(summary,null,2));
console.log('DASHBOARD_FINANCE_PATH '+JSON.stringify(summary));
if(summary.status!=='PASS') process.exit(1);
