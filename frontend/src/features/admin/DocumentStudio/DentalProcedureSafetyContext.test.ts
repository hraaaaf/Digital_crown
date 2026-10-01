import { describe, expect, it } from 'vitest';
import {
  dentalProcedureSafetyContext,
  UNKNOWN_DENTAL_PROCEDURE_SAFETY_CONTEXT,
} from './DentalProcedureSafetyContext';

describe('DentalProcedureSafetyContext', () => {
  it('fails closed when no canonical procedure is supplied', () => {
    expect(dentalProcedureSafetyContext(null)).toEqual(UNKNOWN_DENTAL_PROCEDURE_SAFETY_CONTEXT);
  });

  it('classifies a simple extraction as low postoperative bleeding risk and IE-qualifying', () => {
    expect(dentalProcedureSafetyContext('SIMPLE_EXTRACTION_1_TO_3')).toEqual({
      bleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
      ieProcedureQualifies: true,
      osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
    });
  });

  it('classifies implant surgery as higher postoperative bleeding risk with osseous injury', () => {
    expect(dentalProcedureSafetyContext('IMPLANT_SURGERY')).toEqual({
      bleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
      ieProcedureQualifies: true,
      osseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
    });
  });

  it('does not mark a routine orthodontic adjustment as procedure-sensitive', () => {
    expect(dentalProcedureSafetyContext('ORTHODONTIC_APPLIANCE_ADJUSTMENT')).toEqual({
      bleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
      ieProcedureQualifies: false,
      osseousRisk: 'NO_OSSEOUS_INJURY',
    });
  });
});
