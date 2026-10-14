import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const require = createRequire(import.meta.url);
const { webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const phase = process.argv[2] || 'before';
const out = pathToFileURL(path.resolve(process.env.PATIENT_SHELL_OUTPUT || `../artifacts/patient-shell-${phase}`) + path.sep);
await fs.mkdir(out, {recursive:true});
const browser = await webkit.launch({headless:true});
const evidence=[];
try {
for (const viewport of [{width:390,height:844},{width:768,height:1024},{width:1280,height:900}]) {
 const context = await browser.newContext({viewport,serviceWorkers:'block',timezoneId:'Africa/Casablanca',reducedMotion:'reduce'});
 const page = await context.newPage(); const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/**',r=>r.fulfill({status:503,contentType:'application/json',body:'{}'}));
 await page.route('**/__patient_seed',r=>r.fulfill({contentType:'text/html',body:'<!doctype html><title>Isolated fixture</title>'}));
 await page.goto('http://127.0.0.1:5201/__patient_seed');
 await page.evaluate(async()=>{
  const {PatientCompanionStorage:store}=await import('/src/features/patient-companion/PatientCompanionStorage.ts');
  await store.savePairing({accessToken:'synthetic-patient-only',context:{access_id:'synthetic-access',relationship_type:'SELF',patient:{display_name:'Nadia · patiente fictive'}},pairedAt:'2026-10-12T08:00:00Z',expiresAt:'2027-10-12T08:00:00Z'});
  await store.saveWallet({version:1,accessId:'synthetic-access',syncedAt:'2026-10-12T08:30:00Z',appointments:[{datetime_start:'2026-10-15T09:00:00Z',motif:'Contrôle de suivi',duration_minutes:30,status:'CONFIRME'}],shares:[{share_id:'demo-document',resource_type:'document',title:'Conseils après votre consultation',document_type:'FICHE'},{share_id:'demo-media',resource_type:'media',title:'Radiographie partagée'}],secureMessages:[{messageId:'demo-message',clientMessageId:'demo-client',senderKind:'STAFF',body:'Bonjour Nadia, votre prochain contrôle est prévu jeudi. À bientôt !',createdAt:'2026-10-12T08:15:00Z'}]});
 });
 await page.goto('http://127.0.0.1:5201/companion');
 await page.getByText('Nadia · patiente fictive',{exact:true}).waitFor();
 await page.evaluate(()=>Promise.race([document.fonts.ready,new Promise(resolve=>setTimeout(resolve,3000))]));
 const size=`${viewport.width}x${viewport.height}`;
 const capture=async(name)=>{await page.screenshot({path:new URL(`${name}-${size}.png`,out).pathname.replace(/^\/(\w:)/,'$1'),fullPage:false}); const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);evidence.push({name,size,overflow,errors:[...errors]}); if(overflow||errors.length)throw Error(JSON.stringify(evidence.at(-1)));};
 await capture('today');
 if(phase==='after')for(const [label,name] of [['Agenda','agenda'],['Documents','documents'],['Messages','messages'],['Plus','plus']]){await page.getByRole('navigation',{name:'Navigation patient'}).getByRole('button',{name:label,exact:true}).click();await page.waitForTimeout(300);await capture(name);}
 await context.close();
}
await fs.writeFile(new URL('evidence.json',out),JSON.stringify(evidence,null,2));
} finally {await browser.close();}
console.log(JSON.stringify(evidence));
