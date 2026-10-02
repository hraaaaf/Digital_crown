#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("probe_ammps_dictionary_sync.py")
spec = importlib.util.spec_from_file_location("probe_ammps_dictionary_sync", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

HTML = """
<html><body>
<div>Base de données mise à jour le 01/10/2026</div>
<div>18 médicament(s) trouvé(s)</div>

<div class="medicament-card" data-bs-target="#medicamentModal1">
  <div class="medicament-title">DOLIPRANE</div>
</div>
<div id="medicamentModal1">
  <div class="ammps-modal-item"><span class="ammps-modal-label">Substance active</span><span class="ammps-modal-value">PARACETAMOL</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">EPI</span><span class="ammps-modal-value">OPELLA HEALTHCARE</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Dosage</span><span class="ammps-modal-value">1 G</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Forme</span><span class="ammps-modal-value">COMPRIME EFFERVESCENT SECABLE</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Présentation</span><span class="ammps-modal-value">BOITE DE 8</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Statut commercialisation</span><span class="ammps-modal-value">Commercialisé</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">PPV</span><span class="ammps-modal-value">20,00 DH</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">PH</span><span class="ammps-modal-value">12,50 DH</span></div>
  <a href="javascript:void(0)" aria-disabled="true">Télécharger RCP</a>
</div>

<div class="medicament-card" data-bs-target="#medicamentModal2">
  <div class="medicament-title">TEST RCP</div>
</div>
<div id="medicamentModal2">
  <div class="ammps-modal-item"><span class="ammps-modal-label">Substance active</span><span class="ammps-modal-value">TEST</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">EPI</span><span class="ammps-modal-value">LAB</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Dosage</span><span class="ammps-modal-value">500 MG</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Forme</span><span class="ammps-modal-value">COMPRIME</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Présentation</span><span class="ammps-modal-value">BOITE DE 10</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Statut commercialisation</span><span class="ammps-modal-value">Commercialisé</span></div>
  <a href="https://ammps.gov.ma/sites/default/files/rcp/test.pdf">Télécharger RCP</a>
</div>

<a class="page-link" rel="next" href="/recherche-medicaments?search=DOLIPRANE&page=2">Suivant</a>
</body></html>
"""


def assert_eq(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


rows1, meta1 = mod.parse_page(HTML, "https://ammps.gov.ma/recherche-medicaments?search=DOLIPRANE")
rows2, meta2 = mod.parse_page(HTML, "https://ammps.gov.ma/recherche-medicaments?search=DOLIPRANE")

assert_eq(len(rows1), 2, "row count")
assert_eq(meta1["reported_total"], 18, "reported total")
assert_eq(meta1["updated_at"], "01/10/2026", "updated date")
assert meta1["next_page_url"].endswith("page=2")

dol = rows1[0]
assert_eq(dol["nom"], "DOLIPRANE", "brand")
assert_eq(dol["dci"], "PARACETAMOL", "dci")
assert_eq(dol["dosage"], "1", "dosage")
assert_eq(dol["unite"], "G", "unit")
assert_eq(dol["forme"], "COMPRIME EFFERVESCENT SECABLE", "form")
assert_eq(dol["presentation"], "BOITE DE 8", "presentation")
assert dol["rcp_link_observed"] is True
assert dol["rcp_url"] is None

rcp = rows1[1]
assert_eq(rcp["rcp_url"], "https://ammps.gov.ma/sites/default/files/rcp/test.pdf", "official rcp url")
assert mod.official_url("https://evil.example/rcp.pdf") is None
assert mod.official_url("http://ammps.gov.ma/rcp.pdf") is None

# Stable identity: same source data => same ID; presentation change => new ID.
ids1 = [row["regulatory_presentation_id"] for row in rows1]
ids2 = [row["regulatory_presentation_id"] for row in rows2]
assert_eq(ids1, ids2, "stable ids")
changed = dict(dol)
changed["presentation"] = "BOITE DE 16"
assert mod.presentation_id(changed) != dol["regulatory_presentation_id"]

# Repeat parse is idempotent and metadata is stable.
assert_eq(rows1, rows2, "parse idempotence")
assert_eq(meta1, meta2, "metadata idempotence")

print({
    "status": "PASS",
    "rows": len(rows1),
    "reported_total": meta1["reported_total"],
    "updated_at": meta1["updated_at"],
    "stable_ids": ids1,
})
