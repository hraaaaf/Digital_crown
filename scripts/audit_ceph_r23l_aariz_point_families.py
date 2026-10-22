#!/usr/bin/env python3
"""R23-L: read-only audit of the frozen LOT04 Aariz landmark families.

This script DOES NOT infer, remap channels, retune thresholds, or re-score
individual cases. Without paired per-case expert (x,y) GT it cannot demonstrate
a channel permutation or correct its cause. Reproduces the original decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/audits/evidence/lot04"
MODEL_SHA256 = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
FAMILY = {
    "OSSEOUS": ("A", "ANS", "Ar", "B", "Co", "Gn", "Go", "Me", "N", "Or", "PNS", "Po", "Pog", "S"),
    "DENTAL": ("L1_apex", "L1_incisal", "U1_apex", "U1_incisal"),
    "SOFT_TISSUE": ("Li_soft", "Ls_soft", "N_soft", "Pog_soft", "Prn", "Sn_soft"),
}
FILES = {
    "manifest": "cephalo_vnext_lot04_benchmark_manifest.json",
    "results": "cephalo_vnext_lot04_results.json",
    "acceptance": "cephalo_vnext_lot04_acceptance_record.json",
    "acceptance_detail": "cephalo_vnext_lot04_acceptance_record_detail.json",
}


class EvidenceMismatch(ValueError):
    pass


def sha256_bytes(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def canonical_hash(record: dict) -> str:
    return sha256_bytes(json.dumps(record, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False).encode("utf-8"))


def read_evidence(directory: Path) -> tuple[dict, dict]:
    docs = {}
    digests = {}
    for key, name in FILES.items():
        source = directory / name
        raw = source.read_bytes()
        docs[key] = json.loads(raw)
        digests[key] = sha256_bytes(raw)
    return docs, digests


def _finite_positive(x, label: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0:
        raise EvidenceMismatch(f"invalid positive source value: {label}")
    return float(x)


def analyze(docs: dict, digests: dict) -> dict:
    manifest = docs["manifest"]
    result = docs["results"]
    acceptance = docs["acceptance"]
    detail = docs["acceptance_detail"]
    manifest_hash = canonical_hash(manifest)
    model_hash = manifest["candidate"]["model_sha256"]
    if model_hash != MODEL_SHA256:
        raise EvidenceMismatch("candidate hash drifted from pinned SRPose38")
    for name, payload in (("results", result), ("acceptance", acceptance)):
        if payload["manifest_sha256"] != manifest_hash:
            raise EvidenceMismatch(f"{name} no longer binds frozen manifest")
        if payload["candidate_model_sha256"] != MODEL_SHA256:
            raise EvidenceMismatch(f"{name} no longer binds exact ONNX hash")
    if detail["source_results_sha256"] != digests["results"]:
        raise EvidenceMismatch("acceptance detail not linked to exact source results bytes")
    if manifest["acceptance_policy"]["tolerance_version"] != "REFERENCE_EQUIVALENCE_V1":
        raise EvidenceMismatch("source threshold version drifted")
    if not manifest["acceptance_policy"]["preregistered"]:
        raise EvidenceMismatch("thresholds not pre-registered")
    if len(manifest["dataset"]["acceptance_case_ids"]) != 150:
        raise EvidenceMismatch("untouched sample not exactly 150 cases")
    case_ids = set(manifest["dataset"]["acceptance_case_ids"])
    if len(case_ids) != 150 or case_ids & set(manifest["dataset"]["development_case_ids"]):
        raise EvidenceMismatch("duplicate or contaminated frozen acceptance cases")
    predicted_cases = result["predictions"]
    if len(predicted_cases) != 150 or {r["case_id"] for r in predicted_cases} != case_ids:
        raise EvidenceMismatch("predictions not complete for exact 150-case acceptance")
    if len({r["case_id"] for r in predicted_cases}) != 150:
        raise EvidenceMismatch("duplicate predictions")
    for pred in predicted_cases:
        if set(pred["coordinates"]) != set(pred["scores"]) or len(pred["coordinates"]) != 38:
            raise EvidenceMismatch("one or more predictions lacks 38 model-output channels")
    target_ids = set(sum((list(g) for g in FAMILY.values()), []))
    if len(target_ids) != 24:
        raise EvidenceMismatch("overlapping group assignments")
    acc_rows = acceptance["landmarks"]
    acc = {x["landmark_id"]: x for x in acc_rows}
    if len(acc) != len(acc_rows) or set(acc) != target_ids or set(result["landmarks"]) != target_ids:
        raise EvidenceMismatch("scientific 24-landmark scope changed; refuse to silently regroup")
    tolerance_items = manifest["acceptance_policy"]["landmark_tolerances"]
    tolerance = {x["landmark_id"]: x for x in tolerance_items}
    if len(tolerance) != len(tolerance_items) or set(tolerance) != target_ids:
        raise EvidenceMismatch("frozen landmark thresholds missing, overlapping or added")
    if acceptance["overall_decision"] != "FAIL" or result["overall_decision"] != "FAIL":
        raise EvidenceMismatch("this audit expects frozen FAIL, never rewrite acceptance verdict")
    if len(acceptance["clinical_measurements"]) != 9:
        raise EvidenceMismatch("nine sentinel measurements required (reported, not recomputed)")
    rows = []
    for family, identifiers in FAMILY.items():
        for id_ in identifiers:
            record = acc[id_]
            existing = result["landmarks"][id_]
            lim = tolerance[id_]
            median = _finite_positive(float(record["median_mm"]), id_ + ".median_mm")
            p95 = _finite_positive(float(record["p95_mm"]), id_ + ".p95_mm")
            p95_limit = _finite_positive(float(lim["max_p95_mm"]), id_ + ".max_p95_mm")
            median_limit = float(lim["max_median_mm"])
            if median_limit < 0 or not math.isfinite(median_limit):
                raise EvidenceMismatch(f"bad median threshold {id_}")
            if abs(float(existing["error_mm"]["p95"]) - p95) > 1e-9:
                raise EvidenceMismatch(f"source aggregate drift for {id_}")
            status = record["decision"]
            if status not in ("PASS", "FAIL"):
                raise EvidenceMismatch(f"unknown frozen decision: {id_}")
            reproducible_pass = (
                median <= median_limit and p95 <= p95_limit
                and record["failure_rate"] <= lim["max_failure_rate"]
            )
            if (status == "PASS") != reproducible_pass:
                raise EvidenceMismatch(f"decision inconsistent with preregistered thresholds: {id_}")
            devices = []
            for name, data in sorted(existing["by_device"].items()):
                if data["n"] <= 0:
                    continue
                devices.append({
                    "name": name, "n": int(data["n"]),
                    "p95_mm": float(data["p95"]),
                    "exploratory_only": True,
                    "small_stratum": data["n"] < 59,
                })
            rows.append({
                "family":family, "id":id_,
                "n_reference_eligible":int(record["n"]),
                "decision":status,
                "median_mm":median,
                "median_limit_mm":median_limit,
                "p95_mm":p95,
                "p95_limit_mm":p95_limit,
                "p95_ratio":p95 / p95_limit,
                "median_dx_mm":float(existing["signed_x_mm"]["median"]),
                "median_dy_mm":float(existing["signed_y_mm"]["median"]),
                "by_device":devices,
            })
    rows.sort(key=lambda r: (-r["p95_ratio"], r["id"]))
    group_counts = {
        group:{
            "points": len(names),
            "pass": sum(x["decision"]=="PASS" for x in rows if x["family"]==group),
            "fail": sum(x["decision"]=="FAIL" for x in rows if x["family"]==group),
            "highest_p95_ratio": max(
                (x["p95_ratio"] for x in rows if x["family"]==group), default=None
            ),
        } for group,names in FAMILY.items()
    }
    return {
        "schema":"CEPH_R23L_FROZEN_AARIZ_POINT_FAMILY_READ_ONLY_V1",
        "scope":"already executed frozen LOT04; zero new inference",
        "model_sha256":MODEL_SHA256,
        "manifest_canonical_sha256":manifest_hash,
        "evidence_file_sha256":digests,
        "acceptance_cases":150,
        "landmark_counts":group_counts,
        "total_pass":sum(x["decision"]=="PASS" for x in rows),
        "total_fail":sum(x["decision"]=="FAIL" for x in rows),
        "acceptance_decision_original":"FAIL",
        "audit_conclusion":"FROZEN_RESULTS_VERIFIED_MAPPING_CAUSALITY_UNPROVEN_CLINICAL_NO_GO",
        "clinical_release":False,
        "channel_swap_proven":False,
        "channel_relabel_authorized":False,
        "has_individual_paired_expert_coordinates":False,
        "limitations":[
            "Index-to-anatomical-name mapping is local legacy contract, not independently proven upstream.",
            "Aggregate p95 and per-case model predictions cannot establish an index swap without exact same-case human (x,y) references.",
            "Device-stratified figures are descriptive, not a new prospective diagnostic or retuned selection criterion.",
            "Per-landmark eligible n varies across 150 films; many device groups are small.",
            "Some dermatologic/soft-tissue model channels remain outside Aariz compatible 24; 24-point audit never certifies all 38.",
            "The existing scientific rejection of the candidate under frozen thresholds remains unchanged.",
        ],
        "landmarks":rows,
    }


def to_markdown(report: dict) -> str:
    s=[
        "# R23-L — Frozen Aariz landmark family audit (read-only)",
        "",
        f"Exact pinned SRPose38 SHA256: \`{report['model_sha256']}\`.",
        f"Source: {report['acceptance_cases']} frozen untouched acceptance films; **no new inference**.",
        "**Clinical decision remains NO-GO**; mapping swap is NOT established.",
        "",
        "| Family | PASS | FAIL | Total |",
        "|---|---:|---:|---:|",
    ]
    for name,d in report["landmark_counts"].items():
        s.append(f"| {name} | {d['pass']} | {d['fail']} | {d['points']} |")
    s += [
        "",
        "## Top largest p95/reference-p95 ratios (diagnostic only)",
        "",
        "| Family | Point | p95 error (mm) | Frozen p95 limit (mm) | Ratio | Original decision |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in report["landmarks"][:12]:
        s.append(f"| {r['family']} | {r['id']} | {r['p95_mm']:.3f} | {r['p95_limit_mm']:.3f} | {r['p95_ratio']:.2f}× | {r['decision']} |")
    s += [
        "",
        "## Causal interpretation — bounded",
        "",
        "1. These errors are observed AFTER mapping model channels to local anatomical identifiers; they cannot establish whether the network, the mapping, preprocessing, or device domain was responsible.",
        "2. A small median with a high p95 can mean some images are much worse than others; do not claim this proves an index inversion.",
        "3. Channel permutation testing is NOT possible from this published evidence alone: exact matching per-case expert (x,y) coordinates are absent.",
        "4. Device differences are exploratory and sample counts vary. No new threshold or relabel was fitted to the frozen acceptance set.",
        "5. Never promote 24 compatible Aariz names to confirmation of all 38 CL-Detection2023 channels.",
        "",
        "**Next evidence**: independently authorized same-image 38 expert GT + model output, or qualified reference case-by-case pairs on a fresh held-out dataset, with preregistered mapping candidates and a separate untouched acceptance set.",
        "",
    ]
    return "\n".join(s)


def main() -> int:
    p=argparse.ArgumentParser(description="Readonly R23-L source-locked family audit of frozen LOT04")
    p.add_argument("--evidence-dir",type=Path,default=EVIDENCE)
    p.add_argument("--output-dir",type=Path,default=ROOT/"artifacts/ceph-r23l-family-audit")
    args=p.parse_args()
    docs,digests=read_evidence(args.evidence_dir)
    result=analyze(docs,digests)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"report.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (args.output_dir/"README.md").write_text(to_markdown(result),encoding="utf-8")
    print(json.dumps({
        "result":result["audit_conclusion"],
        "scope":result["scope"],
        "pass":result["total_pass"],"fail":result["total_fail"],
        "model_sha256":result["model_sha256"],
        "clinical_release":False,"channel_swap_proven":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
