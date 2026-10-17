/* R23-G15 actual Chromium exercises TWO separately generated offline forms.
 * Inputs are SYNTHETIC, never orthodontist decisions.
 */
const fs=require('node:fs'),path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.G15_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const root=process.env.G15_PRIVATE_REVIEW_DIR||'/tmp/dc-g15-private-synthetic';
 const proof=process.env.G15_SYNTHETIC_EVIDENCE_DIR||'/tmp/dc-g15-synthetic-proof';
 fs.mkdirSync(proof,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{
  for(const [role,viewport] of [
    ['A',{width:390,height:844}],['B',{width:1280,height:900}]
  ]){
   const ctx=await browser.newContext({viewport,acceptDownloads:true});
   const page=await ctx.newPage(),external=[];
   page.on('pageerror',e=>external.push(e.message));
   page.on('request',r=>{if(!r.url().startsWith('file:///'))external.push('unexpected network '+r.url());});
   const source=path.join(root,role,'independent_review.html');
   await page.goto('file://'+source,{waitUntil:'load'});
   assert.equal(await page.locator('article').count(),6);
   assert.match(await page.locator('h1').textContent(),new RegExp('Relecture indépendante '+role));
   await page.locator('[data-testid=token]').fill('synthetic_role_'+role);
   const cards=await page.locator('article').all();
   for(const [idx,card] of cards.entries()){
      const proposed=idx===0&&role==='A';
      await card.locator('[data-field=status]').selectOption(
        proposed?'RULE_PROPOSED_FOR_ADJUDICATION':'HOLD_UNRESOLVED');
      await card.locator('[data-field=atlas_ch13_page_or_figure]').fill(
        proposed?'TEST CH13 FIGURE 999 — NOT A REAL SOURCE':'');
      await card.locator('[data-field=proposed_pixel_rule]').fill(
        proposed?'SYNTHETIC proposed procedure: click a random pixel for software testing only; NOT a real rule.':'');
      await card.locator('[data-field=ambiguity_and_not_visible_policy]').fill(
        'SYNTHETIC unresolved contours and NOT_VISIBLE, needs actual specialist review.');
      for(let i=0;i<3;i++){
        await card.locator('[data-field="answer_'+i+'"]').fill(
           'SYNTHETIC discussion question '+i+' requires certified Atlas primary source evaluation.');
      }
   }
   if(role==='B'){
       await page.screenshot({path:path.join(proof,'G15_SYNTHETIC_FORM_NONCLINICAL_1280x900.png')});
   }
   const [dl]=await Promise.all([page.waitForEvent('download'),
     page.locator('[data-testid=save]').click()]);
   await dl.saveAs(path.join(proof,'synthetic_completed_'+role+'.json'));
   assert.match(await page.locator('[data-testid=status]').textContent(),/Export local créé/);
   const j=JSON.parse(fs.readFileSync(path.join(proof,'synthetic_completed_'+role+'.json'),'utf8'));
   assert.equal(j.role,role);
   assert.equal(j.clinical_release,false);
   assert.equal(j.cases.length,6);
   assert.equal(j.actual_signature_externally_verified,false);
   assert.deepEqual(external,[],'A private offline form requested network');
   console.log('G15 REAL BROWSER NONCLINICAL REVIEW FORM PASS '+role+' '+viewport.width+'x'+viewport.height+
       '; six source-lock HOLD questions; private local JSON export; no network');
   await ctx.close();
  }
  fs.writeFileSync(path.join(proof,'READ_ME_SYNTHETIC_ONLY.txt'),
    'ALL A/B responses are SYNTHETIC CI FILLER, NOT REAL ORTHODONTISTS, NOT A CLINICAL DOCUMENT.\n'+
    'These forms prove offline input/output interactions only; no credentials, signature or Atlas truth.\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack||e);process.exit(1);});
