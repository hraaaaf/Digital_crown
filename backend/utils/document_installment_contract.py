from __future__ import annotations


def assert_document_installment_path_is_disabled(doc_type: str) -> None:
    """Reject the legacy `/documents/generate` installment path.

    Payment plans have dedicated authoritative endpoints:
    - `POST /installments/` for persistence;
    - `POST /installments/generate-preview` for draft PDFs;
    - `/installments/...` for tracking and collection.

    Keeping a second persistence/rendering path under `/documents/generate`
    would bypass the P5 contract and tenant-aware installment router.
    """
    if str(doc_type or "").strip().lower() == "echeancier":
        raise ValueError(
            "Le flux échéancier Document Studio historique est désactivé. Utilisez les endpoints /installments dédiés."
        )
