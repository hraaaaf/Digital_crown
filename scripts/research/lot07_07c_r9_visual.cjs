// LOT07 / 07-C — only synthetic Command R9 TARGET checks, never Cabinet E2E.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {pathToFileURL}=require('url'),{createRequire}=require('module');
const {chromium}=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const target=path.resolve('docs/research/lot07-07c-command-target-r9.html');
const base=path.resolve('frontend/src/index.css');
const out=path.resolve('artifacts/lot07-07c-r9');fs.mkdirSync(out,{recursive:true});
const hash=x=>crypto.createHash('sha256').update(fs.readFileSync(x)).digest('hex');
const raw=fs.readFileSync(target,'utf8'),css=fs.readFileSync(base,'utf8');
if(/#[0-9a-f]{3,8}\b/i.test(raw.split('<style>')[1].split('</style>')[0]))throw Error('HARD_CODED_COLOR');
for(const x of ['--primary','--sidebar-bg','--card-bg','--bg-medical-pearl','--text-main','--status-warning'])if(!raw.includes('var('+x+','))throw Error('MISSING_TOKEN_'+x);
const themes=['elite','emerald','rose','prestige','ocean','graphite','dark','high-contrast'];
const views=['dashboard','agenda','dossier','imagerie'],widths=[1280,1440,1920];
const errs=[],snaps=[],themeColors=[];
const load=async(browser,width)=>{
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
  const page=await context.newPage();
  page.on('pageerror',e=>errs.push('RUNTIME_'+String(e.message).slice(0,90)));
  await page.route('**/*',r=>['file:','data:'].some(p=>r.request().url().startsWith(p))?r.continue():r.abort('blockedbyclient'));
  await page.goto(pathToFileURL(target).href,{waitUntil:'domcontentloaded'});
  await page.addStyleTag({content:css.replace(/@import\s+[^;]+;/g,'')});
  return {context,page};
};
async function snap(page,name){const file=path.join(out,name+'.png');await page.screenshot({path:file,fullPage:true,animations:'disabled'});snaps.push({name,sha256:hash(file),bytes:fs.statSync(file).size});}
function expectedColor(page,token){return page.evaluate(token=>{const x=document.createElement('i');x.style.color='var('+token+')';document.body.append(x);const c=getComputedStyle(x).color;x.remove();return c;},token);}
function geometry(page){return page.evaluate(()=>{
 const width=document.documentElement.clientWidth;
 const items=[...document.querySelectorAll('.rail,.work,.mast,.identity,.card,.metric,.nav button')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;});
 return {width,scroll:document.documentElement.scrollWidth,
 clipped:items.filter(e=>{const r=e.getBoundingClientRect();return r.left< -3||r.right>width+3;}).map(e=>String(e.className).slice(0,25)).slice(0,8)};
});}
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  for(const width of widths){
   const {page,context}=await load(browser,width);
   for(const view of views){
    await page.locator('[data-view="'+view+'"]').click();
    const g=await geometry(page);
    if(g.scroll>g.width+3||g.clipped.length)errs.push('VIEW_CLIPPED_'+view+'_'+width+':'+JSON.stringify(g));
    if(await page.locator('section[data-screen]:visible').count()!==1)errs.push('SINGLE_SCREEN_'+view+'_'+width);
    if(await page.locator('.identity-main strong').innerText()!=='Patient TEST-001')errs.push('PATIENT_CONTEXT_'+view+'_'+width);
    if(await page.locator('[data-view="'+view+'"]').getAttribute('aria-current')!=='page')errs.push('ACTIVE_NAV_'+view+'_'+width);
    await snap(page,view+'-'+width);
   }
   await context.close();
  }
  for(const theme of themes){
   const {page,context}=await load(browser,1440);
   await page.evaluate(t=>t==='elite'?document.documentElement.removeAttribute('data-theme'):document.documentElement.setAttribute('data-theme',t),theme);
   const primary=await expectedColor(page,'--primary'),side=await expectedColor(page,'--sidebar-bg'),card=await expectedColor(page,'--card-bg');
   const applied=await page.evaluate(()=>({primary:getComputedStyle(document.querySelector('[data-view="dashboard"]')).backgroundColor,
    side:getComputedStyle(document.querySelector('.rail')).backgroundColor,card:getComputedStyle(document.querySelector('.card')).backgroundColor}));
   if(applied.primary!==primary||applied.side!==side||applied.card!==card)errs.push('TOKEN_MISMATCH_'+theme);
   themeColors.push({theme,primary,side,card});
   await snap(page,'theme-'+theme);
   await context.close();
  }
  if(new Set(themeColors.map(x=>x.primary)).size!==8)errs.push('THEME_NOT_DISTINCT');
  const {page,context}=await load(browser,1440);
  await page.locator('[data-view="agenda"]').focus();await page.keyboard.press('Enter');
  if(await page.locator('#agenda').isHidden())errs.push('KEYBOARD_NAV');
  await page.locator('[data-view="dossier"]').click();
  await page.locator('[data-dossier-tab="tracking"]').focus();await page.keyboard.press('ArrowRight');
  if(await page.locator('[data-dossier-tab="clinical"]').getAttribute('aria-selected')!=='true')errs.push('KEYBOARD_DOSSIER');
  await page.locator('[data-view="imagerie"]').click();
  await page.locator('[data-media-tab="rvg"]').focus();await page.keyboard.press('ArrowRight');
  if(await page.locator('[data-media-tab="panoramic"]').getAttribute('aria-selected')!=='true')errs.push('KEYBOARD_MEDIA');
  await context.close();
 }finally{await browser.close();}
 const result={head:process.env.SOURCE_HEAD||'unknown',target_sha256:hash(target),source_css_sha256:hash(base),
  scope:'LOT07_07C_SYNTHETIC_TARGET_ONLY',theming:themeColors,screenshots:snaps,errors:errs,
  mobile_feature_tested:false,native_zoom200_tested:false,clinical_data_tested:false,product_after_validated:false,
  note:'R9 has its own different synthetic fixture versus R8/G0; screenshots are not a homologated before/after.'};
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(result,null,2)+'\n');
 console.log('COMMAND_R9_CHECK='+JSON.stringify({passed:errs.length===0,errors:errs,views:views.length,widths,themes:themes.length,captures:snaps.length,manifest_sha256:hash(path.join(out,'manifest.json')),clinical:false}));
 if(errs.length)process.exitCode=4;
})().catch(e=>{console.error('COMMAND_R9_ERROR='+String(e.stack||e).slice(0,1300));process.exitCode=2});