import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const src = (file: string) => readFileSync(resolve(process.cwd(), 'src/features/admin', file), 'utf8');
const documentHub = src('DocumentHub.tsx');
const documentHubContent = src('DocumentStudio/DocumentHubContent.tsx');
const generator = src('DocumentStudio/useDocumentGenerator.ts');
const studio = src('DocumentStudio/Forms/PrescriptionAgenticStudioV1.tsx');
const clinicalContextPanel = src('DocumentStudio/Forms/PatientClinicalContextPanel.tsx');

describe('Prescription Intelligence V1 active clinical boundary', () => {
  it('does not call or retain the legacy smart suggestion path', () => {
    expect(documentHub).not.toContain('/prescriptions/smart-suggest/');
    expect(documentHub).not.toContain('setSmartSuggestion');
    expect(documentHub).toContain('smartSuggestion: null');
  });

  it('keeps legacy automatic prescription mechanisms outside the active V1 studio', () => {
    expect(studio).not.toContain('PrescriptionAgenticStudioLegacy');
    expect(studio).not.toContain('DEFAULT_MOROCCO_PRESETS');
    expect(studio).not.toContain('QUICK_PRESCRIPTIONS');
    expect(studio).toContain('data-clinical-rule-status="blocked"');
  });

  it('does not call the uncertified legacy safety engine from V1 or expose its internal status copy', () => {
    expect(studio).not.toContain("api.post('/prescriptions/safety/check'");
    expect(studio).toContain('data-safety-status="blocked"');
    expect(studio).not.toContain('Suggestion clinique bloquée');
    expect(studio).not.toContain('Contrôle clinique automatique bloqué');
  });

  it('captures C1 patient facts without introducing a prescription automation path', () => {
    expect(studio).toContain('PatientClinicalContextPanel');
    expect(clinicalContextPanel).toContain('/clinical-context');
    expect(clinicalContextPanel).not.toContain('/prescriptions/');
    expect(clinicalContextPanel).not.toContain('clinical_ready');
    expect(clinicalContextPanel).not.toContain('prescription_indication');
    expect(clinicalContextPanel).not.toContain('Indication de cette prescription');
    expect(clinicalContextPanel).toContain('Enregistrer le contexte');
  });

  it('keeps prescription indication scoped to the ordonnance document', () => {
    expect(studio).toContain('data-prescription-indication="document"');
    expect(studio).toContain("indication: currentIndicationRef.current.trim() || null");
    expect(documentHub).toContain("indication?: string;");
    expect(documentHub).toContain("setPrescriptionIndication(d.indication || '')");
    expect(documentHubContent).toContain('prescriptionIndication={prescriptionIndication}');
  });

  it('does not silently relearn dosage or posology from archived prescriptions', () => {
    expect(generator).not.toContain('/prescriptions/habits/record');
    expect(generator).not.toContain('ibuprofene');
    expect(generator).not.toContain('ketoprofene');
    expect(generator).not.toContain('augmentin');
  });

  it('never invents a medication form when V1 has none', () => {
    expect(documentHub).not.toContain("forme: m.forme || 'Sachets'");
    expect(documentHubContent).not.toContain("forme: 'Comprimés'");
    expect(generator).not.toContain("forme: d.forme || 'Sachets'");
    expect(generator).toContain('forme: d.forme,');
  });
});
