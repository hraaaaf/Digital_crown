export type DentalProcedureBleedingRisk =
  | 'UNKNOWN'
  | 'UNLIKELY_TO_CAUSE_BLEEDING'
  | 'LOW_POSTOP_BLEEDING_RISK'
  | 'HIGHER_POSTOP_BLEEDING_RISK';

export type DentalProcedureOsseousRisk =
  | 'UNKNOWN'
  | 'NO_OSSEOUS_INJURY'
  | 'DENTOALVEOLAR_OSSEOUS_INJURY';

export interface DentalProcedureSafetyContext {
  bleedingRisk: DentalProcedureBleedingRisk;
  ieProcedureQualifies: boolean | null;
  osseousRisk: DentalProcedureOsseousRisk;
}

export type CanonicalDentalProcedure =
  | 'LOCAL_ANAESTHESIA_INFILTRATION'
  | 'REGIONAL_NERVE_BLOCK'
  | 'BASIC_PERIODONTAL_EXAM'
  | 'SUPRAGINGIVAL_DEBRIDEMENT'
  | 'SUPRAGINGIVAL_RESTORATION'
  | 'ORTHOGRADE_ENDODONTICS'
  | 'IMPRESSION_OR_PROSTHETIC_PROCEDURE'
  | 'ORTHODONTIC_APPLIANCE_ADJUSTMENT'
  | 'SIMPLE_EXTRACTION_1_TO_3'
  | 'INTRAORAL_INCISION_AND_DRAINAGE'
  | 'SIX_POINT_PERIODONTAL_EXAM'
  | 'ROOT_SURFACE_DEBRIDEMENT'
  | 'SUBGINGIVAL_RESTORATION'
  | 'COMPLEX_EXTRACTION'
  | 'MULTIPLE_ADJACENT_EXTRACTIONS'
  | 'MORE_THAN_3_EXTRACTIONS'
  | 'SURGICAL_EXTRACTION'
  | 'PERIODONTAL_SURGERY'
  | 'PREPROSTHETIC_SURGERY'
  | 'PERIRADICULAR_SURGERY'
  | 'CROWN_LENGTHENING'
  | 'IMPLANT_SURGERY'
  | 'GINGIVAL_RECONTOURING'
  | 'BIOPSY';

const PROCEDURE_CONTEXT: Record<CanonicalDentalProcedure, DentalProcedureSafetyContext> = {
  LOCAL_ANAESTHESIA_INFILTRATION: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  REGIONAL_NERVE_BLOCK: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  BASIC_PERIODONTAL_EXAM: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  SUPRAGINGIVAL_DEBRIDEMENT: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  SUPRAGINGIVAL_RESTORATION: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  ORTHOGRADE_ENDODONTICS: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  IMPRESSION_OR_PROSTHETIC_PROCEDURE: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  ORTHODONTIC_APPLIANCE_ADJUSTMENT: {
    bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
    ieProcedureQualifies: false,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  SIMPLE_EXTRACTION_1_TO_3: {
    bleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  INTRAORAL_INCISION_AND_DRAINAGE: {
    bleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  SIX_POINT_PERIODONTAL_EXAM: {
    bleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  ROOT_SURFACE_DEBRIDEMENT: {
    bleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  SUBGINGIVAL_RESTORATION: {
    bleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  COMPLEX_EXTRACTION: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  MULTIPLE_ADJACENT_EXTRACTIONS: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  MORE_THAN_3_EXTRACTIONS: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  SURGICAL_EXTRACTION: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  PERIODONTAL_SURGERY: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  PREPROSTHETIC_SURGERY: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  PERIRADICULAR_SURGERY: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  CROWN_LENGTHENING: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  IMPLANT_SURGERY: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
  },
  GINGIVAL_RECONTOURING: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'NO_OSSEOUS_INJURY',
  },
  BIOPSY: {
    bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
    ieProcedureQualifies: true,
    osseousRisk: 'UNKNOWN',
  },
};

export const UNKNOWN_DENTAL_PROCEDURE_SAFETY_CONTEXT: DentalProcedureSafetyContext = {
  bleedingRisk: 'UNKNOWN',
  ieProcedureQualifies: null,
  osseousRisk: 'UNKNOWN',
};

export function dentalProcedureSafetyContext(
  procedure: CanonicalDentalProcedure | null | undefined,
): DentalProcedureSafetyContext {
  if (!procedure) return { ...UNKNOWN_DENTAL_PROCEDURE_SAFETY_CONTEXT };
  return { ...PROCEDURE_CONTEXT[procedure] };
}
