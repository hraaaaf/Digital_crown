import { chromium } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

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

  // Trial activation: preview + explicit activation refusal.
  await page.route('**/api/public/trial-code/DC-BROWSER',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
    email:'invite@example.com',nom_complet:'Dr Invite',cabinet_name:'Cabinet Invite',trial_days:30,expires_at:'2030-01-01T00:00:00Z'
  })}));
  await page.route('**/api/public/activate-trial',route=>route.fulfill({status:400,contentType:'application/json',body:'{"detail":"Code déjà utilisé."}'}));
  await page.goto('http://127.0.0.1:5173/activate?code=DC-BROWSER',{waitUntil:'networkidle',timeout:90000});
  await page.getByDisplayValue('invite@example.com').waitFor({state:'visible',timeout:5000});
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

  await ctx.close();
}

await browser.close();
console.log('G1_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
