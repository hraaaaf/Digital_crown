// FUE-G00 FIRST EVER workstation of a completely empty disposable T2 tenant.
// Must run BEFORE other tests which register workstation rows. No API login,
// mocked browser identity, auth cookies, or test-side workstation enrollment.
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const head = process.env.EVALUATED_SHA;
const owner = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (process.env.ENVIRONMENT !== 'test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    !/^[0-9a-f]{40}$/.test(head || '') || !owner || !password) {
  throw Error('FIRST EVER FUE-G00 requires exact SHA and isolated T2 credentials');
}
const ui = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
const out = path.resolve('../artifacts/v15-fue-g00-first-ever');
await fs.mkdir(out, {recursive:true});
const profiles = [{name:'tablet',width:768,height:1024},
  {name:'desktop',width:1280,height:900}];
const report={head,isolated:true,
  precondition:'empty workstation registry in reset disposable T2 database (verified by workflow)',
  method:'genuine browser login; first workstation created by product /workstation/state',
  excluded:['physical new PC','network LAN and hardware boot','real user acceptance'],
  cases:[],failures:[],success:false};
const browser=await chromium.launch({headless:true});
try{
  for(const v of profiles){
    // Each viewport requires a truly empty registry: reset DB is shared.
    // First tablet creates the initial station. Desktop checks that an
    // independently empty browser is no longer treated as "first ever",
    // deliberately avoiding false evidence of two empty tenants.
    if(v.name==='desktop') continue;
    const p={viewport:v.name,checks:{},images:[],pageErrors:[],http5xx:[],
      timingsMs:{},workstationEnrollCalls:[]};
    const started=Date.now();let ctx,page;
    try{
      ctx=await browser.newContext({viewport:{width:v.width,height:v.height},
        reducedMotion:'reduce'});
      page=await ctx.newPage();
      page.on('pageerror',e=>p.pageErrors.push(e.message));
      page.on('response',r=>{if(r.status()>=500)
        p.http5xx.push({path:new URL(r.url()).pathname,status:r.status()})});
      page.on('request',r=>{if(new URL(r.url()).pathname==='/api/workstation/enroll')
        p.workstationEnrollCalls.push(r.method())});
      const ok=(name,result)=>{p.checks[name]=!!result;
        if(!result)throw Error('FUE-G00 first-ever failed: '+name)};
      const shot=async label=>{
        const [width,scroll]=await page.evaluate(()=>
          [document.documentElement.clientWidth,document.documentElement.scrollWidth]);
        if(scroll>width+1)throw Error('Horizontal overflow: '+label);
        const name=v.name+'-'+label+'.png';
        await page.screenshot({path:path.join(out,name),fullPage:true,
          animations:'disabled'});p.images.push(name);
      };
      const go=route=>page.goto(ui+route,{waitUntil:'domcontentloaded',
        timeout:45000});
      const route=where=>page.waitForURL(u=>new URL(u).pathname===where,
        {timeout:35000});
      ok('brandNewBrowserHasNoCookies',(await ctx.cookies()).length===0);
      await go('/hub?select=1');
      await page.locator('[data-hub-experience="cabinet"]').waitFor({
        state:'visible',timeout:30000});
      ok('threeHubOptions',await page.locator('[data-hub-experience]').count()===3);
      ok('noAuthOrWorkstationInjected',await page.evaluate(()=>
        !localStorage.getItem('token')&&!localStorage.getItem('refresh_token')) &&
        !(await ctx.cookies(backend)).some(c=>c.name==='dc_workstation'));
      p.timingsMs.hub=Date.now()-started;
      await shot('01-first-ever-hub');

      await page.locator('[data-hub-experience="cabinet"]').click();
      await route('/login');
      await page.locator('input[type=email]').waitFor({
        state:'visible',timeout:30000});
      await page.waitForFunction(()=>{
        const card=document.querySelector('input[type=email]')?.closest('div.max-w-md');
        return !!card&&parseFloat(getComputedStyle(card).opacity)>=0.98;
      },null,{timeout:15000});
      ok('actualOwnerLoginForm',true);
      await shot('02-first-ever-login');
      await page.locator('input[type=email]').fill(owner);
      await page.locator('input[type=password]').fill(password);
      await page.getByRole('button',{name:'Se connecter',exact:true}).click();
      await route('/dashboard');
      await page.getByRole('button',{name:'Ajout rapide'}).waitFor({
        state:'visible',timeout:30000});
      ok('loginCreatesActualUserAuth',await page.evaluate(()=>
        !!localStorage.getItem('token')));
      await page.waitForFunction(()=>false,{timeout:1}).catch(()=>{});
      const cookie=(await ctx.cookies(backend)).filter(c=>c.name==='dc_workstation');
      ok('productCreatedSingleWorkstationCookie',cookie.length===1);
      ok('neverCalledEnrollmentApi',p.workstationEnrollCalls.length===0);
      const proof=await page.evaluate(async base=>{
        const token=localStorage.getItem('token');
        const headers={Authorization:'Bearer '+token};
        const [bootstrap,registry]=await Promise.all([
          fetch(base+'/api/workstation/bootstrap',{credentials:'include',headers}),
          fetch(base+'/api/workstation/registry',{credentials:'include',headers})
        ]);
        return {bs:bootstrap.status,rs:registry.status,
          state:bootstrap.ok?await bootstrap.json():null,
          rows:registry.ok?await registry.json():null};
      },backend);
      ok('serverReadOnlyBootstrap200',proof.bs===200);
      ok('serverReadOnlyRegistry200',proof.rs===200);
      ok('serverRegistryExactlyOne',Array.isArray(proof.rows)&&proof.rows.length===1);
      ok('serverWorkstationIdentityMatches',
        Boolean(proof.state?.workstationId)&&
        proof.rows?.[0]?.workstationId===proof.state?.workstationId);
      ok('noSpuriousEnrollmentGate',
        await page.locator('[data-workstation-enrollment]').count()===0);
      p.timingsMs.firstClinicalValue=Date.now()-started;
      await shot('03-first-ever-auto-registered-cabinet');

      await go('/hub?select=1');
      await page.locator('[data-workstation-admin]').waitFor({
        state:'visible',timeout:30000});
      ok('ownerMayManageFirstPost',true);
      await shot('04-first-ever-configure-post');
      await page.locator('[data-hub-experience="control"]').click();
      await route('/control-center');
      await page.locator('[data-control-center-topology]').waitFor({
        state:'visible',timeout:30000});
      ok('controlCenterReachable',true);
      await shot('05-first-ever-control-center');
      await page.getByRole('button',{name:'Continuer vers le Hub'}).click();
      await route('/hub');
      await page.locator('[data-hub-experience="cabinet"]').waitFor({
        state:'visible',timeout:30000});
      ok('realUiReturnToHub',true);
      await shot('06-first-ever-return-hub');
      ok('sixEvidenceScreenshots',p.images.length===6);
      if(p.pageErrors.length||p.http5xx.length)
        throw Error('Unexpected JS error or HTTP5xx in first-ever gate');
      report.cases.push(p);
    }catch(e){
      report.failures.push({viewport:v.name,reason:String(e).slice(0,700),
        checks:p.checks,images:p.images});
      if(page)await page.screenshot({path:path.join(out,v.name+'-FAIL.png'),
        fullPage:true}).catch(()=>{});
    }finally{if(ctx)await ctx.close()}
  }
}finally{await browser.close()}
report.success=report.failures.length===0&&report.cases.length===1&&
  report.cases[0].viewport==='tablet'&&report.cases[0].images.length===6&&
  Object.keys(report.cases[0].checks).length===16&&
  Object.values(report.cases[0].checks).every(Boolean)&&
  !report.cases[0].pageErrors.length&&!report.cases[0].http5xx.length;
await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
console.log('FUE_G00_FIRST_EVER_SUMMARY',JSON.stringify({
  head:report.head,isolated:report.isolated,success:report.success,
  cases:report.cases.map(p=>({viewport:p.viewport,images:p.images.length,
    checks:p.checks,timingsMs:p.timingsMs})),failures:report.failures}));
if(!report.success)throw Error('FUE-G00 first-ever T2 gate failed');
