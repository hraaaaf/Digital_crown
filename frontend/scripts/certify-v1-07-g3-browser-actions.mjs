import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G3 login failed');
const tokens=await login.json();
const headers={Authorization:'Bearer '+tokens.access_token};

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
  let pendingRequests=[
    {
      id:7001,
      patient_name:'Pending Browser',
      phone:'0600000000',
      motif:'Contrôle',
      datetime_start:'2030-01-15T10:00:00',
      duration_minutes:30,
      status:'EN_ATTENTE_DEMANDE',
      source:'browser-cert',
      expires_at:'2030-01-15T12:00:00'
    },
    {
      id:7002,
      patient_name:'Pending Confirm',
      phone:'0600000001',
      motif:'Consultation',
      datetime_start:'2030-01-15T11:00:00',
      duration_minutes:30,
      status:'EN_ATTENTE_DEMANDE',
      source:'browser-cert',
      expires_at:'2030-01-15T13:00:00'
    },
    {
      id:7003,
      patient_name:'Pending Reject',
      phone:'0600000002',
      motif:'Contrôle',
      datetime_start:'2030-01-15T12:00:00',
      duration_minutes:30,
      status:'EN_ATTENTE_DEMANDE',
      source:'browser-cert',
      expires_at:'2030-01-15T14:00:00'
    }
  ];
  let requestConfirmCalls=0,confirmPendingCalls=0,rejectPendingCalls=0;
  await page.route('**/api/appointments/pending',route=>route.fulfill({
    status:200,
    contentType:'application/json',
    body:JSON.stringify(pendingRequests)
  }));
  await page.route('**/api/appointments/7001/request-confirmation',route=>{
    requestConfirmCalls+=1;
    pendingRequests=pendingRequests.map(r=>r.id===7001?{...r,status:'EN_ATTENTE_CONFIRM'}:r);
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({message:'confirmation requested'})});
  });
  await page.route('**/api/appointments/7002/confirm',route=>{
    confirmPendingCalls+=1;
    pendingRequests=pendingRequests.filter(r=>r.id!==7002);
    return route.fulfill({status:200,contentType:'application/json',body:'{}'});
  });
  await page.route('**/api/appointments/7003/reject',route=>{
    rejectPendingCalls+=1;
    pendingRequests=pendingRequests.filter(r=>r.id!==7003);
    return route.fulfill({status:200,contentType:'application/json',body:'{}'});
  });
  await page.goto('http://127.0.0.1:5173/agenda',{waitUntil:'networkidle',timeout:90000});

  // Core view switching -> prove the actual consumer view, not only the click.
  const viewCases=[
    {label:/Jour$/i,testId:'agenda-day-view',name:'day'},
    {label:/Semaine$/i,testId:'agenda-week-view',name:'week'},
    {label:/Mois$/i,testId:'agenda-month-view',name:'month'},
  ];
  for(const item of viewCases){
    const b=page.getByRole('button',{name:item.label}).first();
    await b.click();
    await page.getByTestId(item.testId).waitFor({state:'visible',timeout:10000});
    prove(viewport,'agenda-view-'+item.name);
  }
  const multi=page.getByRole('button',{name:/Multi$/i}).first();
  await multi.click();
  await page.getByText('Vue multi-praticien',{exact:true}).waitFor({state:'visible',timeout:10000});
  prove(viewport,'agenda-view-multi');

  // Return to week for the mutation scenarios below.
  await page.getByRole('button',{name:/Semaine$/i}).first().click();
  await page.getByTestId('agenda-week-view').waitFor({state:'visible',timeout:10000});

  // Frontdesk modal: refusal preserves form; ACK closes and the new pending request appears after refetch.
  const frontdesk=page.getByTitle('Nouvelle demande de rendez-vous');
  if(await frontdesk.count()){
    await page.route('**/api/frontdesk/appointment-request',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Créneau indisponible"}'}));
    await frontdesk.click();
    let frontdeskDialog=page.getByRole('dialog',{name:'Nouvelle demande de RDV'});
    await frontdeskDialog.waitFor({state:'visible',timeout:5000});
    await frontdeskDialog.getByPlaceholder('Prénom').fill('Sara');
    await frontdeskDialog.getByPlaceholder('Nom',{exact:true}).fill('BENALI');
    await frontdeskDialog.getByPlaceholder('Motif de la visite').fill('Contrôle');
    await frontdeskDialog.getByRole('button',{name:/Créer demande/i}).click();
    await frontdeskDialog.getByText('Créneau indisponible',{exact:true}).waitFor({state:'visible',timeout:5000});
    if(!(await frontdeskDialog.isVisible())) throw new Error('frontdesk closed after refusal');
    prove(viewport,'frontdesk-refusal-no-false-success');
    await frontdeskDialog.getByRole('button',{name:'Annuler',exact:true}).click();
    await page.unroute('**/api/frontdesk/appointment-request');

    let frontdeskCreateCalls=0;
    await page.route('**/api/frontdesk/appointment-request',async route=>{
      frontdeskCreateCalls+=1;
      const body=route.request().postDataJSON();
      if(body.first_name!=='Nora' || body.last_name!=='FRONTDESK') throw new Error('frontdesk success payload mismatch');
      const created={
        id:7099,
        patient_name:'FRONTDESK Nora',
        phone:body.phone||null,
        motif:body.appointment_reason||null,
        datetime_start:body.requested_start,
        duration_minutes:body.duration_minutes,
        status:'EN_ATTENTE_DEMANDE',
        source:'frontdesk',
        expires_at:'2030-01-15T15:00:00'
      };
      pendingRequests=[...pendingRequests,created];
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(created)});
    });
    await frontdesk.click();
    frontdeskDialog=page.getByRole('dialog',{name:'Nouvelle demande de RDV'});
    await frontdeskDialog.getByPlaceholder('Prénom').fill('Nora');
    await frontdeskDialog.getByPlaceholder('Nom',{exact:true}).fill('FRONTDESK');
    await frontdeskDialog.getByPlaceholder('Téléphone (optionnel)').fill('0611223344');
    await frontdeskDialog.getByPlaceholder('Motif de la visite').fill('Contrôle succès');
    await frontdeskDialog.getByRole('button',{name:/Créer demande/i}).click();
    await frontdeskDialog.waitFor({state:'detached',timeout:10000});
    await page.getByText('FRONTDESK Nora',{exact:true}).waitFor({state:'visible',timeout:10000});
    if(frontdeskCreateCalls!==1 || !pendingRequests.some(r=>r.id===7099)) throw new Error('frontdesk success ACK/refetch mismatch');
    prove(viewport,'frontdesk-success-ack-visible',{frontdeskCreateCalls});
    await page.unroute('**/api/frontdesk/appointment-request');
  }

  // Appointment create: force refusal and assert dialog remains.
  const addCandidates=[
    page.getByRole('button',{name:/Nouveau rendez-vous/i}),
    page.getByRole('button',{name:/Ajouter.*rendez-vous/i}),
    page.getByRole('button',{name:/Nouveau RDV/i}),
  ];
  let opened=false;
  for(const locator of addCandidates){
    if(await locator.count()){
      await locator.first().click();
      opened=true;
      break;
    }
  }
  if(opened){
    const act=page.getByPlaceholder("Saisir l'acte ou rechercher dans le catalogue...");
    if(await act.count()){
      await page.route('**/api/appointments/**',async route=>{
        if(route.request().method()==='POST') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Créneau refusé"}'});
        return route.continue();
      });
      await act.fill('Détartrage');
      const confirm=page.getByRole('button',{name:'Confirmer le RDV',exact:true});
      if(await confirm.count()){
        await confirm.click();
        await page.waitForTimeout(400);
        const dialog=page.getByRole('dialog',{name:'Nouveau Rendez-vous'});
        if(!(await dialog.count())) throw new Error('appointment modal closed after refused create');
        prove(viewport,'agenda-create-refusal-preserves-dialog');
        const cancel=dialog.getByRole('button',{name:'Annuler',exact:true});
        if(await cancel.count()) await cancel.click();
      }
      await page.unroute('**/api/appointments/**');
    }
  }

  // Appointment create -> real backend ACK -> visible view -> edit ACK -> delete ACK.
  const uniquePatient='G3 Browser '+viewport.width;
  const uniqueMotif='Contrôle G3 '+viewport.width;
  const updatedMotif='Contrôle G3 modifié '+viewport.width;

  await page.route('**/api/appointments/check-conflicts*',route=>route.fulfill({
    status:200,contentType:'application/json',body:'[]'
  }));

  const successAddCandidates=[
    page.getByRole('button',{name:/Nouveau rendez-vous/i}),
    page.getByRole('button',{name:/Ajouter.*rendez-vous/i}),
    page.getByRole('button',{name:/Nouveau RDV/i}),
    page.getByRole('button',{name:/Nouveau RV/i}),
  ];
  let successOpened=false;
  for(const locator of successAddCandidates){
    if(await locator.count()){
      await locator.first().click();
      successOpened=true;
      break;
    }
  }
  if(!successOpened) throw new Error('no appointment create control for success path');

  const successDialog=page.getByRole('dialog',{name:'Nouveau Rendez-vous'});
  await successDialog.waitFor({state:'visible',timeout:5000});
  const patientField=successDialog.getByPlaceholder('Rechercher ou saisir un nom...');
  await patientField.fill(uniquePatient);
  const actField=successDialog.getByPlaceholder("Saisir l'acte ou rechercher dans le catalogue...");
  await actField.fill(uniqueMotif);

  const createAckPromise=page.waitForResponse(
    r=>r.request().method()==='POST' && /\/api\/appointments\/?(?:\?|$)/.test(r.url()),
    {timeout:10000},
  );
  await successDialog.getByRole('button',{name:'Confirmer le RDV',exact:true}).click();
  const createAck=await createAckPromise;
  if(!createAck.ok()) throw new Error('appointment create ACK failed '+createAck.status()+': '+await createAck.text());
  await successDialog.waitFor({state:'hidden',timeout:10000});

  let persisted=(await (await api.get('/api/appointments/',{headers})).json()).find(x=>x.patient_name===uniquePatient);
  if(!persisted) throw new Error('created appointment not persisted in backend');
  prove(viewport,'agenda-create-success-persistence',{appointmentId:persisted.id});

  const createdItem=page.locator('.appointment-item').filter({hasText:uniquePatient}).first();
  await createdItem.waitFor({state:'visible',timeout:10000});
  await createdItem.click();
  const persistedEditDialog=page.getByRole('dialog',{name:'Modifier le Rendez-vous'});
  await persistedEditDialog.waitFor({state:'visible',timeout:5000});

  const editAct=persistedEditDialog.getByPlaceholder("Saisir l'acte ou rechercher dans le catalogue...");
  await editAct.fill(updatedMotif);
  const editAckPromise=page.waitForResponse(
    r=>r.request().method()==='PUT' && r.url().includes('/api/appointments/'+persisted.id),
    {timeout:10000},
  );
  await persistedEditDialog.getByRole('button',{name:'Modifier le RDV',exact:true}).click();
  const editAck=await editAckPromise;
  if(!editAck.ok()) throw new Error('appointment edit ACK failed '+editAck.status()+': '+await editAck.text());
  await persistedEditDialog.waitFor({state:'hidden',timeout:10000});

  persisted=(await (await api.get('/api/appointments/',{headers})).json()).find(x=>x.id===persisted.id);
  if(!persisted || persisted.motif!==updatedMotif) throw new Error('edited appointment not persisted');
  prove(viewport,'agenda-edit-success-persistence',{appointmentId:persisted.id});

  const updatedItem=page.locator('.appointment-item').filter({hasText:uniquePatient}).first();
  await updatedItem.waitFor({state:'visible',timeout:10000});
  await updatedItem.click();
  const deleteSuccessDialog=page.getByRole('dialog',{name:'Modifier le Rendez-vous'});
  await deleteSuccessDialog.waitFor({state:'visible',timeout:5000});
  page.once('dialog',async d=>d.accept());
  const deleteAckPromise=page.waitForResponse(
    r=>r.request().method()==='DELETE' && r.url().includes('/api/appointments/'+persisted.id),
    {timeout:10000},
  );
  await deleteSuccessDialog.getByRole('button',{name:'Supprimer',exact:true}).click();
  const deleteAck=await deleteAckPromise;
  if(!deleteAck.ok()) throw new Error('appointment delete ACK failed '+deleteAck.status()+': '+await deleteAck.text());
  await deleteSuccessDialog.waitFor({state:'hidden',timeout:10000});
  if(await page.locator('.appointment-item').filter({hasText:uniquePatient}).count()) throw new Error('deleted appointment remained visible');
  const afterDelete=await (await api.get('/api/appointments/',{headers})).json();
  if(afterDelete.some(x=>x.id===persisted.id)) throw new Error('deleted appointment remained persisted');
  prove(viewport,'agenda-delete-success-persistence',{appointmentId:persisted.id});

  await page.unroute('**/api/appointments/check-conflicts*');

  // Existing appointment edit/delete: exercise visible controls with refusal + non-mutation.
  const existing=page.locator('.appointment-item').first();
  if(await existing.count()){
    const label=(await existing.innerText()).trim();
    await existing.click();
    const editDialog=page.getByRole('dialog',{name:'Modifier le Rendez-vous'});
    await editDialog.waitFor({state:'visible',timeout:5000});

    await page.route(/\/api\/appointments\/\d+$/,async route=>{
      if(route.request().method()==='PUT') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Modification refusée"}'});
      if(route.request().method()==='DELETE') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Suppression refusée"}'});
      return route.continue();
    });

    await editDialog.getByRole('button',{name:'Modifier le RDV',exact:true}).click();
    await page.getByText('Modification refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
    if(!(await editDialog.count())) throw new Error('appointment edit dialog closed after refused PUT');
    prove(viewport,'agenda-edit-refusal-preserves-dialog',{label});

    page.once('dialog',async d=>d.accept());
    await editDialog.getByRole('button',{name:'Supprimer',exact:true}).click();
    await page.waitForTimeout(350);
    if(!(await editDialog.count())) throw new Error('appointment edit dialog closed after refused DELETE');
    if(!(await page.locator('.appointment-item').first().count())) throw new Error('appointment disappeared after refused DELETE');
    prove(viewport,'agenda-delete-refusal-non-mutation',{label});

    await page.unroute(/\/api\/appointments\/\d+$/);
    const cancelEdit=editDialog.getByRole('button',{name:'Annuler',exact:true});
    if(await cancelEdit.count()) await cancelEdit.click();
  }

  // Pending actions: ACK then refetched UI consequence.
  const requestCard=page.locator('div.border-2').filter({hasText:'Pending Browser'}).first();
  await requestCard.getByRole('button',{name:'Demander confirmation',exact:true}).click();
  await page.getByText(/Message template copié/i).waitFor({state:'visible',timeout:10000});
  if(requestConfirmCalls!==1 || pendingRequests.find(r=>r.id===7001)?.status!=='EN_ATTENTE_CONFIRM') throw new Error('pending request-confirmation mismatch');
  prove(viewport,'agenda-pending-request-confirmation',{requestConfirmCalls});

  const confirmCard=page.locator('div.border-2').filter({hasText:'Pending Confirm'}).first();
  await confirmCard.getByRole('button',{name:'Confirmer',exact:true}).click();
  await page.getByText('Pending Confirm',{exact:true}).waitFor({state:'detached',timeout:10000});
  if(confirmPendingCalls!==1 || pendingRequests.some(r=>r.id===7002)) throw new Error('pending confirm mismatch');
  prove(viewport,'agenda-pending-confirm',{confirmPendingCalls});

  const rejectCard=page.locator('div.border-2').filter({hasText:'Pending Reject'}).first();
  page.once('dialog',d=>d.accept());
  await rejectCard.getByRole('button',{name:'Refuser',exact:true}).click();
  await page.getByText('Pending Reject',{exact:true}).waitFor({state:'detached',timeout:10000});
  if(rejectPendingCalls!==1 || pendingRequests.some(r=>r.id===7003)) throw new Error('pending reject mismatch');
  prove(viewport,'agenda-pending-reject',{rejectPendingCalls});
  // Pending-only toggle -> prove active agenda visibility actually changes.
  const pendingOnly=page.getByRole('button',{name:'Afficher seulement',exact:true});
  await pendingOnly.waitFor({state:'visible',timeout:5000});
  await page.getByText('Pending Browser',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByTestId('agenda-active-view').waitFor({state:'visible',timeout:5000});
  await pendingOnly.click();
  await page.getByRole('button',{name:'Afficher tout',exact:true}).waitFor({state:'visible',timeout:5000});
  if(await page.getByTestId('agenda-active-view').count()) throw new Error('pending-only did not hide active agenda view');
  await page.getByText('Pending Browser',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'agenda-pending-filter-hides-active-view');

  await page.getByRole('button',{name:'Afficher tout',exact:true}).click();
  await page.getByTestId('agenda-active-view').waitFor({state:'visible',timeout:5000});
  await page.getByTestId('agenda-week-view').waitFor({state:'visible',timeout:5000});
  prove(viewport,'agenda-pending-filter-restores-active-view');

  // Google import modal open/close + invalid file non-mutation.
  const importButton=page.getByTitle('Importer depuis Google Agenda');
  if(await importButton.count()){
    await importButton.click();
    const file=page.locator('input[type="file"]').last();
    if(await file.count()){
      await file.setInputFiles({name:'empty.ics',mimeType:'text/calendar',buffer:Buffer.from('invalid')});
      await page.getByText('Aucun rendez-vous valide trouvé dans ce fichier.',{exact:true}).waitFor({state:'visible',timeout:5000});
      prove(viewport,'agenda-import-invalid-file-blocked');
    }
    const cancel=page.getByRole('button',{name:'Annuler',exact:true});
    if(await cancel.count()) await cancel.click();
  }

  await page.unroute('**/api/appointments/pending');

  // MOBILE NOTIFICATIONS — real Chromium filter/navigation/refresh + ACK/refusal consequences.
  const notificationFixture=[
    {
      id:8101,
      patient_id:101,
      patient_name:'Sara BENALI',
      type:'OVERDUE_PAYMENT_HIGH',
      title:'Paiement en retard',
      message:'Solde à traiter',
      priority:'HIGH',
      created_at:'2030-01-15T09:00:00Z'
    },
    {
      id:8102,
      patient_id:102,
      patient_name:'Omar ALAMI',
      type:'PATIENT_FOLLOWUP',
      title:'Contrôle patient',
      message:'Suivi courant',
      priority:'LOW',
      created_at:'2030-01-15T09:05:00Z'
    }
  ];
  await page.route('**/api/mobile/notifications',route=>route.fulfill({
    status:200,
    contentType:'application/json',
    body:JSON.stringify({total:notificationFixture.length,alerts:notificationFixture})
  }));
  await page.route('**/api/mobile/notifications/8101/read',route=>route.fulfill({
    status:200,contentType:'application/json',body:'{"ok":true}'
  }));
  await page.route('**/api/mobile/notifications/8102/snooze',route=>route.fulfill({
    status:503,contentType:'application/json',body:'{"detail":"Report refusé"}'
  }));

  await page.goto('http://127.0.0.1:5173/mobile/g3-cert?tab=notifications',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Paiement en retard',{exact:true}).waitFor({state:'visible',timeout:10000});
  await page.getByText('Contrôle patient',{exact:true}).waitFor({state:'visible',timeout:10000});

  await page.getByRole('button',{name:'Prioritaires',exact:true}).click();
  await page.getByText('Paiement en retard',{exact:true}).waitFor({state:'visible',timeout:5000});
  if(await page.getByText('Contrôle patient',{exact:true}).count()) throw new Error('notification priority filter leaked info alert');
  prove(viewport,'mobile-notifications-priority-filter');

  await page.getByRole('button',{name:'Toutes',exact:true}).click();
  await page.getByText('Contrôle patient',{exact:true}).waitFor({state:'visible',timeout:5000});

  const urgentArticle=page.locator('article').filter({hasText:'Paiement en retard'});
  await urgentArticle.getByRole('button',{name:'Voir finance',exact:true}).click();
  await page.getByTestId('g3-mobile-navigation').filter({hasText:'navigate:finance'}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'mobile-notifications-navigation-consequence');

  await urgentArticle.getByRole('button',{name:/Lu$/}).click();
  await page.getByText('Paiement en retard',{exact:true}).waitFor({state:'hidden',timeout:5000});
  prove(viewport,'mobile-notifications-read-ack-removes-alert');

  const infoArticle=page.locator('article').filter({hasText:'Contrôle patient'});
  await infoArticle.getByRole('button',{name:/24 h/}).click();
  await page.getByText('Report refusé',{exact:true}).waitFor({state:'visible',timeout:5000});
  await page.getByText('Contrôle patient',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'mobile-notifications-snooze-refusal-preserves-alert');

  await page.getByRole('button',{name:'Actualiser les notifications',exact:true}).click();
  await page.getByText('Paiement en retard',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'mobile-notifications-refresh-rereads-backend');

  await page.unroute('**/api/mobile/notifications');
  await page.unroute('**/api/mobile/notifications/8101/read');
  await page.unroute('**/api/mobile/notifications/8102/snooze');

  // MOBILE WAITING ROOM — ACK removes patient from waiting; refusal preserves patient + surfaces error.
  await page.route('**/api/mobile/appointments/9101/status',route=>route.fulfill({
    status:200,contentType:'application/json',body:'{"ok":true}'
  }));
  await page.route('**/api/mobile/appointments/9102/status',route=>route.fulfill({
    status:503,contentType:'application/json',body:'{"detail":"Transition refusée"}'
  }));

  await page.goto('http://127.0.0.1:5173/mobile/g3-cert?tab=waiting-room',{waitUntil:'networkidle',timeout:90000});
  await page.getByLabel('2 patients en salle d’attente',{exact:true}).waitFor({state:'visible',timeout:5000});

  const sara=page.locator('[data-mob5i-waiting-patient="9101"]');
  await sara.getByRole('button',{name:/Au fauteuil/i}).click();
  await sara.waitFor({state:'hidden',timeout:5000});
  await page.getByLabel('1 patient en salle d’attente',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'mobile-waiting-room-status-ack-removes-patient');

  const omar=page.locator('[data-mob5i-waiting-patient="9102"]');
  await omar.getByRole('button',{name:/Au fauteuil/i}).click();
  await page.getByRole('alert').filter({hasText:'Transition refusée'}).waitFor({state:'visible',timeout:5000});
  await omar.waitFor({state:'visible',timeout:5000});
  await page.getByLabel('1 patient en salle d’attente',{exact:true}).waitFor({state:'visible',timeout:5000});
  prove(viewport,'mobile-waiting-room-status-refusal-preserves-patient');

  await page.unroute('**/api/mobile/appointments/9101/status');
  await page.unroute('**/api/mobile/appointments/9102/status');

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G3_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
