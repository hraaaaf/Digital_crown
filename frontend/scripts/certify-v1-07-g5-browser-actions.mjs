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

  // Profile: stage a real change, then persist explicitly on isolated runtime.
  const profileTab=page.getByRole('button',{name:'Profil Cabinet',exact:true});
  if(await profileTab.count()){
    await profileTab.click();
    const cabinet=page.getByPlaceholder('Ex: Cabinet Dentaire Benmoussa');
    if(await cabinet.count()){
      const original=await cabinet.inputValue();
      await cabinet.fill('Cabinet T2 Certification Browser');
      await cabinet.blur();
      const save=page.getByRole('button',{name:/Mettre à jour le profil|Enregistrer la configuration/i}).first();
      if(await save.count()){
        await save.click();
        await page.waitForTimeout(400);
        const check=await api.get('/api/clinics/me',{headers:{Authorization:'Bearer '+tokens.access_token}});
        if(!check.ok()) throw new Error('profile persistence verification failed');
        const body=await check.json();
        const saved=body.nom_cabinet||body.name||'';
        if(saved!=='Cabinet T2 Certification Browser') throw new Error('profile ACK did not persist cabinet name');
        prove(viewport,'settings-profile-save-persistence');
      }
      // restore isolated fixture if the same control is still reachable.
      if(await cabinet.count()){
        await cabinet.fill(original||'Cabinet T2 Certification');
        await cabinet.blur();
        const saveAgain=page.getByRole('button',{name:/Mettre à jour le profil|Enregistrer la configuration/i}).first();
        if(await saveAgain.count()) await saveAgain.click();
      }
    }
  }

  // Branding: preview scope/local runtime preference must not require backend persistence.
  const branding=page.getByRole('button',{name:'Design & Ambiance',exact:true});
  if(await branding.count()){
    await branding.click();
    const doc=page.getByRole('button',{name:'Document',exact:true});
    if(await doc.count()){
      await doc.click();
      const scope=await page.evaluate(()=>localStorage.getItem('branding_preview_scope'));
      if(scope!=='doc') throw new Error('branding preview scope not persisted locally');
      prove(viewport,'settings-branding-preview-local');
    }
    const animated=page.getByRole('button',{name:'Arrière-plan animé',exact:true});
    if(await animated.count()){
      const before=await animated.getAttribute('aria-pressed');
      await animated.click();
      const after=await animated.getAttribute('aria-pressed');
      if(before===after) throw new Error('animated background toggle did not change');
      prove(viewport,'settings-branding-runtime-toggle');
    }
  }

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

  // Catalog: invalid tariff must be blocked before mutation.
  const catalog=page.getByRole('button',{name:'Catalogue Actes',exact:true});
  if(await catalog.count()){
    await catalog.click();
    const addAct=page.getByRole('button',{name:/Ajouter un acte/i}).first();
    if(await addAct.count()){
      await addAct.click();
      const name=page.getByPlaceholder('Ex. Détartrage');
      const price=page.getByPlaceholder('0');
      if(await name.count() && await price.count()){
        await name.fill('G5 Browser Invalid');
        await price.fill('-20');
        await page.getByRole('button',{name:'Créer',exact:true}).click();
        await page.getByText(/tarif doit être un nombre positif ou nul/i).waitFor({state:'visible',timeout:5000});
        prove(viewport,'settings-catalog-invalid-price-refusal');
        const cancel=page.getByRole('button',{name:'Annuler',exact:true}).last();
        if(await cancel.count()) await cancel.click();
      }
    }
  }

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

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G5_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
