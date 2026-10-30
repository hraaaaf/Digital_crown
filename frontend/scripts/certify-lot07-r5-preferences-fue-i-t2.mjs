// LOT07 R5/07-D — real React browser + authenticated FastAPI T2 SQLite FUE-I.
// Synthetic accounts/clinic ONLY. PostgreSQL migration certified separately.
// No production feature activation; no direct writes to clinical patient records.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const sha = process.env.EVALUATED_SHA;
const password = process.env.T2_PASSWORD;
assert.match(sha || '', /^[a-f0-9]{40}$/);
assert.ok(password && process.env.ENVIRONMENT === 'test' &&
  process.env.DIGITALCROWN_ISOLATED_RUNTIME === '1' &&
  process.env.VITE_V15_07_R4_SIGNATURE_LAB === 'true' &&
  process.env.VITE_V15_07_R5_PREFS_LAB === 'true',
  'Real isolated R5 FUE opt-ins are mandatory');
const apiBase = 'http://127.0.0.1:8005';
const uiBase = 'http://127.0.0.1:5173';
const route = '/api/workstation/r5-preferences';
const output = path.resolve('../artifacts/lot07-r5-prefs-fue-i');
await fs.mkdir(output,{recursive:true});
const report = {sha,lab:'ACTUAL_BROWSER_FASTAPI_T2_SQLITE',postgresqlE2E:false,
  syntheticOnly:true,backendMocked:false,production:false,
  humanVisualApproval:false,pass:false,checks:[],error:null};
const checked = (name,details={}) => report.checks.push({name,...details});
const browser = await chromium.launch({headless:true});
const provisioning = await request.newContext({baseURL:apiBase});
const getToken = async email => {
  const response=await provisioning.post('/api/auth/login',{
    form:{username:email,password}});
  assert.equal(response.status(),200,'JWT login for synthetic actor');
  const token=(await response.json()).access_token;
  assert.ok(token);
  return token;
};
const as = async(token,cookies=[]) => request.newContext({
  baseURL:apiBase,extraHTTPHeaders:{Authorization:'Bearer '+token},
  storageState:{cookies,origins:[]},
});
const screenshot = (page,name) => page.screenshot({
  path:path.join(output,name+'.png'),fullPage:true,animations:'disabled'});
const ownerEmail='t2-browser@cabinet.ma';
const staffEmail='t2-restricted@cabinet.ma';
let ownerCookie;
async function visit(email,cookie,phase) {
  const ctx=await browser.newContext({
    viewport:{width:1440,height:900},reducedMotion:'reduce',
    serviceWorkers:'block',storageState:{cookies:[cookie],origins:[]}});
  const page=await ctx.newPage();
  await page.goto(uiBase+'/login',{waitUntil:'domcontentloaded',timeout:90000});
  await page.locator('input[type=email]').fill(email);
  await page.locator('input[type=password]').fill(password);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL(url=>new URL(url).pathname==='/dashboard',{timeout:60000});
  const panel=page.locator('[data-testid="r5-signature-prefs"]');
  await panel.waitFor({state:'visible',timeout:40000});
  await screenshot(page,phase+'-before');
  return {ctx,page,panel};
}
try {
  const ownerToken=await getToken(ownerEmail);
  const enrolled=await enrollT2Workstation(provisioning,ownerToken,password);
  ownerCookie=enrolled.cookies.find(x=>x.name==='dc_workstation');
  assert.ok(ownerCookie,'Real HttpOnly workstation cookie required');
  const ownerAPI=await as(ownerToken,[ownerCookie]);
  const first=await ownerAPI.get(route);
  assert.equal(first.status(),200);
  assert.deepEqual(await first.json(),{record:null,revision:0,canRollback:false});
  checked('A-first-use-empty-revision-zero');

  const a=await visit(ownerEmail,ownerCookie,'A-01');
  assert.equal(await a.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
  await a.panel.getByRole('button',{name:'Signature Iconic'}).click();
  assert.equal(await a.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core',
    'Draft cannot silently activate before preview');
  await a.panel.getByRole('button',{name:'Aperçu'}).click();
  assert.equal(await a.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
  await screenshot(a.page,'A-02-preview');
  await a.panel.getByRole('button',{name:'Annuler'}).click();
  assert.equal(await a.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
  assert.equal((await ownerAPI.get(route)).status(),200);
  assert.equal((await (await ownerAPI.get(route)).json()).revision,0);
  checked('preview-cancel-without-write');

  await a.panel.getByRole('button',{name:'Signature Iconic'}).click();
  const savedResponse=a.page.waitForResponse(r=>r.url().includes(route) &&
    r.request().method()==='PUT',{timeout:30000});
  await a.panel.getByRole('button',{name:'Appliquer et enregistrer'}).click();
  assert.equal((await savedResponse).status(),200);
  const saved=await (await ownerAPI.get(route)).json();
  assert.equal(saved.revision,1);
  assert.equal(saved.record.signature,'iconic');
  assert.equal(saved.record.workstationId.length>0,true);
  assert.equal(saved.record.layout,null);
  for(const key of ['patientId','token','patientName','patient','medical'])
    assert.ok(!Object.hasOwn(saved.record,key),'Sensitive field not persisted: '+key);
  await screenshot(a.page,'A-03-applied');
  // Exact-SHA real authenticated responsive screenshots, not a MultiView
  // certification or human visual approval.
  for (const width of [390,430,768,1280]) {
    await a.page.setViewportSize({width,height:900});
    const rect=await a.panel.boundingBox();
    assert.ok(rect && rect.x>=-1 && rect.x+rect.width<=width+1,
      'R5 signature panel exceeds viewport at '+width);
    assert.equal(await a.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
    await screenshot(a.page,'A-03-applied-'+width);
    checked('responsive-R5-signature-'+width+'px',{width});
  }
  await a.page.setViewportSize({width:1440,height:900});
  await a.page.reload({waitUntil:'domcontentloaded'});
  await a.page.locator('[data-testid="r5-signature-prefs"]').waitFor({timeout:30000});
  assert.equal(await a.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
  checked('apply-persist-reload-with-real-browser-and-api');

  // Genuine R5 MultiView on an authenticated, synthetic patient route:
  // visual evidence only; no clinical write and no production activation.
  assert.equal(process.env.VITE_V15_07_1_MULTIVIEW_LAB,'1');
  const peopleResponse=await ownerAPI.get('/api/patients/');
  assert.equal(peopleResponse.status(),200);
  const people=await peopleResponse.json();
  const fixture=people.find(p=>p.numero_dossier==='T2-0001');
  assert.ok(Number.isSafeInteger(fixture?.id)&&fixture.id>0);
  const patientMediaPath='/patients/'+fixture.id+'?tab=radiology&radioTab=media';
  await a.page.setViewportSize({width:1440,height:900});
  await a.page.goto(uiBase+patientMediaPath,{
    waitUntil:'domcontentloaded',timeout:90000});
  await a.page.locator('[data-testid="r5-multiview-prefs"]')
    .waitFor({state:'visible',timeout:60000});
  assert.equal(await a.page.locator('[data-lot07-polish02]').getAttribute('data-lot07-polish02'),
    'clinical-first','POLISH-02 must remain gated to the DEV workstation lab');
  // At 1440 CSS px, the trusted inner workspace can be <1280 after the
  // sidebar/patient shell. Accept ONLY the existing read-only safety fallback,
  // never force an unreadable two-pane dossier just to pass a visual gate.
  const dossier1440=a.page.locator('[data-v15-071-viewslot="dossier"]');
  const safeFallback1440=a.page.locator('[data-testid="multiview-responsive-single-media-fallback"]');
  const twoPanes1440=await dossier1440.count()===1;
  assert.ok(twoPanes1440 || await safeFallback1440.isVisible(),
    '1440px must show either the authorized clinical layout or its safe fallback');
  const clinical1440 = await (twoPanes1440 ? dossier1440 : safeFallback1440).boundingBox();
  assert.ok(clinical1440 && clinical1440.x >= -1 &&
    clinical1440.x + clinical1440.width <= 1441,
    'Real 1440px safe clinical content must stay in the viewport');
  await screenshot(a.page,'R5-MultiView-desktop-before-1440');
  checked('polish02-real-authenticated-clinical-first-1440', {
    width:1440,clinicalTop:Math.round(clinical1440.y),
    layout:twoPanes1440 ? 'verified-two-pane' : 'read-only-safe-fallback'});
  await a.page.setViewportSize({width:1920,height:1080});
  await a.page.goto(uiBase+patientMediaPath,{
    waitUntil:'domcontentloaded',timeout:90000});
  const layoutPanel=a.page.locator('[data-testid="r5-multiview-prefs"]');
  await layoutPanel.waitFor({state:'visible',timeout:60000});
  assert.match(await layoutPanel.innerText(),/Disposition du cabinet/);
  assert.equal(await a.page.locator('[data-v15-071-viewslot]').count(),2);
  // R5 persistence must be the sole visible disposition selector on desktop;
  // R3's independent view-exchange control remains accessible.
  assert.equal(await a.page.locator('select[aria-label="Disposition MultiView"]').isVisible(),
    false,'Duplicate R3 layout selector visible');
  assert.equal(await a.page.locator('[data-testid="multiview-legacy-selection"]').isVisible(),
    false,'Duplicate R3 preview/apply buttons visible');
  assert.equal(await a.page.locator('[data-testid="multiview-legacy-help"]').isVisible(),
    false,'Misleading R3 non-persisted copy visible alongside R5 persistence');
  assert.equal(await a.page.getByRole('button',{name:'Échanger les vues'}).isVisible(),
    true,'R3 view-exchange must remain available');
  checked('single-visible-r5-disposition-retains-r3-view-tools');
  // POLISH-02 theme contract: inspect computed styles on the actual authenticated
  // patient rails, not just CSS source tokens or unrelated R3 frames.
  const themeAudit=await a.page.evaluate(()=>{
    const themes=['default','emerald','rose','ocean','graphite','prestige','dark','high-contrast'];
    const root=document.documentElement;
    const original=root.getAttribute('data-theme');
    const signature=document.querySelector('[data-testid="r5-signature-prefs"]');
    const multiview=document.querySelector('[data-testid="r5-multiview-prefs"]');
    const button=document.querySelector('[data-testid="r5-multiview-toggle"]');
    if(!signature||!multiview||!button)throw Error('Missing actual POLISH-02 rails');
    const results=[];
    try{
      for(const theme of themes){
        root.setAttribute('data-theme',theme);
        const tokens=getComputedStyle(root);
        const sig=getComputedStyle(signature);
        const mv=getComputedStyle(multiview);
        const focus=getComputedStyle(button);
        const primary=tokens.getPropertyValue('--primary').trim();
        const bg=tokens.getPropertyValue('--bg-medical-pearl').trim();
        const text=tokens.getPropertyValue('--text-main').trim();
        if(!primary||!bg||!text)throw Error('Missing semantic tokens: '+theme);
        if(sig.backgroundColor!==mv.backgroundColor)
          throw Error('Signature/MultiView rail theme mismatch: '+theme);
        if(focus.color!==sig.color)
          throw Error('Preference action text does not inherit theme: '+theme);
        results.push({theme,bg:tokens.getPropertyValue('--bg-medical-pearl').trim(),
          rail:sig.backgroundColor,text:sig.color,focus:focus.outlineColor});
      }
    }finally{
      if(original===null)root.removeAttribute('data-theme');
      else root.setAttribute('data-theme',original);
    }
    if(new Set(results.map(x=>x.rail)).size<4)
      throw Error('Theme rails did not change computed background across themes');
    return results;
  });
  assert.equal(themeAudit.length,8);
  checked('polish02-eight-themes-real-rails-inherit-semantic-tokens',themeAudit);

  // Clinical-first: both preference panels start compact on a genuine patient
  // dossier, retain a keyboard-accessible, explicit way to reopen them, and
  // reclaim meaningful vertical room for the real read-only clinical slots.
  const signatureToggle=a.page.locator('[data-testid="r5-signature-toggle"]');
  const multiToggle=layoutPanel.locator('[data-testid="r5-multiview-toggle"]');
  assert.equal(await signatureToggle.getAttribute('aria-expanded'),'false');
  assert.equal(await multiToggle.getAttribute('aria-expanded'),'false');
  assert.equal(await layoutPanel.getByRole('combobox',{name:'Disposition R5'}).count(),0);
  const clinicalOffset=()=>a.page.evaluate(()=>{
    const a=document.querySelector('[data-testid="r5-signature-prefs"]');
    const b=document.querySelector('[data-v15-071-viewslot="dossier"]');
    if(!a||!b)throw Error('Missing authenticated clinical landmark');
    return Math.round(b.getBoundingClientRect().top-a.getBoundingClientRect().top);
  });
  const compactOffset=await clinicalOffset();
  await screenshot(a.page,'R5-MultiView-desktop-before-1920');
  await signatureToggle.click();
  await multiToggle.click();
  assert.equal(await signatureToggle.getAttribute('aria-expanded'),'true');
  assert.equal(await multiToggle.getAttribute('aria-expanded'),'true');
  const expandedOffset=await clinicalOffset();
  assert.ok(expandedOffset-compactOffset>=120,
    'Compact preference panels must recover at least 120 CSS pixels above clinical content');
  checked('desktop-clinical-first-reclaimed-height-1920',
    {compactOffset,expandedOffset,reclaimedPx:expandedOffset-compactOffset});
  await screenshot(a.page,'R5-MultiView-desktop-expanded-1920');
  // POLISH-02 accessibility: measured computed-color ratios on REAL R5 controls.
  // Includes alpha composition; no assumption that inherited tokens prove contrast.
  const wcagAudit=await a.page.evaluate(()=>{
    const themeNames=['default','emerald','rose','ocean','graphite','prestige','dark','high-contrast'];
    const root=document.documentElement, original=root.getAttribute('data-theme');
    const parse=s=>{
      const m=String(s).match(/^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s\/]+([\d.]+))?\s*\)$/);
      return m?[Number(m[1]),Number(m[2]),Number(m[3]),m[4]===undefined?1:Number(m[4])]:null;
    };
    const composite=(front,back)=>front.slice(0,3).map((v,i)=>v*front[3]+back[i]*(1-front[3]));
    const bgAt=node=>{
      const chain=[];for(let n=node;n;n=n.parentElement)chain.unshift(n);
      let bg=[255,255,255];
      for(const el of chain){const c=parse(getComputedStyle(el).backgroundColor);if(c)bg=composite(c,bg);}
      return bg;
    };
    const lum=c=>c.map(x=>x/255).map(x=>x<=0.04045?x/12.92:Math.pow((x+0.055)/1.055,2.4))
      .reduce((sum,x,i)=>sum+x*[0.2126,0.7152,0.0722][i],0);
    const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);};
    const signature=document.querySelector('[data-testid="r5-signature-prefs"]');
    const multiview=document.querySelector('[data-testid="r5-multiview-prefs"]');
    if(!signature||!multiview)throw Error('Missing real R5 rails for WCAG audit');
    const samples=[],failures=[];
    try{
      for(const theme of themeNames){
        root.setAttribute('data-theme',theme);
        const targets=[
          ['signature-heading',signature.querySelector('h2')],
          ['signature-description',signature.querySelector('p.text-text-muted')],
          ['signature-toggle',signature.querySelector('[data-testid="r5-signature-toggle"]')],
          ['signature-primary',signature.querySelector('button.bg-primary')],
          ['multiview-heading',multiview.querySelector('strong')],
          ['multiview-description',multiview.querySelector('span.text-text-muted')],
          ['multiview-toggle',multiview.querySelector('[data-testid="r5-multiview-toggle"]')],
          ['multiview-primary',multiview.querySelector('button.bg-primary')]
        ];
        for(const [name,el] of targets){
          if(!el||!el.getClientRects().length){
            failures.push({theme,name,reason:'missing-or-hidden'});continue;
          }
          if(el.matches(':disabled'))continue; // WCAG inactive-control exception.
          const s=getComputedStyle(el),fg=parse(s.color),bg=bgAt(el);
          if(!fg){failures.push({theme,name,reason:'unparseable-computed-color',color:s.color});continue;}
          const actual=ratio(composite(fg,bg),bg);
          const large=parseFloat(s.fontSize)>=24||
            (parseFloat(s.fontSize)>=18.66&&parseInt(s.fontWeight,10)>=700);
          const minimum=large?3:4.5;
          samples.push({theme,name,ratio:Number(actual.toFixed(2)),minimum});
          if(actual+0.001<minimum)failures.push({theme,name,ratio:Number(actual.toFixed(2)),minimum});
        }
        for(const name of ['r5-signature-toggle','r5-multiview-toggle']){
          const el=document.querySelector('[data-testid="'+name+'"]');
          el.focus();const s=getComputedStyle(el),c=parse(s.outlineColor);
          const bg=bgAt(el.parentElement);
          const actual=c?ratio(composite(c,bg),bg):0;
          const active=el.matches(':focus-visible')&&s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>=2;
          samples.push({theme,name:name+'-keyboard-focus',ratio:Number(actual.toFixed(2)),minimum:3,active});
          if(!active||actual+0.001<3)failures.push({theme,name:name+'-keyboard-focus',active,ratio:Number(actual.toFixed(2)),minimum:3});
        }
      }
    }finally{
      if(original===null)root.removeAttribute('data-theme');else root.setAttribute('data-theme',original);
    }
    return {samples,failures};
  });
  checked('polish02-wcag-actual-r5-eight-theme-contrast',
    {pass:wcagAudit.failures.length===0,samples:wcagAudit.samples,failures:wcagAudit.failures});
  // The keyboard tab establishes keyboard modality before :focus-visible checks;
  // pass/fail is not inferred from CSS tokens or zero-width outlines.
  const reflowResults=[];
  const measureReflow=()=>a.page.evaluate(()=>{
    const width=document.documentElement.clientWidth;
    const probes=['r5-signature-prefs','r5-signature-toggle','r5-multiview-prefs','r5-multiview-toggle'];
    const landmarks=probes.map(name=>{
      const el=document.querySelector('[data-testid="'+name+'"]');
      if(!el)return {name,present:false};
      const r=el.getBoundingClientRect();
      return {name,present:true,visible:r.width>0&&r.height>0,
        left:Math.round(r.left),right:Math.round(r.right),
        fits:r.left>=-2&&r.right<=width+2};
    });
    return {cssViewport:width,documentScrollWidth:document.documentElement.scrollWidth,landmarks,
      fallbackVisible:Boolean(document.querySelector('[data-testid="multiview-responsive-single-media-fallback"]'))};
  });
  try{
    await a.page.keyboard.press('Tab');
    await a.page.evaluate(()=>document.documentElement.style.setProperty('font-size','200%'));
    const enlarged=await measureReflow();
    reflowResults.push({mode:'200-percent-text-resize',...enlarged});
    await screenshot(a.page,'POLISH02-text-resize-200-percent');
    await a.page.evaluate(()=>document.documentElement.style.removeProperty('font-size'));
    // A 720px CSS layout represents 1440px/2 at 200% browser zoom.
    // This verifies responsive reflow, NOT a native browser-chrome zoom gesture.
    for(const width of [720,640]){
      await a.page.setViewportSize({width,height:900});
      const result=await measureReflow();
      reflowResults.push({mode:'half-width-200-percent-zoom-equivalent',referenceWidth:width*2,...result});
      await screenshot(a.page,'POLISH02-reflow-200-percent-'+width);
    }
  }finally{
    await a.page.evaluate(()=>document.documentElement.style.removeProperty('font-size'));
    await a.page.setViewportSize({width:1920,height:1080});
  }
  const reflowFailures=reflowResults.flatMap(result=>{
    const bad=result.landmarks.filter(el=>!el.present||!el.visible||!el.fits);
    if(result.documentScrollWidth>result.cssViewport+2)bad.push({name:'document-horizontal-overflow'});
    return bad.map(el=>({mode:result.mode,viewport:result.cssViewport,...el}));
  });
  checked('polish02-text-resize-and-200-percent-layout-reflow',
    {pass:reflowFailures.length===0,measurements:reflowResults,failures:reflowFailures});
  report.accessibility={contrastFailures:wcagAudit.failures,reflowFailures,
    caveat:'Half-width CSS layout is not native Chromium browser zoom; screenshots require human visual review.'};
  if(wcagAudit.failures.length||reflowFailures.length){
    throw Error('POLISH-02 ACCESSIBILITY BLOCKER: computed contrast / 200% reflow violations; see report.json');
  }

  // Return Signature to a compact summary; the MultiView editor remains open
  // so the next existing preview/cancel and isolation assertions stay genuine.
  await signatureToggle.click();
  checked('real-authenticated-r5-multiview-1920-visual-evidence');
  await layoutPanel.getByRole('combobox',{name:'Disposition R5'})
    .selectOption('dossier-media-2rows');
  await layoutPanel.getByRole('button',{name:'Aperçu',exact:true}).click();
  await layoutPanel.locator('[data-testid="r5-multiview-preview"]')
    .waitFor({state:'visible',timeout:15000});
  await screenshot(a.page,'R5-MultiView-desktop-preview-1920');
  assert.equal((await (await ownerAPI.get(route)).json()).revision,1);
  checked('r5-multiview-preview-does-not-persist');
  await a.ctx.close();

  // B is a different real authenticated user under the same tenant/station.
  const staffToken=await getToken(staffEmail);
  const staffAPI=await as(staffToken,[ownerCookie]);
  const staffEmpty=await staffAPI.get(route);
  assert.equal(staffEmpty.status(),200);
  assert.equal((await staffEmpty.json()).record,null,'A preferences must not appear in B');
  const forged=await staffAPI.put(route,{data:{expectedRevision:0,record:saved.record}});
  assert.equal(forged.status(),403,'B cannot write A scoped record');
  const b=await visit(staffEmail,ownerCookie,'B-01');
  assert.equal(await b.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'core');
  checked('A-to-B-same-workstation-no-data-leak',{forgedStatus:403});
  await b.ctx.close();

  // Same owner with another enrolled workstation must see a separate empty slot.
  const another=await request.newContext({baseURL:apiBase});
  const second=await enrollT2Workstation(another,ownerToken,password);
  const cookieB=second.cookies.find(x=>x.name==='dc_workstation');
  assert.ok(cookieB && cookieB.value!==ownerCookie.value,'Independent second workstation');
  const ownerStationB=await as(ownerToken,[cookieB]);
  const freshOnB=await ownerStationB.get(route);
  assert.equal(freshOnB.status(),200);
  assert.equal((await freshOnB.json()).record,null);
  const withoutStation=await as(ownerToken,[]);
  assert.equal((await withoutStation.get(route)).status(),423);
  checked('second-workstation-empty-and-unverified-423');
  await ownerStationB.dispose();await another.dispose();await withoutStation.dispose();

  // A returns with its own verified workstation and real UI hydration.
  const a2=await visit(ownerEmail,ownerCookie,'A-04-return');
  assert.equal(await a2.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
  await a2.panel.getByRole('button',{name:'Signature Core'}).click();
  const coreSave=a2.page.waitForResponse(r=>r.url().includes(route) &&
    r.request().method()==='PUT',{timeout:30000});
  await a2.panel.getByRole('button',{name:'Appliquer et enregistrer'}).click();
  assert.equal((await coreSave).status(),200);
  assert.equal((await (await ownerAPI.get(route)).json()).revision,2);
  const undo=a2.page.waitForResponse(r=>r.url().includes(route+'/rollback') &&
    r.request().method()==='POST',{timeout:30000});
  await a2.panel.getByRole('button',{name:'Rollback'}).click();
  assert.equal((await undo).status(),200);
  const restored=await (await ownerAPI.get(route)).json();
  assert.equal(restored.revision,3);
  assert.equal(restored.record.signature,'iconic');
  assert.equal(await a2.page.locator('[data-r4-signature]').getAttribute('data-r4-signature'),'iconic');
  await screenshot(a2.page,'A-05-rollback');
  checked('B-to-A-and-rollback-revision-three');

  const stale=await ownerAPI.put(route,{data:{expectedRevision:1,record:saved.record}});
  assert.equal(stale.status(),409);
  const leaked=await ownerAPI.put(route,{data:{
    expectedRevision:3,record:{...saved.record,patientId:999999}}});
  assert.equal(leaked.status(),422);
  const finalState=await (await ownerAPI.get(route)).json();
  assert.equal(finalState.revision,3);
  assert.equal(finalState.record.signature,'iconic');
  checked('negative-stale-409-and-PHI-422-no-mutation');
  await a2.ctx.close();
  await ownerAPI.dispose();await staffAPI.dispose();
  report.pass=report.checks.length>=7;
} catch(e) {
  report.error=String(e?.stack||e);
  throw e;
} finally {
  await provisioning.dispose();
  await browser.close();
  await fs.writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
  console.log('LOT07_R5_FUE_I_RESULT',JSON.stringify({
    sha,pass:report.pass,checks:report.checks.length,error:report.error}));
}
