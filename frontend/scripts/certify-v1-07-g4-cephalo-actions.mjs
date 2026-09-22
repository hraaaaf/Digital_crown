import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir=path.resolve('../artifacts/t2-browser/g4-cephalo-actions');
fs.mkdirSync(outDir,{recursive:true});

const user=process.env.T2_USER,password=process.env.T2_PASSWORD;
if(!user||!password) throw new Error('T2 credentials required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:user,password}});
if(!login.ok()) throw new Error(`cephalo login failed: ${login.status()}`);
const tokens=await login.json(),headers={Authorization:`Bearer ${tokens.access_token}`};

const patients=await api.get('/api/patients',{headers});
if(!patients.ok()) throw new Error('cephalo patient list failed');
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('cephalo fixture patient missing');

async function activeAnalyses(){
  const r=await api.get(`/api/ia/patients/${patient.id}/cephalo-analyses`,{headers});
  if(!r.ok()) throw new Error(`cephalo active history failed: ${r.status()}`);
  return await r.json();
}
async function trashAnalyses(){
  const r=await api.get(`/api/ia/patients/${patient.id}/cephalo-trash`,{headers});
  if(!r.ok()) throw new Error(`cephalo trash failed: ${r.status()}`);
  return await r.json();
}

const initial=await activeAnalyses();
const seeded=initial.find(x=>String(x.image_original_path||'').endsWith('t2-cephalo-seeded.png'));
if(!seeded) throw new Error('persisted cephalo T2 fixture missing');

const browser=await chromium.launch({headless:true});
const evidence=[];

for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
  const context=await browser.newContext({viewport,colorScheme:'light'});
  const page=await context.newPage();
  await page.addInitScript(({a,r})=>{
    localStorage.setItem('token',a);
    localStorage.setItem('refresh_token',r||'');
    localStorage.setItem('appMode','prod');
    localStorage.setItem('clinical_tips_enabled','false');
  },{a:tokens.access_token,r:tokens.refresh_token});

  const pageErrors=[],http5xx=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('response',r=>{if(r.status()>=500) http5xx.push({url:r.url(),status:r.status()})});

  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=radiology&radioTab=cephalo`,{
    waitUntil:'networkidle',timeout:90000
  });

  const activate=page.getByRole('button',{name:/Activer le Suivi Orthodontique/i});
  if(await activate.count() && await activate.isVisible()){
    const p=page.waitForResponse(r=>r.url().includes(`/api/patients/${patient.id}/ortho`)&&r.request().method()==='PATCH',{timeout:15000});
    await activate.click();
    const resp=await p;
    if(!resp.ok()) throw new Error(`ortho activation failed: ${resp.status()}`);
  }
  await page.getByRole('heading',{name:'Céphalométrie',exact:true}).waitFor({state:'visible',timeout:30000});

  const beforeUpload=await activeAnalyses();
  const uploadP=page.waitForResponse(r=>r.url().includes(`/api/ia/upload-radio?patient_id=${patient.id}`)&&r.request().method()==='POST',{timeout:30000});
  await page.locator('input[type=file][accept="image/*"]').setInputFiles({
    name:'invalid-cephalo.png',
    mimeType:'image/png',
    buffer:Buffer.from('invalid-image-payload')
  });
  const rejected=await uploadP;
  if(rejected.ok()) throw new Error('invalid cephalo upload unexpectedly succeeded');
  const afterUpload=await activeAnalyses();
  if(afterUpload.length!==beforeUpload.length) throw new Error('rejected cephalo upload mutated active history');

  await page.getByRole('button',{name:'Historique',exact:true}).first().click();
  await page.getByText(/Historique des analyses \(/).waitFor({state:'visible',timeout:15000});
  const storedRow=page.getByText('Analyse enregistrée',{exact:true}).first().locator('xpath=ancestor::div[contains(@class,"group")][1]');
  const loadP=page.waitForResponse(r=>r.url().includes(`/api/ia/analyses/${seeded.id}`)&&r.request().method()==='GET',{timeout:15000});
  await storedRow.click();
  const loaded=await loadP;
  if(!loaded.ok()) throw new Error(`cephalo archived load failed: ${loaded.status()}`);

  const save=page.getByRole('button',{name:'Sauvegarder',exact:true});
  await save.waitFor({state:'visible',timeout:15000});
  if(await save.isDisabled()) throw new Error('cephalo save disabled after real history hydration');

  const rail=page.getByRole('complementary',{name:'Contrôles du workbench céphalométrique'});
  await rail.getByRole('button',{name:'Loupe',exact:true}).click();
  if(await rail.getByRole('button',{name:'Loupe',exact:true}).getAttribute('aria-pressed')!=='true') throw new Error('cephalo magnifier toggle not active');
  await rail.getByRole('button',{name:'Tissus mous',exact:true}).click();
  if(await rail.getByRole('button',{name:'Tissus mous',exact:true}).getAttribute('aria-pressed')!=='false') throw new Error('soft tissue toggle did not change');
  await rail.getByRole('button',{name:'Face 3D',exact:true}).click();
  if(await rail.getByRole('button',{name:'Face 3D',exact:true}).getAttribute('aria-pressed')!=='false') throw new Error('3D face toggle did not change');
  await rail.getByRole('button',{name:'Projection T1',exact:true}).click();
  if(await rail.getByRole('button',{name:'Projection T1',exact:true}).getAttribute('aria-pressed')!=='true') throw new Error('T1 projection toggle did not change');
  await rail.getByRole('button',{name:'Projection T2',exact:true}).click();
  if(await rail.getByRole('button',{name:'Projection T2',exact:true}).getAttribute('aria-pressed')!=='true') throw new Error('T2 projection toggle did not change');

  await page.getByTitle('Plein écran').click();
  await page.getByTitle('Quitter plein écran').waitFor({state:'visible',timeout:5000});
  await page.keyboard.press('Escape');
  await page.getByTitle('Plein écran').waitFor({state:'visible',timeout:5000});

  await page.getByTitle('État de calibration et provenance').first().click();
  await page.getByText('Calibration R1',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:'Fermer',exact:true}).click();

  const saveP=page.waitForResponse(r=>r.url().includes(`/api/ia/analyses/${seeded.id}`)&&r.request().method()==='PUT',{timeout:30000});
  await save.click();
  const saved=await saveP;
  if(!saved.ok()) throw new Error(`cephalo save failed: ${saved.status()}`);
  const reload=await api.get(`/api/ia/analyses/${seeded.id}`,{headers});
  if(!reload.ok()) throw new Error('cephalo persisted reload failed');
  const persisted=await reload.json();
  if(!Array.isArray(persisted.landmarks_data)||persisted.landmarks_data.length<30) throw new Error('cephalo landmarks were not preserved');

  for(const next of [/Passer aux moulages/i,/Passer à la synthèse/i,/Préparer les documents et la stratégie/i]){
    const button=page.getByRole('button',{name:next});
    await button.waitFor({state:'visible',timeout:10000});
    const transitionSave=page.waitForResponse(r=>r.url().includes(`/api/ia/analyses/${seeded.id}`)&&r.request().method()==='PUT',{timeout:30000});
    await button.click();
    const transitionResp=await transitionSave;
    if(!transitionResp.ok()) throw new Error(`cephalo step transition save failed: ${transitionResp.status()}`);
  }

  const previewButton=page.getByRole('button',{name:'Prévisualiser',exact:true});
  await previewButton.waitFor({state:'visible',timeout:10000});
  const previewP=page.waitForResponse(r=>r.url().includes(`/api/patients/${patient.id}/pdf`)&&r.request().method()==='POST',{timeout:30000});
  await previewButton.click();
  const preview=await previewP;
  if(!preview.ok()) throw new Error(`cephalo PDF preview failed: ${preview.status()}`);
  await page.getByText('Aperçu du Bilan Orthodontique',{exact:true}).waitFor({state:'visible',timeout:10000});
  await page.getByRole('button',{name:'Fermer',exact:true}).click();

  await page.getByRole('button',{name:'Historique',exact:true}).first().click();
  await page.getByText(/Historique des analyses \(/).waitFor({state:'visible',timeout:10000});
  page.once('dialog',d=>d.accept());
  const trashP=page.waitForResponse(r=>r.url().includes(`/api/ia/cephalo/${seeded.id}`)&&r.request().method()==='DELETE',{timeout:15000});
  await page.getByRole('button',{name:"Mettre l'analyse céphalométrique à la corbeille",exact:true}).first().click();
  const trashed=await trashP;
  if(!trashed.ok()) throw new Error(`cephalo trash action failed: ${trashed.status()}`);
  if((await activeAnalyses()).some(x=>Number(x.id)===Number(seeded.id))) throw new Error('trashed cephalo still visible in active history');
  if(!(await trashAnalyses()).some(x=>Number(x.id)===Number(seeded.id))) throw new Error('trashed cephalo missing from trash');

  const historyButtons=page.getByRole('button',{name:'Corbeille',exact:true});
  await historyButtons.last().click();
  const restore=page.getByRole('button',{name:'Restaurer',exact:true});
  await restore.waitFor({state:'visible',timeout:10000});
  const restoreP=page.waitForResponse(r=>r.url().includes(`/api/ia/cephalo/${seeded.id}/restore`)&&r.request().method()==='POST',{timeout:15000});
  await restore.click();
  const restored=await restoreP;
  if(!restored.ok()) throw new Error(`cephalo restore failed: ${restored.status()}`);
  if(!(await activeAnalyses()).some(x=>Number(x.id)===Number(seeded.id))) throw new Error('restored cephalo missing from active history');
  if((await trashAnalyses()).some(x=>Number(x.id)===Number(seeded.id))) throw new Error('restored cephalo still present in trash');

  await page.getByRole('button',{name:'Historique',exact:true}).last().click();
  await page.getByText('Analyse enregistrée',{exact:true}).first().waitFor({state:'visible',timeout:10000});

  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
  const shot=`g4-cephalo-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({path:path.join(outDir,shot),animations:'disabled'});
  if(overflow) throw new Error('cephalo horizontal overflow');
  if(pageErrors.length) throw new Error('cephalo page errors: '+pageErrors.join(' | '));
  if(http5xx.length) throw new Error('cephalo HTTP5xx: '+JSON.stringify(http5xx));

  evidence.push({
    viewport,
    analysisId:seeded.id,
    uploadRefusal:rejected.status(),
    save:saved.status(),
    preview:preview.status(),
    trash:trashed.status(),
    restore:restored.status(),
    shot
  });
  await context.close();
}

await browser.close();
await api.dispose();
const summary={status:'PASS',viewports:evidence.length,evidence};
fs.writeFileSync(path.join(outDir,'summary.json'),JSON.stringify(summary,null,2));
console.log('G4_CEPHALO_ACTIONS '+JSON.stringify(summary));
