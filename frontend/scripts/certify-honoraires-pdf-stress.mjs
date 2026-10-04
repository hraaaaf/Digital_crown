import fs from 'node:fs';
import path from 'node:path';
import { request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/honoraires-pdf-stress');
fs.mkdirSync(outDir, { recursive: true });
const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: process.env.T2_USER || 't2-browser@cabinet.ma', password } });
if (!login.ok()) throw new Error('Stress login failed: ' + login.status());
const tokens = await login.json();
const headers = { Authorization: 'Bearer ' + tokens.access_token };
const patientResp = await api.post('/api/patients/', {
  headers,
  data: {
    nom: 'PDF-STRESS',
    prenom: 'Honoraires',
    date_naissance: '1990-01-01',
    sexe: 'M',
    telephone: '0600000003',
    email: 'pdf-stress@example.com',
  },
});
if (!patientResp.ok()) throw new Error('Stress patient create failed: ' + patientResp.status() + ' ' + await patientResp.text());
const patient = await patientResp.json();

const longA = 'Réhabilitation prothétique complexe avec préparation périphérique atraumatique, empreinte de précision, contrôle occlusal dynamique et ajustements fonctionnels successifs';
const longB = 'Traitement conservateur plurifactoriel avec isolation opératoire, reconstruction anatomique stratifiée, finition, polissage et vérification des contacts proximaux et occlusaux';

function rows(count, long = false) {
  return Array.from({ length: count }, (_, i) => ({
    date: '2026-09-20',
    acte: long ? (i % 2 ? longA : longB) + ' — séquence clinique ' + String(i + 1).padStart(2, '0') : 'Acte de certification ' + String(i + 1).padStart(2, '0'),
    dent: String([11,12,13,14,15,16,21,22,23,24][i % 10]),
    montant: 100 + i * 7,
    mode_reglement: 'Espèces',
  }));
}

const scenarios = [
  { id: 'baseline', hasLongText: false, payments: rows(3) },
  { id: 'long-text', hasLongText: true, payments: [{ date:'2026-09-20', acte: longA + ' avec contrôle radiographique comparatif et suivi clinique documenté à moyen terme afin de confirmer la stabilité du résultat thérapeutique', dent:'11, 12, 13', montant:1250, mode_reglement:'Virement' }] },
  { id: 'many-lines', hasLongText: false, payments: rows(24) },
  { id: 'long-many-lines', hasLongText: true, payments: rows(24, true) },
  { id: 'extreme-pagination', hasLongText: true, payments: rows(48, true) },
];

const report = { productHead: process.env.PRODUCT_HEAD || null, patientDossier: patient.numero_dossier, scenarios: [] };
for (const scenario of scenarios) {
  const response = await api.post('/api/documents/generate?archive=false&preview=true&force=false', {
    headers,
    data: {
      type: 'note',
      patient_id: patient.id,
      is_accounted: false,
      payment_status: 'EN_ATTENTE',
      data: { payments: scenario.payments, doc_date: '2026-09-20', teeth_data: [], installments: [], is_global_note: false },
    },
  });
  if (!response.ok()) throw new Error(scenario.id + ' generation failed: ' + response.status() + ' ' + await response.text());
  const payload = await response.json();
  if (!payload.pdf_url) throw new Error(scenario.id + ' missing pdf_url');
  const clean = String(payload.pdf_url).replace(/^\//, '').replace(/^api\//, '');
  const pdf = await api.get('/api/' + clean, { headers });
  if (!pdf.ok()) throw new Error(scenario.id + ' PDF fetch failed: ' + pdf.status());
  const bytes = await pdf.body();
  if (bytes.length < 5 || bytes.subarray(0,4).toString('ascii') !== '%PDF') throw new Error(scenario.id + ' invalid PDF signature');
  const file = scenario.id + '.pdf';
  fs.writeFileSync(path.join(outDir, file), bytes);
  report.scenarios.push({
    id: scenario.id,
    rowCount: scenario.payments.length,
    hasLongText: scenario.hasLongText,
    bytes: bytes.length,
    signature: bytes.subarray(0,4).toString('ascii'),
    contentType: pdf.headers()['content-type'] || null,
    pdfFile: file,
    expectedTotal: scenario.payments.reduce((sum,p) => sum + p.montant, 0),
  });
}
fs.writeFileSync(path.join(outDir, 'stress-matrix.json'), JSON.stringify(report, null, 2));
console.log('HONORAIRES_PDF_STRESS_PASS', JSON.stringify(report));
await api.dispose();
