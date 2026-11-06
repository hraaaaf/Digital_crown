/**
 * LOT06 B06: Chromium screenshots of the REAL product React TSX, with an
 * isolated synthetic API module. No real patients, backend, activation or commit.
 * Do not use these as a substitute for the owner's visual approval.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';

if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1'
    || process.env.DC06_B06_VISUAL_LAB !== '1'
    || process.env.ENVIRONMENT !== 'test'
    || !/^[a-f0-9]{40}$/.test(process.env.DC06_B06_VISUAL_SOURCE_SHA || '')) {
  throw new Error('B06_VISUAL_ISOLATION_REQUIRED');
}
const head = process.env.DC06_B06_VISUAL_SOURCE_SHA;
const root = process.cwd();
const output = path.resolve(root, '../artifacts/lot06-b06-react-visual');
const htmlPath = path.join(root, 'lot06-b06-react-visual.html');
const entryPath = path.join(root, 'lot06-b06-react-visual.tsx');
const imagePath = path.join(root, 'lot06-b06-synthetic.png');
await fs.mkdir(output, { recursive: true });

const htmlSource = '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body><div id="root"></div><script type="module" src="/lot06-b06-react-visual.tsx"></script></body></html>';
const entrySource = [
  "import React from 'react';",
  "import { createRoot } from 'react-dom/client';",
  "import './src/index.css';",
  "import { ImagingAcquisitionProductReviewV15 } from './src/features/patients/components/ImagingAcquisitionProductReviewV15';",
  "const theme = new URLSearchParams(window.location.search).get('theme');",
  "if (theme) document.documentElement.dataset.theme = theme;",
  "createRoot(document.getElementById('root')!).render(",
  "  <main className='min-h-screen bg-background px-3 py-6 text-text-main sm:px-6 lg:py-10'>",
  "    <div className='mx-auto max-w-5xl'>",
  "      <h1 className='mb-4 text-xl font-bold'>Dossier patient — Médias</h1>",
  "      <ImagingAcquisitionProductReviewV15 patientId={42} />",
  "    </div>",
  "  </main>",
  ");",
].join('\n');

const syntheticApi = String.raw`
  let promise;
  const fixture = () => {
    promise ||= (async () => {
      const response = await fetch('/lot06-b06-synthetic.png', { cache: 'no-store' });
      if (!response.ok) throw new Error('SYNTHETIC_IMAGE_UNAVAILABLE');
      const bytes = await response.arrayBuffer();
      const hash = await crypto.subtle.digest('SHA-256', bytes);
      const digest = Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2,'0')).join('');
      const capture = { id:17, size:bytes.byteLength, digest, mime:'image/png', category:'PHOTO' };
      const review = {
        schema_version:'dc06-product-review-v1', status:'STAFF_REVIEW_REQUIRED',
        clinical_receipt_authorized:false,
        review_id:'syntheticReviewId123456789012345',
        challenge:'syntheticChallengeValue1234567890',
        capture_id:17, capture_digest:digest, capture_size:bytes.byteLength,
        patient_id:42, nom:'Test', prenom:'Patiente',
        numero_dossier:'TEST-42', date_naissance:'2000-03-04',
        expires_at:Math.floor(Date.now()/1000)+1800,
        preview_url:'/imaging/acquisition/review/syntheticReviewId123456789012345/preview',
        durable_commit_available:true,
      };
      return { bytes, capture, review };
    })();
    return promise;
  };
  export const api = {
    async get(url) {
      const f = await fixture();
      if (url === '/imaging/acquisition/unassigned') return { data: {
        schema_version:'dc06-product-unassigned-v1',
        state:'UNASSIGNED_INVENTORY_READ_ONLY',
        read_only:true, patient_assigned:false,
        clinical_receipt_authorized:false, captures:[f.capture],
      }};
      if (url === f.review.preview_url) return {
        data:f.bytes.slice(0), headers:{'content-type':'image/png'},
      };
      throw new Error('B06_VISUAL_API_DENIED');
    },
    async post(url, payload) {
      const f = await fixture();
      if (url === '/imaging/acquisition/review'
          && payload?.selected_patient_id === 42
          && payload?.capture_id === f.capture.id
          && payload?.capture_digest === f.capture.digest) return { data:f.review };
      throw new Error('B06_VISUAL_NO_CLINICAL_WRITES');
    },
    async delete() { return { status:204 }; },
  };
`;
const plugin = {
  name: 'b06-synthetic-api-only-for-product-review',
  enforce: 'pre',
  resolveId(source, importer) {
    if (source === '../../../services/api'
        && importer?.replaceAll('\\', '/').endsWith(
          '/src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx')) {
      return '\0dc06-b06-synthetic-api';
    }
  },
  load(id) {
    if (id === '\0dc06-b06-synthetic-api') return syntheticApi;
  },
};
const svg = [
  '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180">',
  '<rect width="320" height="180" rx="12" fill="#dbe5ef"/>',
  '<path d="M20 60 Q160 6 300 60 M20 115 Q160 168 300 115" fill="none" stroke="#64748b" stroke-width="4"/>',
  '<g fill="#f8fafc" stroke="#7890a5" stroke-width="2">',
  ...Array.from({ length: 6 }, (_, i) => {
    const x = 35 + i * 46;
    return '<path d="M' + x + ' 40 q-10 -14 1 -19 q10 -5 16 2 q12 -8 19 2 q4 9 -2 15 l-5 23 -9 -7 -9 7z"/>';
  }),
  ...Array.from({ length: 6 }, (_, i) => {
    const x = 35 + i * 46;
    return '<path d="M' + x + ' 140 q-10 14 1 19 q10 5 16 -2 q12 8 19 -2 q4 -9 -2 -15 l-5 -23 -9 7 -9 -7z"/>';
  }),
  '</g></svg>',
].join('');

let browser, server;
const results = [];
try {
  browser = await chromium.launch({headless:true});
  const makeImage = await browser.newPage({viewport:{width:400,height:240}});
  await makeImage.setContent(svg);
  await makeImage.locator('svg').screenshot({path:imagePath});
  await makeImage.close();
  const bytes = await fs.stat(imagePath);
  if (bytes.size > 16384 || bytes.size < 100)
    throw new Error('SYNTHETIC_PNG_BOUNDS_DENIED: ' + bytes.size);

  await fs.writeFile(htmlPath, htmlSource);
  await fs.writeFile(entryPath, entrySource);
  server = await createServer({
    configFile:false, root, plugins:[react(), plugin],
    server:{host:'127.0.0.1',port:5186,strictPort:true},
  });
  await server.listen();

  for (const variant of [
    {width:390,height:844,theme:'default'},
    {width:430,height:932,theme:'default'},
    {width:1280,height:900,theme:'default'},
    {width:390,height:844,theme:'dark'},
  ]) {
    const {width,height,theme}=variant;
    const context = await browser.newContext({viewport:{width,height}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.route('https://fonts.googleapis.com/**', route => route.abort());
    await page.route('https://fonts.gstatic.com/**', route => route.abort());
    await page.goto('http://127.0.0.1:5186/lot06-b06-react-visual.html?theme='+theme, {
      waitUntil:'domcontentloaded',timeout:60000,
    });
    const region = page.getByRole('region', {name:"Revue d'acquisition non attribuée"});
    const examine = region.getByRole('button',{name:'Examiner cette capture pour ce patient'});
    await examine.waitFor({state:'visible',timeout:40000});
    const prefix=theme+'-'+width;
    if(theme==='default' && (width===390||width===1280)) {
      await page.screenshot({path:path.join(output,prefix+'-pending.png'),fullPage:true});
    }
    await examine.click();
    const image = region.getByRole('img',{name:'Aperçu sécurisé de la capture'});
    await image.waitFor({state:'visible',timeout:40000});
    const imageLoaded=await image.evaluate(x=>x.complete&&x.naturalWidth>0);
    if(!imageLoaded) throw new Error('B06_VISUAL_PREVIEW_NOT_LOADED');
    const dossier=region.getByLabel('Ressaisir le numéro de dossier');
    const birth=region.getByLabel('Ressaisir la date de naissance');
    const submit=region.getByRole('button',{name:'Ajouter l’image au dossier'});
    if(await dossier.inputValue() || await birth.inputValue() || await submit.isEnabled())
      throw new Error('B06_VISUAL_TWO_MARKERS_MUST_START_EMPTY_AND_DENIED');
    await page.screenshot({path:path.join(output,prefix+'-review.png'),fullPage:true});
    await dossier.fill('TEST-42');
    await birth.fill('2000-03-04');
    if(await submit.isEnabled()) throw new Error('B06_VISUAL_EXPLICIT_CHECKBOX_REQUIRED');
    await region.getByRole('checkbox').check();
    if(!(await submit.isEnabled())) throw new Error('B06_VISUAL_COMMIT_BUTTON_NOT_ENABLED');
    if(theme==='default' && (width===390 || width===1280)) {
      await page.screenshot({path:path.join(output,prefix+'-ready.png'),fullPage:true});
    }
    const qa=await page.evaluate(() => {
      const panel=document.querySelector('section[aria-label]');
      const button=Array.from(document.querySelectorAll('button')).find(b=>b.textContent?.includes('Ajouter l’image'));
      return {
        overflow:document.documentElement.scrollWidth>innerWidth+2,
        panelOverflow:!!panel && panel.scrollWidth>panel.clientWidth+2,
        backgroundColor:button?getComputedStyle(button).backgroundColor:null,
        text:document.body.innerText,
      };
    });
    if(qa.overflow || qa.panelOverflow) throw new Error('B06_VISUAL_RESPONSIVE_OVERFLOW: '+prefix);
    if(/SHA-256|Reçu durable|Activation cabinet non autorisée|LAB uniquement/.test(qa.text))
      throw new Error('B06_VISUAL_DEV_COPY_LEAK: '+prefix);
    if(errors.length) throw new Error('B06_VISUAL_PAGE_ERROR: '+errors.join('; '));
    results.push({width,height,theme,previewLoaded:true,twoMarkersTyped:true,
      explicitCheckbox:true,commitsExecuted:0,overflow:false,
      primaryTokenComputed:qa.backgroundColor});
    await context.close();
  }
  if(results[0].primaryTokenComputed===results[3].primaryTokenComputed)
    throw new Error('B06_VISUAL_THEME_TOKENS_NOT_SWITCHING');
  await fs.writeFile(path.join(output,'summary.json'),JSON.stringify({
    sourceHead:head, type:'ACTUAL_REACT_COMPONENT_WITH_SYNTHETIC_API',
    exactSource:'src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx',
    validation:'BROWSER_FUE_PASS_NOT_OWNER_APPROVAL',
    limits:'Not the full authenticated patient page, clinical backend, or a physical device',
    results,
  },null,2));
  console.log('DC06_B06_REACT_BROWSER_VISUAL_FUE_PASS: '+head);
} finally {
  if(server) await server.close();
  if(browser) await browser.close();
  for(const file of [htmlPath,entryPath,imagePath])
    await fs.rm(file,{force:true}).catch(()=>{});
}
