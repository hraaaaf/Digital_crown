from typing import Any


def _age_to_bracket(age: Any) -> str:
    """Convert exact age to decade bracket to reduce PII granularity."""
    try:
        a = int(age)
        low = (a // 10) * 10
        return f"{low}-{low + 9} ans"
    except (TypeError, ValueError):
        return "âge inconnu"


def mask_patient_context(raw: dict) -> dict:
    """
    Return a de-identified version of patient_info before sending to a local LLM.
    Removes name, contact details; keeps only clinically necessary fields.
    """
    return {
        "age_bracket": _age_to_bracket(raw.get("age")),
        "genre": raw.get("genre"),
        "antecedents": raw.get("antecedents", "Néant"),
    }
