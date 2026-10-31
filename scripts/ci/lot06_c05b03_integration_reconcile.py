#!/usr/bin/env python3
"""LOT06 C05B-03: exact-SHA integration READINESS audit, not a product FUE.

This script DOES NOT merge branches, alter a database, or issue clinical receipts.
It compares the two existing, diverged LAB histories without silently treating
independent green test suites as an integrated release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

# Immutable, witnessed GitHub branch tips at the start of this pass.
HISTORY_SQLCIPHER = "8f99cbd4fc5045c530d73270ae4dbecdb4ac8c24"
HISTORY_PATIENT_NETWORK = "90fd4a9543057d0af1f56d5d72845d8fa5738f5b"
SOURCE_ONLY = (
    "backend/services/imaging_clinical_asset_verifier_v15.py",
    "backend/services/imaging_lab_authorized_media_gate_v15.py",
    "backend/tests/test_imaging_clinical_asset_verifier_v15.py",
    "backend/tests/test_imaging_lab_authorized_media_gate_v15.py",
    "isolated_fue_lot06c/test_sqlcipher_clinical_asset_receipt_v15.py",
    "isolated_fue_lot06c/test_sqlcipher_persistent_approval_v15.py",
    "isolated_fue_lot06c/test_sqlcipher_wal_durability_contract_v15.py",
)
TARGET_ONLY = (
    "backend/tests/test_lot06_c05b03i_product_contract.py",
    "backend/tests/test_lot06_c05b03j_http_clinic.py",
    "scripts/ci/lot06_c05b03l_windows_sqlcipher.py",
    "scripts/ci/lot06_p105_private_shared_clinic.py",
)
COMMON = (
    "backend/services/clinical_asset_storage.py",
    "alembic/versions/c2a55e700002_add_clinical_asset_storage.py",
)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ("git", *args), capture_output=True, text=True, check=False, timeout=120
    )
    if check and result.returncode:
        raise RuntimeError("GIT_RECONCILE_FAILED: " + " ".join(args[:2]) +
                           " status=" + str(result.returncode))
    return result


def file_inventory(sha: str) -> set[str]:
    output = git("ls-tree", "-r", "--name-only", sha).stdout
    return set(output.splitlines())


def classify(source: set[str], target: set[str]) -> dict:
    """Fail closed if the witnessed test contracts are not actually present."""
    return {
        "source_contracts_present": all(p in source for p in SOURCE_ONLY),
        "target_contracts_present": all(p in target for p in TARGET_ONLY),
        "shared_contracts_present": all(p in source and p in target for p in COMMON),
        "source_only_tests_missing_from_target": sorted(
            p for p in SOURCE_ONLY if p not in target
        ),
        "target_only_tests_missing_from_source": sorted(
            p for p in TARGET_ONLY if p not in source
        ),
    }


def self_test() -> None:
    base = set(SOURCE_ONLY) | set(COMMON)
    other = set(TARGET_ONLY) | set(COMMON)
    result = classify(base, other)
    assert result["source_contracts_present"]
    assert result["target_contracts_present"]
    assert result["shared_contracts_present"]
    assert len(result["source_only_tests_missing_from_target"]) == len(SOURCE_ONLY)
    assert len(result["target_only_tests_missing_from_source"]) == len(TARGET_ONLY)
    assert not classify(base - {SOURCE_ONLY[0]}, other)["source_contracts_present"]
    assert not classify(base, other - {TARGET_ONLY[0]})["target_contracts_present"]
    assert not classify(base - {COMMON[0]}, other)["shared_contracts_present"]
    print("LOT06_C05B03_RECONCILE_PARSER_SELFTEST_PASS")


def build_report() -> dict:
    source = HISTORY_SQLCIPHER
    target = HISTORY_PATIENT_NETWORK
    for sha in (source, target):
        git("cat-file", "-e", sha + "^{commit}")
        if not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise RuntimeError("INVALID_WITNESSED_COMMIT_SHA")
    files_source = file_inventory(source)
    files_target = file_inventory(target)
    contracts = classify(files_source, files_target)
    if not all(contracts[key] for key in (
        "source_contracts_present", "target_contracts_present",
        "shared_contracts_present"
    )):
        raise RuntimeError("WITNESSED_SOURCE_CONTRACT_MISSING")

    # rev-list reports source-only and target-only commits in that order.
    raw = git("rev-list", "--left-right", "--count",
              source + "..." + target).stdout.strip()
    source_only_commits, target_only_commits = map(int, raw.split())
    merge_base = git("merge-base", source, target).stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}", merge_base):
        raise RuntimeError("INVALID_MERGE_BASE")
    if not source_only_commits or not target_only_commits:
        raise RuntimeError("EXPECTED_DIVERGED_HISTORIES_NOT_REPRODUCED")

    # Merge-tree is a READ-ONLY dry run; it never updates HEAD, index or worktree.
    conflict_check = git("merge-tree", "--write-tree", "--name-only",
                         source, target, check=False)
    if conflict_check.returncode not in (0, 1):
        raise RuntimeError("GIT_MERGE_TREE_UNSUPPORTED_OR_FAILED")
    conflict_paths = sorted(set(
        path for path in conflict_check.stdout.splitlines()
        if path.startswith(("backend/", "alembic/", ".github/", "scripts/",
                            "isolated_fue_lot06c/", "tools/", "frontend/"))
        and "\t" not in path and len(path) < 260
    ))[:200]

    changed = git("diff", "--name-only", source, target, "--",
                  "backend/", "alembic/", "scripts/ci/",
                  "isolated_fue_lot06c/", ".github/workflows/").stdout.splitlines()
    critical = [p for p in changed if (
        p.startswith(("backend/services/", "alembic/versions/",
                      "backend/models", "backend/routers/"))
    )]
    # Detection is deliberately conservative: filename absence alone cannot
    # establish that a migration is semantically correct or production-ready.
    migration_candidates = sorted(p for p in files_target | files_source
        if p.startswith("alembic/versions/") and
        re.search(r"(lot06|c05b03|receipt_authority)", p, re.I))

    return {
        "kind": "LOT06_C05B03_BRANCH_RECONCILIATION_NOT_INTEGRATED_FUE",
        "source_history_sha": source,
        "patient_network_history_sha": target,
        "merge_base_sha": merge_base,
        "source_unique_commits": source_only_commits,
        "target_unique_commits": target_only_commits,
        "git_merge_tree_conflict_detected": conflict_check.returncode == 1,
        "merge_tree_potential_conflict_paths_sample": conflict_paths,
        "critical_product_or_schema_file_differences": len(critical),
        "critical_differences_sample": sorted(critical)[:40],
        "alembic_candidate_paths_seen": migration_candidates,
        "contracts": contracts,
        "db_backend_authority_choice_required": True,
        "separate_clinical_migration_approval_required": True,
        "integrated_fue_executed": False,
        "cabinet_migration_executed": False,
        "ready_to_merge": False,
        "product_ready": False,
        "clinical_go": False,
        "next": "Resolve SQLCipher on-prem vs PostgreSQL prototype and reconcile "
                "source-only contracts; then test migration up/down in isolated DB.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", default="lot06-c05b03-integration-audit.json")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    evidence = build_report()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    assert evidence["source_unique_commits"] > 0
    assert evidence["target_unique_commits"] > 0
    assert not any(evidence[key] for key in (
        "integrated_fue_executed", "cabinet_migration_executed",
        "ready_to_merge", "product_ready", "clinical_go",
    ))
    print("LOT06_C05B03_RECONCILIATION_AUDIT_PASS_INTEGRATION_BLOCKED")
    print("source_unique", evidence["source_unique_commits"],
          "target_unique", evidence["target_unique_commits"],
          "merge_tree_conflict", evidence["git_merge_tree_conflict_detected"],
          "critical_file_differences",
          evidence["critical_product_or_schema_file_differences"])


if __name__ == "__main__":
    main()
