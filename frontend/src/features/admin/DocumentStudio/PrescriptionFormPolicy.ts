export interface PrescriptionFormSourceDrug {
  forme?: string;
  type?: string;
}

interface GeneratedMedication {
  forme?: string;
  type?: string;
  [key: string]: unknown;
}

interface GeneratedDocumentPayload {
  data?: {
    medications?: GeneratedMedication[];
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export function hasMissingMedicationForm(drugs: PrescriptionFormSourceDrug[]): boolean {
  return drugs.some(drug => drug.type !== 'EXAMEN' && !drug.forme?.trim());
}

export function preserveExplicitMedicationForms<T extends GeneratedDocumentPayload>(
  payload: T,
  sourceDrugs: PrescriptionFormSourceDrug[],
): T {
  const medications = payload.data?.medications;
  if (!Array.isArray(medications)) return payload;

  medications.forEach((medication, index) => {
    const source = sourceDrugs[index];
    if (!source) return;
    if (source.type === 'EXAMEN') {
      medication.forme = source.forme || '';
      return;
    }
    medication.forme = source.forme?.trim() || '';
  });

  return payload;
}
