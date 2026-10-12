import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const out = path.join(root, 'dc-ceph03b3-keyboard-zoom-artifacts');
const fileName = 'ceph03b3-keyboard-zoom.html';
const port = 5197;
const url = 'http://127.0.0.1:' + port + '/' + fileName;
const sourceHead = process.env.GITHUB_SHA || process.env.PRODUCT_HEAD || 'unknown';
const html = '<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body style="margin:0"><div id="root"></div><script type="module" src="/src/features/ortho/CephaloTracingLayer.visualFixture.tsx"></script></body></html>';
const viewports = [{ width:1280,height:900 },{ width:1600,height:1000 }];
const modes = [{ mode:'com', line:'com-frankfort' },{ mode:'all', line:'ricketts-frankfort' }];
const captures = [];
const blockedExternal = [];
await rm(out,{recursive:true,force:true});
await mkdir(out,{recursive:true});
await writeFile(path.join(root,fileName),html);
const server=spawn(path.join(root,'node_modules','.bin','vite'),['--host','127.0.0.1','--port',String(port)],{cwd:root,env:{...process.env,BROWSER:'none'},stdio:['ignore','pipe','pipe']});
let serverLog='';
server.stdout.on('data',chunk=>serverLog+=chunk);
server.stderr.on('data',chunk=>serverLog+=chunk);
const assert=(condition,message)=>{if(!condition)throw Error(message)};
const near=(a,b)=>Number.isFinite(a)&&Math.abs(a-b)<0.4;
const browser=await chromium.launch({headless:true});
try{
  let started=false;
  for(let i=0;i<120;i++){
    try{const r=await fetch(url);if(r.ok){started=true;break}}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  assert(started,'Vite start timeout');
  for(const viewport of viewports)for(const m of modes){
    const context=await browser.newContext({viewport,locale:'fr-FR',reducedMotion:'reduce'});
    const page=await context.newPage();
    const errors=[];
    const consoleErrors=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',msg=>{if(msg.type()==='error')consoleErrors.push(msg.text())});
    await page.route('**/*',async route=>{
      const u=new URL(route.request().url());
      if(u.hostname==='127.0.0.1'&&u.port===String(port))return route.continue();
      // Never fetch externally: neutralize the known optional stylesheet in-memory.
      if(u.hostname==='fonts.googleapis.com')return route.fulfill({status:200,contentType:'text/css',body:''});
      blockedExternal.push(route.request().url());
      return route.abort('blockedbyclient');
    });
    const key=viewport.width+'x'+viewport.height+'-'+m.mode;
    const record={viewport:key.split('-')[0],mode:m.mode,valid:false,images:[],errors};
    const screenshot=async state=>{const filename=key+'-'+state+'.png';await page.screenshot({path:path.join(out,filename)});record.images.push(filename)};
    const line=()=>page.locator('[data-r19-construction="'+m.line+'"],[data-r18-construction="'+m.line+'"]');
    const point=()=>page.locator('[data-ceph03b-drag-handle="Po"]');
    const xy=()=>line().evaluate(el=>({x:Number(el.getAttribute('x1')),y:Number(el.getAttribute('y1'))}));
    const counter=()=>page.locator('[data-commit-count]').getAttribute('data-commit-count');
    const screenPosition=async(x,y)=>point().evaluate((el,p)=>{
      const svg=el.ownerSVGElement;
      const ctm=svg?.getScreenCTM();
      if(!ctm)throw Error('Missing screen CTM');
      const q=svg.createSVGPoint();q.x=p.x;q.y=p.y;
      const o=q.matrixTransform(ctm);
      return {x:o.x,y:o.y,matrixA:ctm.a};
    },{x,y});
    try{
      const response=await page.goto(url+'?mode='+m.mode+'&zoom=125',{waitUntil:'domcontentloaded'});
      assert(response?.status()===200,'Fixture failed');
      await point().waitFor({state:'attached'});
      await line().waitFor({state:'attached'});
      assert(await page.locator('[data-ceph03b-zoom="1.25"]').count()===1,'Zoom wrapper missing');
      const start=await xy();
      assert(near(start.x,30)&&near(start.y,40),'Initial construction wrong: '+JSON.stringify(start));
      await screenshot('initial');

      await point().focus();
      const focusState=await point().evaluate(el=>document.activeElement===el);
      assert(focusState,'SVG landmark is not keyboard focusable');
      await point().press('ArrowRight');
      assert(await counter()==='1','Keyboard step not persisted once');
      let value=await xy();
      assert(near(value.x,31)&&near(value.y,40),'One pixel keyboard geometry wrong '+JSON.stringify(value));
      await point().press('Shift+ArrowRight');
      assert(await counter()==='2','Coarse keyboard step not persisted once');
      value=await xy();
      assert(near(value.x,41)&&near(value.y,40),'Ten pixel keyboard geometry wrong '+JSON.stringify(value));
      await screenshot('keyboard');

      const before=await screenPosition(41,40);
      const after=await screenPosition(65,75);
      const baseMatrix=await page.locator('[data-ceph03b-browser-fixture] svg').first().evaluate(svg=>svg.getScreenCTM()?.a);
      assert(near(before.matrixA,baseMatrix)&&before.matrixA>1.25,'CTM did not incorporate zoom');
      await page.mouse.move(before.x,before.y);
      await page.mouse.down();
      await page.mouse.move(after.x,after.y,{steps:5});
      // The pointer capture must move the real reticle under the transformed CTM.
      await page.waitForFunction(()=>{
        const el=document.querySelector('[data-ceph03b-drag-handle="Po"] circle');
        return el&&Math.abs(Number(el.getAttribute('cx'))-65)<0.4
                 &&Math.abs(Number(el.getAttribute('cy'))-75)<0.4;
      },null,{timeout:6000});
      assert(await counter()==='2','Pointer preview persisted prematurely');
      value=await xy();
      assert(near(value.x,65)&&near(value.y,75),'Overlay failed to track zoomed drag '+JSON.stringify(value));
      await screenshot('preview');
      await point().dispatchEvent('pointercancel',{pointerId:1,bubbles:true});
      await page.mouse.up();
      await page.waitForTimeout(90);
      assert(await counter()==='2','Cancelled zoom pointer persisted');
      value=await xy();
      assert(near(value.x,41)&&near(value.y,40),'Cancel failed under zoom');
      await screenshot('cancel');

      const initialScreen=await screenPosition(41,40);
      const finalScreen=await screenPosition(65,75);
      await page.mouse.move(initialScreen.x,initialScreen.y);
      await page.mouse.down();
      await page.mouse.move(finalScreen.x,finalScreen.y,{steps:6});
      await page.mouse.up();
      await page.waitForFunction(()=>document.querySelector('[data-commit-count]')?.getAttribute('data-commit-count')==='3',null,{timeout:5000});
      value=await xy();
      assert(near(value.x,65)&&near(value.y,75),'Zoomed pointer up coordinates corrupted');
      await screenshot('commit');
      assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1)),'Horizontal overflow');
      assert(errors.length===0&&consoleErrors.length===0,'Browser console/page errors');
      record.valid=true;
      record.focusState=focusState;
      record.matrixA=before.matrixA;
      record.final=value;
      record.commits=await counter();
      record.consoleErrors=consoleErrors;
    }catch(e){
      record.errors.push(String(e));
      await screenshot('failure').catch(()=>{});
    }finally{
      captures.push(record);
      await context.close();
    }
  }
}finally{
  await browser.close();
  server.kill('SIGTERM');
  await writeFile(path.join(out,'vite.log'),serverLog);
}
const report={suite:'DC-CEPH03B3-KEYBOARD-ZOOM',sourceHead,fixture:'synthetic',captures,blockedExternal,invalidCount:captures.filter(c=>!c.valid).length};
await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
if(report.invalidCount||blockedExternal.length)process.exitCode=1;
