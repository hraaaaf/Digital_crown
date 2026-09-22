import { chromium } from 'playwright';
import fs from 'node:fs/promises';

const phase = process.env.TRUTH_SAFETY_PHASE || 'after';
const baseUrl = process.env.TRUTH_SAFETY_URL || 'http://127.0.0.1:5176/truth-safety-audit.html';
const out = process.env.TRUTH_SAFETY_DIR || '../artifacts/v1-07-truth-safety-after';
const scenarios = [
  'license-expired',
  'landing-geography',
  'stock-read-error',
  'stock-delete-confirm',
  'stock-quantity-refusal',
  'stock-add-refusal',
  'stock-delete-refusal',
];
const viewports = [[390,844],[768,1024],[1440,1000]];

await fs.mkdir(out,{recursive:true});
const browser = await chromium.launch();
const evidence=[];

try {
  for (const scenario of scenarios) {
    for (const [width,height] of viewports) {
      const context = await browser.newContext({viewport:{width,height}});
      const page = await context.newPage();
      const runtimeErrors=[];
      const deletes=[];
      page.on('pageerror',e=>runtimeErrors.push(`pageerror: ${e.message}`));
      page.on('console',m=>{ if(m.type()==='error') runtimeErrors.push(`console: ${m.text()}`); });

      await page.route('**/api/**', async route => {
        const req=route.request();
        const url=new URL(req.url());

        if (url.pathname.endsWith('/stock/items') && req.method()==='GET') {
          if (scenario==='stock-read-error') {
            return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"stock unavailable"}'});
          }
          return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{
            id:1,nom:'Gants nitrile',categorie:'CONSOMMABLE',quantite:10,seuil_alerte:5,unite:'boîte',
            prix_unitaire:30,fournisseur:'Atlas Dental',notes:'Taille M',alerte:false
          }])});
        }

        if (url.pathname.endsWith('/stock/alerts') && req.method()==='GET') {
          return route.fulfill({status:200,contentType:'application/json',body:'{"count":0,"items":[]}'});
        }

        if (url.pathname.endsWith('/stock/items/1') && req.method()==='PATCH') {
          if (scenario==='stock-quantity-refusal') {
            return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Quantité refusée"}'});
          }
          return route.fulfill({status:200,contentType:'application/json',body:'{}'});
        }

        if (url.pathname.endsWith('/stock/items') && req.method()==='POST') {
          if (scenario==='stock-add-refusal') {
            return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"Article refusé"}'});
          }
          return route.fulfill({status:201,contentType:'application/json',body:'{"id":2}'});
        }

        if (url.pathname.endsWith('/stock/items/1') && req.method()==='DELETE') {
          deletes.push(url.pathname);
          return route.fulfill({status:503,contentType:'application/json',body:'{"detail":"delete refused"}'});
        }

        return route.fulfill({status:200,contentType:'application/json',body:'{}'});
      });

      await page.goto(`${baseUrl}?scenario=${scenario}`,{waitUntil:'networkidle'});

      if (scenario==='license-expired') {
        await page.getByRole('heading',{name:'Licence Expirée'}).waitFor({state:'visible',timeout:15000});
        const body=await page.locator('body').innerText();
        if (phase==='before' && !body.includes('licence Elite a expiré')) throw new Error('BEFORE licence copy no longer exposes baseline defect');
        if (phase==='after' && (body.includes('licence Elite a expiré') || !body.includes('Votre licence a expiré'))) throw new Error('AFTER licence copy is not plan-neutral');
      }

      if (scenario==='landing-geography') {
        await page.getByText(/dentistes (algériens|marocains)/i).waitFor({state:'visible',timeout:15000});
        const body=await page.locator('body').innerText();
        if (phase==='before' && !body.includes('dentistes algériens')) throw new Error('BEFORE landing geography defect not present');
        if (phase==='after' && (body.includes('dentistes algériens') || !body.includes('dentistes marocains'))) throw new Error('AFTER landing geography is not Morocco-aligned');
      }

      if (scenario==='stock-read-error') {
        if (phase==='before') {
          await page.getByText('Aucun article. Commencez par en ajouter un.').waitFor({state:'visible',timeout:15000});
        } else {
          await page.getByRole('heading',{name:'Stock indisponible'}).waitFor({state:'visible',timeout:15000});
          const body=await page.locator('body').innerText();
          if (body.includes('Aucun article. Commencez par en ajouter un.')) throw new Error('False empty stock still visible after read failure');
        }
      }

      if (scenario==='stock-delete-confirm') {
        await page.getByText('Gants nitrile',{exact:true}).waitFor({state:'visible',timeout:15000});
        await page.getByTitle('Supprimer').click();
        if (phase==='before') {
          await page.waitForTimeout(150);
          if (await page.getByRole('dialog',{name:'Supprimer cet article ?'}).count()) throw new Error('Unexpected delete dialog in BEFORE');
          if (deletes.length!==1) throw new Error(`BEFORE expected immediate DELETE dispatch, got ${deletes.length}`);
        } else {
          await page.getByRole('dialog',{name:'Supprimer cet article ?'}).waitFor({state:'visible',timeout:5000});
          if (deletes.length!==0) throw new Error('AFTER dispatched DELETE before explicit confirmation');
        }
      }

      if (scenario==='stock-quantity-refusal') {
        const row=page.getByText('Gants nitrile',{exact:true}).locator('xpath=ancestor::tr');
        await row.waitFor({state:'visible',timeout:15000});
        await row.locator('button').nth(1).click();
        if (phase==='before') {
          await page.waitForTimeout(150);
          if (await page.getByText('Action stock non enregistrée',{exact:true}).count()) throw new Error('Unexpected quantity refusal UI in BEFORE');
        } else {
          await page.getByText('Action stock non enregistrée',{exact:true}).waitFor({state:'visible',timeout:5000});
          await page.getByText('Quantité refusée',{exact:true}).waitFor({state:'visible',timeout:5000});
        }
      }

      if (scenario==='stock-add-refusal') {
        await page.getByRole('button',{name:/Ajouter un article/i}).click();
        await page.getByPlaceholder('Ex: Gants nitrile S').fill('Masques FFP2');
        await page.getByRole('button',{name:'Ajouter',exact:true}).click();
        if (phase==='before') {
          await page.waitForTimeout(150);
          if (await page.getByText('Article refusé',{exact:true}).count()) throw new Error('Unexpected add refusal UI in BEFORE');
        } else {
          await page.getByText('Article refusé',{exact:true}).waitFor({state:'visible',timeout:5000});
          await page.getByText('Nouvel article',{exact:true}).waitFor({state:'visible',timeout:5000});
        }
      }

      if (scenario==='stock-delete-refusal') {
        await page.getByText('Gants nitrile',{exact:true}).waitFor({state:'visible',timeout:15000});
        await page.getByTitle('Supprimer').click();
        if (phase==='before') {
          await page.waitForTimeout(150);
          if (await page.getByRole('dialog',{name:'Supprimer cet article ?'}).count()) throw new Error('Unexpected refusal dialog in BEFORE');
          if (deletes.length!==1) throw new Error(`BEFORE expected immediate refused DELETE, got ${deletes.length}`);
        } else {
          const dialog=page.getByRole('dialog',{name:'Supprimer cet article ?'});
          await dialog.waitFor({state:'visible',timeout:5000});
          await page.getByRole('button',{name:'Supprimer définitivement'}).click();
          await dialog.getByText('delete refused',{exact:true}).waitFor({state:'visible',timeout:5000});
          await dialog.waitFor({state:'visible',timeout:5000});
          if (deletes.length!==1) throw new Error(`AFTER expected exactly one confirmed DELETE, got ${deletes.length}`);
        }
      }

      const layout=await page.evaluate(()=>({
        clientWidth:document.documentElement.clientWidth,
        scrollWidth:document.documentElement.scrollWidth,
      }));
      const horizontalOverflow = layout.scrollWidth > layout.clientWidth;
      if(phase === 'after' && horizontalOverflow) {
        throw new Error(`${scenario} horizontal overflow ${layout.scrollWidth}>${layout.clientWidth} at ${width}`);
      }

      if(runtimeErrors.length) {
        const expectedFailureScenario = [
          'stock-read-error',
          'stock-quantity-refusal',
          'stock-add-refusal',
          'stock-delete-refusal',
        ].includes(scenario) || (phase === 'before' && scenario === 'stock-delete-confirm');
        const unexpected = runtimeErrors.filter(error => {
          if (error.startsWith('pageerror:')) {
            return !(phase === 'before' && expectedFailureScenario && error.includes('503'));
          }
          if (expectedFailureScenario && error.startsWith('console:')) return false;
          return !error.includes('503');
        });
        if(unexpected.length) throw new Error(unexpected.join('\n'));
      }

      const path=`${out}/${scenario}-${width}x${height}.png`;
      await page.screenshot({path,fullPage:true,animations:'disabled'});
      evidence.push({scenario,viewport:{width,height},phase,deletes:deletes.length,horizontalOverflow,path});
      await context.close();
    }
  }
} finally {
  await browser.close();
}

await fs.writeFile(`${out}/evidence.json`,JSON.stringify(evidence,null,2));
