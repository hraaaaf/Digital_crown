from pathlib import Path


def test_honoraires_generation_uses_shared_transaction_and_installment_reconciliation():
    source = Path('backend/routers/documents.py').read_text()

    assert 'commit=req.type not in ["honoraires", "note"]' in source
    assert 'actes, _ = persist_honoraires_lines(' in source
    assert 'reconcile_document_installments(' in source
    assert 'installments=installments_data if is_global else []' in source
    assert 'db.rollback()' in source


def test_financial_edit_restores_files_only_before_database_commit():
    source = Path('backend/routers/documents.py').read_text()

    assert 'replacement_file_backups: list[tuple[pathlib.Path, Optional[bytes]]]' in source
    assert '_backup_financial_edit_files()' in source
    assert '_restore_financial_edit_files()' in source
    assert 'if content is None:' in source
    assert 'path.unlink()' in source
    assert 'backup_path != canonical_after' in source
    assert 'financial_edit_committed = True' in source
    assert 'if financial_edit_committed:' in source


def test_archive_service_supports_caller_owned_transaction():
    source = Path('backend/services/archive_service.py').read_text()

    assert 'commit: bool = True' in source
    assert 'if commit:' in source
    assert 'self.db.flush()' in source
