#!/usr/bin/env python3
"""R23-I read-only post-FUE-H provenance audit.

This intentionally does NOT replay the browser or validate cephalometric anatomy.
A green AUDIT result means that we detected/documented the unsafe-UX uncertainty,
NOT that a clinical gate is green.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "ceph-r23i-provenance-gate"
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    "workbench": ROOT / "frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx",
    "calibration": ROOT / "frontend/src/features/ortho/cephaloCalibration.ts",
    "pdf": ROOT / "frontend/src/features/ortho/components/Step4Documents.tsx",
    "h_executed": ROOT / "frontend/scripts/fue-ceph-r23h-first-use.mjs",
}

def evidence(name: str, fragment: str) -> dict:
    p = FILES[name]
    content = p.read_text(encoding="utf-8")
    positions = [i for i, line in enumerate(content.splitlines(), 1) if fragment in line]
    if not positions:
        raise AssertionError(f"Source gate changed: {name} missing expected proof")
    return {"path": str(p.relative_to(ROOT)), "line": positions[0],
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "fragment": fragment}

def file_proof(name: str) -> dict:
    path = FILES[name]
    if not path.is_file():
        raise AssertionError("Required source missing: " + name)
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(data).hexdigest()}

checks = {
    "fue_h_exercised_real_onnx": evidence("h_executed", "ONNX"),
    "angles_count_any_numeric_value": evidence(
        "workbench", "readValue(metricFromResults(anglesData, definition)) !== null"),
    "numeric_count_green_without_human_review": evidence(
        "workbench", "availableCount > 0 ? P.accentSuccess"),
    "numeric_detail_success_icon_without_human_review": evidence(
        "workbench", "<CheckCircle2 size={13}"),
    "available_status_green_without_person_source": evidence(
        "workbench", "metric.availability_status === 'AVAILABLE'"),
    "raw_value_has_a_distinct_label": evidence(
        "workbench", "return 'Mesure brute'"),
    "numeric_norm_is_a_separate_field": evidence(
        "workbench", "typeof metric.norm_min === 'number'"),
    "calibration_unverified_is_displayed": evidence(
        "calibration", "return 'Échelle non vérifiée'"),
    "pdf_disclaims_clinical_validation": evidence(
        "pdf", "Prévisualiser ou archiver un PDF ne constitue pas une validation clinique."),
    "ricketts_ref_reader_separate_from_legacy_all": evidence(
        "workbench", "props.analysis === 'mcnamara' || props.analysis === 'com' || props.analysis === 'ricketts'"),
}

workbench = FILES["workbench"].read_text(encoding="utf-8")
legacy = workbench.split("const CephaloLegacyAnalysisWorkbenchPanel:",1)[1].split(
    "/** Route only R23-G4 historical reference views",1)[0]
# Explicit reviewer provenance would be needed at the point of value promotion,
# not only in a calibration badge attached to the image.
review_tokens = ("CLINICIAN_VALIDATED", "validated_by", "validated_at",
                 "clinician_reviewed", "evidence_review_state")
human_review_gate_in_legacy = any(token in legacy for token in review_tokens)
if human_review_gate_in_legacy:
    raise AssertionError("Workbench review contract changed: re-audit live path before using this report")

head = os.environ.get("PRODUCT_HEAD","UNKNOWN")
fue_h_run_sha = "8ebd8b013c54ee9417b4edce091c942fbdbaf22b"
report = {
    "audit_id": "CEPH-UXCLIN-01/R23-I/PROVENANCE-GATE/2026-10-22",
    "source_head": head,
    "independent_runtime_fue_run": {
        "run": "https://github.com/hraaaaf/Digital_crown/actions/runs/39836036083",
        "exact_head": fue_h_run_sha,
        "evidence_artifact_id": 12450269332,
        "technical_run_status": "SUCCESS",
        "image_count": 2,
        "real_pinned_model": "SRPOSE38_TTA_1024_SHA_LOCKED_CPU",
        "automatic_landmarks_per_study": 38,
        "clinical_validation": False,
    },
    "this_audit_replayed_runtime": False,
    "source_files": {name: file_proof(name) for name in FILES},
    "positive_controls": {
        "angles_without_mm_scale_may_remain_raw": True,
        "mm_scale_unverified_banner_in_ui": True,
        "pdf_has_explicit_clinical_disclaimer": True,
        "ricketts_is_separate_source_locked_read_path": True,
        "normative_reference_must_not_be_confused_with_raw_metric": True,
    },
    "observed_ux_ambiguities": [
        {"severity": "BLOCKING_OWNER_REVIEW", "id": "R23I-01",
         "observation": "In Toutes analyses, any finite value increases the green 'mesures calculées' counter; no explicit independent-clinician review gate in this legacy panel.",
         "not_claimed": "This does not prove any computed angle is mathematically wrong."},
        {"severity": "BLOCKING_OWNER_REVIEW", "id": "R23I-02",
         "observation": "Metric detail uses a green-check success icon when a numeric result exists, even when landmarks are automatic and expert-unvalidated.",
         "not_claimed": "The icon does not formally claim diagnosis, but can be mistaken for clinical validation."},
        {"severity": "NEEDS_CLINICAL_DECISION", "id": "R23I-03",
         "observation": "The status label 'Mesure brute' does not itself identify SRPose38 automatic inference, image-specific source or absent expert review.",
         "not_claimed": "Raw angular readings are not forbidden solely by absent millimetric calibration."},
    ],
    "review_proposal": [
        "Retain raw angles when geometrically calculable; do not suppress them solely for missing mm/pixel.",
        "Add clearly distinct origin and clinical-review state to the All panel; keep unreviewed auto values neutral, never green-approved.",
        "Do not introduce normative interpretation, Ricketts landmark equivalence, treatment or diagnosis.",
        "Require human visual approval of wording and independent orthodontist goldset before changing clinical authority.",
    ],
    "owner_approval": "REQUIRED_NOT_INHERITED",
    "clinical_release": False,
    "roadmap": "41/99_UNCHANGED",
    "result": "AUDIT_EXECUTED__UX_PROMOTION_RISK_OPEN__CLINICAL_NO_GO",
    "checks": checks,
}
(OUT / "report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
summary=[
    "# R23-I — audit de provenance après FUE-H",
    "",
    f"- Code exact : \`{head}\`",
    "- Provenance FUE-H : run 39836036083 (SUCCESS), mais audit R23-I = lecture de code, **pas nouveau FUE-G/H**.",
    "- Résultat : **AUDIT EXÉCUTÉ ; 3 ambiguïtés de présentation ; CLINICAL NO-GO**.",
    "- Les angles bruts en degrés peuvent être calculables sans calibration mm/px.",
    "- Le vert/icône de succès ne doit pas être compris comme validation d'un orthodontiste.",
    "- Aucune modification runtime/patient/API et aucune approbation humaine simulée.",
    "",
    "## Points en attente",
]
for issue in report["observed_ux_ambiguities"]:
    summary.append(f"- **{issue['id']}** ({issue['severity']}) : {issue['observation']}")
summary.append("\nTravail ultérieur : maquette et revue visuelle humaine de badges de provenance ; validation scientifique séparée.")
(OUT/"README.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
print("R23I_PROVENANCE_AUDIT_EXECUTED",json.dumps({
    "head":head,"checks":len(checks),
    "findings":len(report["observed_ux_ambiguities"]),
    "release":report["clinical_release"],
    "result":report["result"]
},sort_keys=True))
