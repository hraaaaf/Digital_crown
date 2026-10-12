import { describe, expect, it } from 'vitest';
import {
  canViewMigrationStudio, isCredentialName, isSupportedJsonSize,
  parseSourceInventory, parseTargetInventory, proposeColumn, proposeTable, progress,
  type SchemaInventory, type TargetInventory,
} from './MappingStudioPolicy';
import type { AppUser } from '../../../types';

const SOURCE = {
  dialect_declared: 'sqlite',
  source_format: 'sqlite-copy',
  sha256: 'a'.repeat(64),
  file_size_bytes: 512,
  tables: [
    { source_name: 'patients', columns: [
      { name: 'id', declared_type: 'INTEGER', not_null: true, primary_key: true },
      { name: 'fullname', declared_type: 'TEXT' },
      { name: 'password_hash', declared_type: 'TEXT' },
    ]},
    { source_name: 'old_unknown', columns: [{ name: 'code', declared_type: 'TEXT' }] },
  ],
  warnings: ['SCHEMA_ONLY_NO_ROW_COUNTS'],
  row_counts: null, mapping_approved: false, dry_run_completed: false, import_permitted: false,
};
const TARGET = {
  schema_revision: 'neo000000027',
  tables: [{ name: 'patients', columns: [{ name: 'id' }, { name: 'name' }] }],
};
const input = () => parseSourceInventory(JSON.stringify(SOURCE));
const output = () => parseTargetInventory(JSON.stringify(TARGET));
const user = (overrides: Record<string, unknown> = {}) => ({
  role: 'SECRETAIRE', employer_id: 13, is_superadmin: false, ...overrides,
}) as unknown as AppUser;

describe('05.2-B1 — schema-only file boundary', () => {
  it('reads a 05.1 schema report without rows or defaults', () => {
    const report = input();
    expect(report.tables).toHaveLength(2);
    expect(report.tables[0].columns[0].name).toBe('id');
    expect(report.sourceSha256).toBe('a'.repeat(64));
    expect(JSON.stringify(report)).not.toContain('SCHEMA_ONLY_NO_ROW_COUNTS');
  });
  it('accepts a bounded target manifest but never grants trust', () => {
    expect(output().schemaRevision).toBe('neo000000027');
  });
  it('denies all unknown top-level metadata that could include patient rows', () => {
    expect(() => parseSourceInventory(JSON.stringify({ ...SOURCE, rows: [{ name: 'patient' }] })))
      .toThrow('UNEXPECTED_METADATA_FIELD');
  });
  it('denies unknown per-column defaults or injected SQL', () => {
    const bad = structuredClone(SOURCE);
    (bad.tables[0].columns[0] as object as Record<string, unknown>).default = 'secret';
    expect(() => parseSourceInventory(JSON.stringify(bad))).toThrow('UNEXPECTED_METADATA_FIELD');
  });
  it('denies imported data or preapproved inspector flags', () => {
    for (const field of ['mapping_approved', 'dry_run_completed', 'import_permitted'] as const) {
      expect(() => parseSourceInventory(JSON.stringify({ ...SOURCE, [field]: true }))).toThrow('UNSAFE_SOURCE_REPORT');
    }
    expect(() => parseSourceInventory(JSON.stringify({ ...SOURCE, row_counts: 9 }))).toThrow('UNSAFE_SOURCE_REPORT');
  });
  it('rejects a source checksum without exact lowercase SHA-256', () => {
    expect(() => parseSourceInventory(JSON.stringify({ ...SOURCE, sha256: 'ABC' }))).toThrow('INVALID_SOURCE_SHA256');
  });
  it('rejects duplicate tables with casefold ambiguity', () => {
    const duplicate = [...SOURCE.tables, { ...SOURCE.tables[0], source_name: 'PATIENTS' }];
    expect(() => parseSourceInventory(JSON.stringify({ ...SOURCE, tables: duplicate }))).toThrow('AMBIGUOUS_TABLE');
  });
  it('rejects target ambiguity and target rows', () => {
    expect(() => parseTargetInventory(JSON.stringify({
      ...TARGET, rows: [], tables: TARGET.tables,
    }))).toThrow('UNEXPECTED_METADATA_FIELD');
    expect(() => parseTargetInventory(JSON.stringify({
      ...TARGET, tables: [{ name: 'patients', columns: [{ name: 'ID' }, { name: 'id' }] }],
    }))).toThrow('AMBIGUOUS_COLUMN');
  });
  it('refuses excessive files and empty values', () => {
    expect(isSupportedJsonSize(1048576)).toBe(true);
    expect(isSupportedJsonSize(1048577)).toBe(false);
    expect(isSupportedJsonSize(0)).toBe(false);
    expect(() => parseTargetInventory(JSON.stringify({ ...TARGET, tables: [] }))).toThrow('INVALID_TABLES');
  });
  it('rejects malicious identifier control characters', () => {
    expect(() => parseSourceInventory(JSON.stringify({
      ...SOURCE, tables: [{ source_name: 'patients\nspoof', columns: [{ name: 'id', declared_type: 'INT' }] }],
    }))).toThrow('INVALID_IDENTIFIER');
  });
  it('refuses JSON carrying unknown credentials or extra data', () => {
    expect(() => parseTargetInventory(JSON.stringify({ ...TARGET, password: 'secret' })))
      .toThrow('UNEXPECTED_METADATA_FIELD');
  });
});

describe('05.2-B1 — suggestions/decisions and privileges', () => {
  it('only proposes exact names, never fuzzy medical synonyms', () => {
    expect(proposeTable('patients', output())).toBe('patients');
    expect(proposeTable('patient', output())).toBeUndefined();
    expect(proposeColumn('fullname', output().tables[0])).toBeUndefined();
    expect(proposeColumn('ID', output().tables[0])).toBe('id');
  });
  it('recognizes credentials and refuses their mapping suggestions', () => {
    expect(isCredentialName('password_hash')).toBe(true);
    expect(isCredentialName('api_key')).toBe(true);
    expect(proposeColumn('password_hash', output().tables[0])).toBeUndefined();
  });
  it('never interprets suggested mapping as a completed decision', () => {
    const p = progress(input(), output(), {});
    expect(p.complete).toBe(false);
    expect(p.reviewed).toBe(0);
    expect(p.total).toBe(6);
  });
  it('requires explicit choices even when a table is set UNMAPPED', () => {
    const p = progress(input(), output(), {
      patients: { target: null, columns: {} },
      old_unknown: { target: null, columns: {} },
    });
    expect(p.reviewed).toBe(2);
    expect(p.complete).toBe(false);
  });
  it('counts fully reviewed data but rejects credentials and collisions', () => {
    const s: SchemaInventory = input();
    const t: TargetInventory = output();
    const decisions = {
      patients: { target: 'patients', columns: { id: 'id', fullname: null, password_hash: null } },
      old_unknown: { target: null, columns: { code: null } },
    };
    expect(progress(s, t, decisions)).toMatchObject({ reviewed: 6, total: 6, collisions: 0,
      credentialBlocked: 0, complete: true });
    const duplicate = { ...decisions, patients: { ...decisions.patients,
      columns: { id: 'id', fullname: 'id', password_hash: null } } };
    expect(progress(s, t, duplicate).complete).toBe(false);
    const stolen = { ...decisions, patients: { ...decisions.patients,
      columns: { id: 'id', fullname: null, password_hash: 'name' } } };
    expect(progress(s, t, stolen).credentialBlocked).toBeGreaterThan(0);
  });
  it('denies secretary, untrusted roles, and partial dentists even with settings permission', () => {
    expect(canViewMigrationStudio(user({ permissions: { settings: true, admin: true } }))).toBe(false);
    expect(canViewMigrationStudio(user({ role: 'DENTISTE', employer_id: undefined }))).toBe(false);
    expect(canViewMigrationStudio(user({ role: 'DENTISTE', employer_id: 7 }))).toBe(false);
    expect(canViewMigrationStudio(null)).toBe(false);
  });
  it('recognizes only explicit superadmin, ADMIN or fully resolved owner dentist', () => {
    expect(canViewMigrationStudio(user({ is_superadmin: true }))).toBe(true);
    expect(canViewMigrationStudio(user({ role: 'ADMIN' }))).toBe(true);
    expect(canViewMigrationStudio(user({ role: 'DENTISTE', employer_id: null }))).toBe(true);
  });
});
