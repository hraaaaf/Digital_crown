import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir=path.resolve('../artifacts/t2-browser/g4-rvg-actions'); fs.mkdirSync(outDir,{recursive:true});
const user=process.env.T2_USER, password=process.env.T2_PASSWORD; if(!user||!password) throw new Error('T2 credentials required');
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:user,password}}); if(!login.ok()) throw new Error('login failed');
const tokens=await login.json(), headers={Authorization:`Bearer ${tokens.access_token}`};
const patients=await api.get('/api/patients',{headers}); const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001'); if(!patient) throw new Error('fixture missing');
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEANmpCD8ongcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfUJxAYTIfIvQAAAAAElFTkSuQmCC','base64');
const browser=await chromium.launch({headless:true}); const evidence=[];
for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
 const context=await browser.newContext({viewport,acceptDownloads:true}); const page=await context.newPage();
 await page.addInitScript(({a,r})=>{localStorage.setItem('token',a);localStorage.setItem('refresh_token',r||'');localStorage.setItem('appMode','prod')},{a:tokens.access_token,r:tokens.refresh_token});
 const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=radiology&radioTab=rvg`,{waitUntil:'networkidle',timeout:90000});
 await page.getByRole('button',{name:'Ajouter une RVG',exact:true}).click();
 await page.locator('input[type=file]').setInputFiles({name:`g4-rvg-${viewport.width}.png`,mimeType:'image/png',buffer:png});
 await page.locator('select').selectOption('periapical');
 await page.getByPlaceholder('ex: 16, 27, 38').fill('16'); await page.getByPlaceholder('ex: UR, LL').fill('UR');
 const noteText=`G4 RVG browser proof ${viewport.width}`; await page.getByLabel(/Note/i).fill(noteText);
 const upP=page.waitForResponse(r=>r.url().includes(`/api/documents/patients/${patient.id}/rvg`)&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Enregistrer',exact:true}).click(); const up=await upP; if(!up.ok()) throw new Error(`upload ${up.status()}`);
 const doc=await up.json(); const note=page.getByText(noteText,{exact:true}); await note.waitFor({state:'visible'});
 const card=note.locator('xpath=ancestor::div[contains(@class,"border")][1]');
 const downP=page.waitForResponse(r=>r.url().includes(`/api/documents/${doc.id}/download`));
 await card.getByRole('button',{name:'Télécharger',exact:true}).click(); const down=await downP; if(!down.ok()) throw new Error(`download ${down.status()}`);
 await card.getByRole('button',{name:'Supprimer',exact:true}).click(); await page.getByRole('button',{name:'Annuler',exact:true}).click(); await note.waitFor({state:'visible'});
 await card.getByRole('button',{name:'Supprimer',exact:true}).click(); const trashP=page.waitForResponse(r=>r.url().includes(`/api/documents/${doc.id}/trash`)&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Supprimer',exact:true}).last().click(); const trash=await trashP; if(!trash.ok()) throw new Error(`trash ${trash.status()}`); await note.waitFor({state:'detached'});
 const list=await api.get(`/api/documents/patients/${patient.id}/rvg`,{headers}); if((await list.json()).some(x=>Number(x.id)===Number(doc.id))) throw new Error('deleted RVG still active');
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2); if(overflow||errors.length) throw new Error('RVG browser invariant failed');
 const shot=`g4-rvg-${viewport.width}x${viewport.height}.png`; await page.screenshot({path:path.join(outDir,shot),animations:'disabled'});
 evidence.push({viewport,id:doc.id,upload:up.status(),download:down.status(),trash:trash.status(),shot}); await context.close();
}
await browser.close(); await api.dispose();
fs.writeFileSync(path.join(outDir,'summary.json'),JSON.stringify({status:'PASS',evidence},null,2));
console.log('G4_RVG_ACTIONS '+JSON.stringify({status:'PASS',viewports:evidence.length}));
