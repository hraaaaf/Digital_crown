import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MigrationMappingStudio } from './MigrationMappingStudio';
import { fetchMigrationPreflight, runSyntheticStaffRehearsal } from './migrationGateway';

vi.mock('./migrationGateway', () => ({
  fetchMigrationPreflight: vi.fn(),
  runSyntheticStaffRehearsal: vi.fn(),
}));
afterEach(() => { cleanup(); vi.clearAllMocks(); });

const good = {
  status: 'construction',
  schema_revision_matches: true,
  declared_subset_matches: true,
  physical_subset_checked: true,
  full_schema_certified: false,
  authenticated_cabinet_scope: true,
  dry_run_real_data_available: false,
  import_permitted: false,
  blockers: ['REAL_IMPORT_NOT_IMPLEMENTED'],
  target_preview: {
    schema_revision: 'observed-read-only:neo000000027',
    tables: [{ name: 'patients', columns: [{ name: 'nom' }, { name: 'prenom' }] }],
  },
} as const;

describe('LOT05.5 Mapping Studio / authenticated backend readiness', () => {
  it('does not contact backend automatically or submit source inventory data', () => {
    render(<MigrationMappingStudio />);
    expect(fetchMigrationPreflight).not.toHaveBeenCalled();
    expect(runSyntheticStaffRehearsal).not.toHaveBeenCalled();
    expect(screen.getByText(/Import bloqué/)).toBeTruthy();
  });
  it('blocks the synthetic button for stale physical or Alembic schema', async () => {
    vi.mocked(fetchMigrationPreflight).mockResolvedValue({
      ...good, schema_revision_matches: false,
      physical_subset_checked: false,
      target_preview: null,
      blockers: ['PHYSICAL_SCHEMA_OR_ALEMBIC_HEAD_MISMATCH'],
    });
    render(<MigrationMappingStudio />);
    fireEvent.click(screen.getByRole('button', { name: 'Contrôler le backend sécurisé' }));
    await waitFor(() => expect(screen.getByText(/simulation bloquée/)).toBeTruthy());
    expect((screen.getByRole('button', { name: /Simuler 100 patients/ }) as HTMLButtonElement).disabled).toBe(true);
    expect(runSyntheticStaffRehearsal).not.toHaveBeenCalled();
  });
  it('allows synthetic-only rehearsal and explicitly retains import prohibition', async () => {
    vi.mocked(fetchMigrationPreflight).mockResolvedValue(good);
    vi.mocked(runSyntheticStaffRehearsal).mockResolvedValue({
      mode: 'SYNTHETIC_MEMORY_ONLY',
      source_patients: 100, source_appointments: 200,
      verified_patients: 100, verified_appointments: 200,
      verified_patient_links: 200, orphan_appointments: 0, cross_tenant_links: 0,
      after_rollback_patients: 0, after_rollback_appointments: 0,
      cabinet_rows_read: false, cabinet_rows_written: false,
      schema_migrated_by_alembic: false, import_permitted: false,
    });
    render(<MigrationMappingStudio />);
    fireEvent.click(screen.getByRole('button', { name: 'Contrôler le backend sécurisé' }));
    await waitFor(() => expect(screen.getByRole('button', { name: /Simuler 100 patients/ })).toBeTruthy());
    fireEvent.click(screen.getByRole('button', { name: /Simuler 100 patients/ }));
    await waitFor(() => expect(screen.getByText(/Simulation fictive : 100\/100/)).toBeTruthy());
    expect(screen.getByText(/Import réel toujours bloqué/)).toBeTruthy();
    expect(runSyntheticStaffRehearsal).toHaveBeenCalledTimes(1);
  });
  it('loads only the sanitized target preview and does not approve a mapping', async () => {
    vi.mocked(fetchMigrationPreflight).mockResolvedValue(good);
    render(<MigrationMappingStudio />);
    fireEvent.click(screen.getByRole('button', { name: 'Contrôler le backend sécurisé' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Charger l’aperçu cible observé' })).toBeTruthy());
    fireEvent.click(screen.getByRole('button', { name: 'Charger l’aperçu cible observé' }));
    expect(screen.getByText(/1 tables · revision observed-read-only/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Importer/ })).toBeNull();
  });
  it('fails closed on backend denied or unavailable', async () => {
    vi.mocked(fetchMigrationPreflight).mockRejectedValue(new Error('403'));
    render(<MigrationMappingStudio />);
    fireEvent.click(screen.getByRole('button', { name: 'Contrôler le backend sécurisé' }));
    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy());
    expect(screen.queryByRole('button', { name: /Simuler 100 patients/ })).toBeNull();
  });
});
