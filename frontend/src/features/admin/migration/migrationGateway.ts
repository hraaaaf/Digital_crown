/** LOT05.5 authenticated OWNER / workstation API, NO source-file upload. */
import { api } from '../../../services/api';
import { parseTargetInventory } from './MappingStudioPolicy';

export type Preflight = Readonly<{
  status: 'construction';
  schema_revision_matches: boolean;
  declared_subset_matches: boolean;
  physical_subset_checked: boolean;
  full_schema_certified: false;
  authenticated_cabinet_scope: boolean;
  dry_run_real_data_available: false;
  import_permitted: false;
  target_preview: unknown | null;
  blockers: string[];
}>;
export type Rehearsal = Readonly<{
  mode: 'SYNTHETIC_MEMORY_ONLY';
  source_patients: 100;
  source_appointments: 200;
  verified_patients: 100;
  verified_appointments: 200;
  verified_patient_links: 200;
  orphan_appointments: 0;
  cross_tenant_links: 0;
  after_rollback_patients: 0;
  after_rollback_appointments: 0;
  cabinet_rows_read: false;
  cabinet_rows_written: false;
  schema_migrated_by_alembic: false;
  import_permitted: false;
}>;

export async function fetchMigrationPreflight(): Promise<Preflight> {
  const { data } = await api.get<Preflight>('/migration/preflight');
  if (data.status !== 'construction' || data.import_permitted !== false ||
      data.dry_run_real_data_available !== false || data.full_schema_certified !== false ||
      !Array.isArray(data.blockers)) {
    throw new Error('PREFLIGHT_INCOHERENT');
  }
  if (data.physical_subset_checked && data.target_preview) {
    parseTargetInventory(JSON.stringify(data.target_preview));
  }
  return data;
}

export async function runSyntheticStaffRehearsal(): Promise<Rehearsal> {
  // No identifiers, patient rows, legacy files or mapping decisions are sent.
  const { data } = await api.post<Rehearsal>('/migration/synthetic-rehearsal', {});
  if (data.mode !== 'SYNTHETIC_MEMORY_ONLY' ||
      data.source_patients !== 100 || data.source_appointments !== 200 ||
      data.verified_patients !== 100 || data.verified_appointments !== 200 ||
      data.verified_patient_links !== 200 || data.orphan_appointments !== 0 ||
      data.cross_tenant_links !== 0 || data.after_rollback_patients !== 0 ||
      data.after_rollback_appointments !== 0 ||
      data.import_permitted !== false || data.cabinet_rows_read !== false ||
      data.cabinet_rows_written !== false || data.schema_migrated_by_alembic !== false) {
    throw new Error('SYNTHETIC_REHEARSAL_INCOHERENT');
  }
  return data;
}
