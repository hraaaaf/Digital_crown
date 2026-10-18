// LOT07/07-C Command R8: verify CSS-token inheritance against CURRENT Cabinet source CSS.
// Never fake or redefine palette values in this file.
const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const {pathToFileURL}=require('url');
const {createRequire}=require('module');
const playwright=createRequire(path.join(process.env.PLAYWRIGHT_LIB||'/tmp/lot07-07c-playwright','package.json'))('playwright');
const html=path.resolve(process.argv[2]||'docs/research/lot07-07c-command-target-r8.html');
const sourceCSS=path.resolve(process.argv[3]||'frontend/src/index.css');
const output=path.resolve(process.argv[4]||'artifacts/lot07-07c-r8');
fs.mkdirSync(output,{recursive:true});
const sha=x=>crypto.createHash('sha256').update(fs.readFileSync(x)).digest('hex');
const raw=fs.readFileSync(html,'utf8');
const source=fs.readFileSync(sourceCSS,'utf8');
const requiredTokens=['--primary','--sidebar-bg','--card-bg','--text-main','--text-muted','--bg-medical-pearl','--input-bg','--border-color','--text-on-primary','--status-warning-surface'];
for(const name of requiredTokens) {
  if(!raw.includes('var('+name+','))throw Error('MISSING_CONSUMED_TOKEN_'+name);
  if(!source.includes(name+':'))throw Error('MISSING_CANONICAL_TOKEN_'+name);
}
const inlineStyle=raw.split('<style>')[1]?.split('</style>')[0]||'';
if(/#[0-9a-f]{3,8}\b/i.test(inlineStyle))throw Error('HARD_CODED_BRAND_HEX_IN_TARGET');
const themes=['elite','emerald','rose','prestige','ocean','graphite','dark','high-contrast'];
const views=['dashboard','agenda','dossier','imagerie'];
const samples=[],issues=[],files=[];
(async()=>{
  const browser=await playwright.chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  try{
    for(const theme of themes) {
      const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
      const page=await context.newPage();
      await page.route('**/*',route=>{
        const u=route.request().url();
        if(u.startsWith('file:')||u.startsWith('data:'))return route.continue();
        return route.abort('blockedbyclient');
      });
      await page.goto(pathToFileURL(html).href,{waitUntil:'load'});
      // The source CSS is loaded at runtime. No hand-copied colors, CSS token proxy, or theme fork.
      await page.addStyleTag({path:sourceCSS});
      await page.evaluate(theme=>{
        if(theme==='elite')document.documentElement.removeAttribute('data-theme');
        else document.documentElement.setAttribute('data-theme',theme);
      },theme);
      const probe=await page.evaluate(()=>{
        function resolveColor(value){
          const el=document.createElement('span');
          el.style.color=value;document.body.appendChild(el);
          const c=getComputedStyle(el).color;el.remove();return c;
        }
        const css=s=>getComputedStyle(document.querySelector(s));
        const actual={
          primary:resolveColor('var(--primary)'),
          sidebar:resolveColor('var(--sidebar-bg)'),
          card:resolveColor('var(--card-bg)'),
          text:resolveColor('var(--text-main)'),
          muted:resolveColor('var(--text-muted)'),
          bg:resolveColor('var(--bg-medical-pearl)'),
          input:resolveColor('var(--input-bg)'),
          activeText:resolveColor('var(--text-on-primary)'),
          warning:resolveColor('var(--status-warning-surface)'),
        };
        return {tokens:actual,
          applied:{
            navBackground:css('[aria-current="page"]').backgroundColor,
            navText:css('[aria-current="page"]').color,
            sidebar:css('.side').backgroundColor,
            panel:css('.panel').backgroundColor,
            body:css('html').backgroundColor,
            patient:css('.patient').backgroundColor,
            warning:css('.warning').backgroundColor,
          }};
      });
      for(const [a,b,key] of [
        ['navBackground','primary','ACTIVE_BACKGROUND'],
        ['navText','activeText','ACTIVE_CONTRAST_TOKEN'],
        ['sidebar','sidebar','SIDEBAR'],
        ['panel','card','CARD'],
        ['body','bg','BACKGROUND'],
        ['patient','input','PATIENT_PANEL'],
        ['warning','warning','WARNING_STATUS']]){
        if(probe.applied[a]!==probe.tokens[b])issues.push(theme+'_'+key+'_MISMATCH');
      }
      for(const view of views) {
        await page.locator('[data-view="'+view+'"]').click();
        if(!(await page.locator('#'+view).isVisible()))issues.push(theme+'_'+view+'_HIDDEN');
        if((await page.locator('.view:not(.hidden)').count())!==1)issues.push(theme+'_'+view+'_MULTIPLE_ACTIVE');
      }
      if((await page.locator('[data-view][aria-current="page"]').count())!==1)issues.push(theme+'_CURRENT_NAV_COUNT');
      await page.locator('[data-view="dashboard"]').click();
      const dest=path.join(output,'command-r8-'+theme+'-1440-token-inheritance.png');
      await page.screenshot({path:dest,fullPage:true,animations:'disabled'});
      files.push({theme,file:path.basename(dest),sha256:sha(dest)});
      samples.push({theme,sourceCSS_sha256:sha(sourceCSS),active:probe.applied.navBackground,sidebar:probe.applied.sidebar,panel:probe.applied.panel,background:probe.applied.body,
        statusWarning:probe.applied.warning,token_contract_pass:!issues.some(x=>x.startsWith(theme+'_'))});
      await context.close();
    }
  }finally{await browser.close();}
  // Distinct themes should not silently collapse into the previous hard-coded green.
  if(new Set(samples.map(x=>x.active)).size<4)issues.push('PRIMARY_THEME_VARIATION_MISSING');
  if(new Set(samples.map(x=>x.sidebar)).size<4)issues.push('SIDEBAR_THEME_VARIATION_MISSING');
  const result={scope:'LOT07_07C_R8_TARGET_ONLY',target_sha256:sha(html),canonical_source:'frontend/src/index.css',
    source_css_sha256:sha(sourceCSS),static_hex_color_count:0,completely_theme_inherited:issues.length===0,themes:samples,files,issues,
    limitations:'CSS inherited only in a Playwright harness; this standalone preview is not integrated into the Cabinet. No real patient records, persistence, or 07-D selection.'};
  fs.writeFileSync(path.join(output,'theme-inheritance-manifest.json'),JSON.stringify(result,null,2)+'\n');
  console.log('COMMAND_R8_THEME_INHERITANCE='+JSON.stringify({tested_themes:themes,source_css_sha256:result.source_css_sha256,passed:issues.length===0,issues,distinct_primary_colors:new Set(samples.map(x=>x.active)).size,distinct_sidebar_colors:new Set(samples.map(x=>x.sidebar)).size,screenshot_count:files.length}));
  if(issues.length)process.exitCode=3;
})().catch(e=>{console.error('R8_THEME_TEST_ERROR='+String(e.stack||e).slice(0,450));process.exitCode=1});
