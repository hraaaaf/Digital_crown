import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const root=process.cwd();
const manifest=JSON.parse(await readFile(path.join(root,'scripts/fixtures/dc-ceph03b3c-public-cephalograms.json'),'utf8'));
const publicDir=path.join(root,'public/dc-ceph03b3c');
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
const assert=(cond,msg)=>{if(!cond)throw Error(msg)};
const near=(a,b)=>Math.abs(Number(a)-b)<0.5;
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
    const point=()=>page.locator('[data-ceph03b-drag-handle="Po"]');
    const pointX=async()=>Number(await stage().getAttribute('data-po-x'));
    const count=async attr=>Number(await stage().getAttribute(attr));
    // Attribute installed on each independently-keyed visual T1/T2 group;
    // stroke-dasharray is NOT a reliable proxy for landmark ghost identity.
    const ghostLines=async id=>page.locator('[data-ceph03b-ghost-layer="'+id+'"] line').count();
    try{
      const response=await page.goto(base+'?film='+radio.id+'&mode='+mode,{waitUntil:'networkidle'});
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
      const initialX=radio.width*0.35;
      assert(near(await pointX(),initialX),'Initial synthetic point coordinate');
      assert(await count('data-audit')===0,'Unexpected initial audit');
      const initialT1=await ghostLines('t1');
      const initialT2=await ghostLines('t2');
      record.initialGhostLines={t1:initialT1,t2:initialT2};
      assert(initialT1>0&&initialT2>0,'Expected independent T1 and T2 visual-only trace lines');
      await screenshot('initial');

      await point().focus();
      assert(await point().evaluate(node=>node===document.activeElement),'SVG keyboard focus failed');
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

      assert(record.consoleErrors.length===0,'Browser console errors');
      assert(record.navigationCount===1,'Unexpected Vite/PWA reload');
      assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),'Horizontal overflow');
      record.valid=true;
      record.decoded=decoded;
      record.initialX=initialX;
      record.currentX=await pointX();
      record.auditEvents=await count('data-audit');
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
const report={suite:'DC-CEPH03B3C-TWO-AUTHENTIC-RADIO-DESKTOP',head,
  provenance:manifest.images.map(({id,author,source_page,license,sha1,width,height})=>({id,author,source_page,license,sha1,width,height})),
  cases,blockedExternal:requests,invalidCount:cases.filter(x=>!x.valid).length,
  scope:'Two real CC-BY-SA radiographs, synthetic unverified anatomical point overlays; not a clinical test'};
await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({head, cases:cases.map(x=>({name:x.name,valid:x.valid,errors:x.errors})),
  blockedExternal:requests,invalidCount:report.invalidCount},null,2));
if(report.invalidCount||requests.length)process.exitCode=1;
