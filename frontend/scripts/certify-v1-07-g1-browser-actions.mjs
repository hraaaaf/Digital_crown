import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const apiLogin=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!apiLogin.ok()) throw new Error('G1 API login failed');
const apiTokens=await apiLogin.json();
const apiHeaders={Authorization:'Bearer '+apiTokens.access_token};

const browser=await chromium.launch({headless:true});
const viewports=[{width:390,height:844},{width:1280,height:900}];
const proofs=[];
function prove(v,a,d={}){proofs.push({viewport:v.width+'x'+v.height,action:a,status:'PASS',...d});}

for(const viewport of viewports){
  const ctx=await browser.newContext({viewport,colorScheme:'light'});
  const page=await ctx.newPage();

  // Landing: Morocco truth + real form refusal/non-false-success.
  await page.goto('http://127.0.0.1:5173/landing',{waitUntil:'networkidle',timeout:90000});
  await page.getByText(/dentistes marocains/i).waitFor({state:'visible',timeout:10000});
  if(await page.getByText(/dentistes algériens/i).count()) throw new Error('landing geography regression');
  prove(viewport,'landing-morocco-truth');

  await page.route('**/api/public/demo-request',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"offline"}'}));
  const name=page.getByPlaceholder('Votre nom *');
  if(await name.count()){
    await name.fill('Dr Browser');
    await page.getByPlaceholder('Email professionnel *').fill('browser@example.com');
    await page.getByPlaceholder('Nom du cabinet *').fill('Cabinet Browser');
    await page.getByRole('button',{name:/Envoyer ma demande/i}).click();
    await page.waitForTimeout(350);
    if(await page.getByText('Demande envoyée !',{exact:true}).count()) throw new Error('false landing success on refused demo request');
    prove(viewport,'landing-demo-refusal-no-false-success');
  }
  await page.unroute('**/api/public/demo-request');

  // Landing success ACK: same control must reach a real visible success state.
  await page.route('**/api/public/demo-request',route=>route.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'}));
  await page.getByRole('button',{name:/Envoyer ma demande/i}).click();
  await page.getByRole('heading',{name:'Demande envoyée !',exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'landing-demo-success-ack');
  await page.unroute('**/api/public/demo-request');

  // Register: legal gating + backend refusal truth.
  await page.goto('http://127.0.0.1:5173/register',{waitUntil:'networkidle',timeout:90000});
  await page.getByPlaceholder('Dr. Jean Dupont').fill('Dr Browser');
  await page.getByPlaceholder('votre@email.com').fill('browser@example.com');
  await page.getByPlaceholder('8 caractères minimum').fill('Secret123!');
  const submit=page.getByRole('button',{name:/Créer mon compte/i});
  if(!(await submit.isDisabled())) throw new Error('registration enabled before legal consent');
  const checks=page.getByRole('checkbox');
  await checks.nth(0).check();
  if(!(await submit.isDisabled())) throw new Error('registration enabled after one legal consent');
  await checks.nth(1).check();
  if(await submit.isDisabled()) throw new Error('registration stayed disabled after both legal consents');
  prove(viewport,'register-legal-gating');

  await page.route('**/api/auth/signup',route=>route.fulfill({status:400,contentType:'application/json',body:'{"detail":"Email déjà utilisé."}'}));
  await submit.click();
  await page.getByText('Email déjà utilisé.',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(await page.getByText('Demande Envoyée',{exact:true}).count()) throw new Error('false register success on refusal');
  prove(viewport,'register-refusal-no-false-success');
  await page.unroute('**/api/auth/signup');

  await page.goto('http://127.0.0.1:5173/register',{waitUntil:'networkidle',timeout:90000});
  await page.getByPlaceholder('Dr. Jean Dupont').fill('Dr Browser Success');
  await page.getByPlaceholder('votre@email.com').fill('browser-success@example.com');
  await page.getByPlaceholder('8 caractères minimum').fill('Secret123!');
  const successChecks=page.getByRole('checkbox');
  await successChecks.nth(0).check();
  await successChecks.nth(1).check();
  await page.route('**/api/auth/signup',route=>route.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'}));
  await page.getByRole('button',{name:/Créer mon compte/i}).click();
  await page.getByRole('heading',{name:'Demande Envoyée',exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'register-success-ack');
  await page.unroute('**/api/auth/signup');

  // Trial activation: preview + explicit activation refusal.
  await page.route('**/api/public/trial-code/DC-BROWSER',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
    email:'invite@example.com',nom_complet:'Dr Invite',cabinet_name:'Cabinet Invite',trial_days:30,expires_at:'2030-01-01T00:00:00Z'
  })}));
  await page.route('**/api/public/activate-trial',route=>route.fulfill({status:400,contentType:'application/json',body:'{"detail":"Code déjà utilisé."}'}));
  await page.goto('http://127.0.0.1:5173/activate?code=DC-BROWSER',{waitUntil:'networkidle',timeout:90000});
  await page.locator('input[value="invite@example.com"]').waitFor({state:'visible',timeout:5000});
  await page.getByPlaceholder('8 caractères minimum').fill('Secret123!');
  const trialChecks=page.getByRole('checkbox');
  await trialChecks.nth(0).check();
  await trialChecks.nth(1).check();
  await page.getByRole('button',{name:/Activer Mon Essai/i}).click();
  await page.getByText('Code déjà utilisé.',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(await page.getByText('Essai activé',{exact:true}).count()) throw new Error('false trial activation success');
  prove(viewport,'trial-preview-and-refusal-truth');
  await page.unroute('**/api/public/trial-code/DC-BROWSER');
  await page.unroute('**/api/public/activate-trial');

  await page.route('**/api/public/trial-code/DC-BROWSER-SUCCESS',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
    email:'invite-success@example.com',nom_complet:'Dr Invite Success',cabinet_name:'Cabinet Invite Success',trial_days:30,expires_at:'2030-01-01T00:00:00Z'
  })}));
  await page.route('**/api/public/activate-trial',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
    message:'Essai activé. Vous pouvez maintenant vous connecter.'
  })}));
  await page.goto('http://127.0.0.1:5173/activate?code=DC-BROWSER-SUCCESS',{waitUntil:'networkidle',timeout:90000});
  await page.locator('input[value="invite-success@example.com"]').waitFor({state:'visible',timeout:5000});
  await page.getByPlaceholder('8 caractères minimum').fill('Secret123!');
  const successTrialChecks=page.getByRole('checkbox');
  await successTrialChecks.nth(0).check();
  await successTrialChecks.nth(1).check();
  await page.getByRole('button',{name:/Activer Mon Essai/i}).click();
  await page.getByText('Essai activé. Vous pouvez maintenant vous connecter.',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'trial-activation-success-ack');
  await page.unroute('**/api/public/trial-code/DC-BROWSER-SUCCESS');
  await page.unroute('**/api/public/activate-trial');

  // Login refusal then real isolated-runtime success.
  await page.goto('http://127.0.0.1:5173/login',{waitUntil:'networkidle',timeout:90000});
  await page.getByPlaceholder('nom@cabinet.com').fill('t2-browser@cabinet.ma');
  await page.getByPlaceholder('••••••••').fill('bad-password');
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.getByText(/Email ou mot de passe incorrect|Identifiants invalides/i).waitFor({state:'visible',timeout:5000});
  if(page.url().includes('/dashboard')) throw new Error('login refusal navigated to dashboard');
  prove(viewport,'login-refusal-no-navigation');

  await page.getByPlaceholder('••••••••').fill(password);
  await page.getByRole('button',{name:'Se connecter',exact:true}).click();
  await page.waitForURL('**/dashboard',{timeout:15000});
  prove(viewport,'login-real-success-navigation');

  // Mobile onboarding manual code gate + claim refusal.
  await page.goto('http://127.0.0.1:5173/mobile/onboarding',{waitUntil:'networkidle',timeout:90000});
  const pairing=page.getByLabel("Code d'appairage à 6 chiffres");
  if(await pairing.count()){
    const ok=page.getByRole('button',{name:"Valider le code d'appairage"});
    if(!(await ok.isDisabled())) throw new Error('pairing OK enabled before six digits');
    await pairing.fill('123456');
    if(await ok.isDisabled()) throw new Error('pairing OK disabled with six digits');

    await page.route('**/*',async route=>{
      const req=route.request();
      if(req.method()==='POST' && /pair|claim|mobile/i.test(req.url())){
        return route.fulfill({status:401,contentType:'application/json',body:'{"detail":"Code expiré."}'});
      }
      return route.continue();
    });
    await ok.click();
    await page.getByText(/Échec de l'appairage/i).waitFor({state:'visible',timeout:10000});
    if(await page.getByText('Appairage réussi',{exact:true}).count()) throw new Error('false mobile pairing success');
    prove(viewport,'mobile-pairing-refusal-truth');
    await page.unroute('**/*');
  }

  // Mobile pairing success: real bridge generation + real ECDH claim + server destination.
  const me=await api.get('/api/auth/me',{headers:apiHeaders});
  if(!me.ok()) throw new Error('G1 /me failed for secure pairing');
  const meBody=await me.json();
  const bridge=await api.post('/api/mobile/bridge-pairing',{
    headers:apiHeaders,
    data:{target_user_id:meBody.id,destination:'agenda'},
  });
  if(!bridge.ok()) throw new Error('secure bridge generation failed '+bridge.status()+': '+await bridge.text());
  const bridgeBody=await bridge.json();
  if(!/^\d{6}$/.test(bridgeBody.token_code||'')) throw new Error('secure bridge manual code invalid');

  await page.goto('http://127.0.0.1:5173/mobile/onboarding',{waitUntil:'networkidle',timeout:90000});
  const securePairing=page.getByLabel("Code d'appairage à 6 chiffres");
  await securePairing.waitFor({state:'visible',timeout:10000});
  await securePairing.fill(bridgeBody.token_code);
  const secureOk=page.getByRole('button',{name:"Valider le code d'appairage"});
  if(await secureOk.isDisabled()) throw new Error('secure pairing submit remained disabled');
  await secureOk.click();
  await page.getByText('Appairage réussi',{exact:true}).waitFor({state:'visible',timeout:15000});
  prove(viewport,'mobile-pairing-secure-ecdh-success',{destination:bridgeBody.destination});
  await page.waitForURL(/\/mobile\/dashboard\?tab=agenda/,{timeout:10000});
  prove(viewport,'mobile-pairing-destination-navigation');

  await ctx.close();

  // SETUP WIZARD — validation, back/next, refusal without persistence, then full ACK to Dashboard.
  const setupCtx=await browser.newContext({viewport,colorScheme:'light'});
  const setupPage=await setupCtx.newPage();
  await setupPage.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
    localStorage.removeItem('digitalcrown_theme');
    sessionStorage.removeItem('digitalcrown-setup-storage');
  },{access:apiTokens.access_token,refresh:apiTokens.refresh_token});

  let setupInitialized=false;
  let failSetupCreate=true;
  let setupCreateCalls=0,completeSetupCalls=0;
  let setupPayload=null;
  await setupPage.route('**/api/clinics/init-status',route=>route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify({is_initialized:setupInitialized})
  }));
  await setupPage.route('**/api/clinics/me/practitioner',route=>route.fulfill({
    status:404,contentType:'application/json',body:JSON.stringify({detail:'not configured'})
  }));
  await setupPage.route('**/api/clinics/me',route=>{
    if(route.request().method()==='GET') return route.fulfill({status:404,contentType:'application/json',body:JSON.stringify({detail:'not configured'})});
    return route.continue();
  });
  await setupPage.route('**/api/clinics/',async route=>{
    if(route.request().method()!=='POST') return route.continue();
    setupCreateCalls+=1;
    setupPayload=route.request().postDataJSON();
    if(failSetupCreate) return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced setup refusal'})});
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({...setupPayload,is_initialized:false})});
  });
  await setupPage.route('**/api/clinics/complete-setup',route=>{
    completeSetupCalls+=1;
    setupInitialized=true;
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({is_initialized:true})});
  });

  await setupPage.goto('http://127.0.0.1:5173/setup',{waitUntil:'networkidle',timeout:90000});
  await setupPage.locator('[data-flow-step="1"]').waitFor({state:'visible',timeout:10000});
  await setupPage.getByRole('button',{name:/Continuer/i}).click();
  if((await setupPage.locator('[data-flow-step="1"]').count())!==1) throw new Error('setup advanced with missing required identity');
  if(setupCreateCalls!==0) throw new Error('setup validation triggered backend mutation');
  prove(viewport,'setup-step1-required-validation');

  await setupPage.getByPlaceholder(/Cabinet Dentaire|Centre Dentaire/).fill('Cabinet Browser Setup');
  await setupPage.getByPlaceholder('Étage, Résidence, Rue, Ville...').fill('Rabat Browser');
  await setupPage.getByPlaceholder('Dr. Jean Dupont').fill('Dr Browser Setup');
  await setupPage.getByRole('button',{name:/Continuer/i}).click();
  await setupPage.locator('[data-flow-step="2"]').waitFor({state:'visible',timeout:5000});
  await setupPage.getByRole('button',{name:/Retour/i}).click();
  await setupPage.locator('[data-flow-step="1"]').waitFor({state:'visible',timeout:5000});
  await setupPage.getByRole('button',{name:/Continuer/i}).click();
  for(let step=3;step<=7;step++){
    await setupPage.getByRole('button',{name:/Continuer/i}).click();
    await setupPage.locator('[data-flow-step="'+step+'"]').waitFor({state:'visible',timeout:5000});
  }
  prove(viewport,'setup-next-back-step-flow');

  if(await setupPage.evaluate(()=>localStorage.getItem('digitalcrown_theme')!==null)) throw new Error('setup theme persisted before backend ACK');
  await setupPage.getByRole('button',{name:/Finaliser l.Installation/i}).click();
  await setupPage.getByText(/Échec de l'initialisation/i).waitFor({state:'visible',timeout:10000});
  if(!setupPage.url().includes('/setup') || completeSetupCalls!==0) throw new Error('setup refusal produced false navigation/completion');
  if(await setupPage.evaluate(()=>localStorage.getItem('digitalcrown_theme')!==null)) throw new Error('setup refusal persisted theme');
  prove(viewport,'setup-finalization-refusal-non-mutation',{setupCreateCalls});

  failSetupCreate=false;
  await setupPage.getByRole('button',{name:/Finaliser l.Installation/i}).click();
  await setupPage.waitForURL('**/dashboard',{timeout:15000});
  if(setupCreateCalls!==2 || completeSetupCalls!==1) throw new Error('setup success ACK count mismatch');
  if(setupPayload?.nom_cabinet!=='Cabinet Browser Setup' || setupPayload?.nom!=='Dr Browser Setup' || setupPayload?.footer_address!=='Rabat Browser'){
    throw new Error('setup final payload mismatch');
  }
  const persistedTheme=await setupPage.evaluate(()=>localStorage.getItem('digitalcrown_theme'));
  if(!persistedTheme) throw new Error('setup theme not persisted after ACK');
  prove(viewport,'setup-finalization-success-ack',{theme:persistedTheme});
  await setupCtx.close();

  // SHARED SHELL — real clicks must reach canonical routes and preserve permission truth.
  const shellCtx=await browser.newContext({viewport,colorScheme:'light'});
  const shellPage=await shellCtx.newPage();
  await shellPage.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:apiTokens.access_token,refresh:apiTokens.refresh_token});

  await shellPage.route('**/api/intelligence/connect-hub',route=>route.fulfill({
    status:200,
    contentType:'application/json',
    body:JSON.stringify({
      total:1,
      requires_attention:1,
      delivery_semantics:'source_state_only',
      items:[{
        id:'g1-attention',
        source:'treasury_hub',
        title:'Relance certification',
        message:'Paiement attendu',
        destination:'/accounting?tab=treasury',
        priority:'high',
        channel:'in_app',
        delivery_state:'source',
        delivery_verified:false
      }]
    })
  }));
  await shellPage.route('**/api/auth/logout',route=>route.fulfill({status:200,contentType:'application/json',body:'{}'}));

  const openSidebar=async()=>{
    const agendaLink=shellPage.getByRole('link',{name:'Agenda',exact:true});
    const box=await agendaLink.boundingBox().catch(()=>null);
    const viewport=shellPage.viewportSize();
    const inViewport=Boolean(
      box && viewport &&
      box.x < viewport.width && box.x + box.width > 0 &&
      box.y < viewport.height && box.y + box.height > 0
    );
    if(!inViewport){
      const menu=shellPage.getByRole('button',{name:'Menu',exact:true});
      if(await menu.count()) await menu.click();
    }
  };
  const clickSidebar=async(label,urlPattern)=>{
    await openSidebar();
    const link=shellPage.getByRole('link',{name:label,exact:true});
    await link.waitFor({state:'visible',timeout:10000});
    await link.click();
    await shellPage.waitForURL(urlPattern,{timeout:10000});
  };

  await shellPage.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
  await clickSidebar('Agenda','**/agenda');
  prove(viewport,'shell-nav-agenda');
  await clickSidebar('Patients','**/patients');
  prove(viewport,'shell-nav-patients');
  await clickSidebar('Bibliothèque clinique','**/bibliotheque');
  prove(viewport,'shell-nav-library');
  await clickSidebar('Approvisionnement','**/approvisionnement');
  prove(viewport,'shell-nav-procurement');

  const settingsLink=shellPage.getByTitle('Réglages');
  await settingsLink.waitFor({state:'visible',timeout:10000});
  await settingsLink.click();
  await shellPage.waitForURL('**/settings',{timeout:10000});
  prove(viewport,'shell-header-settings-navigation');

  await shellPage.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
  const attention=shellPage.getByRole('button',{name:'Ouvrir le centre d’attention',exact:true});
  await attention.click();
  await shellPage.getByText('Centre d’attention',{exact:true}).waitFor({state:'visible',timeout:5000});
  const attentionLink=shellPage.getByRole('link',{name:/Relance certification/i});
  await attentionLink.click();
  await shellPage.waitForURL(/\/accounting\?tab=treasury/,{timeout:10000});
  prove(viewport,'shell-attention-destination');

  await shellPage.goto('http://127.0.0.1:5173/dashboard',{waitUntil:'networkidle',timeout:90000});
  const logout=shellPage.getByTitle('Déconnexion');
  await logout.click();
  await shellPage.getByText('Êtes-vous sûr de vouloir vous déconnecter de votre session ?',{exact:true}).waitFor({state:'visible',timeout:5000});
  await shellPage.getByRole('button',{name:'Annuler',exact:true}).click();
  if(!await shellPage.evaluate(()=>Boolean(localStorage.getItem('token')))) throw new Error('logout cancel cleared session');
  prove(viewport,'shell-logout-cancel-non-mutation');

  await logout.click();
  await shellPage.getByRole('button',{name:'Confirmer',exact:true}).click();
  await shellPage.waitForFunction(()=>window.location.pathname==='/landing',undefined,{timeout:10000});
  if(await shellPage.evaluate(()=>Boolean(localStorage.getItem('token')))) throw new Error('logout confirm kept access token');
  prove(viewport,'shell-logout-confirm-clears-session');
  await shellPage.unroute('**/api/intelligence/connect-hub');
  await shellPage.unroute('**/api/auth/logout');
  await shellCtx.close();
}

await browser.close();
await api.dispose();
console.log('G1_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
