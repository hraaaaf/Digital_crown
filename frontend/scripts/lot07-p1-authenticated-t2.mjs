// LOT07 P1 actual protected patient route — disposable FastAPI/T2 only.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {chromium, request} from 'playwright';

if(process.env.ENVIRONMENT!=='test' || process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
  || process.env.DATABASE_URL!=='sqlite:///./t2-runtime-cert.db')
  throw Error('T2 evidence may only run against the isolated test DB');
const head=process.env.SOURCE_HEAD;
if(!/^[0-9a-f]{40}$/.test(head||''))throw Error('Missing exact candidate SHA');
const out=path.resolve('../artifacts/lot07-p1-actual-t2');
await fs.mkdir(out,{recursive:true});

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{
  form:{username:process.env.T2_USER,password:process.env.T2_PASSWORD},
});
if(!login.ok())throw Error('T2 login rejected HTTP '+login.status());
const tokens=await login.json();
const list=await api.get('/api/patients/',{headers:{Authorization:'Bearer '+tokens.access_token}});
if(!list.ok())throw Error('T2 patient list unavailable HTTP '+list.status());
const patients=await list.json();
if(!Array.isArray(patients))throw Error('Expected patient list');
const patient=patients.find(p=>p.numero_dossier==='T2-0001');
if(!patient||!Number.isInteger(patient.id))throw Error('Missing exact T2-0001 synthetic patient');
const detail=await api.get('/api/patients/'+patient.id,{headers:{Authorization:'Bearer '+tokens.access_token}});
if(!detail.ok())throw Error('Cannot verify active T2 patient history');
const record=await detail.json();
if(record.id!==patient.id)throw Error('Patient API ID mismatch');
if(typeof record.antecedents_medicaux==='string'&&record.antecedents_medicaux.trim())
  throw Error('T2-0001 fixture does not represent missing history — do not fabricate clinical unknown');
const name=[patient.nom,patient.prenom].filter(Boolean).join(' ');
const browser=await chromium.launch({headless:true});
const evidence=[];
async function inject(page,theme){
  await page.addInitScript(({access,refresh,theme})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('refresh_token',refresh||'');
    localStorage.setItem('appMode','prod');
    // The real cabinet profile remains authoritative; persisted storage is
    // deliberately empty so the product must hydrate from the real T2 backend.
    localStorage.removeItem('digitalcrown_theme');
  },{access:tokens.access_token,refresh:tokens.refresh_token,theme});
}
async function checkPage(page,theme,width,zoomNative=false){
  const errors=[],failures=[];
  // Settings profile is the source of truth, not an injected DOM/localStorage theme.
  // This endpoint writes only to the pre-proven disposable T2 SQLite database.
  const auth={Authorization:'Bearer '+tokens.access_token};
  const saved=await api.put('/api/clinics/me',{headers:auth,data:{selected_theme:theme}});
  if(!saved.ok())throw Error('T2 isolated theme update denied HTTP '+saved.status());
  const reread=await api.get('/api/clinics/me',{headers:auth});
  if(!reread.ok())throw Error('T2 isolated theme read unavailable HTTP '+reread.status());
  const clinic=await reread.json();
  if(clinic.selected_theme!==theme)throw Error('T2 backend theme truth mismatch '+JSON.stringify({expected:theme,received:clinic.selected_theme}));
  page.on('pageerror',e=>errors.push(String(e.message).slice(0,280)));
  page.on('response',r=>{if(r.status()>=500)failures.push({status:r.status(),path:new URL(r.url()).pathname});});
  await inject(page,theme);
  await page.goto('http://127.0.0.1:5173/patients/'+patient.id+'?tab=radiology&radioTab=media',{waitUntil:'domcontentloaded',timeout:90000});
  await page.getByText(name,{exact:false}).first().waitFor({state:'visible',timeout:60000});
  await page.getByRole('status',{name:'Antécédents médicaux non renseignés'}).waitFor({state:'visible',timeout:30000});
  const history=await page.getByRole('status',{name:'Antécédents médicaux non renseignés'}).innerText();
  if(!history.includes('ne confirme pas leur absence'))throw Error('Unknown history was misrepresented');
  const cta=page.getByRole('button',{name:'Compléter les antécédents dans la fiche patient'});
  if(await cta.count()!==1)throw Error('No unique protected dossier edit action');
  const note=page.locator('[data-v15-07-g1-inline-nba]');
  await note.waitFor({state:'visible',timeout:30000});
  const message=await note.innerText();
  if(!message.includes('Conseil clinique')||!message.includes('non exécutée'))
    throw Error('Actual backend NBA not displayed as text-only advice');
  const split=await page.locator('[data-v15-07-two-views]').count();
  const media=await page.locator('[data-testid="patient-media-timeline"]').count();
  const effectiveWidth=await page.evaluate(()=>innerWidth);
  if(split!==Number(effectiveWidth>=1280)||media!==1)
    throw Error('G1 split/reflow mismatch '+JSON.stringify({effectiveWidth,split,media}));
  if(effectiveWidth<600){
    const info=await page.getByText('Aucune information d’antécédents n’est enregistrée. Cela ne confirme pas leur absence.').boundingBox();
    const btn=await cta.boundingBox();
    if(!info||!btn||btn.y<info.y+info.height-1)throw Error('Mobile P1 CTA overlaps medical context');
  }
  if(theme==='dark'){
    // The app may briefly restore local preferences before fetching the backend.
    // Require the persisted T2 backend theme to win on BOTH runtime hosts.
    try {
      await page.waitForFunction(()=>document.body?.dataset.theme==='dark' && document.documentElement?.dataset.theme==='dark',null,{timeout:15000});
    } catch(error) {
      const actual=await page.evaluate(()=>({body:document.body?.dataset.theme||null,html:document.documentElement?.dataset.theme||null,stored:localStorage.getItem('digitalcrown_theme')}));
      throw Error('Actual T2 persisted Dark theme did not hydrate '+JSON.stringify({expected:theme,actual,cause:String(error)}));
    }
    const colors=await page.evaluate(()=>{
      const bodyStyle=getComputedStyle(document.body);
      const card=document.createElement('span');
      card.style.backgroundColor='var(--card-bg)';
      document.body.appendChild(card);
      const surface=getComputedStyle(card).backgroundColor;
      card.remove();
      return {surface,bodyTheme:document.body.dataset.theme,htmlTheme:document.documentElement.dataset.theme||null,
        tokens:{primary:bodyStyle.getPropertyValue('--primary').trim(),main:bodyStyle.getPropertyValue('--text-main').trim()}};
    });
    if(colors.bodyTheme!=='dark'||colors.htmlTheme!=='dark')throw Error('Dark DOM tokens not hydrated from cabinet profile '+JSON.stringify(colors));
    const rgb=(value)=>{
      const channels=value.match(/[0-9]+/g)?.slice(0,3).map(Number);
      return channels?.length===3?channels:null;
    };
    const luminance=channels=>channels.map(c=>{
      const n=c/255;return n<=0.04045?n/12.92:((n+0.055)/1.055)**2.4;
    }).reduce((sum,n,i)=>sum+n*[0.2126,0.7152,0.0722][i],0);
    const background=rgb(colors.surface);
    if(!background)throw Error('Unparseable real Dark card surface '+JSON.stringify(colors));
    for(const [name,target] of [['patient header',page.locator('h1').first()],
      ['Imagerie active tab',page.getByRole('button',{name:'Imagerie',exact:true})],
      ['Médiathèque active tab',page.getByRole('button',{name:'Médiathèque',exact:true})]]){
      const ink=await target.evaluate(el=>getComputedStyle(el).color);
      const foreground=rgb(ink);
      if(!foreground)throw Error('Unparseable Dark ink '+name+': '+ink);
      const hi=Math.max(luminance(foreground),luminance(background));
      const lo=Math.min(luminance(foreground),luminance(background));
      const contrast=(hi+0.05)/(lo+0.05);
      if(contrast<4.5)throw Error('Dark '+name+' contrast '+contrast.toFixed(2)+':1 below 4.5:1 '+JSON.stringify({ink,...colors}));
    }
  }
  if(theme==='elite'){
    const runtime=await page.evaluate(()=>({body:document.body?.dataset.theme||'',html:document.documentElement?.dataset.theme||'',stored:localStorage.getItem('digitalcrown_theme')}));
    if(runtime.body!==''||runtime.html!=='')throw Error('Elite T2 profile did not restore real root theme '+JSON.stringify(runtime));
  }
  const metrics=await page.evaluate(()=>({
    width:innerWidth,dpr:devicePixelRatio,outerWidth,visualScale:visualViewport?.scale||1,
    overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+2,
  }));
  if(metrics.overflow)throw Error('Horizontal overflow '+JSON.stringify(metrics));
  if(zoomNative && !(metrics.dpr>=1.9 && metrics.width>=600&&metrics.width<=850
    &&metrics.outerWidth>=1200&&metrics.visualScale===1&&split===0))
    throw Error('Native 200% zoom not demonstrated '+JSON.stringify(metrics));
  const file=theme+'-'+width+(zoomNative?'-native200':'')+'.png';
  // At Chrome's real 200% zoom, page.screenshot() serializes a CSS-sized PNG
  // while painting DPR2 pixels, effectively cropping the physical viewport to
  // its upper-left quadrant. Evidence must capture the COMPLETE compositor.
  // CDP uses the same authenticated browser and native zoom, not a simulated
  // CSS scale or new test-only route.
  const nativeCapture=zoomNative?await page.context().newCDPSession(page):null;
  const captureViewport=async(fileName)=>{
    const target=path.join(out,fileName);
    if(!nativeCapture){
      await page.screenshot({path:target,animations:'disabled',fullPage:false});
      return {bytes:(await fs.stat(target)).size};
    }
    const response=await nativeCapture.send('Page.captureScreenshot',{
      format:'png',captureBeyondViewport:false,fromSurface:true,
    });
    const image=Buffer.from(response.data,'base64');
    if(image.length<24||image.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')
      throw Error('Native 200% compositor screenshot is not PNG '+fileName);
    const size={width:image.readUInt32BE(16),height:image.readUInt32BE(20)};
    const cssHeight=await page.evaluate(()=>innerHeight);
    const expected={width:Math.round(metrics.width*metrics.dpr),
      height:Math.round(cssHeight*metrics.dpr)};
    if(Math.abs(size.width-expected.width)>4||Math.abs(size.height-expected.height)>6)
      throw Error('Native 200% PNG does not cover physical browser viewport '+
        JSON.stringify({fileName,size,expected,cssWidth:metrics.width,cssHeight,dpr:metrics.dpr}));
    await fs.writeFile(target,image);
    return {bytes:image.length,physicalPixels:size,expected};
  };
  let nativeZoomClinicalProof=null;
  if(zoomNative){
    // The Chrome 200% DPR check above proves zoom, NOT the ability to read
    // content. Prove actual scroll-into-viewport access to each clinical fact.
    // Capture browser viewports (not locator crops, simulated zoom or DOM-only
    // screenshots), and fail closed when scrolling cannot expose the content.
    nativeZoomClinicalProof=[];
    for(const [kind,locator,minPixels,minFraction] of [
      ['history',page.getByRole('status',{name:'Antécédents médicaux non renseignés'}),110,0.75],
      ['advice',page.locator('[data-v15-07-g1-inline-nba]'),95,0.55],
      ['media',page.locator('[data-testid="patient-media-timeline"]'),90,0.15],
    ]){
      await locator.scrollIntoViewIfNeeded();
      // scrollIntoViewIfNeeded does not center an element ALREADY visible near
      // the viewport bottom. Reposition the real MainLayout scrolling surface,
      // so the screenshot proves its clinical CONTENT rather than only a header.
      await locator.evaluate(el=>{
        const scroller=el.closest('main.custom-scrollbar');
        if(!scroller)throw Error('Missing real patient route scrolling container at native 200%');
        const r=el.getBoundingClientRect();
        const clip=scroller.getBoundingClientRect();
        const delta=r.height<=clip.height
          ? r.top+r.height/2-(clip.top+clip.height/2)
          : r.top-clip.top-16;
        scroller.scrollTo({top:scroller.scrollTop+delta,behavior:'instant'});
      });
      const geometry=await locator.evaluate(el=>{
        const r=el.getBoundingClientRect();
        const view={width:innerWidth,height:innerHeight};
        const scroller=el.closest('main.custom-scrollbar');
        const clip=scroller?.getBoundingClientRect();
        const visibleTop=Math.max(0,r.top,clip?.top??0);
        const visibleBottom=Math.min(view.height,r.bottom,clip?.bottom??view.height);
        const visibleHeight=Math.max(0,visibleBottom-visibleTop);
        const visibleLeft=Math.max(0,r.left,clip?.left??0);
        const visibleRight=Math.min(view.width,r.right,clip?.right??view.width);
        const visibleWidth=Math.max(0,visibleRight-visibleLeft);
        const centerX=Math.max(1,Math.min(view.width-2,(visibleLeft+visibleRight)/2));
        const centerY=Math.max(1,Math.min(view.height-2,(visibleTop+visibleBottom)/2));
        const onTop=document.elementFromPoint(centerX,centerY);
        return {view,rect:{x:r.x,y:r.y,width:r.width,height:r.height},
          visibleHeight,visibleWidth,visibleFraction:r.height?visibleHeight/r.height:0,
          unobstructed:Boolean(onTop&&(el===onTop||el.contains(onTop))),
          scroll:scroller?{top:scroller.scrollTop,height:scroller.clientHeight,
            contentHeight:scroller.scrollHeight}:null};
      });
      // Store deterministic diagnostic even on failure. Artifacts remain
      // restricted to synthetic test-patient geometry, never credentials.
      await fs.writeFile(path.join(out,'native200-'+kind+'-geometry.json'),JSON.stringify(geometry,null,2));
      // A 95.5px-tall status cannot satisfy a fixed 110px visible-height
      // minimum even when 100% of its real pixels are visible. Bound minimums
      // by intrinsic element height AND the 200%-zoom scroll viewport.
      const clipHeight=geometry.scroll?.height||geometry.view.height;
      const requiredPixels=Math.min(minPixels,geometry.rect.height*0.75,clipHeight*0.5);
      const requiredFraction=Math.min(minFraction,0.7*clipHeight/Math.max(1,geometry.rect.height));
      if(!geometry.scroll||geometry.visibleHeight<requiredPixels
        ||geometry.visibleFraction<requiredFraction
        ||geometry.visibleWidth<100||!geometry.unobstructed){
        throw Error('Native 200% clinical content not viewable '+kind+' '+JSON.stringify({requiredPixels,requiredFraction,...geometry}));
      }
      const proofFile='elite-1440-native200-'+kind+'-viewport.png';
      const proof=await captureViewport(proofFile);
      if(proof.bytes<9000)throw Error('Empty native 200% clinical proof '+proofFile);
      nativeZoomClinicalProof.push({kind,file:proofFile,bytes:proof.bytes,
        physicalPixels:proof.physicalPixels,geometry});
    }
    if(nativeZoomClinicalProof.length!==3)
      throw Error('Missing 200% clinical status, advice or media viewport evidence');
  }
  const image=await captureViewport(file);
  if(image.bytes<12000)throw Error('Blank image evidence '+file+' size='+image.bytes);
  if(errors.length||failures.length)throw Error('Browser errors '+JSON.stringify({errors,failures}));
  evidence.push({theme,width,zoomNative,split,media,metrics,file,imageBytes:image.bytes,
    nativeZoomPhysicalPixels:image.physicalPixels||null,nativeZoomClinicalProof,
    description:'Authentic authenticated protected React patient route, disposable T2 FastAPI, no HTTP mocks'});
}
try{
  for(const theme of ['elite','dark']){
    for(const width of [1440,390]){
      const context=await browser.newContext({viewport:{width,height:900},locale:'fr-FR'});
      try{await checkPage(await context.newPage(),theme,width);}
      finally{await context.close();}
    }
  }
} finally{await browser.close();}
const zoomDir=await fs.mkdtemp(path.join(os.tmpdir(),'dc-p1-native-'));
await fs.mkdir(path.join(zoomDir,'Default'),{recursive:true});
const zoomLevel=Math.log(2)/Math.log(1.2);
await fs.writeFile(path.join(zoomDir,'Default','Preferences'),
  JSON.stringify({partition:{default_zoom_level:{x:zoomLevel}}}));
let zoomContext;
try{
  zoomContext=await chromium.launchPersistentContext(zoomDir,{
    headless:true,channel:'chromium',viewport:null,locale:'fr-FR',
    args:['--window-size=1440,900','--no-first-run','--no-default-browser-check'],
  });
  const storage=await api.storageState();
  if(!storage.cookies?.length)throw Error('No T2 workstation cookie for native-zoom browser');
  await zoomContext.addCookies(storage.cookies);
  await checkPage(await zoomContext.newPage(),'elite',1440,true);
} finally{await zoomContext?.close();await fs.rm(zoomDir,{force:true,recursive:true});await api.dispose();}
if(evidence.length!==5)throw Error('Five authentic captures required');
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({
  exactProductHead:head,runnerHead:process.env.GITHUB_SHA,
  fixture:'disposable T2-0001 from backend API',auth:'real API + enrolled workstation',
  nativeZoom:'Chrome profile default_zoom_level verified by DPR and CSS innerWidth',
  count:evidence.length,evidence,
},null,2));
console.log('LOT07_P1_AUTHENTIC_T2_SUCCESS '+JSON.stringify({head,records:evidence.length,nativeZoom:true}));
