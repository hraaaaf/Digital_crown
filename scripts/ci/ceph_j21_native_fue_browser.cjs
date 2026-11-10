/* Genuine Chromium against the Windows native nonclinical FUE executable.
   Uses synthetic JWT, synthetic PNG and a disposable SQLAlchemy test DB only. */
const { chromium } = require('playwright-core');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const root = process.env.CEPH_J21_EVIDENCE_DIR;
const profile = process.env.CEPH_J21_FUE_PROFILE;
const phase = process.argv[2];
const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');

if (!root || !profile || !['edit', 'reopen'].includes(phase)
    || process.env.GITHUB_ACTIONS !== 'true'
    || process.env.CEPH_J21_NATIVE_FUE_ONLY !== 'GITHUB_WINDOWS_J21_SYNTHETIC_FUE_ONLY') {
  throw Error('Refusing browser FUE without explicit GitHub Windows synthetic gates');
}
fs.mkdirSync(root, {recursive:true});
const fixture = JSON.parse(fs.readFileSync(path.join(profile, 'fixture-id.json'), 'utf8'));
const previous = path.join(root, 'phase-edit.json');
const report = {
  phase, case_id:'CEPH-J21-NATIVE-PACKAGE-FUE', clinical_release:false,
  native_signed_installable_certified:false, synthetic_only:true,
  viewport_proofs:[], api:[], console_errors:[], rejected_origins:[], network_failures:[],
  original_sha256:fixture.original_sha256,
};

async function main() {
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1280,height:850},locale:'fr-FR'});
    page.on('pageerror',e=>report.console_errors.push(String(e.message).slice(0,180)));
    // Deny every outgoing resource except the exact lab HTTP loopback origin.
    // Never silently contact the default clinical port 8005 or any remote host.
    await page.route('**/*',async route=>{
      const target=new URL(route.request().url());
      if(target.origin !== 'http://127.0.0.1:8879'){
        report.rejected_origins.push(target.origin.slice(0,128));
        await route.abort('blockedbyclient');
        return;
      }
      await route.continue();
    });
    page.on('requestfailed',r=>{
      const endpoint=new URL(r.url());
      report.network_failures.push({origin:endpoint.origin,reason:String(r.failure()?.errorText||'network failed').slice(0,100)});
    });
    page.on('response',r=>{
      if(r.url().includes('/api/'))report.api.push({
        method:r.request().method(), status:r.status(), pathname:new URL(r.url()).pathname
      });
    });
    const url=`http://127.0.0.1:8879/__ceph_fue/?patient=${fixture.patient_id}&study=${fixture.study_id}`;
    const first=await page.goto(url,{waitUntil:'networkidle',timeout:45000});
    if(first.status()!==200)throw Error('Native bundled FUE route returned '+first.status());
    await page.getByLabel('Mot de passe fictif').fill('TestPass123!');
    await page.getByRole('button',{name:/Connexion JWT réelle/}).click();
    const realShell=page.locator('[data-ceph-j21-real-shell="true"]');
    await realShell.waitFor({state:'visible',timeout:20000});
    // This is the genuine, source-imported clinic shell: Sidebar + Header +
    // protected content workspace, not a screenshot approximation or fake DOM.
    const liveShell=page.locator('[data-cb01-workspace-shell]');
    await liveShell.waitFor({state:'visible',timeout:20000});
    const clinicLayout=await page.evaluate(()=>{
      const root=document.querySelector('[data-ceph-j21-real-shell="true"]');
      const workspace=root?.querySelector('[data-cb01-workspace-shell]');
      return {
        real_shell:!!root,
        real_workspace:!!workspace,
        main_count:root?.querySelectorAll('main').length||0,
        navigation_count:root?.querySelectorAll('nav').length||0,
        menu_buttons:root?.querySelectorAll('button[aria-label="Menu"]').length||0,
      };
    });
    if(!clinicLayout.real_shell||!clinicLayout.real_workspace
       ||clinicLayout.main_count<1||clinicLayout.menu_buttons<1) {
      throw Error('GENUINE_DIGITAL_CROWN_MAINLAYOUT_MISSING:'+JSON.stringify(clinicLayout));
    }
    report.actual_digital_crown_shell=clinicLayout;
    const svg=page.locator('[data-ceph-j21-svg]');
    await svg.waitFor({state:'visible',timeout:18000}).catch(()=>{
      const apiFailures=report.api.filter(r=>r.status>=400).map(r=>({status:r.status,pathname:r.pathname}));
      throw Error('NATIVE_SVG_NOT_READY:'+JSON.stringify({
        rejected_origins:report.rejected_origins,
        network_failures:report.network_failures,
        api_failures:apiFailures,
        page_errors:report.console_errors,
      }).slice(0,850));
    });
    if(report.rejected_origins.length)throw Error('NATIVE_FUE_UNEXPECTED_NETWORK_ORIGIN');
    const point=svg.locator('circle[data-ceph-point="A"]');
    const x=Number(await point.getAttribute('cx'));
    const expected=phase==='edit'?1:2;
    await page.getByText(new RegExp('Révision '+expected)).waitFor({timeout:15000});
    if(await svg.getAttribute('viewBox')!=='0 0 800 600')throw Error('Wrong source-pixel viewport');
    if(phase==='edit'&&x!==45)throw Error('Synthetic before geometry not 45');
    if(phase==='reopen'&&x!==46)throw Error('Native process restart did not restore saved x=46');
    async function shot(name,width) {
      await page.setViewportSize({width,height:850});
      await page.waitForTimeout(150);
      const file=name+'.png';
      const abs=path.join(root,file);
      await page.screenshot({path:abs,fullPage:true});
      const scroll=await page.evaluate(()=>document.documentElement.scrollWidth);
      if(scroll>width+3)throw Error('Horizontal overflow '+name+' '+scroll+'/'+width);
      report.viewport_proofs.push({name,width,sha256:sha256(fs.readFileSync(abs)),file});
    }
    if(phase==='edit'){
      for(const width of [390,430,768,1280])await shot('BEFORE-'+width,width);
      await page.setViewportSize({width:1280,height:850});
      await point.click({force:true});
      await svg.focus();
      await svg.press('ArrowRight');
      if(Number(await point.getAttribute('cx'))!==46)throw Error('Real SVG edit failed');
      await page.getByRole('button',{name:/Sauvegarder puis relire/}).click();
      await page.getByText(/Révision 2/).waitFor({timeout:30000});
      if(Number(await point.getAttribute('cx'))!==46)throw Error('CAS readback changed edit');
      for(const width of [390,430,768,1280])await shot('AFTER-'+width,width);
    } else {
      const old=JSON.parse(fs.readFileSync(previous,'utf8'));
      if(old.status!=='PASS'||old.scene_sha256.length!==64)throw Error('Missing previous successful edit');
      if(x!==46)throw Error('Scene not persisted through native executable restart');
      await shot('REOPENED-1280',1280);
    }
    const audit=await page.evaluate(async ({patientId,studyId,assetId,patientB,patientX})=>{
      const token=localStorage.getItem('token');
      if(!token)throw Error('No JWT stored in isolated browser');
      const auth={Authorization:'Bearer '+token};
      const sceneResp=await fetch(`/api/ia/analyses/${studyId}/premium-scene-fue?patient_id=${patientId}`,{headers:auth});
      const scene=await sceneResp.json();
      const fileResp=await fetch(`/api/patients/${patientId}/assets/${assetId}/content`,{headers:auth});
      const bytes=await fileResp.arrayBuffer();
      const hash=await crypto.subtle.digest('SHA-256',bytes);
      const digest=Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');
      const anon=await fetch(`/api/ia/analyses/${studyId}/premium-scene-fue?patient_id=${patientId}`,{credentials:'omit'});
      const wrong=await fetch(`/api/ia/analyses/${studyId}/premium-scene-fue?patient_id=999999`,{headers:auth});
      // FUE A/B/X: authenticated owner A must not be able to bind study A to
      // another patient B, while independent dentist X must be rejected.
      const patientBReply=await fetch(
        `/api/ia/analyses/${studyId}/premium-scene-fue?patient_id=${patientB}`,
        {headers:auth,credentials:'omit'}
      );
      const outsiderForm=new URLSearchParams({
        username:'j21-native-fue-outsider@example.com',
        password:'TestPass123!',
      });
      const outsiderLogin=await fetch('/api/auth/login',{
        method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body:outsiderForm,credentials:'omit'
      });
      const outsiderData=await outsiderLogin.json();
      if(outsiderLogin.status!==200||!outsiderData.access_token)
        throw Error('Synthetic outsider JWT login failed in A/B/X FUE');
      const outsiderAuth={Authorization:'Bearer '+outsiderData.access_token};
      const outsiderRead=await fetch(
        `/api/ia/analyses/${studyId}/premium-scene-fue?patient_id=${patientId}`,
        {headers:outsiderAuth,credentials:'omit'}
      );
      const forgedXPatient=await fetch(
        `/api/ia/analyses/${studyId}/premium-scene-fue?patient_id=${patientX}`,
        {headers:outsiderAuth,credentials:'omit'}
      );
      // The exact already-committed revision 2 must never be accepted twice.
      const staleReplay=await fetch(
        `/api/ia/analyses/${studyId}/premium-scene-fue`,{
          method:'POST',
          headers:{...auth,'Content-Type':'application/json'},
          credentials:'omit',
          body:JSON.stringify({scene:scene.scene,expected_parent_sha256:scene.scene.identity.parent_scene_sha256})
        }
      );
      return {
        scene_http:sceneResp.status,media_http:fileResp.status,
        anon_http:anon.status,wrong_patient_http:wrong.status,
        same_cabinet_other_patient_http:patientBReply.status,
        outsider_read_http:outsiderRead.status,
        outsider_wrong_study_http:forgedXPatient.status,
        stale_cas_replay_http:staleReplay.status,
        scene_sha256:scene.scene_sha256,revision:scene.scene_revision,
        edited_point:scene.scene.landmarks.find(p=>p.id==='A'),point_count:scene.scene.landmarks.length,
        original_sha256:scene.scene.identity.original_sha256,
        actual_original_sha256:digest,
        parent_scene_sha256:scene.scene.identity.parent_scene_sha256,
        clinical_release:scene.clinical_release,
        desktop_fue_verified:scene.desktop_fue_verified,
        measurements:scene.scene.measurements.map(m=>({id:m.id,status:m.status,value:m.value}))
      };
    },{
      patientId:fixture.patient_id,studyId:fixture.study_id,assetId:fixture.asset_id,
      patientB:fixture.patient_b_id,patientX:fixture.patient_x_id,
    });
    Object.assign(report,{audit,scene_sha256:audit.scene_sha256,status:'PASS'});
    if(!report.actual_digital_crown_shell?.real_workspace)
      throw Error('FUE_REPORT_MISSING_GENUINE_SHELL_PROOF');
    if(audit.scene_http!==200||audit.media_http!==200||audit.anon_http!==401
       ||![403,404].includes(audit.wrong_patient_http)
       ||audit.same_cabinet_other_patient_http!==404
       ||audit.outsider_read_http!==403
       ||![403,404].includes(audit.outsider_wrong_study_http)
       ||audit.stale_cas_replay_http!==409
       ||audit.point_count!==38||audit.revision!==2||audit.edited_point?.x!==46
       ||audit.edited_point?.origin!=='PRACTITIONER_EDIT'
       ||audit.actual_original_sha256!==fixture.original_sha256
       ||audit.original_sha256!==fixture.original_sha256
       ||audit.clinical_release!==false||audit.desktop_fue_verified!==false
       ||audit.measurements.some(m=>m.status!=='UNAVAILABLE'||m.value!==null)){
      throw Error('Native browser API integrity gate failed: '+JSON.stringify(audit));
    }
    if(phase==='edit'&&audit.parent_scene_sha256!==fixture.first_scene_sha256)throw Error('CAS parent digest mismatch');
    if(phase==='reopen'){
      const old=JSON.parse(fs.readFileSync(previous,'utf8'));
      if(audit.scene_sha256!==old.scene_sha256)throw Error('Native restart changed canonical SHA');
    }
    fs.writeFileSync(path.join(root,'phase-'+phase+'.json'),JSON.stringify(report,null,2));
    console.log('CEPH_NATIVE_FUE_'+phase.toUpperCase()+'_PASS '+JSON.stringify({
      revision:audit.revision,source_sha:audit.actual_original_sha256,
      scene_sha:audit.scene_sha256,viewports:report.viewport_proofs.length,
      anonymous_http:audit.anon_http,wrong_patient_http:audit.wrong_patient_http
    }));
    await page.close();
  }finally{await browser.close();}
}
main().catch(e=>{report.status='FAIL';report.error=String(e.stack||e).slice(0,2000);
  fs.writeFileSync(path.join(root,'phase-'+phase+'.json'),JSON.stringify(report,null,2));
  console.error('CEPH_NATIVE_FUE_'+phase.toUpperCase()+'_FAIL '+String(e.message||e));process.exitCode=1;
});
