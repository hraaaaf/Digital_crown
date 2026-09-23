import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G5 login failed');
const tokens=await login.json();
const headers={Authorization:'Bearer '+tokens.access_token};
const patientsResp=await api.get('/api/patients',{headers});
if(!patientsResp.ok()) throw new Error('G5 patients fixture read failed');
const patient=(await patientsResp.json()).find(x=>x.numero_dossier==='T2-0001');
if(!patient) throw new Error('G5 T2 patient missing');

const browser=await chromium.launch({headless:true});
const viewports=[{width:390,height:844},{width:1280,height:900}];
const proofs=[];

async function seed(page){
  await page.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:tokens.access_token,refresh:tokens.refresh_token});
}
function prove(viewport,action,detail={}){proofs.push({viewport:viewport.width+'x'+viewport.height,action,status:'PASS',...detail});}

for(const viewport of viewports){
  const ctx=await browser.newContext({viewport,colorScheme:'light'});
  const page=await ctx.newPage();
  await seed(page);
  await page.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});

  for(const label of ['Profil Cabinet','Design & Ambiance','Catalogue Actes','Horaires & Agenda','Performance & Assistance','Sécurité & Backup','Mon Équipe']){
    const tab=page.getByRole('button',{name:label,exact:true});
    if(await tab.count()){
      await tab.click();
      await page.waitForTimeout(180);
      prove(viewport,'settings-tab-'+label);
    }
  }

  // Profile — deep contract: identity, specialty, contacts, save refusal, logo upload/delete, fixture restore.
  const originalProfileResp=await api.get('/api/clinics/me',{headers});
  if(!originalProfileResp.ok()) throw new Error('profile original read failed');
  const originalProfile=await originalProfileResp.json();
  const originalProfileRestore={
    nom_cabinet:originalProfile.nom_cabinet,
    specialty_ids:originalProfile.specialty_ids||[],
    custom_specialty_fr:originalProfile.custom_specialty_fr||'',
    custom_specialty_ar:originalProfile.custom_specialty_ar||'',
    header_lines_fr:originalProfile.header_lines_fr||[],
    header_lines_ar:originalProfile.header_lines_ar||[],
    header_customized:Boolean(originalProfile.header_customized),
    contacts_json:originalProfile.contacts_json||{},
    footer_phones:originalProfile.footer_phones||''
  };

  const profileTab=page.getByRole('button',{name:'Profil Cabinet',exact:true});
  if(await profileTab.count()){
    await profileTab.click();
    const cabinet=page.getByPlaceholder('Ex: Cabinet Dentaire Benmoussa');
    await cabinet.waitFor({state:'visible',timeout:10000});
    await cabinet.fill('Cabinet T2 Certification Browser');
    await cabinet.blur();

    // Toggle Orthodontie relative to original state.
    const ortho=page.getByRole('button',{name:/Orthodontie/i}).first();
    const originalOrtho=(originalProfile.specialty_ids||[]).includes('ortho');
    const orthoClass=await ortho.getAttribute('class');
    const currentOrtho=(orthoClass||'').includes('border-primary');
    if(currentOrtho===originalOrtho) await ortho.click();

    // Enable WhatsApp and set a deterministic value.
    let whatsappToggle=page.getByRole('button',{name:/^(Activer|Désactiver) WhatsApp$/});
    const whatsappWasEnabled=(originalProfile.contacts_json?.whatsapp?.enabled)===true;
    const whatsappEnabledNow=(await whatsappToggle.getAttribute('aria-label'))?.startsWith('Désactiver')===true;
    if(!whatsappEnabledNow) await whatsappToggle.click();
    whatsappToggle=page.getByRole('button',{name:/^Désactiver WhatsApp$/});
    const whatsappCard=whatsappToggle.locator('xpath=ancestor::div[contains(@class,"bg-white")][1]');
    const whatsappInput=whatsappCard.locator('input[type="text"]');
    await whatsappInput.fill('0612345678');

    let profileSave=page.getByRole('button',{name:/Mettre à jour le profil|✓ Enregistré !/}).first();
    await profileSave.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
    let profileCheck=await api.get('/api/clinics/me',{headers});
    let profileBody=await profileCheck.json();
    if(profileBody.nom_cabinet!=='Cabinet T2 Certification Browser') throw new Error('profile cabinet name did not persist');
    const savedOrtho=(profileBody.specialty_ids||[]).includes('ortho');
    if(savedOrtho===originalOrtho) throw new Error('profile specialty toggle did not persist');
    if(profileBody.contacts_json?.whatsapp?.enabled!==true || profileBody.contacts_json?.whatsapp?.value!=='0612345678'){
      throw new Error('profile WhatsApp contact did not persist');
    }
    prove(viewport,'settings-profile-identity-specialty-contact-save');

    // Refused save must not mutate persisted backend state.
    await cabinet.fill('Cabinet G5 Refused Value');
    await cabinet.blur();
    let refusedProfilePut=0;
    await page.route('**/api/clinics/me',async route=>{
      if(route.request().method()==='PUT'){
        refusedProfilePut+=1;
        return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced profile refusal"}'});
      }
      return route.continue();
    });
    profileSave=page.getByRole('button',{name:/Mettre à jour le profil|✓ Enregistré !/}).first();
    await profileSave.click();
    await page.getByText('Erreur lors de la sauvegarde',{exact:true}).waitFor({state:'visible',timeout:10000});
    await page.unroute('**/api/clinics/me');
    profileCheck=await api.get('/api/clinics/me',{headers});
    profileBody=await profileCheck.json();
    if(refusedProfilePut!==1 || profileBody.nom_cabinet!=='Cabinet T2 Certification Browser'){
      throw new Error('profile refused save mutated backend');
    }
    prove(viewport,'settings-profile-save-refusal-non-mutation',{refusedProfilePut});

    // Logo upload/delete are isolated from the filesystem but exercise the real UI/store ACK path.
    let logoUploadCalls=0,logoDeleteCalls=0;
    await page.route('**/api/clinics/me/logo',async route=>{
      if(route.request().method()==='POST'){
        logoUploadCalls+=1;
        return route.fulfill({status:200,contentType:'application/json',body:'{"logo_url":"/uploads/g5-browser-logo.png"}'});
      }
      return route.continue();
    });
    const logoInput=page.locator('#logo-input');
    await logoInput.setInputFiles({name:'g5-logo.png',mimeType:'image/png',buffer:Buffer.from('g5-logo')});
    await page.getByAltText('Logo').waitFor({state:'visible',timeout:10000});
    if(logoUploadCalls!==1) throw new Error('profile logo upload ACK mismatch');
    prove(viewport,'settings-profile-logo-upload',{logoUploadCalls});
    await page.unroute('**/api/clinics/me/logo');

    await page.route('**/api/clinics/me',async route=>{
      if(route.request().method()==='PUT'){
        const body=route.request().postDataJSON();
        if(Object.keys(body).length===1 && body.logo_path===null){
          logoDeleteCalls+=1;
          return route.fulfill({status:200,contentType:'application/json',body:'{}'});
        }
      }
      return route.continue();
    });
    await page.getByRole('button',{name:/Supprimer le logo/i}).click();
    await page.getByAltText('Logo').waitFor({state:'detached',timeout:10000});
    if(logoDeleteCalls!==1) throw new Error('profile logo delete ACK mismatch');
    prove(viewport,'settings-profile-logo-delete',{logoDeleteCalls});
    await page.unroute('**/api/clinics/me');

    // Restore the real isolated profile fields changed by this scenario.
    const restoreProfile=await api.put('/api/clinics/me',{headers,data:originalProfileRestore});
    if(!restoreProfile.ok()) throw new Error('profile fixture restore failed');
    profileCheck=await api.get('/api/clinics/me',{headers});
    profileBody=await profileCheck.json();
    if(profileBody.nom_cabinet!==originalProfileRestore.nom_cabinet) throw new Error('profile fixture name restore mismatch');
    if(JSON.stringify(profileBody.specialty_ids||[])!==JSON.stringify(originalProfileRestore.specialty_ids||[])) throw new Error('profile fixture specialties restore mismatch');
    const restoredWhatsapp=profileBody.contacts_json?.whatsapp||{enabled:false,value:''};
    const originalWhatsapp=originalProfileRestore.contacts_json?.whatsapp||{enabled:false,value:''};
    if(Boolean(restoredWhatsapp.enabled)!==Boolean(originalWhatsapp.enabled) || (restoredWhatsapp.value||'')!==(originalWhatsapp.value||'')){
      throw new Error('profile fixture contacts restore mismatch');
    }
    prove(viewport,'settings-profile-fixture-restored',{whatsappWasEnabled});
    await page.reload({waitUntil:'networkidle',timeout:90000});
  }

  // Branding — deep contract: preview consumer, preset persistence/reset, animated background real consumer + reload.
  const brandingOriginalResp=await api.get('/api/clinics/me',{headers});
  if(!brandingOriginalResp.ok()) throw new Error('branding original profile read failed');
  const brandingOriginal=await brandingOriginalResp.json();
  const originalBrandingPatch={
    primary_color:brandingOriginal.primary_color,
    secondary_color:brandingOriginal.secondary_color,
    accent_color:brandingOriginal.accent_color,
    font_fr:brandingOriginal.font_fr,
    selected_template:brandingOriginal.selected_template,
    selected_theme:brandingOriginal.selected_theme,
    margin_top:brandingOriginal.margin_top,
    margin_bottom:brandingOriginal.margin_bottom,
    header_logo_scale:brandingOriginal.header_logo_scale,
    header_font_scale:brandingOriginal.header_font_scale,
    footer_font_scale:brandingOriginal.footer_font_scale,
    header_line_height:brandingOriginal.header_line_height,
    footer_line_height:brandingOriginal.footer_line_height,
    qr_code_enabled:Boolean(brandingOriginal.qr_code_enabled),
    qr_code_type:brandingOriginal.qr_code_type||'VCARD',
    qr_code_value:brandingOriginal.qr_code_value||'',
    qr_code_label:brandingOriginal.qr_code_label||'',
    content_offset_y:Number(brandingOriginal.content_offset_y||0)
  };
  const originalAnimatedBg=await page.evaluate(()=>localStorage.getItem('app_background_animated')==='true');

  const openBranding=async()=>{
    await page.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
    const tab=page.getByRole('button',{name:'Design & Ambiance',exact:true});
    await tab.waitFor({state:'visible',timeout:10000});
    await tab.click();
    await page.getByRole('button',{name:'Arrière-plan animé',exact:true}).waitFor({state:'visible',timeout:10000});
  };

  await openBranding();

  // Preview selector must alter the actual preview surface without backend mutation.
  const profileBeforePreview=await api.get('/api/clinics/me',{headers});
  const profileBeforePreviewBody=await profileBeforePreview.json();
  await page.getByRole('button',{name:'Document',exact:true}).click();
  await page.getByText('PDF réel',{exact:true}).first().waitFor({state:'visible',timeout:10000});
  const scopeDoc=await page.evaluate(()=>localStorage.getItem('branding_preview_scope'));
  if(scopeDoc!=='doc') throw new Error('branding document preview scope not persisted');
  const profileAfterPreview=await api.get('/api/clinics/me',{headers});
  const profileAfterPreviewBody=await profileAfterPreview.json();
  if(JSON.stringify(profileAfterPreviewBody)!==JSON.stringify(profileBeforePreviewBody)) throw new Error('branding preview mutated backend profile');
  await page.getByRole('button',{name:'Application',exact:true}).click();
  await page.getByText('Tableau de bord',{exact:true}).first().waitFor({state:'visible',timeout:10000});
  prove(viewport,'settings-branding-preview-consumer');

  // Apply Swiss preset -> shared save -> backend truth.
  await page.getByRole('button',{name:/Ambiance active/i}).click();
  await page.getByRole('button',{name:/Swiss Clinic \(Ligne Claire\)/i}).click();
  await page.getByRole('button',{name:/Appliquer l'ambiance/i}).click();
  let sharedBrandingSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
  await sharedBrandingSave.waitFor({state:'visible',timeout:5000});
  await sharedBrandingSave.click();
  await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
  let brandingCheck=await api.get('/api/clinics/me',{headers});
  let brandingBody=await brandingCheck.json();
  if(brandingBody.selected_theme!=='graphite' || brandingBody.selected_template!=='swiss' || brandingBody.font_fr!=='inter'){
    throw new Error('branding Swiss preset did not persist');
  }
  prove(viewport,'settings-branding-preset-save');

  // Reset requires explicit confirmation and persists Royal preset.
  page.once('dialog',dialog=>dialog.accept());
  await page.getByRole('button',{name:/Réinitialiser/i}).click();
  sharedBrandingSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
  await sharedBrandingSave.waitFor({state:'visible',timeout:5000});
  await sharedBrandingSave.click();
  await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
  brandingCheck=await api.get('/api/clinics/me',{headers});
  brandingBody=await brandingCheck.json();
  if(brandingBody.selected_theme!=='elite' || brandingBody.selected_template!=='royal' || brandingBody.font_fr!=='playfair'){
    throw new Error('branding reset did not persist Royal preset');
  }
  prove(viewport,'settings-branding-reset-save');

  // StudioControls — exercise every QR type + persisted value/label + content position + reset.
  await openBranding();
  let qrToggle=page.getByRole('button',{name:/^(Activer|Désactiver) le code QR$/});
  let qrEnabled=(await qrToggle.getAttribute('aria-label'))?.startsWith('Désactiver')===true;
  if(!qrEnabled) await qrToggle.click();

  const qrTypes=['Contact','Site Web','Instagram','WhatsApp','Maps','Vérification du document','Suivi du paiement'];
  for(const qrType of qrTypes){
    const typeButton=page.getByRole('button',{name:qrType,exact:true});
    await typeButton.click();
    const typeClass=await typeButton.getAttribute('class');
    if(!(typeClass||'').includes('border-[var(--text-main)]')) throw new Error('QR type did not become selected: '+qrType);
    prove(viewport,'settings-branding-qr-type-'+qrType);
  }

  await page.getByRole('button',{name:'Site Web',exact:true}).click();
  await page.getByPlaceholder('https://cabinet.ma').fill('https://g5-browser.example');
  await page.getByPlaceholder('Ex: Prenez RDV').fill('G5 Browser');
  const positionSlider=page.getByRole('slider',{name:'Position verticale du contenu'});
  await positionSlider.evaluate(el=>{
    const input=el;
    input.value='0.6';
    input.dispatchEvent(new Event('input',{bubbles:true}));
    input.dispatchEvent(new Event('change',{bubbles:true}));
  });
  await page.getByText('6 mm plus bas',{exact:true}).waitFor({state:'visible',timeout:5000});

  let studioSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
  await studioSave.waitFor({state:'visible',timeout:5000});
  await studioSave.click();
  await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
  let studioCheck=await api.get('/api/clinics/me',{headers});
  let studioBody=await studioCheck.json();
  if(studioBody.qr_code_enabled!==true || studioBody.qr_code_type!=='WEBSITE' || studioBody.qr_code_value!=='https://g5-browser.example' || studioBody.qr_code_label!=='G5 Browser'){
    throw new Error('branding QR StudioControls did not persist');
  }
  if(Math.abs(Number(studioBody.content_offset_y)-0.6)>0.001) throw new Error('branding content offset did not persist');
  prove(viewport,'settings-branding-studio-controls-save');

  await page.getByRole('button',{name:'Réinitialiser la position verticale du contenu',exact:true}).click();
  studioSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
  await studioSave.click();
  await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
  studioCheck=await api.get('/api/clinics/me',{headers});
  studioBody=await studioCheck.json();
  if(Math.abs(Number(studioBody.content_offset_y))>0.001) throw new Error('branding content offset reset did not persist');
  prove(viewport,'settings-branding-content-position-reset');

  qrToggle=page.getByRole('button',{name:'Désactiver le code QR',exact:true});
  await qrToggle.click();
  studioSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
  await studioSave.click();
  await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
  studioCheck=await api.get('/api/clinics/me',{headers});
  studioBody=await studioCheck.json();
  if(studioBody.qr_code_enabled!==false) throw new Error('branding QR disable did not persist');
  prove(viewport,'settings-branding-qr-disable');

  // Restore original backend branding fixture.
  const restoreBranding=await api.put('/api/clinics/me',{headers,data:originalBrandingPatch});
  if(!restoreBranding.ok()) throw new Error('branding original profile restore failed');

  // Animated background ON/OFF must mount/unmount the real MainLayout consumer and survive reload.
  await openBranding();
  let animated=page.getByRole('button',{name:'Arrière-plan animé',exact:true});
  let animatedState=(await animated.getAttribute('aria-pressed'))==='true';
  if(!animatedState) await animated.click();
  await page.getByTestId('animated-background').waitFor({state:'visible',timeout:10000});
  await page.reload({waitUntil:'networkidle',timeout:90000});
  await page.getByTestId('animated-background').waitFor({state:'visible',timeout:10000});
  prove(viewport,'settings-branding-background-enabled');

  await openBranding();
  animated=page.getByRole('button',{name:'Arrière-plan animé',exact:true});
  animatedState=(await animated.getAttribute('aria-pressed'))==='true';
  if(animatedState) await animated.click();
  await page.getByTestId('animated-background').waitFor({state:'detached',timeout:10000});
  await page.reload({waitUntil:'networkidle',timeout:90000});
  if(await page.getByTestId('animated-background').count()) throw new Error('animated background persisted while disabled');
  prove(viewport,'settings-branding-background-disabled');

  // Restore original local background preference.
  await openBranding();
  animated=page.getByRole('button',{name:'Arrière-plan animé',exact:true});
  animatedState=(await animated.getAttribute('aria-pressed'))==='true';
  if(animatedState!==originalAnimatedBg) await animated.click();
  await page.reload({waitUntil:'networkidle',timeout:90000});
  const restoredBgCount=await page.getByTestId('animated-background').count();
  if((restoredBgCount>0)!==originalAnimatedBg) throw new Error('animated background original state not restored');
  prove(viewport,'settings-branding-fixture-restored',{originalAnimatedBg});

  // Performance/assistance — deep contract: stage -> save -> backend -> consumer effect -> inverse -> restore.
  const openRuntimeSettings=async()=>{
    await page.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
    const iaTab=page.getByRole('button',{name:'Performance & Assistance',exact:true});
    await iaTab.waitFor({state:'visible',timeout:10000});
    await iaTab.click();
    return {
      perf: page.getByRole('button',{name:'Mode Performance',exact:true}),
      aiAnimation: page.getByRole('button',{name:'Animation d’activité IA',exact:true}),
      badges: page.getByRole('button',{name:'Indicateurs de suivi patient',exact:true}),
    };
  };
  const setToggle=async(toggle,target)=>{
    await toggle.waitFor({state:'visible',timeout:5000});
    const current=(await toggle.getAttribute('aria-pressed'))==='true';
    if(current!==target) await toggle.click();
    const after=(await toggle.getAttribute('aria-pressed'))==='true';
    if(after!==target) throw new Error('runtime toggle did not reach target state');
  };
  const saveRuntime=async(expected)=>{
    const save=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
    await save.waitFor({state:'visible',timeout:5000});
    await save.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
    const check=await api.get('/api/clinics/me',{headers});
    if(!check.ok()) throw new Error('runtime profile persistence verification failed');
    const body=await check.json();
    for(const [key,value] of Object.entries(expected)){
      if(body[key]!==value) throw new Error('runtime ACK mismatch '+key+': '+body[key]+' !== '+value);
    }
  };

  let controls=await openRuntimeSettings();
  const original={
    performance_mode:(await controls.perf.getAttribute('aria-pressed'))==='true',
    clinical_tips_enabled:(await controls.aiAnimation.getAttribute('aria-pressed'))==='true',
    show_patient_badges:(await controls.badges.getAttribute('aria-pressed'))==='true',
  };

  // Enable all three, then prove the actual consumer behavior.
  await setToggle(controls.perf,true);
  await setToggle(controls.aiAnimation,true);
  await setToggle(controls.badges,true);
  await saveRuntime({performance_mode:true,clinical_tips_enabled:true,show_patient_badges:true});
  await page.reload({waitUntil:'networkidle',timeout:90000});

  await page.waitForFunction(()=>document.body.classList.contains('performance-mode'));
  const perfComputed=await page.evaluate(()=>{
    const probe=document.createElement('div');
    probe.style.transition='opacity 2s';
    probe.style.animation='pulse 2s infinite';
    document.body.appendChild(probe);
    const style=getComputedStyle(probe);
    const result={transitionDuration:style.transitionDuration,animationName:style.animationName};
    probe.remove();
    return result;
  });
  if(perfComputed.transitionDuration!=='0s' || perfComputed.animationName!=='none') {
    throw new Error('performance mode CSS consumer not applied');
  }
  prove(viewport,'settings-performance-consumer-enabled',perfComputed);

  const logo=page.getByAltText('Digital Crown').first();
  await page.evaluate(()=>window.dispatchEvent(new Event('ai-generation-start')));
  await page.waitForFunction(()=>document.querySelector('img[alt="Digital Crown"]')?.classList.contains('animate-logo-pulse-light'));
  prove(viewport,'settings-ai-activity-animation-enabled');
  await page.evaluate(()=>window.dispatchEvent(new Event('ai-generation-end')));

  await page.route('**/api/patients/scores',route=>route.fulfill({
    status:200,
    contentType:'application/json',
    body:JSON.stringify({
      [patient.id]:{
        score:null,grade:null,is_manual:false,comment:null,
        details:{rdv_honores:1,rdv_annules:0,rdv_total_observe:1,total_facture:1000,total_encaisse:800,remaining_due:200,has_billing_data:true}
      }
    })
  }));
  await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
  const listSearchEnabled=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
  await listSearchEnabled.fill('T2-0001');
  await page.getByText(/CERTIFICATION\s+T2/i).first().waitFor({state:'visible',timeout:10000});
  await page.getByRole('button',{name:'Tag cabinet manuel',exact:true}).first().waitFor({state:'visible',timeout:10000});
  prove(viewport,'settings-patient-indicators-consumer-enabled',{patientId:patient.id});

  // Disable all three, then prove their consumer effects disappear.
  controls=await openRuntimeSettings();
  await setToggle(controls.perf,false);
  await setToggle(controls.aiAnimation,false);
  await setToggle(controls.badges,false);
  await saveRuntime({performance_mode:false,clinical_tips_enabled:false,show_patient_badges:false});
  await page.reload({waitUntil:'networkidle',timeout:90000});

  await page.waitForFunction(()=>!document.body.classList.contains('performance-mode'));
  prove(viewport,'settings-performance-consumer-disabled');

  await page.evaluate(()=>window.dispatchEvent(new Event('ai-generation-start')));
  await page.waitForTimeout(100);
  const logoClass=await logo.getAttribute('class');
  if((logoClass||'').includes('animate-logo-pulse-light')) throw new Error('AI activity animation still active while disabled');
  prove(viewport,'settings-ai-activity-animation-disabled');
  await page.evaluate(()=>window.dispatchEvent(new Event('ai-generation-end')));

  await page.goto('http://127.0.0.1:5173/patients',{waitUntil:'networkidle',timeout:90000});
  const listSearchDisabled=page.getByPlaceholder('Rechercher par nom, prénom ou dossier...');
  await listSearchDisabled.fill('T2-0001');
  await page.getByText(/CERTIFICATION\s+T2/i).first().waitFor({state:'visible',timeout:10000});
  if(await page.getByRole('button',{name:'Tag cabinet manuel',exact:true}).count()) {
    throw new Error('patient indicators still rendered while disabled');
  }
  prove(viewport,'settings-patient-indicators-consumer-disabled',{patientId:patient.id});
  await page.unroute('**/api/patients/scores');

  // Restore the isolated fixture to its original state and verify backend truth.
  controls=await openRuntimeSettings();
  await setToggle(controls.perf,original.performance_mode);
  await setToggle(controls.aiAnimation,original.clinical_tips_enabled);
  await setToggle(controls.badges,original.show_patient_badges);
  await saveRuntime(original);
  prove(viewport,'settings-runtime-preferences-restored',original);

  // Agenda — deep contract: success, local overlap refusal, backend refusal/non-mutation, closure add/delete, fixture restore.
  const weekly=Object.fromEntries(
    ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'].map(day=>[day,{
      is_open:true,is_continuous:false,morning_start:'09:00',morning_end:'13:00',afternoon_start:'14:00',afternoon_end:'18:00'
    }])
  );
  let agendaSettings={
    opening_time_morning:'09:00',
    closing_time_morning:'13:00',
    opening_time_afternoon:'14:00',
    closing_time_afternoon:'18:00',
    is_continuous:false,
    agenda_mode:'EXACT',
    use_tickets:false,
    weekly_schedule:weekly
  };
  let agendaExceptions=[{
    id:5,start_date:'2026-09-25T00:00:00',end_date:'2026-09-25T23:59:59',reason:'Congés',is_holiday:false,created_at:'2026-09-19T00:00:00'
  }];
  let agendaPutAttempts=0,agendaPutAcks=0,agendaPostCalls=0,agendaDeleteCalls=0;
  let failNextAgendaSave=false;

  await page.route('**/api/agenda/settings',async route=>{
    const method=route.request().method();
    if(method==='GET') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(agendaSettings)});
    if(method==='PUT'){
      agendaPutAttempts+=1;
      if(failNextAgendaSave){
        failNextAgendaSave=false;
        return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced schedule refusal"}'});
      }
      agendaSettings=route.request().postDataJSON();
      agendaPutAcks+=1;
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(agendaSettings)});
    }
    return route.continue();
  });
  await page.route('**/api/agenda/exceptions',async route=>{
    const method=route.request().method();
    if(method==='GET') return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(agendaExceptions)});
    if(method==='POST'){
      agendaPostCalls+=1;
      const body=route.request().postDataJSON();
      const created={id:6,start_date:body.start_date,end_date:body.end_date,reason:body.reason,is_holiday:false,created_at:'2026-09-23T00:00:00'};
      agendaExceptions=[...agendaExceptions,created];
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(created)});
    }
    return route.continue();
  });
  await page.route('**/api/agenda/exceptions/*',async route=>{
    if(route.request().method()==='DELETE'){
      agendaDeleteCalls+=1;
      const id=Number(new URL(route.request().url()).pathname.split('/').pop());
      agendaExceptions=agendaExceptions.filter(x=>x.id!==id);
      return route.fulfill({status:200,contentType:'application/json',body:'{}'});
    }
    return route.continue();
  });

  const agenda=page.getByRole('button',{name:'Horaires & Agenda',exact:true});
  if(await agenda.count()){
    await agenda.click();
    await page.getByRole('heading',{name:'Horaires & Agenda',exact:true}).waitFor({state:'visible',timeout:10000});

    // Successful persisted change.
    await page.getByLabel('Lundi ouvert').click();
    await page.getByText('Modifications non enregistrées',{exact:true}).waitFor({state:'visible',timeout:5000});
    await page.getByRole('button',{name:'Enregistrer les horaires',exact:true}).click();
    await page.getByText('Horaires sauvegardés',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(agendaPutAttempts!==1 || agendaPutAcks!==1 || agendaSettings.weekly_schedule.monday.is_open!==false){
      throw new Error('agenda success persistence mismatch');
    }
    prove(viewport,'settings-agenda-save-success',{agendaPutAttempts,agendaPutAcks});

    // Local overlap validation must block the API completely.
    await page.getByLabel('Lundi ouvert').click();
    await page.getByLabel('Lundi fermeture matin').fill('15:00');
    await page.getByLabel('Lundi ouverture après-midi').fill('14:00');
    await page.getByRole('button',{name:'Enregistrer les horaires',exact:true}).click();
    await page.getByText(/plages matin et après-midi se chevauchent/i).waitFor({state:'visible',timeout:5000});
    if(agendaPutAttempts!==1) throw new Error('agenda overlap validation leaked a backend mutation');
    prove(viewport,'settings-agenda-overlap-local-refusal');

    // Restore valid hours, then force backend refusal and prove dirty/non-mutation.
    await page.getByLabel('Lundi fermeture matin').fill('13:00');
    await page.getByLabel('Lundi ouverture après-midi').fill('14:00');
    await page.getByLabel('Mardi ouvert').click();
    failNextAgendaSave=true;
    await page.getByRole('button',{name:'Enregistrer les horaires',exact:true}).click();
    await page.getByText(/Impossible d'enregistrer ces horaires/i).waitFor({state:'visible',timeout:5000});
    await page.getByText('Modifications non enregistrées',{exact:true}).waitFor({state:'visible',timeout:5000});
    if(agendaPutAttempts!==2 || agendaPutAcks!==1 || agendaSettings.weekly_schedule.tuesday.is_open!==true){
      throw new Error('agenda backend refusal mutated persisted state');
    }
    prove(viewport,'settings-agenda-backend-refusal-non-mutation',{agendaPutAttempts,agendaPutAcks});

    // Return UI to original schedule and persist it.
    await page.getByLabel('Mardi ouvert').click();
    await page.getByRole('button',{name:'Enregistrer les horaires',exact:true}).click();
    await page.getByText('Horaires sauvegardés',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(agendaSettings.weekly_schedule.monday.is_open!==true || agendaSettings.weekly_schedule.tuesday.is_open!==true){
      throw new Error('agenda fixture was not restored');
    }
    prove(viewport,'settings-agenda-fixture-restored');

    // Closure create.
    await page.getByRole('button',{name:/Ajouter une fermeture/i}).click();
    const closureDialog=page.getByRole('dialog',{name:'Ajouter une fermeture'});
    await closureDialog.getByLabel(/Début/).fill('2026-10-01');
    await closureDialog.getByLabel(/Fin/).fill('2026-10-02');
    await closureDialog.getByPlaceholder('Ex. Congés annuels').fill('Formation');
    await closureDialog.getByRole('button',{name:'Ajouter',exact:true}).click();
    await page.getByText('Formation',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(agendaPostCalls!==1 || !agendaExceptions.some(x=>x.reason==='Formation')) throw new Error('agenda closure create ACK mismatch');
    prove(viewport,'settings-agenda-closure-create',{agendaPostCalls});

    // Explicit two-step delete.
    const formation=page.getByText('Formation',{exact:true}).locator('xpath=ancestor::article[1]');
    await formation.getByRole('button',{name:'Retirer',exact:true}).click();
    if(agendaDeleteCalls!==0) throw new Error('agenda closure deleted before confirmation');
    await formation.getByRole('button',{name:'Confirmer',exact:true}).click();
    await page.getByText('Formation',{exact:true}).waitFor({state:'detached',timeout:10000});
    if(agendaDeleteCalls!==1 || agendaExceptions.some(x=>x.reason==='Formation')) throw new Error('agenda closure delete ACK mismatch');
    prove(viewport,'settings-agenda-closure-delete',{agendaDeleteCalls});
  }
  await page.unroute('**/api/agenda/settings');
  await page.unroute('**/api/agenda/exceptions');
  await page.unroute('**/api/agenda/exceptions/*');

  // Catalog — deep contract through the real catalog store endpoints and refetch.
  let catalogSpecialties=[{
    id:1,name:'Soins',color:'#3B82F6',
    acts:[{id:10,specialty_id:1,name:'Détartrage',code:'DET',base_price:500,color:'#60A5FA',is_active:true}],
    pathologies:[{id:20,specialty_id:1,name:'Gingivite',description:'Inflammation',is_active:true}]
  }];
  let nextSpecialtyId=2,nextActId=11,nextPathologyId=21;
  let catalogCreateSpecialty=0,catalogUpdateSpecialty=0,catalogCreateAct=0,catalogUpdateAct=0,catalogCreatePathology=0,catalogUpdatePathology=0;
  let failCatalogRead=false,failNextSpecialtyCreate=false;

  await page.route('**/api/catalog/**',async route=>{
    const req=route.request();
    const method=req.method();
    const path=new URL(req.url()).pathname;
    const json=(status,body)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});

    if(method==='GET' && path==='/api/catalog/specialties'){
      if(failCatalogRead) return json(503,{detail:'catalog unavailable'});
      return json(200,catalogSpecialties);
    }
    if(method==='POST' && path==='/api/catalog/specialties'){
      if(failNextSpecialtyCreate){
        failNextSpecialtyCreate=false;
        return json(503,{detail:'forced specialty refusal'});
      }
      catalogCreateSpecialty+=1;
      const body=req.postDataJSON();
      const created={id:nextSpecialtyId++,...body,acts:[],pathologies:[]};
      catalogSpecialties=[...catalogSpecialties,created];
      return json(200,created);
    }
    let match=path.match(/^\/api\/catalog\/specialties\/(\d+)$/);
    if(method==='PUT' && match){
      catalogUpdateSpecialty+=1;
      const id=Number(match[1]);
      const body=req.postDataJSON();
      catalogSpecialties=catalogSpecialties.map(s=>s.id===id?{...s,...body}:s);
      return json(200,catalogSpecialties.find(s=>s.id===id));
    }
    match=path.match(/^\/api\/catalog\/specialties\/(\d+)\/acts$/);
    if(method==='POST' && match){
      catalogCreateAct+=1;
      const specialtyId=Number(match[1]);
      const body=req.postDataJSON();
      const created={id:nextActId++,specialty_id:specialtyId,...body};
      catalogSpecialties=catalogSpecialties.map(s=>s.id===specialtyId?{...s,acts:[...s.acts,created]}:s);
      return json(200,created);
    }
    match=path.match(/^\/api\/catalog\/acts\/(\d+)$/);
    if(method==='PUT' && match){
      catalogUpdateAct+=1;
      const id=Number(match[1]);
      const body=req.postDataJSON();
      let updated=null;
      catalogSpecialties=catalogSpecialties.map(s=>({...s,acts:s.acts.map(a=>{
        if(a.id!==id) return a;
        updated={...a,...body};
        return updated;
      })}));
      return json(200,updated||{});
    }
    match=path.match(/^\/api\/catalog\/specialties\/(\d+)\/pathologies$/);
    if(method==='POST' && match){
      catalogCreatePathology+=1;
      const specialtyId=Number(match[1]);
      const body=req.postDataJSON();
      const created={id:nextPathologyId++,specialty_id:specialtyId,...body};
      catalogSpecialties=catalogSpecialties.map(s=>s.id===specialtyId?{...s,pathologies:[...s.pathologies,created]}:s);
      return json(200,created);
    }
    match=path.match(/^\/api\/catalog\/pathologies\/(\d+)$/);
    if(method==='PUT' && match){
      catalogUpdatePathology+=1;
      const id=Number(match[1]);
      const body=req.postDataJSON();
      let updated=null;
      catalogSpecialties=catalogSpecialties.map(s=>({...s,pathologies:s.pathologies.map(p=>{
        if(p.id!==id) return p;
        updated={...p,...body};
        return updated;
      })}));
      return json(200,updated||{});
    }
    return json(500,{detail:'unexpected G5 catalog request '+method+' '+path});
  });

  const catalog=page.getByRole('button',{name:'Catalogue Actes',exact:true});
  if(await catalog.count()){
    await catalog.click();
    await page.getByText('Détartrage',{exact:true}).waitFor({state:'visible',timeout:10000});

    // Create specialty.
    await page.getByRole('button',{name:/Nouvelle spécialité/i}).click();
    let catalogDialog=page.getByRole('dialog');
    await catalogDialog.getByPlaceholder('Ex. Orthodontie').fill('  Orthodontie   Clinique ');
    await catalogDialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.getByText('Orthodontie Clinique',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(catalogCreateSpecialty!==1) throw new Error('catalog specialty create ACK mismatch');
    prove(viewport,'settings-catalog-specialty-create',{catalogCreateSpecialty});

    // Edit specialty and prove refetch result.
    await page.getByRole('button',{name:'Modifier Soins',exact:true}).click();
    catalogDialog=page.getByRole('dialog');
    const specialtyName=catalogDialog.getByPlaceholder('Ex. Orthodontie');
    await specialtyName.fill('Soins restaurateurs');
    await catalogDialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await page.getByText('Soins restaurateurs',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(catalogUpdateSpecialty!==1) throw new Error('catalog specialty update ACK mismatch');
    prove(viewport,'settings-catalog-specialty-edit',{catalogUpdateSpecialty});

    // Select the edited specialty.
    await page.getByRole('button',{name:/Soins restaurateurs/i}).first().click();
    await page.getByText('Détartrage',{exact:true}).waitFor({state:'visible',timeout:5000});

    // Invalid price must never reach store/API.
    await page.getByRole('button',{name:/Ajouter un acte/i}).click();
    catalogDialog=page.getByRole('dialog');
    await catalogDialog.getByPlaceholder('Ex. Détartrage').fill('Consultation invalide');
    await catalogDialog.getByPlaceholder('0').fill('-20');
    await catalogDialog.getByRole('button',{name:'Créer',exact:true}).click();
    await catalogDialog.getByText(/tarif doit être un nombre positif ou nul/i).waitFor({state:'visible',timeout:5000});
    if(catalogCreateAct!==0) throw new Error('catalog invalid tariff leaked an API mutation');
    prove(viewport,'settings-catalog-invalid-price-refusal');
    await catalogDialog.getByRole('button',{name:'Annuler',exact:true}).click();

    // Create act.
    await page.getByRole('button',{name:/Ajouter un acte/i}).click();
    catalogDialog=page.getByRole('dialog');
    await catalogDialog.getByPlaceholder('Ex. Détartrage').fill('Consultation');
    await catalogDialog.getByPlaceholder('Ex. DET').fill('CONS');
    await catalogDialog.getByPlaceholder('0').fill('350');
    await catalogDialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.getByText('Consultation',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(catalogCreateAct!==1 || !catalogSpecialties[0].acts.some(a=>a.code==='CONS')) throw new Error('catalog act create ACK mismatch');
    prove(viewport,'settings-catalog-act-create',{catalogCreateAct});

    // Edit/deactivate existing act.
    await page.getByRole('button',{name:"Modifier l'acte Détartrage",exact:true}).click();
    catalogDialog=page.getByRole('dialog');
    await catalogDialog.getByRole('checkbox',{name:'Actif'}).uncheck();
    await catalogDialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    const detArticle=page.getByText('Détartrage',{exact:true}).locator('xpath=ancestor::article[1]');
    await detArticle.getByText('Inactif',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(catalogUpdateAct!==1 || catalogSpecialties[0].acts.find(a=>a.id===10)?.is_active!==false) throw new Error('catalog act deactivate ACK mismatch');
    prove(viewport,'settings-catalog-act-deactivate',{catalogUpdateAct});

    // Create pathology.
    await page.getByRole('button',{name:/Ajouter une pathologie/i}).click();
    catalogDialog=page.getByRole('dialog');
    await catalogDialog.getByPlaceholder('Ex. Gingivite').fill('Parodontite');
    await catalogDialog.getByPlaceholder('Description facultative').fill('Atteinte parodontale');
    await catalogDialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.getByText('Parodontite',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(catalogCreatePathology!==1) throw new Error('catalog pathology create ACK mismatch');
    prove(viewport,'settings-catalog-pathology-create',{catalogCreatePathology});

    // Edit/deactivate pathology.
    await page.getByRole('button',{name:'Modifier la pathologie Gingivite',exact:true}).click();
    catalogDialog=page.getByRole('dialog');
    await catalogDialog.getByRole('checkbox',{name:'Actif'}).uncheck();
    await catalogDialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    const gingArticle=page.getByText('Gingivite',{exact:true}).locator('xpath=ancestor::article[1]');
    await gingArticle.getByText('Inactif',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(catalogUpdatePathology!==1 || catalogSpecialties[0].pathologies.find(p=>p.id===20)?.is_active!==false) throw new Error('catalog pathology deactivate ACK mismatch');
    prove(viewport,'settings-catalog-pathology-deactivate',{catalogUpdatePathology});

    // Mutation refusal keeps modal open and state unchanged.
    const specialtyCountBefore=catalogSpecialties.length;
    failNextSpecialtyCreate=true;
    await page.getByRole('button',{name:/Nouvelle spécialité/i}).click();
    catalogDialog=page.getByRole('dialog');
    await catalogDialog.getByPlaceholder('Ex. Orthodontie').fill('Implantologie refusée');
    await catalogDialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.waitForTimeout(200);
    if(!(await catalogDialog.isVisible())) throw new Error('catalog refusal closed modal');
    if(catalogSpecialties.length!==specialtyCountBefore) throw new Error('catalog refusal mutated specialty state');
    prove(viewport,'settings-catalog-mutation-refusal-non-mutation');
    await catalogDialog.getByRole('button',{name:'Annuler',exact:true}).click();

    // Read failure must fail closed, then retry restores truth.
    failCatalogRead=true;
    await page.getByRole('button',{name:'Profil Cabinet',exact:true}).click();
    await page.getByRole('button',{name:'Catalogue Actes',exact:true}).click();
    await page.getByText('Catalogue indisponible',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(await page.getByText('Détartrage',{exact:true}).count()) throw new Error('catalog stale contents exposed during read failure');
    failCatalogRead=false;
    await page.getByRole('button',{name:'Réessayer',exact:true}).click();
    await page.getByText('Détartrage',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-catalog-read-retry');
  }
  await page.unroute('**/api/catalog/**');

  // Security/restore — deep contract: export, compatible preflight, cancel, prepare, exact confirmation, apply/status, refusal.
  const security=page.getByRole('button',{name:'Sécurité & Backup',exact:true});
  if(await security.count()){
    await security.click();

    let exportCalls=0;
    await page.route('**/api/admin/export-db',route=>{
      exportCalls+=1;
      return route.fulfill({
        status:200,
        contentType:'application/octet-stream',
        headers:{'content-disposition':'attachment; filename="clinic.dcbackup"'},
        body:Buffer.from('backup')
      });
    });
    await page.getByRole('button',{name:/Créer et télécharger la sauvegarde/i}).click();
    await page.getByText('Sauvegarde chiffrée créée et téléchargée',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(exportCalls!==1) throw new Error('verified backup export request count mismatch');
    prove(viewport,'settings-backup-export',{exportCalls});
    await page.unroute('**/api/admin/export-db');

    const preflightReady={
      restore_id:'restore-g5',
      status:'preflight_ready',
      original_name:'backup.enc',
      size_bytes:2048,
      archive_type:'ENC',
      backup_created_at:'2026-09-19',
      compatible:true,
      restore_database:true,
      restore_media:false,
      media_file_count:0,
      preserved:['media'],
      warnings:[],
      errors:[]
    };
    const prepared={...preflightReady,status:'prepared',prepared_at:'2026-09-19T12:00:00Z'};
    const success={...prepared,status:'success',message:'Restauration terminée',smoke_check:'ok',rollback:'not_needed'};
    let preflightCalls=0,prepareCalls=0,applyCalls=0,statusCalls=0,cancelCalls=0;

    await page.route('**/api/admin/restore/preflight',route=>{
      preflightCalls+=1;
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(preflightReady)});
    });
    await page.route('**/api/admin/restore/restore-g5/prepare',route=>{
      prepareCalls+=1;
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(prepared)});
    });
    await page.route('**/api/admin/restore/restore-g5/apply',route=>{
      applyCalls+=1;
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...prepared,status:'scheduled'})});
    });
    await page.route('**/api/admin/restore/restore-g5/status',route=>{
      statusCalls+=1;
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(success)});
    });
    await page.route('**/api/admin/restore/restore-g5',route=>{
      if(route.request().method()==='DELETE'){
        cancelCalls+=1;
        return route.fulfill({status:200,contentType:'application/json',body:'{}'});
      }
      return route.continue();
    });

    const file=page.locator('input[type="file"]').first();
    await file.setInputFiles({name:'backup.enc',mimeType:'application/octet-stream',buffer:Buffer.from('backup')});
    await page.getByText('Préflight validé',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(preflightCalls!==1 || prepareCalls!==0 || applyCalls!==0) throw new Error('restore mutated before explicit prepare/apply');
    prove(viewport,'settings-restore-preflight-compatible',{preflightCalls});

    await page.getByRole('button',{name:/Fermer ce préflight/i}).click();
    await page.waitForFunction(()=>!document.body.innerText.includes('Préflight validé'));
    if(cancelCalls!==1 || applyCalls!==0) throw new Error('restore cancel contract mismatch');
    prove(viewport,'settings-restore-cancel',{cancelCalls});

    await file.setInputFiles({name:'backup.enc',mimeType:'application/octet-stream',buffer:Buffer.from('backup')});
    await page.getByText('Préflight validé',{exact:true}).waitFor({state:'visible',timeout:10000});
    await page.getByRole('button',{name:/Préparer la restauration/i}).click();
    const confirmation=page.getByPlaceholder('RESTAURER');
    await confirmation.waitFor({state:'visible',timeout:10000});
    if(prepareCalls!==1 || applyCalls!==0) throw new Error('restore prepare gate mismatch');

    await confirmation.fill('restaurer');
    const apply=page.getByRole('button',{name:/Redémarrer et restaurer/i});
    if(!(await apply.isDisabled())) throw new Error('restore apply enabled without exact confirmation');
    if(applyCalls!==0) throw new Error('restore apply called before exact confirmation');

    await confirmation.fill('RESTAURER');
    if(await apply.isDisabled()) throw new Error('restore apply remained disabled with exact confirmation');
    await apply.click();
    await page.getByText('Restauration terminée',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(applyCalls!==1 || statusCalls<1) throw new Error('restore apply/status contract mismatch');
    prove(viewport,'settings-restore-apply-terminal-success',{prepareCalls,applyCalls,statusCalls});

    await page.unroute('**/api/admin/restore/preflight');
    await page.unroute('**/api/admin/restore/restore-g5/prepare');
    await page.unroute('**/api/admin/restore/restore-g5/apply');
    await page.unroute('**/api/admin/restore/restore-g5/status');
    await page.unroute('**/api/admin/restore/restore-g5');

    await page.getByRole('button',{name:/Fermer ce préflight/i}).click().catch(()=>{});
    await page.route('**/api/admin/restore/preflight',route=>route.fulfill({status:400,contentType:'application/json',body:'{"detail":"Backup corrompu"}'}));
    await file.setInputFiles({name:'bad.enc',mimeType:'application/octet-stream',buffer:Buffer.from('bad')});
    await page.getByRole('main').getByText('Backup corrompu',{exact:true}).waitFor({state:'visible',timeout:5000});
    if(await page.getByRole('button',{name:/Préparer la restauration/i}).count()) throw new Error('prepare exposed after refused preflight');
    if(await page.getByRole('button',{name:/Redémarrer et restaurer/i}).count()) throw new Error('apply exposed after refused preflight');
    prove(viewport,'settings-restore-preflight-refusal');
    await page.unroute('**/api/admin/restore/preflight');
  }

  // Team — deep browser contract with deterministic isolated API state.
  const team=page.getByRole('button',{name:'Mon Équipe',exact:true});
  if(await team.count()){
    let teamMembers=[
      {id:11,email:'active@example.com',role:'SECRETAIRE',nom_complet:'Active User',telephone_mobile:null,is_active:true,approval_status:'approved',approval_note:null,created_at:null,permissions:{agenda:true,patients:true}},
      {id:12,email:'inactive@example.com',role:'SECRETAIRE',nom_complet:'Inactive User',telephone_mobile:null,is_active:false,approval_status:'approved',approval_note:null,created_at:null,permissions:{agenda:true,patients:true}},
      {id:10,email:'pending-approve@example.com',role:'SECRETAIRE',nom_complet:'Pending Approve',telephone_mobile:null,is_active:false,approval_status:'pending',approval_note:null,created_at:null,permissions:{agenda:true,patients:true}},
      {id:13,email:'pending-reject@example.com',role:'SECRETAIRE',nom_complet:'Pending Reject',telephone_mobile:null,is_active:false,approval_status:'pending',approval_note:null,created_at:null,permissions:{agenda:true,patients:true}}
    ];
    let nextTeamId=20;
    let teamCreateCalls=0,approveCalls=0,rejectCalls=0,permissionCalls=0,statusCalls=0,deleteCalls=0;
    let failNextStatus=false;

    await page.route('**/api/team**',async route=>{
      const req=route.request();
      const method=req.method();
      const url=new URL(req.url());
      const path=url.pathname;
      const json=(status,body)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});

      if(method==='GET' && path==='/api/team/quota'){
        const pending=teamMembers.filter(m=>m.approval_status==='pending').length;
        return json(200,{plan:'ELITE',dentistes_used:1,dentistes_max:null,secretaires_used:teamMembers.length,secretaires_max:null,pending_count:pending,can_add_dentiste:true,can_add_secretaire:true});
      }
      if(method==='GET' && path==='/api/team/') return json(200,teamMembers);

      if(method==='POST' && path==='/api/team/'){
        teamCreateCalls+=1;
        const body=req.postDataJSON();
        const member={id:nextTeamId++,...body,is_active:true,approval_status:'approved',approval_note:null,created_at:null};
        teamMembers=[...teamMembers,member];
        return json(200,member);
      }

      let match=path.match(/^\/api\/team\/(\d+)\/approve$/);
      if(method==='POST' && match){
        approveCalls+=1;
        const id=Number(match[1]);
        teamMembers=teamMembers.map(m=>m.id===id?{...m,approval_status:'approved',is_active:true}:m);
        return json(200,{});
      }
      match=path.match(/^\/api\/team\/(\d+)\/reject$/);
      if(method==='POST' && match){
        rejectCalls+=1;
        const id=Number(match[1]);
        teamMembers=teamMembers.map(m=>m.id===id?{...m,approval_status:'rejected',is_active:false}:m);
        return json(200,{});
      }
      match=path.match(/^\/api\/team\/(\d+)$/);
      if(method==='PUT' && match){
        const id=Number(match[1]);
        const body=req.postDataJSON();
        if(Object.prototype.hasOwnProperty.call(body,'permissions')){
          permissionCalls+=1;
          teamMembers=teamMembers.map(m=>m.id===id?{...m,permissions:body.permissions}:m);
          return json(200,{});
        }
        if(Object.prototype.hasOwnProperty.call(body,'is_active')){
          statusCalls+=1;
          if(failNextStatus){
            failNextStatus=false;
            return json(503,{detail:'forced team status refusal'});
          }
          teamMembers=teamMembers.map(m=>m.id===id?{...m,is_active:body.is_active}:m);
          return json(200,{});
        }
      }
      if(method==='DELETE' && match){
        deleteCalls+=1;
        const id=Number(match[1]);
        teamMembers=teamMembers.filter(m=>m.id!==id);
        return json(200,{});
      }
      return json(500,{detail:'unexpected G5 team request '+method+' '+path});
    });

    await team.click();
    await page.getByText('Active User',{exact:true}).waitFor({state:'visible',timeout:10000});

    // Create
    await page.getByRole('button',{name:/Ajouter un membre/i}).click();
    await page.getByPlaceholder('Ex: Fatima Zahra').fill('Browser New Member');
    await page.getByPlaceholder('assistante@cabinet.com').fill('browser-new@example.com');
    await page.getByPlaceholder('••••••••').fill('TestPass123!');
    await page.getByRole('button',{name:'Créer le compte',exact:true}).click();
    await page.getByText('Browser New Member',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(teamCreateCalls!==1) throw new Error('team create ACK count mismatch');
    prove(viewport,'settings-team-create',{teamCreateCalls});

    const pendingCard=name=>page.getByText(name,{exact:true}).locator('xpath=ancestor::div[.//button[normalize-space()="Valider"]][1]');
    const memberCard=name=>page.getByText(name,{exact:true}).locator('xpath=ancestor::div[.//button[@title="Gérer les permissions"]][1]');

    // Approve pending identity
    await pendingCard('Pending Approve').getByRole('button',{name:'Valider',exact:true}).click();
    const approvedCard=memberCard('Pending Approve');
    await approvedCard.getByText('Actif',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(approveCalls!==1) throw new Error('team approve ACK count mismatch');
    prove(viewport,'settings-team-approve',{approveCalls});

    // Reject another pending identity with explicit confirmation
    page.once('dialog',dialog=>dialog.accept());
    await pendingCard('Pending Reject').getByRole('button',{name:'Refuser',exact:true}).click();
    const rejectedCard=memberCard('Pending Reject');
    await rejectedCard.getByText('Refusé',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(rejectCalls!==1) throw new Error('team reject ACK count mismatch');
    if(await rejectedCard.getByTitle("Suspendre l'accès").count()) throw new Error('rejected identity exposes suspend action');
    if(await rejectedCard.getByTitle("Réactiver l'accès").count()) throw new Error('rejected identity exposes reactivate action');
    prove(viewport,'settings-team-reject',{rejectCalls});

    // Permissions
    let activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle('Gérer les permissions').click();
    const permissionsDialog=page.getByText(/Droits d'accès : Active User/).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    const patientsPermission=permissionsDialog.getByRole('checkbox',{name:/Dossiers Patients/i});
    const beforePatients=await patientsPermission.isChecked();
    await patientsPermission.setChecked(!beforePatients);
    await permissionsDialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await page.getByText(/Permissions de Active User mises à jour/i).waitFor({state:'visible',timeout:10000});
    if(permissionCalls!==1) throw new Error('team permissions ACK count mismatch');
    const storedPermissions=teamMembers.find(m=>m.id===11)?.permissions||{};
    if(storedPermissions.patients===beforePatients) throw new Error('team permissions did not persist');
    prove(viewport,'settings-team-permissions',{permissionCalls});

    // Refused status mutation must not alter UI state.
    activeCard=memberCard('Active User');
    await activeCard.hover();
    failNextStatus=true;
    await activeCard.getByTitle("Suspendre l'accès").click();
    await page.getByText('Erreur lors de la modification du statut.',{exact:true}).waitFor({state:'visible',timeout:10000});
    activeCard=memberCard('Active User');
    await activeCard.getByText('Actif',{exact:true}).waitFor({state:'visible',timeout:5000});
    if(teamMembers.find(m=>m.id===11)?.is_active!==true) throw new Error('team status changed after refused mutation');
    prove(viewport,'settings-team-status-refusal-non-mutation');

    const closeTeamError=page.getByRole('button',{name:"Fermer l'erreur"});
    if(await closeTeamError.count()) await closeTeamError.click();

    // Suspend then reactivate after ACK/refetch.
    activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle("Suspendre l'accès").click();
    activeCard=memberCard('Active User');
    await activeCard.getByText('Suspendu',{exact:true}).waitFor({state:'visible',timeout:10000});
    await activeCard.hover();
    await activeCard.getByTitle("Réactiver l'accès").click();
    activeCard=memberCard('Active User');
    await activeCard.getByText('Actif',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(statusCalls<3) throw new Error('team status mutation count incomplete');
    prove(viewport,'settings-team-suspend-reactivate',{statusCalls});

    // Delete the created member with explicit confirmation.
    const newCard=memberCard('Browser New Member');
    await newCard.hover();
    page.once('dialog',dialog=>dialog.accept());
    await newCard.getByTitle('Supprimer définitivement').click();
    await page.getByText('Browser New Member',{exact:true}).waitFor({state:'detached',timeout:10000});
    if(deleteCalls!==1) throw new Error('team delete ACK count mismatch');
    prove(viewport,'settings-team-delete',{deleteCalls});

    await page.unroute('**/api/team**');
  }

  // Settings shell — fail closed on profile read and preserve dirty state after shared-save refusal.
  const shellPage=await ctx.newPage();
  await seed(shellPage);
  let failProfileRead=true;
  await shellPage.route('**/api/clinics/me',async route=>{
    const method=route.request().method();
    if(method==='GET' && failProfileRead){
      return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced profile read failure"}'});
    }
    return route.continue();
  });
  await shellPage.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
  await shellPage.getByText('Profil indisponible',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(await shellPage.getByPlaceholder('Ex: Cabinet Dentaire Benmoussa').count()) throw new Error('settings exposed profile controls during read failure');
  failProfileRead=false;
  await shellPage.getByRole('button',{name:'Réessayer',exact:true}).click();
  await shellPage.getByPlaceholder('Ex: Cabinet Dentaire Benmoussa').waitFor({state:'visible',timeout:10000});
  prove(viewport,'settings-shell-read-failure-retry');
  await shellPage.unroute('**/api/clinics/me');

  await shellPage.getByRole('button',{name:'Performance & Assistance',exact:true}).click();
  const shellPerf=shellPage.getByRole('button',{name:'Mode Performance',exact:true});
  await shellPerf.click();
  await shellPage.getByTestId('settings-save-bar').waitFor({state:'visible',timeout:5000});
  let refusedSharedSave=0;
  await shellPage.route('**/api/clinics/me',async route=>{
    if(route.request().method()==='PUT'){
      refusedSharedSave+=1;
      return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced shared save refusal"}'});
    }
    return route.continue();
  });
  await shellPage.getByRole('button',{name:'Enregistrer la configuration',exact:true}).click();
  await shellPage.getByText('Erreur lors de la sauvegarde',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(refusedSharedSave!==1) throw new Error('settings shared save refusal request mismatch');
  await shellPage.getByTestId('settings-save-bar').waitFor({state:'visible',timeout:5000});
  prove(viewport,'settings-shell-shared-save-refusal-dirty',{refusedSharedSave});
  await shellPage.close();

  // Practitioner context — API truth, explicit selection continuity, owner fallback.
  const practitionerPage=await ctx.newPage();
  await seed(practitionerPage);
  await practitionerPage.route('**/api/appointments/multi-practitioner*',route=>route.fulfill({
    status:200,
    contentType:'application/json',
    body:JSON.stringify({dentists:[
      {dentist_id:7,dentist_name:'Dr Owner',appointments:[{},{}]},
      {dentist_id:8,dentist_name:'Dr Associate',appointments:[{}]}
    ]})
  }));
  await practitionerPage.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
  const practitionerRegion=practitionerPage.getByRole('region',{name:'Contexte praticien'});
  await practitionerRegion.waitFor({state:'visible',timeout:10000});
  const associate=practitionerRegion.getByRole('button',{name:/Dr Associate/i});
  await associate.click();
  if((await associate.getAttribute('aria-pressed'))!=='true') throw new Error('practitioner explicit selection did not activate');
  await practitionerPage.getByRole('link',{name:'Agenda',exact:true}).click();
  await practitionerPage.waitForURL('**/agenda');
  const agendaPractitioner=practitionerPage.getByRole('region',{name:'Contexte praticien'}).getByRole('button',{name:/Dr Associate/i});
  await agendaPractitioner.waitFor({state:'visible',timeout:10000});
  if((await agendaPractitioner.getAttribute('aria-pressed'))!=='true') throw new Error('practitioner selection did not survive SPA navigation');
  prove(viewport,'settings-practitioner-selection-continuity');
  await practitionerPage.close();

  const fallbackPage=await ctx.newPage();
  await seed(fallbackPage);
  await fallbackPage.route('**/api/appointments/multi-practitioner*',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced practitioner read failure"}'}));
  await fallbackPage.goto('http://127.0.0.1:5173/settings',{waitUntil:'networkidle',timeout:90000});
  const fallbackRegion=fallbackPage.getByRole('region',{name:'Contexte praticien'});
  await fallbackRegion.waitFor({state:'visible',timeout:10000});
  const fallbackButtons=fallbackRegion.getByRole('button');
  if(await fallbackButtons.count()!==1) throw new Error('practitioner owner fallback did not produce exactly one selectable practitioner');
  if((await fallbackButtons.first().getAttribute('aria-pressed'))!=='true') throw new Error('practitioner fallback is not selected');
  prove(viewport,'settings-practitioner-owner-fallback');
  await fallbackPage.close();

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G5_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
