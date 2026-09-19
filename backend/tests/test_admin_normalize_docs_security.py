"""Security contract for the legacy document-normalization admin route."""

from pathlib import Path


def test_normalize_docs_is_post_and_tenant_scoped():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "admin_legacy.py"
    ).read_text(encoding="utf-8")
    start = source.index('@router.post("/normalize-docs")')
    block = source[start:start + 2200]

    assert '@router.get("/normalize-docs")' not in source
    assert 'current_user.get_employer_id()' in block
    assert 'patient_id IN (SELECT id FROM patients WHERE employer_id = :employer_id)' in block
    assert block.count('{"employer_id": employer_id}') >= 2
    assert 'detail="Échec de normalisation des documents"' in block
    assert '"message": str(e)' not in block
