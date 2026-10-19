// LOT07/07-C R4: isolated synthetic user journeys, never Cabinet E2E.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createRequire}=require('node:module');
const {chromium}=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const out=path.resolve('artifacts/lot07-07c-command-react');
fs.mkdirSync(out,{recursive:true});
const cases=[],screens=[];
async function check(page,label,predicate){
 const ok=await predicate();
 cases.push({label,pass:!!ok});
 if(!ok)throw Error('R4_JOURNEY_FAILED: '+label);
}
async function snap(page,name){
 const file=path.join(out,name+'.png');
 await page.screenshot({path:file,fullPage:true,animations:'disabled'});
 screens.push({name:path.basename(file),sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')});
}
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  for(const width of [1440,430,390]){
   const context=await browser.newContext({viewport:{width,height:950},reducedMotion:'reduce'});
   const page=await context.newPage();
   const forbidden=[];
   page.on('request',request=>{if(new URL(request.url()).pathname.startsWith('/api/'))forbidden.push(request.url())});
   await page.goto('http://127.0.0.1:5193/command-target.html',{waitUntil:'networkidle'});
   await check(page,'J1 initial context '+width,async()=>
    await page.locator('.cmd-shell').getAttribute('data-active-patient-id')==='TEST-001'
    &&(await page.locator('.cmd-patienthero').innerText()).includes('Dr A')
    &&(await page.locator('.cmd-patienthero').innerText()).includes('09:00'));
   if(width===1440){
    await check(page,'J1 initial counters tied to mock status',async()=>(await page.locator('.cmd-chips').innerText()).includes('1 au fauteuil'));
    await page.getByRole('button',{name:'Mettre en pause'}).click();
    await check(page,'J1 mock pause status',async()=> (await page.locator('.cmd-patienthero').innerText()).includes('En pause')
      &&(await page.locator('.cmd-appt').filter({hasText:'TEST-001'}).getAttribute('class')).includes('cmd-appt-paused'));
    await check(page,'J1 paused counter',async()=>(await page.locator('.cmd-chips').innerText()).includes('0 au fauteuil'));
    await page.getByRole('button',{name:'Reprendre (simulation)'}).click();
    await check(page,'J1 mock resume',async()=>(await page.locator('.cmd-patienthero').innerText()).includes('En cours'));
   }
   if(width<500)await page.getByRole('button',{name:'Agenda Dr A'}).click();
   await page.getByRole('button',{name:'Patient suivant (même praticien)'}).click();
   if(width===1440)await check(page,'J2 keyboard focus to confirmation',async()=>
      (await page.evaluate(()=>document.activeElement?.textContent||'')).includes('Confirmer le changement de patient'));
   await check(page,'J2 explicit confirmation and no early switch '+width,async()=>
      (await page.getByRole('alertdialog').innerText()).includes('TEST-007')
      &&await page.locator('.cmd-shell').getAttribute('data-active-patient-id')==='TEST-001');
   await page.getByRole('button',{name:'Confirmer le changement de patient'}).click();
   await check(page,'J2 Dr A 10:00 and bound context '+width,async()=>
      await page.locator('.cmd-shell').getAttribute('data-active-patient-id')==='TEST-007'
      &&await page.locator('.cmd-right').getAttribute('data-patient-id')==='TEST-007'
      &&(await page.locator('.cmd-patienthero').innerText()).includes('Dr A')
      &&(await page.locator('.cmd-patienthero').innerText()).includes('10:00')
      &&!(await page.locator('.cmd-right').innerText()).includes('TEST-001'));
   if(width===1440)await check(page,'J2 coherent practitioner queue',async()=>(await page.locator('.cmd-card').filter({hasText:'File d’attente'}).innerText()).includes('TEST-URG'));
   await page.getByRole('tab',{name:'Dossier',exact:true}).click();
   await check(page,'J3 patient B dossier panels '+width,async()=>
      await page.locator('.cmd-cards > .cmd-card:visible').count()===3
      &&await page.locator('.cmd-cards').getAttribute('data-patient-id')==='TEST-007');
   await page.getByRole('tab',{name:'Odontogramme',exact:true}).click();
   await page.getByRole('tab',{name:'Odontogramme',exact:true}).focus();
   await page.keyboard.press('ArrowRight');
   await check(page,'J3 keyboard tab Imagerie '+width,async()=>
      await page.getByRole('tab',{name:'Imagerie',exact:true}).getAttribute('aria-selected')==='true'
      &&await page.locator('.cmd-cards > .cmd-card:visible').count()===1
      &&(await page.locator('.cmd-cards').innerText()).includes('Aucun média pour TEST-007'));
   await snap(page,'r4-imagerie-test007-'+width);
   await page.getByRole('tab',{name:'Dossier',exact:true}).click();
   await check(page,'J3 return same dossier '+width,async()=>
      await page.locator('.cmd-cards > .cmd-card:visible').count()===3
      &&await page.locator('.cmd-cards').getAttribute('data-patient-id')==='TEST-007');
   if(width<500)await page.getByRole('button',{name:'Agenda Dr A'}).click();
   await page.locator('.cmd-appt').filter({hasText:'TEST-001'}).click();
   await page.getByRole('button',{name:'Confirmer le changement de patient'}).click();
   await check(page,'J2 A-B-A return no previous patient leakage '+width,async()=>
      await page.locator('.cmd-shell').getAttribute('data-active-patient-id')==='TEST-001'
      &&await page.locator('.cmd-cards').getAttribute('data-patient-id')==='TEST-001'
      &&!(await page.locator('.cmd-right').innerText()).includes('TEST-007'));
   if(width===1440){
     await page.getByRole('button',{name:'Terminer le RDV (simulation)'}).click();
     await check(page,'J1 mock finish disables clinical-action affordance',async()=> 
       (await page.locator('.cmd-patienthero').innerText()).includes('Terminé')
       &&!(await page.getByRole('button',{name:'Mettre en pause'}).isEnabled()));
     await snap(page,'r4-consultation-finished-test001-1440');
   }
   await check(page,'No Cabinet API requests '+width,async()=>forbidden.length===0);
   await context.close();
  }
 }finally{await browser.close()}
 const result={source:'LOT07_07C_ISOLATED_SYNTHETIC_R4',pass:cases.every(x=>x.pass),cases,screens,realCabinet:false,patientRbacTested:false};
 fs.writeFileSync(path.join(out,'journeys-r4.json'),JSON.stringify(result,null,2)+'\n');
 console.log('R4_SYNTHETIC_JOURNEYS '+JSON.stringify({pass:result.pass,checks:cases.length,screens:screens.length}));
})().catch(error=>{console.error(String(error.stack||error));process.exitCode=1});
