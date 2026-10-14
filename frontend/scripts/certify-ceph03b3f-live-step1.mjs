// DC-CEPH-03B.3f — true product Step1 -> HTTP -> isolated SQLite browser proof.
// This script DOES NOT serve prediction JSON or intercept/mimic API responses.
import { createServer } from 'vite';
import { chromium } from 'playwright';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const assert=(condition,message)=>{if(!condition)throw new Error(message)};
assert(process.env.DC_CEPH03B3F_ACK==='synthetic-only','Refuse non-isolated run');
assert(process.env.DIGITALCROWN_ISOLATED_RUNTIME==='true' && process.env.ENVIRONMENT==='test',
  'Real clinic environment forbidden');
const root=process.cwd();
const out=path.join(root,'dc-ceph03b3f-live-http-proof');
await mkdir(out,{recursive:true});
const meta=JSON.parse(await readFile(process.env.DC_CEPH03B3F_METADATA,'utf8'));
assert(meta.scope==='SYNTHETIC_ONLY_LIVE_HTTP_BACKEND_NO_PATIENT_DATA','Invalid isolated metadata');
const manifest=JSON.parse(await readFile('scripts/fixtures/dc-ceph03b3c-public-cephalograms.json','utf8'));
const radioDir=process.env.DC_CEPH03B3C_RADIO_DIR;
const imageBytes={};
for(const radio of manifest.images){
  const bytes=await readFile(path.join(radioDir,radio.file_name));
  assert(bytes.length===radio.size_bytes && createHash('sha1').update(bytes).digest('hex')===radio.sha1,
    'Real Wikimedia source checksum mismatch '+radio.id);
  imageBytes[radio.id]=bytes;
}
const origin='http://127.0.0.1:4173';
const server=await createServer({
  configFile:path.join(root,'vite.config.ts'),
  server:{host:'127.0.0.1',port:4173,strictPort:true,
    proxy:{'/api':{target:'http://127.0.0.1:8005',changeOrigin:true,secure:false}} },
});
let browser;
const cases=[];const zoomProof=[];const errors=[];
const reqs=[];
const waitFor=async(fn,label,timeoutMs=30000)=>{
  const start=Date.now();
  while(Date.now()-start<timeoutMs){
    const v=await fn();
    if(v)return v;
    await new Promise(resolve=>setTimeout(resolve,180));
  }
  throw Error('Timed out '+label);
};
const persistedPoint=(data,id)=>data.landmarks_data.find(p=>p.id===id);
const pathForId=id=>'/api/ia/analyses/'+id;
const getPointX=async(page,id='N')=>{
  const marker=page.locator('[data-ceph03b-drag-handle="'+id+'"] > circle[fill]:not([fill="transparent"])').first();
  return Number(await marker.getAttribute('cx'));
};
const verifySvg=async(page,expected)=>{
  const handles=await page.locator('[data-ceph03b-drag-handle]').evaluateAll(nodes=>nodes.map(node=>{
    const marker=[...node.children].find(child=>child.tagName.toLowerCase()==='circle'
      && child.getAttribute('fill')!=='transparent');
    return {id:node.getAttribute('data-ceph03b-drag-handle'),x:Number(marker?.getAttribute('cx')),y:Number(marker?.getAttribute('cy'))};
  }));
  assert(handles.length>0,'No real Step1 handles');
  for(const p of handles){
    const q=expected.find(point=>point.id===p.id);
    assert(q && Math.abs(q.x-p.x)<0.0001 && Math.abs(q.y-p.y)<0.0001,
      'SVG != live API anatomical coordinates '+p.id);
  }
  return handles.length;
};
const setMode=async(page,mode)=>{
  if(await page.locator('[data-cephalo-analysis="'+mode+'"]').count())return;
  const name=mode==='com'?'COM':'Tous';
  const button=page.locator('[data-cephalo-analysis] button').filter({hasText:new RegExp('^'+name+'$')}).first();
  await button.click();
  await page.locator('[data-cephalo-analysis="'+mode+'"]').waitFor({timeout:10000});
};
const shot=async(page,film,mode,size,stage)=>{
  const name=film+'-'+mode+'-'+size+'-'+stage+'.png';
  const full=path.join(out,name);
  await page.screenshot({path:full,animations:'disabled',fullPage:false});
  const png=await readFile(full);
  assert(png.subarray(1,4).toString()==='PNG' && (png.readUInt32BE(16)+'x'+png.readUInt32BE(20))===size,
    'Invalid PNG viewport '+name);
  return name;
};
try {
  await server.listen();
  browser=await chromium.launch({headless:true,args:['--disable-dev-shm-usage']});
  for(const radio of manifest.images){
    const film=radio.id;
    const context=await browser.newContext({viewport:{width:1280,height:900},serviceWorkers:'block'});
    const anon=await browser.newContext({viewport:{width:1280,height:900},serviceWorkers:'block'});
    try{
      const patient=meta.patient_ids[film];
      assert(Number.isSafeInteger(patient)&&patient>0,'Missing disposable patient');
      const anonPatient=await anon.request.get(origin+'/api/patients/'+patient);
      assert([401,403].includes(anonPatient.status()),'Unauthenticated patient GET not blocked');
      const anonUpload=await anon.request.post(origin+'/api/ia/upload-radio?patient_id='+patient,{
        multipart:{file:{name:radio.file_name,mimeType:'image/jpeg',buffer:imageBytes[film]}}});
      assert([401,403].includes(anonUpload.status()),'Unauthenticated real upload not blocked');
      const outsider=await browser.newContext({viewport:{width:1280,height:900},serviceWorkers:'block'});
      try {
        const outsiderLogin=await outsider.request.post(origin+'/api/auth/login',{
          form:{username:meta.other_doctor_email,password:'TestPass123!'}});
        assert(outsiderLogin.status()===200,'Second clinician login failed');
        const deniedCrossPatient=await outsider.request.get(origin+'/api/patients/'+patient);
        assert([403,404].includes(deniedCrossPatient.status()),
          'CROSS_CABINET_PATIENT_READ: '+deniedCrossPatient.status());
        const deniedCrossUpload=await outsider.request.post(origin+'/api/ia/upload-radio?patient_id='+patient,{
          multipart:{file:{name:radio.file_name,mimeType:'image/jpeg',buffer:imageBytes[film]}}});
        assert([403,404].includes(deniedCrossUpload.status()),
          'CROSS_CABINET_UPLOAD: '+deniedCrossUpload.status());
      } finally {
        await outsider.close();
      }
      const login=await context.request.post(origin+'/api/auth/login',{
        form:{username:meta.doctor_email,password:'TestPass123!'}});
      assert(login.status()===200,'Real login failed '+film+': '+login.status());
      const loginJson=await login.json();
      assert(typeof loginJson.access_token==='string' && loginJson.access_token.length>20,
        'Login did not create real authenticated session');
      const cookies=await context.cookies(origin);
      assert(cookies.some(cookie=>cookie.name==='access_token'&&cookie.httpOnly),
        'Backend must issue HttpOnly access cookie');
      // The actual Axios interceptor sends the HttpOnly cookie; no token is
      // inserted into localStorage or a mock network route.
      const page=await context.newPage();
      const consoleErrors=[];
      const badResponses=[];
      page.on('response',response=>{
        if(response.status()>=400)badResponses.push({
          status:response.status(),method:response.request().method(),
          url:new URL(response.url()).pathname,resourceType:response.request().resourceType(),
        });
      });
      page.on('pageerror',err=>consoleErrors.push(String(err)));
      page.on('console',msg=>{if(msg.type()==='error')consoleErrors.push(msg.text())});
      page.on('request',r=>{if(r.url().includes('/api/'))reqs.push({film,url:new URL(r.url()).pathname,method:r.method()})});
      await page.goto(origin+'/ceph03b3f-live-step1.html?patient='+patient,{waitUntil:'domcontentloaded',timeout:60000});
      await page.getByText('Uploader une radiographie').waitFor({timeout:30000});
      const uploadDone=page.waitForResponse(resp=>
        resp.url().includes('/api/ia/upload-radio') && resp.request().method()==='POST',
        {timeout:120000});
      await page.locator('input[type="file"]').setInputFiles({
        name:radio.file_name,mimeType:'image/jpeg',buffer:imageBytes[film]});
      const uploadResponse=await uploadDone;
      assert(uploadResponse.status()===200,'Real product upload failed '+film+' '+uploadResponse.status());
      const uploaded=await uploadResponse.json();
      const source=uploaded.results?.calibration_source_resolution;
      // Real detector executes in isolated HTTP server. Neither a ruler
      // candidate nor absent evidence may authorize a physical ratio.
      const expectedSourceState=uploaded.results?.calibration_candidate
        ? 'IMAGE_RULER_UNVERIFIED' : 'NO_PHYSICAL_SOURCE';
      assert(source?.schema_version==='CEPHALO_SOURCE_RESOLUTION_V1'
        && source.state===expectedSourceState
        && source.eligible_mm_per_pixel===null && source.applied_to_analysis===false,
        'Real Step1 source resolver must fail closed for '+film+': '+JSON.stringify(source));
      assert(uploaded.status==='success' && uploaded.landmarks?.length===38,'Backend did not return 38 SRPose38 points');
      assert(uploaded.results?.vision_metadata?.mode_inference==='SOTA_ONNX_38',
        'Live product upload switched to non-SRPose model');
      assert(uploaded.is_calibrated===false && uploaded.mm_per_pixel===null,'Unjustified physical calibration');
      const id=uploaded.analysis_id;
      assert(Number.isSafeInteger(id)&&id>0,'Missing real analysis ID');
      await page.locator('[data-r20-workbench-layout]').waitFor({timeout:35000}).catch(async original => {
        const diagnostic={
          film,
          url:page.url(),
          body:(await page.locator('body').innerText().catch(()=>'' )).slice(0,3500),
          workbenchCount:await page.locator('[data-r20-workbench-layout]').count(),
          rootHtml:(await page.locator('#root').innerHTML().catch(()=>'' )).slice(0,3500),
          consoleErrors:consoleErrors.slice(-20),
          uploadResponseKeys:Object.keys(uploaded),
          uploadPath:uploaded.image_path,
        };
        const file=film+'-AFTER-LIVE-UPLOAD-FAILURE.png';
        await page.screenshot({path:path.join(out,file),fullPage:false}).catch(()=>{});
        await writeFile(path.join(out,film+'-failure.json'),JSON.stringify(diagnostic,null,2));
        console.error('DC_CEPH03B3F_LIVE_STEP1_BLOCKER',JSON.stringify(diagnostic).slice(0,6500));
        throw original;
      });
      const workbenchLabel=await page.locator('[data-ortho-workspace-patient]').innerText();
      assert(workbenchLabel.includes('RADIOGRAPHIE PUBLIQUE')
        && workbenchLabel.includes('DOSSIER FICTIF')
        && workbenchLabel.includes('AUCUN PATIENT RÉEL'),
        'Public radiograph attribution and disposable patient status must be explicit');
      const desktopStage=await page.locator('[data-r20-radiograph-stage]').boundingBox();
      assert(desktopStage && desktopStage.width >= 625,
        'Radiograph stage too narrow at desktop 1280: '+JSON.stringify(desktopStage));
      await page.locator('[data-ceph03b-drag-handle="N"]').waitFor({timeout:60000});
      await page.locator('svg[viewBox="0 0 '+radio.width+' '+radio.height+'"]').first().waitFor({timeout:45000});
      const initialGet=await context.request.get(origin+pathForId(id));
      assert(initialGet.status()===200,'Initial authenticated GET failed');
      const initial=await initialGet.json();
      assert(initial.angles_data?.calibration_source_resolution?.state===expectedSourceState
        && initial.angles_data?.calibration_source_resolution?.applied_to_analysis===false
        && initial.mm_per_pixel===null && initial.is_calibrated===false,
        'SQLite GET lost calibrated source provenance/no-mm invariant');
      assert(initial.landmarks_data.length===38,'Initial SQLite GET not 38 landmarks');
      let expected=initial.landmarks_data;
      const originalN=persistedPoint(initial,'N');
      assert(originalN,'N absent from SRPose38 output');
      assert(Math.abs(await getPointX(page)-originalN.x)<0.0001,
        'Live Step1 browser N not equal to authenticated GET');

      // Cross-layer zoom regression witness on the ACTUAL public film, clinical
      // browser and authenticated session. View-only: no analysis PUT is issued.
      await setMode(page,'com');
      const readZoom=()=>page.evaluate(()=>{
        const base=document.querySelector('svg[data-cephalo-viewport="base"]');
        const overlay=document.querySelector('svg[data-cephalo-viewport="overlay"]');
        return {
          base:base?.getAttribute('viewBox')??null,
          overlay:overlay?.getAttribute('viewBox')??null,
          level:document.querySelector('[data-cephalo-zoom-level]')?.textContent?.trim()??null,
        };
      });
      const originalZoom=await readZoom();
      const imageView='0 0 '+radio.width+' '+radio.height;
      assert(originalZoom.base===imageView && originalZoom.overlay===imageView && originalZoom.level?.includes('100'),
        'Base and overlay must both start at the full image on '+film+': '+JSON.stringify(originalZoom));
      const zoomIn=page.getByRole('button',{name:'Agrandir la radiographie'});
      await zoomIn.click(); await zoomIn.click();
      const magnified=await readZoom();
      const crop=(value)=>String(value||'').split(' ').map(Number);
      const crop150=crop(magnified.base);
      assert(magnified.base===magnified.overlay && magnified.level?.includes('150')
        && crop150.length===4 && crop150.every(Number.isFinite)
        && Math.abs(crop150[2]-radio.width/1.5)<0.001
        && Math.abs(crop150[3]-radio.height/1.5)<0.001,
        '150% overlay/base crop mismatch on '+film+': '+JSON.stringify(magnified));
      assert(Math.abs(await getPointX(page)-originalN.x)<0.0001,
        'Zoom unexpectedly changed landmark X on '+film);
      await page.getByRole('button',{name:'Déplacer la radiographie à droite'}).click();
      const panned=await readZoom();
      const shifted=crop(panned.base);
      assert(panned.base===panned.overlay && shifted[0]>crop150[0],
        'Pan must move both viewBoxes without skew on '+film+': '+JSON.stringify(panned));
      const zoomShot=await shot(page,film,'com','1280x900','zoom150-pan');
      await page.getByRole('button',{name:'Afficher toute la radiographie'}).click();
      const reset=await readZoom();
      assert(reset.base===imageView && reset.overlay===imageView && reset.level?.includes('100'),
        'Zoom reset did not restore complete image on '+film);
      assert(Math.abs(await getPointX(page)-originalN.x)<0.0001,
        'View-only pan/reset mutated anatomical N on '+film);
      zoomProof.push({film,viewport:'1280x900',originalZoom,magnified,panned,reset,
        screenshot:zoomShot,valid:true});
      for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
        await page.setViewportSize(viewport);
        const size=viewport.width+'x'+viewport.height;
        for(const mode of ['all','com']){
          await setMode(page,mode);
          const count=await verifySvg(page,expected);
          assert(mode!=='all'||count===38,'All mode must display 38 editable landmarks');
          const file=await shot(page,film,mode,size,'uploaded');
          cases.push({film,mode,viewport:size,screenshot:file,handles:count,valid:true,analysisId:id});
        }
      }
      await setMode(page,'all');
      const point=page.locator('[data-ceph03b-drag-handle="N"]');
      await point.focus();
      assert(await point.getAttribute('data-ceph03b-keyboard-focused')==='true','Real Step1 DOM focus missing');
      const edit=async(key,desired,label)=>{
        const saved=page.waitForResponse(resp=>resp.url().includes('/api/ia/analyses/'+id)
          &&resp.request().method()==='PUT',{timeout:60000});
        await page.keyboard.press(key);
        const response=await saved;
        assert(response.status()===200,'Live edit PUT failure '+label+' '+response.status());
        return await waitFor(async()=>{
          const res=await context.request.get(origin+pathForId(id));
          if(res.status()!==200)return false;
          const data=await res.json();
          return Math.abs(persistedPoint(data,'N')?.x-desired)<0.0001?data:false;
        },'durable '+label);
      };
      await edit('ArrowRight',originalN.x+1,'arrow1');
      expected=(await edit('Shift+ArrowRight',originalN.x+11,'shift10')).landmarks_data;
      assert(Math.abs(await getPointX(page)-(originalN.x+11))<0.0001,'Keyboard store lost rapid edits');
      // The integrated UX keeps history commands inside a semantic disclosure.
      // Open it through the actual user-facing summary before exercising the
      // real authenticated undo/redo PUT transactions.
      const historyDisclosure=page.locator('details').filter({has:page.locator('[data-ortho-edit-history]')});
      assert(await historyDisclosure.count()===1,'Expected one accessible correction history disclosure');
      await historyDisclosure.locator('summary').click();
      assert(await historyDisclosure.evaluate(el=>el.open),'Correction history not expanded');
      const undoWait=page.waitForResponse(resp=>resp.url().includes('/api/ia/analyses/'+id)
        &&resp.request().method()==='PUT',{timeout:60000});
      await page.getByRole('button',{name:'Annuler dernière correction'}).click();
      assert((await undoWait).status()===200,'Real undo PUT failed');
      await waitFor(async()=>{
        const res=await context.request.get(origin+pathForId(id));
        return res.status()===200 && Math.abs(persistedPoint(await res.json(),'N').x-(originalN.x+1))<0.0001;
      },'undo committed');
      const redoWait=page.waitForResponse(resp=>resp.url().includes('/api/ia/analyses/'+id)
        &&resp.request().method()==='PUT',{timeout:60000});
      await page.getByRole('button',{name:'Rétablir correction'}).click();
      assert((await redoWait).status()===200,'Real redo PUT failed');
      const redone=await waitFor(async()=>{
        const res=await context.request.get(origin+pathForId(id));
        if(res.status()!==200)return false;
        const data=await res.json();
        return Math.abs(persistedPoint(data,'N').x-(originalN.x+11))<0.0001?data:false;
      },'redo committed');
      assert(redone.angles_data?.calibration_source_resolution?.state===expectedSourceState
        && redone.angles_data?.calibration_source_resolution?.applied_to_analysis===false
        && redone.mm_per_pixel===null && redone.is_calibrated===false,
        'Refined SQLite record discarded immutable calibration source evidence');
      const anonRead=await anon.request.get(origin+pathForId(id));
      const anonMedia=await anon.request.get(origin+'/'+uploaded.image_path);
      assert([401,403].includes(anonRead.status()),'Anonymous GET leaked persisted landmark analysis');
      assert([401,403].includes(anonMedia.status()),'Anonymous GET leaked protected image');
      const beforeReload=await shot(page,film,'all','1600x1000','edited');
      // Real product rehydration: fresh browser navigation -> actual History UI
      // -> authenticated GET -> real store, no imported JSON snapshots.
      await page.reload({waitUntil:'domcontentloaded'});
      await page.getByRole('button',{name:'Historique',exact:true}).first().click();
      await page.getByText('Analyse enregistrée').first().waitFor({timeout:30000});
      const reloadGet=page.waitForResponse(resp=>resp.url().includes(pathForId(id))
        &&resp.request().method()==='GET',{timeout:30000});
      await page.getByText('Analyse enregistrée').first().click();
      assert((await reloadGet).status()===200,'History rehydration GET not authenticated');
      await page.locator('[data-r20-workbench-layout]').waitFor({timeout:30000});
      await page.locator('[data-ceph03b-drag-handle="N"]').waitFor({timeout:30000});
      assert(Math.abs(await getPointX(page)-(originalN.x+11))<0.0001,
        'History reload did not show durable SQLite correction');
      assert((await verifySvg(page,redone.landmarks_data))===38,'History image-space mismatch');
      const afterReload=await shot(page,film,'all','1600x1000','api-reload');
      // Allow non-fatal font fetch console messages, but never API 401/403
      // during authenticated product use (negative probes use anon context).
      const relevantErrors=consoleErrors.filter(msg=>/uncaught|TypeError|ReferenceError|not defined/i.test(msg));
      const criticalHttp=badResponses.filter(r=>r.url.startsWith('/api/') ||
        (r.resourceType==='script' && r.status>=400));
      if(relevantErrors.length || criticalHttp.length || badResponses.length){
        await writeFile(path.join(out,film+'-browser-http-diagnostic.json'),
          JSON.stringify({film,relevantErrors,criticalHttp,badResponses},null,2));
      }
      assert(relevantErrors.length===0 && criticalHttp.length===0,'Browser errors '+film+': '+relevantErrors.join(' | ').slice(0,700)
        +' HTTP='+JSON.stringify(badResponses).slice(0,1800));
      const filmApi=reqs.filter(r=>r.film===film);
      assert(filmApi.some(r=>r.method==='POST'&&r.url==='/api/ia/upload-radio'),
        'No live upload from actual browser');
      assert(filmApi.filter(r=>r.method==='PUT'&&r.url===pathForId(id)).length>=4,
        'No real Step1 4 clinical correction PUT transactions');
      assert(filmApi.some(r=>r.method==='GET'&&r.url===pathForId(id)),
        'No actual GET from real Step1/history');
      errors.push(...relevantErrors.map(v=>film+': '+v));
      cases.push({film,stage:'reloaded',analysisId:id,model:'SOTA_ONNX_38',
        calibrationSourceState:expectedSourceState,
        detectorActiveInThisHarness:true,calibrationApplied:false,nInitial:originalN.x,
        nPersisted:originalN.x+11,beforeReload,afterReload,authenticated:true,
        deniedAnonymousPatient:anonPatient.status(),deniedAnonymousUpload:anonUpload.status(),
        deniedAnonymousRead:anonRead.status(),deniedAnonymousMedia:anonMedia.status(),
        realHttpApi:filmApi,valid:true});
    }finally{
      await anon.close();
      await context.close();
    }
  }
}finally{
  if(browser)await browser.close();
  await server.close();
}
const report={
  suite:'DC-CEPH03B3F-REAL-STEP1-LIVE-HTTP-FASTAPI-SQLITE-AUTH',
  head:process.env.GITHUB_SHA || 'unknown',
  model:'SRPose38 actual unpatched ONNX, no clinical accuracy assertion',
  browserEntry:'CephaloWorkspace -> Step1Cephalo -> useOrthoStore -> cephaloRepository -> Axios',
  backend:'FastAPI app real HTTP /api, authenticated HttpOnly cookie, in-memory SQLite',
  untested:'Product /login visual screen, mobile UI, clinical anatomical accuracy, physical calibration',
  cases,zoomProof,errors,invalidCount:cases.filter(x=>!x.valid).length,
};
await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
assert(cases.length===10&&zoomProof.length===2&&zoomProof.every(x=>x.valid)&&report.invalidCount===0&&errors.length===0,'Incomplete live Step1 evidence');
console.log('DC_CEPH03B3F_REAL_STEP1_HTTP_TWO_RADIOS_8_SCENES_4_EDIT_TRANSACTIONS_PER_FILM_PASS');
