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

  // Agenda: prove refusal leaves dirty state visible.
  const agenda=page.getByRole('button',{name:'Horaires & Agenda',exact:true});
  if(await agenda.count()){
    await agenda.click();
    await page.route('**/api/agenda/settings',async route=>{
      if(route.request().method()==='PUT') return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"forced schedule refusal"}'});
      return route.continue();
    });
    const monday=page.getByLabel('Lundi ouvert');
    if(await monday.count()){
      await monday.click();
      const save=page.getByRole('button',{name:'Enregistrer les horaires',exact:true});
      await save.click();
      await page.getByText(/Impossible d'enregistrer ces horaires/i).waitFor({state:'visible',timeout:5000});
      await page.getByText('Modifications non enregistrées',{exact:true}).waitFor({state:'visible',timeout:5000});
      prove(viewport,'settings-agenda-refusal-preserves-dirty');
    }
    await page.unroute('**/api/agenda/settings');
  }

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

  // Security/restore: force preflight refusal and ensure prepare/apply never appear.
  const security=page.getByRole('button',{name:'Sécurité & Backup',exact:true});
  if(await security.count()){
    await security.click();
    await page.route('**/api/admin/restore/preflight',route=>route.fulfill({status:400,contentType:'application/json',body:'{"detail":"Backup corrompu"}'}));
    const file=page.locator('input[type="file"]').first();
    if(await file.count()){
      await file.setInputFiles({name:'bad.enc',mimeType:'application/octet-stream',buffer:Buffer.from('bad')});
      await page.getByRole('main').getByText('Backup corrompu',{exact:true}).waitFor({state:'visible',timeout:5000});
      if(await page.getByRole('button',{name:/Préparer la restauration/i}).count()) throw new Error('prepare exposed after refused preflight');
      if(await page.getByRole('button',{name:/Redémarrer et restaurer/i}).count()) throw new Error('apply exposed after refused preflight');
      prove(viewport,'settings-restore-preflight-refusal');
    }
    await page.unroute('**/api/admin/restore/preflight');
  }

  // Team: certify that the surface is reachable and dynamic controls join denominator.
  const team=page.getByRole('button',{name:'Mon Équipe',exact:true});
  if(await team.count()){
    await team.click();
    await page.waitForTimeout(300);
    const dynamicControls=await page.locator('button:visible,input:visible,select:visible').count();
    if(dynamicControls===0) throw new Error('Team surface exposes zero controls');
    prove(viewport,'settings-team-surface-dynamic-controls',{dynamicControls});
  }

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G5_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
