import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/g4-clinical-actions');
fs.mkdirSync(outDir, { recursive: true });
const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('clinical login failed');
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patientsResponse = await api.get('/api/patients', { headers });
if (!patientsResponse.ok()) throw new Error('clinical patient list failed');
const patient = (await patientsResponse.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('clinical fixture patient missing');

const masterUrl = `/api/patients/${patient.id}/master-plan`;
const seededPlan = [{ title: 'Étape G4 clinique', assistant: 'general', status: 'pending', date_str: 'À planifier', order_index: 0 }];
const masterSeed = await api.put(masterUrl, { headers, data: seededPlan });
if (!masterSeed.ok()) throw new Error('clinical master-plan seed failed');

const assistants = [
  { name:'Parodontologie', options:['Aucune / Saine','1 à 2 mm','3 à 4 mm','≥ 5 mm'] },
  { name:'Endodontie', options:['Aucune douleur (Découverte fortuite ou radio)','Douleur provoquée courte (froid/sucre)','Douleur spontanée, nocturne, irradiante','Douleur à la pression / mastication'] },
  { name:'Chirurgie orale', options:['Dent de sagesse incluse / semi-incluse','Délabrement carieux irrécupérable / Fracture','Mobilité terminale (Parodontite)','Indication Orthodontique (Désencombrement)'] },
  { name:'Prothèse & esthétique', options:['Lésion coronaire mineure à moyenne (< 2 parois)','Perte coronaire majeure (≥ 2 parois)','Dent dépulpée avec perte modérée','Édentement (Dent manquante)'] },
  { name:'Pédodontie', options:['Denture Temporaire (< 6 ans)','Denture Mixte (6 à 12 ans)','Denture Permanente Jeune (> 12 ans)'] },
  { name:'Orthodontie (ODF)', options:['Encombrement / Chevauchement','Espaces / Diastèmes','Décalage osseux (Classe II, Classe III)','Habitude déformante (Pouce, Déglutition atypique)'] },
  { name:'Occlusodontie & ATM', options:["Limitation d'ouverture buccale / Blocage",'Bruits articulaires (Claquements / Crissements)','Douleurs musculaires (Cervicales, masséters) au réveil'] },
  { name:'Médecine buccale', options:['Ulcération (Aphte, lésion traumatique)','Lésion Blanche (Lichen, Leucoplasie, Candidose)','Lésion Rouge / Vésiculeuse (Herpès, Érythème)','Tuméfaction / Excroissance (Diapneusie, Papillome)'] },
  { name:'Examen clinique complet', options:['Contrôle de routine / Bilan','Urgence / Douleur aiguë'], triage:true },
];

const browser = await chromium.launch({ headless:true });
const evidence=[];

async function seedAuth(page){
  await page.addInitScript(({access,refresh})=>{
    localStorage.setItem('token',access);
    localStorage.setItem('refresh_token',refresh||'');
    localStorage.setItem('appMode','prod');
  },{access:tokens.access_token,refresh:tokens.refresh_token});
}

async function gotoClinical(page){
  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=clinical`,{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Espace Clinique',{exact:true}).waitFor({state:'visible',timeout:30000});
}

async function openAssistant(page,name){
  await page.getByRole('button',{name:'Examens',exact:true}).click();
  const launcher=page.getByRole('button',{name:new RegExp('^'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))}).first();
  await launcher.click();
  await page.getByText(`Examen · ${name}`,{exact:true}).waitFor({state:'visible',timeout:10000});
}

async function wizardRoot(page,name){
  const title=page.getByText(`Examen · ${name}`,{exact:true});
  return title.locator('xpath=ancestor::div[contains(@class,"rounded-3xl")][1]');
}

for(const viewport of [{width:390,height:844},{width:1280,height:900}]){
  const context=await browser.newContext({viewport,colorScheme:'light'});
  const page=await context.newPage();
  await seedAuth(page);
  const pageErrors=[]; const http5xx=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('response',r=>{if(r.status()>=500)http5xx.push({url:r.url(),status:r.status()});});
  const actions=[];

  await gotoClinical(page);

  const practitioner=page.getByLabel('Praticien référent');
  if(await practitioner.count()){
    const opts=await practitioner.locator('option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean));
    if(opts.length && !(await practitioner.isDisabled())) await practitioner.selectOption(opts[0]);
    actions.push('practitioner-reference');
  }

  await page.getByRole('button',{name:'Odontogramme',exact:true}).click();
  await page.getByRole('button',{name:'Enfant',exact:true}).click();
  await page.getByRole('button',{name:'Adulte',exact:true}).click();
  const globalActs=page.getByRole('button',{name:'Actes Globaux',exact:true});
  await globalActs.click();
  await page.getByText('Actes Globaux',{exact:true}).last().waitFor({state:'visible',timeout:5000});
  await page.getByRole('button',{name:'Fermer',exact:true}).click();
  for(const tool of ['Sélection','Carie','Composite','Couronne','Canal','Absente','Gommer']){
    const toolButton=page.getByRole('button',{name:tool,exact:true});
    await toolButton.waitFor({state:'visible',timeout:10000});
    await toolButton.dispatchEvent('click');
    if(tool!=='Sélection'){
      const tooth=page.getByRole('button',{name:/^Dent 11,/}).first();
      await tooth.waitFor({state:'visible',timeout:10000});
      await tooth.dispatchEvent('click');
    }
  }
  const saveOdonto=page.getByRole('button',{name:'Enregistrer',exact:true}).first();
  if(await saveOdonto.isDisabled()) throw new Error('odontogram save unexpectedly disabled after edits');
  const saveResp=page.waitForResponse(r=>r.url().includes(`/api/patients/${patient.id}/odontogram`)&&['POST','PUT'].includes(r.request().method()),{timeout:15000});
  await saveOdonto.click();
  const odontoResp=await saveResp;
  if(!odontoResp.ok()) throw new Error(`odontogram save failed: ${odontoResp.status()}`);
  actions.push('odontogram-toolbar-save');

  await page.getByText('Étape G4 clinique',{exact:true}).waitFor({state:'visible',timeout:10000});
  await page.getByRole('button',{name:'Fait',exact:true}).click();
  await page.getByRole('button',{name:'Reporté',exact:true}).click();
  await page.getByRole('button',{name:'À faire',exact:true}).click();
  actions.push('master-plan-status');

  for(const assistant of assistants){
    await openAssistant(page,assistant.name);
    let root=await wizardRoot(page,assistant.name);
    await root.getByRole('button',{name:'Annuler',exact:true}).click();
    await page.getByText(`Examen · ${assistant.name}`,{exact:true}).waitFor({state:'detached',timeout:5000});
    actions.push(`assistant-cancel:${assistant.name}`);

    for(const option of assistant.options){
      await openAssistant(page,assistant.name);
      root=await wizardRoot(page,assistant.name);
      const optionButton=root.getByRole('button',{name:new RegExp(option.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))}).first();
      await optionButton.click();
      await page.waitForTimeout(250);
      const back=root.getByRole('button',{name:/Retour/i}).first();
      const triage=root.getByRole('button',{name:/Triage/i}).first();
      if(await back.isVisible().catch(()=>false)) await back.click();
      else if(await triage.isVisible().catch(()=>false)) await triage.click();
      else {
        await gotoClinical(page);
        await page.getByRole('button',{name:'Examens',exact:true}).click();
      }
      if(await page.getByText(`Examen · ${assistant.name}`,{exact:true}).isVisible().catch(()=>false)){
        await (await wizardRoot(page,assistant.name)).getByRole('button',{name:'Annuler',exact:true}).click();
      }
      actions.push(`assistant-option:${assistant.name}:${option}`);
    }

    await openAssistant(page,assistant.name);
    root=await wizardRoot(page,assistant.name);
    for(let step=0;step<12;step++){
      if(!(await page.getByText(`Examen · ${assistant.name}`,{exact:true}).isVisible().catch(()=>false))) break;
      root=await wizardRoot(page,assistant.name);
      const buttons=root.getByRole('button');
      const count=await buttons.count();
      let clicked=false;
      for(let i=0;i<count;i++){
        const b=buttons.nth(i);
        if(!(await b.isVisible().catch(()=>false))||await b.isDisabled().catch(()=>true)) continue;
        const label=(await b.innerText()).trim();
        if(/Annuler|Retour|Triage/i.test(label)) continue;
        await b.click();
        clicked=true;
        await page.waitForTimeout(450);
        break;
      }
      if(!clicked) break;
    }
    const proposal=page.getByText(new RegExp(`Proposition à valider · ${assistant.name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}`));
    await proposal.waitFor({state:'visible',timeout:10000});
    actions.push(`assistant-complete:${assistant.name}`);

    const useDraft=page.getByRole('button',{name:'Utiliser comme brouillon',exact:true});
    await useDraft.click();
    const conclusion=page.getByPlaceholder('Saisir la conclusion que vous retenez après examen…');
    if(!(await conclusion.inputValue()).trim()) throw new Error(`proposal draft empty: ${assistant.name}`);
    const saveConclusion=page.getByRole('button',{name:'Enregistrer la conclusion',exact:true});
    const response=page.waitForResponse(r=>r.url().includes(`/api/patients/${patient.id}/clinical-conclusions`)&&r.request().method()==='POST',{timeout:15000});
    await saveConclusion.click();
    if(!(await response).ok()) throw new Error(`conclusion save failed: ${assistant.name}`);
    const clearProposal=page.getByRole('button',{name:'Supprimer la proposition'});
    if(await clearProposal.count()) await clearProposal.click();
    actions.push(`assistant-conclusion:${assistant.name}`);
  }

  await page.getByRole('button',{name:'Recharger les conclusions'}).click();
  await page.waitForTimeout(250);
  actions.push('conclusions-reload');

  const deleteStep=page.getByRole('button',{name:'Supprimer l’étape'}).first();
  if(!(await deleteStep.count())) throw new Error('master-plan delete control missing');
  await deleteStep.click();
  actions.push('master-plan-delete');

  const resetPlan=page.getByRole('button',{name:'Réinitialiser',exact:true});
  if(await resetPlan.count() && !(await resetPlan.isDisabled())){
    page.once('dialog',d=>d.accept());
    await resetPlan.click();
    actions.push('master-plan-reset');
  }

  const expectedAssistantCount=assistants.length;
  const expectedOptionCount=assistants.reduce((sum,item)=>sum+item.options.length,0);
  const countPrefix=prefix=>actions.filter(action=>action.startsWith(prefix)).length;
  if(countPrefix('assistant-cancel:')!==expectedAssistantCount) throw new Error('assistant cancel coverage incomplete');
  if(countPrefix('assistant-option:')!==expectedOptionCount) throw new Error('assistant option coverage incomplete');
  if(countPrefix('assistant-complete:')!==expectedAssistantCount) throw new Error('assistant completion coverage incomplete');
  if(countPrefix('assistant-conclusion:')!==expectedAssistantCount) throw new Error('assistant conclusion coverage incomplete');

  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
  const shot=`g4-clinical-${viewport.width}x${viewport.height}-final.png`;
  await page.screenshot({path:path.join(outDir,shot),fullPage:false,animations:'disabled'});
  if(overflow) throw new Error('clinical horizontal overflow');
  if(pageErrors.length) throw new Error('clinical page errors: '+pageErrors.join(' | '));
  if(http5xx.length) throw new Error('clinical HTTP5xx: '+JSON.stringify(http5xx));
  evidence.push({viewport,actions,shot,pageErrors,http5xx});
  await context.close();
}

await browser.close();
await api.dispose();
const summary={status:'PASS',evidence};
fs.writeFileSync(path.join(outDir,'summary.json'),JSON.stringify(summary,null,2));
console.log('G4_CLINICAL_ACTIONS '+JSON.stringify({status:summary.status,viewports:evidence.length}));
