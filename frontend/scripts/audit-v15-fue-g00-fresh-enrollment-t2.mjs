// Genuine fresh-browser enrollment through product owner UI, NEVER API-injected.
// Runs after FUE-G00 integrated T2 creates legitimate workstations for this tenant.
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';
const head=process.env.EVALUATED_SHA, owner=process.env.T2_USER, password=process.env.T2_PASSWORD;
if(!/^[a-f0-9]{40}$/.test(head||'')||!owner||!password||
process.env.ENVIRONMENT!=='test'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1')
  throw Error('FUE-G00 fresh browser requires isolated T2 and exact SHA');
const url='http://127.0.0.1:5173', backend='http://127.0.0.1:8005';
const dir=path.resolve('../artifacts/v15-fue-g00-fresh');
await fs.mkdir(dir,{recursive:true});
const viewports=[{name:'tablet',width:768,height:1024},{name:'desktop',width:1280,height:900}];
const report={head,isolated:true,
  precondition:'existing workstation rows in disposable T2 tenant; NO workstation cookie in browser',
  exclusions:['physical first PC','first ever station in empty tenant','reboot and field LAN'],
  cases:[],failures:[],success:false};
const browser=await chromium.launch({headless:true});
try{
for(const v of viewports){
  const p={viewport:v.name,checks:{},images:[],pageErrors:[],http5xx:[],timingsMs:{}};
  let ctx,page;const begin=Date.now();
  try{
    ctx=await browser.newContext({viewport:{width:v.width,height:v.height},reducedMotion:'reduce'});
    page=await ctx.newPage();
    page.on('pageerror',e=>p.pageErrors.push(e.message));
    page.on('response',r=>{if(r.status()>=500)p.http5xx.push({status:r.status(),path:new URL(r.url()).pathname})});
    const ok=(key,value)=>{p.checks[key]=Boolean(value);if(!value)throw Error('FUE-G00 FAILED: '+key)};
    const img=async label=>{
      const [width,full]=await page.evaluate(()=>[document.documentElement.clientWidth,document.documentElement.scrollWidth]);
      if(full>width+1)throw Error('Overflow at '+label);
      const name=v.name+'-'+label+'.png';
      await page.screenshot({path:path.join(dir,name),fullPage:true,animations:'disabled'});
      p.images.push(name);
    };
    const goto=route=>page.goto(url+route,{waitUntil:'domcontentloaded',timeout:45000});
    const at=route=>page.waitForURL(u=>new URL(u).pathname===route,{timeout:35000});
    const uncookied=async()=>!(await ctx.cookies(backend)).some(x=>x.name==='dc_workstation');
    const gate=page.locator('[data-workstation-enrollment]');
    ok('browserInitiallyHasZeroCookies',(await ctx.cookies()).length===0);
    await goto('/hub?select=1');
    await page.locator('[data-hub-experience="cabinet"]').waitFor({state:'visible',timeout:30000});
    ok('threeHubCards',await page.locator('[data-hub-experience]').count()===3);
    ok('stationIdentityNotInjected',await uncookied());
    ok('noUserAuthInjected',await page.evaluate(()=>!localStorage.getItem('token')));
    p.timingsMs.hub=Date.now()-begin;
    await img('01-before-virgin-hub');

    await page.locator('[data-hub-experience="cabinet"]').click();
    await at('/login');
    await page.locator('input[type=email]').waitFor({state:'visible',timeout:30000});
    await page.waitForFunction(()=>{
      const el=document.querySelector('input[type=email]');
      const card=el?.closest('div.max-w-md');
      return !!card&&parseFloat(getComputedStyle(card).opacity)>=0.98;
    },null,{timeout:15000});
    ok('loginIsVisibleNotPreAuthenticated',true);
    await img('02-owner-login');
    await page.locator('input[type=email]').fill(owner);
    await page.locator('input[type=password]').fill(password);
    await page.getByRole('button',{name:'Se connecter',exact:true}).click();
    await page.waitForURL(u=>{
      const x=new URL(u);return x.pathname==='/hub'&&x.searchParams.get('enroll')==='1';
    },{timeout:60000});
    await gate.waitFor({state:'visible',timeout:30000});
    ok('loginRedirectsUnregisteredBrowserToEnrollment',true);
    ok('realLoginCreatedUserAuth',await page.evaluate(()=>!!localStorage.getItem('token')));
    ok('workstationStillHasNoCookie',await uncookied());
    p.timingsMs.prompt=Date.now()-begin;
    await img('03-enrollment-required');
    // Test API only for READ-ONLY fail-closed assertion; never perform enrollment via API.
    const deniedState=await page.evaluate(async backend=>{
      const jwt=localStorage.getItem('token');
      const r=await fetch(backend+'/api/workstation/state',{
        credentials:'include',headers:{Authorization:'Bearer '+jwt}});
      return r.status;
    },backend);
    ok('backendStateRefusesFreshBrowser423',deniedState===423);
    await goto('/dashboard');
    await page.waitForURL(u=>{
      const x=new URL(u);return x.pathname==='/hub'&&x.searchParams.get('enroll')==='1';
    },{timeout:35000});
    await gate.waitFor({state:'visible',timeout:30000});
    ok('clinicalDashboardRedirectsToEnrollment',true);

    await gate.locator('summary').filter({hasText:'Récupération propriétaire sans code'}).click();
    const input=gate.getByLabel('Mot de passe du compte propriétaire',{exact:true});
    await input.fill('INVALID-FIRST-USE-PASSWORD');
    const reject=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/workstation/enroll'&&
      r.request().method()==='POST',{timeout:30000});
    await gate.getByRole('button',{name:'Réenregistrer le poste'}).click();
    ok('wrongOwnerPassword403',(await reject).status()===403);
    ok('wrongPasswordNoStationIdentity',await uncookied());
    ok('wrongPasswordGateStillVisible',await gate.isVisible());
    await img('04-invalid-owner-password');

    await input.fill(password);
    const accept=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/workstation/enroll'&&
      r.request().method()==='POST',{timeout:30000});
    await gate.getByRole('button',{name:'Réenregistrer le poste'}).click();
    ok('realOwnerUiEnrollment200',(await accept).status()===200);
    await page.locator('[data-workstation-admin]').waitFor({state:'visible',timeout:30000});
    ok('stationCookieIssuedOnlyAfterOwnerUi',
      (await ctx.cookies(backend)).filter(c=>c.name==='dc_workstation').length===1);
    ok('enrollmentGateDisappeared',await gate.count()===0);
    await img('05-owner-authorized-enrollment');
    await goto('/dashboard');
    await at('/dashboard');
    await page.getByRole('button',{name:'Ajout rapide'}).waitFor({state:'visible',timeout:30000});
    ok('clinicalDashboardNowAccessible',true);
    p.timingsMs.clinical=Date.now()-begin;
    await img('06-dashboard-after-enrollment');
    await goto('/hub?select=1');
    await page.locator('[data-hub-experience="control"]').click();
    await at('/control-center');
    await page.locator('[data-control-center-topology]').waitFor({state:'visible',timeout:30000});
    ok('controlCenterAccessible',true);
    await img('07-control-center');
    await page.getByRole('button',{name:'Continuer vers le Hub'}).click();
    await at('/hub');
    await page.locator('[data-hub-experience="cabinet"]').waitFor({state:'visible',timeout:30000});
    ok('returnHubThroughRealButton',true);
    await img('08-hub-after-real-ui-enrollment');
    ok('eightBeforeAfterImages',p.images.length===8);
    if(p.pageErrors.length||p.http5xx.length)throw Error('Unexpected JS exception or HTTP5xx');
    report.cases.push(p);
  }catch(e){
    report.failures.push({viewport:v.name,reason:String(e).slice(0,650),
      checks:p.checks,images:p.images});
    if(page)await page.screenshot({path:path.join(dir,v.name+'-FAIL.png'),fullPage:true}).catch(()=>{});
  }finally{if(ctx)await ctx.close()}
}
}finally{await browser.close()}
report.success=report.failures.length===0&&report.cases.length===viewports.length&&
report.cases.every(p=>p.images.length===8&&Object.keys(p.checks).length===20&&
Object.values(p.checks).every(Boolean)&&!p.pageErrors.length&&!p.http5xx.length);
await fs.writeFile(path.join(dir,'report.json'),JSON.stringify(report,null,2));
console.log('FUE_G00_FRESH_ENROLLMENT_SUMMARY',JSON.stringify({
  head:report.head,success:report.success,
  profiles:report.cases.map(p=>({viewport:p.viewport,images:p.images.length,
    checks:p.checks,timingsMs:p.timingsMs})),failures:report.failures}));
if(!report.success)throw Error('FUE-G00 first-use enrollment failed closed');
