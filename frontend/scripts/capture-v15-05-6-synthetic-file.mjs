import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const dest=path.resolve('artifacts/v15-05-6-file');
await fs.mkdir(dest,{recursive:true});
const browser=await chromium.launch({headless:true});
const demo=Buffer.alloc(2048,0);
Buffer.from('SQLite format 3\0').copy(demo,0);
const good={
 status:'construction',schema_revision_matches:true,
 declared_subset_matches:true,physical_subset_checked:true,
 full_schema_certified:false,authenticated_cabinet_scope:true,
 dry_run_real_data_available:false,import_permitted:false,
 blockers:['REAL_IMPORT_NOT_IMPLEMENTED'],
 target_preview:{schema_revision:'observed-read-only:neo000000027',
 tables:[{name:'patients',columns:[{name:'nom'}]}]},
};
const result={
 mode:'OFFICIAL_SYNTHETIC_SQLITE_FILE_ONLY',
 source_sha256:createHash('sha256').update(demo).digest('hex'),source_patients:100,source_appointments:200,
 verified_patients:100,verified_appointments:200,verified_patient_links:200,
 orphan_appointments:0,cross_tenant_links:0,
 after_rollback_patients:0,after_rollback_appointments:0,
 source_persisted:false,cabinet_rows_read:false,cabinet_rows_written:false,
 import_permitted:false,
};
const cases=[];
try{
 for(const vp of [
   {name:'390x844',width:390,height:844,scale:100},
   {name:'430x932',width:430,height:932,scale:100},
   {name:'768x1024',width:768,height:1024,scale:100},
   {name:'1280x900',width:1280,height:900,scale:100},
   {name:'390x844-text200',width:390,height:844,scale:200},
   {name:'430x932-text200',width:430,height:932,scale:200},
   {name:'768x1024-text200',width:768,height:1024,scale:200},
   {name:'1280x900-text200',width:1280,height:900,scale:200},
 ]){
  const ctx=await browser.newContext({viewport:{width:vp.width,height:vp.height},acceptDownloads:true});
  const page=await ctx.newPage();
  const errors=[],unexpected=[],serverRequests=[];
  page.on('pageerror',e=>errors.push(e.message));
  await ctx.route('**/*',route=>{
    const u=new URL(route.request().url()), method=route.request().method();
    if(u.pathname==='/api/migration/preflight' && method==='GET'){
      serverRequests.push('preflight');
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(good)});
    }
    if(u.pathname==='/api/migration/synthetic-fixture' && method==='GET'){
      serverRequests.push('fixture');
      return route.fulfill({status:200,contentType:'application/vnd.sqlite3',body:demo});
    }
    if(u.pathname==='/api/migration/synthetic-file-dryrun' && method==='POST'){
      serverRequests.push('dryrun');
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(result)});
    }
    if(u.hostname==='127.0.0.1' && u.port==='4197' && !u.pathname.startsWith('/api/'))return route.continue();
    if(['fonts.googleapis.com','fonts.gstatic.com'].includes(u.hostname))return route.abort();
    unexpected.push(u.origin+u.pathname);
    return route.abort();
  });
  // Vite's isolated CI browser can see a transient module warm-up page.
  // Fail closed after bounded navigation retries, preserving every page error
  // and unexpected network request as an eventual hard failure.
  let ready=false, loadIssue='';
  for(let attempt=1;attempt<=3;attempt++){
    try {
      await page.goto('http://127.0.0.1:4197/migration-preview.html?filled=0',
                      {waitUntil:'networkidle'});
      await page.getByRole('heading',{name:'Mapping Studio'}).waitFor({timeout:10000});
      ready=true;
      break;
    } catch (cause) {
      loadIssue=String(cause);
    }
  }
  if(!ready){
    const visible=await page.locator('body').innerText().catch(()=>'unavailable');
    throw new Error('MAPPING_PREVIEW_NOT_READY:'+JSON.stringify({
      viewport:vp.name,url:page.url(),visible:visible.slice(0,900),
      errors,unexpected,loadIssue,
    }));
  }
  // CSS root text scaling (not a claim of native browser zoom or physical device testing).
  if(vp.scale===200) await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
  const alert=page.getByRole('note',{name:'Limites de certification'});
  await alert.getByText('Import réel interdit.').waitFor();
  if(await alert.innerText().then(t=>t.includes('**entièrement fictive'))) {
    throw new Error('UNRENDERED_MARKDOWN_IN_WARNING:'+vp.name);
  }
  const details=alert.locator('details');
  if(!await details.count()) throw new Error('WARNING_DETAILS_MISSING:'+vp.name);
  const before=await page.evaluate(()=>({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));
  await page.screenshot({path:path.join(dest,'BEFORE-'+vp.name+'.png'),fullPage:true,animations:'disabled'});
  await page.getByRole('button',{name:'Contrôler le backend sécurisé'}).click();
  await page.getByRole('button',{name:'Télécharger la base SQLite fictive'}).click();
  const fileInput=page.getByLabel('Fichier SQLite fictif Digital Crown');
  await fileInput.waitFor();
  // The file input is visible but DISABLED until the async fixture download
  // finishes and the local expected SHA is stored in React state.
  await page.waitForFunction(() => {
    const field=document.querySelector('input[aria-label="Fichier SQLite fictif Digital Crown"]');
    return field instanceof HTMLInputElement && !field.disabled;
  });
  await fileInput.setInputFiles({name:'digital-crown-synthetic-100x200.db',
    mimeType:'application/vnd.sqlite3',buffer:demo});
  try {
    await page.getByText(/Fichier SQLite fictif vérifié : 100\/100/).waitFor({timeout:12000});
  } catch (cause) {
    const status=await page.evaluate(()=>document.body.innerText.slice(0,1800));
    throw new Error('SYNTHETIC_FILE_UI_DEBUG:'+JSON.stringify({vp:vp.name,
      serverRequests,errors,unexpected,status,cause:String(cause)}));
  }
  const after=await page.evaluate(()=>({width:document.documentElement.clientWidth,
    scroll:document.documentElement.scrollWidth,importLocked:document.body.textContent?.includes('Import bloqué')}));
  await page.screenshot({path:path.join(dest,'AFTER-'+vp.name+'.png'),fullPage:true,animations:'disabled'});
  if(before.scroll>before.width+1||after.scroll>after.width+1||
    !after.importLocked||errors.length||unexpected.length||
    serverRequests.join(',')!=='preflight,fixture,dryrun'){
    throw new Error('FAIL_CLOSED_SYNTHETIC_UI:'+JSON.stringify({vp,before,after,errors,unexpected,serverRequests}));
  }
  cases.push({viewport:vp.name,textScalePercent:vp.scale,before,after,serverRequests,errors,unexpected});
  await ctx.close();
 }
}finally{await browser.close();}
await fs.writeFile(path.join(dest,'manifest.json'),JSON.stringify({
 head:process.env.GITHUB_SHA||null,
 note:'Fixture and API mocked in browser; 200% cases use CSS root font scaling, not browser zoom; not live staff JWT or actual SQLite parsing proof',
 cases,
},null,2));
console.log(JSON.stringify(cases,null,2));
