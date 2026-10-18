// Real X11/Chromium browser zoom, not CSS zoom and not Playwright scale.
const fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
const {createRequire}=require('node:module');
const pw=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const out=path.resolve('artifacts/lot07-07c-command-react');fs.mkdirSync(out,{recursive:true});
const evidence={method:'XVFB_XDOTOOL_REAL_NATIVE_ZOOM',source:'REACT_VITE_ISOLATED',before:null,after:null,ratio:null,zoom200:false,overflow:false,clipped:[],pass:false};
(async()=>{
 const browser=await pw.chromium.launch({headless:false,args:['--no-sandbox','--disable-dev-shm-usage','--window-size=1600,1100']});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1,reducedMotion:'reduce'});
  const page=await context.newPage();await page.goto('http://127.0.0.1:5193/command-target.html',{waitUntil:'networkidle'});
  evidence.before=await page.evaluate(()=>({css:document.documentElement.clientWidth,dpr:devicePixelRatio}));
  const wins=execFileSync('xdotool',['search','--onlyvisible','--class','chromium'],{encoding:'utf8'}).trim().split(/\s+/).filter(Boolean);
  if(!wins.length)throw Error('NO_GUI_CHROMIUM_WINDOW');
  execFileSync('xdotool',['windowfocus','--sync',wins.at(-1)]);
  for(let i=0;i<5;i++){execFileSync('xdotool',['key','--clearmodifiers','ctrl+plus']);await page.waitForTimeout(200);}
  await page.waitForTimeout(350);
  evidence.after=await page.evaluate(()=>({css:document.documentElement.clientWidth,dpr:devicePixelRatio,doc:document.documentElement.scrollWidth}));
  evidence.ratio=+(evidence.before.css/evidence.after.css).toFixed(3);
  evidence.zoom200=evidence.ratio>=1.9&&evidence.ratio<=2.1;
  const geom=await page.evaluate(()=>{const viewport=document.documentElement.clientWidth;const elems=['.cmd-shell','.cmd-main','.cmd-heading','.cmd-workbench','.cmd-agenda','.cmd-right','.cmd-patienthero'].map(s=>document.querySelector(s)).filter(Boolean);
   return {viewport,doc:document.documentElement.scrollWidth,clipped:elems.filter(e=>{const r=e.getBoundingClientRect();return r.right>viewport+4||r.left< -4}).map(e=>e.className)};
  });
  evidence.overflow=geom.doc>geom.viewport+3;evidence.clipped=geom.clipped;
  await page.screenshot({path:path.join(out,'command-react-1440-native-zoom200.png'),fullPage:true,animations:'disabled'});
  execFileSync('scrot',['-z','-o',path.join(out,'command-react-1440-native-zoom200-x11.png')],{timeout:15000});
  evidence.pass=evidence.zoom200&&!evidence.overflow&&!evidence.clipped.length;
  await context.close();
 }finally{await browser.close();}
 fs.writeFileSync(path.join(out,'native-zoom-result.json'),JSON.stringify(evidence,null,2)+'\n');
 console.log('REACT_NATIVE_ZOOM='+JSON.stringify(evidence));
 if(!evidence.pass)process.exitCode=5;
})().catch(e=>{console.error('REACT_NATIVE_ZOOM_ERROR='+e.message);process.exitCode=3});
