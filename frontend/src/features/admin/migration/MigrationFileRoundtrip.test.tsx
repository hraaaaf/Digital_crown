import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MigrationMappingStudio } from './MigrationMappingStudio';
import { fetchMigrationPreflight, downloadOfficialSyntheticFile, dryrunOfficialSyntheticFile } from './migrationGateway';
vi.mock('./migrationGateway', () => ({
  fetchMigrationPreflight: vi.fn(), runSyntheticStaffRehearsal: vi.fn(),
  downloadOfficialSyntheticFile: vi.fn(), dryrunOfficialSyntheticFile: vi.fn(),
}));
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.clearAllMocks(); });
const ready = {
  status: 'construction', schema_revision_matches: true, declared_subset_matches: true,
  physical_subset_checked: true, full_schema_certified: false,
  authenticated_cabinet_scope: true, dry_run_real_data_available: false,
  import_permitted: false, blockers: ['REAL_IMPORT_NOT_IMPLEMENTED'],
  target_preview: { schema_revision: 'observed-read-only:neo000000027',
                    tables: [{name:'patients',columns:[{name:'nom'}]}] },
} as const;
async function mounted() {
  vi.mocked(fetchMigrationPreflight).mockResolvedValue(ready);
  render(<MigrationMappingStudio />);
  fireEvent.click(screen.getByRole('button',{name:'Contrôler le serveur sécurisé'}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'Télécharger la base SQLite fictive'})).toBeTruthy());
}
describe('LOT05.6 synthetic-only SQLite file staff workflow', () => {
  it('keeps the real-import ban immediately visible and formats the fake-only warning', () => {
    render(<MigrationMappingStudio />);
    const note=screen.getByRole('note',{name:'Limites de certification'});
    expect(note.textContent).toContain('Import réel interdit.');
    expect(note.textContent).toContain('base entièrement fictive fournie par Digital Crown');
    expect(note.textContent).not.toContain('**entièrement fictive');
    const warningDetail=screen.getByText('Précautions et limites de la simulation');
    expect(warningDetail.closest('details')?.open).toBe(false);
    fireEvent.click(warningDetail);
    expect(warningDetail.closest('details')?.open).toBe(true);
    expect(note.textContent).toContain('Ne sélectionnez jamais de véritable export patient');
  });
  it('never exposes file input before preflight and never uploads automatically', () => {
    render(<MigrationMappingStudio />);
    expect(screen.queryByLabelText('Fichier SQLite fictif Digital Crown')).toBeNull();
    expect(dryrunOfficialSyntheticFile).not.toHaveBeenCalled();
  });
  it('keeps file selection disabled until official download', async () => {
    await mounted();
    expect((screen.getByLabelText('Fichier SQLite fictif Digital Crown') as HTMLInputElement).disabled).toBe(true);
  });
  it('allows only downloaded demo file to be simulated', async () => {
    await mounted();
    vi.stubGlobal('URL', {createObjectURL: vi.fn(()=> 'blob:fake'), revokeObjectURL: vi.fn()});
    vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
    vi.mocked(downloadOfficialSyntheticFile).mockResolvedValue({bytes:new ArrayBuffer(512),sha:'a'.repeat(64)});
    vi.mocked(dryrunOfficialSyntheticFile).mockResolvedValue({
      mode:'OFFICIAL_SYNTHETIC_SQLITE_FILE_ONLY',source_sha256:'a'.repeat(64),
      source_patients:100,source_appointments:200,
      verified_patients:100,verified_appointments:200,verified_patient_links:200,
      orphan_appointments:0,cross_tenant_links:0,
      after_rollback_patients:0,after_rollback_appointments:0,
      source_persisted:false,cabinet_rows_read:false,cabinet_rows_written:false,
      import_permitted:false,
    });
    fireEvent.click(screen.getByRole('button',{name:'Télécharger la base SQLite fictive'}));
    await waitFor(()=>expect((screen.getByLabelText('Fichier SQLite fictif Digital Crown') as HTMLInputElement).disabled).toBe(false));
    const file = new File([new Uint8Array(512)],'digital-crown-synthetic-100x200.db');
    fireEvent.change(screen.getByLabelText('Fichier SQLite fictif Digital Crown'),{target:{files:[file]}});
    await waitFor(()=>expect(screen.getByText(/Fichier SQLite fictif vérifié : 100\/100/)).toBeTruthy());
    expect(dryrunOfficialSyntheticFile).toHaveBeenCalledWith(file,'a'.repeat(64));
    vi.unstubAllGlobals();
  });
});
