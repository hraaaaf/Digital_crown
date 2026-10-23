/**
 * CB-02 FUE: genuine LoginPage in a fresh browser, real MainLayout and FastAPI.
 * GitHub disposable synthetic SQLite/SQLCipher workstation only. NEVER a clinic.
 * Distinct from screenshots with pre-injected auth tokens: those are not FUE login.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const pw = createRequire(path.resolve('frontend/package.json'))('playwright');
const { chromium, request } = pw;
const required = [
  ['GITHUB_ACTIONS','true'],['DIGITALCROWN_ISOLATED_RUNTIME','1'],
  ['CLOUD_AI_ENABLED','false'],['TELEMETRY_ENABLED','false'],
  ['CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED','true'],
  ['CROWN_BOT_GUIDED_NLU_ENABLED','true'],
  ['VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED','true'],
  ['VITE_CROWN_BOT_GUIDED_NLU_ENABLED','true'],
];
for (const [key,val] of required) if(process.env[key]!==val)
  throw Error('REFUSED: CB-02 synthetic-only FUE missing guard '+key);
if(process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db')
  throw Error('REFUSED: unexpected clinical database target');
const sha = process.env.CB02_SOURCE_HEAD;
if(!/^[a-f0-9]{40}$/.test(sha||'')||!process.env.T2_PASSWORD
   ||process.env.T2_USER!=='t2-browser@cabinet.ma')
  throw Error('REFUSED: synthetic credentials and exact SHA required');
const origin='http://127.0.0.1:5173';
const apiOrigin='http://127.0.0.1:8005';
const out=path.resolve('artifacts/cb02-fue-real-login');
fs.mkdirSync(out,{recursive:true});
const report={schema:'CB02_FUE_REAL_LOGIN_ISOLATED_V1',sha,
  realUiLogin:false,mainLayout:false,cabinetDayRead:false,
  authorizedProgramme:false,guidedPreview:false,
  rejectedZeroPatient:false,roleDeniedBeforePatient:false,
  zeroClinicalWrites:true,synthetic:true,humanE2E:false,
  clinicalDBSnapshot:'SEPARATE_REQUIRED',screenshots:[],errors:[],httpProof:{}};
const http=await request.newContext({baseURL:apiOrigin});
let browser;
try {
  const auth=await http.post('/api/auth/login',{
    form:{username:process.env.T2_USER,password:process.env.T2_PASSWORD}});
  if(auth.status()!==200)throw Error('REFUSED: bootstrap owner login '+auth.status());
  const owner=await auth.json();
  const enrolled=await http.post('/api/workstation/enroll',{
    data:{accountPassword:process.env.T2_PASSWORD},
    headers:{Authorization:'Bearer '+owner.access_token}});
  if(enrolled.status()!==200)throw Error('REFUSED: canonical workstation enrollment '+enrolled.status());
  const state=await http.storageState();
  const cookie=state.cookies.filter(x=>x.name==='dc_workstation');
  if(cookie.length!==1||cookie[0].httpOnly!==true)
    throw Error('REFUSED: no real HttpOnly workstation cookie');
  const station={cookies:cookie,origins:[]};
  browser=await chromium.launch({headless:true});
  for(const role of ['S05','S06']){
    const context=await browser.newContext({
      viewport:{width:1280,height:900},storageState:station});
    const page=await context.newPage();
    const writes=[],pageErrors=[];
    page.on('pageerror',e=>pageErrors.push(String(e)));
    page.on('request',q=>{
      const u=new URL(q.url());
      if(q.method()!=='GET'&&/^\/api\/(?:bot\/execute|appointments|patients|devis|actes|payments)/.test(u.pathname))
        writes.push(q.method()+':'+u.pathname);
    });
    try {
      await page.goto(origin+'/login',{waitUntil:'domcontentloaded',timeout:60000});
      await page.locator('input[type=email]').waitFor({state:'visible',timeout:30000});
      const virgin=await page.evaluate(()=>({
        token:!!localStorage.getItem('token'),
        refresh:!!localStorage.getItem('refresh_token'),
        zustand:!!localStorage.getItem('auth-storage')}));
      if(Object.values(virgin).some(Boolean)||new URL(page.url()).pathname!=='/login')
        throw Error('NOT_FUE: not a fresh LoginPage');
      const before='cb02-fue-'+role+'-before-login.png';
      await page.screenshot({path:path.join(out,before)});
      report.screenshots.push(before);
      const login=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/auth/login'
         &&r.request().method()==='POST',{timeout:45000});
      await page.locator('input[type=email]').fill(
        role==='S05'?'t2-s05-reception@cabinet.ma':'t2-s06-no-agenda@cabinet.ma');
      await page.locator('input[type=password]').fill(process.env.T2_PASSWORD);
      await page.getByRole('button',{name:'Se connecter',exact:true}).click();
      const resp=await login;
      if(resp.status()!==200)throw Error('NOT_FUE: real UI login denied '+role+' '+resp.status());
      await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:60000});
      await page.locator('main').first().waitFor({state:'visible',timeout:60000});
      const tokenPresent=await page.evaluate(()=>!!localStorage.getItem('token'));
      if(!tokenPresent)throw Error('NOT_FUE: UI login did not create a live session');
      report.realUiLogin=true;report.mainLayout=true;
      const opener=page.getByRole('button',{name:'Ouvrir CrownBot'}).first();
      await opener.waitFor({state:'visible',timeout:30000});
      await opener.click();
      const guided=page.getByRole('region',{name:'Français guidé Crown Bot CB-02'});
      await guided.waitFor({state:'visible',timeout:30000});
      if(role==='S05'){
        const programme=page.waitForResponse(r=>
          new URL(r.url()).pathname==='/api/appointments/'&&
          r.request().method()==='GET',{timeout:45000});
        await page.getByRole('button',{name:'Mon programme',exact:true}).click();
        const appt=await programme;
        if(appt.status()!==200)throw Error('NOT_FUE: authorized real Agenda GET '+appt.status());
        await page.getByRole('status',{name:'Programme du jour'}).waitFor({state:'visible'});
        report.cabinetDayRead=true;
        report.authorizedProgramme=true;
        report.httpProof.programme=200;
      }
      const input=guided.getByRole('textbox',{name:'Votre demande en français'});
      async function submit(text,expectedStatus){
        await input.fill(text);
        const response=page.waitForResponse(r=>
          new URL(r.url()).pathname==='/api/bot/guided/preview'
          &&r.request().method()==='POST',{timeout:30000});
        await guided.getByRole('button',{name:'Comprendre la demande'}).click();
        const res=await response;
        const payload=await res.json();
        if(res.status()!==expectedStatus)throw Error('NOT_FUE: '+role+' preview '+res.status()+' != '+expectedStatus);
        return payload;
      }
      if(role==='S05'){
        const agenda=await submit('Mon agenda demain',200);
        if(agenda.status!=='requires_server_authorization'||agenda.intent!=='AGENDA_READ'
          ||agenda.executable!==false||agenda.proposal!==null)
          throw Error('NOT_FUE: guided agenda contract');
        await guided.getByText('Syntaxe comprise ; contrôles serveur obligatoires.').waitFor({state:'visible'});
        report.guidedPreview=true;
        const refused=await submit('Trouve patient 0',200);
        if(refused.status!=='refused'||refused.intent!==null||refused.executable!==false
          ||Object.keys(refused.fields||{}).length)
          throw Error('NOT_FUE: zero patient not refused');
        report.rejectedZeroPatient=true;
        report.httpProof.guided200=200;
      }else{
        const deny=await submit('Mon agenda demain',403);
        if(!deny?.detail)throw Error('NOT_FUE: missing role-denial payload');
        await guided.getByRole('alert').waitFor({state:'visible'});
        report.roleDeniedBeforePatient=true;
        report.httpProof.s06Denied=403;
      }
      const after='cb02-fue-'+role+'-after.png';
      await guided.scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(out,after)});
      report.screenshots.push(after);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>
        document.documentElement.clientWidth+2);
      if(overflow||writes.length||pageErrors.length)
        throw Error('NOT_FUE: layout, clinical HTTP write or JS error '+JSON.stringify({overflow,writes,pageErrors}));
    }finally{
      await context.close();
    }
  }
  if(!report.realUiLogin||!report.authorizedProgramme||!report.guidedPreview
    ||!report.rejectedZeroPatient||!report.roleDeniedBeforePatient)
    throw Error('NOT_FUE: incomplete critical journey');
  report.status='PASS_AUTOMATED_SYNTHETIC_FUE';
  console.log('CB02_FUE_REAL_LOGIN: PASS',JSON.stringify({
    sha,login:report.realUiLogin,firstValue:report.authorizedProgramme,
    zeroPatientRefused:report.rejectedZeroPatient,role403:report.roleDeniedBeforePatient,
    writes:0}));
}catch(e){
  report.status='NOT_CERTIFIED';report.errors.push(String(e));
  console.error('CB02_FUE_REAL_LOGIN: NOT_CERTIFIED',String(e));
  process.exitCode=1;
}finally{
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
  if(browser)await browser.close();
  await http.dispose();
}
