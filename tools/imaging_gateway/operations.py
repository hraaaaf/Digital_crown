"""LOT06-F: local operator-facing projection. Read only, never clinical confirmation.

The existing local SQLite spool is the only information source.  This module
cannot attach a patient, create an upload ticket or claim server success.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from html import escape
from typing import Literal, Mapping


class OperationsRejected(ValueError):
    pass


@dataclass(frozen=True)
class OperatorNotice:
    code: str
    severity: Literal["STOP", "ACTION", "INFO"]
    title: str
    instruction: str


# Static controlled vocabulary: never interpolate filenames, hashes, patients or DB keys.
_CAPACITY_CODES = {
    "QUEUE_ITEM_LIMIT",
    "SPOOL_BYTE_LIMIT",
    "DISK_RESERVE_LIMIT",
    "DISK_FULL",
    "SPOOL_DIRECTORY_LIMIT",
}
_KNOWN_STATES = frozenset({
    "PENDING_CONFIRMATION", "QUARANTINED", "RETRY_PENDING", "BLOCKED",
    "UNRECOGNIZED_STATE",
})


def project_operations(health: Mapping[str, object]) -> dict:
    """Build an auditable, no-PHI operator checklist from aggregate counters."""
    if not isinstance(health, Mapping):
        raise OperationsRejected("INVALID_HEALTH")
    states = health.get("states")
    if not isinstance(states, dict):
        raise OperationsRejected("INVALID_COUNTS")
    counts = {}
    for key, value in states.items():
        if key not in _KNOWN_STATES or type(value) is not int or value < 0:
            raise OperationsRejected("UNTRUSTED_COUNTS")
        counts[key] = value
    queued = health.get("queued_items")
    if type(queued) is not int or queued < 0 or sum(counts.values()) != queued:
        raise OperationsRejected("INCONSISTENT_TOTAL")
    if health.get("state") not in {"READY", "BACKPRESSURE"}:
        raise OperationsRejected("UNKNOWN_HEALTH")
    issue = health.get("last_capacity_issue")
    if issue is not None and issue not in _CAPACITY_CODES:
        raise OperationsRejected("UNKNOWN_CAPACITY_ISSUE")
    orphan = health.get("orphan_files")
    if type(orphan) is not int or orphan < 0:
        raise OperationsRejected("INVALID_ORPHAN_TOTAL")
    for name in ("spool_bytes", "orphan_bytes", "free_bytes",
                 "max_spool_bytes", "max_queue_items", "min_free_bytes"):
        val = health.get(name)
        if type(val) is not int or val < 0:
            raise OperationsRejected("INVALID_CAPACITY_METRIC")
    if health["orphan_bytes"] > health["spool_bytes"]:
        raise OperationsRejected("INCONSISTENT_SPOOL")
    notes = []

    def notice(code, severity, title, instruction):
        notes.append(OperatorNotice(code, severity, title, instruction))

    if health["state"] == "BACKPRESSURE":
        notice("LOCAL_BACKPRESSURE", "STOP", "Collecte locale sous pression",
               "Vérifier le disque et les quotas du poste. Conserver les originaux ; "
               "aucune suppression automatique ni transfert clinique.")
    if counts.get("UNRECOGNIZED_STATE", 0):
        notice("UNKNOWN_QUEUE_STATE", "STOP", "État de file inconnu",
               "Bloquer toute reprise automatique et faire examiner le journal local "
               "par l'administrateur habilité.")
    if orphan:
        notice("ORPHAN_SPOOL", "ACTION", "Fichiers chiffrés sans ligne de file",
               "Vérifier la reprise après incident. Ne pas effacer manuellement "
               "les fichiers sans procédure d'audit.")
    if counts.get("BLOCKED", 0):
        notice("RETRY_EXHAUSTED", "ACTION", "Acquisitions locales bloquées",
               "Examiner le journal du poste et traiter la cause ; aucune "
               "relance clinique n'est autorisée par cette vue.")
    if counts.get("QUARANTINED", 0):
        notice("QUARANTINE_REVIEW", "ACTION", "Fichiers en quarantaine",
               "Contrôler le format avec une procédure autorisée. "
               "Ne pas attribuer automatiquement de patient.")
    if counts.get("RETRY_PENDING", 0):
        notice("RETRY_PENDING", "INFO", "Reprise locale en attente",
               "Vérifier la stabilité de l'agent et du stockage. "
               "Un réessai local n'est pas un accusé serveur.")
    if counts.get("PENDING_CONFIRMATION", 0):
        notice("HUMAN_LINK_REQUIRED", "ACTION", "Association patient non confirmée",
               "Consulter ultérieurement le patient et le rendez-vous côté serveur "
               "avec une session autorisée. Aucun patient n'est associé ici.")
    notice("CLINICAL_INTEGRATION_PENDING", "STOP", "Intégration clinique en cours de construction",
           "Confirmation humaine, autorisation appareil, envoi et accusé serveur "
           "ne sont pas disponibles depuis cette interface.")

    return {
        "contract": "DC06F-LOCAL-OPERATIONS-V1",
        "mode": "READ_ONLY",
        "clinical_status": "NOT_CONNECTED",
        "upload_permitted": False,
        "patient_confirmation_permitted": False,
        "server_confirmed": False,
        "queued_items": queued,
        "counts": counts,
        "orphan_files": orphan,
        "notices": [vars(n) for n in notes],
    }


def render_operations_text(view: Mapping[str, object]) -> str:
    """Human-readable, narrow-terminal friendly; all text comes from contracts."""
    if view.get("contract") != "DC06F-LOCAL-OPERATIONS-V1":
        raise OperationsRejected("INVALID_VIEW")
    lines = [
        "DIGITAL CROWN · IMAGERIE / POSTE LOCAL",
        "Mode : LECTURE SEULE · AUCUNE IMPORTATION CLINIQUE",
        f"File locale : {view['queued_items']} élément(s)",
        f"Fichiers chiffrés orphelins : {view['orphan_files']}",
    ]
    for notice in view["notices"]:
        lines.append(f"[{notice['severity']}] {notice['title']}")
        lines.append(f"  {notice['instruction']}")
    return "\n".join(lines)


def render_operations_json(view: Mapping[str, object]) -> str:
    if view.get("contract") != "DC06F-LOCAL-OPERATIONS-V1":
        raise OperationsRejected("INVALID_VIEW")
    return json.dumps(view, ensure_ascii=False, sort_keys=True, indent=2)


def render_operations_html(view: Mapping[str, object]) -> str:
    """Offline responsive read-only preview, never mounted on clinical routes.

    All displayed content originates from the validated projection's finite
    operator vocabulary; no source filenames, patient details or image bytes.
    There are intentionally NO submit buttons, forms, fetch, or JavaScript.
    """
    if view.get("contract") != "DC06F-LOCAL-OPERATIONS-V1":
        raise OperationsRejected("INVALID_VIEW")
    cards = []
    for entry in view["notices"]:
        if entry["severity"] not in {"STOP", "ACTION", "INFO"}:
            raise OperationsRejected("INVALID_NOTICE")
        severity = entry["severity"].lower()
        cards.append(
            '<article class="notice ' + severity + '">'
            '<p class="level">' + escape(entry["severity"]) + '</p>'
            '<h2>' + escape(entry["title"]) + '</h2>'
            '<p>' + escape(entry["instruction"]) + '</p>'
            '</article>'
        )
    return """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>Digital Crown · Imagerie locale · Aperçu lecture seule</title>
<style>
:root { color-scheme: light; font-family: system-ui,-apple-system,Segoe UI,sans-serif; }
* { box-sizing: border-box; }
body { margin: 0; min-width: 280px; background: #f6f7fa; color: #182536; }
main { width: min(1120px,100%); margin: 0 auto; padding: 32px 28px 64px; }
header { padding: 26px; border-radius: 20px; background: #172b3c; color: white; }
.eyebrow { font-size: 12px; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
h1 { font-size: clamp(24px,3.2vw,38px); line-height: 1.2; margin: 8px 0 14px; }
p { line-height: 1.6; margin: 8px 0 0; }
.locked { padding: 12px 14px; border: 1px solid #cbdce6; border-radius: 12px;
          margin-top: 18px; background: #ebf4fa; color: #13354c; font-weight: 750; }
.summary { display: flex; flex-wrap: wrap; gap: 14px; margin: 24px 0; }
.metric { flex: 1 1 220px; border: 1px solid #dce3ea; border-radius: 16px;
          background: white; padding: 18px; }
.metric b { display: block; font-size: 28px; margin-top: 8px; }
.notices { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16px; }
.notice { background: white; border: 1px solid #dce3ea; border-left: 5px solid #64748b;
          border-radius: 14px; padding: 18px; min-width: 0; overflow-wrap: anywhere; }
.notice.stop { border-left-color: #b42318; }
.notice.action { border-left-color: #a36316; }
.notice.info { border-left-color: #246b9e; }
.notice h2 { font-size: 18px; margin: 6px 0; }
.level { font-size: 11px; font-weight: 800; letter-spacing: .1em; }
footer { margin-top: 30px; color: #536372; font-size: 13px; }
@media (max-width: 600px) {
 main { padding: 14px 14px 36px; }
 header { padding: 20px; border-radius: 14px; }
 .summary { margin: 16px 0; gap: 10px; }
 .notices { grid-template-columns: minmax(0,1fr); gap: 10px; }
 .notice { padding: 16px; }
}
</style>
</head>
<body>
<main data-imaging-operations="read-only">
<header>
<p class="eyebrow">Digital Crown · Poste Imagerie</p>
<h1>État des acquisitions locales</h1>
<p>Ce tableau décrit uniquement le spool chiffré sur ce poste.</p>
<div class="locked" role="status">Lecture seule · Association patient et envoi clinique en cours de construction</div>
</header>
<div class="summary" aria-label="Compteurs locaux">
<section class="metric"><span>Acquisitions en file locale</span><b>""" + escape(str(view["queued_items"])) + """</b></section>
<section class="metric"><span>Fichiers chiffrés orphelins</span><b>""" + escape(str(view["orphan_files"])) + """</b></section>
</div>
<section class="notices" aria-label="Actions de vérification">
""" + "\n".join(cards) + """
</section>
<footer>Aucune image transmise, aucun patient confirmé, aucun accusé serveur produit depuis cette vue.</footer>
</main>
</body>
</html>
"""
