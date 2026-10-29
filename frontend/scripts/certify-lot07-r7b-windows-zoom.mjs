/**
 * R7B hosted Windows real browser zoom check on the authenticated real Cabinet.
 * Browser chrome zoom != Windows OS display DPI. Never report this as native
 * Windows display scaling, NVDA, or two physical screens.
 */
import { execFileSync } from 'node:child_process';

const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
export async function certifyR7HostedWindowsBrowserZoom({page,patientId,webBase,check,capture,report}) {
  if(process.platform!=='win32'||process.env.GITHUB_ACTIONS!=='true')
    throw Error('R7B only on hosted Windows CI');
  const evidence={
    platform:process.platform,mode:'HEADed Chromium native browser accelerator',
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
  const before=await measure();
  evidence.before=before;
  await capture(page,'r7b-win-before-native-zoom-100');
  for(let i=0;i<5;i++){
    await page.keyboard.press('Control+Shift+Equal');
    await sleep(250);
  }
  let after=await measure();
  evidence.method='Playwright Chromium real key accelerator';
  if(after.dpr<before.dpr*1.95){
    // Avoid SendWait blocking the Windows desktop message loop. Send the
    // actual OS shortcut without waiting synchronously for each key, then
    // measure the live browser DPR+viewport. Never fake zoom via CSS or CDP.
    const cmd='Add-Type -AssemblyName System.Windows.Forms; '+
      '1..5 | ForEach-Object { [System.Windows.Forms.SendKeys]::Send("^{ADD}"); '+
      'Start-Sleep -Milliseconds 230 }';
    execFileSync('powershell.exe',['-NoProfile','-NonInteractive','-Command',cmd],
      {stdio:'pipe',timeout:30000});
    await sleep(950);
    after=await measure();
    evidence.method='Windows native nonblocking SendKeys Ctrl+Plus';
  }
  evidence.after=after;
  check('r7b-windows-headed-chromium-native-200-percent-zoom',
    before.dpr>0 && after.dpr/before.dpr>=1.95 &&
    after.dpr/before.dpr<=2.06 && after.innerWidth<before.innerWidth*0.61 &&
    before.cssZoom==='' && after.cssZoom==='',
    {before,after,method:evidence.method});
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
