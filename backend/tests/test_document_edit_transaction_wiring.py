from pathlib import Path


def test_honoraires_generation_uses_shared_transaction_and_installment_reconciliation():
    source = Path('backend/routers/documents.py').read_text()

    assert 'commit=req.type not in ["honoraires", "note"]' in source
    assert 'actes, _ = persist_honoraires_lines(' in source
    assert 'reconcile_document_installments(' in source
    assert 'installments=installments_data if is_global else []' in source
    assert 'db.rollback()' in source


def test_archive_service_supports_caller_owned_transaction():
    source = Path('backend/services/archive_service.py').read_text()

    assert 'commit: bool = True' in source
    assert 'if commit:' in source
    assert 'self.db.flush()' in source
