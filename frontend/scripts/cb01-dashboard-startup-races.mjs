// CB-01 #42: real isolated FastAPI, original responses delayed but never mocked.
import path from 'node:path';
const endpoints=['/health','/api/workstation/bootstrap','/api/auth/me','/api/clinics/init-status'];
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const cases=[
  {name:'health-slow',delays:[1800,0,200,0]},
  {name:'workstation-slow',delays:[0,2200,0,300]},
  {name:'auth-init-slow',delays:[100,300,1600,2100]},
  {name:'parallel-a',delays:[1250,100,1800,200]},
  {name:'parallel-b',delays:[0,1750,150,1850]},
];
export async function runCb01DashboardStartupRaces({browser,origin,out,sourceHead}) {
  if(process.env.GITHUB_ACTIONS!=='true'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
     ||!/^[a-f0-9]{40}$/.test(sourceHead||''))throw Error('REFUSED: #42 isolated exact-HEAD only');
  const test=async spec=>{
    const page=await browser.newPage(), start=Date.now(), seen=[],writes=[],errors=[];
    try{
      if(!(await browser.cookies()).some(c=>c.name==='access_token'))
        throw Error('REFUSED: no actual UI login session');
      page.on('pageerror',e=>errors.push(String(e?.name||'pageerror').slice(0,80)));
      page.on('request',r=>{
        const p=new URL(r.url()).pathname;
        if(r.method()!=='GET'&&/^\/api\/(?:bot\/execute|appointments|patients|devis)(?:\/|$)/.test(p))
          writes.push(r.method()+' '+p);
      });
      await page.route('**/*',async route=>{
        const req=route.request(),u=new URL(req.url()),i=endpoints.indexOf(u.pathname);
        if(u.hostname!=='127.0.0.1'||u.port!=='8005'||req.method()!=='GET'||i<0){
          await route.continue();return;
        }
        const upstream=await route.fetch({timeout:25000});
        await pause(spec.delays[i]);
        seen.push({path:u.pathname,status:upstream.status(),atMs:Date.now()-start});
        await route.fulfill({response:upstream});
      });
      await page.goto(origin+'/dashboard',{waitUntil:'domcontentloaded',timeout:30000});
      await page.locator('main').first().waitFor({state:'visible',timeout:25000});
      await page.getByRole('button',{name:'Ouvrir CrownBot'}).waitFor({state:'visible',timeout:25000});
      const finalPath=new URL(page.url()).pathname;
      if(finalPath!=='/dashboard')throw Error('unexpected redirect '+finalPath);
      if(endpoints.some(p=>!seen.some(o=>o.path===p&&o.status===200)))
        throw Error('real HTTP 200 bootstrap evidence incomplete');
      if(errors.length||writes.length)throw Error('JS exception or clinical write');
      if(await page.getByText('Démarrage de Digital Crown…').isVisible().catch(()=>false))
        throw Error('startup loader remained');
      return {name:spec.name,status:'PASS_REAL_BACKEND_DELAYED_RESPONSE',
        elapsedMs:Date.now()-start,finalPath,delaysMs:spec.delays,
        responseTimeline:seen,pageErrors:0,clinicalWrites:0};
    }catch(e){
      await page.screenshot({path:path.join(out,'cb01-42-'+spec.name+'-failure.png')}).catch(()=>{});
      throw Error('CB01 #42 '+spec.name+' '+String(e?.message||e)+'; observed='+JSON.stringify(seen)+
        '; errors='+errors.length+'; writes='+writes.length+'; urlPath='+new URL(page.url()).pathname);
    }finally{await page.close().catch(()=>{});}
  };
  const results=[];
  for(const item of cases.slice(0,3))results.push(await test(item));
  results.push(...await Promise.all(cases.slice(3).map(test)));
  if(results.length!==5)throw Error('FAIL: incomplete CB01 #42 matrix');
  return {status:'PASS_5_DIRECT_DASHBOARD_REAL_BACKEND_RACE_CASES',
    sourceHead,scenarioCount:5,realBackend:true,mockedResponses:0,results};
}
