/**
 * V1.5-03 FUE-G03 A2: actual kiosk fallback form -> FastAPI -> SQLCipher.
 * Synthetic T2 only. No HTTP mocks, real browser controls and independent SQL.
 */
import { chromium, request } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

if (process.env.T2_G03_A2 !== '1' ||
    process.env.T2_STATION_FUE !== '1' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    process.env.ENVIRONMENT !== 'test' ||
    process.env.DATABASE_URL !== 'sqlite:///./t2-runtime-cert.db') {
  throw Error('FAIL CLOSED: A2 disposable runtime only');
}
const origin='http://127.0.0.1:5173';
const backend='http://127.0.0.1:8005';
const user=process.env.T2_USER, password=process.env.T2_PASSWORD;
if (!user || !password || !/^[0-9a-f]{40}$/.test(process.env.EVALUATED_SHA||'')) {
  throw Error('Missing synthetic login or exact CI SHA');
}
const pin='2468';
const out=path.resolve('artifacts/v15-03-a2-fallback-real');
await fs.mkdir(out,{recursive:true});
const fixtures=JSON.parse(await fs.readFile(path.join(out,'seed.json'),'utf8')).patients;
const evidence={
  gate:'FUE-G03-A2',head:process.env.EVALUATED_SHA,
  scope:'Actual Chromium Station + local HTTP FastAPI + isolated SQLCipher; synthetic patient only; no real camera/NFC/LAN/Windows',
  cases:{}, actors:{}, http:[], screenshots:[]
};
function assert(ok,msg){if(!ok)throw Error(msg)}
async function expectStatus(res,label,codes){
  assert(codes.includes(res.status()),label+' expected '+codes+' but received HTTP '+res.status());
  return res;
}
async function actor(){
  const api=await request.newContext({baseURL:backend,timeout:20000});
  const res=await expectStatus(await api.post('/api/auth/login',{
    form:{username:user,password}
  }),'synthetic account login',[200]);
  const access=(await res.json()).access_token;
  return {api,access,headers:{Authorization:'Bearer '+access}};
}
async function screenshot(page,name){
  await page.screenshot({path:path.join(out,name),fullPage:true,animations:'disabled'});
  evidence.screenshots.push(name);
}
function observe(page){
  page.on('response',r=>{
    if(r.url().startsWith(backend+'/api/')){
      evidence.http.push({
        method:r.request().method(),path:new URL(r.url()).pathname,
        status:r.status()
      });
    }
  });
  page.on('pageerror',err=>evidence.http.push({pageerror:err.message}));
}
async function kioskFlow(browser,kiosk,width=430){
  const ctx=await browser.newContext({
    storageState:await kiosk.api.storageState(),
    viewport:{width,height:width===768?1024:width===390?844:932}
  });
  const page=await ctx.newPage();
  await page.addInitScript(({access})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('appMode','prod');
  },{access:kiosk.access});
  observe(page);
  await page.goto(origin+'/station',{waitUntil:'domcontentloaded'});
  const choose=page.locator('[data-station-action="appointment"]');
  await choose.waitFor({state:'visible',timeout:45000});
  const createdResponse=page.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/workstation/patient-session'
    && r.request().method()==='POST'
  );
  await choose.click();
  const created=await expectStatus(await createdResponse,'UI Station session creation',[201]);
  const session=await created.json();
  await page.locator('[data-station-patient-session] img[alt*="QR"]').waitFor({state:'visible',timeout:25000});
  return {page,ctx,session};
}
async function showFallback(flow){
  await flow.page.locator('[data-station-fallback-toggle]').click();
  await flow.page.locator('[data-station-fallback-form]').waitFor({state:'visible'});
}
async function enter(flow,mode,values){
  const form=flow.page.locator('[data-station-fallback-form]');
  if(mode==='phone_dob'){
    await form.getByRole('textbox',{name:'Téléphone'}).fill(values.phone);
  }else{
    await form.getByRole('textbox',{name:'Prénom'}).fill(values.firstName);
    await form.getByRole('textbox',{name:'Nom'}).fill(values.lastName);
  }
  await form.locator('input[type="date"]').fill(values.birthDate);
}
async function submit(flow,codes){
  const resPromise=flow.page.waitForResponse(r=>
    new URL(r.url()).pathname.endsWith('/fallback') && r.request().method()==='POST'
  );
  await flow.page.getByRole('button',{name:'Confirmer mon identité'}).click();
  return expectStatus(await resPromise,'real UI fallback POST',codes);
}
async function configure(kiosk,mode,p=pin,expected=[200]){
  return expectStatus(await kiosk.api.patch('/api/workstation/patient-session/config',{
    headers:kiosk.headers,data:{fallbackMode:mode,ownerPin:p}
  }),'authorized fallback mode '+mode,expected);
}

let kiosk,other,browser;
try{
  browser=await chromium.launch({headless:true});
  kiosk=await actor();
  const enrollment=await expectStatus(await kiosk.api.post('/api/workstation/enroll',{
    headers:kiosk.headers,data:{accountPassword:password}
  }),'owner station enrollment',[200]);
  evidence.actors.kiosk=(await enrollment.json()).workstationId;
  await expectStatus(await kiosk.api.post('/api/workstation/owner-pin',{
    headers:kiosk.headers,data:{accountPassword:password,newPin:pin}
  }),'synthetic owner PIN',[200]);
  await expectStatus(await kiosk.api.post('/api/workstation/mode',{
    headers:kiosk.headers,data:{mode:'station',ownerPin:pin}
  }),'mode=station',[200]);

  // A separate true workstation identity must not read/modify this kiosk session.
  other=await actor();
  const otherEnrollment=await expectStatus(await other.api.post('/api/workstation/enroll',{
    headers:other.headers,data:{accountPassword:password}
  }),'second independently enrolled workstation',[200]);
  evidence.actors.other=(await otherEnrollment.json()).workstationId;
  assert(evidence.actors.other!==evidence.actors.kiosk,'workstations share identity');
  await expectStatus(await other.api.post('/api/workstation/mode',{
    headers:other.headers,data:{mode:'station',ownerPin:pin}
  }),'other station mode',[200]);

  const deniedPin=await configure(kiosk,'phone_dob','0000',[403]);
  evidence.cases.wrong_pin=deniedPin.status();
  await configure(kiosk,'phone_dob');

  // Real UI positive: phone digits with spacing normalize without partial identity leakage.
  const first=await kioskFlow(browser,kiosk,430);
  assert(first.session.fallbackMode==='phone_dob','phone_dob config not visible in real UI');
  await screenshot(first.page,'01-phone-qr-before.png');
  await showFallback(first);
  await enter(first,'phone_dob',{phone:'06 12 34 56 78',birthDate:'1992-05-04'});
  await screenshot(first.page,'02-phone-form-action.png');
  await submit(first,[200]);
  await first.page.getByText(fixtures.unique.displayName,{exact:false}).first().waitFor({state:'visible',timeout:25000});
  await screenshot(first.page,'03-phone-identified-after.png');
  evidence.cases.phone_success=true;
  await first.ctx.close();

  // Alternate authorized mode: normalize accent, case and whitespace from real inputs.
  await configure(kiosk,'name_dob');
  const second=await kioskFlow(browser,kiosk,390);
  assert(second.session.fallbackMode==='name_dob','name mode not returned');
  await showFallback(second);
  await enter(second,'name_dob',{
    firstName:'elodie',lastName:' BENMOUSSA ',birthDate:'1992-05-04'
  });
  await submit(second,[200]);
  await second.page.getByText(fixtures.unique.displayName,{exact:false}).first().waitFor({state:'visible',timeout:25000});
  await screenshot(second.page,'04-name-normalized-after.png');
  evidence.cases.name_success=true;
  await second.ctx.close();

  // Disabled means no public fallback control and a real server rejection.
  await configure(kiosk,'disabled');
  const disabled=await kioskFlow(browser,kiosk,768);
  assert(disabled.session.fallbackMode==='disabled','disabled config not respected');
  assert(await disabled.page.locator('[data-station-fallback-toggle]').count()===0,
    'disabled fallback unexpectedly visible');
  await screenshot(disabled.page,'05-disabled-before.png');
  await disabled.page.setViewportSize({width:1280,height:800});
  await screenshot(disabled.page,'06-disabled-1280-responsive.png');
  const disabledResponse=await kiosk.api.post(
    '/api/workstation/patient-session/'+disabled.session.sessionId+'/fallback',{
      headers:kiosk.headers,data:{phone:'0612345678',birthDate:'1992-05-04'}
    });
  await expectStatus(disabledResponse,'disabled denied on real server',[403]);
  evidence.cases.disabled=disabledResponse.status();
  const wrongStation=await other.api.post(
    '/api/workstation/patient-session/'+disabled.session.sessionId+'/fallback',{
      headers:other.headers,data:{phone:'0612345678',birthDate:'1992-05-04'}
    });
  await expectStatus(wrongStation,'cross-workstation fallback denied',[404]);
  evidence.cases.wrong_station=wrongStation.status();
  await disabled.ctx.close();

  // Wrong date and unknown number: generic real-UI denial, no identity display.
  // Use the independent station so the five-collision oracle below starts at zero.
  await configure(kiosk,'phone_dob');
  const negative=await kioskFlow(browser,other,390);
  await showFallback(negative);
  await enter(negative,'phone_dob',{phone:'0612345678',birthDate:'1901-01-01'});
  const wrongDob=await submit(negative,[403]);
  await enter(negative,'phone_dob',{phone:'0600000000',birthDate:'1992-05-04'});
  const unknownPhone=await submit(negative,[403]);
  assert(await negative.page.getByText(fixtures.unique.displayName,{exact:false}).count()===0,
    'invalid fallback revealed a patient identity');
  evidence.cases.wrong_dob_unknown=[wrongDob.status(),unknownPhone.status()];
  await screenshot(negative.page,'07-invalid-dob-and-phone-denied.png');
  await negative.ctx.close();

  // Real TTL invalidation, injected ONLY in the disposable DB.
  const expiry=await kioskFlow(browser,kiosk);
  execFileSync('python',['scripts/seed_v15_station_fallback_a2.py','--expire-session',expiry.session.sessionId],{
    cwd:path.resolve('..'),env:process.env,timeout:15000,stdio:'pipe'
  });
  const expiredResponse=await kiosk.api.post(
    '/api/workstation/patient-session/'+expiry.session.sessionId+'/fallback',{
      headers:kiosk.headers,data:{phone:'0612345678',birthDate:'1992-05-04'}
    });
  // A parallel UI status poll may already purge the expired row, so both
  // 'expired but not purged' (409) and 'already purged' (404) fail closed.
  await expectStatus(expiredResponse,'expired fallback rejected',[409,404]);
  evidence.cases.expiry=expiredResponse.status();
  await expiry.page.getByText('Session expirée',{exact:true}).waitFor({state:'visible',timeout:20000});
  await screenshot(expiry.page,'08-expired-session-verified.png');
  await expiry.ctx.close();

  // Two different matching patients must NEVER be identified by a shared phone + DOB.
  const collision=await kioskFlow(browser,kiosk);
  await showFallback(collision);
  await enter(collision,'phone_dob',{phone:'0698877665',birthDate:'1990-06-07'});
  await screenshot(collision.page,'06-collision-before.png');
  const denied=[];
  for(let attempt=1;attempt<=5;attempt++){
    const res=await submit(collision,[attempt===5?429:403]);
    denied.push(res.status());
    assert(await collision.page.getByText(fixtures.collisionA.displayName,{exact:false}).count()===0,
      'collision displayed a matched identity');
    assert(await collision.page.getByText(fixtures.collisionB.displayName,{exact:false}).count()===0,
      'collision leaked a second identity');
  }
  await collision.page.getByRole('alert').filter({hasText:'Trop de tentatives'})
    .waitFor({state:'visible',timeout:15000});
  await screenshot(collision.page,'07-collision-locked-after.png');
  evidence.cases.collision_lock=denied;
  await collision.ctx.close();

  // Regenerating a new one-shot QR cannot reset a station-scoped failure limit.
  const replacement=await expectStatus(await kiosk.api.post(
    '/api/workstation/patient-session',{
      headers:kiosk.headers,data:{purpose:'appointment'}
    }),'fresh QR after lock',[201]);
  const freshSession=await replacement.json();
  const locked=await kiosk.api.post(
    '/api/workstation/patient-session/'+freshSession.sessionId+'/fallback',{
      headers:kiosk.headers,data:{phone:'0612345678',birthDate:'1992-05-04'}
    });
  await expectStatus(locked,'lock survives QR regeneration',[429]);
  evidence.cases.regen_locked=locked.status();

  // Another workstation within the same synthetic cabinet has its own counter.
  const otherSession=await expectStatus(await other.api.post(
    '/api/workstation/patient-session',{
      headers:other.headers,data:{purpose:'appointment'}
    }),'other station new session',[201]);
  const otherId=(await otherSession.json()).sessionId;
  const unaffected=await other.api.post(
    '/api/workstation/patient-session/'+otherId+'/fallback',{
      headers:other.headers,data:{phone:'0612345678',birthDate:'1992-05-04'}
    });
  await expectStatus(unaffected,'independent station unaffected',[200]);
  evidence.cases.other_station_accepted=unaffected.status();

  // Do not leak tokens, birth dates or phone values into evidence.
  assert(evidence.http.every(h=>!h.pageerror),'real browser JavaScript error');
  assert(evidence.screenshots.length>=9,'Missing multi-width before/after screenshots');
  assert(evidence.http.every(h=>!JSON.stringify(h).includes('stationSession=')),
    'QR bearer secret accidentally logged');
  console.log('G03_A2_REAL_FALLBACK_PASS '+JSON.stringify(evidence.cases));
}finally{
  await browser?.close();
  await Promise.allSettled([kiosk?.api?.dispose(),other?.api?.dispose()]);
  await fs.mkdir(out,{recursive:true});
  await fs.writeFile(path.join(out,'evidence-after.json'),JSON.stringify(evidence,null,2));
}
