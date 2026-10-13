/** LOT05.6: owner gateway, only byte-exact synthetic fixture file supported. */
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
  blockers: readonly string[];
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


const MAX_OFFICIAL_SQLITE_BYTES = 512 * 1024;
const SQLITE_MAGIC = 'SQLite format 3';

function hex(buffer: ArrayBuffer): string {
  return [...new Uint8Array(buffer)].map(n => n.toString(16).padStart(2, '0')).join('');
}

async function digestOfficialFixture(bytes: ArrayBuffer): Promise<string> {
  // Without a trustworthy local WebCrypto digest, refuse upload entirely.
  if (typeof crypto === 'undefined' || !crypto.subtle) throw new Error('WEBCRYPTO_REQUIRED');
  return hex(await crypto.subtle.digest('SHA-256', bytes));
}

export type SyntheticFileDryrun = Readonly<{
  mode: 'OFFICIAL_SYNTHETIC_SQLITE_FILE_ONLY';
  source_sha256: string;
  source_patients: 100;
  source_appointments: 200;
  verified_patients: 100;
  verified_appointments: 200;
  verified_patient_links: 200;
  orphan_appointments: 0;
  cross_tenant_links: 0;
  after_rollback_patients: 0;
  after_rollback_appointments: 0;
  source_persisted: false;
  cabinet_rows_read: false;
  cabinet_rows_written: false;
  import_permitted: false;
}>;

export async function downloadOfficialSyntheticFile(): Promise<{ bytes: ArrayBuffer; sha: string }> {
  const { data } = await api.get<ArrayBuffer>('/migration/synthetic-fixture', {
    responseType: 'arraybuffer',
  });
  if (!(data instanceof ArrayBuffer) || data.byteLength < 100 ||
      data.byteLength > MAX_OFFICIAL_SQLITE_BYTES) throw new Error('INVALID_OFFICIAL_FIXTURE');
  const magic = new TextDecoder().decode(new Uint8Array(data, 0, 15));
  if (magic !== SQLITE_MAGIC) throw new Error('INVALID_OFFICIAL_FIXTURE');
  return { bytes: data, sha: await digestOfficialFixture(data) };
}

export async function dryrunOfficialSyntheticFile(file: File, expectedSha: string): Promise<SyntheticFileDryrun> {
  if (!/\\.db$/i.test(file.name) || file.size <= 0 || file.size > MAX_OFFICIAL_SQLITE_BYTES ||
      !/^[a-f0-9]{64}$/.test(expectedSha)) throw new Error('ONLY_OFFICIAL_SYNTHETIC_FILE');
  const buffer = await file.arrayBuffer();
  const actualSha = await digestOfficialFixture(buffer);
  // Local SHA gate runs BEFORE transmitting the selected file bytes.
  if (actualSha !== expectedSha) throw new Error('ONLY_DOWNLOADED_SYNTHETIC_FIXTURE');
  const { data } = await api.post<SyntheticFileDryrun>(
    '/migration/synthetic-file-dryrun', buffer,
    { headers: { 'Content-Type': 'application/vnd.sqlite3' }, timeout: 30000 },
  );
  if (data.mode !== 'OFFICIAL_SYNTHETIC_SQLITE_FILE_ONLY' ||
      data.source_sha256 !== expectedSha || data.source_patients !== 100 ||
      data.source_appointments !== 200 || data.verified_patients !== 100 ||
      data.verified_appointments !== 200 || data.verified_patient_links !== 200 ||
      data.orphan_appointments !== 0 || data.cross_tenant_links !== 0 ||
      data.after_rollback_patients !== 0 || data.after_rollback_appointments !== 0 ||
      data.source_persisted !== false || data.cabinet_rows_read !== false ||
      data.cabinet_rows_written !== false || data.import_permitted !== false) {
    throw new Error('SYNTHETIC_FILE_RESULT_INCOHERENT');
  }
  return data;
}
