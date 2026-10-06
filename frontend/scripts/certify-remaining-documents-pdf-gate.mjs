import fs from 'node:fs';
import path from 'node:path';
import { request } from 'playwright';
import { execFileSync } from 'node:child_process';

const outDir = path.resolve('../artifacts/t2-browser/remaining-documents-pdf-gate');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD required');
const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: process.env.T2_USER || 't2-browser@cabinet.ma', password } });
if (!login.ok()) throw new Error('Remaining PDF login failed: ' + login.status());
const tokens = await login.json();
const headers = { Authorization: 'Bearer ' + tokens.access_token };

const patientResp = await api.post('/api/patients/', { headers, data: {
  nom: 'PDF-REMAINING', prenom: 'Élodie', date_naissance: '1990-01-01', sexe: 'F',
  telephone: '0600000043', email: 'pdf-remaining@example.com',
}});
if (!patientResp.ok()) throw new Error('Patient create failed: ' + patientResp.status() + ' ' + await patientResp.text());
const patient = await patientResp.json();

const certDense = [
  'Je certifie avoir examiné la patiente ce jour dans le cadre de son suivi bucco-dentaire.',
  'Le présent document reprend exclusivement les éléments saisis et validés par le praticien.',
  'Contrôle clinique réalisé avec attention particulière portée à la tolérance fonctionnelle et au confort rapporté.',
  'Réévaluation recommandée selon l’évolution clinique observée par le praticien.',
].join('\n');
const stressUnit = 'Évaluation médico-dentaire — contrôle : sensibilité, œdème, évolution post-opératoire et tolérance fonctionnelle. Texte de robustesse : à â ç é è ê ë î ï ô ù û ü œ « » — ’.';

const scenarios = [
  { document:'certificat', id:'standard', endpoint:'/api/documents/generate?archive=false&preview=true&force=false',
    body:{type:'certificat',patient_id:patient.id,is_accounted:false,payment_status:'EN_ATTENTE',data:{reason:'Arrêt de travail',days:4,doc_date:'2026-10-02',start_date:'2026-10-02'}},
    needles:['CERTIFICAT MEDICAL','arrêt de travail','4 jours','02/10/2026'] },
  { document:'certificat', id:'dense', endpoint:'/api/documents/generate?archive=false&preview=true&force=false',
    body:{type:'certificat',patient_id:patient.id,is_accounted:false,payment_status:'EN_ATTENTE',data:{reason:'Certificat médical',days:0,doc_date:'2026-10-02',content:certDense}},
    needles:['CERTIFICAT MEDICAL','suivi bucco-dentaire','Réévaluation recommandée'] },
  { document:'certificat', id:'stress', endpoint:'/api/documents/generate?archive=false&preview=true&force=false',
    body:{type:'certificat',patient_id:patient.id,is_accounted:false,payment_status:'EN_ATTENTE',data:{reason:'Certificat médical',days:0,doc_date:'2026-10-02',content:Array.from({length:18},(_,i)=>stressUnit.replace('contrôle','contrôle n° '+(i+1))).join('\n\n')}},
    needles:['CERTIFICAT MEDICAL','Évaluation médico-dentaire','œdème'] },

  { document:'echeancier', id:'standard', endpoint:'/api/installments/generate-preview',
    body:{patient_id:patient.id,title:'Plan de paiement standard',total_amount:1000,items:[
      {label:'Avance Initiale',amount:200,due_date:'2026-10-02',paid:true},
      {label:'Mensualité 1',amount:400,due_date:'2026-11-02',paid:false},
      {label:'Mensualité 2',amount:400,due_date:'2026-12-02',paid:false}]},
    needles:['SUIVI DE PAIEMENT','Plan de paiement standard','1000.00 MAD'] },
  { document:'echeancier', id:'dense', endpoint:'/api/installments/generate-preview',
    body:{patient_id:patient.id,title:'Plan de paiement dense',total_amount:3600,items:Array.from({length:12},(_,i)=>({label:'Échéance '+(i+1),amount:300,due_date:'2027-'+String((i%12)+1).padStart(2,'0')+'-15',paid:i<3}))},
    needles:['SUIVI DE PAIEMENT','Plan de paiement dense','3600.00 MAD'] },
  { document:'echeancier', id:'stress', endpoint:'/api/installments/generate-preview',
    body:{patient_id:patient.id,title:'Plan long — Échéancier robustesse',total_amount:7200,items:Array.from({length:24},(_,i)=>({label:'Échéance longue n° '+(i+1)+' — contrôle',amount:300,due_date:(2027+Math.floor(i/12))+'-'+String((i%12)+1).padStart(2,'0')+'-15',paid:i<6}))},
    needles:['SUIVI DE PAIEMENT','Plan long','7200.00 MAD'] },

  { document:'libre', id:'standard', endpoint:'/api/documents/generate?archive=false&preview=true&force=false',
    body:{type:'libre',patient_id:patient.id,is_accounted:false,payment_status:'EN_ATTENTE',data:{title:'ATTESTATION',content:'À qui de droit,\nDocument libre standard de certification PDF.',doc_date:'2026-10-02',page_size:'A5',alignment:'justify',hide_patient_header:false}},
    needles:['ATTESTATION','Document libre standard'] },
  { document:'libre', id:'dense', endpoint:'/api/documents/generate?archive=false&preview=true&force=false',
    body:{type:'libre',patient_id:patient.id,is_accounted:false,payment_status:'EN_ATTENTE',data:{title:'LETTRE MÉDICALE',content:Array.from({length:8},(_,i)=>'Paragraphe '+(i+1)+' — contenu explicitement saisi par le praticien, sans enrichissement automatique.').join('\n\n'),doc_date:'2026-10-02',page_size:'A4',alignment:'justify',hide_patient_header:false}},
    needles:['LETTRE MÉDICALE','contenu explicitement saisi'] },
  { document:'libre', id:'stress', endpoint:'/api/documents/generate?archive=false&preview=true&force=false',
    body:{type:'libre',patient_id:patient.id,is_accounted:false,payment_status:'EN_ATTENTE',data:{title:'DOCUMENT ROBUSTESSE',content:Array.from({length:36},(_,i)=>'Section '+(i+1)+' — '+stressUnit).join('\n\n'),doc_date:'2026-10-02',page_size:'A4',alignment:'justify',hide_patient_header:false}},
    needles:['DOCUMENT ROBUSTESSE','Section 1','œdème'] },
];

const requestedDocument = String(process.env.REMAINING_DOCUMENT_FILTER || '').trim();
const selectedScenarios = requestedDocument ? scenarios.filter(s => s.document === requestedDocument) : scenarios;
if (requestedDocument && selectedScenarios.length === 0) throw new Error('Unknown remaining document filter: ' + requestedDocument);
const report={productHead:process.env.PRODUCT_HEAD||null,patientDossier:patient.numero_dossier,filter:requestedDocument||null,scenarios:[]};

function fetchPdfPath(payload) {
  if (!payload?.pdf_url) throw new Error('missing pdf_url');
  return String(payload.pdf_url).replace(/^\//,'').replace(/^api\//,'');
}

for (const scenario of selectedScenarios) {
  const response=await api.post(scenario.endpoint,{headers,data:scenario.body});
  if (!response.ok()) throw new Error(scenario.document+'/'+scenario.id+' generation failed: '+response.status()+' '+await response.text());
  const payload=await response.json();
  const clean=fetchPdfPath(payload);
  const pdf=await api.get('/api/'+clean,{headers});
  if (!pdf.ok()) throw new Error(scenario.document+'/'+scenario.id+' PDF fetch failed: '+pdf.status());
  const bytes=await pdf.body();
  if(bytes.length<5||bytes.subarray(0,4).toString('ascii')!=='%PDF') throw new Error(scenario.document+'/'+scenario.id+' invalid PDF signature');
  const dir=path.join(outDir,scenario.document); fs.mkdirSync(dir,{recursive:true});
  const file=scenario.id+'.pdf'; fs.writeFileSync(path.join(dir,file),bytes);
  report.scenarios.push({document:scenario.document,id:scenario.id,bytes:bytes.length,signature:'%PDF',pdfFile:path.join(scenario.document,file),expectedNeedles:scenario.needles});
}

for(const scenario of report.scenarios){
  const pdfPath=path.join(outDir,scenario.pdfFile); const stem=scenario.document+'-'+scenario.id;
  let info; try{info=execFileSync('pdfinfo',[pdfPath],{encoding:'utf8'});}catch{throw new Error('pdfinfo required');}
  const m=info.match(/^Pages:\s+(\d+)/m); if(!m) throw new Error(stem+' missing page count');
  const pages=Number(m[1]); if(!Number.isInteger(pages)||pages<1) throw new Error(stem+' invalid page count');
  const renderDir=path.join(outDir,'renders',scenario.document,scenario.id); fs.mkdirSync(renderDir,{recursive:true});
  execFileSync('pdftoppm',['-png','-r','144',pdfPath,path.join(renderDir,'page')],{stdio:'pipe'});
  const rendered=fs.readdirSync(renderDir).filter(n=>/^page-\d+\.png$/.test(n)).length;
  if(rendered!==pages) throw new Error(stem+' render/page mismatch '+rendered+'/'+pages);
  const textPath=path.join(outDir,scenario.document,scenario.id+'.txt');
  execFileSync('pdftotext',['-layout',pdfPath,textPath],{stdio:'pipe'});
  const extracted=fs.readFileSync(textPath,'utf8'); if(extracted.trim().length<40) throw new Error(stem+' extracted text too short');
  for(const needle of scenario.expectedNeedles) if(!extracted.includes(needle)) throw new Error(stem+' missing expected text: '+needle);
  if (scenario.document === 'certificat' && scenario.id === 'stress') {
    const lastTextPath = path.join(outDir,scenario.document,scenario.id+'-last-page.txt');
    execFileSync('pdftotext',['-f',String(pages),'-l',String(pages),'-layout',pdfPath,lastTextPath],{stdio:'pipe'});
    const lastPageText = fs.readFileSync(lastTextPath,'utf8');
    if (!lastPageText.includes('contrôle n° 18')) throw new Error(stem+' last page missing final medical body');
    if (!lastPageText.includes('Signature manuscrite du praticien')) throw new Error(stem+' last page missing practitioner signature');
  }
  scenario.pages=pages; scenario.renderedPages=rendered; scenario.textBytes=Buffer.byteLength(extracted); scenario.renderDir=path.relative(outDir,renderDir); scenario.textFile=path.relative(outDir,textPath);
}
const byDocument={};
for(const s of report.scenarios){byDocument[s.document]??=[];byDocument[s.document].push({id:s.id,pages:s.pages,bytes:s.bytes,textBytes:s.textBytes});}
report.byDocument=byDocument;
fs.writeFileSync(path.join(outDir,'remaining-documents-matrix.json'),JSON.stringify(report,null,2));
console.log('REMAINING_DOCUMENTS_PDF_GATE_PASS '+JSON.stringify(report));
await api.dispose();
