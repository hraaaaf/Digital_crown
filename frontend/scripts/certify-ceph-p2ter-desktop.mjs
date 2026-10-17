/** P2ter true authenticated Cabinet path — T2 synthetic patient A/B only.
 * Requires backend:8005 + frontend:5173 + enrolled T2 workstation.
 * Produces BEFORE (initial studio), TARGET (history), AFTER (PDF preview)
 * for both requested desktop viewports. Do not treat captures as visual approval.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const out = path.resolve('../artifacts/p2ter-desktop');
fs.mkdirSync(out, {recursive:true});
const base = 'http://127.0.0.1:8005';
const user = process.env.T2_USER, password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('Isolated T2 credentials missing');

const api = await request.newContext({baseURL:base});
const login = await api.post('/api/auth/login',{form:{username:user,password}});
if (!login.ok()) throw new Error('T2 test-login failed '+login.status());
const tokens=await login.json();
const headers={Authorization:`Bearer ${tokens.access_token}`};
const patients=await api.get('/api/patients',{headers});
if (!patients.ok()) throw new Error('Cannot fetch authenticated T2 patient');
const patient=(await patients.json()).find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('Synthetic patient T2-0001 missing');

async function currentHistory(){
  const x=await api.get(`/api/ia/patients/${patient.id}/cephalo-analyses`,{headers});
  if(!x.ok()) throw new Error('Authenticated cephalo history denied: '+x.status());
  return await x.json();
}
const history=await currentHistory();
const studies={
  A:history.find(x=>String(x.image_original_path).endsWith('t2-cephalo-seeded.png')),
  B:history.find(x=>String(x.image_original_path).endsWith('p2ter-synthetic-study-B.png')),
};
if(!studies.A||!studies.B||studies.A.id===studies.B.id) throw new Error('Two distinct persisted synthetic studies required');

const browser=await chromium.launch({headless:true});
const summary=[];
try{
  for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
    for(const key of ['A','B']){
      const study=studies[key];
      const suffix=`${key}-${viewport.width}x${viewport.height}`;
      const context=await browser.newContext({viewport,colorScheme:'light',acceptDownloads:true});
      const page=await context.newPage();
      const pageErrors=[],http5xx=[];
      page.on('pageerror',e=>pageErrors.push(String(e)));
      page.on('response',r=>{if(r.status()>=500)http5xx.push({status:r.status(),url:r.url()});});
      await page.addInitScript(({token,refresh})=>{
        localStorage.setItem('token',token);
        localStorage.setItem('refresh_token',refresh||'');
        localStorage.setItem('appMode','prod');
        localStorage.setItem('clinical_tips_enabled','false');
      },{token:tokens.access_token,refresh:tokens.refresh_token});
      await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=radiology&radioTab=cephalo`,{
        waitUntil:'networkidle',timeout:90000,
      });
      const activate=page.getByRole('button',{name:/Activer le Suivi Orthodontique/i});
      if(await activate.count() && await activate.isVisible()){
        const patch=page.waitForResponse(r=>r.url().includes(`/api/patients/${patient.id}/ortho`)&&r.request().method()==='PATCH',{timeout:15000});
        await activate.click();
        if(!(await patch).ok())throw new Error('T2 synthetic ortho activation failed');
      }
      await page.getByRole('heading',{name:'Céphalométrie',exact:true}).waitFor({state:'visible',timeout:30000});
      await page.screenshot({path:path.join(out,`before-${suffix}.png`),animations:'disabled',fullPage:true});

      await page.getByRole('button',{name:'Historique',exact:true}).first().click();
      await page.getByText(/Historique des analyses \(/).waitFor({state:'visible',timeout:15000});
      const live=await currentHistory();
      const index=live.findIndex(x=>x.id===study.id);
      const rows=page.getByText('Analyse enregistrée',{exact:true});
      if(index<0 || await rows.count()!==live.length)throw new Error('History ordering/fixture mismatch');
      await page.screenshot({path:path.join(out,`target-${suffix}.png`),animations:'disabled',fullPage:true});

      const hydrate=page.waitForResponse(r=>r.request().method()==='GET'&&r.url().includes(`/api/ia/analyses/${study.id}`),{timeout:20000});
      await rows.nth(index).locator('xpath=ancestor::div[contains(@class,"group")][1]').click();
      const hydrated=await hydrate;
      if(!hydrated.ok()) throw new Error('Selected study hydration failed '+hydrated.status());
      const source=await hydrated.json();
      if(source.id!==study.id || !/^sha256:[0-9a-f]{64}$/.test(source.source_revision||'')){
        throw new Error('Hydrated study identity/revision invalid');
      }
      for(const name of [/Passer aux moulages/i,/Passer à la synthèse/i,/Préparer les documents et la stratégie/i]){
        const button=page.getByRole('button',{name});
        await button.waitFor({state:'visible',timeout:12000});
        const saving=page.waitForResponse(r=>r.url().includes(`/api/ia/analyses/${study.id}`)&&r.request().method()==='PUT',{timeout:30000});
        await button.click();
        if(!(await saving).ok()) throw new Error('Selected-study save/step transition refused');
      }
      const previewBtn=page.getByRole('button',{name:'Prévisualiser',exact:true});
      await previewBtn.waitFor({state:'visible',timeout:15000});
      const p=page.waitForResponse(r=>r.url().includes(`/api/patients/${patient.id}/pdf`)&&r.request().method()==='POST',{timeout:45000});
      await previewBtn.click();
      const response=await p;
      if(!response.ok()) throw new Error('Selected-study browser preview refused: '+response.status());
      const requestBody=JSON.parse(response.request().postData()||'{}');
      if(requestBody.patient_id!==patient.id||requestBody.analysis_id!==study.id||
         !/^sha256:[0-9a-f]{64}$/.test(requestBody.source_revision||'')||
         requestBody.archive!==false){
        throw new Error('React sent a wrong/ambiguous identity for '+suffix);
      }
      const previewBytes=await response.body();
      if(previewBytes.subarray(0,4).toString()!=='%PDF')throw new Error('Not a binary PDF');
      fs.writeFileSync(path.join(out,`preview-${suffix}.pdf`),previewBytes);
      await page.getByText('Aperçu du Bilan Orthodontique',{exact:true}).waitFor({state:'visible',timeout:15000});
      await page.screenshot({path:path.join(out,`after-${suffix}.png`),animations:'disabled',fullPage:true});
      await page.getByRole('button',{name:'Fermer',exact:true}).click();

      const archiveButton=page.getByRole('button',{name:/Archiver le bilan/i});
      await archiveButton.waitFor({state:'visible',timeout:10000});
      if(await archiveButton.isDisabled()) throw new Error('Archiving disabled for seeded study '+suffix);
      // Store.handlePrint offers open-or-download after a successful authenticated archive.
      page.once('dialog',dialog=>dialog.dismiss());
      const archivePending=page.waitForResponse(r=>r.url().includes(`/api/patients/${patient.id}/pdf`)&&r.request().method()==='POST',{timeout:45000});
      await archiveButton.click();
      const archivedResponse=await archivePending;
      if(!archivedResponse.ok())throw new Error('React archive PDF refused: '+archivedResponse.status());
      const archivedReq=JSON.parse(archivedResponse.request().postData()||'{}');
      if(archivedReq.patient_id!==patient.id||archivedReq.analysis_id!==study.id||
         archivedReq.archive!==true||archivedReq.source_revision!==requestBody.source_revision){
        throw new Error('React archive source diverged from preview identity');
      }
      const archivedBytes=await archivedResponse.body();
      if(archivedBytes.subarray(0,4).toString()!=='%PDF')throw new Error('Archive returned non-PDF bytes');
      fs.writeFileSync(path.join(out,`archived-${suffix}.pdf`),archivedBytes);

      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
      if(overflow) throw new Error('Desktop horizontal overflow at '+suffix);
      if(pageErrors.length) throw new Error('React page errors '+pageErrors.join(' | '));
      if(http5xx.length) throw new Error('HTTP 5xx: '+JSON.stringify(http5xx));
      summary.push({viewport,study:key,patient_id:patient.id,analysis_id:study.id,
        source_revision:requestBody.source_revision,
        preview_pdf:`preview-${suffix}.pdf`,archived_pdf:`archived-${suffix}.pdf`,
        http_archive:archivedResponse.status(),snapshots:[
          `before-${suffix}.png`,`target-${suffix}.png`,`after-${suffix}.png`,
        ],http_preview:response.status(),pages_checked:false});
      fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(summary,null,2));
      await context.close();
    }
  }
}finally{
  await browser.close();
  await api.dispose();
}
if(summary.length!==4)throw new Error('Incomplete desktop matrix');
console.log('P2TER_DESKTOP_E2E '+JSON.stringify({status:'HTTP_CAPTURED_NOT_YET_VISUALLY_APPROVED',scenarios:summary.length}));
