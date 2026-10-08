import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

// V1.5-00.2: PR #783 adaptive laboratory applied to the Hub, not FUE-A.
const root = path.resolve('artifacts/fue-v15-00-2');
await fs.mkdir(root,{recursive:true});
const browser = await chromium.launch({headless:true});
const results=[];
const baseFailures=[];
const bootstrap={workstationId:null,defaultExperience:null,stationLocked:false,stationEscapeAuthorized:false,stationEscapeExpiresAt:null,enrollmentRequired:false,authenticated:false,pinConfigured:false,canManage:false,canConfigurePin:false};
for(const vp of [{name:'tablet',width:768,height:1024},{name:'desktop',width:1280,height:900}]){
 const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
 await context.route('**/api/workstation/bootstrap',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(bootstrap)}));
 await context.route('**/api/clinics/me',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({nom_cabinet:'Cabinet FUE synthétique',cabinet_type:'CABINET'})}));
 // The browser harness has no backend. Make /health deterministic so the product\'s\n // 15 x 2s readiness retry does not outlive the authorization assertion.\n await context.route('**/health',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({status:'ok'})}));\n await context.route('**/auth/me',r=>r.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:'Unauthenticated'})}));\n const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const started=Date.now();
 try {
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.locator('[data-hub-experience]').first().waitFor({state:'visible'});
 const cards=await page.locator('[data-hub-experience]').count();
 if(cards!==3)throw new Error('Hub must display exactly three destinations, observed '+cards);
 await page.screenshot({path:path.join(root,vp.name+'-01-hub.png'),fullPage:true});
 const hubMs=Date.now()-started;
 await page.locator('[data-hub-experience="control"]').click();
 await page.waitForURL('**/control-center',{timeout:15000});
 await page.locator('[data-workstation-experience="control-center"]').waitFor({state:'visible',timeout:15000}).catch(async()=>{await page.getByText('Centre de contrôle').first().waitFor({state:'visible',timeout:5000})});
 await page.screenshot({path:path.join(root,vp.name+'-02-control.png'),fullPage:true});
 const firstValueMs=Date.now()-started;
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.locator('[data-hub-experience="station"]').click();
 await page.waitForURL('**/hub?select=1',{timeout:15000}); // unpaired station must not be entered
 await page.screenshot({path:path.join(root,vp.name+'-03-station-refusal.png'),fullPage:true});
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.locator('[data-hub-experience="cabinet"]').click();
 // Prove the negative authorization outcome, not merely absence of /dashboard.
 await page.waitForURL('**/login', { timeout: 15000 });
 const cabinetUrl=new URL(page.url()).pathname;
 if(cabinetUrl !== '/login') throw new Error('Expected login after anonymous Cabinet selection, got '+cabinetUrl);
 await page.getByRole('textbox').first().waitFor({state:'visible',timeout:10000});
 // Direct URL must enforce the same boundary, preventing a false-green SPA route.
 await page.goto('http://127.0.0.1:4195/dashboard');
 await page.waitForURL('**/login', {timeout:15000});
 if(new URL(page.url()).pathname !== '/login') throw new Error('Direct Dashboard URL bypassed auth');
 await page.goto('http://127.0.0.1:4195/login');
 await page.screenshot({path:path.join(root,vp.name+'-04-cabinet-auth-boundary.png'),fullPage:true});
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.route('**/api/clinics/me',r=>r.abort());
 await page.reload();
 await page.locator('[data-hub-offline]').waitFor({state:'visible',timeout:12000});
 await page.screenshot({path:path.join(root,vp.name+'-05-offline.png'),fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1);
 if(overflow||errors.length)throw new Error(JSON.stringify({overflow,errors}));
 results.push({viewport:vp.name,dimensions:[vp.width,vp.height],cards,hubMs,firstValueMs,stationUnpairedRejected:true,cabinetUrl,anonymousCabinetRejected:true,directDashboardRejected:true,offlineMessage:true,overflow,pageErrors:errors});
 } catch(error) {
  baseFailures.push({viewport:vp.name,error:String(error),lastUrl:page.url()});
  await page.screenshot({path:path.join(root,vp.name+'-FAIL.png'),fullPage:true}).catch(()=>{});
 } finally { await context.close(); }
}

const cases = [];
async function scenario(name, viewport, overrides, perform) {
  const context = await browser.newContext({viewport});
  const state = {...bootstrap,...overrides};
  await context.route('**/api/workstation/bootstrap', route => route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(state)}));
  await context.route('**/api/clinics/me', route => route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({nom_cabinet:'Cabinet FUE synthétique',cabinet_type:'CABINET'})}));
  await context.route('**/health',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({status:'ok'})}));
  await context.route('**/auth/me',r=>r.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:'Unauthenticated'})}));
  const page = await context.newPage();
  const findings=[];
  page.on('pageerror',error=>findings.push(error.message));
  const capture=async label => {
    await page.screenshot({path:path.join(root, name+'-'+label+'.png'),fullPage:true});
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
    if(overflow)throw Error(name+': horizontal overflow at '+label);
  };
  try {
    await perform(page,capture,state);
    if(findings.length)throw Error(name+': '+JSON.stringify(findings));
    cases.push({name,status:'PASS',pageErrors:findings});
  } catch(error){
    cases.push({name,status:'FAIL',error:String(error)});
    await page.screenshot({path:path.join(root,name+'-FAIL.png'),fullPage:true}).catch(()=>{});
  } finally {await context.close();}
}
for(const vp of [{name:'tablet',width:768,height:1024},{name:'desktop',width:1280,height:900}]){
 const viewport={width:vp.width,height:vp.height};
 await scenario(vp.name+'-station-locked',viewport,{defaultExperience:'station',stationLocked:true,workstationId:'synthetic-1'},async(page,capture)=>{
   await page.goto('http://127.0.0.1:4195/station');
   await page.locator('[data-station-admin]').count(); // optional locked shell, proof is URL
   await capture('01-station');
   await page.goto('http://127.0.0.1:4195/hub?select=1');
   await page.waitForURL('**/station',{timeout:15000});
   await capture('02-hub-blocked');
   await page.goto('http://127.0.0.1:4195/control-center');
   await page.waitForURL('**/station',{timeout:15000});
   await capture('03-control-blocked');
 });
 await scenario(vp.name+'-station-escape-authorized',viewport,{defaultExperience:'station',stationLocked:true,stationEscapeAuthorized:true,stationEscapeExpiresAt:Math.floor(Date.now()/1000)+120,workstationId:'synthetic-1'},async(page,capture)=>{
   await page.goto('http://127.0.0.1:4195/hub?select=1');
   await page.locator('[data-hub-experience]').first().waitFor({state:'visible'});
   await capture('01-authorized-hub');
   await page.locator('[data-hub-experience="control"]').click();
   await page.waitForURL('**/control-center',{timeout:15000});
   await page.locator('[data-workstation-experience="control-center"]').waitFor({state:'visible'});
   await capture('02-authorized-control');
 });
 await scenario(vp.name+'-enrollment-required',viewport,{enrollmentRequired:true},async(page,capture)=>{
   await page.goto('http://127.0.0.1:4195/control-center');
   await page.waitForURL('**/hub?enroll=1',{timeout:15000});
   await capture('01-enrollment');
 });
 await scenario(vp.name+'-bootstrap-failure',viewport,{},async(page,capture)=>{
   await page.route('**/api/workstation/bootstrap',route=>route.abort());
   await page.goto('http://127.0.0.1:4195/hub?select=1');
   await page.locator('[data-hub-experience]').first().waitFor({state:'visible'});
   await capture('01-recovery-hub');
   await page.goto('http://127.0.0.1:4195/dashboard');
   await page.waitForURL('**/login',{timeout:15000});
   await capture('02-protected-refusal');
 });
}
const mandatoryCases=8;
const summary={baseFailures,protocol:'PR #783 contextual FUE-I V1.5-00.2',head:process.env.GITHUB_SHA||'unknown',baseScenarios:results,extendedScenarios:cases,expectedExtended:mandatoryCases,passed:cases.filter(x=>x.status==='PASS').length,failed:cases.filter(x=>x.status==='FAIL').length,limitations:['Synthetic bootstrap mocks are not backend PIN verification','No real authenticated Cabinet session','No patient data or real cabinet runtime','Station PIN lifecycle/restart not proven'],complete:false};
summary.complete=cases.length===mandatoryCases && summary.failed===0 && results.length===2 && baseFailures.length===0;
await fs.writeFile(path.join(root,'certification-matrix.json'),JSON.stringify(summary,null,2));
await fs.writeFile(path.join(root,'report.json'),JSON.stringify({baseFailures,results,cases,complete:summary.complete},null,2));
await browser.close();
console.log(JSON.stringify({baseFailures,results,cases,complete:summary.complete},null,2));
if(!summary.complete)throw Error('FUE-I matrix failed: '+JSON.stringify({baseFailures,failures:cases.filter(x=>x.status==='FAIL')}));
