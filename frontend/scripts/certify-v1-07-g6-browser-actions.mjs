import { chromium, request } from 'playwright';

const password=process.env.T2_PASSWORD;
const superEmail=process.env.T2_SUPERADMIN_EMAIL;
if(!password||!superEmail) throw new Error('T2_PASSWORD and T2_SUPERADMIN_EMAIL required');

const api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
const login=await api.post('/api/auth/login',{form:{username:superEmail,password}});
if(!login.ok()) throw new Error('G6 superadmin login failed');
const tokens=await login.json();
const headers={Authorization:'Bearer '+tokens.access_token};

const me=await api.get('/api/auth/me',{headers});
if(!me.ok()) throw new Error('G6 /me failed');
const meBody=await me.json();
if(meBody.is_superadmin!==true) throw new Error('isolated fixture is not superadmin');

const clientsResp=await api.get('/api/superadmin/clients',{headers});
if(!clientsResp.ok()) throw new Error('G6 clients read failed');
const target=(await clientsResp.json()).find(x=>x.email==='t2-browser@cabinet.ma');
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
  const ctx=await browser.newContext({viewport,colorScheme:'light'});
  const page=await ctx.newPage();
  await seed(page);
  await page.goto('http://127.0.0.1:5173/super-admin',{waitUntil:'networkidle',timeout:90000});
  await page.getByText('Dr T2 Browser',{exact:true}).waitFor({state:'visible',timeout:15000});

  const card=page.getByText('Dr T2 Browser',{exact:true}).locator('xpath=ancestor::*[contains(@class,"group")][1]');
  if(!(await card.count())) throw new Error('target client card missing');

  // Plan mutation with backend verification, then restore GOLD.
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

    const verify=await api.get('/api/superadmin/clients',{headers});
    const row=(await verify.json()).find(x=>x.id===target.id);
    if(row.subscription_plan!==targetPlan) throw new Error('plan ACK not persisted');
    prove(viewport,'superadmin-plan-persistence',{from:original,to:targetPlan});

    const restorePlanAckPromise=page.waitForResponse(
      r=>r.request().method()==='PATCH' && r.url().includes('/api/superadmin/clients/'+target.id+'/plan'),
      {timeout:10000},
    );
    await plan.selectOption(original);
    const restorePlanAck=await restorePlanAckPromise;
    if(!restorePlanAck.ok()) throw new Error('plan restore refused '+restorePlanAck.status()+': '+await restorePlanAck.text());
  }

  // Internal notes persistence.
  const notesButton=card.getByTitle('Notes internes');
  if(await notesButton.count()){
    await notesButton.click();
    const field=page.getByPlaceholder(/Notes sur ce client/);
    await field.fill('G6 browser certification note');
    await page.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await page.waitForTimeout(300);
    const verify=await api.get('/api/superadmin/clients',{headers});
    const row=(await verify.json()).find(x=>x.id===target.id);
    if(row.internal_notes!=='G6 browser certification note') throw new Error('notes ACK not persisted');
    prove(viewport,'superadmin-notes-persistence');
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

  // Trial code create + reload + revoke.
  const email=page.getByPlaceholder('Email professionnel');
  if(await email.count()){
    const unique='g6-'+viewport.width+'@example.com';
    await email.fill(unique);
    const name=page.getByPlaceholder('Nom complet');
    if(await name.count()) await name.fill('Dr Browser G6');
    const cabinet=page.getByPlaceholder('Nom du cabinet');
    if(await cabinet.count()) await cabinet.fill('Cabinet G6');
    await page.getByRole('button',{name:/Générer Et Copier Le Lien/i}).click();
    await page.waitForTimeout(400);

    const codes=await api.get('/api/superadmin/trial-codes',{headers});
    const created=(await codes.json()).find(x=>x.email===unique);
    if(!created) throw new Error('trial code ACK not persisted');
    prove(viewport,'superadmin-trial-create',{codeId:created.id});

    const codeText=page.getByText(created.code,{exact:true});
    await codeText.waitFor({state:'visible',timeout:10000});
    const codeRow=codeText.locator('xpath=ancestor::*[.//button[contains(.,"Révoquer")]][1]');
    const revoke=codeRow.getByRole('button',{name:'Révoquer',exact:true});
    if(await revoke.count()){
      await revoke.click();
      await page.waitForTimeout(350);
      const refreshed=await api.get('/api/superadmin/trial-codes',{headers});
      const after=(await refreshed.json()).find(x=>x.id===created.id);
      if(!after?.revoked_at) throw new Error('trial revoke not persisted');
      prove(viewport,'superadmin-trial-revoke',{codeId:created.id});
    }
  }

  // Explicit refresh -> prove a real clients re-read and stable rendered result.
  const refresh=page.getByRole('button',{name:'Actualiser',exact:true});
  if(await refresh.count()){
    const refreshAckPromise=page.waitForResponse(
      r=>r.request().method()==='GET' && r.url().includes('/api/superadmin/clients'),
      {timeout:10000},
    );
    await refresh.click();
    const refreshAck=await refreshAckPromise;
    if(!refreshAck.ok()) throw new Error('superadmin refresh refused '+refreshAck.status());
    await page.getByText('Dr T2 Browser',{exact:true}).waitFor({state:'visible',timeout:10000});
    prove(viewport,'superadmin-explicit-refresh',{status:refreshAck.status()});
  }

  await ctx.close();
}

await browser.close();
await api.dispose();
console.log('G6_BROWSER_ACTIONS',JSON.stringify({status:'PASS',proofs}));
