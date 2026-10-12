import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { MigrationMappingStudio } from './MigrationMappingStudio';
import { type SchemaInventory, type TargetInventory } from './MappingStudioPolicy';

const source: SchemaInventory = {
  sourceSha256: 'a'.repeat(64), sourceFormat: 'sqlite-copy',
  tables: [
    { name: 'patients', columns: [
      { name: 'id', declared_type: 'INT' },
      { name: 'fullname', declared_type: 'TEXT' },
      { name: 'password_hash', declared_type: 'TEXT' },
    ] },
    { name: 'legacy_unmapped', columns: [{ name: 'code', declared_type: 'TEXT' }] },
  ],
};
const target: TargetInventory = {
  schemaRevision: 'neo000000027',
  tables: [{ name: 'patients', columns: [{ name: 'id' }, { name: 'name' }] }],
};
afterEach(cleanup);
function launch() { render(<MigrationMappingStudio initialSource={source} initialTarget={target} />); }
function review() {
  fireEvent.click(screen.getByRole('button', { name: /Examiner les correspondances/i }));
}
function choose(label: string, value: string) {
  fireEvent.change(screen.getByRole('combobox', { name: label }), { target: { value } });
}
function completed() {
  review();
  choose('Destination table patients', 'patients');
  choose('Colonne patients.id', 'id');
  choose('Colonne patients.fullname', '__unmapped__');
  choose('Colonne patients.password_hash', '__unmapped__');
  choose('Destination table legacy_unmapped', '__unmapped__');
  choose('Colonne legacy_unmapped.code', '__unmapped__');
}

describe('LOT05.2-B1 Mapping Studio staff wizard', () => {
  it('has a real accessible three-step interface with no data transmission or import control', () => {
    launch();
    expect(screen.getByRole('heading', { name: 'Mapping Studio' })).toBeTruthy();
    expect(screen.getByRole('note', { name: 'Limites de certification' })).toBeTruthy();
    expect(screen.getByText(/aucune approbation administrateur ni dry-run réel/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Examiner les correspondances/i })).not.toHaveProperty('disabled', true);
    expect(screen.queryByRole('button', { name: /Importer/i })).toBeNull();
  });
  it('makes exact-name suggestions visible but never pre-selects them', () => {
    launch(); review();
    expect(screen.getAllByText('Suggestion : patients').length).toBeGreaterThan(0);
    expect((screen.getByRole('combobox', { name: 'Destination table patients' }) as HTMLSelectElement).value).toBe('');
    expect((screen.getByRole('combobox', { name: 'Colonne patients.id' }) as HTMLSelectElement).disabled).toBe(true);
    expect((screen.getByRole('button', { name: /^Vérifier/ }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('requires all table/column reviews and then still forbids the import', () => {
    launch(); completed();
    const verify = screen.getByRole('button', { name: /^Vérifier/ }) as HTMLButtonElement;
    expect(verify.disabled).toBe(false);
    fireEvent.click(verify);
    expect(screen.getByText(/NON VALIDÉ : aucune approbation/i)).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Importer — indisponible' }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText('6')).toBeTruthy();
  });
  it('does not silently select destination for sensitive legacy credentials', () => {
    launch(); review();
    choose('Destination table patients', 'patients');
    expect(screen.getByText(/Secret : mapping interdit/)).toBeTruthy();
    const select = screen.getByRole('combobox', { name: 'Colonne patients.password_hash' }) as HTMLSelectElement;
    expect([...select.options].map(item => item.value)).toEqual(['', '__unmapped__']);
  });
  it('changing target table invalidates prior column decisions', () => {
    launch(); review();
    choose('Destination table patients', 'patients');
    choose('Colonne patients.id', 'id');
    choose('Destination table patients', '__unmapped__');
    expect((screen.getByRole('combobox', { name: 'Colonne patients.id' }) as HTMLSelectElement).value).toBe('');
    expect((screen.getByRole('button', { name: /^Vérifier/ }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('a delayed older file read cannot overwrite a newer source inventory', async () => {
    launch();
    let resolveOld: ((v: string) => void) | undefined;
    const older = new File(['old'], 'old.json', { type: 'application/json' });
    const newer = new File(['new'], 'new.json', { type: 'application/json' });
    Object.defineProperty(older, 'text', {
      value: () => new Promise<string>(resolve => { resolveOld = resolve; }),
    });
    const newerReport = {
      dialect_declared: 'sqlite', source_format: 'sqlite-copy',
      sha256: 'b'.repeat(64), file_size_bytes: 123, row_counts: null,
      warnings: [], mapping_approved: false, dry_run_completed: false, import_permitted: false,
      tables: [{ source_name: 'patients', columns: [{ name: 'id', declared_type: 'INT' }] }],
    };
    Object.defineProperty(newer, 'text', { value: async () => JSON.stringify(newerReport) });
    const fileInput = screen.getByLabelText('Rapport source JSON');
    fireEvent.change(fileInput, { target: { files: [older] } });
    fireEvent.change(fileInput, { target: { files: [newer] } });
    await waitFor(() => expect(screen.getByText(/SHA bbbbbbbbbbbb/)).toBeTruthy());
    resolveOld?.(JSON.stringify({ ...newerReport, sha256: 'a'.repeat(64) }));
    await waitFor(() => expect(screen.getByText(/SHA bbbbbbbbbbbb/)).toBeTruthy());
    expect(screen.queryByText(/SHA aaaaaaaaaaaa/)).toBeNull();
  });
  it('a newly rejected source inventory clears the old source and all decisions', async () => {
    launch(); completed();
    fireEvent.click(screen.getByRole('button', { name: 'Inventaires' }));
    const file = new File(['{"rows":[{"patient":"PRIVATE"}]}'], 'unsafe.json', { type: 'application/json' });
    Object.defineProperty(file, 'text', { value: async () => '{"rows":[{"patient":"PRIVATE"}]}' });
    fireEvent.change(screen.getByLabelText('Rapport source JSON'), { target: { files: [file] } });
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('UNEXPECTED_METADATA_FIELD'));
    expect(screen.getByText('Aucune source chargée')).toBeTruthy();
    expect((screen.getByRole('button', { name: /Examiner les correspondances/i }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByText('PRIVATE')).toBeNull();
  });
});
