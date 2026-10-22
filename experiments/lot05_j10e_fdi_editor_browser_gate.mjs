/* FUE-I browser proof on SYNTHETIC canvas only, no real radiograph or patient. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright-core';

const chromePaths = ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium'];
const executablePath = chromePaths.find(p => fs.existsSync(p));
if (!executablePath) throw Error('installed_chromium_not_found');
const browser = await chromium.launch({
  executablePath, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const externalRequests = [];
await page.route('**/*', async route => {
  const url = new URL(route.request().url());
  if (url.hostname !== '127.0.0.1') {
    externalRequests.push(url.hostname);
    await route.abort();
  } else await route.continue();
});
try {
  await page.goto('http://127.0.0.1:8765/lot05_j10e_fdi_review_demo.html', {
    waitUntil: 'networkidle'
  });
  assert.match(await page.title(), /Digital Crown/);
  const imageBytes = await page.evaluate(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1200;
    canvas.height = 600;
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 1200, 600);
    gradient.addColorStop(0, '#202b33');
    gradient.addColorStop(.5, '#a9b7c0');
    gradient.addColorStop(1, '#283844');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 1200, 600);
    // Synthetic ellipses, not real radiographs
    ctx.fillStyle = '#e5edf0';
    for(let x=120; x<1050; x+=150) {
      ctx.beginPath();ctx.ellipse(x,330,44,98,0,0,2*Math.PI);ctx.fill();
    }
    return canvas.toDataURL('image/png').split(',')[1];
  });
  await page.locator('#imageInput').setInputFiles({
    name: 'synthetic-fdi.png', mimeType: 'image/png',
    buffer: Buffer.from(imageBytes, 'base64')
  });
  await page.locator('#photo').waitFor({state:'visible'});
  const demo = {
    schema:'digital-crown-fdi-review-v1',image_width:1200,image_height:600,
    proposals:[
      {fdi:'36',bbox:[.12,.20,.22,.65],confidence:.91},
      {fdi:'37',bbox:[.24,.20,.34,.65],confidence:.76}
    ]
  };
  await page.locator('#predictionInput').setInputFiles({
    name:'synthetic-proposals.json',mimeType:'application/json',
    buffer:Buffer.from(JSON.stringify(demo))
  });
  assert.equal(await page.locator('#toothList .toothitem').count(),2);
  assert.match(await page.locator('#confirmed').innerText(),/0 confirmée/);
  await page.locator('#toothList .toothitem').first().click();
  await page.locator('#fdiSelect').selectOption('35');
  await page.locator('#confirmBtn').click();
  assert.match(await page.locator('#confirmed').innerText(),/1 confirmée/);
  await page.locator('#specialty').selectOption('Endodontie');
  await page.locator('#actLabel').fill('Geste manuel synthétique');
  await page.locator('#addActBtn').click();
  await page.locator('#assignActBtn').click();
  assert.match(await page.locator('#selectedActs').innerText(),/Geste manuel synthétique/);
  await page.screenshot({path:'lot05-j10e-fdi-synthetic-preview.png',fullPage:true});
  // Any later edit must invalidate confirmation/acts.
  await page.locator('#x1').fill('15');
  await page.locator('#applyBoxBtn').click();
  assert.match(await page.locator('#confirmed').innerText(),/0 confirmée/);
  assert.match(await page.locator('#selectedActs').innerText(),/aucun/);
  // Add a truly missing tooth through click-to-place.
  await page.locator('#manualFdi').selectOption('38');
  await page.locator('#addModeBtnAside').click();
  await page.locator('#overlay').click({position:{x:30,y:30}});
  assert.equal(await page.locator('#toothList .toothitem').count(),3);
  assert.equal(externalRequests.length,0,'external network request during offline prototype');
  console.log(JSON.stringify({
    status:'PASS_SYNTHETIC_FDI_BROWSER_INTERACTION',
    imported_proposals:2,manually_added:1,manual_fdi_correction:true,
    confirm_before_act:true,edit_invalidates_confirmation:true,
    external_requests:externalRequests.length, patient_data:false,
    clinic_approved:false
  }));
} finally {
  await browser.close();
}
