import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir=path.resolve('../artifacts/t2-browser/g4-panoramic-actions'); fs.mkdirSync(outDir,{recursive:true});
const user=process.env.T2_USER,password=process.env.T2_PASSWORD; if(!user||!password) throw new Error('T2 credentials required');
const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:user,password}}); if(!login.ok()) throw new Error('panoramic login failed');
const tokens=await login.json(),headers={Authorization:`Bearer ${tokens.access_token}`};
const patients=await api.get('/api/patients',{headers}); if(!patients.ok()) throw new Error('patient list failed');
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001'); if(!patient) throw new Error('fixture patient missing');
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAY0lEQVR4nO3PQQ3AIADAQEANmpCD8ongcVnSU9DOfe74s6UDXjWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgfUJxAYTIfIvQAAAAAElFTkSuQmCC','base64');
const browser=await chromium.launch({headless:true}),evidence=[];

async function upload(page,label){
 const input=page.locator('input[type=file][accept="image/*"]');
 const p=page.waitForResponse(r=>r.url().includes(`/api/ia/upload-panoramic?patient_id=${patient.id}`)&&r.request().method()==='POST',{timeout:30000});
 await input.setInputFiles({name:`${label}.png`,mimeType:'image/png',buffer:png});
 const resp=await p; if(!resp.ok()) throw new Error(`panoramic upload failed ${resp.status()}`);
 const body=await resp.json(); if(!body?.id) throw new Error('panoramic upload missing id');
 await page.locator('img[alt="OPG"]').waitFor({state:'visible',timeout:30000});
 return body;
}
async function analyses(){
 const r=await api.get(`/api/ia/patients/${patient.id}/panoramic-analyses`,{headers}); if(!r.ok()) throw new Error(`history ${r.status()}`); return await r.json();
}

for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
 const context=await browser.newContext({viewport,colorScheme:'light'}),page=await context.newPage();
 await page.addInitScript(({a,r})=>{localStorage.setItem('token',a);localStorage.setItem('refresh_token',r||'');localStorage.setItem('appMode','prod')},{a:tokens.access_token,r:tokens.refresh_token});
 const pageErrors=[],http5xx=[]; page.on('pageerror',e=>pageErrors.push(String(e))); page.on('response',r=>{if(r.status()>=500)http5xx.push({url:r.url(),status:r.status()})});
 await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=radiology&radioTab=panoramic`,{waitUntil:'networkidle',timeout:90000});
 await page.getByRole('button',{name:'Nouvel Examen',exact:true}).waitFor({state:'visible',timeout:30000});

 const a=await upload(page,`g4-pano-a-${viewport.width}`);
 const ranges=page.locator('input[type=range]'); if(await ranges.count()<2) throw new Error('panoramic filter ranges missing');
 await ranges.nth(0).fill('145'); await ranges.nth(1).fill('155');
 await page.getByTitle('Inverser les couleurs (Négatif)').click();
 if(!String(await page.getByTitle('Inverser les couleurs (Négatif)').getAttribute('class')).includes('bg-indigo-500')) throw new Error('invert state not visible');
 await page.getByTitle('Loupe contextuelle').click();
 if(!String(await page.getByTitle('Loupe contextuelle').getAttribute('class')).includes('bg-indigo-500')) throw new Error('magnifier state not visible');
 await page.getByTitle('Réinitialiser les filtres').click();
 if(await ranges.nth(0).inputValue()!=='100'||await ranges.nth(1).inputValue()!=='110') throw new Error('filter reset mismatch');

 await page.getByTitle('Ajouter un détail clinique').click();
 const svg=page.locator('svg.cursor-crosshair'); await svg.waitFor({state:'visible',timeout:10000});
 page.once('dialog',d=>d.accept(`G4 annotation ${viewport.width}`));
 const box=await svg.boundingBox(); if(!box) throw new Error('panoramic SVG box missing');
 await svg.click({position:{x:Math.max(5,box.width*0.62),y:Math.max(5,box.height*0.36)}});
 const annotationText=page.getByText(`G4 annotation ${viewport.width}`,{exact:true});
 await annotationText.first().waitFor({state:'visible',timeout:10000});
 if(await annotationText.count()<2) throw new Error('panoramic annotation not mirrored in image and findings panel');

 await svg.click({position:{x:Math.max(5,box.width*0.58),y:Math.max(5,box.height*0.40)}});
 await page.getByRole('heading',{name:'Diagnostic Clinique'}).waitFor({state:'visible',timeout:10000});
 await page.getByRole('button',{name:"Carie de l'émail",exact:true}).click();
 await page.getByRole('heading',{name:'Diagnostic Clinique'}).locator('xpath=..').getByRole('button').click();

 await page.getByRole('button',{name:'Alvéolyse généralisée légère',exact:true}).click();
 const genP=page.waitForResponse(r=>r.url().endsWith('/api/ia/generate-panoramic-report')&&r.request().method()==='POST',{timeout:20000});
 await page.getByRole('button',{name:/VALIDER ET GÉNÉRER/i}).click(); const gen=await genP; if(!gen.ok()) throw new Error(`report generation ${gen.status()}`);
 const genBody=await gen.json(); if(!genBody?.report_narrative) throw new Error('report narrative missing');

 await page.getByRole('button',{name:'Bilan PDF',exact:true}).click();
 await page.getByTitle('Modifier le bilan (ligne par ligne)').click();
 const marker=`### G4 PANO EDIT ${viewport.width}`;
 const reportInputs=page.locator('div.space-y-2 input'); if(await reportInputs.count()<1) throw new Error('report edit inputs missing');
 await reportInputs.first().fill(marker);
 const putP=page.waitForResponse(r=>r.url().includes(`/api/ia/panoramic/${a.id}/report`)&&r.request().method()==='PUT',{timeout:15000});
 await page.getByTitle('Enregistrer les modifications').click(); const put=await putP; if(!put.ok()) throw new Error(`report edit ${put.status()}`);
 const persisted=(await analyses()).find(x=>Number(x.id)===Number(a.id)); if(!persisted?.report_narrative?.includes('G4 PANO EDIT')) throw new Error('edited report not persisted');

 const previewP=page.waitForResponse(r=>r.url().includes(`/api/ia/panoramic/${a.id}/pdf`)&&r.request().method()==='GET',{timeout:30000});
 await page.getByTitle('Aperçu du PDF').click(); const preview=await previewP; if(!preview.ok()) throw new Error(`preview PDF ${preview.status()}`);
 await page.getByRole('button',{name:'Fermer',exact:true}).click();

 const downloadP=page.waitForResponse(r=>r.url().includes(`/api/ia/panoramic/${a.id}/pdf`)&&r.request().method()==='GET',{timeout:30000});
 await page.getByTitle('Télécharger le bilan PDF').click(); const download=await downloadP; if(!download.ok()) throw new Error(`download PDF ${download.status()}`);

 const b=await upload(page,`g4-pano-b-${viewport.width}`);
 const cmpApi=await api.get(`/api/ia/patients/${patient.id}/panoramic-comparison`,{headers}); if(!cmpApi.ok()) throw new Error(`comparison api ${cmpApi.status()}`); const cmp=await cmpApi.json(); if(cmp.available!==true) throw new Error('comparison not available after two persisted analyses');
 await page.getByRole('button',{name:'Évolution',exact:true}).click();
 if(cmp.summary_text) await page.getByText(cmp.summary_text,{exact:true}).waitFor({state:'visible',timeout:10000});

 await page.getByRole('button',{name:'Comparer T0/T1',exact:true}).click();
 await page.locator('[data-m4b-history]').waitFor({state:'visible',timeout:10000});
 const rows=page.locator('[data-m4b-history] > .grid > div'); if(await rows.count()<2) throw new Error('history has fewer than two analyses');
 await rows.nth(1).click();
 await page.getByText(/Archive \(T0\)/).waitFor({state:'visible',timeout:10000}); await page.getByText(/Examen Actuel \(T1\)/).waitFor({state:'visible',timeout:10000});
 await page.getByRole('button',{name:'Quitter Comparaison',exact:true}).click();

 await page.getByRole('button',{name:'Historique',exact:true}).click(); await page.locator('[data-m4b-history]').waitFor({state:'visible'});
 page.once('dialog',d=>d.accept());
 const delP=page.waitForResponse(r=>/\/api\/ia\/panoramic\/\d+$/.test(new URL(r.url()).pathname)&&r.request().method()==='DELETE',{timeout:15000});
 await page.getByRole('button',{name:"Supprimer définitivement l'examen panoramique"}).first().click(); const del=await delP; if(!del.ok()) throw new Error(`panoramic delete ${del.status()}`);
 const deletedId=Number(new URL(del.url()).pathname.split('/').pop()); if((await analyses()).some(x=>Number(x.id)===deletedId)) throw new Error('deleted panoramic still present');

 const geometry=await page.evaluate(()=>({documentWidth:document.documentElement.scrollWidth,viewportWidth:document.documentElement.clientWidth,bodyWidth:document.body.scrollWidth}));
 const overflow=geometry.documentWidth>geometry.viewportWidth+2||geometry.bodyWidth>geometry.viewportWidth+2;
 const shot=`g4-panoramic-${viewport.width}x${viewport.height}.png`; await page.screenshot({path:path.join(outDir,shot),animations:'disabled'});
 if(overflow) throw new Error('panoramic horizontal overflow'); if(pageErrors.length) throw new Error('panoramic page errors: '+pageErrors.join(' | ')); if(http5xx.length) throw new Error('panoramic HTTP5xx: '+JSON.stringify(http5xx));
 evidence.push({viewport,firstId:a.id,secondId:b.id,report:gen.status(),edit:put.status(),preview:preview.status(),download:download.status(),deletedId,geometry,shot});
 await context.close();
}
await browser.close(); await api.dispose();
const summary={status:'PASS',viewports:evidence.length,evidence}; fs.writeFileSync(path.join(outDir,'summary.json'),JSON.stringify(summary,null,2)); console.log('G4_PANORAMIC_ACTIONS '+JSON.stringify(summary));
