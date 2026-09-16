export type InsuranceMappingStatus = 'NOT_EVALUATED' | 'EXACT' | 'AMBIGUOUS' | 'NO_MATCH' | 'OUTDATED';
export type InsuranceDraftStatus = 'INCOMPLETE' | 'READY_FOR_REVIEW' | 'VALIDATED';
export type InsuranceCareType = 'SOINS' | 'PROTHESE' | 'ORTHODONTIE_FACIALE' | 'AUTRES';
export type InsuranceRequestNature = 'EXECUTION' | 'PRIOR_APPROVAL';

export interface InsuranceAdministrativeSnapshot {
  request_nature?: InsuranceRequestNature | null;
  insured_full_name?: string | null;
  insured_affiliation_number?: string | null;
  insured_registration_number?: string | null;
  insured_national_id?: string | null;
  insured_address?: string | null;
  insured_quality?: string | null;
  beneficiary_full_name?: string | null;
  beneficiary_birth_date?: string | null;
  beneficiary_national_id?: string | null;
  beneficiary_sex?: string | null;
  relationship_to_insured?: string | null;
  practitioner_full_name?: string | null;
  practitioner_inpe?: string | null;
  care_type?: InsuranceCareType | null;
  prior_approval_number?: string | null;
  accident_date?: string | null;
  accident_circumstances?: string | null;
  attachments_count: number;
}

export interface InsuranceSubmissionLine {
  service_date: string;
  label: string;
  teeth: string[];
  amount_mad: number;
  mapping_status: InsuranceMappingStatus;
  ngap_code?: string | null;
  ngap_coefficient?: number | null;
  mapping_rule_id?: string | null;
  source: {
    honoraires_document_id: number;
    honoraires_line_index: number;
    acte_id?: number | null;
    source_line_uid?: string | null;
    catalog_act_id?: number | null;
  };
}

export interface InsuranceSubmissionDraft {
  schema_version: string;
  patient_id: number;
  organization: 'CNSS' | 'CNOPS' | 'FAR';
  honoraires_document_id: number;
  lines: InsuranceSubmissionLine[];
  administrative: InsuranceAdministrativeSnapshot;
  unresolved_fields: string[];
  status: InsuranceDraftStatus;
  template: {
    template_version: string;
    template_hash?: string | null;
    source_url?: string | null;
    trust?: string | null;
  };
  reference: {
    ngap_reference_version?: string | null;
    ngap_reference_hash?: string | null;
  };
  validated_by_practitioner_id?: number | null;
  validated_at?: string | null;
}

export interface InsuranceFinalizationResult {
  document_id: number;
  is_new_version: boolean;
  file_hash: string;
  original_filename: string;
}
