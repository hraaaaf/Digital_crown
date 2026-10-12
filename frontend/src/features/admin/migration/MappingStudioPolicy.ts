/**
 * LOT05.2-B: in-memory schema-only review, NOT the authoritative Python mapping draft.
 * Never accepts patient rows, SQL, credentials, target DB connections or approval.
 */
import type { AppUser } from '../../../types';

export type ColumnMeta = Readonly<{ name: string; declared_type?: string }>;
export type TableMeta = Readonly<{ name: string; columns: readonly ColumnMeta[] }>;
export type SchemaInventory = Readonly<{ sourceSha256: string; sourceFormat: string; tables: readonly TableMeta[] }>;
export type TargetInventory = Readonly<{ schemaRevision: string; tables: readonly TableMeta[] }>;
export type ColumnChoice = string | null | undefined;
export type TableReview = Readonly<{ target: ColumnChoice; columns: Readonly<Record<string, ColumnChoice>> }>;
export type ReviewDecisions = Readonly<Record<string, TableReview>>;

const SHA = /^[a-f0-9]{64}$/;
const IDENTIFIER = /^[^\x00-\x1F\x7F]{1,255}$/u;
const MAX_SIZE = 1024 * 1024;
const SECRET = /password|passwd|pwd|secret|token|credential|api[_ -]?key|private[_ -]?key|hash|salt|oauth|session[_ -]?key|otp|authentication/i;
const hasOwn = (record: object, key: string) => Object.prototype.hasOwnProperty.call(record, key);
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const fail = (code: string): never => { throw new Error(code); };

export function canViewMigrationStudio(user: AppUser | null | undefined): boolean {
  return !!user && (
    user.is_superadmin === true ||
    user.role === 'ADMIN' ||
    (user.role === 'DENTISTE' && user.employer_id === null)
  );
}
export const isCredentialName = (name: string) => SECRET.test(name);
export const isSupportedJsonSize = (size: number) => Number.isInteger(size) && size > 0 && size <= MAX_SIZE;

function strictKeys(v: Record<string, unknown>, keys: readonly string[]): void {
  if (Object.keys(v).some(key => !keys.includes(key))) fail('UNEXPECTED_METADATA_FIELD');
}
function safeId(v: unknown): string {
  if (typeof v !== 'string' || !IDENTIFIER.test(v)) return fail('INVALID_IDENTIFIER');
  return v;
}
function safeString(v: unknown, code: string, max = 128): string {
  if (typeof v !== 'string' || !v || v.length > max || /[\x00-\x1F\x7F]/.test(v)) return fail(code);
  return v;
}
function tables(v: unknown, kind: 'source' | 'target'): readonly TableMeta[] {
  if (!Array.isArray(v) || v.length === 0 || v.length > 512) return fail('INVALID_TABLES');
  const seen = new Set<string>();
  return v.map((raw): TableMeta => {
    if (!object(raw)) return fail('INVALID_TABLE');
    strictKeys(raw, kind === 'source' ? ['source_name', 'columns'] : ['name', 'columns']);
    const name = safeId(raw[kind === 'source' ? 'source_name' : 'name']);
    if (seen.has(name.toLowerCase())) return fail('AMBIGUOUS_TABLE');
    seen.add(name.toLowerCase());
    if (!Array.isArray(raw.columns) || raw.columns.length === 0 || raw.columns.length > 512) return fail('INVALID_COLUMNS');
    const keys = new Set<string>();
    const columns = raw.columns.map((c: unknown): ColumnMeta => {
      if (!object(c)) return fail('INVALID_COLUMN');
      strictKeys(c, kind === 'source' ? ['name', 'declared_type', 'not_null', 'primary_key'] : ['name']);
      const col = safeId(c.name);
      if (keys.has(col.toLowerCase())) return fail('AMBIGUOUS_COLUMN');
      keys.add(col.toLowerCase());
      if (kind === 'source') {
        const declared_type = safeString(c.declared_type, 'INVALID_DECLARED_TYPE', 128);
        if (c.not_null !== undefined && c.not_null !== null && typeof c.not_null !== 'boolean') return fail('INVALID_COLUMN_META');
        if (c.primary_key !== undefined && c.primary_key !== null && typeof c.primary_key !== 'boolean') return fail('INVALID_COLUMN_META');
        return { name: col, declared_type };
      }
      return { name: col };
    });
    return { name, columns };
  });
}

export function parseSourceInventory(text: string): SchemaInventory {
  if (new TextEncoder().encode(text).byteLength > MAX_SIZE) return fail('SOURCE_REPORT_TOO_LARGE');
  const data: unknown = JSON.parse(text);
  if (!object(data)) return fail('INVALID_SOURCE_REPORT');
  strictKeys(data, ['dialect_declared', 'source_format', 'sha256', 'file_size_bytes',
    'tables', 'warnings', 'row_counts', 'mapping_approved', 'dry_run_completed', 'import_permitted']);
  if (data.mapping_approved !== false || data.dry_run_completed !== false ||
      data.import_permitted !== false || data.row_counts !== null) return fail('UNSAFE_SOURCE_REPORT');
  if (typeof data.sha256 !== 'string' || !SHA.test(data.sha256)) return fail('INVALID_SOURCE_SHA256');
  const fmt = safeString(data.source_format, 'INVALID_SOURCE_FORMAT');
  if (!['sql-text-ddl', 'sqlite-copy'].includes(fmt)) return fail('UNSUPPORTED_SOURCE_FORMAT');
  if (!['sqlite', 'postgresql', 'mysql', 'mariadb'].includes(String(data.dialect_declared))) return fail('INVALID_DIALECT');
  if (typeof data.file_size_bytes !== 'number' || !Number.isSafeInteger(data.file_size_bytes) || data.file_size_bytes <= 0) return fail('INVALID_FILE_SIZE');
  if (!Array.isArray(data.warnings) || data.warnings.some(w => typeof w !== 'string' || w.length > 128)) return fail('INVALID_WARNINGS');
  return { sourceSha256: data.sha256, sourceFormat: fmt, tables: tables(data.tables, 'source') };
}

export function parseTargetInventory(text: string): TargetInventory {
  if (new TextEncoder().encode(text).byteLength > MAX_SIZE) return fail('TARGET_REPORT_TOO_LARGE');
  const data: unknown = JSON.parse(text);
  if (!object(data)) return fail('INVALID_TARGET_REPORT');
  strictKeys(data, ['schema_revision', 'tables']);
  return { schemaRevision: safeString(data.schema_revision, 'INVALID_SCHEMA_REVISION'), tables: tables(data.tables, 'target') };
}

function exactMatch(needle: string, haystack: readonly string[]): string | undefined {
  return haystack.find(name => name.toLowerCase() === needle.toLowerCase());
}
export function proposeTable(source: string, target: TargetInventory): string | undefined {
  if (isCredentialName(source)) return undefined;
  return exactMatch(source, target.tables.map(t => t.name));
}
export function proposeColumn(source: string, target?: TableMeta): string | undefined {
  if (!target || isCredentialName(source)) return undefined;
  const candidate = exactMatch(source, target.columns.map(c => c.name));
  return candidate && !isCredentialName(candidate) ? candidate : undefined;
}
export function progress(source: SchemaInventory, target: TargetInventory, decisions: ReviewDecisions) {
  const acceptedTables = new Set<string>();
  let reviewed = 0;
  let total = 0;
  let mapped = 0;
  let unmapped = 0;
  let collisions = 0;
  let credentialBlocked = 0;
  for (const table of source.tables) {
    const decision = decisions[table.name];
    total += 1 + table.columns.length;
    if (decision && decision.target !== undefined) {
      reviewed++;
      if (decision.target !== null) {
        if (isCredentialName(table.name) || isCredentialName(decision.target)) credentialBlocked++;
        const selectedTarget = target.tables.find(t => t.name === decision.target);
        if (!selectedTarget) collisions++;
        if (acceptedTables.has(decision.target)) collisions++;
        acceptedTables.add(decision.target);
        mapped++;
      } else {
        unmapped++;
      }
    }
    const selected = target.tables.find(t => t.name === decision?.target);
    const usedCols = new Set<string>();
    for (const column of table.columns) {
      const picked = decision?.columns[column.name];
      if (picked === undefined) continue;
      reviewed++;
      if (picked === null) {
        unmapped++;
      } else {
        if (isCredentialName(column.name) || isCredentialName(picked)) credentialBlocked++;
        if (!selected || !selected.columns.some(c => c.name === picked) || usedCols.has(picked)) collisions++;
        if (decision?.target === null) collisions++;
        usedCols.add(picked);
        mapped++;
      }
    }
  }
  return { reviewed, total, mapped, unmapped, collisions, credentialBlocked,
    complete: reviewed === total && collisions === 0 && credentialBlocked === 0 };
}
