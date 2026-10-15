/** Isolated G1 theme-token browser proof. No production route or API is enabled. */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFileSync, writeFileSync, mkdirSync, rmSync, existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {chromium} from 'playwright';

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.resolve(frontend, '..');
const out = path.join(root, 'artifacts/v15-07-g1-theme-tokens');
mkdirSync(out,{recursive:true});
const component = readFileSync(path.join(frontend,'src/features/multiview/ViewSlotThemeFrame.tsx'),'utf8');
const css = readFileSync(path.join(frontend,'src/index.css'),'utf8');
const store = readFileSync(path.join(frontend,'src/features/admin/Settings/hooks/useSettingsStore.ts'),'utf8');
for(const token of ['bg-card','text-text-main','text-text-muted','border-border-main','bg-primary','text-on-primary','bg-input-field']){
 assert(component.includes(token),'missing semantic token '+token);
}
assert(!/#[0-9a-f]{3,8}\b/i.test(component),'hardcoded color in ViewSlot');
for(const token of ['--card-bg','--text-main','--border-color','--primary','--text-on-primary']) assert(css.includes(token));
assert(store.includes('document.documentElement.dataset.theme = finalTheme'));
assert(store.includes("setProperty('--primary', profile.primary_color)"));
const themes=['elite','emerald','rose','prestige','ocean','graphite','dark'];
for(const theme of themes.slice(1)) assert(css.includes("[data-theme='"+theme+"']"));
const html=path.join(frontend,'v15-07-g1-probe.html');
const tsx=path.join(frontend,'v15-07-g1-probe.tsx');
const config=path.join(frontend,'v15-07-g1-probe.config.mjs');
const temps=[html,tsx,config];
for(const file of temps) assert(!existsSync(file),'probe file path occupied: '+file);
writeFileSync(html,'<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><div id="root"></div><script type="module" src="/v15-07-g1-probe.tsx"></script></body></html>');
writeFileSync(tsx,[
 "import React from 'react';",
 "import {createRoot} from 'react-dom/client';",
 "import './src/index.css';",
 "import {ViewSlotThemeFrame} from './src/features/multiview/ViewSlotThemeFrame';",
 "function App(){",
 "  const [n,setN]=React.useState(0);",
 "  return <main className='min-h-screen bg-medical-pearl p-4 text-text-main'>",
 "    <div className='mx-auto max-w-5xl space-y-3'>",
 "      <p className='text-sm text-text-muted'>Digital Crown — vérification du thème actif (sonde technique isolée)</p>",
 "      <ViewSlotThemeFrame title='Dossier patient' description='Aucune donnée réelle' onExchange={()=>setN(n+1)} onEnlarge={()=>setN(n+1)}>",
 "        <p>Aucune donnée clinique réelle.</p><span data-count>{n}</span>",
 "      </ViewSlotThemeFrame>",
 "    </div>",
 "  </main>;",
 "}",
 "createRoot(document.getElementById('root')!).render(<App/>);"
].join('\n'));
writeFileSync(config,[
 "import {defineConfig} from 'vite';",
 "import tailwindcss from '@tailwindcss/postcss';",
 "export default defineConfig({ root: process.cwd(), css:{postcss:{plugins:[tailwindcss()]}},",
 " esbuild:{jsx:'automatic'}, server:{host:'127.0.0.1',port:5197,strictPort:true}, plugins:[] });"
].join('\n'));
const url='http://127.0.0.1:5197/v15-07-g1-probe.html';
let server=null, browser=null;
const errors=[],samples=[],screenshots=[];
function same(a,b){return a.replace(/\s+/g,'')===b.replace(/\s+/g,'');}
try{
 server=spawn(process.execPath,[path.join(root,'node_modules/vite/bin/vite.js'),'--config',config],{cwd:frontend,stdio:['ignore','pipe','pipe']});
 server.stdout.on('data',x=>process.stdout.write('[vite] '+x.toString().slice(0,300)));
 server.stderr.on('data',x=>process.stderr.write('[vite error] '+x.toString().slice(0,900)));
 let up=false;
 for(let attempt=0;attempt<130;attempt++){
   if(server.exitCode!==null) throw Error('Vite exited: '+server.exitCode);
   try{let r=await fetch(url);if(r.ok){up=true;break;}}catch{}
   await new Promise(r=>setTimeout(r,350));
 }
 assert(up,'Vite startup timeout');
 browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:900},locale:'fr-FR'});
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.status()>=500)errors.push(r.status()+' '+r.url());});
 await page.goto(url,{waitUntil:'networkidle',timeout:45000});
 const slot=page.locator('[data-v15-07-theme-slot]');
 await slot.waitFor({timeout:45000});
 assert.equal(await slot.count(),1);
 await page.getByRole('button',{name:'Échanger les vues'}).click();
 await page.getByRole('button',{name:'Agrandir cette vue'}).click();
 assert.equal(await page.locator('[data-count]').innerText(),'2');
 for(const theme of themes){
   const s=await page.evaluate(theme=>{
     document.documentElement.dataset.theme=theme==='elite'?'':theme;
     document.body.dataset.theme=theme==='elite'?'':theme;
     document.documentElement.style.removeProperty('--primary');
     document.body.style.removeProperty('--primary');
     const el=document.querySelector('[data-v15-07-theme-slot]');
     const inner=document.querySelector('[data-v15-07-theme-slot-content]');
     const btn=el.querySelectorAll('button')[1];
     const ref=document.createElement('div');
     ref.style.cssText='background:var(--card-bg);color:var(--text-main);border:1px solid var(--border-color)';
     const pri=document.createElement('div');
     pri.style.background='var(--primary)';
     document.body.append(ref,pri);
     const a=getComputedStyle(el),r=getComputedStyle(ref),c=getComputedStyle(inner);
     const ret={
       bg:a.backgroundColor,bgExpected:r.backgroundColor,
       fg:a.color,fgExpected:r.color,
       border:a.borderTopColor,borderExpected:r.borderTopColor,
       contentBg:c.backgroundColor,contentText:c.color,
       buttonBg:getComputedStyle(btn).backgroundColor,primaryExpected:getComputedStyle(pri).backgroundColor,
       scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth
     };
     ref.remove();pri.remove();return ret;
   },theme);
   for(const [a,b] of [['bg','bgExpected'],['fg','fgExpected'],['border','borderExpected'],['contentBg','bgExpected'],['contentText','fgExpected'],['buttonBg','primaryExpected']]){
     assert(same(s[a],s[b]),theme+' mismatch '+a+': '+s[a]+' vs '+s[b]);
   }
   assert(s.scrollWidth<=s.viewport,theme+' horizontal overflow');
   const f='theme-'+theme+'-1440.png';
   await page.screenshot({path:path.join(out,f),fullPage:true});
   screenshots.push(f);samples.push({theme,...s});
   console.log('THEME_OK '+theme+' '+s.bg+' '+s.fg+' '+s.buttonBg);
 }
 assert(!same(samples[0].bg,samples[3].bg),'dark must differ from default');
 for(const width of [1280,1920,2560,390]){
   await page.setViewportSize({width,height:900});
   const dims=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
   assert(dims.scroll<=dims.viewport,'horizontal overflow at '+width);
   const f='viewport-'+width+'.png';await page.screenshot({path:path.join(out,f),fullPage:true});screenshots.push(f);
 }
 await page.setViewportSize({width:1440,height:900});
 const custom=await page.evaluate(()=>{
   document.documentElement.style.setProperty('--primary','#ad5100');
   document.body.style.setProperty('--primary','#ad5100');
   return getComputedStyle(document.querySelectorAll('[data-v15-07-theme-slot] button')[1]).backgroundColor;
 });
 assert(same(custom,'rgb(173, 81, 0)'),'custom primary ignored: '+custom);
 const f='custom-primary.png';await page.screenshot({path:path.join(out,f),fullPage:true});screenshots.push(f);
 assert.deepEqual(errors,[],'browser errors');
 writeFileSync(path.join(out,'manifest.json'),JSON.stringify({
   gitHead:process.env.GITHUB_SHA||null,sourceBase:'9158902e034c22b162873d5fd44ea7afd45f3e16',
   proof:'React + canonical index.css compiled by Tailwind/PostCSS + real Chromium',
   realClinicalRoute:false,realAuth:false,viewSlotProductionEnabled:false,
   screens:screenshots,customPrimary:custom,errors,samples
 },null,2));
 console.log('V15_07_G1_THEME_PROOF_PASS '+JSON.stringify({themes:themes.length,screenshots:screenshots.length,errors:errors.length,customPrimary:custom}));
}catch(e){
 console.error('V15_07_G1_THEME_PROOF_FAIL '+String(e.stack||e));
 writeFileSync(path.join(out,'failure.json'),JSON.stringify({error:String(e.stack||e),errors,samples,screenshots},null,2));
 process.exitCode=1;
}finally{
 if(browser)await browser.close().catch(()=>{});
 if(server)server.kill('SIGTERM');
 for(const f of temps)rmSync(f,{force:true});
}
