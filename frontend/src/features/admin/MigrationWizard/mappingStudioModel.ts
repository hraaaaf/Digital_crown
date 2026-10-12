/** V1.5-05.2-B: staff-facing metadata-only rehearsal. No backend import or approval. */
export interface InventoryColumn {
  name: string;
  declared_type: string;
}
export interface InventoryTable {
  source_name: string;
  columns: readonly InventoryColumn[];
}
export interface SourceInventory {
  dialect_declared: string;
  source_format: string;
  sha256: string;
  tables: readonly InventoryTable[];
  warnings?: readonly string[];
  import_permitted: false;
}
export interface TargetTable {
  name: string;
  columns: readonly string[];
}
export interface TargetManifest {
  schema_revision: string;
  tables: readonly TargetTable[];
  /** Must stay false until an authenticated server-side adapter exists. */
  server_verified: false;
}
export interface ColumnChoice {
  /** undefined = not reviewed; null = explicitly UNMAPPED. */
  target?: string | null;
}
export interface TableChoice {
  /** undefined = not reviewed; null = explicitly UNMAPPED. */
  target?: string | null;
  columns: Record<string, ColumnChoice>;
}
export type MappingChoices = Record<string, TableChoice>;
export interface MappingReview {
  reviewed: number;
  total: number;
  tableCount: number;
  columnCount: number;
  unmapped: number;
  issues: string[];
  complete: boolean;
  /** This is always false. Only a real server-side admin gate may authorize later. */
  admin_approved: false;
  dry_run_completed: false;
  import_permitted: false;
}

const HEX_64 = /^[a-f0-9]{64}$/;
const secretWords = ['password', 'passwd', 'pwd', 'secret', 'token', 'credential',
  'apikey', 'api_key', 'privatekey', 'private_key', 'hashed', 'salt',
  'oauth', 'session_key', 'otp', 'authentication'];
const isSecret = (value: string): boolean =>
  secretWords.some(fragment => value.toLowerCase().replace(/[- ]/g, '_').includes(fragment));

function uniqueNames(names: readonly string[]): boolean {
  return names.length > 0 && names.every(name =>
    typeof name === 'string' && name.length > 0 && name.length <= 255 && !/[\x00-\x1f\x7f]/.test(name),
  ) && new Set(names.map(name => name.toLowerCase())).size === names.length;
}

export function inspectMetadataShape(source: SourceInventory, target: TargetManifest): string[] {
  const failures: string[] = [];
  if (!source || source.import_permitted !== false || !HEX_64.test(source.sha256)) failures.push('SOURCE_UNVERIFIED');
  if (!source || !Array.isArray(source.tables) || !uniqueNames(source.tables.map(t => t.source_name))
    || source.tables.some(t => !Array.isArray(t.columns) || !uniqueNames(t.columns.map(c => c.name)))) {
    failures.push('SOURCE_SCHEMA_AMBIGUOUS');
  }
  if (!target || target.server_verified !== false || !target.schema_revision
    || !Array.isArray(target.tables) || !uniqueNames(target.tables.map(t => t.name))
    || target.tables.some(t => !Array.isArray(t.columns) || !uniqueNames(t.columns))) {
    failures.push('TARGET_SCHEMA_AMBIGUOUS');
  }
  return failures;
}

/** Only non-ambiguous exact-name candidates; they are NEVER selected automatically. */
export function suggestExact(name: string, candidates: readonly string[]): string | null {
  if (isSecret(name)) return null;
  const matches = candidates.filter(candidate =>
    !isSecret(candidate) && candidate.toLowerCase() === name.toLowerCase(),
  );
  return matches.length === 1 ? matches[0] : null;
}

/** Every table AND every column must be intentionally reviewed, including UNMAPPED. */
export function evaluateMapping(
  source: SourceInventory,
  target: TargetManifest,
  choices: MappingChoices,
): MappingReview {
  const issues = inspectMetadataShape(source, target);
  let reviewed = 0;
  let total = 0;
  let unmapped = 0;
  let columnCount = 0;
  const usedTables = new Set<string>();
  for (const table of source?.tables ?? []) {
    const decision = choices[table.source_name];
    total += 1;
    columnCount += table.columns.length;
    total += table.columns.length;
    if (decision && decision.target !== undefined) {
      reviewed += 1;
      if (decision.target === null) unmapped += 1;
      else if (!target.tables.some(t => t.name === decision.target)) issues.push('UNKNOWN_TARGET_TABLE');
      else if (usedTables.has(decision.target)) issues.push('TABLE_COLLISION');
      else if (isSecret(table.source_name) || isSecret(decision.target)) issues.push('CREDENTIAL_MAPPING_FORBIDDEN');
      else usedTables.add(decision.target);
    }
    const destination = target?.tables?.find(t => t.name === decision?.target);
    const usedColumns = new Set<string>();
    for (const sourceColumn of table.columns) {
      const columnDecision = decision?.columns?.[sourceColumn.name];
      if (columnDecision && columnDecision.target !== undefined) {
        reviewed += 1;
        if (columnDecision.target === null) unmapped += 1;
        else if (!destination) issues.push('ORPHAN_COLUMN_MAPPING');
        else if (!destination.columns.includes(columnDecision.target)) issues.push('UNKNOWN_TARGET_COLUMN');
        else if (isSecret(sourceColumn.name) || isSecret(columnDecision.target))
          issues.push('CREDENTIAL_MAPPING_FORBIDDEN');
        else if (usedColumns.has(columnDecision.target)) issues.push('COLUMN_COLLISION');
        else usedColumns.add(columnDecision.target);
      }
    }
  }
  if (reviewed !== total) issues.push('REVIEW_INCOMPLETE');
  return {
    reviewed, total,
    tableCount: source?.tables?.length ?? 0,
    columnCount,
    unmapped,
    issues,
    complete: issues.length === 0,
    admin_approved: false,
    dry_run_completed: false,
    import_permitted: false,
  };
}

export function setTableChoice(choices: MappingChoices, sourceTable: string, target: string | null): MappingChoices {
  // Fail closed: selecting a different destination invalidates ALL prior column reviews.
  return { ...choices, [sourceTable]: { target, columns: {} } };
}
export function setColumnChoice(
  choices: MappingChoices, sourceTable: string, sourceColumn: string, target: string | null,
): MappingChoices {
  const table = choices[sourceTable];
  if (!table || table.target === undefined) return choices;
  return {
    ...choices,
    [sourceTable]: {
      ...table,
      columns: { ...table.columns, [sourceColumn]: { target } },
    },
  };
}

/** Synthetic-only fixtures. NOT the real Digital Crown SQLAlchemy schema. */
export const syntheticSource: SourceInventory = {
  dialect_declared: 'postgresql',
  source_format: 'sql-text-ddl',
  sha256: 'a'.repeat(64),
  import_permitted: false,
  warnings: ['DDL_ONLY_NO_ROWS_OR_RELATIONS_VALIDATED'],
  tables: [
    { source_name: 'patients', columns: [
      { name: 'id', declared_type: 'INTEGER' },
      { name: 'name', declared_type: 'TEXT' },
      { name: 'legacy_no', declared_type: 'TEXT' },
      { name: 'password_hash', declared_type: 'TEXT' },
    ] },
    { source_name: 'appointments', columns: [
      { name: 'id', declared_type: 'INTEGER' },
      { name: 'patient_id', declared_type: 'INTEGER' },
      { name: 'appointment_date', declared_type: 'TIMESTAMP' },
    ] },
    { source_name: 'legacy_notes', columns: [
      { name: 'note', declared_type: 'TEXT' },
    ] },
  ],
};
export const syntheticTarget: TargetManifest = {
  schema_revision: 'DEMO-NOT-A-REAL-MIGRATION-REVISION',
  server_verified: false,
  tables: [
    { name: 'patients', columns: ['id', 'name', 'legacy_no'] },
    { name: 'appointments', columns: ['id', 'patient_id', 'date'] },
    { name: 'clinical_notes', columns: ['id', 'note'] },
  ],
};
