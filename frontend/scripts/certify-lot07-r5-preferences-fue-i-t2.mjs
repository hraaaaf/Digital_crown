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
  await a.page.setViewportSize({width:1920,height:1080});
  await a.page.goto(uiBase+'/patients/'+fixture.id+'?tab=radiology&radioTab=media',{
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
  await screenshot(a.page,'R5-MultiView-desktop-before-1920');
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
