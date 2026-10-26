/**
 * No-deploy synthetic render of the real WelcomeScreen component.
 * BASE and HEAD share component/markup; only five theme --text-muted values differ.
 * Browser screenshots are evidence, not human signoff or comprehensive accessibility.
 */
import { execFileSync } from 'node:child_process';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import { createServer } from 'vite';

const baseSha = process.env.THEME_CONTRAST_BASE_SHA || '';
const headSha = process.env.THEME_CONTRAST_HEAD_SHA || '';
const checkedOutSha = execFileSync('git',['rev-parse','HEAD'],{cwd:'..',encoding:'utf8'}).trim();
if (checkedOutSha !== headSha) throw new Error('Evidence HEAD mismatch: checkout='+checkedOutSha+' expected='+headSha);
if (!/^[0-9a-f]{40}$/.test(baseSha) || !/^[0-9a-f]{40}$/.test(headSha)) throw new Error('Exact base/HEAD SHA required');
const out = resolve('theme-contrast-visual-evidence');
const html = resolve('theme-contrast-aa-visual.html');
const entry = resolve('src/theme-contrast-aa-visual.tsx');
const themes = ['default','emerald','rose','ocean','graphite','prestige','dark','high-contrast'];
const viewports = [{width:390,height:844},{width:1280,height:900}];
const currentCss = await readFile('src/index.css','utf8');
const priorCss = execFileSync('git',['show',baseSha + ':frontend/src/index.css'],{cwd:'..',encoding:'utf8'});

function paletteMuted(css, theme) {
  const selector = theme === 'default' ? ':root' : "[data-theme='" + theme + "']";
  const escaped = selector.replace(/[.*+?^$()|[\]{}\\]/g,'\\$&');
  const rx = new RegExp(escaped + '\\s*\\{([^}]*)\\}', 'g');
  const candidates = [...css.matchAll(rx)].map(match => /--text-muted:\s*(#[0-9a-f]{6})\s*;/i.exec(match[1])?.[1]).filter(Boolean);
  if (candidates.length !== 1) throw new Error('Ambiguous palette token for ' + theme);
  return candidates[0].toLowerCase();
}
const beforeColors = Object.fromEntries(themes.map(theme=>[theme,paletteMuted(priorCss,theme)]));
const afterColors = Object.fromEntries(themes.map(theme=>[theme,paletteMuted(currentCss,theme)]));
const changed = themes.filter(theme=>beforeColors[theme] !== afterColors[theme]);
if (changed.join(',') !== 'default,emerald,rose,ocean,dark') throw new Error('Unexpected token change set: '+changed);
await mkdir(out,{recursive:true});
await writeFile(html,'<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Digital Crown Theme Proof</title></head><body><div id="root"></div><script type="module" src="/src/theme-contrast-aa-visual.tsx"></script></body></html>');
await writeFile(entry, [
 "import React from 'react';",
 "import { createRoot } from 'react-dom/client';",
 "import { MemoryRouter } from 'react-router-dom';",
 "import './index.css';",
 "import { WelcomeScreen } from './pages/WelcomeScreen';",
 "createRoot(document.getElementById('root')!).render(<MemoryRouter><WelcomeScreen /></MemoryRouter>);"
].join('\n'));
function linear(v) { return v <= 0.04045 ? v/12.92 : ((v+0.055)/1.055)**2.4; }
function rgbChannels(s) {
  const parts=/^rgba?\((\d+)[,\s]+(\d+)[,\s]+(\d+)/.exec(s);
  if(!parts) throw new Error('Non-RGB computed color '+s);
  return parts.slice(1,4).map(v=>Number(v)/255);
}
function ratio(a,b) {
  const luminance = s => {const v=rgbChannels(s).map(linear);return v[0]*0.2126+v[1]*0.7152+v[2]*0.0722;};
  const [x,y]=[luminance(a),luminance(b)].sort((m,n)=>n-m);
  return (x+0.05)/(y+0.05);
}
const report = {base_sha:baseSha,head_sha:headSha,component:'frontend/src/pages/WelcomeScreen.tsx',themes,viewports,changed,baseline:beforeColors,after:afterColors,checks:[],failures:[]};
let browser, server;
try {
  server = await createServer({server:{host:'127.0.0.1',port:4229,strictPort:true},clearScreen:false,optimizeDeps:{include:['react','react-dom/client','react-router-dom','lucide-react','workbox-window']}});
  await server.listen();
  browser = await chromium.launch({headless:true});
  for (const theme of themes) for (const viewport of viewports) {
    const context = await browser.newContext({viewport,deviceScaleFactor:1,locale:'fr-FR',timezoneId:'Africa/Casablanca',reducedMotion:'reduce'});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror',e=>errors.push('pageerror '+e.message));
    let loaded=false;
    for(let attempt=1;attempt<=3;attempt++) {
      try {
        const response=await page.goto('http://127.0.0.1:4229/theme-contrast-aa-visual.html?welcome_bg_before='+ (process.env.THEME_WELCOME_BG_BEFORE==='1'?'1':'0'),{waitUntil:'domcontentloaded',timeout:25000});
        if(!response || response.status()!==200) throw new Error('HTML status '+response?.status());
        await page.getByRole('heading',{name:/Digital Crown/}).waitFor({state:'visible',timeout:20000});
        loaded=true; break;
      }catch(e){if(attempt===3) throw e; await page.waitForTimeout(800);}
    }
    if(!loaded) throw new Error('Welcome component unavailable');
    await page.addStyleTag({content:'*,*::before,*::after { transition: none !important; animation: none !important; caret-color: transparent !important; }'});
    await page.evaluate(value=>{if(value==='default') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme=value;},theme);
    for(const phase of ['before','after']) {
      await page.evaluate(({phase,color})=>{
        if(phase==='before') document.documentElement.style.setProperty('--text-muted',color);
        else document.documentElement.style.removeProperty('--text-muted');
        if(window.location.search.includes('welcome_bg_before=1')) {
          const pageRoot=document.querySelector('div.min-h-screen');
          if(!pageRoot) throw new Error('WelcomeScreen background root missing');
          if(phase==='before') pageRoot.style.backgroundColor='#f8fafc';
          else pageRoot.style.removeProperty('background-color');
        }
      },{phase,color:beforeColors[theme]});
      await page.waitForTimeout(80);
      let state;
      for(let stableAttempt=1;stableAttempt<=4;stableAttempt++) {
        await page.getByRole('heading',{name:/Digital Crown/}).waitFor({state:'visible',timeout:20000});
        try {
          state=await page.evaluate(()=>{
        const anchors=[
          ['page-heading','h1'],
          ['page-description','.max-w-4xl > .text-center p'],
          ['card-heading','.max-w-md button h2'],
          ['card-description','.max-w-md button p'],
          ['footer','.max-w-4xl > p.text-text-muted']
        ];
        function closestOpaqueBackground(element) {
          for(let node=element;node;node=node.parentElement) {
            const c=getComputedStyle(node).backgroundColor;
            if(c && c!=='transparent' && c!=='rgba(0, 0, 0, 0)' && !/^rgba\([^)]*,\s*0\)$/.test(c)) return c;
          }
          return 'rgb(255, 255, 255)';
        }
        const samples=anchors.map(([label,selector])=>{
          const el=document.querySelector(selector);
          if(!el) throw new Error('Missing production anchor '+selector);
          return {label,color:getComputedStyle(el).color,background:closestOpaqueBackground(el),text:el.textContent?.trim().slice(0,70)};
        });
        return {samples,clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,computedMuted:getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim()};
          });
          break;
        } catch (error) {
          if(stableAttempt===4 || !/Missing production anchor|Execution context was destroyed/.test(String(error))) throw error;
          await page.waitForTimeout(500);
        }
      }
      state.samples.forEach(x=>{x.ratio=ratio(x.color,x.background);if(phase==='after' && x.ratio<4.5) report.failures.push(theme+' '+viewport.width+' '+x.label+' contrast '+x.ratio.toFixed(2)+' < 4.5');});
      if(state.scrollWidth>state.clientWidth) report.failures.push(theme+' '+viewport.width+' horizontal overflow');
      if(errors.length) report.failures.push(theme+' '+viewport.width+' '+errors.join('; '));
      const expected = phase==='before'?beforeColors[theme]:afterColors[theme];
      if(state.computedMuted.toLowerCase()!==expected) report.failures.push(theme+' '+viewport.width+' '+phase+' muted expected '+expected+' got '+state.computedMuted);
      report.checks.push({theme,viewport,phase,...state});
      await page.screenshot({path:resolve(out,phase+'-'+theme+'-'+viewport.width+'x'+viewport.height+'.png'),fullPage:true,animations:'disabled'});
    }
    await context.close();
  }
} finally {
  if(browser) await browser.close();
  if(server) await server.close();
  await rm(html,{force:true});
  await rm(entry,{force:true});
  await writeFile(resolve(out,'report.json'),JSON.stringify(report,null,2));
}
if(report.checks.length!==32) throw new Error('Expected 32 captures, got '+report.checks.length);
if(report.failures.length) throw new Error('Rendered contrast NOT CERTIFIED: '+report.failures.join(' | '));
console.log('WelcomeScreen rendered AA checks PASS for 8 themes x 2 viewports x before/after');
