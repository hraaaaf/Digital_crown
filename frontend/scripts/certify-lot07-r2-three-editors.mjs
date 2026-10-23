/**
 * LOT07 R2 FUE-I expansion: actual Prescription, Certificate and Honoraires.
 * Real Chromium + FastAPI but strictly disposable T2 and synthetic users.
 * No save, print, generate, upload or clinical production operations.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head=process.env.PRODUCT_HEAD;
const password=process.env.T2_PASSWORD;
const a=Number(process.env.R2_T2_PATIENT_A_ID);
const b=Number(process.env.R2_T2_PATIENT_B_ID);
if (process.env.ENVIRONMENT!=='test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1' ||
    process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db' ||
    !/^[0-9a-f]{40}$/.test(head||'') || !password ||
    !Number.isSafeInteger(a) || !Number.isSafeInteger(b) ||
    a<=0 || b<=0 || a===b) {
  throw Error('REFUSED: R2 multi-editor certification requires disposable exact-HEAD T2');
}
const app='http://127.0.0.1:5173';
const out=path.resolve('../artifacts/lot07-r2-real-cabinet');
const report={head,environment:'DISPOSABLE_T2_THREE_CLINICAL_EDITORS',syntheticOnly:true,clinicalRelease:false,checks:[]};
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const browser=await chromium.launch({headless:true});
let ctx;
try {
  const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
  if(login.status()!==200)throw Error('FAIL: synthetic owner auth');
  const token=(await login.json()).access_token;
  const ownerState=await enrollT2Workstation(api,token,password);
  const ws=ownerState.cookies.filter(c=>c.name==='dc_workstation');
  if(ws.length!==1 || ws[0].httpOnly!==true)throw Error('FAIL: no unique enrolled T2 workstation');
  ctx=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce',storageState:{cookies:ws,origins:[]}});
  const page=await ctx.newPage();
  const jsErrors=[];
  page.on('pageerror',e=>jsErrors.push(e.message));
  await page.goto(app+'/hub?select=1',{waitUntil:'domcontentloaded',timeout:45000});
  await page.locator('[data-hub-experience="cabinet"]').click();
  await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:45000});
  report.checks.push('THREE_EDITORS_REAL_OWNER_LOGIN_AND_WORKSTATION');

  const modal=page.getByRole('alertdialog',{name:'Brouillon non enregistré'});
  const back=page.getByRole('button',{name:'Retourner à la liste des patients'});
  const switchEditor=async(patientId,tab)=>{
    await page.goto(app+'/patients/'+patientId+'?tab=admin',{waitUntil:'domcontentloaded',timeout:45000});
    await page.locator('[data-tour="tab-'+tab+'"]').waitFor({state:'visible',timeout:45000});
    await page.locator('[data-tour="tab-'+tab+'"]').click();
  };
  const exercise=async ({type, tab, edit, read, clean})=>{
    await switchEditor(a,tab);
    await edit();
    if(!await read())throw Error('FAIL: '+type+' edited value did not appear in real clinical editor');

    await back.click();
    await modal.waitFor({state:'visible',timeout:20000});
    // An open alertdialog correctly blocks interaction with the background
    // treasury modal. Verify Honoraires's live mode immediately AFTER Stay;
    // other editors expose their textarea behind the dialog and can be read.
    const visibleDraft=type==='HONORAIRES_PAYMENT_ONLY' ? true : await read();
    if(new URL(page.url()).pathname!=='/patients/'+a || !visibleDraft)
      throw Error('FAIL: '+type+' route switched or lost draft before consent');
    await modal.getByRole('button',{name:'Rester sur ce dossier'}).click();
    await modal.waitFor({state:'hidden',timeout:15000});
    if(!await read())throw Error('FAIL: '+type+' Stay lost unsaved draft');
    report.checks.push(type+'_STAY_PRESERVES_REAL_DRAFT');

    await back.click();
    await modal.waitFor({state:'visible',timeout:20000});
    await modal.getByRole('button',{name:'Quitter sans sauvegarder'}).click();
    await page.waitForURL(u=>new URL(u).pathname==='/patients',{timeout:20000});
    report.checks.push(type+'_EXPLICIT_DISCARD_BEFORE_LEAVE');

    // Reload on B is intentional: the sensitive state must not leak even
    // after a fresh React load. No store/DevTools mutation in this browser.
    await switchEditor(b,tab);
    if(!await clean())throw Error('FAIL: '+type+' A draft visible in B');
    report.checks.push(type+'_B_EMPTY');

    await switchEditor(a,tab);
    if(!await clean())throw Error('FAIL: '+type+' A draft reappeared after discard');
    report.checks.push(type+'_A_CLEAN_AFTER_RETURN');
  };

  const prescription=page.getByRole('textbox',{name:'Indication de cette ordonnance'});
  const px='R2_T2_ORDONNANCE_SYNTHETIC_UNSAVED';
  await exercise({
    type:'PRESCRIPTION',tab:'ordonnance',
    edit:async()=>{await prescription.waitFor({state:'visible'});await prescription.fill(px);},
    read:async()=>(await prescription.inputValue())===px,
    clean:async()=>{await prescription.waitFor({state:'visible'});return (await prescription.inputValue())==='';},
  });

  const certificate=page.locator('textarea[placeholder^="Rédigez librement le contenu certifié"]');
  const cx='R2_T2_CERTIFICAT_SYNTHETIC_UNSAVED';
  const ensureCert=async()=>{
    await page.getByRole('button',{name:'Certificat médical',exact:true}).first().click();
    await certificate.waitFor({state:'visible',timeout:15000});
  };
  await exercise({
    type:'CERTIFICATE',tab:'certificat',
    edit:async()=>{await ensureCert();await certificate.fill(cx);},
    read:async()=>(await certificate.inputValue())===cx,
    clean:async()=>{await ensureCert();return (await certificate.inputValue())==='';},
  });

  // Honest minimal-note scenario: no act line exists; changing payment mode
  // must still count as an unsaved Honoraires draft.
  // The Studio footer ALSO exposes a "Virement" button. Only target the
  // actual treasury dialog, never an unrelated footer control.
  const treasury=page.locator('div.fixed').filter({
    has:page.getByRole('heading',{name:'Encaissement',exact:true}),
  });
  const mode=treasury.getByRole('button',{name:'Virement',exact:true});
  const openTreasury=async()=>{
    await page.getByRole('button',{name:/Échéances & options/i}).click();
    await mode.waitFor({state:'visible'});
  };
  const selected=async()=>(await mode.getAttribute('class')||'').includes('bg-white text-slate-800');
  await exercise({
    type:'HONORAIRES_PAYMENT_ONLY',tab:'honoraires',
    edit:async()=>{
      await openTreasury();
      await mode.click();
      if(!await selected())throw Error('FAIL: Honoraires payment not selected');
      await page.getByRole('button',{name:'Appliquer à la note'}).click();
    },
    read:async()=>{
      await openTreasury();
      const ok=await selected();
      await page.getByRole('button',{name:'Fermer',exact:true}).click();
      return ok;
    },
    clean:async()=>{
      await openTreasury();
      const clean=!await selected();
      await page.getByRole('button',{name:'Fermer',exact:true}).click();
      return clean;
    },
  });

  if(jsErrors.length)throw Error('FAIL: JavaScript runtime errors: '+jsErrors.length);
  report.checks.push('THREE_EDITORS_NO_JS_ERRORS');
  report.status='PASS_R2_THREE_REAL_EDITORS_T2';
  await fs.mkdir(out,{recursive:true});
  await fs.writeFile(path.join(out,'three-editors.json'),JSON.stringify(report,null,2));
  console.log('LOT07_R2_THREE_EDITORS_T2_PASS',JSON.stringify({head,status:report.status,checks:report.checks}));
} finally {
  await ctx?.close();
  await browser.close();
  await api.dispose();
}
