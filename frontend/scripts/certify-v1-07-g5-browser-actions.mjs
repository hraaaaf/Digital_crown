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

    // Every visible specialty button must toggle its actual selected state, then restore it.
    const specialtySection=page.getByText('Expertises & Spécialités Cliniques',{exact:true}).locator('xpath=..');
    const specialtyButtons=specialtySection.locator('button');
    const specialtyCount=await specialtyButtons.count();
    if(specialtyCount===0) throw new Error('profile exposes zero specialty controls');
    for(let i=0;i<specialtyCount;i++){
      const specialty=specialtyButtons.nth(i);
      const before=(await specialty.getAttribute('aria-pressed'))==='true';
      await specialty.click();
      const after=(await specialty.getAttribute('aria-pressed'))==='true';
      if(after===before) throw new Error('profile specialty control did not toggle at index '+i);
      await specialty.click();
      const restored=(await specialty.getAttribute('aria-pressed'))==='true';
      if(restored!==before) throw new Error('profile specialty control did not restore at index '+i);
    }
    prove(viewport,'settings-profile-all-specialty-controls',{specialtyCount});

    // Every contact toggle must change enabled/disabled input truth, then restore it.
    for(const contactLabel of ['Tél. Fixe','Tél. Mobile','WhatsApp','Instagram']){
      const contactToggle=page.getByRole('button',{name:new RegExp('^(Activer|Désactiver) '+contactLabel.replace('.','\\.')+'
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

    let profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
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
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
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
    const [logoChooser]=await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button',{name:'Choisir le logo du cabinet',exact:true}).click()
    ]);
    await logoChooser.setFiles({name:'g5-logo.png',mimeType:'image/png',buffer:Buffer.from('g5-logo')});
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

    // Return the staged cabinet name to the last persisted truth before testing advanced header controls.
    await cabinet.fill('Cabinet T2 Certification Browser');
    await cabinet.blur();
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
    await profileSave.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});

    // Advanced bilingual header: open, add/delete FR+AR rows, persist a manual line, then reset from canonical cabinet data.
    const headerToggle=page.getByRole('button',{name:/En-tête bilingue/i});
    await headerToggle.click();
    if((await headerToggle.getAttribute('aria-expanded'))!=='true') throw new Error('profile advanced header did not open');

    let frDeletes=page.getByRole('button',{name:/Supprimer la ligne française/});
    let arDeletes=page.getByRole('button',{name:/Supprimer la ligne arabe/});
    const frBefore=await frDeletes.count();
    const arBefore=await arDeletes.count();

    await page.getByRole('button',{name:'+ Ligne FR',exact:true}).click();
    frDeletes=page.getByRole('button',{name:/Supprimer la ligne française/});
    if(await frDeletes.count()!==frBefore+1) throw new Error('profile + Ligne FR did not add a row');
    await page.getByRole('button',{name:'Supprimer la ligne française '+(frBefore+1),exact:true}).click();
    if(await page.getByRole('button',{name:/Supprimer la ligne française/}).count()!==frBefore) throw new Error('profile FR delete did not remove the added row');
    prove(viewport,'settings-profile-header-fr-add-delete');

    await page.getByRole('button',{name:'+ Ligne AR',exact:true}).click();
    arDeletes=page.getByRole('button',{name:/Supprimer la ligne arabe/});
    if(await arDeletes.count()!==arBefore+1) throw new Error('profile + Ligne AR did not add a row');
    await page.getByRole('button',{name:'Supprimer la ligne arabe '+(arBefore+1),exact:true}).click();
    if(await page.getByRole('button',{name:/Supprimer la ligne arabe/}).count()!==arBefore) throw new Error('profile AR delete did not remove the added row');
    prove(viewport,'settings-profile-header-ar-add-delete');

    const firstFrDelete=page.getByRole('button',{name:'Supprimer la ligne française 1',exact:true});
    const firstFrInput=firstFrDelete.locator('xpath=..').locator('input');
    await firstFrInput.fill('G5 Header Custom');
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
    await profileSave.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
    profileCheck=await api.get('/api/clinics/me',{headers});
    profileBody=await profileCheck.json();
    if(profileBody.header_customized!==true || profileBody.header_lines_fr?.[0]!=='G5 Header Custom'){
      throw new Error('profile manual header did not persist');
    }
    prove(viewport,'settings-profile-header-custom-save');

    const resetHeader=page.getByRole('button',{name:/Réinitialiser depuis le cabinet|Modèle Benmoussa/});
    const resetHeaderLabel=(await resetHeader.innerText()).trim();
    await resetHeader.click();
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
    await profileSave.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
    profileCheck=await api.get('/api/clinics/me',{headers});
    profileBody=await profileCheck.json();
    if(profileBody.header_lines_fr?.[0]==='G5 Header Custom') throw new Error('profile header reset left manual content active');
    if(resetHeaderLabel.includes('Réinitialiser') && profileBody.header_customized!==false){
      throw new Error('profile owner header reset did not restore automatic mode');
    }
    prove(viewport,'settings-profile-header-reset',{resetHeaderLabel});

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

  // Real document preview controls: generate -> stale -> refresh -> open.
  await page.getByRole('button',{name:'Document',exact:true}).click();
  let previewPostCalls=0,previewPdfCalls=0;
  await page.route('**/api/documents/sample-preview',route=>{
    previewPostCalls+=1;
    return route.fulfill({status:200,contentType:'application/json',body:'{"pdf_url":"/g5-preview.pdf"}'});
  });
  await page.route('**/g5-preview.pdf',route=>{
    previewPdfCalls+=1;
    return route.fulfill({status:200,contentType:'application/pdf',body:Buffer.from('%PDF-1.4\n%%EOF')});
  });
  await page.getByRole('button',{name:'Générer le rendu PDF réel',exact:true}).click();
  await page.getByText('Rendu à jour',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(previewPostCalls!==1 || previewPdfCalls!==1) throw new Error('branding real PDF preview generation mismatch');
  prove(viewport,'settings-branding-pdf-preview-generate',{previewPostCalls,previewPdfCalls});

  const previewPosition=page.getByRole('slider',{name:'Position verticale du contenu'});
  const previewOriginalPosition=await previewPosition.inputValue();
  const previewChanged=previewOriginalPosition==='0.1'?'0.2':'0.1';
  await previewPosition.evaluate((el,value)=>{
    const input=el;
    input.value=value;
    input.dispatchEvent(new Event('input',{bubbles:true}));
    input.dispatchEvent(new Event('change',{bubbles:true}));
  },previewChanged);
  await page.getByText('À actualiser',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:'Actualiser le rendu',exact:true}).click();
  await page.getByText('Rendu à jour',{exact:true}).waitFor({state:'visible',timeout:10000});
  if(previewPostCalls!==2 || previewPdfCalls!==2) throw new Error('branding real PDF preview refresh mismatch');
  prove(viewport,'settings-branding-pdf-preview-refresh',{previewPostCalls,previewPdfCalls});

  const popupPromise=page.waitForEvent('popup',{timeout:5000}).catch(()=>null);
  await page.getByRole('button',{name:'Ouvrir',exact:true}).click();
  const popup=await popupPromise;
  if(!popup) throw new Error('branding PDF Open did not create a browser target');
  await popup.close();
  prove(viewport,'settings-branding-pdf-preview-open');

  await previewPosition.evaluate((el,value)=>{
    const input=el;
    input.value=value;
    input.dispatchEvent(new Event('input',{bubbles:true}));
    input.dispatchEvent(new Event('change',{bubbles:true}));
  },previewOriginalPosition);
  await page.unroute('**/api/documents/sample-preview');
  await page.unroute('**/g5-preview.pdf');

  // Ambiance modal close/cancel semantics before applying a preset.
  await page.getByRole('button',{name:/Ambiance active/i}).click();
  await page.getByRole('heading',{name:/ambiances cohérentes, prêtes à l'emploi/i}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:'Fermer les ambiances',exact:true}).click();
  await page.getByRole('heading',{name:/ambiances cohérentes, prêtes à l'emploi/i}).waitFor({state:'detached',timeout:5000});
  prove(viewport,'settings-branding-ambiance-close');

  await page.getByRole('button',{name:/Ambiance active/i}).click();
  await page.getByRole('button',{name:'Annuler',exact:true}).click();
  await page.getByRole('heading',{name:/ambiances cohérentes, prêtes à l'emploi/i}).waitFor({state:'detached',timeout:5000});
  prove(viewport,'settings-branding-ambiance-cancel');

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

  // Practitioner availability sub-module fixture.
  const practitionerRows=[
    {practitioner_id:7,practitioner_name:'Dr Owner',inherits_cabinet:true},
    {practitioner_id:8,practitioner_name:'Dr Associate',inherits_cabinet:true}
  ];
  const practitionerSettings=new Map([
    [7,{practitioner_id:7,practitioner_name:'Dr Owner',inherits_cabinet:true,weekly_schedule:null}],
    [8,{practitioner_id:8,practitioner_name:'Dr Associate',inherits_cabinet:true,weekly_schedule:null}]
  ]);
  const practitionerExceptions=new Map([[7,[]],[8,[]]]);
  let practitionerPutCalls=0,practitionerResetCalls=0,practitionerAbsencePostCalls=0,practitionerAbsenceDeleteCalls=0;
  let failPractitionerSettingsId=null;
  await page.route('**/api/agenda/practitioners*',async route=>{
    const req=route.request();
    const method=req.method();
    const path=new URL(req.url()).pathname;
    const json=(status,body)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});

    if(method==='GET' && path==='/api/agenda/practitioners') return json(200,practitionerRows);
    let match=path.match(/^\/api\/agenda\/practitioners\/(\d+)\/settings$/);
    if(match){
      const id=Number(match[1]);
      if(method==='GET'){
        if(failPractitionerSettingsId===id) return json(503,{detail:'forced practitioner settings failure'});
        return json(200,practitionerSettings.get(id));
      }
      if(method==='PUT'){
        practitionerPutCalls+=1;
        const body=req.postDataJSON();
        const saved={practitioner_id:id,practitioner_name:practitionerRows.find(x=>x.practitioner_id===id)?.practitioner_name||'Praticien',inherits_cabinet:false,weekly_schedule:body.weekly_schedule,updated_at:'2026-09-23T10:00:00Z'};
        practitionerSettings.set(id,saved);
        return json(200,saved);
      }
      if(method==='DELETE'){
        practitionerResetCalls+=1;
        const reset={practitioner_id:id,practitioner_name:practitionerRows.find(x=>x.practitioner_id===id)?.practitioner_name||'Praticien',inherits_cabinet:true,weekly_schedule:null};
        practitionerSettings.set(id,reset);
        return json(200,{});
      }
    }
    match=path.match(/^\/api\/agenda\/practitioners\/(\d+)\/exceptions$/);
    if(match){
      const id=Number(match[1]);
      if(method==='GET') return json(200,practitionerExceptions.get(id)||[]);
      if(method==='POST'){
        practitionerAbsencePostCalls+=1;
        const body=req.postDataJSON();
        const rows=practitionerExceptions.get(id)||[];
        const created={id:70+practitionerAbsencePostCalls,practitioner_id:id,start_date:body.start_date,end_date:body.end_date,reason:body.reason,created_at:'2026-09-23T10:00:00Z'};
        practitionerExceptions.set(id,[...rows,created]);
        return json(200,created);
      }
    }
    match=path.match(/^\/api\/agenda\/practitioners\/(\d+)\/exceptions\/(\d+)$/);
    if(match && method==='DELETE'){
      practitionerAbsenceDeleteCalls+=1;
      const id=Number(match[1]);
      const exceptionId=Number(match[2]);
      practitionerExceptions.set(id,(practitionerExceptions.get(id)||[]).filter(x=>x.id!==exceptionId));
      return json(200,{});
    }
    return json(500,{detail:'unexpected practitioner availability request '+method+' '+path});
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

    // Practitioner availability: both practitioner selectors + every weekday Plage action.
    const availability=page.getByTestId('practitioner-availability-panel');
    await availability.getByRole('button',{name:/Dr Owner/i}).waitFor({state:'visible',timeout:10000});
    await availability.getByRole('button',{name:/Dr Associate/i}).click();
    await availability.getByText(/Dr Associate suit les horaires du cabinet/i).waitFor({state:'visible',timeout:10000});
    await availability.getByRole('button',{name:/Dr Owner/i}).click();
    await availability.getByText(/Dr Owner suit les horaires du cabinet/i).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-practitioner-availability-selection');

    await availability.getByRole('button',{name:'Personnaliser',exact:true}).click();
    const practitionerDays=['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'];
    for(const day of practitionerDays){
      const dayArticle=availability.getByText(day,{exact:true}).locator('xpath=ancestor::article[1]');
      await dayArticle.getByRole('button',{name:'Plage',exact:true}).click();
      const added=dayArticle.getByRole('button',{name:'Retirer plage '+day+' 3',exact:true});
      await added.waitFor({state:'visible',timeout:5000});
      await added.click();
      await added.waitFor({state:'detached',timeout:5000});
    }
    prove(viewport,'settings-practitioner-availability-all-add-remove-slots',{dayCount:practitionerDays.length});

    const mondayAvailability=availability.getByText('Lundi',{exact:true}).locator('xpath=ancestor::article[1]');
    await mondayAvailability.getByLabel('Lundi plage 1 début').fill('08:30');
    await availability.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await page.getByText('Disponibilités praticien enregistrées',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(practitionerPutCalls!==1 || practitionerSettings.get(7)?.weekly_schedule?.monday?.intervals?.[0]?.start!=='08:30'){
      throw new Error('practitioner availability save ACK mismatch');
    }
    prove(viewport,'settings-practitioner-availability-save',{practitionerPutCalls});

    await availability.getByRole('button',{name:'Hériter du cabinet',exact:true}).click();
    await availability.getByText(/Dr Owner suit les horaires du cabinet/i).waitFor({state:'visible',timeout:10000});
    if(practitionerResetCalls!==1 || practitionerSettings.get(7)?.inherits_cabinet!==true) throw new Error('practitioner inheritance reset mismatch');
    prove(viewport,'settings-practitioner-availability-inherit',{practitionerResetCalls});

    // Invalid absence range must be blocked before API mutation.
    const absenceStart=availability.getByLabel('Début');
    const absenceEnd=availability.getByLabel('Fin');
    const absenceReason=availability.getByLabel('Motif');
    await absenceStart.fill('2026-10-03T12:00');
    await absenceEnd.fill('2026-10-03T11:00');
    await absenceReason.fill('Formation G5');
    await availability.getByRole('button',{name:'Ajouter',exact:true}).click();
    await availability.getByText(/La fin de l’indisponibilité doit être après son début/i).waitFor({state:'visible',timeout:5000});
    if(practitionerAbsencePostCalls!==0) throw new Error('invalid practitioner absence reached API');
    prove(viewport,'settings-practitioner-absence-local-refusal');

    await absenceEnd.fill('2026-10-03T15:00');
    await availability.getByRole('button',{name:'Ajouter',exact:true}).click();
    const absenceRow=availability.getByText('Formation G5',{exact:true}).locator('xpath=ancestor::div[contains(@class,"rounded-xl")][1]');
    await absenceRow.waitFor({state:'visible',timeout:10000});
    if(practitionerAbsencePostCalls!==1) throw new Error('practitioner absence create ACK mismatch');
    await absenceRow.getByRole('button',{name:'Retirer',exact:true}).click();
    await availability.getByText('Formation G5',{exact:true}).waitFor({state:'detached',timeout:10000});
    if(practitionerAbsenceDeleteCalls!==1) throw new Error('practitioner absence delete ACK mismatch');
    prove(viewport,'settings-practitioner-absence-create-delete',{practitionerAbsencePostCalls,practitionerAbsenceDeleteCalls});

    // Selected practitioner read failure must surface truth; selecting another practitioner recovers.
    failPractitionerSettingsId=8;
    await availability.getByRole('button',{name:/Dr Associate/i}).click();
    await availability.getByText('Impossible de charger les disponibilités de ce praticien.',{exact:true}).waitFor({state:'visible',timeout:10000});
    failPractitionerSettingsId=null;
    await availability.getByRole('button',{name:/Dr Owner/i}).click();
    await availability.getByText(/Dr Owner suit les horaires du cabinet/i).waitFor({state:'visible',timeout:10000});
    await availability.getByRole('button',{name:/Dr Associate/i}).click();
    await availability.getByText(/Dr Associate suit les horaires du cabinet/i).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-practitioner-availability-read-recovery');
  }
  await page.unroute('**/api/agenda/settings');
  await page.unroute('**/api/agenda/exceptions');
  await page.unroute('**/api/agenda/exceptions/*');
  await page.unroute('**/api/agenda/practitioners*');

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
    // Install deterministic Mobile Security + Audit fixtures before mounting the Security tab.
    let bridgeOptionsCalls=0,bridgePairingCalls=0,revokeMobileCalls=0;
    let failBridgeOptions=false,failNextBridgePairing=false;
    const bridgeTargets=[
      {id:1,name:'Dr T2 Browser',email:'t2-browser@cabinet.ma',role:'DENTISTE',is_current_user:true,destinations:[
        {id:'dashboard',label:'Tableau de bord mobile'},
        {id:'agenda',label:'Agenda mobile'}
      ]},
      {id:2,name:'Assistante G5',email:'assistante-g5@cabinet.ma',role:'SECRETAIRE',is_current_user:false,destinations:[
        {id:'agenda',label:'Agenda mobile'},
        {id:'frontdesk',label:'Accueil mobile'}
      ]}
    ];
    await page.route('**/api/mobile/bridge-options',route=>{
      bridgeOptionsCalls+=1;
      if(failBridgeOptions) return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Options mobiles indisponibles"}'});
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({targets:bridgeTargets,expires_in:300})});
    });
    await page.route('**/api/mobile/bridge-pairing',route=>{
      bridgePairingCalls+=1;
      if(failNextBridgePairing){
        failNextBridgePairing=false;
        return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Pairing refusé"}'});
      }
      const body=route.request().postDataJSON();
      const target=bridgeTargets.find(x=>x.id===body.target_user_id);
      const destination=target?.destinations.find(x=>x.id===body.destination);
      const qrSvg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" fill="black"/></svg>').toString('base64');
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
        qr_code:'data:image/svg+xml;base64,'+qrSvg,
        token_code:'G5MOBILE',
        expires_in:300,
        target_user_id:body.target_user_id,
        target_user_name:target?.name||'Utilisateur',
        target_role:target?.role||'',
        destination:body.destination,
        destination_label:destination?.label||body.destination,
        contains_patient_data:false
      })});
    });
    await page.route('**/api/admin/revoke-mobile',route=>{
      revokeMobileCalls+=1;
      return route.fulfill({status:200,contentType:'application/json',body:'{}'});
    });

    let auditCalls=[];
    let failAuditRead=false;
    const makeAuditLog=(id,action='LOGIN_SUCCESS',severity='INFO')=>({
      id,
      timestamp:'2026-09-23T10:00:00Z',
      user_id:1,
      employer_id:1,
      action,
      resource_type:'Patient',
      resource_id:String(id),
      severity,
      ip_address:'127.0.0.1',
      details:'G5 audit detail '+id
    });
    await page.route('**/api/admin/audit-logs*',route=>{
      const url=new URL(route.request().url());
      const action=url.searchParams.get('action')||'';
      const severity=url.searchParams.get('severity')||'';
      const offset=Number(url.searchParams.get('offset')||'0');
      auditCalls.push({action,severity,offset});
      if(failAuditRead) return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"audit unavailable"}'});
      if(action || severity){
        const log=makeAuditLog(100,action||'DELETE',severity||'WARNING');
        return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({logs:[log],total:1})});
      }
      const logs=offset>=20
        ? [21,22,23,24,25].map(id=>makeAuditLog(id,id===21?'DELETE':'LOGIN_SUCCESS',id===21?'WARNING':'INFO'))
        : Array.from({length:20},(_,i)=>makeAuditLog(i+1,i===0?'DELETE':'LOGIN_SUCCESS',i===0?'WARNING':'INFO'));
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({logs,total:25})});
    });

    await security.click();

    // Mobile Security — options, target/destination, pairing success/refusal, revoke cancel/ACK, options retry.
    await page.getByRole('heading',{name:'Compagnon Mobile',exact:true}).waitFor({state:'visible',timeout:10000});
    const targetSelect=page.getByRole('combobox',{name:'Utilisateur mobile cible'});
    const destinationSelect=page.getByRole('combobox',{name:'Destination mobile'});
    await targetSelect.waitFor({state:'visible',timeout:10000});
    if(bridgeOptionsCalls<1) throw new Error('mobile bridge options were not loaded');

    await targetSelect.selectOption('2');
    await destinationSelect.selectOption('frontdesk');
    await page.getByRole('button',{name:'Générer le QR de connexion',exact:true}).click();
    await page.getByText('G5MOBILE',{exact:true}).waitFor({state:'visible',timeout:10000});
    await page.getByAltText('QR de connexion Digital Crown Mobile').waitFor({state:'visible',timeout:5000});
    if(bridgePairingCalls!==1) throw new Error('mobile pairing success call mismatch');
    prove(viewport,'settings-mobile-pairing-success',{bridgePairingCalls});

    await targetSelect.selectOption('1');
    await page.getByText('G5MOBILE',{exact:true}).waitFor({state:'detached',timeout:5000});
    failNextBridgePairing=true;
    await page.getByRole('button',{name:'Générer le QR de connexion',exact:true}).click();
    await page.getByText('Pairing refusé',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(await page.getByText('G5MOBILE',{exact:true}).count()) throw new Error('mobile pairing refusal left stale pairing visible');
    prove(viewport,'settings-mobile-pairing-refusal-non-mutation');

    page.once('dialog',dialog=>dialog.dismiss());
    await page.getByRole('button',{name:/Révoquer tous les accès mobiles/i}).click();
    if(revokeMobileCalls!==0) throw new Error('mobile revoke called despite cancelled confirmation');
    prove(viewport,'settings-mobile-revoke-cancel');

    page.once('dialog',dialog=>dialog.accept());
    await page.getByRole('button',{name:/Révoquer tous les accès mobiles/i}).click();
    await page.getByText(/Tous les téléphones ont été déconnectés/i).waitFor({state:'visible',timeout:10000});
    if(revokeMobileCalls!==1) throw new Error('mobile revoke ACK count mismatch');
    prove(viewport,'settings-mobile-revoke-success',{revokeMobileCalls});

    failBridgeOptions=true;
    await page.getByRole('button',{name:'Performance & Assistance',exact:true}).click();
    await page.getByRole('button',{name:'Sécurité & Backup',exact:true}).click();
    await page.getByText('Options mobiles indisponibles',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(!(await targetSelect.isDisabled())) throw new Error('mobile target selector enabled during options read failure');
    failBridgeOptions=false;
    await page.getByText('Options mobiles indisponibles',{exact:true}).locator('xpath=ancestor::div[1]').getByRole('button',{name:'Réessayer',exact:true}).click();
    await targetSelect.waitFor({state:'visible',timeout:10000});
    await page.waitForFunction(()=>!document.body.innerText.includes('Options mobiles indisponibles'));
    prove(viewport,'settings-mobile-options-retry',{bridgeOptionsCalls});

    // Audit log — filters, refresh, details, pagination, read failure + retry.
    await page.getByRole('heading',{name:"Journal d'Audit",exact:true}).waitFor({state:'visible',timeout:10000});
    const actionFilter=page.getByRole('combobox',{name:'Filtrer le journal par action'});
    const severityFilter=page.getByRole('combobox',{name:'Filtrer le journal par sévérité'});
    await actionFilter.selectOption('DELETE');
    await page.getByText('Suppression',{exact:true}).first().waitFor({state:'visible',timeout:10000});
    if(!auditCalls.some(x=>x.action==='DELETE')) throw new Error('audit action filter did not reach backend query');
    prove(viewport,'settings-audit-action-filter');

    await severityFilter.selectOption('WARNING');
    await page.getByText('Attention',{exact:true}).first().waitFor({state:'visible',timeout:10000});
    if(!auditCalls.some(x=>x.action==='DELETE'&&x.severity==='WARNING')) throw new Error('audit severity filter did not compose with action filter');
    prove(viewport,'settings-audit-severity-filter');

    await actionFilter.selectOption('');
    await severityFilter.selectOption('');
    await page.getByText('25 entrées',{exact:true}).waitFor({state:'visible',timeout:10000});
    const refreshBefore=auditCalls.length;
    await page.getByRole('button',{name:'Rafraîchir le journal',exact:true}).click();
    await page.waitForFunction(expected=>document.body.innerText.includes('25 entrées'),refreshBefore);
    if(auditCalls.length<=refreshBefore) throw new Error('audit refresh did not refetch');

    const detailsButton=page.getByRole('button',{name:/Voir les détails/i}).first();
    await detailsButton.click();
    await page.getByText('G5 audit detail 1',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'settings-audit-details-expand');

    await page.getByRole('button',{name:/Suivant/i}).click();
    await page.getByText('Page 2 / 2',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(!auditCalls.some(x=>x.offset===20)) throw new Error('audit pagination did not request second page');
    await page.getByRole('button',{name:/Précédent/i}).click();
    await page.getByText('Page 1 / 2',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-audit-pagination');

    failAuditRead=true;
    await page.getByRole('button',{name:'Rafraîchir le journal',exact:true}).click();
    await page.getByText("Journal d'audit indisponible",{exact:true}).waitFor({state:'visible',timeout:10000});
    if(await page.getByText('Aucun log trouvé',{exact:true}).count()) throw new Error('audit read failure rendered a false empty state');
    failAuditRead=false;
    const auditError=page.getByText("Journal d'audit indisponible",{exact:true}).locator('xpath=ancestor::div[contains(@class,"rounded")][1]');
    await auditError.getByRole('button',{name:'Réessayer',exact:true}).click();
    await page.getByText('25 entrées',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-audit-read-retry');

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

    await page.unroute('**/api/mobile/bridge-options');
    await page.unroute('**/api/mobile/bridge-pairing');
    await page.unroute('**/api/admin/revoke-mobile');
    await page.unroute('**/api/admin/audit-logs*');
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
    let failNextStatus=false,failTeamRead=false;

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
      if(method==='GET' && path==='/api/team/') {
        if(failTeamRead) return json(503,{detail:'forced team read failure'});
        return json(200,teamMembers);
      }

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

    // Create form auxiliary controls + role/permission semantics.
    await page.getByRole('button',{name:/Ajouter un membre/i}).click();
    const roleSelect=page.getByRole('combobox',{name:'Rôle du collaborateur'});
    if(await roleSelect.inputValue()!=='SECRETAIRE') throw new Error('team create default role is not secretary');
    if(!(await page.getByRole('checkbox',{name:/Dossiers Patients/i}).isChecked())) throw new Error('team secretary default patients permission missing');
    if(await page.getByRole('checkbox',{name:/Prescriptions/i}).isChecked()) throw new Error('team secretary default prescriptions permission unexpectedly enabled');

    const passwordInput=page.getByPlaceholder('••••••••');
    await passwordInput.fill('TestPass123!');
    if(await passwordInput.getAttribute('type')!=='password') throw new Error('team password is not masked by default');
    await page.getByRole('button',{name:'Afficher le mot de passe',exact:true}).click();
    if(await passwordInput.getAttribute('type')!=='text') throw new Error('team password reveal did not work');
    await page.getByRole('button',{name:'Masquer le mot de passe',exact:true}).click();
    if(await passwordInput.getAttribute('type')!=='password') throw new Error('team password re-mask did not work');
    prove(viewport,'settings-team-password-reveal-hide');

    await page.getByRole('button',{name:'Annuler',exact:true}).click();
    await page.getByText('Nouveau sous-compte',{exact:true}).waitFor({state:'detached',timeout:5000});
    if(teamCreateCalls!==0) throw new Error('team create cancel triggered a mutation');
    prove(viewport,'settings-team-create-cancel');

    await page.getByRole('button',{name:/Ajouter un membre/i}).click();
    const createRole=page.getByRole('combobox',{name:'Rôle du collaborateur'});
    await createRole.selectOption('DENTISTE');
    if(!(await page.getByRole('checkbox',{name:/Prescriptions/i}).isChecked())) throw new Error('team dentist defaults did not enable prescriptions');
    const settingsPermission=page.getByRole('checkbox',{name:/Réglages Cabinet/i});
    if(await settingsPermission.isChecked()) throw new Error('team dentist settings permission should default false');
    await settingsPermission.check();

    await page.getByPlaceholder('Ex: Fatima Zahra').fill('Browser New Member');
    await page.getByPlaceholder('assistante@cabinet.com').fill('browser-new@example.com');
    await page.getByPlaceholder('••••••••').fill('TestPass123!');
    await page.getByPlaceholder('06 00 00 00 00').fill('0600000000');
    await page.getByRole('button',{name:'Créer le compte',exact:true}).click();
    await page.getByText('Browser New Member',{exact:true}).waitFor({state:'visible',timeout:10000});
    const createdMember=teamMembers.find(m=>m.nom_complet==='Browser New Member');
    if(teamCreateCalls!==1 || createdMember?.role!=='DENTISTE' || createdMember?.permissions?.settings!==true){
      throw new Error('team create role/permissions ACK mismatch');
    }
    prove(viewport,'settings-team-create',{teamCreateCalls,role:createdMember.role});

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

    // Permissions modal close/cancel semantics, then persisted update.
    let activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle('Gérer les permissions').click();
    let permissionsDialog=page.getByText(/Droits d'accès : Active User/).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    await permissionsDialog.getByRole('button',{name:'Annuler',exact:true}).click();
    await page.getByText(/Droits d'accès : Active User/).waitFor({state:'detached',timeout:5000});
    if(permissionCalls!==0) throw new Error('team permissions cancel triggered mutation');
    prove(viewport,'settings-team-permissions-cancel');

    activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle('Gérer les permissions').click();
    permissionsDialog=page.getByText(/Droits d'accès : Active User/).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    await permissionsDialog.getByRole('button',{name:'Fermer les permissions',exact:true}).click();
    await page.getByText(/Droits d'accès : Active User/).waitFor({state:'detached',timeout:5000});
    if(permissionCalls!==0) throw new Error('team permissions close triggered mutation');
    prove(viewport,'settings-team-permissions-close');

    activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle('Gérer les permissions').click();
    permissionsDialog=page.getByText(/Droits d'accès : Active User/).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
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

    // Team truth gate read failure -> no management UI -> retry restores truth.
    failTeamRead=true;
    await page.getByRole('button',{name:'Performance & Assistance',exact:true}).click();
    await page.getByRole('button',{name:'Mon Équipe',exact:true}).click();
    await page.getByText('Équipe indisponible',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(await page.getByRole('button',{name:/Ajouter un membre/i}).count()) throw new Error('team controls exposed while truth gate failed');
    failTeamRead=false;
    await page.getByRole('button',{name:'Réessayer',exact:true}).click();
    await page.getByText('Active User',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-team-read-retry');

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
)});
      const before=(await contactToggle.getAttribute('aria-pressed'))==='true';
      const card=contactToggle.locator('xpath=ancestor::div[contains(@class,"bg-white")][1]');
      const input=card.locator('input[type="text"]');
      if((await input.isDisabled())===before) throw new Error('profile contact input initial enabled truth mismatch: '+contactLabel);
      await contactToggle.click();
      const after=(await contactToggle.getAttribute('aria-pressed'))==='true';
      if(after===before || (await input.isDisabled())===after) throw new Error('profile contact toggle effect mismatch: '+contactLabel);
      await contactToggle.click();
      const restored=(await contactToggle.getAttribute('aria-pressed'))==='true';
      if(restored!==before || (await input.isDisabled())===restored) throw new Error('profile contact toggle restore mismatch: '+contactLabel);
    }
    prove(viewport,'settings-profile-all-contact-toggles');

    // Dynamic Arabic keyboard: exercise every revealed key and Space, then restore the source field.
    const customArabic=page.getByPlaceholder('مثال: زراعة الأسنان');
    const originalCustomArabic=await customArabic.inputValue();
    await customArabic.fill('');
    await customArabic.focus();
    const arabicKeys=['ض','ص','ث','ق','ف','غ','ع','ه','خ','ح','ج','د','ش','س','ي','ب','ل','ا','ت','ن','م','ك','ط','ئ','ء','ؤ','ر','لا','ى','ة','و','ز','ظ'];
    for(const key of arabicKeys){
      await page.getByRole('button',{name:key,exact:true}).click();
    }
    await page.getByRole('button',{name:'Espace',exact:true}).click();
    const arabicExpected=arabicKeys.join('')+' ';
    if(await customArabic.inputValue()!==arabicExpected) throw new Error('Arabic keyboard did not append every key in order');
    prove(viewport,'settings-profile-arabic-keyboard-all-keys',{keyCount:arabicKeys.length+1});
    await customArabic.fill(originalCustomArabic);
    await page.mouse.click(2,2);
    await page.waitForTimeout(50);

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

    let profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
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
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
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
    const [logoChooser]=await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button',{name:'Choisir le logo du cabinet',exact:true}).click()
    ]);
    await logoChooser.setFiles({name:'g5-logo.png',mimeType:'image/png',buffer:Buffer.from('g5-logo')});
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

    // Return the staged cabinet name to the last persisted truth before testing advanced header controls.
    await cabinet.fill('Cabinet T2 Certification Browser');
    await cabinet.blur();
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
    await profileSave.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});

    // Advanced bilingual header: open, add/delete FR+AR rows, persist a manual line, then reset from canonical cabinet data.
    const headerToggle=page.getByRole('button',{name:/En-tête bilingue/i});
    await headerToggle.click();
    if((await headerToggle.getAttribute('aria-expanded'))!=='true') throw new Error('profile advanced header did not open');

    let frDeletes=page.getByRole('button',{name:/Supprimer la ligne française/});
    let arDeletes=page.getByRole('button',{name:/Supprimer la ligne arabe/});
    const frBefore=await frDeletes.count();
    const arBefore=await arDeletes.count();

    await page.getByRole('button',{name:'+ Ligne FR',exact:true}).click();
    frDeletes=page.getByRole('button',{name:/Supprimer la ligne française/});
    if(await frDeletes.count()!==frBefore+1) throw new Error('profile + Ligne FR did not add a row');
    await page.getByRole('button',{name:'Supprimer la ligne française '+(frBefore+1),exact:true}).click();
    if(await page.getByRole('button',{name:/Supprimer la ligne française/}).count()!==frBefore) throw new Error('profile FR delete did not remove the added row');
    prove(viewport,'settings-profile-header-fr-add-delete');

    await page.getByRole('button',{name:'+ Ligne AR',exact:true}).click();
    arDeletes=page.getByRole('button',{name:/Supprimer la ligne arabe/});
    if(await arDeletes.count()!==arBefore+1) throw new Error('profile + Ligne AR did not add a row');
    await page.getByRole('button',{name:'Supprimer la ligne arabe '+(arBefore+1),exact:true}).click();
    if(await page.getByRole('button',{name:/Supprimer la ligne arabe/}).count()!==arBefore) throw new Error('profile AR delete did not remove the added row');
    prove(viewport,'settings-profile-header-ar-add-delete');

    const firstFrDelete=page.getByRole('button',{name:'Supprimer la ligne française 1',exact:true});
    const firstFrInput=firstFrDelete.locator('xpath=..').locator('input');
    await firstFrInput.fill('G5 Header Custom');
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
    await profileSave.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
    profileCheck=await api.get('/api/clinics/me',{headers});
    profileBody=await profileCheck.json();
    if(profileBody.header_customized!==true || profileBody.header_lines_fr?.[0]!=='G5 Header Custom'){
      throw new Error('profile manual header did not persist');
    }
    prove(viewport,'settings-profile-header-custom-save');

    const resetHeader=page.getByRole('button',{name:/Réinitialiser depuis le cabinet|Modèle Benmoussa/});
    const resetHeaderLabel=(await resetHeader.innerText()).trim();
    await resetHeader.click();
    profileSave=page.getByRole('button',{name:'Enregistrer la configuration',exact:true});
    await profileSave.click();
    await page.getByText('Configuration enregistrée',{exact:true}).waitFor({state:'visible',timeout:10000});
    profileCheck=await api.get('/api/clinics/me',{headers});
    profileBody=await profileCheck.json();
    if(profileBody.header_lines_fr?.[0]==='G5 Header Custom') throw new Error('profile header reset left manual content active');
    if(resetHeaderLabel.includes('Réinitialiser') && profileBody.header_customized!==false){
      throw new Error('profile owner header reset did not restore automatic mode');
    }
    prove(viewport,'settings-profile-header-reset',{resetHeaderLabel});

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

  // Ambiance modal close/cancel semantics before applying a preset.
  await page.getByRole('button',{name:/Ambiance active/i}).click();
  await page.getByRole('heading',{name:/ambiances cohérentes, prêtes à l'emploi/i}).waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:'Fermer les ambiances',exact:true}).click();
  await page.getByRole('heading',{name:/ambiances cohérentes, prêtes à l'emploi/i}).waitFor({state:'detached',timeout:5000});
  prove(viewport,'settings-branding-ambiance-close');

  await page.getByRole('button',{name:/Ambiance active/i}).click();
  await page.getByRole('button',{name:'Annuler',exact:true}).click();
  await page.getByRole('heading',{name:/ambiances cohérentes, prêtes à l'emploi/i}).waitFor({state:'detached',timeout:5000});
  prove(viewport,'settings-branding-ambiance-cancel');

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
    // Install deterministic Mobile Security + Audit fixtures before mounting the Security tab.
    let bridgeOptionsCalls=0,bridgePairingCalls=0,revokeMobileCalls=0;
    let failBridgeOptions=false,failNextBridgePairing=false;
    const bridgeTargets=[
      {id:1,name:'Dr T2 Browser',email:'t2-browser@cabinet.ma',role:'DENTISTE',is_current_user:true,destinations:[
        {id:'dashboard',label:'Tableau de bord mobile'},
        {id:'agenda',label:'Agenda mobile'}
      ]},
      {id:2,name:'Assistante G5',email:'assistante-g5@cabinet.ma',role:'SECRETAIRE',is_current_user:false,destinations:[
        {id:'agenda',label:'Agenda mobile'},
        {id:'frontdesk',label:'Accueil mobile'}
      ]}
    ];
    await page.route('**/api/mobile/bridge-options',route=>{
      bridgeOptionsCalls+=1;
      if(failBridgeOptions) return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Options mobiles indisponibles"}'});
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({targets:bridgeTargets,expires_in:300})});
    });
    await page.route('**/api/mobile/bridge-pairing',route=>{
      bridgePairingCalls+=1;
      if(failNextBridgePairing){
        failNextBridgePairing=false;
        return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Pairing refusé"}'});
      }
      const body=route.request().postDataJSON();
      const target=bridgeTargets.find(x=>x.id===body.target_user_id);
      const destination=target?.destinations.find(x=>x.id===body.destination);
      const qrSvg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" fill="black"/></svg>').toString('base64');
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
        qr_code:'data:image/svg+xml;base64,'+qrSvg,
        token_code:'G5MOBILE',
        expires_in:300,
        target_user_id:body.target_user_id,
        target_user_name:target?.name||'Utilisateur',
        target_role:target?.role||'',
        destination:body.destination,
        destination_label:destination?.label||body.destination,
        contains_patient_data:false
      })});
    });
    await page.route('**/api/admin/revoke-mobile',route=>{
      revokeMobileCalls+=1;
      return route.fulfill({status:200,contentType:'application/json',body:'{}'});
    });

    let auditCalls=[];
    let failAuditRead=false;
    const makeAuditLog=(id,action='LOGIN_SUCCESS',severity='INFO')=>({
      id,
      timestamp:'2026-09-23T10:00:00Z',
      user_id:1,
      employer_id:1,
      action,
      resource_type:'Patient',
      resource_id:String(id),
      severity,
      ip_address:'127.0.0.1',
      details:'G5 audit detail '+id
    });
    await page.route('**/api/admin/audit-logs*',route=>{
      const url=new URL(route.request().url());
      const action=url.searchParams.get('action')||'';
      const severity=url.searchParams.get('severity')||'';
      const offset=Number(url.searchParams.get('offset')||'0');
      auditCalls.push({action,severity,offset});
      if(failAuditRead) return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"audit unavailable"}'});
      if(action || severity){
        const log=makeAuditLog(100,action||'DELETE',severity||'WARNING');
        return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({logs:[log],total:1})});
      }
      const logs=offset>=20
        ? [21,22,23,24,25].map(id=>makeAuditLog(id,id===21?'DELETE':'LOGIN_SUCCESS',id===21?'WARNING':'INFO'))
        : Array.from({length:20},(_,i)=>makeAuditLog(i+1,i===0?'DELETE':'LOGIN_SUCCESS',i===0?'WARNING':'INFO'));
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({logs,total:25})});
    });

    await security.click();

    // Mobile Security — options, target/destination, pairing success/refusal, revoke cancel/ACK, options retry.
    await page.getByRole('heading',{name:'Compagnon Mobile',exact:true}).waitFor({state:'visible',timeout:10000});
    const targetSelect=page.getByRole('combobox',{name:'Utilisateur mobile cible'});
    const destinationSelect=page.getByRole('combobox',{name:'Destination mobile'});
    await targetSelect.waitFor({state:'visible',timeout:10000});
    if(bridgeOptionsCalls<1) throw new Error('mobile bridge options were not loaded');

    await targetSelect.selectOption('2');
    await destinationSelect.selectOption('frontdesk');
    await page.getByRole('button',{name:'Générer le QR de connexion',exact:true}).click();
    await page.getByText('G5MOBILE',{exact:true}).waitFor({state:'visible',timeout:10000});
    await page.getByAltText('QR de connexion Digital Crown Mobile').waitFor({state:'visible',timeout:5000});
    if(bridgePairingCalls!==1) throw new Error('mobile pairing success call mismatch');
    prove(viewport,'settings-mobile-pairing-success',{bridgePairingCalls});

    await targetSelect.selectOption('1');
    await page.getByText('G5MOBILE',{exact:true}).waitFor({state:'detached',timeout:5000});
    failNextBridgePairing=true;
    await page.getByRole('button',{name:'Générer le QR de connexion',exact:true}).click();
    await page.getByText('Pairing refusé',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(await page.getByText('G5MOBILE',{exact:true}).count()) throw new Error('mobile pairing refusal left stale pairing visible');
    prove(viewport,'settings-mobile-pairing-refusal-non-mutation');

    page.once('dialog',dialog=>dialog.dismiss());
    await page.getByRole('button',{name:/Révoquer tous les accès mobiles/i}).click();
    if(revokeMobileCalls!==0) throw new Error('mobile revoke called despite cancelled confirmation');
    prove(viewport,'settings-mobile-revoke-cancel');

    page.once('dialog',dialog=>dialog.accept());
    await page.getByRole('button',{name:/Révoquer tous les accès mobiles/i}).click();
    await page.getByText(/Tous les téléphones ont été déconnectés/i).waitFor({state:'visible',timeout:10000});
    if(revokeMobileCalls!==1) throw new Error('mobile revoke ACK count mismatch');
    prove(viewport,'settings-mobile-revoke-success',{revokeMobileCalls});

    failBridgeOptions=true;
    await page.getByRole('button',{name:'Performance & Assistance',exact:true}).click();
    await page.getByRole('button',{name:'Sécurité & Backup',exact:true}).click();
    await page.getByText('Options mobiles indisponibles',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(!(await targetSelect.isDisabled())) throw new Error('mobile target selector enabled during options read failure');
    failBridgeOptions=false;
    await page.getByText('Options mobiles indisponibles',{exact:true}).locator('xpath=ancestor::div[1]').getByRole('button',{name:'Réessayer',exact:true}).click();
    await targetSelect.waitFor({state:'visible',timeout:10000});
    await page.waitForFunction(()=>!document.body.innerText.includes('Options mobiles indisponibles'));
    prove(viewport,'settings-mobile-options-retry',{bridgeOptionsCalls});

    // Audit log — filters, refresh, details, pagination, read failure + retry.
    await page.getByRole('heading',{name:"Journal d'Audit",exact:true}).waitFor({state:'visible',timeout:10000});
    const actionFilter=page.getByRole('combobox',{name:'Filtrer le journal par action'});
    const severityFilter=page.getByRole('combobox',{name:'Filtrer le journal par sévérité'});
    await actionFilter.selectOption('DELETE');
    await page.getByText('Suppression',{exact:true}).first().waitFor({state:'visible',timeout:10000});
    if(!auditCalls.some(x=>x.action==='DELETE')) throw new Error('audit action filter did not reach backend query');
    prove(viewport,'settings-audit-action-filter');

    await severityFilter.selectOption('WARNING');
    await page.getByText('Attention',{exact:true}).first().waitFor({state:'visible',timeout:10000});
    if(!auditCalls.some(x=>x.action==='DELETE'&&x.severity==='WARNING')) throw new Error('audit severity filter did not compose with action filter');
    prove(viewport,'settings-audit-severity-filter');

    await actionFilter.selectOption('');
    await severityFilter.selectOption('');
    await page.getByText('25 entrées',{exact:true}).waitFor({state:'visible',timeout:10000});
    const refreshBefore=auditCalls.length;
    await page.getByRole('button',{name:'Rafraîchir le journal',exact:true}).click();
    await page.waitForFunction(expected=>document.body.innerText.includes('25 entrées'),refreshBefore);
    if(auditCalls.length<=refreshBefore) throw new Error('audit refresh did not refetch');

    const detailsButton=page.getByRole('button',{name:/Voir les détails/i}).first();
    await detailsButton.click();
    await page.getByText('G5 audit detail 1',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'settings-audit-details-expand');

    await page.getByRole('button',{name:/Suivant/i}).click();
    await page.getByText('Page 2 / 2',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(!auditCalls.some(x=>x.offset===20)) throw new Error('audit pagination did not request second page');
    await page.getByRole('button',{name:/Précédent/i}).click();
    await page.getByText('Page 1 / 2',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-audit-pagination');

    failAuditRead=true;
    await page.getByRole('button',{name:'Rafraîchir le journal',exact:true}).click();
    await page.getByText("Journal d'audit indisponible",{exact:true}).waitFor({state:'visible',timeout:10000});
    if(await page.getByText('Aucun log trouvé',{exact:true}).count()) throw new Error('audit read failure rendered a false empty state');
    failAuditRead=false;
    const auditError=page.getByText("Journal d'audit indisponible",{exact:true}).locator('xpath=ancestor::div[contains(@class,"rounded")][1]');
    await auditError.getByRole('button',{name:'Réessayer',exact:true}).click();
    await page.getByText('25 entrées',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-audit-read-retry');

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

    await page.unroute('**/api/mobile/bridge-options');
    await page.unroute('**/api/mobile/bridge-pairing');
    await page.unroute('**/api/admin/revoke-mobile');
    await page.unroute('**/api/admin/audit-logs*');
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
    let failNextStatus=false,failTeamRead=false;

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
      if(method==='GET' && path==='/api/team/') {
        if(failTeamRead) return json(503,{detail:'forced team read failure'});
        return json(200,teamMembers);
      }

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

    // Create form auxiliary controls + role/permission semantics.
    await page.getByRole('button',{name:/Ajouter un membre/i}).click();
    const roleSelect=page.getByRole('combobox',{name:'Rôle du collaborateur'});
    if(await roleSelect.inputValue()!=='SECRETAIRE') throw new Error('team create default role is not secretary');
    if(!(await page.getByRole('checkbox',{name:/Dossiers Patients/i}).isChecked())) throw new Error('team secretary default patients permission missing');
    if(await page.getByRole('checkbox',{name:/Prescriptions/i}).isChecked()) throw new Error('team secretary default prescriptions permission unexpectedly enabled');

    const passwordInput=page.getByPlaceholder('••••••••');
    await passwordInput.fill('TestPass123!');
    if(await passwordInput.getAttribute('type')!=='password') throw new Error('team password is not masked by default');
    await page.getByRole('button',{name:'Afficher le mot de passe',exact:true}).click();
    if(await passwordInput.getAttribute('type')!=='text') throw new Error('team password reveal did not work');
    await page.getByRole('button',{name:'Masquer le mot de passe',exact:true}).click();
    if(await passwordInput.getAttribute('type')!=='password') throw new Error('team password re-mask did not work');
    prove(viewport,'settings-team-password-reveal-hide');

    await page.getByRole('button',{name:'Annuler',exact:true}).click();
    await page.getByText('Nouveau sous-compte',{exact:true}).waitFor({state:'detached',timeout:5000});
    if(teamCreateCalls!==0) throw new Error('team create cancel triggered a mutation');
    prove(viewport,'settings-team-create-cancel');

    await page.getByRole('button',{name:/Ajouter un membre/i}).click();
    const createRole=page.getByRole('combobox',{name:'Rôle du collaborateur'});
    await createRole.selectOption('DENTISTE');
    if(!(await page.getByRole('checkbox',{name:/Prescriptions/i}).isChecked())) throw new Error('team dentist defaults did not enable prescriptions');
    const settingsPermission=page.getByRole('checkbox',{name:/Réglages Cabinet/i});
    if(await settingsPermission.isChecked()) throw new Error('team dentist settings permission should default false');
    await settingsPermission.check();

    await page.getByPlaceholder('Ex: Fatima Zahra').fill('Browser New Member');
    await page.getByPlaceholder('assistante@cabinet.com').fill('browser-new@example.com');
    await page.getByPlaceholder('••••••••').fill('TestPass123!');
    await page.getByPlaceholder('06 00 00 00 00').fill('0600000000');
    await page.getByRole('button',{name:'Créer le compte',exact:true}).click();
    await page.getByText('Browser New Member',{exact:true}).waitFor({state:'visible',timeout:10000});
    const createdMember=teamMembers.find(m=>m.nom_complet==='Browser New Member');
    if(teamCreateCalls!==1 || createdMember?.role!=='DENTISTE' || createdMember?.permissions?.settings!==true){
      throw new Error('team create role/permissions ACK mismatch');
    }
    prove(viewport,'settings-team-create',{teamCreateCalls,role:createdMember.role});

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

    // Permissions modal close/cancel semantics, then persisted update.
    let activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle('Gérer les permissions').click();
    let permissionsDialog=page.getByText(/Droits d'accès : Active User/).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    await permissionsDialog.getByRole('button',{name:'Annuler',exact:true}).click();
    await page.getByText(/Droits d'accès : Active User/).waitFor({state:'detached',timeout:5000});
    if(permissionCalls!==0) throw new Error('team permissions cancel triggered mutation');
    prove(viewport,'settings-team-permissions-cancel');

    activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle('Gérer les permissions').click();
    permissionsDialog=page.getByText(/Droits d'accès : Active User/).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
    await permissionsDialog.getByRole('button',{name:'Fermer les permissions',exact:true}).click();
    await page.getByText(/Droits d'accès : Active User/).waitFor({state:'detached',timeout:5000});
    if(permissionCalls!==0) throw new Error('team permissions close triggered mutation');
    prove(viewport,'settings-team-permissions-close');

    activeCard=memberCard('Active User');
    await activeCard.hover();
    await activeCard.getByTitle('Gérer les permissions').click();
    permissionsDialog=page.getByText(/Droits d'accès : Active User/).locator('xpath=ancestor::div[contains(@class,"fixed")][1]');
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

    // Team truth gate read failure -> no management UI -> retry restores truth.
    failTeamRead=true;
    await page.getByRole('button',{name:'Performance & Assistance',exact:true}).click();
    await page.getByRole('button',{name:'Mon Équipe',exact:true}).click();
    await page.getByText('Équipe indisponible',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(await page.getByRole('button',{name:/Ajouter un membre/i}).count()) throw new Error('team controls exposed while truth gate failed');
    failTeamRead=false;
    await page.getByRole('button',{name:'Réessayer',exact:true}).click();
    await page.getByText('Active User',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'settings-team-read-retry');

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
