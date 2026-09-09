from pathlib import Path


def test_patient_snapshot_excludes_deleted_actes_and_hidden_generated_payments():
    source = Path('backend/routers/patient_financial_p6.py').read_text()
    assert 'models.Acte.deleted_at.is_(None)' in source
    assert 'accounting_service._visible_payment_filter()' in source


def test_stats_use_canonical_payment_visibility_and_active_actes():
    source = Path('backend/routers/stats.py').read_text()
    assert 'accounting_service._visible_payment_filter()' in source
    assert 'models.Acte.deleted_at.is_(None)' in source


def test_patient_appointment_hint_uses_same_financial_truth():
    source = Path('backend/routers/patients.py').read_text()
    assert 'accounting_service._visible_payment_filter()' in source
    assert 'models.Acte.deleted_at.is_(None)' in source
    assert 'models.DocumentArchive.status == models.DocumentStatus.ACTIF' in source
