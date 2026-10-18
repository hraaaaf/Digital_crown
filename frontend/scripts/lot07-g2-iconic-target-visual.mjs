/* G2 visual TARGET evidence only — no clinic runtime, auth, or patient data. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const head = process.env.SOURCE_HEAD;
if (!head || !/^[a-f0-9]{40}$/.test(head)) throw new Error('Missing immutable G2 source HEAD');
const output = path.resolve(root, '..', 'artifacts', 'v15-07-g2-iconic-target');
fs.mkdirSync(output, { recursive: true });
const htmlPath = path.join(root, 'v15-07-g2-isolated-target.html');
const entryPath = path.join(root, 'src/features/desktop-experience/.g2-target-isolated-entry.tsx');

const html = `<!doctype html>
<html lang="fr"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>LOT07 G2 — Signature Iconic isolated target</title>
<style>html,body,#g2-root{margin:0;min-height:100%;width:100%;}body{background:var(--bg-medical-pearl,#f3f6fb);}</style>
</head><body><div id="g2-root"></div>
<script type="module" src="/src/features/desktop-experience/.g2-target-isolated-entry.tsx"></script>
</body></html>`;
const entry = `import React from 'react';
import { createRoot } from 'react-dom/client';
import '../../index.css';
import { SignatureIconicTarget } from './SignatureIconicTarget';
const el = document.getElementById('g2-root');
if (!el) throw Error('G2 isolated root missing');
createRoot(el).render(React.createElement(SignatureIconicTarget));`;

let server;
let browser;
const results = [];
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const base = 'http://127.0.0.1:5179/v15-07-g2-isolated-target.html';
const pause = ms => new Promise(done => setTimeout(done, ms));

async function startVite() {
  // npm starts Vite/esbuild as children. A plain server.kill() terminates
  // only npm, leaving children alive with inherited stdout/stderr pipes and
  // preventing this Node proof process from exiting (G2 cancellation).
  // Use a dedicated Unix process group exclusively for this fixture.
  server = spawn('npm', ['run','dev','--','--host','127.0.0.1','--port','5179','--strictPort'],{
    cwd:root, env:{...process.env, NODE_ENV:'development'},
    detached:true, stdio:['ignore','pipe','pipe']
  });
  let stderr='';
  server.stdout.on('data', part => { stderr += String(part).slice(0,500); });
  server.stderr.on('data', part => { stderr += String(part).slice(0,500); });
  for (let n=0;n<120;n++) {
    if (server.exitCode!==null) throw Error('G2 Vite exited: '+stderr.slice(-1600));
    try {
      const response=await fetch(base);
      if (response.ok) return;
    } catch { /* wait for synthetic Vite server */ }
    await pause(500);
  }
  throw Error('G2 Vite did not become ready: '+stderr.slice(-1600));
}

const samples = [
  {name:'desktop1280',width:1280,height:900},
  {name:'desktop1440',width:1440,height:900},
  {name:'desktop1920',width:1920,height:1080},
  {name:'desktop2560',width:2560,height:1080},
  {name:'tablet768-fallback',width:768,height:1024},
  {name:'mobile430-fallback',width:430,height:932},
  {name:'mobile390-fallback',width:390,height:844},
  // 720 CSS px approximates native 200% zoom at physical 1440, BUT DOES
  // NOT certify Chromium native zoom. Exact native zoom stays OPEN.
  {name:'zoom200-css-proxy-not-native',width:720,height:900},
];
function assert(ok, message) {if(!ok)throw new Error(message);}

try {
  fs.writeFileSync(htmlPath,html,{flag:'wx'});
  fs.writeFileSync(entryPath,entry,{flag:'wx'});
  await startVite();
  browser = await chromium.launch({headless:true});
  for (const size of samples) {
    for (const theme of (size.name==='desktop1440' ? ['elite','prestige'] : ['elite'])) {
      const context=await browser.newContext({
        viewport:{width:size.width,height:size.height},
        locale:'fr-FR', colorScheme:theme==='prestige'?'dark':'light',
        reducedMotion:'reduce',
      });
      const page=await context.newPage();
      const pageErrors=[],backendCalls=[],serverErrors=[];
      page.on('pageerror', e=>pageErrors.push(String(e)));
      page.on('request', request=>{
        if(new URL(request.url()).pathname.startsWith('/api/'))backendCalls.push(request.url());
      });
      page.on('response', response=>{
        if(response.status()>=500)serverErrors.push(response.url()+':'+response.status());
      });
      // Set the fixture theme only AFTER the isolated React root has
      // mounted. CSS/HMR startup and React paint must complete before this
      // baseline; subsequent Core/Iconic clicks may not change the theme.
      await page.goto(base,{waitUntil:'networkidle',timeout:90000});
      const rootElement=page.locator('[data-v15-07-g2-target]');
      await rootElement.waitFor({state:'visible',timeout:20000});
      await page.evaluate(t=>{
        if (!document.documentElement) throw Error('G2 html root not created');
        document.documentElement.dataset.theme=t;
      },theme);
      assert(await page.evaluate(()=>document.documentElement.dataset.theme)===theme,
        'G2 could not establish a cabinet theme fixture: '+theme);
      const names=['Tableau de bord','Agenda','Dossier patient','Imagerie'];
      for(const name of names){
        assert(await page.getByRole('navigation',{name:'Écrans témoins'}).getByRole('button',{name}).count()===1,
          'G2 target missing '+name);
      }
      for(const selected of ['core','iconic']){
        if(selected==='iconic') await page.getByRole('group',{name:'Style à prévisualiser'})
          .getByRole('button',{name:/Signature Iconic/}).click();
        assert(await rootElement.getAttribute('data-preview-experience')===selected,
          'G2 style switch did not update state');
        assert(!pageErrors.length && !backendCalls.length && !serverErrors.length,
          'G2 target has runtime/backend error '+JSON.stringify({pageErrors,backendCalls,serverErrors}));
        const metrics=await page.evaluate(()=>{
          const root=document.querySelector('[data-v15-07-g2-target]');
          const nav=root?.querySelectorAll('nav button').length||0;
          return {
            viewport:innerWidth,
            documentWidth:document.documentElement.scrollWidth,
            nav,
            rootOverflow:!!root&&root.scrollWidth>root.clientWidth+1,
            preview:root?.getAttribute('data-preview-experience'),
            theme:document.documentElement.dataset.theme,
          };
        });
        assert(metrics.nav===4,'G2 four canonical surfaces missing');
        assert(metrics.documentWidth<=size.width+1&&!metrics.rootOverflow,
          'G2 horizontal overflow '+JSON.stringify(metrics));
        assert(metrics.theme===theme,
          'G2 altered cabinet palette '+JSON.stringify({
            expected:theme,actual:metrics.theme,size:size.name,selected,
            documentWidth:metrics.documentWidth,nav:metrics.nav
          }));
        const fileName=`g2-${size.name}-${theme}-${selected}.png`;
        const dest=path.join(output,fileName);
        await page.screenshot({path:dest,fullPage:true,animations:'disabled'});
        results.push({
          sourceHead:head,screen:'isolated-target',size:size.name,
          theme,preview:selected,width:size.width,height:size.height,
          screenshot:fileName,sha256:hash(dest),metrics,
          backendCalls:backendCalls.length,pageErrors:pageErrors.length,
          nativeZoomCertified:false,clinicalRuntimeCertified:false,
        });
      }
      // Prove navigation choice is retained when reverting from Iconic.
      await page.getByRole('navigation',{name:'Écrans témoins'})
        .getByRole('button',{name:'Imagerie'}).click();
      await page.getByRole('group',{name:'Style à prévisualiser'})
        .getByRole('button',{name:/Signature Core/}).click();
      assert(await page.getByRole('navigation',{name:'Écrans témoins'})
        .getByRole('button',{name:'Imagerie'}).getAttribute('aria-current')==='page',
        'G2 style reset lost chosen workspace');
      await context.close();
    }
  }
  const manifest={
    sourceHead:head,kind:'ISOLATED_G2_TARGET_NOT_CLINICAL_BEFORE_AFTER',
    captured:results.length,errors:0,items:results,
    mobileFeatureSupported:false,
    mobileFallbackOnly:true,clinicalRuntimeCertified:false,
    nativePageZoom200Certified:false,needsHumanVisualApproval:true,
  };
  assert(results.length===18,'Unexpected G2 screenshot count '+results.length);
  fs.writeFileSync(path.join(output,'manifest.json'),JSON.stringify(manifest,null,2));
  console.log('G2_TARGET_SCREENSHOT_COUNT='+results.length);
  console.log('G2_TARGET_SOURCE_HEAD='+head);
  console.log('G2_TARGET_BROWSER_PROOF=PASS_ISOLATED_ONLY');
  console.log('G2_NATIVE_ZOOM200=OPEN');
  console.log('G2_CLINICAL_RUNTIME=NOT_ENABLED');
} finally {
  if(browser)await browser.close().catch(()=>{});
  if (server) {
    // Kill the whole isolated Vite/npm/esbuild process group, not npm alone.
    // This is POSIX-only because CI runs on ubuntu-24.04; never signal any
    // unrelated runner process.
    if (Number.isInteger(server.pid) && server.pid > 0) {
      try { process.kill(-server.pid, 'SIGTERM'); }
      catch (error) {
        if (error.code !== 'ESRCH') throw error;
      }
    }
    server.stdout?.destroy();
    server.stderr?.destroy();
    server.unref();
    await pause(250);
  }
  for(const file of [entryPath,htmlPath]){
    try{fs.rmSync(file);}catch{/* clean temporary visual target */}
  }
}
