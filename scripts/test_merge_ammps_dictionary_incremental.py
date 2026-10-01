#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("merge_ammps_dictionary_incremental.py")
spec = importlib.util.spec_from_file_location("merge_ammps_dictionary_incremental", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

existing = [
    {
        "nom": "CLAMOXYL",
        "dci": "AMOXICILLINE",
        "dosage": "500",
        "unite": "MG",
        "forme": "POUDRE POUR SUSPENSION BUVABLE",
        "presentation": "FLACON DE 60 ML",
        "epi": "GSK",
        "amm_status": "AMM ENREGISTREE",
        "market_status": "Commercialisé",
        "market_status_checked_at": "2026-09-15",
        "source_page_url": "https://old.example/page",
        "rcp_link_observed": True,
        "rcp_url": "https://ammps.gov.ma/rcp/verified.pdf",
        "rcp_snapshot_status": "VERIFIED",
        "rcp_sha256": "abc123",
        "rcp_checked_at": "2026-09-20",
    }
]
incoming_match = {
    "nom": "CLAMOXYL",
    "dci": "AMOXICILLINE",
    "dosage": "500",
    "unite": "MG",
    "forme": "POUDRE POUR SUSPENSION BUVABLE",
    "presentation": "FLACON DE 60 ML",
    "epi": "GSK",
    "market_status": "Commercialisé",
    "ppv": "30,00 DH",
    "ph": "20,00 DH",
    "source_page_url": "https://ammps.gov.ma/recherche-medicaments?search=CLAMOXYL",
    "rcp_link_observed": True,
    "rcp_url": None,
}
incoming_new = {
    "nom": "DOLIPRANE",
    "dci": "PARACETAMOL",
    "dosage": "1",
    "unite": "G",
    "forme": "COMPRIME EFFERVESCENT SECABLE",
    "presentation": "BOITE DE 8",
    "epi": "OPELLA HEALTHCARE",
    "market_status": "Commercialisé",
    "ppv": "20,00 DH",
    "ph": "12,50 DH",
    "source_page_url": "https://ammps.gov.ma/recherche-medicaments?search=DOLIPRANE",
    "rcp_link_observed": True,
    "rcp_url": None,
}
report = {
    "page_meta": {"updated_at": "01/10/2026"},
    "rows": [incoming_match, incoming_new],
}

merged1, diff1 = mod.merge_dictionary(existing, [report])
assert len(merged1) == 2
assert diff1["existing_count"] == 1
assert diff1["added_count"] == 1
assert diff1["updated_count"] == 1
assert diff1["deleted_count"] == 0
assert diff1["source_snapshot_dates"] == ["2026-10-01"]

clam = next(r for r in merged1 if r["nom"] == "CLAMOXYL")
assert clam["amm_status"] == "AMM ENREGISTREE"
assert clam["rcp_url"] == "https://ammps.gov.ma/rcp/verified.pdf"
assert clam["rcp_snapshot_status"] == "VERIFIED"
assert clam["rcp_sha256"] == "abc123"
assert clam["rcp_checked_at"] == "2026-09-20"
assert clam["market_status_checked_at"] == "2026-10-01"
assert clam["source_snapshot_date"] == "2026-10-01"
assert clam["ppv"] == "30,00 DH"

dol = next(r for r in merged1 if r["nom"] == "DOLIPRANE")
assert dol["amm_status"] == "PENDING_VERIFICATION"
assert dol["rcp_snapshot_status"] == "PENDING_DOWNLOAD"
assert dol["rcp_sha256"] is None
assert dol["market_status_checked_at"] == "2026-10-01"

# Idempotence: merging the same observations again changes nothing semantically.
merged2, diff2 = mod.merge_dictionary(merged1, [report])
assert merged2 == merged1
assert diff2["added_count"] == 0
assert diff2["updated_count"] == 0
assert diff2["deleted_count"] == 0

# Overlapping reports do not duplicate packages.
merged3, diff3 = mod.merge_dictionary(existing, [report, report])
assert len(merged3) == 2
assert diff3["incoming_unique_count"] == 2

print({
    "status": "PASS",
    "first_merge": diff1,
    "second_merge": diff2,
    "overlap_merge": diff3,
})
