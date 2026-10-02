#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("inspect_ammps_rcp_transport.py")
spec = importlib.util.spec_from_file_location("inspect_ammps_rcp_transport", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

html = """
<html><body>
<div class="medicament-card" data-bs-target="#m1">
  <div class="medicament-title">AMOXICILLINE SP</div>
</div>
<div id="m1">
  <div class="ammps-modal-item"><span class="ammps-modal-label">Substance active</span><span class="ammps-modal-value">AMOXICILLINE</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">EPI</span><span class="ammps-modal-value">AMANYS PHARMA</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Dosage</span><span class="ammps-modal-value">1 G</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Forme</span><span class="ammps-modal-value">COMPRIME DISPERSIBLE</span></div>
  <div class="ammps-modal-item"><span class="ammps-modal-label">Présentation</span><span class="ammps-modal-value">BOITE DE 12</span></div>
  <button class="btn-rcp" data-file="/docs/rcp/amox.pdf">Télécharger RCP</button>
</div>
<script>
document.querySelectorAll('.btn-rcp').forEach((b) => {
  b.addEventListener('click', () => fetch(b.dataset.file));
});
</script>
</body></html>
"""

r = mod.inspect(
    html,
    "https://ammps.gov.ma/recherche-medicaments?search=AMOXICILLINE",
    "ammps-reg:6fd268f476e7efe0c11f0c4b",
)
assert r["matched"] is True
assert len(r["controls"]) == 1
assert r["controls"][0]["tag"] == "button"
assert r["controls"][0]["attrs"]["data-file"] == "/docs/rcp/amox.pdf"
assert len(r["scripts"]) == 1
print({"status": "PASS"})
