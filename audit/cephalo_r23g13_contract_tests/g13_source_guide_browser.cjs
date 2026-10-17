/* G13: real Chromium on hash-locked public JPEGs, anatomy guide/HOLD behavior. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.G12_PLAYWRIGHT_MODULE||'playwright');

(async()=>{
 const base=process.env.G12_URL||'http://127.0.0.1:8765/';
 const out=process.env.G13_EVIDENCE_DIR||'/tmp/dc-g13-browser-evidence';
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try {
  for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
   const ctx=await browser.newContext({viewport,acceptDownloads:false});
   const page=await ctx.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   page.on('request',req=>{if(!req.url().startsWith(base)&&!req.url().startsWith('blob:'))errors.push('nonlocal '+req.url());});
   await page.goto(base,{waitUntil:'load'});
   assert.equal(await page.locator('[data-testid=landmark] option').count(),21);
   assert.equal(await page.locator('[data-testid=guide-source]').count(),1);
   const ids=await page.evaluate(()=>{
     return G13_GUIDE.rows.map(r=>r.id);
   });
   assert.equal(ids.length,21);
   assert.equal(new Set(ids).size,21);
   assert.equal(await page.locator('#scan').getAttribute('href'),'images/anug.jpg');
   await page.locator('[data-testid=operator]').fill('synthetic_sourceguide_ci');
   // A source concept without an operational pixel rule must refuse clicks.
   await page.locator('[data-testid=landmark]').selectOption('Ba');
   assert.equal(await page.locator('[data-testid=guide-status]').getAttribute('data-hold'),'true');
   assert.match(await page.locator('[data-testid=guide-source]').textContent(),/CEPHALO_LOT08_RICKETTS_GREGORET13_SOURCE_LOCK/);
   let box=await page.locator('#tracing').boundingBox();
   await page.mouse.click(box.x+box.width*.25,box.y+box.height*.20);
   assert.equal(await page.locator('#markers circle').count(),0);
   assert.match(await page.locator('[data-testid=status]').textContent(),/HOLD source/);
   // Valid source DESCRIPTION is not human validation; manual click is allowed only as draft.
   await page.locator('[data-testid=landmark]').selectOption('Pt_Ricketts');
   assert.equal(await page.locator('[data-testid=guide-status]').getAttribute('data-hold'),'false');
   assert.match(await page.locator('[data-testid=guide-meaning]').textContent(),/foramen rotundum/);
   assert.match(await page.locator('[data-testid=guide-aliases]').textContent(),/PR_Ricketts_PTV/);
   await page.mouse.click(box.x+box.width*.25,box.y+box.height*.20);
   assert.equal(await page.locator('#markers circle').count(),1);
   assert.equal(await page.locator('[data-testid=operator]').isDisabled(),true);
   await page.locator('[data-testid=case]').selectOption('challiyan');
   assert.equal(await page.locator('#scan').getAttribute('href'),'images/challiyan.jpg');
   await page.locator('[data-testid=landmark]').selectOption('FOP_PREMOLAR_Ricketts');
   assert.equal(await page.locator('[data-testid=guide-status]').getAttribute('data-hold'),'true');
   box=await page.locator('#tracing').boundingBox();
   await page.mouse.click(box.x+box.width*.25,box.y+box.height*.20);
   assert.equal(await page.locator('#markers circle').count(),0);
   await page.locator('[data-testid=landmark]').selectOption('R3_Ricketts');
   assert.equal(await page.locator('[data-testid=guide-status]').getAttribute('data-hold'),'false');
   assert.match(await page.locator('[data-testid=guide-meaning]').textContent(),/sigmoïde/);
   await page.mouse.click(box.x+box.width*.25,box.y+box.height*.20);
   assert.equal(await page.locator('#markers circle').count(),1);
   await page.locator('[data-testid=landmark]').selectOption('Ba');
   await page.screenshot({path:path.join(out,'G13_HOLD_SIX_AND_TWO_PUBLIC_IMAGES__SYNTHETIC__'+viewport.width+'x'+viewport.height+'.png')});
   assert.deepEqual(errors,[]);
   console.log('G13 PUBLIC SOURCE GUIDE PASS '+viewport.width+'x'+viewport.height+
    '; 21 linked source identities; 6 source HOLD; real public images; synthetic operator clicks');
   await ctx.close();
  }
  fs.writeFileSync(path.join(out,'G13_EVIDENCE_NOTICE.txt'),
    'NONCLINICAL: G13 screenshot shows public radiograph with synthetic unverified point and HOLD warnings. '+
    'No orthodontist validated annotations, image orientation, calibration, Atlas factor or diagnosis.\n'+
    'ANUG 2014 https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG CC BY-SA 4.0\n'+
    'Challiyan 2023 https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg CC BY-SA 4.0\n'+
    'Derivative public screenshots retain source attribution and CC BY-SA 4.0 obligations.\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack||e);process.exit(1);});
