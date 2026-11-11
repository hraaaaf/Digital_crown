"""J1.B1-S4: read-only Desktop review lexicon parity and clinical HOLD.

Cross-check a frontend lexicon projection against the S3 evidence audit.
Does not approve the model's anatomical identities or any clinical inference.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import sys

AUDIT = Path("docs/audits/CEPHALO_J1B1_S3_38_LANDMARK_TERMINOLOGY.json")
UI_LEXICON = Path("frontend/src/features/ortho/cephaloLandmarkReviewLexicon.ts")
UI_PANEL = Path("frontend/src/features/ortho/components/CephaloLandmarkReviewLexicon.tsx")
STEP1 = Path("frontend/src/features/ortho/components/Step1Cephalo.tsx")
SHARED = Path("frontend/src/features/ortho/cephaloShared.ts")

class UnsafeGlossary(RuntimeError):
    pass

def require(ok, code):
    if not ok:
        raise UnsafeGlossary(code)

def parse_static_review_rows(ts: str):
    result = []
    for line in ts.splitlines():
        if not line.strip().startswith("{ index: "):
            continue
        value = re.sub(
            r'([,{]\s*)(index|id|fr|en|aliases|sourceEvidence):\s*',
            r'\1"\2": ',
            line.strip().rstrip(","),
        )
        try:
            result.append(json.loads(value))
        except (ValueError, TypeError) as exc:
            raise UnsafeGlossary(f"TS_LEXICON_LITERAL_PARSE_FAILED: {exc}") from exc
    return result

def verify_38(rows, audit):
    expected = audit.get("landmarks")
    require(isinstance(expected, list) and len(expected) == 38 and len(rows) == 38, "NOT_38")
    require(audit.get("clinical_activation_authorized") is False
            and audit.get("model_to_anatomy_certified") is False
            and audit.get("gate") == "SOURCE_LOCK_REQUIRED", "SOURCE_AUDIT_NO_LONGER_HOLD")
    ids = set()
    for i, (row, source) in enumerate(zip(rows, expected)):
        require(row.get("index") == i and source.get("index") == i
                and source.get("challenge_number") == i + 1, "SOURCE_INDEX_CHANGED_" + str(i))
        require(row.get("id") == source.get("legacy_runtime_id")
                and row["id"] not in ids, "ID_MISMATCH_OR_DUPLICATE_" + str(i))
        ids.add(row["id"])
        require(row.get("fr") == source.get("term_fr") and row.get("en") == source.get("term_en"),
                "SOURCE_BILINGUAL_NAME_DRIFT_" + str(i))
        require(row.get("aliases") == source.get("terminology_equivalents"),
                "SOURCE_SYNONYM_DRIFT_" + str(i))
        require(row.get("sourceEvidence") == source.get("challenge_numbered_evidence"),
                "SOURCE_PROVENANCE_DRIFT_" + str(i))
        require(source.get("automated_clinical_use_allowed") is False
                and source.get("validated_model_output_identity") is False,
                "UNAPPROVED_CLINICAL_PROMOTION_" + str(i))
    return ids

def verify_ui():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    text = UI_LEXICON.read_text(encoding="utf-8")
    rows = parse_static_review_rows(text)
    detector_ids = verify_38(rows, audit)
    matches = re.findall(r'\{\s*id:\s*"(Occ_Ant|Occ_Post)"', text)
    require(matches == ["Occ_Ant", "Occ_Post"] and not detector_ids.intersection(matches),
            "TWO_OCCLUSAL_CONSTRUCTIONS_NOT_SEPARATE")
    shared = SHARED.read_text(encoding="utf-8")
    match = re.search(r'export const REQUIRED_LANDMARKS = \[(.*?)\] as const;', shared, re.S)
    require(match is not None, "REQUIRED_LANDMARKS_MISSING")
    required = re.findall(r"'([^']+)'", match.group(1))
    require(len(required) == 40 and len(set(required)) == 40, "FRONTEND_NOT_EXACTLY_40_REQUIRED")
    require(set(required) == detector_ids.union(matches), "FRONTEND_38_PLUS_2_DIFFER")
    component = UI_PANEL.read_text(encoding="utf-8")
    wrapper = STEP1.read_text(encoding="utf-8")
    for marker in ('data-review-only="true"', 'data-clinical-validated="false"',
                   'data-model-channel={number === undefined', 'lecture seule'):
        require(marker.lower() in component.lower(), "PANEL_SAFETY_UI_MARKER_MISSING_" + marker)
    require('data-cephalo-review-lexicon-details' in wrapper
            and '<CephaloLandmarkReviewLexicon' in wrapper
            and '<Step1CephaloBase {...props} embedded />' in wrapper,
            "DESKTOP_STEP1_INTEGRATION_MISSING")
    for forbidden in ('updateLandmarksOptimistic', 'setLocal(', 'setAnglesData(',
                      'onUpdateLandmarks', 'fetch(', 'axios.', 'diagnose('):
        require(forbidden not in component, "PANEL_MUTATING_OR_REMOTE_ACTION_" + forbidden)
    print("J1B1_S4_38_EXACT_BILINGUAL_TERMS_AND_SYNONYMS_SOURCE_PARITY_PASS")
    print("J1B1_S4_38_SRPOSE_CHANNELS_PLUS_2_DISTINCT_OCCLUSAL_IDS_PASS")
    print("J1B1_S4_MANUAL_REVIEW_ONLY_NO_CLINICAL_MUTATION_CONTRACT_PASS")
    return rows, audit

def negative_tests(rows, audit):
    scenarios = [
        ("SWAPPED_NUMBER", lambda x: x[0].update(index=1)),
        ("WRONG_ID", lambda x: x[12].update(id="Pog")),
        ("INVENTED_LANGUAGE", lambda x: x[0].update(fr="Non scientifique")),
        ("FORGED_NUMBERED_SOURCE", lambda x: x[1].update(sourceEvidence="AUTHOR_PAPER_EXPLICIT")),
        ("REMOVED_SYNONYM", lambda x: x[15].update(aliases=[])),
        ("DROPPED_ROW", lambda x: x.pop()),
    ]
    for key, change in scenarios:
        altered = copy.deepcopy(rows)
        change(altered)
        try:
            verify_38(altered, audit)
        except UnsafeGlossary:
            pass
        else:
            raise UnsafeGlossary("NEGATIVE_CASE_ACCEPTED_" + key)
    modified = copy.deepcopy(audit)
    modified["clinical_activation_authorized"] = True
    try:
        verify_38(rows, modified)
    except UnsafeGlossary:
        pass
    else:
        raise UnsafeGlossary("NEGATIVE_CLINICAL_GATE_BYPASS")
    print("J1B1_S4_SEVEN_ADVERSARIAL_PROVENANCE_AND_NO_CLINICAL_GO_GATES_PASS")

if __name__ == "__main__":
    try:
        rows, original = verify_ui()
        negative_tests(rows, original)
    except (UnsafeGlossary, ValueError, FileNotFoundError, TypeError, KeyError) as exc:
        print("J1B1_S4_FAIL_CLOSED:", exc, file=sys.stderr)
        sys.exit(2)
