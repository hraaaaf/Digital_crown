/** CEPH-P1 real FUE: browser/real FastAPI/real image/model, no forged calibration.
 * Extends previously proven FUE-H. All actions through authenticated React.
 * Original public images on disposable T2 only. NO genuine patient records.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const head=process.env.PRODUCT_HEAD, password=process.env.T2_PASSWORD;
const db=process.env.DATABASE_URL, seed=JSON.parse(process.env.CEPH_R23H_PATIENT||'{}');
if(process.env.ENVIRONMENT!=='test'||process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'
 ||db!=='sqlite:///./t2-runtime-cert.db'||!password||!/^[a-f0-9]{40}$/.test(head||'')
 ||!Number.isSafeInteger(seed.patient_id)||seed.clinical_release!==false)
 throw Error('P1 refuses non-disposable patient or database');
const prev=JSON.parse(await fs.readFile('../artifacts/ceph-r23h-first-use/report.json','utf8'));
if(prev.head!==head||prev.overall!=='FUE_H_REAL_UI_ONNX_PERSISTENCE_SECURITY_PASS_NONCLINICAL'
 ||prev.case_ids?.length!==2||prev.errors?.length) throw Error('Exact-head FUE-H prerequisite not green');
const out=path.resolve('../artifacts/ceph-fue-p1-authenticated');
await fs.mkdir(out,{recursive:true});
const report={schema:'CEPH_FUE_P1_AUTHENTICATED_UNCALIBRATED_SAFETY_V1',head,source:'H_REAL_UI_PUBLIC_ONNX',
  predecessor:'FUE_H_REAL_UI_ONNX_PERSISTENCE_SECURITY_PASS_NONCLINICAL',case_id:prev.case_ids[0],
  patient_synthetic:true,calibration_verified:false,clinical_release:false,all_four_steps_complete:false,
  facad_parity_verified:false,checks:[],errors:[],screenshots:[],overall:'NOT_TESTED'};
const browser=await chromium.launch({headless:true}), api=await request.newContext({baseURL:'http://127.0.0.1:8005'});
let ctx=null,page=null,token=null;
function ensure(v,msg){if(!v)throw Error(msg)}
async function shot(name){if(page){const file=name+'.png';await page.screenshot({path:path.join(out,file),animations:'disabled',fullPage:false});report.screenshots.push(file)}}
async function check(id,fn){try{const proof=await fn();report.checks.push({id,status:'PASS',evidence:proof});console.log('FUE_P1_PASS',id);return true}catch(e){report.checks.push({id,status:'FAIL',error:String(e)});report.errors.push(id+': '+e);console.error('FUE_P1_FAIL',id,e);await shot('fail-'+id).catch(()=>{});return false;}}
async function detail(){const r=await api.get('/api/ia/analyses/'+report.case_id,{headers:{Authorization:'Bearer '+token}});ensure(r.status()===200,'Study GET refused '+r.status());return r.json();}
try{
 const loginOk=await check('REAL_CABINET_LOGIN_AND_EXISTING_STUDY',async()=>{
   const auth=await api.post('/api/auth/login',{form:{username:'t2-browser@cabinet.ma',password}});
   ensure(auth.status()===200,'T2 login rejected');token=(await auth.json()).access_token;
   const station=await enrollT2Workstation(api,token,password);
   ctx=await browser.newContext({viewport:{width:1280,height:900},
     storageState:{cookies:station.cookies.filter(c=>c.name==='dc_workstation'),origins:[]}});
   page=await ctx.newPage();page.setDefaultTimeout(25000);
   await page.goto('http://127.0.0.1:5173/hub?select=1',{waitUntil:'domcontentloaded'});
   await page.locator('[data-hub-experience="cabinet"]').click();
   await page.locator('input[type=email]').fill('t2-browser@cabinet.ma');
   await page.locator('input[type=password]').fill(password);
   await page.getByRole('button',{name:'Se connecter',exact:true}).click();
   await page.waitForURL(u=>new URL(u).pathname==='/dashboard',{timeout:50000});
   await page.goto('http://127.0.0.1:5173/patients/'+seed.patient_id+'?tab=radiology&radioTab=cephalo',{waitUntil:'domcontentloaded'});
   await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
   await page.getByRole('button',{name:'Historique',exact:true}).click();
   await page.locator('[data-cephalo-history-analysis-id="'+report.case_id+'"]').click();
   await page.locator('[data-cephalo-selected-analysis-id="'+report.case_id+'"]').waitFor({state:'visible'});
   await page.locator('svg[data-cephalo-viewport="base"] image').waitFor({state:'attached'});
   const d=await detail();
   ensure(d.is_calibrated===false && d.mm_per_pixel==null && d.landmarks_data?.length===38,
     'Study falsified calibration or model outputs');
   await shot('01-real-cabinet-before');
   return {selected_study:report.case_id,landmarks:38,calibration:'UNVERIFIED'};
 });
 if(loginOk){
 await check('CALIBRATION_ASSISTANT_NO_FALSE_MM',async()=>{
   const before=await detail();
   const badge=page.locator('[data-r20-radiograph-stage]').getByRole('button',{name:/Calibration :/});
   await badge.waitFor({state:'visible'});
   await badge.click();
   const assistant=page.locator('[data-cephalo-calibration-assistant]');
   await assistant.waitFor({state:'visible'});
   ensure((await assistant.innerText()).includes('Aucune échelle physique vérifiée'),
      'No physical scale not transparently disclosed');
   await assistant.getByRole('button',{name:'Calibrer manuellement'}).click();
   await page.getByText('Calibration manuelle',{exact:true}).waitFor({state:'visible'});
   await shot('02-calibration-unverified');
   // Never enter invented mm or claim physical calibration; reload is a user-safe cancel.
   await page.reload({waitUntil:'domcontentloaded'});
   await page.locator('[data-cephalo-selected-analysis-id="'+report.case_id+'"]').waitFor({state:'visible'});
   const after=await detail();
   ensure(before.is_calibrated===false && after.is_calibrated===false && after.mm_per_pixel==null,
     'Viewing a calibration dialog generated a false physical scale');
   return {manual_entry_observed:true,applied:false,mm_per_pixel:null};
 });
 await check('REAL_PROTOCOL_SELECTORS_AND_UNVERIFIED_LABELS',async()=>{
   const options=['all','steiner','tweed','mcnamara','com','ricketts'];
   const selector=page.locator('#cephalo-ready-analysis');
   await selector.waitFor({state:'visible'});
   const found=await selector.locator('option').evaluateAll(nodes=>nodes.map(n=>n.value));
   ensure(options.every(x=>found.includes(x)),'Missing protocol select options '+JSON.stringify(found));
   for(const option of options){
     await selector.selectOption(option);
     await page.locator('[data-r20-measures-panel]').waitFor({state:'visible'});
     // Source completeness and measurements are NOT certified by showing a menu.
     await page.waitForTimeout(80);
   }
   await selector.selectOption('steiner');
   await shot('03-steiner-source-status');
   await selector.selectOption('ricketts');
   await shot('04-ricketts-held');
   await selector.selectOption('all');
   return {selectable:options,complete_protocols_certified:0,scientific_mre_certified:false};
 });
 await check('VIEWER_ZOOM_AND_LAYER_REAL_INTERACTIONS',async()=>{
   const zoom=page.locator('[data-cephalo-zoom-controls]');
   await zoom.waitFor({state:'visible'});
   ensure((await zoom.locator('[data-cephalo-zoom-level]').innerText()).includes('100'),'Not original 100% zoom');
   await zoom.getByRole('button',{name:'Agrandir la radiographie'}).click();
   ensure((await zoom.locator('[data-cephalo-zoom-level]').innerText()).includes('125'),'Zoom did not change to 125');
   await zoom.getByRole('button',{name:'Afficher toute la radiographie'}).click();
   ensure((await zoom.locator('[data-cephalo-zoom-level]').innerText()).includes('100'),'Zoom did not reset');
   await page.getByText('Gestionnaire de couches',{exact:true}).click();
   const lm=page.locator('[data-ortho-layer-control="landmarks"] button');
   await lm.waitFor({state:'visible'});
   const initial=await lm.getAttribute('aria-pressed');
   ensure(initial==='true'||initial==='false','Landmark layer lacks truthful accessible pressed state');
   await lm.click();
   ensure((await lm.getAttribute('aria-pressed'))!===initial,'Layer toggle did not change');
   await lm.click();
   ensure((await lm.getAttribute('aria-pressed'))===initial,'Layer toggle failed restore');
   await shot('05-controls-and-layers');
   return {zoom:'100→125→100',landmarks_layer:'toggle+restore'};
 });
 await check('LANDMARK_POINTER_EDIT_UNDO_REDO_SAVE_RELOAD',async()=>{
   await page.getByText('Historique des corrections',{exact:true}).click();
   const undo=page.getByRole('button',{name:'Annuler dernière correction'});
   const redo=page.getByRole('button',{name:'Rétablir correction'});
   ensure(await undo.isDisabled(),'Unexpected preexisting edit history');
   const original=(await detail()).landmarks_data;
   const pt=page.locator('g[data-ortho-layer="landmarks"] g[style*="pointer-events"]').first();
   await pt.waitFor({state:'visible'});
   const rect=await pt.boundingBox();ensure(rect&&rect.width>1,'Landmark drag geometry unavailable');
   const x=rect.x+rect.width/2,y=rect.y+rect.height/2;
   await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+16,y+9,{steps:8});await page.mouse.up();
   await undo.waitFor({state:'visible'});
   ensure(!(await undo.isDisabled()),'Real drag did not create an undo transaction');
   await undo.click();ensure(!(await redo.isDisabled()),'Undo did not produce redo');
   await redo.click();ensure(!(await undo.isDisabled()),'Redo not restored');
   await page.getByRole('button',{name:'Sauvegarder l’analyse céphalométrique'}).click();
   await page.waitForTimeout(1500);
   const saved=await detail();
   ensure(saved.landmarks_data?.length===38,'Saved landmark count corrupted');
   const changed=original.some((l,i)=>{
      const b=saved.landmarks_data[i];return l.id===b?.id&&(Math.abs(l.x-b.x)>0.05||Math.abs(l.y-b.y)>0.05);
   });
   ensure(changed,'Real pointer correction did not persist after Save');
   ensure(saved.is_calibrated===false&&saved.mm_per_pixel==null,'Editing fabricated physical calibration');
   await shot('06-correction-saved');
   await page.reload({waitUntil:'domcontentloaded'});
   await page.locator('[data-ortho-workspace-title]').waitFor({state:'visible'});
   await page.getByRole('button',{name:'Historique',exact:true}).click();
   await page.locator('[data-cephalo-history-analysis-id="'+report.case_id+'"]').click();
   await page.locator('[data-cephalo-selected-analysis-id="'+report.case_id+'"]').waitFor({state:'visible'});
   const reopened=await detail();
   ensure(JSON.stringify(reopened.landmarks_data)===JSON.stringify(saved.landmarks_data),
     'Saved data changed after fresh browser reload');
   return {real_drag:true,undo:true,redo:true,saved:true,reloaded:true,validated_clinically:false};
 });
 await check('DOCUMENT_STEPPER_SAFELY_BLOCKS_UNCALIBRATED_STUDY',async()=>{
   const docs=page.getByRole('button',{name:'Documents & stratégie',exact:true});
   await docs.waitFor({state:'visible'});
   await docs.click();
   // The current UI intentionally refuses to advance without a physical scale.
   await page.getByText('Calibration manuelle',{exact:true}).waitFor({state:'visible',timeout:6000});
   ensure(await page.getByRole('button',{name:'Céphalométrie',exact:true}).count()>0,
     'Actual stepper missing');
   const still=await detail();
   ensure(still.is_calibrated===false&&still.mm_per_pixel==null,'Step navigation silently invented a scale');
   await shot('07-document-step-blocked-by-true-calibration-gate');
   return {requested_document_preview:true,actual_pdf_generated:false,
      expected_blocker:'PHYSICAL_SCALE_UNAVAILABLE',complete_four_steps:false};
 });
 }
 report.overall=report.errors.length?'FUE_P1_REAL_UI_FAILED':'FUE_P1_REAL_UI_SAFE_PARTIAL__DOCUMENT_BLOCKED_CALIBRATION';
}catch(e){report.errors.push('UNEXPECTED '+String(e));report.overall='FUE_P1_REAL_UI_FAILED'}
finally{
 if(ctx)await ctx.close().catch(()=>{});
 await api.dispose();await browser.close();
 await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
 console.log('FUE_P1_RESULT',report.overall,JSON.stringify({head,passed:report.checks.filter(x=>x.status==='PASS').length,failed:report.checks.filter(x=>x.status==='FAIL').map(x=>x.id),clinical_go:false}));
 if(report.errors.length)process.exitCode=1;
}
