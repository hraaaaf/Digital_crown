from __future__ import annotations


def normalize_document_installment_plan_id(doc_type: str, data: object) -> int | None:
    """Require Document Studio installment generation to reference a saved plan.

    New plans and draft PDFs use the dedicated `/installments/` and
    `/installments/generate-preview` endpoints. `/documents/generate` must never
    create an installment plan from an untyped raw dictionary.
    """
    if str(doc_type or "").strip().lower() != "echeancier":
        return None

    if not isinstance(data, dict):
        raise ValueError(
            "Un échéancier Document Studio doit référencer un plan enregistré via plan_id."
        )

    raw_plan_id = data.get("plan_id")
    if isinstance(raw_plan_id, bool):
        raise ValueError("plan_id doit être un entier positif.")
    try:
        plan_id = int(raw_plan_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("plan_id doit être un entier positif.") from exc

    if plan_id <= 0 or str(raw_plan_id).strip() != str(plan_id):
        raise ValueError("plan_id doit être un entier positif.")
    return plan_id
