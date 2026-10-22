#!/usr/bin/env python3
"""R23-L scientific evidence AUDIT only: archived Aariz LOT04 errors by anatomical family.

This is NOT a re-scored benchmark, detector selection, clinical approval, or remapping.
It intentionally cannot infer channel swaps from predictions without same-case expert GT.
Uses archived frozen acceptance outputs and model-generated predictions. Never train/tune.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/audits/evidence/lot04"
EXPECTED_MODEL_SHA = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
FAMILIES = {
    "osseux": ("A","ANS","Ar","B","Co","Gn","Go","Me","N","Or","PNS","Po","Pog","S"),
    "dentaire": ("L1_apex","L1_incisal","U1_apex","U1_incisal"),
    "cutane": ("Li_soft","Ls_soft","N_soft","Pog_soft","Prn","Sn_soft"),
}
SCHEMA = "CEPH_R23L_AARIZ_FAMILY_HYPOTHESIS_AUDIT_V1"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def source_mapping(path: Path) -> dict[str, str]:
    """Read static benchmark AARIZ_TO_DC literal, do not run scientific model."""
    root = ast.parse(path.read_text(encoding="utf-8"))
    found = [ast.literal_eval(n.value) for n in root.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id=="AARIZ_TO_DC" for t in n.targets)]
    if len(found) != 1 or not isinstance(found[0], dict):
        raise ValueError("Frozen Aariz→DC mapping absent or ambiguous")
    return found[0]

def validate_archived_evidence(record: dict, results: dict, detail: dict, mapping: dict) -> None:
    if record.get("overall_decision")!="FAIL" or results.get("overall_decision")!="FAIL":
        raise ValueError("Historical FAIL must not be silently overwritten or promoted")
    if record.get("candidate_model_sha256")!=EXPECTED_MODEL_SHA or results.get("candidate_model_sha256")!=EXPECTED_MODEL_SHA:
        raise ValueError("Candidate/model drift")
    if record.get("manifest_sha256")!=results.get("manifest_sha256"):
        raise ValueError("Different benchmark manifests")
    if len(results.get("predictions",[]))!=150 or results.get("acceptance_cases")!=150:
        raise ValueError("Unexpected untouched acceptance cohort")
    if len(record.get("clinical_measurements",[]))!=9:
        raise ValueError("Expected 9 downstream geometry errors, not model output")
    all_family = [point for names in FAMILIES.values() for point in names]
    if len(all_family)!=24 or len(set(all_family))!=24 or set(mapping.values())!=set(all_family):
        raise ValueError("Incorrect overlap between frozen Aariz mappings and 24 family labels")
    if len(record.get("landmarks",[]))!=24 or {x["landmark_id"] for x in record["landmarks"]}!=set(all_family):
        raise ValueError("Archived clinical-landmark subset does not equal frozen 24")
    if set(results.get("landmarks",{}))!=set(all_family):
        raise ValueError("Per-landmark results missing or unexpected")
    if any(x["decision"] not in ("PASS","FAIL") for x in record["landmarks"]):
        raise ValueError("Unresolved status; do not count as passing")
    if "source_results_sha256" not in detail:
        raise ValueError("Source results hash binding missing")
    if any(set(p.get("coordinates",{}))!=set(p.get("scores",{}))
           or len(p.get("coordinates",{}))!=38 for p in results["predictions"]):
        raise ValueError("Cannot confirm 38 model-output coordinates on each acceptance image")
    if any("ground_truth" in p or "reference_coordinates" in p or "gt" in p for p in results["predictions"]):
        raise ValueError("Expert coordinates unexpectedly present: audit evidence boundary changed")
    if len({p["case_id"] for p in results["predictions"]})!=150:
        raise ValueError("Duplicate case IDs in frozen prediction archive")

def analyze(record: dict, results: dict, *, source_digest: str, manifest_sha: str) -> dict:
    records = {x["landmark_id"]:x for x in record["landmarks"]}
    cohorts={}
    for name,ids in FAMILIES.items():
        point_rows=[]
        for label in ids:
            r=records[label]; e=results["landmarks"][label]
            threshold=float(r["human_reference_uncertainty_mm"])
            observed=float(r["p95_mm"])
            median=float(r["median_mm"])
            if threshold<=0 or not all(math.isfinite(z) for z in (threshold,observed,median)):
                raise ValueError(f"Invalid frozen p95/median for {label}")
            device_rows=[{"device":device,"n":v["n"],"p95_mm":round(v["p95"],4),
                          "small_sample_lt_20":v["n"]<20} for device,v in sorted(e["by_device"].items())]
            point_rows.append({
                "id":label,"decision":r["decision"],"n_reference_pairs":r["n"],
                "median_mm":round(median,4),"p95_mm":round(observed,4),
                "frozen_human_reference_p95_mm":round(threshold,4),
                "observed_to_human_p95_ratio":round(observed/threshold,3),
                "median_signed_x_mm":round(e["signed_x_mm"]["median"],4),
                "median_signed_y_mm":round(e["signed_y_mm"]["median"],4),
                "devices":device_rows,
            })
        cohorts[name]={
            "total":len(ids),
            "passed":sum(x["decision"]=="PASS" for x in point_rows),
            "failed":sum(x["decision"]=="FAIL" for x in point_rows),
            "points":point_rows,
            "ranked_high_p95_ratio":sorted(point_rows,key=lambda x:-x["observed_to_human_p95_ratio"])[:4],
        }
    other=list(set(results["predictions"][0]["coordinates"])-set(records))
    report={
      "schema":SCHEMA,"source_results_sha256":source_digest,"frozen_manifest_sha256":manifest_sha,
      "model_sha256":EXPECTED_MODEL_SHA,
      "source": "immutable archived LOT04 acceptance outputs only; no rerun",
      "acceptance_cases":150,"compared_reference_points":24,
      "other_model_channels_without_Aariz_reference":len(other),
      "other_model_channel_operational_ids_sorted":sorted(other),
      "total_fail":sum(x["failed"] for x in cohorts.values()),
      "total_pass":sum(x["passed"] for x in cohorts.values()),
      "families":cohorts,
      "downstream_angle_results_not_detector_outputs":{
        x["measurement_id"]:{"decision":x["decision"],"p95_error":x["absolute_error"]}
        for x in record["clinical_measurements"]
      },
      "evidence_limits":{
        "same_case_expert_coordinates_accessible_in_this_archive":False,
        "automated_swap_detection_possible":False,
        "anatomical_channel_identity_source_verified":False,
        "causal_device_effect_proven":False,
        "reference_landmark_taxonomy":"audit grouping only; not original CL2023 channel definitions",
        "new_experiment_executed":False,
        "clinical_release":False,
        "scientific_detector_selected":False,
        "no_posthoc_thresholds_or_remapping":True,
        "case_predictions_not_exported":True,
      },
      "verdict":"TECHNICAL_DIAGNOSTIC__MAPPING_HYPOTHESIS_OPEN__CLINICAL_NO_GO"
    }
    if report["total_fail"]!=23 or report["total_pass"]!=1:
        raise ValueError("Existing scientific record unexpectedly changed")
    return report

def markdown(report: dict) -> str:
    lines=["# R23-L — analyse des erreurs des repères SRPose38 (Aariz déjà figé)","",
        "**Étude exploratoire de causes, PAS validation clinique ou remapping automatique.**",
        f"Archive de {report['acceptance_cases']} cas et {report['compared_reference_points']} repères comparables. ",
        "Les 38 prédictions par cas existent, mais les annotations humaines x/y par cas ne sont pas stockées dans CETTE archive.",
        "Les seuils préenregistrés ne sont ni ajustés ni réinterprétés.","",
        "| Famille | Compatibles | PASS | FAIL |", "|---|---:|---:|---:|"]
    for family,group in report["families"].items():
        lines.append(f"| {family} | {group['total']} | {group['passed']} | {group['failed']} |")
    lines += ["","## Priorités descriptives — excès p95 vs enveloppe humaine figée","",
              "| Famille | Point | p95 modèle (mm) | p95 humain (mm) | Rapport |",
              "|---|---|---:|---:|---:|"]
    for family,group in report["families"].items():
        for point in group["ranked_high_p95_ratio"]:
            lines.append(f"| {family} | {point['id']} | {point['p95_mm']:.3f} | {point['frozen_human_reference_p95_mm']:.3f} | {point['observed_to_human_p95_ratio']:.2f}× |")
    lines += ["","## Intégrité des archives historiques", "",
       f"- SHA256 du fichier résultats lu : \`{report['source_results_sha256']}\`",
       f"- SHA256 attendu dans le document detail historique : \`{report['detail_declared_source_results_sha256']}\`",
       "- Correspondance : **OUI**" if report["evidence_limits"]["archived_detail_sha256_matches_current_results_bytes"] else "- Correspondance : **NON — TRAÇABILITÉ OU SÉRIALISATION HISTORIQUE À ÉLUCIDER**, aucune preuve scientifique nouvelle certifiée.",
       "", "## Interprétation limitée", "",
      "1. Les groupes sont des **classes de suivi local** (osseux, dentaire, cutané), pas une preuve des 38 noms anatomiques amont.",
      "2. Une p95 élevée sur certains appareils peut signaler un problème de domaine/imagerie, mais les effectifs sont hétérogènes : **pas de causalité démontrée** ni de nouvelle normalisation.",
      "3. **Aucun swap de canaux ne peut être testé ou prouvé** sans coordonnées expertes par cas appariées aux 38 prédictions. Les métriques agrégées seules ne le permettent pas.",
      "4. Les 9 erreurs angulaires/distances de l'ancien benchmark sont des **mesures aval**, non des sorties ONNX du poids.",
      "5. La seule démarche recevable ensuite : retrouver les coordonnées expertes originales de mêmes cas, vérifier les index et préparer un diagnostic *hors set untouched*, puis confirmation indépendante sur nouveau jeu autorisé.",
      "6. Source du poids, mapping product et six HOLD Ricketts non modifiés ; pas de nouvelle sélection scientifique.",
      "",
      f"**Résultat : `{report['verdict']}`**. PR DRAFT, no merge/deploy/Production, 41/99 inchangé.",""]
    return "\n".join(lines)

def run(output: Path, evidence: Path=EVIDENCE, repository_root: Path=ROOT):
    paths={name:evidence/file for name,file in {
        "record":"cephalo_vnext_lot04_acceptance_record.json",
        "results":"cephalo_vnext_lot04_results.json",
        "detail":"cephalo_vnext_lot04_acceptance_record_detail.json"}.items()}
    raw={name:path.read_bytes() for name,path in paths.items()}
    # This archive may have been serialized after the original detail attestation.
    # NEVER suppress or silently repair a mismatch; make it an explicit unresolved gate.
    actual_sha256 = digest(raw["results"])
    record=json.loads(raw["record"]);results=json.loads(raw["results"]);detail=json.loads(raw["detail"])
    declared_sha256 = detail["source_results_sha256"]
    matches_archived_attestation = actual_sha256 == declared_sha256
    mapping=source_mapping(repository_root/"scripts/run_cephalo_vnext_lot04_benchmark.py")
    validate_archived_evidence(record,results,detail,mapping)
    report=analyze(record,results,source_digest=actual_sha256,manifest_sha=record["manifest_sha256"])
    report["detail_declared_source_results_sha256"] = declared_sha256
    report["evidence_limits"]["archived_detail_sha256_matches_current_results_bytes"] = matches_archived_attestation
    report["evidence_limits"]["archival_chain_of_custody_verified"] = matches_archived_attestation
    if not matches_archived_attestation:
        report["verdict"] = "TECHNICAL_DIAGNOSTIC__ARCHIVE_DIGEST_DRIFT_OPEN__CLINICAL_NO_GO"
    output.mkdir(parents=True,exist_ok=True)
    (output/"report.json").write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    (output/"README.md").write_text(markdown(report),encoding="utf-8")
    print(json.dumps({"verdict":report["verdict"],"n":report["acceptance_cases"],
       "family_counts":{k:{"pass":v["passed"],"fail":v["failed"]} for k,v in report["families"].items()},
       "scientific_detector_selected":False},sort_keys=True))
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Source-only R23-L evidence audit: NEVER infer model swap from aggregate results")
    parser.add_argument("--output",type=Path,default=ROOT/"artifacts/ceph-r23l-families")
    args=parser.parse_args()
    run(args.output)
