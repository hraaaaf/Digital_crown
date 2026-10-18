// LOT07 / 07-C R8 synthetic HTML target only.
// Browser tests must not be mistaken for Cabinet E2E or native 200%-zoom certification.
const {createRequire}=require('node:module');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const requirePlaywright=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'));
const {chromium}=requirePlaywright('playwright');
const html=path.resolve(process.argv[2]||'docs/research/lot07-07c-command-target-r8.html');
const out=path.resolve(process.argv[3]||'artifacts/lot07-07c-command-r8');
if (!fs.existsSync(html)) throw Error('TARGET_HTML_MISSING');
fs.mkdirSync(out,{recursive:true});
const required=['dashboard','agenda','dossier','imagerie'];
const sizes=[1280,1440,1920];
const results=[],files=[],issues=[];
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const browserLaunch={headless:true,args:['--no-sandbox','--disable-dev-shm-usage']};
(async()=>{
  const browser=await chromium.launch(browserLaunch);
  try {
    for(const width of sizes){
      const context=await browser.newContext({viewport:{width,height:900},deviceScaleFactor:1,reducedMotion:'reduce',colorScheme:'light'});
      const page=await context.newPage();
      const pageErrors=[];
      page.on('pageerror',e=>pageErrors.push(String(e.message)));
      await page.route('**/*',route=>{
        const u=route.request().url();
        if(u.startsWith('file://')||u.startsWith('data:'))return route.continue();
        return route.abort('blockedbyclient');
      });
      await page.goto(pathToFileURL(html).href,{waitUntil:'load'});
      await page.addStyleTag({path:path.resolve('frontend/src/index.css')});
      if(pageErrors.length) issues.push('PAGE_ERRORS_'+width+':'+pageErrors.length);
      const links=await page.locator('[data-view]').count();
      if(links!==4) issues.push('NAV_COUNT_'+width);
      for(const view of required){
        await page.locator('[data-view="'+view+'"]').click();
        if(await page.locator('#'+view).isHidden()) issues.push('HIDDEN_'+view+'_'+width);
        if(await page.locator('[data-view="'+view+'"]').getAttribute('aria-current')!=='page')issues.push('ARIA_'+view+'_'+width);
        const visible=await page.locator('.view:not(.hidden)').count();
        if(visible!==1)issues.push('MULTIPLE_VIEWS_'+view+'_'+width);
        const stats=await page.evaluate(()=>({bodyScrollWidth:document.body.scrollWidth,viewport:document.documentElement.clientWidth,bodyHeight:document.body.scrollHeight}));
        if(stats.bodyScrollWidth>stats.viewport+3)issues.push('HORIZONTAL_BODY_OVERFLOW_'+view+'_'+width+':'+stats.bodyScrollWidth);
        if(!await page.locator('.patient').isVisible())issues.push('MISSING_PATIENT_CONTEXT_'+view+'_'+width);
        const target=path.join(out,'command-r8-'+view+'-'+width+'x900.png');
        await page.screenshot({path:target,fullPage:true,animations:'disabled'});
        files.push({view,width,filename:path.basename(target),sha256:sha(target),bytes:fs.statSync(target).size,overflow:stats.bodyScrollWidth>stats.viewport+3});
      }
      await page.locator('[data-view="dashboard"]').focus();
      const before=await page.evaluate(()=>({dpr:window.devicePixelRatio,inner:window.innerWidth,client:document.documentElement.clientWidth}));
      for(let i=0;i<5;i++)await page.keyboard.press('Control+Equal');
      await page.waitForTimeout(300);
      const after=await page.evaluate(()=>({dpr:window.devicePixelRatio,inner:window.innerWidth,client:document.documentElement.clientWidth}));
      const scale=before.client/after.client;
      const zoom200proven=scale>=1.9&&scale<=2.1;
      results.push({width,browser:'Chromium Playwright',states_checked:4,focusable_nav:await page.locator('[data-view="dashboard"]').evaluate(el=>el.matches(':focus')),native_zoom_attempt:'Control+Equal 5 times',browser_before:before,browser_after:after,zoom_ratio:Number(scale.toFixed(3)),native_zoom200_proven:zoom200proven});
      if(zoom200proven){
        const zoomFile=path.join(out,'command-r8-dashboard-'+width+'-zoom200.png');
        await page.screenshot({path:zoomFile,fullPage:true,animations:'disabled'});
        files.push({view:'dashboard',width,zoom:'200% verified',filename:path.basename(zoomFile),sha256:sha(zoomFile),bytes:fs.statSync(zoomFile).size});
      }
      await context.close();
    }
  }finally{await browser.close();}
  const gate={scope:'LOT07_07C_R8_SYNTHETIC_TARGET_BROWSER_ONLY',html_sha256:sha(html),results,files,issues,native_zoom200_certified:results.every(x=>x.native_zoom200_proven),cabinet_before_after_certified:false,clinical_workflows_certified:false,source_data:'entirely synthetic',next:'human visual review, then matched real Cabinet BEFORE and native 200 percent zoom test'};
  fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(gate,null,2)+'\n');
  console.log('COMMAND_R8_BROWSER_PROOF='+JSON.stringify({states:files.length,issues,zoom200certified:gate.native_zoom200_certified,zoom_ratios:results.map(x=>({width:x.width,ratio:x.zoom_ratio})),manifest_sha256:sha(path.join(out,'manifest.json')),clinical_workflows_certified:false}));
  if(issues.length)process.exitCode=3;
})().catch(e=>{console.error('BROWSER_GATE_ERROR='+String(e.message).slice(0,450));process.exitCode=1});
