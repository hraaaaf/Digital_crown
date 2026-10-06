import fs from 'node:fs';
import path from 'node:path';
import { request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser/certificat-pdf-gate');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: process.env.T2_USER || 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error('Certificate PDF login failed: ' + login.status());
const tokens = await login.json();
const headers = { Authorization: 'Bearer ' + tokens.access_token };

const patientResp = await api.post('/api/patients/', {
  headers,
  data: {
    nom: 'PDF-CERTIFICAT',
    prenom: 'Élodie',
    date_naissance: '1990-01-01',
    sexe: 'F',
    telephone: '0600000042',
    email: 'pdf-certificat@example.com',
  },
});
if (!patientResp.ok()) throw new Error('Certificate patient create failed: ' + patientResp.status() + ' ' + await patientResp.text());
const patient = await patientResp.json();

const denseParagraph = [
  'Je certifie avoir examiné la patiente ce jour dans le cadre de son suivi bucco-dentaire.',
  'Le présent document reprend exclusivement les éléments saisis et validés par le praticien.',
  'Contrôle clinique réalisé avec attention particulière portée à la tolérance fonctionnelle et au confort rapporté.',
  'Réévaluation recommandée selon l’évolution clinique observée par le praticien.',
].join('\n');

const stressUnit = [
  'Évaluation médico-dentaire — contrôle n° 1 : sensibilité, œdème, évolution post-opératoire et tolérance fonctionnelle.',
  'Texte de robustesse avec accents : à, â, ç, é, è, ê, ë, î, ï, ô, ù, û, ü, œ ; ponctuation : « » — ’.',
  'Aucune donnée clinique implicite ne doit être ajoutée par le générateur ; ce texte provient intégralement de la fixture.',
].join('\n');

const scenarios = [
  {
    id: 'standard',
    expectedReason: 'Arrêt de travail',
    expectedNeedles: ['CERTIFICAT MEDICAL', 'arrêt de travail', '4 jours', '02/10/2026'],
    data: { reason: 'Arrêt de travail', days: 4, doc_date: '2026-10-02', start_date: '2026-10-02' },
  },
  {
    id: 'dense',
    expectedReason: 'Certificat médical',
    expectedNeedles: ['CERTIFICAT MEDICAL', 'suivi bucco-dentaire', 'Réévaluation recommandée'],
    data: { reason: 'Certificat médical', days: 0, doc_date: '2026-10-02', content: denseParagraph },
  },
  {
    id: 'stress',
    expectedReason: 'Certificat médical',
    expectedNeedles: ['CERTIFICAT MEDICAL', 'Évaluation médico-dentaire', 'robustesse avec accents'],
    data: {
      reason: 'Certificat médical',
      days: 0,
      doc_date: '2026-10-02',
      content: Array.from({ length: 18 }, (_, i) => stressUnit.replace('n° 1', 'n° ' + (i + 1))).join('\n\n'),
    },
  },
];

const report = {
  productHead: process.env.PRODUCT_HEAD || null,
  patientDossier: patient.numero_dossier,
  scenarios: [],
};

for (const scenario of scenarios) {
  const response = await api.post('/api/documents/generate?archive=false&preview=true&force=false', {
    headers,
    data: {
      type: 'certificat',
      patient_id: patient.id,
      is_accounted: false,
      payment_status: 'EN_ATTENTE',
      data: scenario.data,
    },
  });
  if (!response.ok()) throw new Error(scenario.id + ' generation failed: ' + response.status() + ' ' + await response.text());
  const payload = await response.json();
  if (!payload.pdf_url) throw new Error(scenario.id + ' missing pdf_url');

  const clean = String(payload.pdf_url).replace(/^\//, '').replace(/^api\//, '');
  const pdf = await api.get('/api/' + clean, { headers });
  if (!pdf.ok()) throw new Error(scenario.id + ' PDF fetch failed: ' + pdf.status());
  const bytes = await pdf.body();
  if (bytes.length < 5 || bytes.subarray(0, 4).toString('ascii') !== '%PDF') {
    throw new Error(scenario.id + ' invalid PDF signature');
  }

  const file = scenario.id + '.pdf';
  fs.writeFileSync(path.join(outDir, file), bytes);
  report.scenarios.push({
    id: scenario.id,
    reason: scenario.expectedReason,
    bytes: bytes.length,
    signature: bytes.subarray(0, 4).toString('ascii'),
    contentType: pdf.headers()['content-type'] || null,
    pdfFile: file,
    expectedNeedles: scenario.expectedNeedles,
  });
}

fs.writeFileSync(path.join(outDir, 'certificate-matrix.json'), JSON.stringify(report, null, 2));
console.log('CERTIFICAT_PDF_GATE_PASS ' + JSON.stringify(report));
await api.dispose();
