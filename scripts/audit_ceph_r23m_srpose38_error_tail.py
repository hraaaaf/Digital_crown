#!/usr/bin/env python3
"""CEPH R23-M: aggregate-only scientific error-tail diagnostic.

Read-only analysis of R23-L's SHA-locked frozen LOT04 source. No re-inference,
no case-level expert coordinates, no mapping changes, no clinical promotion.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_ceph_r23l_aariz_point_families import (  # noqa: E402
    EVIDENCE, MODEL_SHA256, EvidenceMismatch, analyze, read_evidence,
)

SCHEMA = "CEPH_R23M_AGGREGATE_ERROR_TAIL_READ_ONLY_V1"


def number(x, label: str, *, allow_zero=False) -> float:
    if isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x):
        raise EvidenceMismatch("invalid nonfinite aggregate: " + label)
    if x < 0 or (x == 0 and not allow_zero):
        raise EvidenceMismatch("invalid aggregate sign: " + label)
    return float(x)


def count(x, label: str) -> int:
    if isinstance(x, bool) or not isinstance(x, int) or x < 1:
        raise EvidenceMismatch("invalid aggregate count: " + label)
    return x


def inspect_aggregates(documents: dict, digests: dict) -> dict:
    frozen = analyze(documents, digests)  # Pin blobs, frozen manifest, 24 original decisions.
    if frozen["total_pass"] != 1 or frozen["total_fail"] != 23:
        raise EvidenceMismatch("unexpected frozen landmark decisions")
    if frozen["original_results_byte_binding_verified"]:
        raise EvidenceMismatch("historic mismatch unexpectedly resolved; independent review required")

    source = documents["results"]
    measured = source["landmarks"]
    if len(measured) != 24:
        raise EvidenceMismatch("source does not contain precisely 24 compatible landmarks")
    overall_n = 0
    overall_sum = 0.0
    per_landmark = []
    for name in sorted(measured):
        rec = measured[name]
        agg = rec["error_mm"]
        n = count(agg["n"], name + ".n")
        if rec["valid_n"] != n:
            raise EvidenceMismatch("valid_n mismatch: " + name)
        mean = number(agg["mean"], name + ".mean")
        median = number(agg["median"], name + ".median", allow_zero=True)
        p95 = number(agg["p95"], name + ".p95")
        maximum = number(agg["max"], name + ".max")
        if not median <= p95 <= maximum:
            raise EvidenceMismatch("median/p95/max ordering mismatch: " + name)
        if not rec.get("by_device"):
            raise EvidenceMismatch("missing device summary: " + name)
        device_n, device_sum, device_max = 0, 0.0, 0.0
        for device, values in sorted(rec["by_device"].items()):
            k = count(values["n"], name + "." + device + ".n")
            device_n += k
            device_sum += k * number(values["mean"], name + "." + device + ".mean", allow_zero=True)
            device_max = max(device_max, number(values["max"], name + "." + device + ".max"))
        if device_n != n or not math.isclose(device_sum, mean*n, rel_tol=1e-8, abs_tol=1e-7):
            raise EvidenceMismatch("device/landmark mean/count drift: " + name)
        if not math.isclose(device_max, maximum, rel_tol=1e-8, abs_tol=1e-7):
            raise EvidenceMismatch("global maximum not supported by device groups: " + name)
        overall_n += n
        overall_sum += n * mean
        per_landmark.append({
            "point": name, "n": n, "mean_mm": mean, "median_mm": median,
            "p95_mm": p95, "max_mm": maximum,
            "original_decision": rec["decision"],
        })

    if overall_n != 3374:
        raise EvidenceMismatch("frozen qualified-pair denominator unexpectedly changed")
    go = measured["Go"]
    go_summary = go["error_mm"]
    source_device_maxima = sorted(
        ((device, number(v["max"], "Go." + device + ".max"),
          count(v["n"], "Go." + device + ".n"))
         for device, v in go["by_device"].items()),
        key=lambda item: item[1], reverse=True,
    )
    extreme = [r for r in source_device_maxima if r[1] >= 100.0]
    if len(extreme) != 2 or {x[0] for x in extreme} != {"ART Plus", "Hyperion X5"}:
        raise EvidenceMismatch("unexpected 100mm descriptive Go tail; review required")
    # Maxima of different device groups necessarily represent distinct film/point observations.
    # This is a lower bound from two concrete cases, NOT a reconstructed complete error distribution.
    two_known_errors_sum = sum(x[1] for x in extreme)
    go_sum = number(go_summary["mean"], "Go.mean") * count(go_summary["n"], "Go.n")
    if not 0 < two_known_errors_sum < go_sum:
        raise EvidenceMismatch("invalid Go contribution arithmetic")
    # Sensitivity is descriptive only; do not suppress/remove the two observations from validation.
    hypothetical_mean = (go_sum - two_known_errors_sum) / (go_summary["n"] - 2)

    return {
        "schema": SCHEMA,
        "scope": "frozen 150 Aariz acceptance films, source aggregates only; no new inference",
        "model_sha256": MODEL_SHA256,
        "raw_results_sha256_embedded": frozen["source_results_sha256_embedded"],
        "raw_results_sha256_committed": frozen["source_results_sha256_committed_file"],
        "original_results_byte_binding_verified": False,
        "provenance_warning": frozen["provenance_warning"],
        "aggregate_compatible_landmarks": len(per_landmark),
        "qualified_point_comparisons": overall_n,
        "qualified_point_mean_error_mm": overall_sum / overall_n,
        "landmarks_with_mean_below_2_mm": sum(x["mean_mm"] < 2.0 for x in per_landmark),
        "landmarks_with_p95_at_most_2_mm": sum(x["p95_mm"] <= 2.0 for x in per_landmark),
        "go_tail": {
            "n": go_summary["n"],
            "mean_mm": go_summary["mean"],
            "median_mm": go_summary["median"],
            "p95_mm": go_summary["p95"],
            "max_mm": go_summary["max"],
            "two_independent_device_group_maxima_over_100mm": [
                {"device": dev, "max_mm": max_error, "device_qualified_n": n}
                for dev, max_error, n in extreme
            ],
            "two_observations_share_of_total_absolute_error": two_known_errors_sum / go_sum,
            "descriptive_leave_two_out_mean_mm_NOT_ACCEPTANCE": hypothetical_mean,
            "tail_concentration_is_not_causal_proof": True,
        },
        "per_landmark_aggregates": per_landmark,
        "not_comparable_directly_to_miccai38_mre": True,
        "individual_expert_gt_available": False,
        "channel_swap_proven": False,
        "new_tuning_or_thresholds_authorized": False,
        "original_frozen_acceptance_decision": "FAIL",
        "clinical_release": False,
        "next_gate": "AUTHORIZED_DEVELOPMENT_SET_PAIRED_GT_AND_ORIGINAL_BYTE_PROVENANCE",
    }


def to_markdown(report: dict) -> str:
    go = report["go_tail"]
    items = [
        "# CEPH R23-M — SRPose38 error-tail diagnostic (aggregate-only)",
        "",
        "**READ-ONLY / no patient records, no inference, no retuning, clinical NO-GO.**",
        "",
        f"Compatible Aariz points: {report['aggregate_compatible_landmarks']} (not all 38 model channels).",
        f"Qualified point comparisons: {report['qualified_point_comparisons']}.",
        f"Weighted mean Euclidean error: {report['qualified_point_mean_error_mm']:.4f} mm.",
        "This MRE is NOT an apples-to-apples replication of the MICCAI 38-point leaderboard.",
        f"Source-provenance warning: {report['provenance_warning']}.",
        "",
        "## Go (gonion, legacy local mapping) tail",
        f"Original frozen mean {go['mean_mm']:.4f} mm; median {go['median_mm']:.4f} mm;",
        f"p95 {go['p95_mm']:.4f} mm; max {go['max_mm']:.4f} mm (n={go['n']}).",
        "Two independent device-group maxima above 100 mm:",
    ]
    for v in go["two_independent_device_group_maxima_over_100mm"]:
        items.append(f"- {v['device']}: max {v['max_mm']:.3f} mm (device n={v['device_qualified_n']})")
    items += [
        f"These TWO recorded extreme errors alone explain **{100*go['two_observations_share_of_total_absolute_error']:.2f}%**",
        "of Go's summed absolute error. They are NOT excluded from any frozen result.",
        f"Pure arithmetic leave-two-out illustration: {go['descriptive_leave_two_out_mean_mm_NOT_ACCEPTANCE']:.3f} mm.",
        "This is NOT a rescored PASS, a robust replacement metric, or proof of their cause.",
        "",
        "## Limits and next independent test",
        "1. The upstream SUTD-VLG competition ensemble of seven models and the standalone checkpoint are different.",
        "2. Unknown upstream anatomical index-to-name semantics and unavailable per-film expert x/y",
        "   prevent identifying a wrong mapping, false GT pair, device-calibration error, or source of the Go maxima.",
        "3. The original embedded results-file SHA mismatch remains open and cannot be normalized away.",
        "4. Obtain authorized 38-index paired annotations on a separate development set;",
        "   compare same-checkpoint PyTorch and ONNX per numerical channel with native spacing/orientation",
        "   and inspect errors in developer-only local environment, then preregister independent validation.",
        "",
    ]
    return "\n".join(items)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence-dir", type=Path, default=EVIDENCE)
    p.add_argument("--output-dir", type=Path, default=ROOT/"artifacts/ceph-r23m-error-tail")
    args = p.parse_args()
    documents, digests = read_evidence(args.evidence_dir)
    report = inspect_aggregates(documents, digests)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    (args.output_dir/"README.md").write_text(to_markdown(report), encoding="utf-8")
    print(json.dumps({
        "result": "R23M_READ_ONLY_SOURCE_ERROR_TAIL_REPRODUCED__CLINICAL_NO_GO",
        "qualified_pairs": report["qualified_point_comparisons"],
        "weighted_mre_mm": round(report["qualified_point_mean_error_mm"], 4),
        "go_two_extreme_share": round(report["go_tail"]["two_observations_share_of_total_absolute_error"], 4),
        "provenance_warning_open": True, "clinical_release": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
