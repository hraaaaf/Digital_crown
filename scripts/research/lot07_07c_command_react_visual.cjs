// LOT07/07-C only: Real React/Vite browser target, fixture-only; not application E2E.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createRequire}=require('node:module');
const pw=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const url='http://127.0.0.1:5193/command-target.html';
const out=path.resolve('artifacts/lot07-07c-command-react');fs.mkdirSync(out,{recursive:true});
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const css=fs.readFileSync('frontend/src/features/command/command-react-target.css','utf8');
if(css.includes('rgb(') || css.includes('rgba(') || /#[0-9a-fA-F]{3,8}/.test(css)) throw Error('COMMAND_CSS_LITERAL_COLOR');
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
    const hero=document.querySelector('.cmd-patienthero')?.getBoundingClientRect();
    const agenda=document.querySelector('.cmd-agenda')?.getBoundingClientRect();
    const quarterRows=document.querySelectorAll('.cmd-hour').length;
    return {viewport,doc:document.documentElement.scrollWidth,overflow,clipped,logos,odontogram:!!document.querySelector('[data-premium-odontogram="adult"]'),appointments:document.querySelectorAll('.cmd-appt').length,quarterRows,patientFirst:!!hero&&!!agenda&&hero.top<agenda.top,patientTop:hero?.top,agendaTop:agenda?.top};
   });
   if(result.overflow||result.clipped.length)failures.push('LAYOUT_'+w+'_'+JSON.stringify(result));
   if(result.appointments!==21)failures.push('APPOINTMENTS_'+w+'_'+result.appointments);
   if(result.quarterRows!==36)failures.push('NOT_15_MIN_GRID_'+w+'_'+result.quarterRows);
   const day=page.getByRole('button',{name:'Jour — vue disponible'});
   const week=page.getByRole('button',{name:'Semaine — en construction'});
   const list=page.getByRole('button',{name:'Liste — en construction'});
   if(await day.count()!==1||await day.getAttribute('aria-pressed')!=='true')failures.push('DAY_VIEW_PRIMARY_'+w);
   for(const [label,button] of [['WEEK',week],['LIST',list]]){
     if(await button.count()!==1||!(await button.isDisabled())||await button.getAttribute('aria-pressed')!=='false')
       failures.push('HONEST_MODE_'+label+'_'+w);
   }
   if(await page.locator('.cmd-calendar [data-quarter-hour-grid]').count()!==0)failures.push('UNEXPECTED_NESTED_GRID_'+w);

   if(w<=1080&&!result.patientFirst)failures.push('PATIENT_NOT_FIRST_'+w+'_'+JSON.stringify(result));
   if(!result.odontogram)failures.push('ODO_MISSING_'+w);
   if(!result.logos.some(x=>x.ok))failures.push('LOGO_MISSING_'+w);
   if(w<=430){
      for(const name of ['Command','Agenda','Patients','Imagerie']){
        if(await page.getByRole('button',{name,exact:true}).count()!==1)failures.push('MOBILE_A11Y_NAV_'+w+'_'+name);
      }
      if(await page.locator('.cmd-lanehead:visible').count()!==1)failures.push('MOBILE_VISIBLE_LANES_'+w);
      await page.getByRole('button',{name:'Agenda Dr B'}).click();
      if(await page.locator('.cmd-lanehead:visible').count()!==1 || await page.getByRole('button',{name:/TEST-003/}).isVisible()!==true || await page.locator('.cmd-appt').filter({hasText:'TEST-002'}).isVisible()!==false)failures.push('MOBILE_LANE_SWITCH_'+w);
      await page.getByRole('button',{name:'Agenda Dr A'}).click();
      const opener=page.getByRole('button',{name:'Afficher les 4 panneaux complémentaires'});
      if(!(await opener.isVisible())||await opener.getAttribute('aria-expanded')!=='false')failures.push('MOBILE_DISCLOSURE_MISSING_'+w);
      const afterCards=await page.evaluate(()=>{const cards=document.querySelector('.cmd-cards'),button=document.querySelector('.cmd-secondary-toggle');if(!cards||!button)return false;return button.getBoundingClientRect().top>=cards.getBoundingClientRect().bottom-3;});
      if(!afterCards)failures.push('MOBILE_DISCLOSURE_POSITION_'+w);
      if(await page.locator('.cmd-cards > .cmd-card:visible').count()!==5)failures.push('MOBILE_SECONDARY_DEFAULT_'+w);
      await opener.focus();
      await page.keyboard.press('Enter');
      if(await page.locator('.cmd-cards > .cmd-card:visible').count()!==9 || await page.locator('.cmd-secondary-toggle').getAttribute('aria-expanded')!=='true')failures.push('MOBILE_DISCLOSURE_OPEN_'+w);
      if(w===430){
        const extra=path.join(out,'command-react-mobile-expanded-430.png');
        await page.screenshot({path:extra,fullPage:true,animations:'disabled'});
        snaps.push({name:path.basename(extra),bytes:fs.statSync(extra).size,sha256:hash(extra),purpose:'explicit secondary panels open, mobile'}); 
      }
      await page.getByRole('button',{name:'Masquer les 4 panneaux complémentaires'}).click();
      if(await page.locator('.cmd-cards > .cmd-card:visible').count()!==5 || await page.locator('.cmd-secondary-toggle').getAttribute('aria-expanded')!=='false')failures.push('MOBILE_DISCLOSURE_CLOSE_'+w);
   }
   const img=path.join(out,'command-react-elite-'+w+'.png');await page.screenshot({path:img,fullPage:true,animations:'disabled'});
   snaps.push({name:path.basename(img),bytes:fs.statSync(img).size,sha256:hash(img),...result});
   if(w===1440){
      await page.getByRole('button',{name:'Agenda',exact:true}).first().click();
      if(!(await page.locator('h1').innerText()).includes('Command')
          ||await page.locator('.cmd-placeholder').count()!==0
          ||await page.locator('.cmd-appt').count()!==21
          ||await page.locator('#cmd-agenda').count()!==1
          ||await page.locator('.cmd-shell').getAttribute('data-active-patient-id')!=='TEST-001'
          ||!(await page.getByRole('button',{name:'Agenda',exact:true}).first().getAttribute('aria-current')))
        failures.push('AGENDA_REAL_RAIL_NAV_1440');
      if(await page.evaluate(()=>document.activeElement?.id)!=='cmd-agenda')failures.push('AGENDA_RAIL_FOCUS_1440');
      await page.getByRole('button',{name:'Patients',exact:true}).first().click();
      if(!(await page.locator('h1').innerText()).includes('Patients')
          ||!(await page.locator('.cmd-placeholder').innerText()).includes('en construction')
          ||await page.locator('.cmd-appt').count()!==0)
        failures.push('EXPLICIT_PLACEHOLDER_ONLY_NON_AGENDA_1440');
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
    const bg=document.createElement('span');bg.style.backgroundColor='var(--card-bg)';document.body.append(bg);
    const expectCard=getComputedStyle(bg).backgroundColor;bg.remove();
    const side=document.createElement('span');side.style.backgroundColor='var(--sidebar-bg)';document.body.append(side);
    const expectSide=getComputedStyle(side).backgroundColor;side.remove();
    return {token:p,active,expected,card:getComputedStyle(document.querySelector('.cmd-card')).backgroundColor,expectCard,sidebar:getComputedStyle(document.querySelector('.cmd-sidebar')).backgroundColor,expectSide};
   });
   if(check.active!==check.expected)failures.push('THEME_PRIMARY_'+theme);
   if(check.card!==check.expectCard)failures.push('THEME_CARD_'+theme);
   if(check.sidebar!==check.expectSide)failures.push('THEME_SIDEBAR_'+theme);
   const contrast=await page.evaluate(()=>{
     const rgb=value=>{const values=value.match(/[0-9.]+/g)?.slice(0,3).map(Number);return values?.length===3?values:null;};
     const lum=xs=>xs.map(v=>{const x=v/255;return x<=0.04045?x/12.92:((x+0.055)/1.055)**2.4;}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
     return ['.cmd-pill-warning','.cmd-pill-success','.cmd-alerts p','.cmd-lanehead b'].map(selector=>{
       const el=document.querySelector(selector);if(!el)return {selector,ratio:0};
       const style=getComputedStyle(el),fg=rgb(style.color),bg=rgb(style.backgroundColor);
       if(!fg||!bg)return {selector,ratio:0};
       const a=lum(fg),b=lum(bg);return {selector,ratio:(Math.max(a,b)+0.05)/(Math.min(a,b)+0.05)};
     });
   });
   if(contrast.some(row=>row.ratio<4.5))failures.push('STATUS_TEXT_CONTRAST_'+theme+'_'+JSON.stringify(contrast));
   const img=path.join(out,'command-react-theme-'+theme+'.png');
   await page.screenshot({path:img,fullPage:true,animations:'disabled'});
   snaps.push({name:path.basename(img),sha256:hash(img),bytes:fs.statSync(img).size,...check});
   await context.close();
 }
 const result={source:'REACT_VITE_ISOLATED_NO_APP_ROUTE',widths:[390,430,768,1280,1440],themes,snaps,failures,pass:failures.length===0};
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(result,null,2)+'\n');
 console.log('COMMAND_REACT_VISUAL_RESULT '+JSON.stringify({pass:result.pass,failures,screenshot_count:snaps.length,source:result.source}));
 if(result.pass){
   // Strict semantic check for the five isolated Command TS/TSX modules.
   require('node:child_process').execFileSync('node',['scripts/research/lot07_07c_command_typecheck.cjs'],{stdio:'inherit',timeout:120000});
   const typePath=path.join(out,'typecheck-target.json');
   if(!fs.existsSync(typePath))throw Error('COMMAND_TYPECHECK_EVIDENCE_MISSING');
   const typeProof=JSON.parse(fs.readFileSync(typePath,'utf8'));
   if(!typeProof.pass||typeProof.files?.length!==7||typeProof.wholeAppChecked!==false)
     throw Error('COMMAND_TYPECHECK_PROOF_UNTRUSTED');
   // Execute fixture-only R4 journeys under the same live React laboratory.
   require('node:child_process').execFileSync('node',['scripts/research/lot07_07c_command_react_journeys.cjs'],{stdio:'inherit',timeout:120000});
   if(!fs.existsSync(path.join(out,'journeys-r4.json')))throw Error('R4_JOURNEYS_EVIDENCE_MISSING');
 }
 if(!result.pass)process.exitCode=1;
}finally{await browser.close()}})().catch(e=>{console.error('REACT_VISUAL_ERROR '+e.stack);process.exitCode=2});
