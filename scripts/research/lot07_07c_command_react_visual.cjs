// LOT07/07-C only: Real React/Vite browser target, fixture-only; not application E2E.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createRequire}=require('node:module');
const pw=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const url='http://127.0.0.1:5193/command-target.html';
const out=path.resolve('artifacts/lot07-07c-command-react');fs.mkdirSync(out,{recursive:true});
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const failures=[],snaps=[],themes=['elite','emerald','rose','prestige','ocean','graphite','dark','high-contrast'];
(async()=>{const browser=await pw.chromium.launch({headless:true,args:['--no-sandbox']});
try{
 for(const w of [390,430,768,1280,1440]){
   const context=await browser.newContext({viewport:{width:w,height:w<768?900:950},deviceScaleFactor:1,reducedMotion:'reduce'});
   const page=await context.newPage();page.on('pageerror',e=>failures.push('JS_'+String(e.message).slice(0,150)));
   const response=await page.goto(url,{waitUntil:'networkidle',timeout:30000});
   if(response.status()!==200)failures.push('HTTP_'+response.status());
   await page.locator('[data-command-target="07-C-react-isolated"]').waitFor();
   const result=await page.evaluate(()=>{
    const viewport=document.documentElement.clientWidth;
    const shell=document.querySelector('.cmd-shell'),work=document.querySelector('.cmd-workbench'),right=document.querySelector('.cmd-right');
    const logos=Array.from(document.querySelectorAll('.cmd-brand img')).map(x=>({src:x.currentSrc?.split('/').pop(),ok:x.complete&&x.naturalWidth>0}));
    const overflow=document.documentElement.scrollWidth>viewport+3;
    const clipped=[shell,work,right].filter(Boolean).filter(x=>{const r=x.getBoundingClientRect();return r.right>viewport+4||r.left< -4;}).map(x=>x.className);
    return {viewport,doc:document.documentElement.scrollWidth,overflow,clipped,logos,odontogram:!!document.querySelector('[data-premium-odontogram="adult"]'),appointments:document.querySelectorAll('.cmd-appt').length};
   });
   if(result.overflow||result.clipped.length)failures.push('LAYOUT_'+w+'_'+JSON.stringify(result));
   if(result.appointments!==21)failures.push('APPOINTMENTS_'+w+'_'+result.appointments);
   if(!result.odontogram)failures.push('ODO_MISSING_'+w);
   if(!result.logos.some(x=>x.ok))failures.push('LOGO_MISSING_'+w);
   if(w===1440){
      await page.getByRole('button',{name:'Agenda',exact:true}).first().click();
      if(!(await page.locator('h1').innerText()).includes('Agenda') || await page.locator('.cmd-placeholder').count()!==1 || await page.locator('.cmd-appt').count()!==0)failures.push('NAV_FAILED');
      await page.getByRole('button',{name:'Retour au cockpit'}).click();
      await page.getByRole('button',{name:'RDV',exact:true}).click();
      if(await page.getByRole('status').count()!==1)failures.push('DEMO_BANNER');
      await page.keyboard.press('Tab');
      const focused=await page.evaluate(()=>document.activeElement?.tagName);
      if(focused!=='BUTTON')failures.push('KEYBOARD_TAB');
      const svgResponse=await page.request.get('http://127.0.0.1:5193/assets/odontogram/digital-crown-adult-reference-v3.svg');
      const text=await svgResponse.text();
      if(!text.trimStart().startsWith('<svg'))failures.push('OFFICIAL_ODO_ASSET_NOT_SVG');
   }
   const img=path.join(out,'command-react-elite-'+w+'.png');await page.screenshot({path:img,fullPage:true,animations:'disabled'});
   snaps.push({name:path.basename(img),bytes:fs.statSync(img).size,sha256:hash(img),...result});
   await context.close();
 }
 for(const theme of themes){
   const context=await browser.newContext({viewport:{width:1440,height:950},reducedMotion:'reduce'});
   const page=await context.newPage();await page.goto(url,{waitUntil:'networkidle'});
   await page.evaluate(t=>{if(t==='elite')document.documentElement.removeAttribute('data-theme');else document.documentElement.setAttribute('data-theme',t);},theme);
   const check=await page.evaluate(()=>{
    const p=getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
    const active=getComputedStyle(document.querySelector('.cmd-selected')).backgroundColor;
    const f=document.createElement('span');f.style.backgroundColor='var(--primary)';document.body.append(f);
    const expected=getComputedStyle(f).backgroundColor;f.remove();
    return {token:p,active,expected,card:getComputedStyle(document.querySelector('.cmd-card')).backgroundColor};
   });
   if(check.active!==check.expected)failures.push('THEME_PRIMARY_'+theme);
   const img=path.join(out,'command-react-theme-'+theme+'.png');
   await page.screenshot({path:img,fullPage:true,animations:'disabled'});
   snaps.push({name:path.basename(img),sha256:hash(img),bytes:fs.statSync(img).size,...check});
   await context.close();
 }
 const result={source:'REACT_VITE_ISOLATED_NO_APP_ROUTE',widths:[390,430,768,1280,1440],themes,snaps,failures,pass:failures.length===0};
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(result,null,2)+'\n');
 console.log('COMMAND_REACT_VISUAL_RESULT '+JSON.stringify({pass:result.pass,failures,screenshot_count:snaps.length,source:result.source}));
 if(!result.pass)process.exitCode=1;
}finally{await browser.close()}})().catch(e=>{console.error('REACT_VISUAL_ERROR '+e.stack);process.exitCode=2});
