"""P2 PDF profile continuity: synthetic, nonclinical, fail closed."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from backend.services.cephalo_r23g2_pdf_sections import (
    _PROFILES, project_r23g2_pdf_sections,
)
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator


def _fixtures():
    profiles = {}
    for slot, _title, profile_id, count, status, gate in _PROFILES:
        profiles[slot] = {
            "protocol_profile_id": profile_id,
            "profile_status": status,
            "source_lock_gate": gate,
            "classification_authority": False,
            "rows": [
                {
                    "order": i + 1,
                    "canonical_measurement_id": f"M_SYNTHETIC_{slot.upper()}_{i+1}_MM_V1",
                    "source_contract": profile_id,
                    "classification_authority": False,
                    "label": f"NON CLINIQUE {i+1}",
                    "availability_status": "NOT_COMPUTABLE",
                    "contract_state": "CONDITIONAL_EXECUTABLE",
                    "value": None,
                    "unit": "mm",
                }
                for i in range(count)
            ],
        }
    return profiles


def test_all_versions_keep_exact_ids_order_and_nc():
    data = _fixtures()
    sections = project_r23g2_pdf_sections(data, active_runtime_chain_verified=True)
    assert [len(section["rows"]) for section in sections] == [13, 33, 13]
    assert all(section["verified"] for section in sections)
    for section in sections:
        original = data[section["slot"]]["rows"]
        assert [row["canonical_measurement_id"] for row in section["rows"]] == [
            row["canonical_measurement_id"] for row in original
        ]
        assert all(row["value"] == "NC — non calculable" for row in section["rows"])


def test_stale_chain_identity_count_and_fabricated_values_fail_closed():
    data = _fixtures()
    stale = project_r23g2_pdf_sections(data, active_runtime_chain_verified=False)
    assert all(not section["verified"] and not section["rows"] for section in stale)

    mutations = [
        lambda p: p["mcnamara"]["rows"].pop(),
        lambda p: p["ricketts_atlas2009"].update(
            {"protocol_profile_id": "WRONG_PROFILE"}
        ),
        lambda p: p["ricketts_gregoret13"]["rows"][1].update(
            {"canonical_measurement_id": p["ricketts_gregoret13"]["rows"][0]["canonical_measurement_id"]}
        ),
        lambda p: p["mcnamara"]["rows"][0].update({"value": 123.4}),
        lambda p: p["ricketts_atlas2009"].update({"classification_authority": True}),
    ]
    for mutate in mutations:
        payload = deepcopy(data)
        mutate(payload)
        invalid = project_r23g2_pdf_sections(
            payload, active_runtime_chain_verified=True
        )
        assert any(not section["verified"] and not section["rows"] for section in invalid)
        assert all(
            row["value"] == "NC — non calculable"
            for section in invalid for row in section["rows"]
        )


def test_available_number_requires_typed_authority_and_finite_value():
    data = _fixtures()
    row = data["mcnamara"]["rows"][0]
    row.update({"availability_status": "AVAILABLE", "value": 12.5})
    blocked = project_r23g2_pdf_sections(data, active_runtime_chain_verified=True)
    assert not blocked[0]["verified"]
    row.update({
        "measurement_refs": ["synthetic-measurement-ref"],
        "value_authority_method_id": "TEST_METHOD_NOT_CLINICAL",
    })
    ok = project_r23g2_pdf_sections(data, active_runtime_chain_verified=True)
    assert ok[0]["verified"]
    assert ok[0]["rows"][0]["value"] == "12.5 mm"
    row["value"] = float("nan")
    blocked_again = project_r23g2_pdf_sections(data, active_runtime_chain_verified=True)
    assert not blocked_again[0]["verified"]


def test_real_pdf_template_contains_all_canonical_ids_and_explicit_nc(tmp_path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    vm = SimpleNamespace(
        cabinet_config={}, patient_nom="SYNTHETIC", patient_prenom="NEVER_REAL",
        patient_age="12", date_generation="2026-10-17", doctor_name="TEST ONLY",
        is_pre_bilan=True, validation_warnings=[],
    )
    projection = {
        "active_runtime_chain_verified": True,
        "document_state": "INCOMPLETE", "protocol_profiles": _fixtures(),
        "clinical_validation_available": False, "measurements": [],
        "stages": [], "blocking_gates": ["clinical_no_go"],
    }
    context = generator._shared_context(vm, projection)
    assert [len(p["rows"]) for p in context["r23g2_protocols"]] == [13, 33, 13]
    html = generator.jinja_env.get_template("bilan_ortho_authoritative.html").render(**context)
    assert "Analyse protocolaire McNamara 1984" in html
    assert "Analyse protocolaire Ricketts Atlas 2009" in html
    assert "Analyse protocolaire Ricketts Gregoret 1997" in html
    assert html.count("NC — non calculable") == 59
    for section in context["r23g2_protocols"]:
        for row in section["rows"]:
            assert row["canonical_measurement_id"] in html

    # Both backend PDF engines share this exact context. Exercise ReportLab
    # directly, not only a string search in its source.
    output = Path(tmp_path) / "synthetic-r23g2.pdf"
    generator._generate_reportlab(vm, str(output), projection=projection)
    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 1000
