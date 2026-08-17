from backend.services.devis_document_lifecycle import (
    should_archive_financial_document,
    should_learn_financial_document,
    should_offer_financial_rdv_suggestion,
)


def test_devis_generation_does_not_archive_implicitly():
    assert not should_archive_financial_document("devis", archive_requested=False, preview=False)
    assert should_archive_financial_document("devis", archive_requested=True, preview=False)


def test_preview_never_archives_or_learns():
    assert not should_archive_financial_document("devis", archive_requested=True, preview=True)
    assert not should_learn_financial_document("devis", archived=False, preview=True)


def test_devis_learning_requires_real_archive():
    assert not should_learn_financial_document("devis", archived=False, preview=False)
    assert should_learn_financial_document("devis", archived=True, preview=False)


def test_financial_documents_do_not_invent_followup_interval():
    assert not should_offer_financial_rdv_suggestion("devis")
    assert not should_offer_financial_rdv_suggestion("honoraires")
