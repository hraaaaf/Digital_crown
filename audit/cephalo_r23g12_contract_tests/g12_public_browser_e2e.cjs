/* Browser truth: two original Wikimedia JPEGs rendered, synthetic clicks in pixel space,
 * switch/zoom/remove/export; NEVER assert clinical anatomical accuracy.
 */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.G12_PLAYWRIGHT_MODULE||'playwright');

(async()=>{
 const base=process.env.G12_URL||'http://127.0.0.1:8765/';
 const out=process.env.G12_EVIDENCE_DIR||'/tmp/dc-g12-browser-evidence';
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{
  const errors=[];
  for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
   const ctx=await browser.newContext({viewport,acceptDownloads:true});
   const page=await ctx.newPage();
   page.on('pageerror',e=>errors.push(e.message));
   page.on('request',req=>{
    if(!req.url().startsWith(base)&&!req.url().startsWith('blob:'))errors.push('External request '+req.url());
   });
   await page.goto(base,{waitUntil:'load'});
   assert.equal(await page.locator('[data-testid=landmark] option').count(),21);
   assert.equal(await page.locator('[data-testid=case] option').count(),2);
   const imageSize=await page.evaluate(async()=>{
    const image=document.getElementById('scan');
    const bitmap=new Image();bitmap.src=image.href.baseVal;
    await bitmap.decode();
    return [bitmap.naturalWidth,bitmap.naturalHeight];
   });
   assert.deepEqual(imageSize,[2272,1818]);
   // Source image clicks without a real operator token are blocked.
   let rect=await page.locator('#tracing').boundingBox();
   assert(rect&&rect.width>200&&rect.height>100);
   await page.mouse.click(rect.x+rect.width*0.35,rect.y+rect.height*0.28);
   assert.equal(await page.locator('#markers circle').count(),0);
   await page.locator('[data-testid=operator]').fill('synthetic_ci_operator');
   await page.locator('[data-testid=landmark]').selectOption('Po_anatomic');
   await page.mouse.click(rect.x+rect.width*0.35,rect.y+rect.height*0.28);
   assert.equal(await page.locator('#markers circle').count(),1);
   assert.match(await page.locator('[data-testid=counter]').textContent(),/1 \/ 21/);
   assert.equal(await page.locator('[data-testid=operator]').isDisabled(),true);
   await page.locator('[data-testid=case]').selectOption('challiyan');
   const altSize=await page.evaluate(async()=>{
    const bitmap=new Image();bitmap.src=document.getElementById('scan').href.baseVal;
    await bitmap.decode();return [bitmap.naturalWidth,bitmap.naturalHeight];
   });
   assert.deepEqual(altSize,[1000,1255]);
   assert.equal(await page.locator('#markers circle').count(),0);
   await page.locator('[data-testid=zoom]').selectOption('1.5');
   await page.locator('[data-testid=landmark]').selectOption('Pt_Ricketts');
   rect=await page.locator('#tracing').boundingBox();
   await page.mouse.click(rect.x+rect.width*0.24,rect.y+rect.height*0.36);
   assert.equal(await page.locator('#markers circle').count(),1);
   await page.locator('[data-testid=undo]').click();
   assert.equal(await page.locator('#markers circle').count(),0);
   await page.mouse.click(rect.x+rect.width*0.22,rect.y+rect.height*0.32);
   assert.equal(await page.locator('#markers circle').count(),1);
   await page.locator('[data-testid=case]').selectOption('anug');
   assert.equal(await page.locator('#markers circle').count(),1);
   if(viewport.width===1600){
     await page.locator('[data-testid=case]').selectOption('challiyan');
     await page.screenshot({path:path.join(out,'SYNTHETIC_CLICK_DEMO_NONCLINICAL_1600x1000.png')});
     await page.locator('[data-testid=case]').selectOption('anug');
   }
   const [download]=await Promise.all([page.waitForEvent('download'),
                                      page.locator('[data-testid=export]').click()]);
   const downloaded=path.join(out,'synthetic_browser_export_'+viewport.width+'.json');
   await download.saveAs(downloaded);
   const data=JSON.parse(fs.readFileSync(downloaded,'utf8'));
   assert.equal(data.clinical_release,false);
   assert.equal(data.independent_expert_authentication,false);
   assert.equal(data.atlas33_measurements_validated,0);
   assert.deepEqual(data.cases.map(c=>c.source_case),['anug','challiyan']);
   for(const c of data.cases){
     assert.equal(c.annotation_status,'MANUAL_DRAFT_UNVERIFIED');
     assert.equal(c.is_ricketts_goldset_reference,false);
     assert.equal(c.calibration_mm_per_pixel,null);
     assert.equal(Object.keys(c.landmarks).length,1);
   }
   assert(Object.hasOwn(data.cases[0].landmarks,'Po_anatomic'));
   assert(Object.hasOwn(data.cases[1].landmarks,'Pt_Ricketts'));
   console.log('G12 BROWSER PIXEL DRAFT (NONCLINICAL) PASS '+viewport.width+'x'+viewport.height+'; 2 public JPEGs; 2 synthetic clicks');
   await ctx.close();
  }
  assert.deepEqual(errors,[],'Browser errors / external network');
  fs.writeFileSync(path.join(out,'PUBLIC_SOURCE_ATTRIBUTION.txt'),
    'Synthetic browser demonstration only. NO HUMAN ANATOMICAL REFERENCE.\n' +
    'ANUG 2014: https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG — CC BY-SA 4.0\n' +
    'Challiyan 2023: https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg — CC BY-SA 4.0\n' +
    'Source images licensed CC BY-SA 4.0; screenshot derivative is CC BY-SA 4.0, without clinical endorsement.\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack||e);process.exit(1);});
