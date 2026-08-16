import pytest

from backend.utils.document_installment_contract import assert_document_installment_path_is_disabled


def test_non_installment_document_is_allowed():
    assert assert_document_installment_path_is_disabled("devis") is None


@pytest.mark.parametrize("doc_type", ["echeancier", "ECHEANCIER", " echeancier "])
def test_legacy_installment_document_path_is_rejected(doc_type):
    with pytest.raises(ValueError):
        assert_document_installment_path_is_disabled(doc_type)
