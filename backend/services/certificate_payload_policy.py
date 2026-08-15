from __future__ import annotations


CERTIFICATE_TYPE_WORK_STOP = "Arrêt de travail"
CERTIFICATE_TYPE_PRESENCE = "Certificat de Présence"
CERTIFICATE_TYPE_FREE = "Certificat médical"

LEGACY_WORK_STOP_TYPES = {
    "Repos médical",
    "Certificat de Repos",
    "Repos Post-Opératoire",
    "Suite d'Intervention",
}


def _field_was_explicitly_provided(data, field_name: str) -> bool:
    """Distingue une valeur réellement envoyée d'un default injecté par Pydantic.

    Les objets internes/legacy sans `model_fields_set` sont considérés explicites ;
    les modèles Pydantic issus de l'API doivent avoir reçu le champ dans le payload.
    """
    fields_set = getattr(data, "model_fields_set", None)
    if fields_set is None:
        return True
    return field_name in fields_set


def normalize_and_validate_certificate_data(data):
    """Normalise les anciens certificats et refuse les états incohérents avant PDF.

    La politique reflète le contrat frontend P3 mais reste indépendante du client :
    un appel API direct ne doit jamais réintroduire un fallback implicite vers un
    arrêt de travail ou une durée clinique par défaut.
    """
    if not _field_was_explicitly_provided(data, "reason"):
        raise ValueError("La nature du certificat doit être choisie explicitement par le praticien.")

    raw_reason = str(getattr(data, "reason", "") or "").strip()
    raw_content = str(getattr(data, "content", "") or "")

    if not raw_reason:
        raise ValueError("La nature du certificat doit être choisie explicitement par le praticien.")

    if raw_reason in LEGACY_WORK_STOP_TYPES:
        reason = CERTIFICATE_TYPE_WORK_STOP
    elif raw_reason == CERTIFICATE_TYPE_WORK_STOP:
        reason = CERTIFICATE_TYPE_WORK_STOP
    elif raw_reason == CERTIFICATE_TYPE_PRESENCE:
        reason = CERTIFICATE_TYPE_PRESENCE
    elif raw_reason in {CERTIFICATE_TYPE_FREE, "Autre"}:
        reason = CERTIFICATE_TYPE_FREE
    else:
        # Un ancien motif libre ne doit jamais devenir silencieusement un arrêt.
        reason = CERTIFICATE_TYPE_FREE
        if not raw_content.strip():
            raw_content = raw_reason

    if reason == CERTIFICATE_TYPE_WORK_STOP:
        if not _field_was_explicitly_provided(data, "days"):
            raise ValueError("La durée de l'arrêt de travail doit être saisie explicitement par le praticien.")
        days = getattr(data, "days", None)
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 365:
            raise ValueError("La durée de l'arrêt de travail doit être un entier compris entre 1 et 365 jours.")
        data.days = days
        data.content = None
    elif reason == CERTIFICATE_TYPE_PRESENCE:
        data.days = 0
        data.start_date = None
        data.content = None
    else:
        content = raw_content.strip()
        if not content:
            raise ValueError("Le contenu du certificat médical est requis.")
        data.days = 0
        data.start_date = None
        data.content = content

    data.reason = reason
    return data
