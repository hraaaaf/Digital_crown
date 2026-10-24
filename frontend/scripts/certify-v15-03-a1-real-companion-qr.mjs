/**
 * Digital Crown V1.5-03 FUE-G03 / A1: REAL paired Companion QR handoff.
 * One disposable SQLCipher SQLite, two real independent Chromium contexts,
 * authenticated kiosk and phone, no HTTP interception or fake API responses.
 */
import { chromium, request } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

if (
  process.env.T2_STATION_FUE !== '1' ||
  process.env.T2_G03_A1 !== '1' ||
  process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
  process.env.ENVIRONMENT !== 'test' ||
  process.env.DATABASE_URL !== 'sqlite:///./t2-runtime-cert.db'
) throw Error('FAIL CLOSED: G03-A1 isolated synthetic runtime is required');

const origin = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw Error('T2 synthetic credentials missing');
const pin = '2468';
const out = path.resolve('artifacts/v15-03-a1-companion-real');
const fixtures = JSON.parse(await fs.readFile(path.join(out, 'seed.json'), 'utf8')).patients;
const evidence = {
  gate: 'FUE-G03-A1', head: process.env.EVALUATED_SHA,
  scope: 'real HTTP Chromium kiosk + separately paired Chromium phone + FastAPI + disposable encrypted SQLite on one runner; NOT camera/NFC hardware',
  cases: {}, screenshots: [], http: [], actors: {},
};
const assert = (condition, detail) => { if (!condition) throw Error(detail); };
async function expected(response, label, accepted) {
  const status = response.status();
  assert(accepted.includes(status), label + ' HTTP ' + status + ' ' + (await response.text()).slice(0, 250));
  return response;
}
async function logIn(api, email=user) {
  const r = await expected(await api.post('/api/auth/login', {
    form: {username:email,password},
  }), 'T2 account login', [200]);
  return (await r.json()).access_token;
}
async function apiActor() {
  const api = await request.newContext({baseURL:backend,timeout:20000});
  const access = await logIn(api);
  return {api, headers:{Authorization:'Bearer '+access},access};
}
async function snap(page, name) {
  await page.screenshot({path:path.join(out,name),fullPage:true,animations:'disabled'});
  evidence.screenshots.push(name);
}
function observe(page, label) {
  page.on('response', r => {
    if (r.url().startsWith(backend + '/api/')) {
      const url = new URL(r.url());
      evidence.http.push({actor:label,method:r.request().method(),path:url.pathname,status:r.status()});
    }
  });
  page.on('pageerror', err => evidence.http.push({actor:label,pageerror:err.message}));
}
async function stationPage(browser, station) {
  const ctx=await browser.newContext({
    storageState:await station.api.storageState(),
    viewport:{width:430,height:932},
  });
  const page=await ctx.newPage();
  await page.addInitScript(({access})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('appMode','prod');
  },{access:station.access});
  observe(page,'kiosk');
  await page.goto(origin+'/station',{waitUntil:'domcontentloaded'});
  await page.locator('[data-station-action="appointment"]').waitFor({state:'visible',timeout:50000});
  return {page,ctx};
}
let kiosk, paired, third, patientApi, browser, phone, station;
try {
  // Cold, unpaired first browser must not expose patient data.
  browser=await chromium.launch({headless:true});
  const cold=await browser.newContext({viewport:{width:430,height:932}});
  const coldPage=await cold.newPage();
  await coldPage.goto(origin+'/station',{waitUntil:'domcontentloaded'});
  await coldPage.waitForTimeout(1200);
  assert(await coldPage.locator('[data-station-arrival-confirmed]').count()===0,'unauthenticated browser leaked arrival data');
  await snap(coldPage,'01-fresh-unpaired-before.png');
  await cold.close();
  evidence.cases['01_cold_start']={anonymousArrivalHidden:true};

  kiosk=await apiActor();
  const enroll=await expected(await kiosk.api.post('/api/workstation/enroll',{
    headers:kiosk.headers,data:{accountPassword:password},
  }),'owner workstation enroll',[200]);
  const owner=(await enroll.json()).workstationId;
  await expected(await kiosk.api.post('/api/workstation/owner-pin',{
    headers:kiosk.headers,data:{accountPassword:password,newPin:pin},
  }),'set disposable owner PIN',[200]);
  await expected(await kiosk.api.post('/api/workstation/mode',{
    headers:kiosk.headers,data:{mode:'station',ownerPin:pin},
  }),'kiosk station mode',[200]);
  evidence.actors.kiosk={workstationId:owner};

  // Second physical *identity* in same runner via the product's genuine
  // 6-digit one-use enrollment code; never share a cookie with the kiosk.
  const codeResult=await expected(await kiosk.api.post('/api/workstation/pairing-code',{
    headers:kiosk.headers,data:{ownerPin:pin},
  }),'issue workstation pairing code',[200]);
  const code=(await codeResult.json()).code;
  paired=await apiActor();
  const pair=await expected(await paired.api.post('/api/workstation/pair',{
    headers:paired.headers,data:{code,displayName:'A1 Secondary Station (fictif)'},
  }),'pair a fresh secondary station',[200]);
  const secondaryStation=(await pair.json()).workstationId;
  assert(secondaryStation!==owner,'two distinct workstation identities expected');
  await expected(await paired.api.post('/api/workstation/mode',{
    headers:paired.headers,data:{mode:'station',ownerPin:pin},
  }),'secondary station mode',[200]);
  third=await apiActor();
  const stalePair=await third.api.post('/api/workstation/pair',{
    headers:third.headers,data:{code,displayName:'Duplicate Station'},
  });
  await expected(stalePair,'replayed workstation code denied',[403]);
  evidence.cases['02_station_pairing']={newStation:true,distinct:true,usedCodeDenied:stalePair.status()};
  evidence.actors.secondaryStation={workstationId:secondaryStation};

  // Product-issued invitations and product Pair endpoint: no synthetic
  // Companion access tokens or manually constructed encrypted vault.
  const invitations={};
  for (const key of ['primary','secondary']) {
    const res=await expected(await kiosk.api.post(
      '/api/patient-companion/admin/patients/'+fixtures[key].patientId+'/local-invitation',{
        headers:kiosk.headers,data:{relationship_type:'SELF',expires_in_minutes:15},
      }),key+' real invitation',[201]);
    invitations[key]=(await res.json()).manual_code;
  }
  const phoneCtx=await browser.newContext({viewport:{width:390,height:844}});
  phone=await phoneCtx.newPage();
  observe(phone,'companion');
  await phone.goto(origin+'/companion',{waitUntil:'domcontentloaded'});
  const pairPhone=async (key) => {
    await phone.locator('[data-pc00-manual-code]').waitFor({state:'visible',timeout:40000});
    await phone.locator('[data-pc00-manual-code]').fill(invitations[key]);
    const reply=phone.waitForResponse(r=>r.url().includes('/api/patient-companion/pair')&&r.request().method()==='POST');
    await phone.locator('[data-pc00-pair-manual]').click();
    const result=await reply;
    await expected(result,key+' patient phone pairing',[201]);
    await phone.getByText('Coffre local actif',{exact:false}).waitFor({state:'visible',timeout:35000});
    return await result.json();
  };
  const primaryAccess=await pairPhone('primary');
  await snap(phone,'03-companion-paired-primary.png');
  await phone.getByRole('button',{name:'Plus'}).click();
  await phone.getByRole('button',{name:'Ajouter un dossier'}).click();
  const secondaryAccess=await pairPhone('secondary');
  assert(primaryAccess.context.access_id!==secondaryAccess.context.access_id,'two genuine access contexts needed');
  await snap(phone,'03-companion-two-contexts.png');
  evidence.cases['03_real_companion_pairing']={
    productPairingHTTP:201, twoAuthorizedContexts:true, encryptedVaultViaProductUI:true,
  };

  station=await stationPage(browser,kiosk);
  const kioskPage=station.page;
  const pendingResponse=kioskPage.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/workstation/patient-session'&&r.request().method()==='POST');
  await kioskPage.locator('[data-station-action="appointment"]').click();
  const qr=await pendingResponse;
  await expected(qr,'station QR create',[201]);
  const created=await qr.json();
  assert(created.handoffUrl.startsWith(origin+'/companion?stationSession='),'handoff link must target actual Companion frontend');
  assert(created.handoffUrl===created.nfcPayload,'QR and NFC must carry identical opaque handoff');
  assert(created.qrDataUrl.startsWith('data:image/png;base64,'),'real QR PNG is missing');
  await kioskPage.locator('img[alt*="QR"]').waitFor({state:'visible',timeout:15000});
  await snap(kioskPage,'03-kiosk-qr-before.png');
  const before=await kiosk.api.get('/api/workstation/patient-session/'+created.sessionId+'/appointments/today',{headers:kiosk.headers});
  await expected(before,'arrivals before identity blocked',[409]);
  const wrongStation=await paired.api.get('/api/workstation/patient-session/'+created.sessionId+'/appointments/today',{headers:paired.headers});
  await expected(wrongStation,'other workstation cannot read private identity',[404,423]);

  // Put the ACTUAL handoff URL emitted by FastAPI into the separately paired
  // Chromium Patient Companion. The app must request explicit selection when
  // two encrypted patient contexts exist on that phone.
  await phone.goto(created.handoffUrl,{waitUntil:'domcontentloaded'});
  await phone.getByText('Choisir un dossier',{exact:true}).waitFor({state:'visible',timeout:25000});
  await snap(phone,'03-companion-choice-before.png');
  const claims=phone.waitForResponse(r=>
    new URL(r.url()).pathname==='/api/workstation/patient-session/claim'&&r.request().method()==='POST');
  await phone.locator('[data-pc00-context]').filter({hasText:fixtures.primary.displayName}).click();
  const claimed=await claims;
  await expected(claimed,'real Companion QR claim',[200]);
  await phone.locator('[data-station-handoff-status]').waitFor({state:'visible',timeout:25000});
  await kioskPage.locator('[data-station-arrival-bridge]').waitFor({state:'visible',timeout:25000});
  await snap(phone,'03-companion-claimed-after.png');
  await snap(kioskPage,'03-kiosk-patient-identified-after.png');
  const selected=kioskPage.locator('[data-station-appointment-id="'+fixtures.primary.appointmentId+'"]');
  await selected.waitFor({state:'visible',timeout:12000});
  await selected.click();
  await kioskPage.getByRole('button',{name:'Confirmer mon arrivée'}).click();
  await kioskPage.locator('[data-station-arrival-confirmed]').waitFor({state:'visible',timeout:15000});
  await snap(kioskPage,'03-kiosk-arrival-after.png');
  evidence.cases['03_real_phone_to_station']={
    realQRHandoff:true, explicitPatientSelection:true,
    claimStatus:claimed.status(), kioskIdentified:true, appointmentPersistedByRealAPI:true,
    wrongWorkstationDenied:wrongStation.status(), unclaimedArrivalDenied:before.status(),
  };

  // Replay and invented opaque bearer value are refused by genuine FastAPI.
  const handoffToken=new URL(created.handoffUrl).searchParams.get('stationSession');
  const auth={Authorization:'Bearer '+primaryAccess.access_token};
  // Patient claim checks must come from a phone-only HTTP client with no staff
  // workstation cookie or clinical auth inherited from the kiosk actors.
  patientApi=await request.newContext({baseURL:backend,timeout:20000});
  const postClaim=(token,accessId)=>patientApi.post('/api/workstation/patient-session/claim',{
    headers:auth,data:{token,accessId},
  });
  const replay=await postClaim(handoffToken,primaryAccess.context.access_id);
  await expected(replay,'single-use QR replay refused',[409]);
  const invalid=await postClaim('A'.repeat(48),primaryAccess.context.access_id);
  await expected(invalid,'invented QR token refused',[409]);

  // Server TTL enforced after real HTTP creation; the test-only SQL helper
  // sets only the disposable unclaimed session's expiry in the past.
  const exp=await expected(await paired.api.post('/api/workstation/patient-session',{
    headers:paired.headers,
  }),'secondary station expired-case QR issue',[201]);
  const expiredSession=await exp.json();
  execFileSync('python',['scripts/seed_v15_station_companion_a1.py','--expire-session',expiredSession.sessionId],{
    cwd:path.resolve('..'),env:process.env,stdio:'pipe',timeout:15000,
  });
  const expired=await postClaim(new URL(expiredSession.handoffUrl).searchParams.get('stationSession'),primaryAccess.context.access_id);
  await expected(expired,'real expired session claim denied',[409]);

  // New pending handoff is made invalid by actual workstation revocation.
  const rev=await expected(await paired.api.post('/api/workstation/patient-session',{
    headers:paired.headers,
  }),'secondary station revocation-case QR issue',[201]);
  const revSession=await rev.json();
  await expected(await kiosk.api.post('/api/workstation/'+secondaryStation+'/revoke',{
    headers:kiosk.headers,data:{ownerPin:pin},
  }),'owner revokes paired station',[200]);
  const revokedClaim=await postClaim(new URL(revSession.handoffUrl).searchParams.get('stationSession'),primaryAccess.context.access_id);
  await expected(revokedClaim,'revoked workstation cannot be claimed',[409]);
  const wallDenied=await paired.api.get('/api/workstation/wall-display',{headers:paired.headers});
  await expected(wallDenied,'revoked workstation cannot read station feed',[423]);
  evidence.cases['04_replay_expiry_revocation']={
    replayDenied:replay.status(),forgedTokenDenied:invalid.status(),
    expiredClaimDenied:expired.status(),revokedStationClaimDenied:revokedClaim.status(),
    revokedStationFeedDenied:wallDenied.status(),
  };

  const finalPhoneError=evidence.http.filter(e=>e.pageerror);
  assert(finalPhoneError.length===0,'JavaScript error from actual browser: '+JSON.stringify(finalPhoneError));
  assert(evidence.http.some(h=>h.actor==='companion'&&h.path.endsWith('/claim')&&h.status===200),
    'missing browser-observed genuine Companion claim');
  assert(evidence.http.some(h=>h.actor==='kiosk'&&h.path.includes('/appointments/')&&h.path.endsWith('/arrive')&&h.status===200),
    'missing browser-observed arrived appointment mutation');
  await snap(phone,'03-companion-final-after.png');
  console.log('G03_A1_REAL_COMPANION_QR_PASS '+JSON.stringify(evidence.cases));
} finally {
  await browser?.close();
  await Promise.allSettled([kiosk?.api?.dispose(),paired?.api?.dispose(),third?.api?.dispose(),patientApi?.dispose()]);
  await fs.mkdir(out,{recursive:true});
  await fs.writeFile(path.join(out,'evidence-after.json'),JSON.stringify(evidence,null,2));
}
