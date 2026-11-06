/**
 * B06 source-exact visual evidence. Runs ONLY on disposable GitHub CI.
 * Imports the actual patient component with a synthetic API alias and the
 * actual frontend theme CSS. Never imports backend or writes clinical data.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright';

if (process.env.GITHUB_ACTIONS !== 'true' ||
    process.env.ENVIRONMENT !== 'test' ||
    process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1' ||
    process.env.B06_REACT_VISUAL_ONLY !== '1') {
  throw new Error('REFUSED: disposable isolated GitHub visual FUE only');
}
const head = process.env.B06_EXACT_HEAD || '';
if (!/^[a-f0-9]{40}$/.test(head)) throw new Error('Exact source SHA required');
const repoHead = execFileSync('git', ['rev-parse', 'HEAD'], {
  cwd: path.resolve('..'), encoding: 'utf8',
}).trim();
if (repoHead !== head) throw new Error('Checked-out source does not match expected SHA');

const root = process.cwd();
const htmlPath = path.join(root, 'lot06-b06-visual-evidence.html');
const entryPath = path.join(root, 'src', '.lot06-b06-visual-evidence.tsx');
const mockPath = path.join(root, 'src', '.lot06-b06-synthetic-api.ts');
const out = path.resolve('../artifacts/lot06-b06-react-chromium');
await fs.mkdir(out, { recursive: true });

const entry = String.raw`
import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import { ImagingAcquisitionProductReviewV15 } from './features/patients/components/ImagingAcquisitionProductReviewV15';
const theme = new URLSearchParams(window.location.search).get('theme');
if (theme === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
createRoot(document.getElementById('root')!).render(
  <main className="min-h-screen bg-background px-3 py-8 text-text-main sm:px-6">
    <div className="mx-auto w-full max-w-6xl">
      <ImagingAcquisitionProductReviewV15 patientId={42} />
    </div>
  </main>
);
`;
const mock = String.raw`
/* Synthetic in-memory API for visual evidence only. No real backend or writes. */
let fixturePromise: Promise<{bytes: ArrayBuffer, digest: string, size: number}> | null = null;
function fixture() {
  if (!fixturePromise) fixturePromise = (async () => {
    const canvas = document.createElement('canvas');
    canvas.width = 640; canvas.height = 420;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Synthetic preview canvas unavailable');
    // Grayscale synthetic image pixels, NOT application UI colors.
    ctx.fillStyle = 'rgb(24,24,24)'; ctx.fillRect(0,0,640,420);
    ctx.strokeStyle = 'rgb(190,190,190)'; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.ellipse(320,190,220,90,0,0,Math.PI*2); ctx.stroke();
    ctx.lineWidth = 4;
    for(let i=0;i<12;i++){
      const x=125+i*35;
      ctx.strokeStyle = 'rgb(150,150,150)';
      ctx.strokeRect(x,160+Math.round(24*Math.sin(i/2)),25,55);
    }
    ctx.fillStyle = 'rgb(205,205,205)';
    ctx.font = '16px sans-serif'; ctx.textAlign='center';
    ctx.fillText('IMAGE SYNTHETIQUE',320,350);
    const blob = await new Promise<Blob>((resolve,reject)=>{
      canvas.toBlob(v=>v?resolve(v):reject(new Error('PNG synthetic fixture unavailable')),'image/png');
    });
    const bytes = await blob.arrayBuffer();
    if (bytes.byteLength > 16384) throw new Error('Synthetic PNG exceeds real capture limit');
    const hash = await crypto.subtle.digest('SHA-256',bytes);
    const digest = Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');
    return {bytes,digest,size:bytes.byteLength};
  })();
  return fixturePromise;
}
const reviewId = 'syntheticReviewId123456789012345';
const challenge = 'syntheticChallengeValue1234567890';
export const api = {
  async get(url: string) {
    const f=await fixture();
    if(url==='/imaging/acquisition/unassigned') return {data:{
      schema_version:'dc06-product-unassigned-v1',
      state:'UNASSIGNED_INVENTORY_READ_ONLY', clinical_receipt_authorized:false,
      patient_assigned:false, read_only:true,
      captures:[{id:17,digest:f.digest,size:f.size,mime:'image/png',category:'PHOTO'}],
    }};
    if(url==='/imaging/acquisition/review/'+reviewId+'/preview')
      return {data:f.bytes.slice(0),headers:{'content-type':'image/png'}};
    throw new Error('Synthetic API refused unexpected GET');
  },
  async post(url: string, request: Record<string, unknown>) {
    const f=await fixture();
    if(url==='/imaging/acquisition/review' &&
      request.selected_patient_id===42 && request.capture_id===17 &&
      request.capture_digest===f.digest) return {data:{
        schema_version:'dc06-product-review-v1',status:'STAFF_REVIEW_REQUIRED',
        clinical_receipt_authorized:false,review_id:reviewId,challenge,
        capture_id:17,capture_digest:f.digest,capture_size:f.size,
        patient_id:42,nom:'Test',prenom:'Patiente',numero_dossier:'SYN-42',
        date_naissance:'2000-03-04',expires_at:Math.floor(Date.now()/1000)+900,
        preview_url:'/imaging/acquisition/review/'+reviewId+'/preview',
        durable_commit_available:true,
      }};
    throw new Error('Synthetic API refuses confirmation or clinical write');
  },
  async delete() { throw new Error('Synthetic API refuses deletion'); },
};
`;
const html = '<!doctype html><html lang="fr"><head><meta charset="UTF-8"/>' +
  '<meta name="viewport" content="width=device-width,initial-scale=1"/></head>' +
  '<body><div id="root"></div><script type="module" src="/src/.lot06-b06-visual-evidence.tsx"></script></body></html>';
const report = [];
let server;
let browser;
try {
  await Promise.all([
    fs.writeFile(htmlPath, html), fs.writeFile(entryPath,entry),
    fs.writeFile(mockPath,mock),
  ]);
  server = await createServer({
    configFile:false, root, plugins:[react()],
    resolve:{alias:[{find:'../../../services/api',replacement:mockPath}]},
    server:{host:'127.0.0.1',port:5179,strictPort:true},
  });
  await server.listen();
  browser = await chromium.launch({headless:true});
  const colors = {};
  for (const [width,theme] of [[390,'default'],[430,'default'],[1280,'default'],[1280,'dark']]) {
    const label = theme+'-'+width;
    const context = await browser.newContext({
      viewport:{width,height:width<500?844:900},deviceScaleFactor:1,
      colorScheme:theme==='dark'?'dark':'light',
    });
    const page = await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    page.on('requestfailed',req=>errors.push('request failed: '+req.url()));
    await page.goto('http://127.0.0.1:5179/lot06-b06-visual-evidence.html?theme='+theme,
      {waitUntil:'networkidle',timeout:45000});
    const region = page.getByRole('region',{name:"Revue d'acquisition non attribuée"});
    await region.waitFor({state:'visible'});
    const pending=region.getByRole('button',{name:/Examiner cette capture/});
    await pending.waitFor({state:'visible'});
    await region.screenshot({path:path.join(out,label+'-pending.png')});
    await pending.click();
    const confirm=region.getByRole('button',{name:/Ajouter l.image au dossier/});
    await confirm.waitFor({state:'visible'});
    const image=region.getByRole('img',{name:/Aperçu sécurisé/});
    await image.waitFor({state:'visible'});
    await page.waitForFunction(() => {
      const im=document.querySelector('img[alt="Aperçu sécurisé de la capture"]');
      return Boolean(im && im.complete && im.naturalWidth>0);
    });
    const dossier=region.getByLabel('Ressaisir le numéro de dossier');
    const dob=region.getByLabel('Ressaisir la date de naissance');
    if(await dossier.inputValue()!=='' || await dob.inputValue()!==''
      || !(await confirm.isDisabled())) throw new Error('Identity fields not blank or confirm not disabled');
    await region.getByRole('heading',{name:/1\. Contrôler l.image/}).waitFor();
    await region.getByRole('heading',{name:/2\. Vérifier l.identité du patient/}).waitFor();
    await region.screenshot({path:path.join(out,label+'-review.png')});
    await dossier.fill('SYN-42');
    await dob.fill('2000-03-04');
    if(!(await confirm.isDisabled())) throw new Error('Confirmation enabled without explicit checkbox');
    await region.getByRole('checkbox').check();
    if(await confirm.isDisabled())throw new Error('Correct two-marker consent refused');
    const uiText=await region.innerText();
    if(/SHA-256|Reçu durable|Activation cabinet non autorisée|LAB uniquement|DC06-[a-f0-9]{32}/i.test(uiText))
      throw new Error('Technical/debug detail exposed to dentist');
    const metrics=await page.evaluate(()=>{
      const region=document.querySelector('section[aria-label]');
      const btn=Array.from(document.querySelectorAll('button')).find(b=>b.textContent?.includes('Ajouter l’image au dossier'));
      if(!region||!btn)throw new Error('Real component DOM missing');
      return {
        documentOverflow:document.documentElement.scrollWidth>innerWidth+2,
        regionOverflow:region.scrollWidth>region.clientWidth+2,
        background:getComputedStyle(btn).backgroundColor,
        foreground:getComputedStyle(btn).color,
        regionWidth:region.getBoundingClientRect().width,
      };
    });
    if(metrics.documentOverflow||metrics.regionOverflow||metrics.regionWidth>width+2||errors.length)
      throw new Error('Responsive or browser errors '+JSON.stringify({label,metrics,errors}));
    colors[label]=metrics.background;
    await region.screenshot({path:path.join(out,label+'-ready.png')});
    report.push({label,width,theme,result:'PASS',metrics,screenshots:[
      label+'-pending.png',label+'-review.png',label+'-ready.png',
    ],consentAndTwoMarkers:'typed and checked; no commit invoked'});
    await context.close();
  }
  if(colors['default-1280']===colors['dark-1280'])
    throw new Error('Theme inheritance not confirmed (same primary across themes)');
  const summary={sourceHead:head,scope:'actual patient React component + actual theme CSS in Chromium',
    syntheticOnly:true,clinicalBackend:false,clinicalWrites:0,
    humanUXApproval:'PENDING_OWNER',
    result:'PASS',report};
  await fs.writeFile(path.join(out,'summary.json'),JSON.stringify(summary,null,2));
  process.stdout.write('DC06_B06_REACT_CHROMIUM_VISUAL_FUE_PASS '+head+'\n');
} finally {
  if(browser)await browser.close();
  if(server)await server.close();
  await Promise.all([htmlPath,entryPath,mockPath].map(f=>fs.rm(f,{force:true})));
}
