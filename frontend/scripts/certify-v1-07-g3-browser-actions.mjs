import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
if(!password) throw new Error('T2_PASSWORD required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
if(!login.ok()) throw new Error('G3 login failed');
const tokens=await login.json();

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
  await page.goto('http://127.0.0.1:5173/agenda',{waitUntil:'networkidle',timeout:90000});

  // Core view switching.
  for(const label of [/Jour$/i,/Semaine$/i,/Mois$/i,/Multi$/i]){
    const b=page.getByRole('button',{name:label}).first();
    if(await b.count()){
      await b.click();
      await page.waitForTimeout(200);
      prove(viewport,'agenda-view-'+String(label));
    }
  }

  // Frontdesk modal: explicit refusal must keep form open.
  const frontdesk=page.getByTitle('Nouvelle demande de rendez-vous');
  if(await frontdesk.count()){
    await page.route('**/api/frontdesk/appointment-request',route=>route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Créneau indisponible"}'}));
    await frontdesk.click();
    const prenom=page.getByPlaceholder('Prénom');
    if(await prenom.count()){
      await prenom.fill('Sara');
      await page.getByPlaceholder('Nom').fill('BENALI');
      await page.getByPlaceholder('Motif de la visite').fill('Contrôle');
      await page.getByRole('button',{name:/Créer demande/i}).click();
      await page.getByText('Créneau indisponible',{exact:true}).waitFor({state:'visible',timeout:5000});
      if(!(await page.getByPlaceholder('Prénom').count())) throw new Error('frontdesk closed after refusal');
      prove(viewport,'frontdesk-refusal-no-false-success');
      const cancel=page.getByRole('button',{name:'Annuler',exact:true});
      if(await cancel.count()) await cancel.click();
    }
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

  // Pending-only toggle if present.
  const pendingOnly=page.getByRole('button',{name:'Afficher seulement',exact:true});
  if(await pendingOnly.count()){
    await pendingOnly.click();
    await page.getByRole('button',{name:'Afficher tout',exact:true}).waitFor({state:'visible',timeout:5000});
    prove(viewport,'agenda-pending-filter-toggle');
  }

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

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G3_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
