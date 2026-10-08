import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

// V1.5-00.2: PR #783 adaptive laboratory applied to the Hub, not FUE-A.
const root = path.resolve('artifacts/fue-v15-00-2');
await fs.mkdir(root,{recursive:true});
const browser = await chromium.launch({headless:true});
const results=[];
const bootstrap={workstationId:null,defaultExperience:null,stationLocked:false,stationEscapeAuthorized:false,stationEscapeExpiresAt:null,enrollmentRequired:false,authenticated:false,pinConfigured:false,canManage:false,canConfigurePin:false};
for(const vp of [{name:'tablet',width:768,height:1024},{name:'desktop',width:1280,height:900}]){
 const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
 await context.route('**/api/workstation/bootstrap',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(bootstrap)}));
 await context.route('**/api/clinics/me',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({nom_cabinet:'Cabinet FUE synthétique',cabinet_type:'CABINET'})}));
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const started=Date.now();
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.locator('[data-hub-experience]').first().waitFor({state:'visible'});
 const cards=await page.locator('[data-hub-experience]').count();
 if(cards!==3)throw new Error('Hub must display exactly three destinations, observed '+cards);
 await page.screenshot({path:path.join(root,vp.name+'-01-hub.png'),fullPage:true});
 const hubMs=Date.now()-started;
 await page.locator('[data-hub-experience="control"]').click();
 await page.waitForURL('**/control-center',{timeout:15000});
 await page.locator('[data-workstation-experience="control-center"]').waitFor({state:'visible',timeout:15000}).catch(async()=>{await page.getByText('Centre de contrôle').first().waitFor({state:'visible',timeout:5000})});
 await page.screenshot({path:path.join(root,vp.name+'-02-control.png'),fullPage:true});
 const firstValueMs=Date.now()-started;
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.locator('[data-hub-experience="station"]').click();
 await page.waitForURL('**/hub?select=1',{timeout:15000}); // unpaired station must not be entered
 await page.screenshot({path:path.join(root,vp.name+'-03-station-refusal.png'),fullPage:true});
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.locator('[data-hub-experience="cabinet"]').click();
 await page.waitForTimeout(600);
 const cabinetUrl=new URL(page.url()).pathname;
 // Unauthenticated synthetic profile must not see an unrestricted clinical page.
 if(cabinetUrl==='/dashboard')throw new Error('Unauthenticated cabinet access bypass');
 await page.screenshot({path:path.join(root,vp.name+'-04-cabinet-auth-boundary.png'),fullPage:true});
 await page.goto('http://127.0.0.1:4195/hub?select=1');
 await page.route('**/api/clinics/me',r=>r.abort());
 await page.reload();
 await page.locator('[data-hub-offline]').waitFor({state:'visible',timeout:12000});
 await page.screenshot({path:path.join(root,vp.name+'-05-offline.png'),fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1);
 if(overflow||errors.length)throw new Error(JSON.stringify({overflow,errors}));
 results.push({viewport:vp.name,dimensions:[vp.width,vp.height],cards,hubMs,firstValueMs,stationUnpairedRejected:true,cabinetUrl,offlineMessage:true,overflow,pageErrors:errors});
 await context.close();
}
await browser.close();
await fs.writeFile(path.join(root,'report.json'),JSON.stringify({protocol:'PR #783 / FUE-I V1.5-00.2',productHead:process.env.GITHUB_SHA||null,scope:'synthetic unpaired workstation; configured Station and authenticated Cabinet NOT certified',results},null,2));
console.log(JSON.stringify(results,null,2));
