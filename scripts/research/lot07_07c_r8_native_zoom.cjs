// LOT07 / 07-C: actual GUI-host browser zoom attempt under Xvfb; NO CSS zoom or DPI emulation.
// Ephemeral Chromium window receives OS X11 Ctrl+plus shortcuts via xdotool.
// Never claim 200% unless its real CSS viewport halves on the same window.
const fs=require('fs');const path=require('path');const {execFileSync}=require('child_process');
const {createRequire}=require('module');const {pathToFileURL}=require('url');
const crypto=require('crypto');
const pw=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const inFile=path.resolve(process.argv[2]||'docs/research/lot07-07c-command-target-r8.html');
const dir=path.resolve(process.argv[3]||'artifacts/lot07-07c-r8');
fs.mkdirSync(dir,{recursive:true});
const send=(...args)=>execFileSync('xdotool',args,{encoding:'utf8',timeout:8000}).trim();
(async()=>{
 let browser,ctx,page;
 const evidence={method:'HEADFUL_CHROMIUM_XVFB_XDOTOOL_OS_KEYBOARD',actual_zoom_css_emulation:false,
   source:'R8_SYNTHETIC_TARGET_ONLY',window_focused:false,zoom200_proven:false,zoom_before:null,zoom_after:null,ratio:1,
   views:[],limitations:['Real Cabinet BEFORE not exercised','Patient data all synthetic']};
 try{
   browser=await pw.chromium.launch({headless:false,args:['--no-sandbox','--disable-dev-shm-usage','--window-size=1600,1100']});
   ctx=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1});
   page=await ctx.newPage();
   await page.goto(pathToFileURL(inFile).href,{waitUntil:'load'});
   evidence.zoom_before=await page.evaluate(()=>({innerWidth:innerWidth,clientWidth:document.documentElement.clientWidth,dpr:devicePixelRatio}));
   try {
     const wins=send('search','--onlyvisible','--class','chromium').split(/\s+/).filter(Boolean);
     evidence.window_candidate_count=wins.length;
     const win=wins.at(-1);
     if(win){send('windowfocus','--sync',win);evidence.window_focused=true;
       for(let i=0;i<5;i++){send('key','--clearmodifiers','ctrl+plus');await page.waitForTimeout(200);}
     }
   }catch(e){evidence.window_error=String(e.message).slice(0,140);}
   await page.waitForTimeout(600);
   evidence.zoom_after=await page.evaluate(()=>({innerWidth:innerWidth,clientWidth:document.documentElement.clientWidth,dpr:devicePixelRatio}));
   evidence.ratio=Number((evidence.zoom_before.clientWidth/evidence.zoom_after.clientWidth).toFixed(3));
   evidence.zoom200_proven=evidence.ratio>=1.9&&evidence.ratio<=2.1;
   for(const view of ['dashboard','agenda','dossier','imagerie']){
     await page.locator('[data-view="'+view+'"]').click();
     const state=await page.evaluate(()=>{
       const viewport=document.documentElement.clientWidth;
       const clipped=[];
       for(const el of document.querySelectorAll('.side,.nav,[data-view],.main,.top,.patient,.patient > *,.panel,.panel h2')){
         const r=el.getBoundingClientRect();
         if(r.width===0||r.height===0)continue;
         if(r.right>viewport+4||r.left< -4)clipped.push({type:el.tagName.toLowerCase(),className:String(el.className||'').slice(0,36),right:Math.round(r.right),viewport});
       }
       return {body:document.body.scrollWidth,viewport,visibleViews:document.querySelectorAll('.view:not(.hidden)').length,navVisibleButtons:Array.from(document.querySelectorAll('[data-view]')).filter(b=>b.getBoundingClientRect().width>0).length,clipped:clipped.slice(0,12)};
     });
     evidence.views.push({view,overflow:state.body>state.viewport+3,visible_views:state.visibleViews,nav_visible:state.navVisibleButtons,edge_clipped:state.clipped});
     if(evidence.zoom200_proven){
       const f=path.join(dir,'command-r8-'+view+'-1440-native-zoom200.png');
       await page.screenshot({path:f,fullPage:true,animations:'disabled'});
       evidence.views.at(-1).image=path.basename(f);evidence.views.at(-1).sha256=crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
     }
   }
 }finally{await ctx?.close();await browser?.close();}
 fs.writeFileSync(path.join(dir,'native-zoom-result.json'),JSON.stringify(evidence,null,2)+'\n');
 evidence.zoom200_layout_proven=evidence.zoom200_proven&&evidence.views.every(v=>!v.overflow&&v.nav_visible===4&&v.visible_views===1&&v.edge_clipped.length===0);
  console.log('COMMAND_R8_X11_NATIVE_ZOOM='+JSON.stringify(evidence));
})().catch(e=>{console.error('NATIVE_ZOOM_TEST_ERROR='+String(e.message).slice(0,220));process.exitCode=2});
