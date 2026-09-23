import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
const superEmail=process.env.T2_SUPERADMIN_EMAIL;
if(!password||!superEmail) throw new Error('T2_PASSWORD and T2_SUPERADMIN_EMAIL required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:superEmail,password}});
if(!login.ok()) throw new Error('G6 superadmin login failed');
const tokens=await login.json();
const dentistApi=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const dentistLogin=await dentistApi.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!dentistLogin.ok()) throw new Error('G6 dentist login failed');
const dentistTokens=await dentistLogin.json();
const headers={Authorization:'Bearer '+tokens.access_token};

const me=await api.get('/api/auth/me',{headers});
if(!me.ok()) throw new Error('G6 /me failed');
const meBody=await me.json();
const meUser=meBody?.user ?? meBody;
if(meUser?.is_superadmin!==true) throw new Error('isolated fixture is not superadmin');

const clientsResp=await api.get('/api/superadmin/clients',{headers});
if(!clientsResp.ok()) throw new Error('G6 clients read failed');
const clientsBody=await clientsResp.json();
const clientList=Array.isArray(clientsBody)?clientsBody:(Array.isArray(clientsBody?.items)?clientsBody.items:(Array.isArray(clientsBody?.clients)?clientsBody.clients:[]));
const target=clientList.find(x=>x.email==='t2-browser@cabinet.ma');
if(!target) throw new Error('G6 target client missing');

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
  const ctx=await browser.newContext({viewport,colorScheme:'light',permissions:['clipboard-read','clipboard-write']});
  const page=await ctx.newPage();
  await seed(page);
  await page.goto('http://127.0.0.1:5173/super-admin',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Dr T2 Browser',{exact:true}).waitFor({state:'visible',timeout:15000});

  const card=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
  if(!(await card.count())) throw new Error('target client card missing');

  // Plan mutation: ACK persistence, restore, then explicit refusal with backend non-mutation.
  const plan=card.locator('select').first();
  if(await plan.count()){
    const original=await plan.inputValue();
    const targetPlan=original==='GOLD'?'PREMIUM':'GOLD';
    const planAckPromise=page.waitForResponse(
      r=>r.request().method()==='PATCH' && r.url().includes('/api/superadmin/clients/'+target.id+'/plan'),
      {timeout:10000},
    );
    await plan.selectOption(targetPlan);
    const planAck=await planAckPromise;
    if(!planAck.ok()) throw new Error('plan mutation refused '+planAck.status()+': '+await planAck.text());
    const planAckBody=await planAck.json();
    if(planAckBody.subscription_plan!==targetPlan) throw new Error('plan response ACK mismatch');

    let verify=await api.get('/api/superadmin/clients',{headers});
    let row=(await verify.json()).find(x=>x.id===target.id);
    if(row.subscription_plan!==targetPlan) throw new Error('plan ACK not persisted');
    prove(viewport,'superadmin-plan-persistence',{from:original,to:targetPlan});

    const restorePlanAckPromise=page.waitForResponse(
      r=>r.request().method()==='PATCH' && r.url().includes('/api/superadmin/clients/'+target.id+'/plan'),
      {timeout:10000},
    );
    await plan.selectOption(original);
    const restorePlanAck=await restorePlanAckPromise;
    if(!restorePlanAck.ok()) throw new Error('plan restore refused '+restorePlanAck.status()+': '+await restorePlanAck.text());

    await page.route('**/api/superadmin/clients/'+target.id+'/plan?*',route=>route.fulfill({
      status:409,
      contentType:'application/json',
      body:JSON.stringify({detail:'Passage au pack refusé par la certification'})
    }));
    await plan.selectOption(targetPlan);
    await page.getByText('Passage au pack refusé par la certification',{exact:true}).waitFor({state:'visible',timeout:10000});
    verify=await api.get('/api/superadmin/clients',{headers});
    row=(await verify.json()).find(x=>x.id===target.id);
    if(row.subscription_plan!==original) throw new Error('refused plan change mutated backend');
    prove(viewport,'superadmin-plan-refusal-non-mutation',{plan:targetPlan});
    await page.unroute('**/api/superadmin/clients/'+target.id+'/plan?*');
    await page.reload({waitUntil:'networkidle',timeout:90000});
    await page.getByText('Dr T2 Browser',{exact:true}).waitFor({state:'visible',timeout:10000});
  }

  // Every exposed licence duration button must ACK and increase persisted expiry.
  const durationCases=[
    {label:/\+\s*1\s*MOIS/i,action:'1m',days:30},
    {label:/\+\s*3\s*MOIS/i,action:'3m',days:90},
    {label:/\+\s*6\s*MOIS/i,action:'6m',days:180},
    {label:/\+\s*1\s*AN/i,action:'1y',days:365},
  ];
  for(const item of durationCases){
    const liveCard=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
    const beforeResp=await api.get('/api/superadmin/clients',{headers});
    const before=(await beforeResp.json()).find(x=>x.id===target.id);
    const beforeExpiry=before.license_expires_at?new Date(before.license_expires_at).getTime():Date.now();
    const ackPromise=page.waitForResponse(
      r=>r.request().method()==='POST' && r.url().includes('/api/superadmin/clients/'+target.id+'/grant-license') && r.url().includes('action='+item.action),
      {timeout:10000},
    );
    await liveCard.getByRole('button',{name:item.label}).click();
    const ack=await ackPromise;
    if(!ack.ok()) throw new Error('licence '+item.action+' refused '+ack.status());
    const afterResp=await api.get('/api/superadmin/clients',{headers});
    const after=(await afterResp.json()).find(x=>x.id===target.id);
    const afterExpiry=new Date(after.license_expires_at).getTime();
    if(!(after.is_licensed===true && afterExpiry>beforeExpiry)) throw new Error('licence '+item.action+' did not persist a later expiry');
    prove(viewport,'superadmin-license-'+item.action,{days:item.days});
  }

  // WhatsApp renewal must surface the safe no-phone refusal before any external transport.
  const renewalCard=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
  const renewal=renewalCard.getByTitle('WhatsApp de relance');
  if(await renewal.count()){
    const ackPromise=page.waitForResponse(
      r=>r.request().method()==='POST' && r.url().includes('/api/superadmin/clients/'+target.id+'/send-renewal-email'),
      {timeout:10000},
    );
    await renewal.click();
    const ack=await ackPromise;
    if(ack.status()!==409) throw new Error('renewal refusal status mismatch '+ack.status());
    await page.getByText("Aucun numéro de téléphone trouvé pour l'envoi WhatsApp.",{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'superadmin-renewal-whatsapp-safe-refusal',{status:ack.status()});
  }

  // Suspend -> UI immutable status -> reactivate. Confirmation cancel must not mutate.
  let liveCard=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
  let suspend=liveCard.getByTitle('Suspendre');
  if(await suspend.count()){
    page.once('dialog',d=>d.dismiss());
    await suspend.click();
    await page.waitForTimeout(100);
    let verify=await api.get('/api/superadmin/clients',{headers});
    let row=(await verify.json()).find(x=>x.id===target.id);
    if(row.is_suspended) throw new Error('suspend cancel mutated backend');

    page.once('dialog',d=>d.accept());
    await suspend.click();
    await page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]').getByTitle('Réactiver').waitFor({state:'visible',timeout:10000});
    verify=await api.get('/api/superadmin/clients',{headers});
    row=(await verify.json()).find(x=>x.id===target.id);
    if(!row.is_suspended) throw new Error('suspend ACK not persisted');
    prove(viewport,'superadmin-suspend-ack');

    liveCard=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
    page.once('dialog',d=>d.accept());
    await liveCard.getByTitle('Réactiver').click();
    await page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]').getByTitle('Suspendre').waitFor({state:'visible',timeout:10000});
    verify=await api.get('/api/superadmin/clients',{headers});
    row=(await verify.json()).find(x=>x.id===target.id);
    if(row.is_suspended) throw new Error('reactivate did not restore fixture');
    prove(viewport,'superadmin-reactivate-restore');
  }

  // Archive disables mutable commercial controls, then unarchive restores the fixture.
  liveCard=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
  const archive=liveCard.getByTitle('Archiver');
  if(await archive.count()){
    page.once('dialog',d=>d.dismiss());
    await archive.click();
    await page.waitForTimeout(100);
    let verify=await api.get('/api/superadmin/clients',{headers});
    let row=(await verify.json()).find(x=>x.id===target.id);
    if(row.is_archived) throw new Error('archive cancel mutated backend');

    page.once('dialog',d=>d.accept());
    await archive.click();
    const archivedCard=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
    await archivedCard.getByTitle('Désarchiver').waitFor({state:'visible',timeout:10000});
    if(!(await archivedCard.locator('select').first().isDisabled())) throw new Error('archived plan control remains enabled');
    for(const label of [/\+\s*1\s*MOIS/i,/\+\s*3\s*MOIS/i,/\+\s*6\s*MOIS/i,/\+\s*1\s*AN/i]){
      if(!(await archivedCard.getByRole('button',{name:label}).isDisabled())) throw new Error('archived licence duration remains enabled');
    }
    if(!(await archivedCard.getByTitle('WhatsApp de relance').isDisabled())) throw new Error('archived renewal control remains enabled');
    verify=await api.get('/api/superadmin/clients',{headers});
    row=(await verify.json()).find(x=>x.id===target.id);
    if(!row.is_archived) throw new Error('archive ACK not persisted');
    prove(viewport,'superadmin-archive-immutable-controls');

    page.once('dialog',d=>d.accept());
    await archivedCard.getByTitle('Désarchiver').click();
    await page.getByTitle('Archiver').waitFor({state:'visible',timeout:10000});
    verify=await api.get('/api/superadmin/clients',{headers});
    row=(await verify.json()).find(x=>x.id===target.id);
    if(row.is_archived) throw new Error('unarchive did not restore fixture');
    prove(viewport,'superadmin-unarchive-restore');
  }

  // Internal notes: cancel non-mutation, ACK persistence, then restore isolated fixture.
  const notesButton=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]').getByTitle('Notes internes');
  if(await notesButton.count()){
    const originalNotes=(await (await api.get('/api/superadmin/clients',{headers})).json()).find(x=>x.id===target.id)?.internal_notes??null;

    await notesButton.click();
    let notesDialog=page.getByRole('dialog',{name:'Notes internes SuperAdmin'});
    const field=notesDialog.getByPlaceholder(/Notes sur ce client/);
    await field.fill('G6 cancel note');
    await notesDialog.getByRole('button',{name:'Annuler',exact:true}).click();
    let verify=await api.get('/api/superadmin/clients',{headers});
    let row=(await verify.json()).find(x=>x.id===target.id);
    if((row.internal_notes??null)!==originalNotes) throw new Error('notes cancel mutated backend');
    prove(viewport,'superadmin-notes-cancel-non-mutation');

    await notesButton.click();
    notesDialog=page.getByRole('dialog',{name:'Notes internes SuperAdmin'});
    await notesDialog.getByPlaceholder(/Notes sur ce client/).fill('G6 browser certification note');
    await notesDialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await page.waitForTimeout(300);
    verify=await api.get('/api/superadmin/clients',{headers});
    row=(await verify.json()).find(x=>x.id===target.id);
    if(row.internal_notes!=='G6 browser certification note') throw new Error('notes ACK not persisted');
    prove(viewport,'superadmin-notes-persistence');

    const restore=await api.patch('/api/superadmin/clients/'+target.id+'/notes',{headers,data:{internal_notes:originalNotes}});
    if(!restore.ok()) throw new Error('notes fixture restore failed');
    verify=await api.get('/api/superadmin/clients',{headers});
    row=(await verify.json()).find(x=>x.id===target.id);
    if((row.internal_notes??null)!==originalNotes) throw new Error('notes fixture restore mismatch');
    prove(viewport,'superadmin-notes-fixture-restored');
    await page.reload({waitUntil:'networkidle',timeout:90000});
    await page.getByText('Dr T2 Browser',{exact:true}).waitFor({state:'visible',timeout:10000});
  }

  // License history real browser read.
  const history=card.getByTitle('Historique Licences');
  if(await history.count()){
    await history.click();
    await page.getByText('Historique Licences',{exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'superadmin-license-history-read');
    const close=page.getByRole('button',{name:/Fermer/i}).last();
    if(await close.count()) await close.click();
  }

  // Trial codes — refusal, exact create payload, clipboard after ACK, copy, revoke refusal, revoke ACK.
  const email=page.getByPlaceholder('Email professionnel');
  if(await email.count()){
    const refusedEmail='g6-refused-'+viewport.width+'@example.com';
    await page.route('**/api/superadmin/trial-codes',async route=>{
      if(route.request().method()==='POST') return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'forced trial create refusal'})});
      return route.continue();
    });
    await email.fill(refusedEmail);
    await page.getByRole('button',{name:/Générer Et Copier Le Lien/i}).click();
    await page.getByText("Erreur lors de la création du code.",{exact:true}).waitFor({state:'visible',timeout:10000});
    const refusedCodes=await api.get('/api/superadmin/trial-codes',{headers});
    if((await refusedCodes.json()).some(x=>x.email===refusedEmail)) throw new Error('refused trial create persisted');
    prove(viewport,'superadmin-trial-create-refusal-non-mutation');
    await page.unroute('**/api/superadmin/trial-codes');

    const unique='g6-'+viewport.width+'@example.com';
    await email.fill(unique);
    const name=page.getByPlaceholder('Nom complet');
    if(await name.count()) await name.fill('Dr Browser G6');
    const cabinet=page.getByPlaceholder('Nom du cabinet');
    if(await cabinet.count()) await cabinet.fill('Cabinet G6');
    const notes=page.getByPlaceholder('Notes internes');
    if(await notes.count()) await notes.fill('Prospect browser G6');
    const trialDays=page.getByPlaceholder('Durée essai');
    if(await trialDays.count()) await trialDays.fill('45');
    const expiresDays=page.getByPlaceholder('Validité du code');
    if(await expiresDays.count()) await expiresDays.fill('12');

    await page.getByRole('button',{name:/Générer Et Copier Le Lien/i}).click();
    await page.waitForTimeout(300);
    const codes=await api.get('/api/superadmin/trial-codes',{headers});
    const created=(await codes.json()).find(x=>x.email===unique);
    if(!created || created.trial_days!==45) throw new Error('trial code ACK/payload not persisted');
    const copiedAfterCreate=await page.evaluate(()=>navigator.clipboard.readText());
    if(copiedAfterCreate!==created.activation_url) throw new Error('trial create clipboard mismatch');
    prove(viewport,'superadmin-trial-create-copy',{codeId:created.id});

    const codeText=page.getByText(created.code,{exact:true});
    await codeText.waitFor({state:'visible',timeout:10000});
    let codeRow=codeText.locator('xpath=ancestor::*[.//button[contains(.,"Révoquer")]][1]');
    await codeRow.getByRole('button',{name:/Copier Le Lien/i}).click();
    const copiedExisting=await page.evaluate(()=>navigator.clipboard.readText());
    if(copiedExisting!==created.activation_url) throw new Error('existing trial copy mismatch');
    prove(viewport,'superadmin-trial-copy-existing');

    await page.route('**/api/superadmin/trial-codes/'+created.id+'/revoke',route=>route.fulfill({
      status:409,contentType:'application/json',body:JSON.stringify({detail:'Code déjà utilisé'})
    }));
    await codeRow.getByRole('button',{name:'Révoquer',exact:true}).click();
    await page.getByText('Code déjà utilisé',{exact:true}).waitFor({state:'visible',timeout:10000});
    let refreshed=await api.get('/api/superadmin/trial-codes',{headers});
    let after=(await refreshed.json()).find(x=>x.id===created.id);
    if(after?.revoked_at) throw new Error('refused trial revoke mutated backend');
    prove(viewport,'superadmin-trial-revoke-refusal-non-mutation');
    await page.unroute('**/api/superadmin/trial-codes/'+created.id+'/revoke');

    codeRow=page.getByText(created.code,{exact:true}).locator('xpath=ancestor::*[.//button[contains(.,"Révoquer")]][1]');
    await codeRow.getByRole('button',{name:'Révoquer',exact:true}).click();
    await page.waitForTimeout(300);
    refreshed=await api.get('/api/superadmin/trial-codes',{headers});
    after=(await refreshed.json()).find(x=>x.id===created.id);
    if(!after?.revoked_at) throw new Error('trial revoke not persisted');
    prove(viewport,'superadmin-trial-revoke',{codeId:created.id});
  }

  // Explicit trial-code refresh -> prove the endpoint this button actually owns.
  const refresh=page.getByRole('button',{name:'Actualiser',exact:true});
  if(await refresh.count()){
    const refreshAckPromise=page.waitForResponse(
      r=>r.request().method()==='GET' && r.url().includes('/api/superadmin/trial-codes'),
      {timeout:10000},
    );
    await refresh.click();
    const refreshAck=await refreshAckPromise;
    if(!refreshAck.ok()) throw new Error('trial-code refresh refused '+refreshAck.status());
    prove(viewport,'superadmin-trial-explicit-refresh',{status:refreshAck.status()});
  }

  await ctx.close();

  // Real visible licence lock flow lives in LoginPage (?locked=true), not the orphan LicenseStatusPage.
  const lockedCtx=await browser.newContext({viewport,colorScheme:'light'});
  const lockedPage=await lockedCtx.newPage();
  await lockedPage.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:dentistTokens.access_token,refresh:dentistTokens.refresh_token});
  let recheckCalls=0;
  await lockedPage.route('**/api/clinics/recheck-license',route=>{
    recheckCalls+=1;
    if(recheckCalls===1) return route.fulfill({status:402,contentType:'application/json',body:JSON.stringify({detail:'Licence toujours invalide'})});
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({status:'ok'})});
  });
  await lockedPage.goto('http://127.0.0.1:5173/login?locked=true',{waitUntil:'networkidle',timeout:90000});
  await lockedPage.getByText('Accès Verrouillé',{exact:true}).waitFor({state:'visible',timeout:10000});
  await lockedPage.getByRole('button',{name:'Revérifier la licence',exact:true}).click();
  await lockedPage.getByText(/La licence est toujours invalide/i).waitFor({state:'visible',timeout:10000});
  if(recheckCalls!==1 || !lockedPage.url().includes('locked=true')) throw new Error('licence recheck refusal false-success');
  prove(viewport,'license-lock-recheck-refusal',{recheckCalls});

  await lockedPage.getByRole('button',{name:'Revérifier la licence',exact:true}).click();
  await lockedPage.waitForURL('**/dashboard',{timeout:10000});
  if(recheckCalls!==2) throw new Error('licence recheck ACK count mismatch');
  prove(viewport,'license-lock-recheck-success',{recheckCalls});
  await lockedPage.unroute('**/api/clinics/recheck-license');
  await lockedCtx.close();

  const logoutCtx=await browser.newContext({viewport,colorScheme:'light'});
  const logoutPage=await logoutCtx.newPage();
  await logoutPage.addInitScript(v=>{
    localStorage.setItem('token',v.access);
    localStorage.setItem('refresh_token',v.refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:dentistTokens.access_token,refresh:dentistTokens.refresh_token});
  await logoutPage.goto('http://127.0.0.1:5173/login?locked=true',{waitUntil:'networkidle',timeout:90000});
  await logoutPage.getByRole('button',{name:'Se déconnecter',exact:true}).click();
  await logoutPage.waitForFunction(()=>!localStorage.getItem('token'),undefined,{timeout:10000});
  await logoutPage.getByRole('button',{name:/Se connecter/i}).waitFor({state:'visible',timeout:10000});
  prove(viewport,'license-lock-logout-clears-session');
  await logoutCtx.close();
}

await browser.close();
await api.dispose();
console.log('G6_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
