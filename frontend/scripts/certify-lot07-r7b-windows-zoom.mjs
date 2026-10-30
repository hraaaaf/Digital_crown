/**
 * R7B hosted Windows real browser zoom check on the authenticated real Cabinet.
 * Browser chrome zoom != Windows OS display DPI. Never report this as native
 * Windows display scaling, NVDA, or two physical screens.
 */
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
export async function certifyR7HostedWindowsBrowserZoom({page,patientId,webBase,check,capture,report,zoomWorker}) {
  if(process.platform!=='win32'||process.env.GITHUB_ACTIONS!=='true')
    throw Error('R7B only on hosted Windows CI');
  const evidence={
    platform:process.platform,mode:'Chromium extension chrome.tabs.setZoom/getZoom (real native browser)',
    nativeBrowserZoom200:false,nativeWindowsDisplayDpi200:false,
    nvdaSpeechCertified:false,physicalSecondDisplay:false,
    method:null,before:null,after:null,
  };
  report.r7Windows=evidence;
  await page.setViewportSize({width:1440,height:900});
  await page.goto(webBase+'/patients/'+patientId+'?tab=tracking',{
    waitUntil:'domcontentloaded',timeout:90000,
  });
  await page.locator('[data-testid="r6-longitudinal-three-points"]')
    .waitFor({state:'visible',timeout:70000});
  await page.bringToFront();
  const measure=async()=>{
    let error=null;
    for(let n=0;n<16;n++){
      try{
        return await page.evaluate(()=>({
          dpr:window.devicePixelRatio,
          innerWidth:window.innerWidth,
          clientWidth:document.documentElement.clientWidth,
          cssZoom:document.body.style.zoom,
        }));
      }catch(e){error=e;await sleep(200);}
    }
    throw Error('Windows native browser measurement failed: '+String(error));
  };
  if(!zoomWorker || !zoomWorker.url().startsWith('chrome-extension://'))
    throw Error('NOT_CERTIFIED: real Chromium extension service worker missing');
  const tabUrl=page.url();
  if(!tabUrl.startsWith(webBase+'/patients/'+patientId+'?tab=tracking'))
    throw Error('REFUSED: non-canonical T2 patient zoom target');
  // Chrome's real tabs API, NOT Playwright deviceScaleFactor, CSS zoom,
  // OS SendKeys, or an emulated CDP metric. Only local synthetic patient tab.
  const nativeZoom=async(target)=>{
    const result=await zoomWorker.evaluate(async({url,target})=>{
      const tabs=(await chrome.tabs.query({})).filter(tab=>
        typeof tab.id==='number' && tab.url===url);
      if(tabs.length!==1)throw Error('NOT_CERTIFIED: expected one real synthetic Chromium tab');
      const id=tabs[0].id;
      if(target!==null)await chrome.tabs.setZoom(id,target);
      return {id,value:await chrome.tabs.getZoom(id)};
    },{url:tabUrl,target});
    if(target!==null && Math.abs(result.value-target)>0.01)
      throw Error('NOT_CERTIFIED: Chrome native zoom API disagrees with requested zoom');
    return result;
  };
  const zoom100=await nativeZoom(1);
  await page.waitForFunction(()=>Math.abs(window.devicePixelRatio-1)<0.05,
    null,{timeout:10000});
  const before=await measure();
  evidence.before=before;
  await capture(page,'r7b-win-before-native-zoom-100');
  const zoom200=await nativeZoom(2);
  if(zoom200.id!==zoom100.id)throw Error('NOT_CERTIFIED: Chrome tab identity changed at zoom');
  await page.waitForFunction(()=>window.devicePixelRatio>=1.95,
    null,{timeout:10000});
  const after=await measure();
  evidence.after=after;
  evidence.method='native Chromium chrome.tabs.setZoom/getZoom';
  evidence.nativeZoomAt100=zoom100.value;
  evidence.nativeZoomAt200=zoom200.value;
  check('r7b-windows-headed-chromium-native-200-percent-zoom',
    Math.abs(zoom100.value-1)<0.01 && Math.abs(zoom200.value-2)<0.01 &&
    before.dpr>0 && after.dpr/before.dpr>=1.95 &&
    after.dpr/before.dpr<=2.06 && after.innerWidth<before.innerWidth*0.61 &&
    before.cssZoom==='' && after.cssZoom==='',
    {before,after,nativeApi:{at100:zoom100.value,at200:zoom200.value},method:evidence.method});
  const triple=page.locator('[data-testid="r6-longitudinal-three-points"]');
  await triple.scrollIntoViewIfNeeded();
  check('r7b-windows-zoom200-real-react-triptych-still-visible',
    await triple.isVisible());
  await capture(page,'r7b-win-after-native-browser-zoom-200');
  evidence.nativeBrowserZoom200=true;
  // Verify native zoom while Chromium still owns Windows focus. Starting NVDA
  // before browser zoom steals accelerator focus on the hosted desktop.
  // NVDA then speaks against the already zoomed REAL authenticated browser.
  if(process.env.LOT07_R7_NVDA_CERT==='1'){
    const {certifyR7RealWindowsNvda}=await import('./certify-lot07-r7b-windows-nvda.mjs');
    await certifyR7RealWindowsNvda({page,check,capture,report});
    await page.bringToFront();
  }
  // These gates are *not* inferred from browser zoom or hosted CI.
  check('r7b-windows-no-fake-physical-display-or-dpi-claim',
    !evidence.nativeWindowsDisplayDpi200 &&
    !evidence.nvdaSpeechCertified && !evidence.physicalSecondDisplay);
  return evidence;
}
