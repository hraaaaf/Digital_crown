import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const out = path.resolve('artifacts/v15-05-5-gateway');
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const viewports = [
  { label: '390x844', width: 390, height: 844 },
  { label: '768x1024', width: 768, height: 1024 },
  { label: '1280x900', width: 1280, height: 900 },
];
const preflight = {
  status:'construction', schema_revision_matches:true,
  declared_subset_matches:true, physical_subset_checked:true,
  full_schema_certified:false, authenticated_cabinet_scope:true,
  dry_run_real_data_available:false, import_permitted:false,
  blockers:['REAL_IMPORT_NOT_IMPLEMENTED'],
  target_preview:{schema_revision:'observed-read-only:neo000000027',
    tables:[{name:'patients',columns:[{name:'nom'},{name:'prenom'}]}]},
};
const report = {
  mode:'SYNTHETIC_MEMORY_ONLY',
  source_patients:100, source_appointments:200,
  verified_patients:100, verified_appointments:200, verified_patient_links:200,
  orphan_appointments:0, cross_tenant_links:0,
  after_rollback_patients:0, after_rollback_appointments:0,
  cabinet_rows_read:false, cabinet_rows_written:false,
  schema_migrated_by_alembic:false, import_permitted:false,
};
const cases = [];
try {
  for (const vp of viewports) {
    const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
    const page=await context.newPage();
    const errors=[], unexpected=[];
    page.on('pageerror',e=>errors.push(e.message));
    await context.route('**/*', route=>{
      const u=new URL(route.request().url());
      if(u.pathname==='/api/migration/preflight' && route.request().method()==='GET'){
        return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(preflight)});
      }
      if(u.pathname==='/api/migration/synthetic-rehearsal' && route.request().method()==='POST'){
        return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(report)});
      }
      if(u.hostname==='127.0.0.1' && u.port==='4196' && !u.pathname.startsWith('/api/')){
        return route.continue();
      }
      if(['fonts.googleapis.com','fonts.gstatic.com'].includes(u.hostname)){
        return route.abort();
      }
      unexpected.push(u.origin+u.pathname.slice(0,90));
      return route.abort();
    });
    await page.goto('http://127.0.0.1:4196/migration-preview.html?filled=0',{waitUntil:'networkidle'});
    await page.getByRole('heading',{name:'Correspondances de données'}).waitFor();
    const before=await page.evaluate(()=>({
      width:document.documentElement.clientWidth,
      scroll:document.documentElement.scrollWidth,
      importEnabled:!!document.querySelector('button:not([disabled])[aria-label*="Importer"]')
    }));
    await page.screenshot({path:path.join(out,'BEFORE-'+vp.label+'.png'),fullPage:true,animations:'disabled'});
    await page.getByRole('button',{name:'Contrôler le serveur sécurisé'}).click();
    await page.getByText(/Sous-ensemble de tables et révision vérifiés/).waitFor();
    await page.getByRole('button',{name:/Simuler 100 patients/}).click();
    await page.getByText(/Simulation fictive : 100\/100/).waitFor();
    const after=await page.evaluate(()=>({
      width:document.documentElement.clientWidth,
      scroll:document.documentElement.scrollWidth,
      noLivePatientData:!document.body.textContent?.includes('PATIENT IDENTIFIABLE'),
      importEnabled:!!document.querySelector('button:not([disabled])[aria-label*="Importer"]')
    }));
    await page.screenshot({path:path.join(out,'AFTER-'+vp.label+'.png'),fullPage:true,animations:'disabled'});
    if(before.scroll>before.width+1||after.scroll>after.width+1||after.importEnabled||before.importEnabled||
       !after.noLivePatientData||errors.length||unexpected.length){
      throw new Error('GATEWAY_VISUAL_FAILED:'+JSON.stringify({vp,before,after,errors,unexpected}));
    }
    cases.push({vp:vp.label,before,after,errors,unexpected});
    await context.close();
  }
} finally {await browser.close();}
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({
 head:process.env.GITHUB_SHA||null,
 mode:'mocked API only; no actual backend JWT, cabinet DB, or staff session',
 previousPR:'https://github.com/hraaaaf/Digital_crown/pull/854',
 cases,
},null,2));
console.log(JSON.stringify(cases,null,2));
