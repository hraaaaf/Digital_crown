import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MappingStudio } from './MappingStudio';
import {
  evaluateMapping, inspectMetadataShape, setColumnChoice, setTableChoice,
  suggestExact, syntheticSource, syntheticTarget, type MappingChoices,
} from './mappingStudioModel';

afterEach(() => cleanup());

const select = (id: string, value: string) => {
  const input = document.getElementById(id) as HTMLSelectElement | null;
  if (!input) throw new Error('Test missing select: ' + id);
  fireEvent.change(input, { target: { value } });
};
const start = () => {
  render(<MappingStudio />);
  fireEvent.click(screen.getByRole('button', { name: /Choisir les correspondances/i }));
};

describe('V1.5-05.2-B inert Mapping Studio', () => {
  it('warns in French that source/target are fictitious and import is impossible', () => {
    render(<MappingStudio />);
    expect(screen.getByText(/En cours de construction — import strictement désactivé/)).toBeTruthy();
    expect(screen.getByText(/Aucune ligne ou relation réellement vérifiée/)).toBeTruthy();
    expect(screen.getByText(/Ne reflète pas le vrai schéma SQLAlchemy/)).toBeTruthy();
    expect(screen.queryByText(/Importer les données — désactivé/)).toBeNull();
  });
  it('only suggests, never preselects, an exact match', () => {
    start();
    expect(screen.getByText(/Proposé : patients/)).toBeTruthy();
    expect((document.getElementById('table-choice-0') as HTMLSelectElement).value).toBe('');
    expect((document.getElementById('column-choice-0-0') as HTMLSelectElement).disabled).toBe(true);
    expect((screen.getByRole('button', { name: /Contrôler le brouillon/i }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('requires explicit UNMAPPED for every column even when parent table is skipped', () => {
    start();
    select('table-choice-2', '__unmapped__');
    expect((document.getElementById('column-choice-2-0') as HTMLSelectElement).value).toBe('');
    select('column-choice-2-0', '__unmapped__');
    expect(screen.getByText(/Décisions : 2\/11/)).toBeTruthy();
    expect((screen.getByRole('button', { name: /Contrôler le brouillon/i }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('can review a complete synthetic-only draft but never import or persist it', () => {
    const fakeNetwork = vi.spyOn(window, 'fetch');
    start();
    select('table-choice-0', 'patients');
    select('column-choice-0-0', 'id');
    select('column-choice-0-1', 'name');
    select('column-choice-0-2', 'legacy_no');
    select('column-choice-0-3', '__unmapped__');
    select('table-choice-1', 'appointments');
    select('column-choice-1-0', 'id');
    select('column-choice-1-1', 'patient_id');
    select('column-choice-1-2', '__unmapped__');
    select('table-choice-2', '__unmapped__');
    select('column-choice-2-0', '__unmapped__');
    expect(screen.getByText('Décisions : 11/11')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Contrôler le brouillon/i }));
    expect(screen.getByTestId('mapping-review-step')).toBeTruthy();
    expect((screen.getByTestId('migration-import-disabled') as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText(/Aucune approbation administrateur/i)).toBeTruthy();
    expect(fakeNetwork).not.toHaveBeenCalled();
    fakeNetwork.mockRestore();
  });
  it('invalidates all previously chosen columns when a table mapping is changed', () => {
    start();
    select('table-choice-0', 'patients');
    select('column-choice-0-0', 'id');
    expect((document.getElementById('column-choice-0-0') as HTMLSelectElement).value).toBe('id');
    select('table-choice-0', 'clinical_notes');
    expect((document.getElementById('column-choice-0-0') as HTMLSelectElement).value).toBe('');
  });
  it('flags collisions rather than unlocking the review', () => {
    start();
    select('table-choice-0', 'patients');
    select('table-choice-1', 'patients');
    expect(screen.getByRole('alert').textContent).toMatch(/TABLE_COLLISION/);
    expect((screen.getByRole('button', { name: /Contrôler le brouillon/i }) as HTMLButtonElement).disabled).toBe(true);
  });
  it('does not map a credential as a live password, even via proposal', () => {
    start();
    select('table-choice-0', 'patients');
    const secretSelect = document.getElementById('column-choice-0-3') as HTMLSelectElement;
    expect(secretSelect.querySelectorAll('option')).toHaveLength(2);
    expect(secretSelect.textContent).not.toMatch(/id|name|legacy_no/);
    expect(suggestExact('password_hash', ['password_hash'])).toBeNull();
  });
  it('reset drops all decisions and goes back to the inventory', () => {
    start();
    select('table-choice-0', 'patients');
    fireEvent.click(screen.getByRole('button', { name: /Réinitialiser/i }));
    expect(screen.getByTestId('mapping-source-step')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Choisir les correspondances/i }));
    expect((document.getElementById('table-choice-0') as HTMLSelectElement).value).toBe('');
  });
  it('metadata guard rejects forged approved source or untrusted manifest shape', () => {
    expect(inspectMetadataShape({ ...syntheticSource, import_permitted: true } as never, syntheticTarget)).toContain('SOURCE_UNVERIFIED');
    expect(inspectMetadataShape(syntheticSource, { ...syntheticTarget, server_verified: true } as never)).toContain('TARGET_SCHEMA_AMBIGUOUS');
    expect(inspectMetadataShape(syntheticSource, {
      ...syntheticTarget, tables: [{ name: 'patients', columns: ['id', 'ID'] }],
    })).toContain('TARGET_SCHEMA_AMBIGUOUS');
  });
  it('unmapped source decisions never imply authorization', () => {
    let choices: MappingChoices = {};
    choices = setTableChoice(choices, 'patients', null);
    for (const c of syntheticSource.tables[0].columns) choices = setColumnChoice(choices, 'patients', c.name, null);
    const status = evaluateMapping(syntheticSource, syntheticTarget, choices);
    expect(status.import_permitted).toBe(false);
    expect(status.admin_approved).toBe(false);
    expect(status.dry_run_completed).toBe(false);
  });
});
