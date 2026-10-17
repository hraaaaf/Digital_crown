/* Two real Wikimedia image browser tasks, no real human marks.
 * Distinguishes source evidence and non-authoritative proposal per HOLD.
 */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.G12_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const url=process.env.G12_URL||'http://127.0.0.1:8765/';
 const out=process.env.G14_EVIDENCE_DIR||'/tmp/dc-g14-browser-evidence';
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try {
  for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
   const ctx=await browser.newContext({viewport,acceptDownloads:false});
   const page=await ctx.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   page.on('request',req=>{if(!req.url().startsWith(url))errors.push("Nonlocal network "+req.url());});
   await page.goto(url,{waitUntil:'load'});
   const status=page.locator('[data-testid=g14-status]');
   assert.equal(await page.locator('[data-testid=landmark] option').count(),21);
   const ids=await page.evaluate(()=>G14_PACK.cards.map(c=>c.id));
   assert.deepEqual(ids,["Ba","FOP_MOLAR_Ricketts","FOP_PREMOLAR_Ricketts",
      "GO_Ricketts_PFH","L6_DISTAL_Ricketts","PNS_Ricketts"]);
   assert.equal(await page.evaluate(()=>G14_PACK.independent_reviewer_a_signed),false);
   assert.equal(await page.evaluate(()=>G14_PACK.independent_reviewer_b_signed),false);
   await page.locator('[data-testid=operator]').fill('synthetic_reviewer_contract');
   for(const source_case of ['anug','challiyan']){
     await page.locator('[data-testid=case]').selectOption(source_case);
     for(const id of ids){
       await page.locator('[data-testid=landmark]').selectOption(id);
       assert.match(await status.textContent(),/HOLD explicite/);
       assert.equal(await page.locator('[data-testid=g14-questions] li').count(),3);
       assert.match(await page.locator('[data-testid=g14-question]').textContent(),/NON AUTORITATIVE/);
       assert.match(await page.locator('[data-testid=g14-references]').textContent(),/https:\/\/(pubmed|pmc|www.ncbi)/);
       assert.equal(await page.locator('[data-testid=guide-status]').getAttribute('data-hold'),'true');
       const box=await page.locator('#tracing').boundingBox();
       await page.mouse.click(box.x+box.width*.2,box.y+box.height*.15);
       assert.equal(await page.locator('#markers circle').count(),0,
         "HOLD accepted a click for "+id);
     }
     if(source_case==='challiyan'){
       await page.locator('[data-testid=landmark]').selectOption('PNS_Ricketts');
       await page.screenshot({path:path.join(out,"G14_SIX_HOLD_READ_ONLY_NONCLINICAL_"+viewport.width+"x"+viewport.height+".png")});
     }
   }
   await page.locator('[data-testid=landmark]').selectOption('Pt_Ricketts');
   assert.match(await status.textContent(),/n'appartient pas aux 6/);
   assert.equal(await page.locator('[data-testid=g14-questions] li').count(),0);
   assert.deepEqual(errors,[]);
   console.log('G14 REAL BROWSER SOURCE REVIEW PASS '+viewport.width+'x'+viewport.height+
       '; 2 original public JPEGs; 6/6 HOLD cannot place; 0/2 expert signatures');
   await ctx.close();
  }
  fs.writeFileSync(path.join(out,'SOURCE_AND_COPYRIGHT.txt'),
   'R23-G14 is NONCLINICAL: No actual orthodontist, Atlas33 pixel authority, image orientation or mm calibration verified.\n'+
   'The G14 screenshots are public JPEG derivatives showing HOLD explanatory panels, no real or synthetic dots.\n'+
   'ANUG 2014 Wikimedia Commons: https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG CC BY-SA 4.0\n'+
   'Challiyan 2023 Wikimedia Commons: https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg CC BY-SA 4.0\n'+
   'Derivative screenshots follow attribution and CC BY-SA 4.0 conditions.\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack||e);process.exit(1);});
