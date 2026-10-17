// LOT07 07-A P2 — AFTER only. Real current React, deterministic local API fixture.
// Never touches clinical databases or makes remote API writes.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { chromium } from 'playwright';
import { createServer } from 'vite';

const head=process.env.SOURCE_HEAD;
const parent=process.env.BASELINE_P1_HEAD;
if(!/^[0-9a-f]{40}$/.test(head||'')||parent!=='e7a359040840deb02c17c69593e982cfc192483e') throw Error('Pinned P1 baseline required');
if(process.env.ENVIRONMENT!=='test'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1') throw Error('Isolated visual fixture only');
const out=path.resolve('../artifacts/lot07-p2-agenda-after');
await fs.mkdir(out,{recursive:true});
const fixtureDay='2026-09-16';
const fixtureNow='2026-09-16T10:00:00+01:00';
const sizes=[[390,844],[430,932],[768,1024],[1280,900],[1440,900],[1920,1080],[2560,1440]];
const modes=[['week','agenda-week-view'],['day','agenda-day-view'],['month','agenda-month-view'],['multi','multi-practitioner-scroll']];
const patient=(id,name,pid,at,duration,motif,status='PRÉVU')=>({
  id,patient_name:name,patient_id:id+1000,praticien_id:pid,datetime_start:fixtureDay+'T'+at+':00',
  duration_minutes:duration,motif,status,scheduling_type:'EXACT_TIME',reminder_sent:false,
});
const lina=[patient(201,'Sara El Amrani',1,'09:00',30,'Consultation'),patient(202,'Adam Tazi',1,'11:00',45,'Endodontie','CONFIRMÉ')];
const youssef=[patient(211,'Yasmine Fassi',2,'09:00',60,'Prothèse','CONFIRMÉ'),patient(212,'Omar Bennani',2,'14:30',30,'Consultation')];
const salma=[patient(221,'Aya Alaoui',3,'10:30',30,'Contrôle')];
const legacy=[patient(299,'Non assigné (historique)',null,'12:00',30,'RDV historique')];
const all=[...lina,...youssef,...salma,...legacy];
const multi={plan:'ELITE',dentists:[
  {dentist_id:1,dentist_name:'Dr Lina Alaoui',appointments:lina},
  {dentist_id:2,dentist_name:'Dr Youssef Benali',appointments:youssef},
  {dentist_id:3,dentist_name:'Dr Salma Idrissi',appointments:salma}
],legacy_unassigned:legacy,total_appointments:all.length};
const weekly=Object.fromEntries(['monday','tuesday','wednesday','thursday','friday','saturday','sunday'].map(day=>[
  day,{is_open:true,is_continuous:false,morning_start:'09:00',morning_end:'13:00',
    afternoon_start:'14:00',afternoon_end:'18:00'}
]));
const settings={id:1,opening_time_morning:'09:00',closing_time_morning:'13:00',
 opening_time_afternoon:'14:00',closing_time_afternoon:'18:00',
 is_continuous:false,agenda_mode:'EXACT',use_tickets:false,weekly_schedule:weekly};
const json=body=>({status:200,contentType:'application/json',body:JSON.stringify(body)});
// These files exist ONLY in this disposable CI workspace, never in the product branch.
await fs.writeFile('lot07-p2-after.html','<!doctype html><html lang="fr"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body><div id="root"></div><script type="module" src="/src/lot07-p2-after.tsx"></script></body></html>');
await fs.writeFile('src/lot07-p2-after.tsx',[
  "import React from 'react';",
  "import {createRoot} from 'react-dom/client';",
  "import {MemoryRouter} from 'react-router-dom';",
  "import './index.css';",
  "import {AgendaPage} from './pages/AgendaPage';",
  "import {useAuthStore} from './stores/useAuthStore';",
  "const theme=new URLSearchParams(window.location.search).get('theme');",
  "for(const host of [document.documentElement,document.body]){if(theme==='dark')host.dataset.theme='dark';else delete host.dataset.theme;}",
  "useAuthStore.setState({user:{id:1,email:'p2-fixture@test.invalid',nom_complet:'Dr Lina Alaoui',role:'ADMIN',is_superadmin:false,permissions:{}} as any,isAuthenticated:true,isLoading:false,error:null});",
  "createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/agenda']}><div data-lot07-p2-after className='min-h-screen min-w-0 p-3 sm:p-4 lg:p-6' style={{backgroundColor:'var(--bg-main,#f8fafc)',color:'var(--text-main)'}}><AgendaPage/></div></MemoryRouter>);"
].join('\n'));
const vite=await createServer({server:{host:'127.0.0.1',port:4217,strictPort:true},clearScreen:false});
await vite.listen();
const browser=await chromium.launch({headless:true});
const rows=[];
const report={phase:'AFTER',source:'real AgendaPage/AgendaStudio React with synthetic intercepted API, NOT authenticated backend',
  sourceHead:head,p1Parent:parent,fixture:'synthetic 2026-09-16, six appointments, three practitioners and one legacy unassigned',
  themes:['elite','dark'],viewports:sizes,modes:modes.map(x=>x[0]),captures:rows};
async function attachFixture(page,violations){
  await page.route('**/api/**',async route=>{
    const req=route.request(),u=new URL(req.url()),p=u.pathname;
    if(req.method()!=='GET'){violations.push('unexpected mutation '+req.method()+' '+p);
      return route.fulfill({status:409,contentType:'application/json',body:'{"error":"AFTER must not mutate"}'});}
    if(p==='/api/appointments/multi-practitioner')return route.fulfill(json(multi));
    if(p==='/api/appointments/'||p.startsWith('/api/appointments?'))return route.fulfill(json(all));
    if(p==='/api/agenda/settings')return route.fulfill(json(settings));
    if(p==='/api/agenda/exceptions'||p==='/api/agenda/upcoming-holidays'||p==='/api/appointments/pending')return route.fulfill(json([]));
    if(p.startsWith('/api/patients/')||p.startsWith('/api/catalog/')||p.startsWith('/api/actes/'))return route.fulfill(json([]));
    // Log unexpected fixture endpoints, never claim they were real backend results.
    violations.push('unhandled intercepted GET '+p);
    return route.fulfill(json([]));
  });
}
async function runMatrix(page,theme,width,height,zoom=false){
  const failures=[],violations=[];
  page.on('pageerror',e=>failures.push(String(e.message).slice(0,300)));
  page.on('response',r=>{if(r.status()>=500)failures.push('HTTP '+r.status()+' '+new URL(r.url()).pathname);});
  await attachFixture(page,violations);
  await page.clock.setFixedTime(new Date(fixtureNow));
  await page.goto('http://127.0.0.1:4217/lot07-p2-after.html?theme='+theme,{waitUntil:'domcontentloaded',timeout:60000});
  await page.getByRole('heading',{name:'Agenda',exact:true}).waitFor({state:'visible',timeout:45000});
  const css=await page.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,outerWidth,scale:visualViewport?.scale??1,
    htmlTheme:document.documentElement.dataset.theme||'',bodyTheme:document.body.dataset.theme||''}));
  if((theme==='dark')!==(css.bodyTheme==='dark'&&css.htmlTheme==='dark'))throw Error('Dark visual baseline not activated '+JSON.stringify(css));
  if(zoom&&!(css.dpr>=1.9&&css.width>=600&&css.width<=850&&css.outerWidth>=1200&&css.scale===1))throw Error('Real native 200% zoom not proven '+JSON.stringify(css));
  const cdp=zoom?await page.context().newCDPSession(page):null;
  for(const [mode,testId] of modes){
    if(mode!=='week')await page.getByRole('button',{name:({day:'Jour',month:'Mois',multi:'Multi'})[mode],exact:true}).click();
    const area=page.getByTestId(testId);
    await area.waitFor({state:'visible',timeout:30000});
    if(mode==='multi')await page.getByText('09:00 · Sara El Amrani',{exact:true}).first().waitFor({state:'visible',timeout:20000});
    else if(mode==='month')await area.locator('[data-m4d-month-appointment]').filter({visible:true}).first().waitFor({state:'visible',timeout:20000});
    else await area.getByText('Sara El Amrani',{exact:false}).filter({visible:true}).first().waitFor({state:'visible',timeout:20000});
    const metric=await page.evaluate(()=>{
      const doc=document.documentElement;
      const internal=document.querySelector('[data-testid="multi-practitioner-scroll"]');
      return {viewportWidth:innerWidth,viewportHeight:innerHeight,dpr:devicePixelRatio,
        pageClientWidth:doc.clientWidth,pageScrollWidth:doc.scrollWidth,
        pageOverflow:doc.scrollWidth>doc.clientWidth+2,
        multiInnerScroll:internal?{clientWidth:internal.clientWidth,scrollWidth:internal.scrollWidth}:null,
        theme:document.body.dataset.theme||'elite'};
    });
    if(mode==='day'){
      const concurrent=await page.evaluate(()=>{
        const a=document.querySelector('[data-p2-day-appointment="201"]')?.getBoundingClientRect();
        const b=document.querySelector('[data-p2-day-appointment="211"]')?.getBoundingClientRect();
        if(!a||!b)return null;
        return {a:{left:a.left,right:a.right,top:a.top,bottom:a.bottom},
          b:{left:b.left,right:b.right,top:b.top,bottom:b.bottom}};
      });
      if(!concurrent||!(concurrent.a.right<=concurrent.b.left+2||concurrent.b.right<=concurrent.a.left+2))
        throw Error('P2 day simultaneous practitioner appointments visually overlap '+JSON.stringify({theme,width,concurrent}));
    }
    if(mode==='month'){
      const mobile=css.width<640;
      const mobileVisible=await page.locator('[data-p2-mobile-month-list]').isVisible();
      const gridVisible=await page.locator('[data-p2-month-grid]').isVisible();
      if(mobile?(!mobileVisible||gridVisible):(!gridVisible||mobileVisible))
        throw Error('P2 month responsive view not truthful '+JSON.stringify({theme,width,css,mobileVisible,gridVisible}));
      if(mobile){
        const dates=await page.locator('[data-p2-month-day]').count();
        const buttons=await page.locator('[data-p2-month-appointment]').filter({visible:true}).count();
        if(dates<1||buttons!==all.length)
          throw Error('P2 month missing actual dated appointment text '+JSON.stringify({theme,width,dates,buttons,expected:all.length}));
      }
    }
    if(theme==='dark'){
      const contrasts=await page.evaluate(()=>{
        const header=document.querySelector('[data-tour="agenda-header"]');
        const heading=header?.querySelector('h1');
        const date=header?.querySelector('span.text-slate-600');
        const inactive=header?.querySelector('[data-tour="agenda-view-switcher"] button[aria-pressed="false"]');
        if(!heading||!header||!date||!inactive)return null;
        const rgb=s=>{const a=s.match(/\d+(?:\.\d+)?/g);return a&&a.length>=3?a.slice(0,3).map(Number):null;};
        const lum=ch=>{const v=ch/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;};
        const L=c=>.2126*lum(c[0])+.7152*lum(c[1])+.0722*lum(c[2]);
        const panelColor=rgb(getComputedStyle(header).backgroundColor);
        if(!panelColor)return null;
        return [['title',heading],['date',date],['inactive-mode',inactive]].map(([label,el])=>{
          const foreground=rgb(getComputedStyle(el).color);
          if(!foreground)return {label,ratio:0};
          const a=L(foreground),b=L(panelColor);
          return {label,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
        });
      });
      if(!contrasts||contrasts.length!==3||contrasts.some(c=>c.ratio<4.5))
        throw Error('P2 Dark header title/date/inactive-mode WCAG <4.5:1 '+JSON.stringify({mode,width,contrasts}));
    }
    const filename='agenda-'+theme+'-'+mode+'-'+(zoom?'native200':width+'x'+height)+'.png';
    const target=path.join(out,filename);
    let physical=null;
    if(cdp){
      const shot=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,fromSurface:true});
      const buf=Buffer.from(shot.data,'base64');
      if(buf.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('CDP screenshot is not PNG');
      physical={width:buf.readUInt32BE(16),height:buf.readUInt32BE(20)};
      const expected={width:Math.round(css.width*css.dpr),height:Math.round(css.height*css.dpr)};
      if(Math.abs(physical.width-expected.width)>4||Math.abs(physical.height-expected.height)>6)
        throw Error('Truncated native zoom screenshot '+JSON.stringify({physical,expected}));
      await fs.writeFile(target,buf);
    }else await page.screenshot({path:target,fullPage:true,animations:'disabled'});
    const image=await fs.stat(target);
    if(image.size<5000)throw Error('Blank Agenda AFTER image '+filename);
    let zoomContent=null;
    if(cdp){
      // A full native physical screenshot can still contain only the header:
      // a 380px CSS viewport at zoom200 has no room for the full agenda below.
      // Keep that viewport AND an actual scroll-to-content compositor image.
      await area.evaluate(el=>{
        const r=el.getBoundingClientRect();
        window.scrollTo({top:Math.max(0,window.scrollY+r.top-8),behavior:'instant'});
      });
      const location=await area.evaluate(el=>{
        const r=el.getBoundingClientRect();
        return {top:r.top,bottom:r.bottom,height:r.height,scrollY:window.scrollY,
          viewport:innerHeight,visibleHeight:Math.max(0,Math.min(innerHeight,r.bottom)-Math.max(0,r.top))};
      });
      if(location.visibleHeight<Math.min(120,location.viewport*0.3))
        throw Error('Zoom200 Agenda content not in browser viewport '+JSON.stringify({mode,theme,location}));
      const contentFile='agenda-'+theme+'-'+mode+'-native200-content.png';
      const shot=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,fromSurface:true});
      const buf=Buffer.from(shot.data,'base64');
      if(buf.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')
        throw Error('Zoom200 scrolled content compositor is not PNG '+contentFile);
      const pixels={width:buf.readUInt32BE(16),height:buf.readUInt32BE(20)};
      if(Math.abs(pixels.width-physical.width)>4||Math.abs(pixels.height-physical.height)>6)
        throw Error('Zoom200 scrolled content screenshot physically cropped '+JSON.stringify({pixels,physical}));
      if(buf.length<5000)throw Error('Blank zoom200 scrolled Agenda '+contentFile);
      await fs.writeFile(path.join(out,contentFile),buf);
      zoomContent={file:contentFile,bytes:buf.length,pixels,location};
    }
    if(failures.length)throw Error('Agenda JS errors '+JSON.stringify(failures));
    if(violations.some(v=>v.startsWith('unexpected mutation')))throw Error('Agenda AFTER attempted mutation '+JSON.stringify(violations));
    rows.push({theme,mode,viewport:{width,height},zoomNative:zoom,css,metric,physical,zoomContent,
      file:filename,bytes:image.size,unhandledSyntheticEndpoints:[...new Set(violations)]});
  }
}
try {
  for(const theme of ['elite','dark']){
    for(const [w,h] of sizes){
      const context=await browser.newContext({viewport:{width:w,height:h},locale:'fr-FR',timezoneId:'Africa/Casablanca'});
      try{await runMatrix(await context.newPage(),theme,w,h);}
      finally{await context.close();}
    }
  }
}finally{await browser.close();}
const profile=await fs.mkdtemp(path.join(os.tmpdir(),'dc-p2-after-native-'));
await fs.mkdir(path.join(profile,'Default'),{recursive:true});
await fs.writeFile(path.join(profile,'Default','Preferences'),JSON.stringify({partition:{default_zoom_level:{x:Math.log(2)/Math.log(1.2)}}}));
let native;
try {
  for(const theme of ['elite','dark']){
    native=await chromium.launchPersistentContext(profile,{headless:true,channel:'chromium',
      viewport:null,locale:'fr-FR',timezoneId:'Africa/Casablanca',
      args:['--window-size=1440,900','--no-first-run','--no-default-browser-check']});
    try{await runMatrix(await native.newPage(),theme,1440,900,true);}
    finally{await native.close();native=null;}
  }
}finally{await native?.close();await fs.rm(profile,{force:true,recursive:true});await vite.close();}
if(rows.length!==64||rows.filter(r=>r.zoomContent?.file).length!==8)
  throw Error('AFTER requires 64 baseline scenes plus 8 scrolled zoom200 content proofs: '+rows.length);
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({
  ...report,sceneCount:rows.length,totalScreenshots:rows.length+8,
  note:'64 baseline scenes plus 8 real native-200 scrolled-to-agenda compositor views'
},null,2));
console.log('LOT07_P2_AGENDA_AFTER_SUCCESS '+JSON.stringify({head,baseline:parent,screens:rows.length+8,
  overflowCases:rows.filter(r=>r.metric.pageOverflow).map(r=>r.file),zoom:true,zoomContent:8}));
