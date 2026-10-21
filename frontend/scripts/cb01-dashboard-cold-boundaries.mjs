// CB-01 #42 negative cold-start boundary checks, real isolated FastAPI responses.
import path from 'node:path';
import { chromium, request } from 'playwright';
const API='http://127.0.0.1:8005';
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const tracked=['/health','/api/workstation/bootstrap','/api/auth/me','/api/auth/refresh','/api/clinics/init-status'];
const clinical=/^\/api\/(?:bot\/execute|appointments|patients|devis)(?:\/|$)/;
const expiredMarker='e30.'+Buffer.from(JSON.stringify({exp:1})).toString('base64url')+'.intentionally-invalid-expired';
export async function runCb01DashboardColdBoundaries({browser,origin,out,sourceHead,staffToken}) {
  if(process.env.GITHUB_ACTIONS!=='true'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
    ||!/^[0-9a-f]{40}$/.test(sourceHead||'')||!staffToken)
    throw Error('REFUSED: CB-01 #42 cold boundary requires isolated runner and authenticated S05 fixture');
  const clean=await chromium.launch({channel:'chromium',headless:true,args:['--disable-background-networking']});
  const results=[];
  async function cold(spec){
    const context=await clean.newContext({viewport:{width:1280,height:900}});
    const page=await context.newPage();
    const start=Date.now(),responses=[],writes=[],errors=[];
    let maxMainObserved=0;
    try{
      if(spec.token){
        await context.addInitScript(token=>{
          if(location.hostname==='127.0.0.1'&&location.port==='5173')localStorage.setItem('token',token);
        },spec.token);
      }
      // Observer is attached before React mounts, to catch even a short-lived clinical render.
      await context.addInitScript(()=>{
        window.__cb01MainSeen=0;
        const detect=()=>{
          const main=document.querySelector('main');
          const bot=[...document.querySelectorAll('button')].some(b=>b.textContent?.includes('Ouvrir CrownBot'));
          // The public, data-free Hub legitimately renders <main>; count ONLY clinical Dashboard exposure.
          if(location.pathname==='/dashboard'&&(main||bot))window.__cb01MainSeen++;
        };
        new MutationObserver(detect).observe(document,{childList:true,subtree:true});
      });
      page.on('pageerror',e=>errors.push(String(e?.name||'pageerror').slice(0,60)));
      page.on('request',r=>{
        let u;try{u=new URL(r.url());}catch{return;}
        if(r.method()!=='GET'&&clinical.test(u.pathname))writes.push(r.method()+' '+u.pathname);
      });
      page.on('response',r=>{
        let u;try{u=new URL(r.url());}catch{return;}
        if(u.hostname==='127.0.0.1'&&u.port==='8005'&&tracked.includes(u.pathname))
          responses.push({path:u.pathname,status:r.status(),atMs:Date.now()-start});
      });
      await page.route('**/*',async route=>{
        const r=route.request();let u;try{u=new URL(r.url());}catch{await route.continue();return;}
        const ms=(r.method()==='GET'&&u.hostname==='127.0.0.1'&&u.port==='8005')
          ? (spec.delays?.[u.pathname]||0):0;
        if(!ms){await route.continue();return;}
        const upstream=await route.fetch({timeout:25000});
        await pause(ms);
        await route.fulfill({response:upstream});
      });
      await page.goto(origin+'/dashboard',{waitUntil:'domcontentloaded',timeout:40000});
      if(spec.destination==='login'){
        await page.waitForURL(u=>u.pathname==='/login',{timeout:30000});
        await page.locator('input[type="email"]').first().waitFor({state:'visible',timeout:12000});
        if(spec.expected401&&!responses.some(x=>['/api/auth/me','/api/auth/refresh'].includes(x.path)&&x.status===401))
          throw Error('expired marker did not exercise real HTTP401');
      }else{
        await page.waitForURL(u=>u.pathname==='/hub'&&u.searchParams.get('enroll')==='1',{timeout:30000});
        if(!responses.some(x=>x.path==='/api/workstation/bootstrap'&&[200,423].includes(x.status)))
          throw Error('real workstation enrollment verdict not observed');
      }
      await pause(350);
      maxMainObserved=await page.evaluate(()=>window.__cb01MainSeen||0);
      if(maxMainObserved||await page.getByRole('button',{name:'Ouvrir CrownBot'}).isVisible().catch(()=>false))
        throw Error('FAIL-OPEN: clinical MainLayout became visible');
      if(new URL(page.url()).pathname==='/setup')throw Error('FAIL-OPEN: reached clinic setup');
      if(errors.length||writes.length)throw Error('JS exception or clinical write');
      const final=new URL(page.url());
      return {name:spec.name,status:'PASS_COLD_FAIL_CLOSED_REAL_FASTAPI',
        elapsedMs:Date.now()-start,finalPath:final.pathname,finalEnrollment:final.searchParams.get('enroll')==='1',
        responseTimeline:responses,clinicalMainSeen:0,pageErrors:0,clinicalWrites:0};
    }catch(e){
      await page.screenshot({path:path.join(out,'cb01-42-cold-'+spec.name+'-failure.png')}).catch(()=>{});
      throw Error('CB01 #42 cold '+spec.name+' '+String(e?.message||e)
        +';responses='+JSON.stringify(responses)+';mainSeen='+maxMainObserved
        +';pageErrors='+errors.length+';writes='+writes.length+';path='+new URL(page.url()).pathname);
    }finally{await context.close().catch(()=>{});}
  }
  try{
    // Each scenario is a separate empty incognito Chromium context: NO persistent browser cookies.
    results.push(await cold({name:'anonymous-bootstrap-delayed',destination:'login',
      delays:{'/health':900,'/api/workstation/bootstrap':1600}}));
    results.push(await cold({name:'expired-local-token-refresh-401',destination:'login',
      token:expiredMarker,expected401:true,
      delays:{'/health':700,'/api/auth/me':1600,'/api/workstation/bootstrap':400}}));
    // This is a genuine short-lived signed S05 token on a brand-new, UNPAIRED browser.
    // Probe real backend 423 without workstation cookies; never synthesize a 423 body.
    const noStation=await request.newContext({baseURL:API,storageState:{cookies:[],origins:[]}});
    try{
      const denied=await noStation.get('/api/clinics/init-status',{
        headers:{Authorization:'Bearer '+staffToken}});
      if(denied.status()!==423)throw Error('FAIL: real unpaired clinic init did not HTTP423; '+denied.status());
    }finally{await noStation.dispose();}
    results.push(await cold({name:'valid-s05-unpaired-real-423',destination:'hub',
      token:staffToken,delays:{'/health':800,'/api/workstation/bootstrap':2400}}));
  }finally{await clean.close();}
  // A 24s real network-response delay tests near the historical splash, below Axios 30s timeout.
  const page=await browser.newPage(),observed=[],errors=[],writes=[],started=Date.now();
  try{
    if(!(await browser.cookies()).some(c=>c.name==='access_token'))
      throw Error('REFUSED: no UI-authenticated session for 24s health delay');
    page.on('pageerror',e=>errors.push(String(e?.name||'pageerror').slice(0,60)));
    page.on('request',r=>{const u=new URL(r.url());
      if(r.method()!=='GET'&&clinical.test(u.pathname))writes.push(r.method()+' '+u.pathname);
    });
    await page.route('**/health',async route=>{
      const u=new URL(route.request().url());
      if(u.hostname!=='127.0.0.1'||u.port!=='8005'||route.request().method()!=='GET'){
        await route.continue();return;
      }
      const res=await route.fetch({timeout:25000});
      observed.push({path:'/health',status:res.status()});
      await pause(24000);
      await route.fulfill({response:res});
    });
    await page.goto(origin+'/dashboard',{waitUntil:'domcontentloaded',timeout:45000});
    await page.locator('main').first().waitFor({state:'visible',timeout:48000});
    await page.getByRole('button',{name:'Ouvrir CrownBot'}).waitFor({state:'visible',timeout:48000});
    const elapsed=Date.now()-started;
    if(new URL(page.url()).pathname!=='/dashboard'||elapsed<23000||elapsed>54000
       ||!observed.some(x=>x.status===200)||writes.length||errors.length)
      throw Error('FAIL: slow health did not recover cleanly');
    results.push({name:'signed-in-real-health-24s',status:'PASS_24S_REAL_BACKEND_RECOVERY',
      elapsedMs:elapsed,finalPath:'/dashboard',responseTimeline:observed,
      pageErrors:0,clinicalWrites:0});
  }catch(e){
    await page.screenshot({path:path.join(out,'cb01-42-cold-health-24s-failure.png')}).catch(()=>{});
    throw Error('CB01 #42 24s '+String(e?.message||e)+';elapsed='+(Date.now()-started)
      +';errors='+errors.length+';writes='+writes.length);
  }finally{await page.close().catch(()=>{});}
  if(results.length!==4)throw Error('FAIL: CB-01 #42 negative matrix incomplete');
  return {status:'PASS_4_COLD_AUTH_WORKSTATION_AND_24S_REAL_BACKEND',sourceHead,
    scenarioCount:4,realBackend:true,mockedResponses:0,results};
}
