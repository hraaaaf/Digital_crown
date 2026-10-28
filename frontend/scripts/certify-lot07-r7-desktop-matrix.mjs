/**
 * LOT07 R7 / 07.1.E + 07-E, automated portion ONLY.
 * Real browser + real authenticated FastAPI data created by R6D synthetic T2 FUE.
 * Simulated Chromium pixel density is NOT native Windows DPI / screen reader proof.
 */
import { certifyR7HostedWindowsBrowserZoom } from './certify-lot07-r7b-windows-zoom.mjs';

export async function verifyR7DesktopMatrix({
  context,webBase,patient,patientB,clinicalAssets,check,capture,report,
}) {
  const results={
    testedViewports:[1280,1440,1920,2560],
    browser:process.platform==='win32' ? 'Windows headed Chromium CI' : 'Linux headless Chromium CI',
    nativeWindows200Percent:false,
    realPhysicalSecondDisplay:false,
    nvdaScreenReader:false,
    humanVisualApproval:false,
    sessionServerRevocation:false,
    patientData:'synthetic only',
    timingsMs:[],
    heapMeasurementsBytes:[],
  };
  report.r7=results;
  const view=await context.newPage();
  const errors=[];
  view.on('pageerror',error=>errors.push(String(error).slice(0,160)));
  const sourceIds=Object.values(clinicalAssets);
  try {
    for(const width of results.testedViewports) {
      await view.setViewportSize({width,height:900});
      const started=Date.now();
      await view.goto(webBase+'/patients/'+patient.id+'?tab=tracking',{
        waitUntil:'domcontentloaded',timeout:90000,
      });
      const triptych=view.locator('[data-testid="r6-longitudinal-three-points"]');
      await triptych.waitFor({state:'visible',timeout:70000});
      await triptych.scrollIntoViewIfNeeded();
      const present=await triptych.evaluate(el=>{
        const box=el.getBoundingClientRect();
        return {
          x:box.left,right:box.right,width:box.width,visible:box.width>0 && box.height>0,
          viewport:document.documentElement.clientWidth,
        };
      });
      check('r7-canonical-triptych-visible-'+width,
        present.visible && present.x>=-4 && present.right<=width+4,{width,box:present});
      const shown=await triptych.innerText();
      check('r7-source-and-ordinal-parity-'+width,
        ['T0','T1','T2'].every(t=>shown.includes(t)) &&
        sourceIds.every(id=>shown.includes('#'+id)) &&
        !shown.includes('R6_PRIVATE_SYNTHETIC_NOTE_DO_NOT_RENDER'));
      const button=view.getByRole('button',{name:'Ouvrir sur un autre écran'});
      check('r7-presenter-available-to-authenticated-owner-'+width,
        await button.isEnabled());
      results.timingsMs.push({width,render:Date.now()-started});
      await capture(view,'r7-'+width+'-canonical-BEFORE');
    }

    await view.setViewportSize({width:1440,height:900});
    await view.goto(webBase+'/patients/'+patient.id+'?tab=tracking',{
      waitUntil:'domcontentloaded',timeout:90000,
    });
    await view.locator('[data-testid="r6-longitudinal-three-points"]')
      .waitFor({state:'visible',timeout:70000});
    const button=view.getByRole('button',{name:'Ouvrir sur un autre écran'});
    await button.focus();
    check('r7-keyboard-button-focus',await button.evaluate(el=>document.activeElement===el));
    const [popup]=await Promise.all([
      view.waitForEvent('popup',{timeout:20000}),
      view.keyboard.press('Enter'),
    ]);
    await popup.locator('[data-testid="r6d-readonly-presenter"]')
      .waitFor({state:'visible',timeout:20000});
    check('r7-keyboard-opens-real-detached-window',
      popup.url()==='about:blank' &&
      await popup.locator('[data-r6d-ordinal]').count()===3);
    const popupSafe=await popup.evaluate(()=>{
      const body=document.body.textContent||'';
      return {
        openerNull:window.opener===null,
        scriptCount:document.scripts.length,
        controls:document.querySelectorAll('form,input,button,select,textarea,a').length,
        hasPatientRoute:location.href.includes('/patients/'),
        text:body,
      };
    });
    check('r7-presenter-inert-no-edit-controls',
      popupSafe.openerNull && popupSafe.scriptCount===0 &&
      popupSafe.controls===0 && !popupSafe.hasPatientRoute);
    check('r7-presenter-no-private-clinical-notes',
      !popupSafe.text.includes('R6_PRIVATE_SYNTHETIC_NOTE_DO_NOT_RENDER') &&
      sourceIds.every(id=>popupSafe.text.includes('source #'+id)));
    // SECURITY REVIEW: about:blank inherits the app's origin. Even if the
    // document contains no script, this is NOT origin-isolated. Never export
    // credential values; report only whether the synthetic token is readable.
    const credentialSurfaceReadable=await popup.evaluate(()=>{
      try { return Boolean(localStorage.getItem('token')); }
      catch { return false; }
    });
    results.presenterOriginSecurity={
      inheritedCredentialSurfaceReadable:credentialSurfaceReadable,
      detachedOriginIsolationCertified:false,
      clinicalActivationApproved:false,
      review:'BLOCKED_PENDING_ISOLATED_ORIGIN',
    };
    check('r7-records-popout-origin-security-gate-without-token',
      typeof credentialSurfaceReadable==='boolean' &&
      results.presenterOriginSecurity.detachedOriginIsolationCertified===false &&
      results.presenterOriginSecurity.review==='BLOCKED_PENDING_ISOLATED_ORIGIN');
    await capture(popup,'r7-1440-detached-TARGET');

    // Stress stale patient identity through actual React Router, not mocked API.
    const closed=popup.waitForEvent('close',{timeout:20000});
    await view.evaluate(url=>{
      history.pushState({},'',url);
      dispatchEvent(new PopStateEvent('popstate'));
    },'/patients/'+patientB.id+'?tab=tracking');
    await view.getByText(patientB.numero_dossier,{exact:true}).first()
      .waitFor({state:'visible',timeout:30000});
    await closed;
    check('r7-change-patient-closes-detached-screen',popup.isClosed());
    check('r7-patient-B-never-shows-A-three-sources',
      await view.locator('[data-testid="r6-longitudinal-three-points"]').count()===0 &&
      !(await view.locator('body').innerText()).includes('Céphalo #'+sourceIds[0]));
    await capture(view,'r7-1440-patient-B-AFTER');

    // Capture a browser memory metric as an observation, not as a clinical PASS.
    const session=await context.newCDPSession(view);
    try {
      await session.send('Performance.enable');
      const metrics=await session.send('Performance.getMetrics');
      results.heapMeasurementsBytes=metrics.metrics
        .filter(m=>['JSHeapUsedSize','JSHeapTotalSize'].includes(m.name))
        .map(m=>({name:m.name,value:m.value}));
    } finally {await session.detach();}
    check('r7-no-unhandled-browser-errors',errors.length===0,
      {errors:errors.slice(0,2)});
    // Denials were performed through actual backend in the R6D FUE; re-check
    // their stored status so a successful browser matrix cannot hide a red gate.
    check('r7-rbac-and-foreign-tenant-refusals-observed',
      report.denials.some(x=>x.reason==='STAFF_RBAC' && x.status===403) &&
      report.denials.some(x=>x.reason==='CROSS_TENANT' && [403,404].includes(x.status)));
    if(process.platform==='win32' && process.env.LOT07_R7_WINDOWS_NATIVE==='1'){
      await certifyR7HostedWindowsBrowserZoom({
        page:view,patientId:patient.id,webBase,check,capture,report,
      });
      if(process.env.LOT07_R7_NVDA_CERT==='1'){
        const {certifyR7RealWindowsNvda}=await import('./certify-lot07-r7b-windows-nvda.mjs');
        await certifyR7RealWindowsNvda({page:view,check,capture,report});
      }
    }
    check('r7-no-physical-or-nvda-certification-inferred',
      !results.nativeWindows200Percent && !results.realPhysicalSecondDisplay &&
      !results.nvdaScreenReader && !results.humanVisualApproval &&
      !results.sessionServerRevocation);
    return results;
  } finally {
    await view.close();
  }
}
