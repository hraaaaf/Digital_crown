import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const root=process.cwd();
const manifest=JSON.parse(await readFile(path.join(root,'scripts/fixtures/dc-ceph03b3c-public-cephalograms.json'),'utf8'));
const publicDir=path.join(root,'public/dc-ceph03b3c');
const expectedModel='a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb';
const bridges=new Map();
const assert=(cond,msg)=>{if(!cond)throw Error(msg)};
const near=(a,b)=>Math.abs(Number(a)-b)<0.5;
const out=path.join(root,'dc-ceph03b3c-real-radio-proof');
const scratch=path.join(root,'node_modules/.cache/dc-ceph03b3c-screens');
const htmlFile='dc-ceph03b3c-real-radio.html';
const configFile='dc-ceph03b3c-isolated.vite.config.mjs';
const port=5198;
const base='http://127.0.0.1:'+port+'/'+htmlFile;
const head=process.env.GITHUB_SHA || 'unknown';
const cases=[];
const requests=[];
await rm(out,{recursive:true,force:true});
await rm(scratch,{recursive:true,force:true});
await mkdir(out,{recursive:true});
await mkdir(scratch,{recursive:true});

for(const radio of manifest.images){
  const bytes=await readFile(path.join(publicDir,radio.file_name));
  if(createHash('sha1').update(bytes).digest('hex')!==radio.sha1 || bytes.length!==radio.size_bytes){
    throw Error('Radio source bytes invalid '+radio.id);
  }
  const b=JSON.parse(await readFile(path.join(publicDir,'cephalo-'+radio.id+'-predictions.json'),'utf8'));
  const actualN=b.baseline?.find(p=>p.id==='N');
  const savedN=b.after_redo?.find(p=>p.id==='N');
  assert(b.source==='AUTHENTICATED_SQLITE_API_READ_AFTER_REAL_SRPOSE38_UPLOAD'
    &&b.model_sha256===expectedModel
    &&b.source_image_sha1===radio.sha1
    &&b.radio===radio.id &&b.inference_mode==='SOTA_ONNX_38'
    &&b.clinical_accuracy_evaluated===false
    &&b.is_calibrated===false &&b.mm_per_pixel===null
    &&b.baseline.length===38&&b.after_redo.length===38
    &&actualN&&savedN&&near(actualN.x+11,savedN.x),
    'Invalid authenticated real-model inference bridge '+radio.id);
  bridges.set(radio.id,b);
}
await writeFile(path.join(root,htmlFile),
  '<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body style="margin:0"><div id="root"></div><script type="module" src="/src/features/ortho/CephaloTracingLayer.realRadioFixture.tsx"></script></body></html>');
await writeFile(path.join(root,configFile),
  "import { defineConfig } from 'vite';\n"+
  "import react from '@vitejs/plugin-react';\n"+
  "export default defineConfig({ plugins:[react()], server:{strictPort:true}, optimizeDeps:{noDiscovery:true, include:['react','react-dom/client','framer-motion','localforage','zustand','zustand/middleware']} });\n");
const server=spawn(path.join(root,'node_modules/.bin/vite'),
  ['--config',configFile,'--host','127.0.0.1','--port',String(port)],
  {cwd:root,env:{...process.env,BROWSER:'none'},stdio:['ignore','pipe','pipe']});
let viteLog='';
server.stdout.on('data',x=>{viteLog+=x});
server.stderr.on('data',x=>{viteLog+=x});

const browser=await chromium.launch({headless:true});
try{
  let ready=false;
  for(let i=0;i<120;i++){
    try { const r=await fetch(base);if(r.status===200){ready=true;break} } catch {}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  assert(ready,'Vite failed to serve real-radio fixture');

  for(const radio of manifest.images)for(const mode of ['com','all'])
  for(const viewport of [{width:1280,height:900},{width:1600,height:1000}]){
    const name=radio.id+'-'+mode+'-'+viewport.width+'x'+viewport.height;
    const record={name,film:radio.id,mode,viewport:viewport.width+'x'+viewport.height,
      valid:false,images:[],errors:[],consoleErrors:[],navigationCount:0};
    const context=await browser.newContext({viewport,locale:'fr-FR',reducedMotion:'reduce'});
    const page=await context.newPage();
    page.setDefaultTimeout(8000);
    page.on('pageerror',e=>record.consoleErrors.push(e.message));
    page.on('console',e=>{if(e.type()==='error')record.consoleErrors.push(e.text())});
    page.on('framenavigated',f=>{if(f===page.mainFrame())record.navigationCount++});
    await page.route('**/*',async route=>{
      const u=new URL(route.request().url());
      if(u.hostname==='127.0.0.1'&&u.port===String(port))return route.continue();
      if(u.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});
      requests.push(u.href);return route.abort('blockedbyclient');
    });
    const screenshot=async stage=>{
      const f=name+'-'+stage+'.png';
      await page.screenshot({path:path.join(scratch,f)});
      record.images.push(f);
    };
    const stage=()=>page.locator('[data-film="'+radio.id+'"]');
    // COM intentionally excludes the N editing handle; Po is the COM-safe
    // exposed reticle. In ALL, edit N exactly as the backend persisted edits.
    const editId=mode==='com'?'Po':'N';
    const point=()=>page.locator('[data-ceph03b-drag-handle="'+editId+'"]');
    const pointX=async()=>Number(await stage().getAttribute(editId==='Po'?'data-po-x':'data-n-x'));
    const count=async attr=>Number(await stage().getAttribute(attr));
    // Attribute installed on each independently-keyed visual T1/T2 group;
    // stroke-dasharray is NOT a reliable proxy for landmark ghost identity.
    const ghostLines=async id=>page.locator('[data-ceph03b-ghost-layer="'+id+'"] line').count();
    try{
      const response=await page.goto(base+'?film='+radio.id+'&mode='+mode+'&predicted=1',{waitUntil:'networkidle'});
      assert(response?.status()===200,'Fixture HTTP not 200');
      await point().waitFor({state:'attached'});
      const expectedSrc='/dc-ceph03b3c/'+radio.file_name;
      const image=page.locator('svg image[href="'+expectedSrc+'"]').first();
      assert(await image.count()===1,'Original radio JPEG not rendered');
      const decoded=await page.evaluate(async url=>{
        const r=await fetch(url);
        if(!r.ok)throw Error('Xray fetch failed');
        const img=await createImageBitmap(await r.blob());
        const dimensions={width:img.width,height:img.height};
        img.close();return dimensions;
      },expectedSrc);
      assert(decoded.width===radio.width&&decoded.height===radio.height,'Original JPEG dimensions mismatch');
      const bridge=bridges.get(radio.id);
      const initialX=bridge.baseline.find(p=>p.id===editId)?.x;
      assert(Number.isFinite(initialX),'Missing expected real SRPose38 edit handle '+editId);
      assert(near(await pointX(),initialX),'Original real SRPose38 '+editId+' point differs from authenticated API');
      assert(await stage().getAttribute('data-predicted')==='true','Browser did not load real inference data');
      assert(await stage().getAttribute('data-model-sha256')===expectedModel,'Model provenance mismatch');
      assert(await stage().getAttribute('data-source-image-sha1')===radio.sha1,'Image provenance mismatch');
      assert(await stage().getAttribute('data-predicted-count')==='38','Model point count not 38');
      assert(await count('data-audit')===0,'Unexpected initial audit');
      // The visual overlay may move label glyphs but never model coordinates.
      const visibleModelPoints=await page.locator('[data-ceph03b-drag-handle]').evaluateAll(nodes=>
        nodes.map(node=>{
          const marker=[...node.children].find(child=>child.tagName.toLowerCase()==='circle'&&child.getAttribute('fill')!=='transparent');
          return {id:node.getAttribute('data-ceph03b-drag-handle'),
            x:Number(marker?.getAttribute('cx')),y:Number(marker?.getAttribute('cy'))};
        }));
      assert(visibleModelPoints.length>0,'No visible editable landmarks');
      if(mode==='all')assert(visibleModelPoints.length===38,'ALL mode must expose 38 model handles');
      for(const pt of visibleModelPoints){
        const source=bridge.baseline.find(p=>p.id===pt.id);
        assert(source&&Math.abs(source.x-pt.x)<0.00001&&Math.abs(source.y-pt.y)<0.00001,
          'Visual work changed a source model coordinate '+pt.id);
      }
      const initialLabelCount=await page.locator('[data-ceph03b-landmark-label]').count();
      assert(initialLabelCount===0,'Ambient labels still crowd the radiograph');
      const initialT1=await ghostLines('t1');
      const initialT2=await ghostLines('t2');
      const ghostOpacities=await page.locator('[data-ceph03b-ghost-layer] [data-cephalo-line-key]')
        .evaluateAll(nodes=>nodes.map(node=>Number(node.getAttribute('opacity'))));
      assert(ghostOpacities.length>0&&ghostOpacities.every(x=>x>0&&x<=0.380001),
        'Ghost presentation opacity not explicitly bounded');
      record.initialGhostLines={t1:initialT1,t2:initialT2};
      assert(initialT1>0&&initialT2>0,'Expected independent T1 and T2 visual-only trace lines');
      await screenshot('initial');

      await point().focus();
      assert(await point().evaluate(node=>node===document.activeElement),'SVG keyboard focus failed');
      assert(await point().getAttribute('data-ceph03b-keyboard-focused')==='true',
        'DOM focus not reflected in reticle');
      const focusedLabelCount=await page.locator('[data-ceph03b-landmark-label]').count();
      const focusRingCount=await page.locator('[data-ceph03b-focus-ring="'+editId+'"] circle').count();
      assert(focusedLabelCount===1
        &&await page.locator('[data-ceph03b-landmark-label="'+editId+'"]').count()===1,
        'Focused landmark label hidden or colliding with others');
      assert(focusRingCount===2,'Keyboard focus requires a double high-contrast ring');
      await screenshot('focus');
      await page.keyboard.press('ArrowRight');
      await page.keyboard.press('Shift+ArrowRight');
      assert(near(await pointX(),initialX+11),'Rapid keyboard moves lost state');
      assert(await count('data-audit')===2&&await count('data-undo')===2,'Keyboard audit missing');
      await screenshot('keyboard');

      await page.getByRole('button',{name:'Annuler'}).click();
      assert(near(await pointX(),initialX+1),'Undo did not restore first edit');
      assert(await count('data-redo')===1,'Undo stack or redo stack invalid');
      await page.getByRole('button',{name:'Rétablir'}).click();
      assert(near(await pointX(),initialX+11),'Redo did not reapply second edit');
      assert(await count('data-audit')===4,'Audit does not show undo+redo');
      await screenshot('redo');

      await page.locator('[data-t1]').click();
      assert(await stage().getAttribute('data-ghost-t1')==='false','T1 was not hidden');
      assert(await ghostLines('t1')===0,'T1 ghost remained rendered after hide');
      assert(await ghostLines('t2')===initialT2,'T1 toggle corrupted T2 ghost');
      await page.locator('[data-t2]').click();
      assert(await stage().getAttribute('data-ghost-t2')==='false','T2 was not hidden');
      assert(await ghostLines('t1')===0&&await ghostLines('t2')===0,'Hidden ghosts should have no anatomical trace lines');
      assert(near(await pointX(),initialX+11),'T1/T2 toggle moved active point');
      assert(await count('data-audit')===4,'T1/T2 visibility persisted an anatomical edit');
      await screenshot('ghosts-off');
      await page.locator('[data-t1]').click();
      await page.locator('[data-t2]').click();
      assert(await ghostLines('t1')===initialT1&&await ghostLines('t2')===initialT2,'T1/T2 traces not restored');

      const auditBeforeReload=await count('data-audit');
      assert(auditBeforeReload===4,'Transient edit audit must contain EDIT EDIT UNDO REDO');
      // New top-level navigation: rehydrate the read-after-write response
      // exported from the isolated authenticated API's last GET. This remains
      // a fixture handoff, NOT live browser/backend authentication.
      await page.goto(base+'?film='+radio.id+'&mode='+mode+'&predicted=1&snapshot=after-redo',
        {waitUntil:'networkidle'});
      await point().waitFor({state:'attached'});
      assert(await stage().getAttribute('data-loaded-snapshot')==='after-redo',
        'Not showing persisted authenticated GET snapshot');
      const expectedReloadX=initialX+(editId==='N'?11:0);
      assert(near(await pointX(),expectedReloadX),
        'Fresh page did not use the authoritative API snapshot for '+editId);
      const persistedN=bridge.after_redo.find(p=>p.id==='N')?.x;
      assert(Number.isFinite(persistedN)
        &&near(Number(await stage().getAttribute('data-n-x')),persistedN),
        'Persisted N correction missing on reloaded DOM in '+mode+' mode');
      assert(await count('data-audit')===0&&await count('data-undo')===0,
        'Fresh DOM should not reuse ephemeral edit timeline');
      await screenshot('api-readback');
      record.reloadRehydrated=true;
      record.editedPointId=editId;
      record.persistedN=bridge.after_redo.find(p=>p.id==='N')?.x;
      assert(record.consoleErrors.length===0,'Browser console errors');
      assert(record.navigationCount===2,'Unexpected dev-server reload');
      assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),'Horizontal overflow');
      record.valid=true;
      record.decoded=decoded;
      record.initialX=initialX;
      record.currentX=await pointX();
      record.initialLabelCount=initialLabelCount;
      record.focusedLabelCount=focusedLabelCount;
      record.focusRingCount=focusRingCount;
      record.ghostOpacityMax=Math.max(...ghostOpacities);
      record.verifiedModelHandleCount=visibleModelPoints.length;
      record.auditEvents=auditBeforeReload;
      record.reloadedAuditEvents=await count('data-audit');
      record.ghostLines={t1:initialT1,t2:initialT2};
    }catch(e){
      record.errors.push(String(e));
      await screenshot('failure').catch(()=>{});
    }finally{
      cases.push(record);
      await context.close();
    }
  }
}finally{
  await browser.close();
  server.kill('SIGTERM');
  await cp(scratch,out,{recursive:true,force:true});
  await writeFile(path.join(out,'vite.log'),viteLog);
}
const report={suite:'DC-CEPH03B3E-READABILITY-REAL-SRPOSE38-API-READBACK-DESKTOP',head,
  provenance:manifest.images.map(({id,author,source_page,license,sha1,width,height})=>({id,author,source_page,license,sha1,width,height})),
  cases,blockedExternal:requests,invalidCount:cases.filter(x=>!x.valid).length,
  scope:'03B.3e visual readability on 03B.3d pinned SRPose38 authenticated SQLite API GET exports. Original model coordinates compared against every visible handle. Not a live-browser/API session, not certified anatomy. T1/T2 simulated only'};
await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({head, cases:cases.map(x=>({name:x.name,valid:x.valid,errors:x.errors})),
  blockedExternal:requests,invalidCount:report.invalidCount},null,2));
if(report.invalidCount||requests.length)process.exitCode=1;
