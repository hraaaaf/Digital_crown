"""Lifecycle policy for Document Studio financial documents.

A Devis is a proposal. Generating or previewing it is not proof of performed care,
and must not implicitly archive, train habits, or schedule a follow-up visit.
"""

FINANCIAL_DOCUMENT_TYPES = {"devis", "honoraires", "note"}
LEGACY_AUTO_ARCHIVE_TYPES = {"honoraires", "note"}


def should_archive_financial_document(doc_type: str, archive_requested: bool, preview: bool) -> bool:
    if preview:
        return False
    if archive_requested:
        return True
    return doc_type in LEGACY_AUTO_ARCHIVE_TYPES


def should_learn_financial_document(doc_type: str, archived: bool, preview: bool) -> bool:
    return doc_type in FINANCIAL_DOCUMENT_TYPES and archived and not preview


def should_offer_financial_rdv_suggestion(doc_type: str) -> bool:
    """No generic financial document may invent a follow-up interval.

    Appointment timing needs an explicit clinical protocol / performed-care event.
    """
    return False
