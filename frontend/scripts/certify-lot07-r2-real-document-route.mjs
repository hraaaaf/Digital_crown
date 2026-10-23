/**
 * LOT07 R2 FUE-I: real Cabinet React UI + real FastAPI, fully disposable T2.
 * This is NOT a clinical release/Windows dual-screen certification.
 * No stateful writes, uploads, printing, external APIs or real patient data.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head = process.env.PRODUCT_HEAD;
const password = process.env.T2_PASSWORD;
const a = Number(process.env.R2_T2_PATIENT_A_ID);
const b = Number(process.env.R2_T2_PATIENT_B_ID);
if (process.env.ENVIRONMENT !== 'test'
  || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
  || process.env.DATABASE_URL !== 'sqlite:///./t2-runtime-cert.db'
  || !/^[0-9a-f]{40}$/.test(head || '')
  || !password || !Number.isSafeInteger(a) || !Number.isSafeInteger(b)
  || a <= 0 || b <= 0 || a === b) {
  throw Error('REFUSED: isolated exact-HEAD T2 with two different synthetic patients required');
}
const app = 'http://127.0.0.1:5173';
const backend = 'http://127.0.0.1:8005';
const out = path.resolve('../artifacts/lot07-r2-real-cabinet');
await fs.mkdir(out,{recursive:true});
const report={head,environment:'DISPOSABLE_T2_REAL_FASTAPI_AND_REAL_CABINET',patientReal:false,checks:[],clinicalRelease:false};
const api = await request.newContext({baseURL:backend});
const browser = await chromium.launch({headless:true});
let context;
let page;
try {
  const login = await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
  if(login.status() !== 200) throw Error('FAIL: disposable T2 browser identity not authenticated');
  const token = (await login.json()).access_token;
  const ownerState = await enrollT2Workstation(api,token,password);
  const workstation = ownerState.cookies.filter(c=>c.name==='dc_workstation');
  if(workstation.length !== 1 || workstation[0].httpOnly!==true)
    throw Error('REFUSED: no unique pre-enrolled T2 station cookie');
  report.checks.push('REAL_SYNTHETIC_FASTAPI_AUTH_AND_WORKSTATION');

  // Confirm backend denies a distinct restricted staff actor independently of UI.
  const restrictedApi = await request.newContext({baseURL:backend});
  try {
    const restrictedLogin=await restrictedApi.post('/api/auth/login',{
      form:{username:'t2-restricted@cabinet.ma',password},
    });
    if(restrictedLogin.status()!==200)throw Error('FAIL: restricted synthetic actor login unavailable');
    const restrictedToken=(await restrictedLogin.json()).access_token;
    const staffState=await restrictedApi.storageState();
    const staffCookies=staffState.cookies.filter(c=>c.name==='access_token');
    if(staffCookies.length!==1 || staffCookies[0].value!==restrictedToken)
      throw Error('REFUSED: unambiguous restricted actor cookie missing');
    const staffOnOwnerEnrolledWorkstation=await request.newContext({
      baseURL:backend,
      storageState:{cookies:[...staffCookies,...workstation],origins:[]},
    });
    try {
      const forbidden=await staffOnOwnerEnrolledWorkstation.get('/api/patients/'+a,{
        headers:{Authorization:'Bearer '+restrictedToken},
      });
      if(forbidden.status()!==403)
        throw Error('FAIL: restricted staff with valid workstation must receive 403, not '+forbidden.status());
      report.checks.push('ENROLLED_RESTRICTED_ROLE_PATIENT_GET_HTTP_403');
    } finally {await staffOnOwnerEnrolledWorkstation.dispose();}
  } finally {await restrictedApi.dispose();}

  context = await browser.newContext({
    viewport:{width:1440,height:900}, reducedMotion:'reduce',
    storageState:{cookies:workstation,origins:[]},
  });
  page = await context.newPage();
  const pageErrors=[];
  page.on('pageerror',err=>pageErrors.push(err.message));
  await page.goto(app+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
  await page.locator('[data-hub-experience="cabinet"]').click();
  await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/dashboard',{timeout:45000});
  if(!await page.evaluate(()=>Boolean(localStorage.getItem('token'))))
    throw Error('FAIL: no real browser Cabinet auth session');
  report.checks.push('REAL_CABINET_UI_LOGIN');

  await page.goto(app+'/patients/'+a+'?tab=admin',{
    waitUntil:'domcontentloaded',timeout:45000,
  });
  await page.locator('[data-tour="tab-libre"]').waitFor({state:'visible',timeout:45000});
  await page.locator('[data-tour="tab-libre"]').click();
  const editor=page.locator('textarea[placeholder^="Rédigez votre document ici"]');
  await editor.waitFor({state:'visible',timeout:30000});
  const syntheticSentinel='T2_R2_A_REAL_DOCUMENT_UNSAVED';
  await editor.fill(syntheticSentinel);
  if(await editor.inputValue()!==syntheticSentinel)
    throw Error('FAIL: real Document Libre editor did not accept synthetic draft');
  const backToList=page.getByRole('button',{name:'Retourner à la liste des patients'});
  await backToList.click();
  const modal=page.getByRole('alertdialog',{name:'Brouillon non enregistré'});
  await modal.waitFor({state:'visible',timeout:16000});
  if(new URL(page.url()).pathname!=='/patients/'+a || await editor.inputValue()!==syntheticSentinel)
    throw Error('FAIL: draft lost or route changed before user decision');
  report.checks.push('REAL_DOCUMENT_DRAFT_BLOCKS_BEFORE_NAVIGATION');

  await modal.getByRole('button',{name:'Rester sur ce dossier'}).click();
  await modal.waitFor({state:'hidden',timeout:12000});
  if(new URL(page.url()).pathname!=='/patients/'+a || await editor.inputValue()!==syntheticSentinel)
    throw Error('FAIL: Stay did not preserve A real Document Libre draft');
  report.checks.push('CANCEL_PRESERVES_REAL_DOCUMENT_CONTENT');

  await backToList.click();
  await modal.waitFor({state:'visible',timeout:16000});
  await modal.getByRole('button',{name:'Quitter sans sauvegarder'}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/patients',{timeout:20000});
  if((await page.locator('body').innerText()).includes(syntheticSentinel))
    throw Error('FAIL: A draft leaked to patient list after discard');
  report.checks.push('EXPLICIT_DISCARD_BEFORE_LEAVING_A');

  // Open B with real React PatientList navigation, not a hard page reload.
  const patientB=page.getByText('T2-R2-B',{exact:true}).first();
  await patientB.waitFor({state:'visible',timeout:30000});
  await patientB.click();
  await page.waitForURL(url=>new URL(url).pathname==='/patients/'+b,{timeout:30000});
  // A selected from the patient list opens Tracking by default. Switch into
  // Documents using the REAL Cabinet tab button, preserving SPA navigation.
  await page.locator('[data-tour="patient-tabs"]').getByRole('button',{name:'Document',exact:true}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/patients/'+b
    && new URL(url).searchParams.get('tab')==='admin',{timeout:15000});
  await page.locator('[data-tour="tab-libre"]').waitFor({state:'visible',timeout:30000});
  await page.locator('[data-tour="tab-libre"]').click();
  await editor.waitFor({state:'visible',timeout:30000});
  if((await editor.inputValue()).includes(syntheticSentinel))
    throw Error('FAIL: A draft leaked into patient B real editor');
  report.checks.push('REAL_A_TO_B_DOCUMENT_ISOLATION');

  // Use the browser history POP path with B's dirty draft: cancel must keep B.
  const bSentinel='T2_R2_B_REAL_DOCUMENT_UNSAVED';
  await editor.fill(bSentinel);
  // The first Back goes from ?tab=admin to the SAME patient's Tracking tab;
  // React would unmount the dirty DocumentHub here without the R2 query guard.
  await page.evaluate(()=>history.back());
  await modal.waitFor({state:'visible',timeout:16000});
  if(new URL(page.url()).pathname!=='/patients/'+b || await editor.inputValue()!==bSentinel)
    throw Error('FAIL: browser Back abandoned B draft without consent');
  await modal.getByRole('button',{name:'Rester sur ce dossier'}).click();
  if((await editor.inputValue())!==bSentinel)
    throw Error('FAIL: browser Back cancel lost real B draft');
  report.checks.push('REAL_BROWSER_BACK_SAME_PATIENT_TAB_DRAFT_GUARD');

  await backToList.click();
  await modal.waitFor({state:'visible'});
  await modal.getByRole('button',{name:'Quitter sans sauvegarder'}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/patients');
  const patientA=page.getByText('T2-0001',{exact:true}).first();
  await patientA.waitFor({state:'visible',timeout:30000});
  await patientA.click();
  await page.waitForURL(url=>new URL(url).pathname==='/patients/'+a,{timeout:30000});
  await page.locator('[data-tour="patient-tabs"]').getByRole('button',{name:'Document',exact:true}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/patients/'+a
    && new URL(url).searchParams.get('tab')==='admin',{timeout:15000});
  await page.locator('[data-tour="tab-libre"]').click();
  await editor.waitFor({state:'visible',timeout:30000});
  if((await editor.inputValue()).includes(syntheticSentinel) || (await editor.inputValue()).includes(bSentinel))
    throw Error('FAIL: A or B draft reappeared on A after A->B->A');
  report.checks.push('REAL_A_TO_B_TO_A_CLEAN_AFTER_EXPLICIT_DISCARD');
  if(pageErrors.length)throw Error('FAIL: browser reported JS exceptions ('+pageErrors.length+')');
  report.checks.push('NO_BROWSER_JS_ERRORS');

  report.status='PASS_TARGETED_REAL_CABINET_FUE_I_T2';
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  console.log('R2_T2_REAL_CABINET_UI_PASS',JSON.stringify({head,checks:report.checks,status:report.status}));
} finally {
  await context?.close();
  await browser.close();
  await api.dispose();
}
